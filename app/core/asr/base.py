import os
import pickle
import tempfile
import threading
import time
import uuid
import zlib
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional, Union, cast

from pydub import AudioSegment

from app.core.storage import get_storage
from app.core.utils.cache import get_asr_cache, is_cache_enabled
from app.core.utils.logger import setup_logger

from .asr_data import ASRData, ASRDataSeg

logger = setup_logger("asr")


class BaseASR:
    """Base class for ASR (Automatic Speech Recognition) implementations.

    Provides common functionality including:
    - Audio file loading and validation
    - CRC32-based file identification
    - Disk caching with automatic key generation
    - Template method pattern for subclass implementation
    - Rate limiting for public charity services
    """

    SUPPORTED_SOUND_FORMAT = ["flac", "m4a", "mp3", "wav"]
    _lock = threading.Lock()

    RATE_LIMIT_MAX_CALLS = 100
    RATE_LIMIT_MAX_DURATION = 360 * 60
    RATE_LIMIT_TIME_WINDOW = 12 * 3600

    def __init__(
        self,
        audio_path: Optional[Union[str, bytes]] = None,
        use_cache: bool = False,
        need_word_time_stamp: bool = False,
    ):
        """Initialize ASR with audio data.

        Args:
            audio_path: Path to audio file or raw audio bytes
            use_cache: Whether to cache recognition results
            need_word_time_stamp: Whether to return word-level timestamps
        """
        self.audio_path = audio_path
        self.file_binary = None
        self.use_cache = use_cache
        self._set_data()
        self._cache = get_asr_cache()
        self.audio_duration = self._get_audio_duration()

    def _set_data(self):
        """Load audio data and compute CRC32 hash for cache key.

        支持从 MinIO 读取音频文件。
        """
        if isinstance(self.audio_path, bytes):
            self.file_binary = self.audio_path
        elif isinstance(self.audio_path, str):
            ext = self.audio_path.split(".")[-1].lower()
            assert ext in self.SUPPORTED_SOUND_FORMAT, (
                f"Unsupported sound format: {ext}"
            )

            # 检查是否是 MinIO 对象
            storage = get_storage()
            if storage.file_exists(self.audio_path):
                # 从 MinIO 下载到临时文件
                logger.debug(f"从 MinIO 下载音频文件: {self.audio_path}")
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=Path(self.audio_path).suffix
                ) as tmp_file:
                    tmp_path = tmp_file.name
                storage.download_file(self.audio_path, tmp_path)
                try:
                    with open(tmp_path, "rb") as f:
                        self.file_binary = f.read()
                finally:
                    # 清理临时文件
                    Path(tmp_path).unlink(missing_ok=True)
            elif os.path.exists(self.audio_path):
                # 本地文件
                with open(self.audio_path, "rb") as f:
                    self.file_binary = f.read()
            else:
                raise FileNotFoundError(f"File not found: {self.audio_path}")
        else:
            raise ValueError("audio_path must be provided as string or bytes")
        crc32_value = zlib.crc32(self.file_binary) & 0xFFFFFFFF
        self.crc32_hex = format(crc32_value, "08x")

    def _get_audio_duration(self) -> float:
        """Get audio duration in seconds using pydub."""
        if not self.file_binary:
            return 0.0
        try:
            audio = AudioSegment.from_file(BytesIO(self.file_binary))
            return audio.duration_seconds
        except Exception as e:
            logger.warning(f"Failed to get audio duration: {e}")
            return 60.0 * 10

    def run(
        self, callback: Optional[Callable[[int, str], None]] = None, **kwargs
    ) -> ASRData:
        """Run ASR with caching support.

        Args:
            callback: Optional progress callback(progress: int, message: str)
            **kwargs: Additional arguments passed to _run()

        Returns:
            ASRData: Recognition results with segments
        """
        cache_key = f"{self.__class__.__name__}:{self._get_key()}"

        # Try cache first
        if self.use_cache and is_cache_enabled():
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                # 反序列化缓存结果
                cached_result = pickle.loads(cached_result)
                cached_result = cast(Optional[dict], cached_result)
                logger.info("找到缓存，直接返回")
                segments = self._make_segments(cached_result)
                return ASRData(segments)

        # Run ASR
        resp_data = self._run(callback, **kwargs)

        # Cache result
        cached_data = pickle.dumps(resp_data)
        self._cache.setex(cache_key, 86400 * 2, cached_data)

        segments = self._make_segments(resp_data)
        return ASRData(segments)

    def _get_key(self) -> str:
        """Get cache key for this ASR request.

        Default implementation uses file CRC32.
        Subclasses can override to include additional parameters.

        Returns:
            Cache key string
        """
        return self.crc32_hex

    def _make_segments(self, resp_data: dict) -> list[ASRDataSeg]:
        """Convert ASR response to segment list.

        Args:
            resp_data: Raw response from ASR service

        Returns:
            List of ASRDataSeg objects
        """
        raise NotImplementedError(
            "_make_segments method must be implemented in subclass"
        )

    def _run(
        self, callback: Optional[Callable[[int, str], None]] = None, **kwargs
    ) -> dict:
        """Execute ASR service and return raw response.

        Args:
            callback: Progress callback(progress: int, message: str)
            **kwargs: Implementation-specific parameters

        Returns:
            Raw response data (dict or str depending on implementation)
        """
        raise NotImplementedError("_run method must be implemented in subclass")

    def _check_rate_limit(self) -> None:
        """Check rate limit for public charity services."""
        service_name = self.__class__.__name__
        tag = f"rate_limit:{service_name}"
        time_limit = time.time() - self.RATE_LIMIT_TIME_WINDOW

        # Query recent records
        try:
            query = "SELECT key FROM Cache WHERE tag = ? AND store_time >= ?"
            results = self._cache._sql(query, (tag, time_limit)).fetchall()
        except Exception as e:
            raise RuntimeError(f"Failed to query rate limit: {e}")

        # Get durations using cache API
        durations = []
        for (key,) in results:
            duration_bytes = self._cache.get(key)
            if duration_bytes is not None:
                duration = pickle.loads(duration_bytes)
                if isinstance(duration, (int, float)):
                    durations.append(duration)

        call_count = len(durations)
        total_duration = sum(durations)

        # Check duration limit
        if total_duration + self.audio_duration > self.RATE_LIMIT_MAX_DURATION:
            error_msg = f"{service_name} duration limit exceeded"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        # Check call count limit
        if call_count >= self.RATE_LIMIT_MAX_CALLS:
            error_msg = f"{service_name} call count limit exceeded"
            logger.warning(error_msg)
            raise RuntimeError(error_msg)

        # Record current call (store duration directly as float)
        duration_bytes = pickle.dumps(self.audio_duration)
        expire_time = int(self.RATE_LIMIT_TIME_WINDOW) + 3600
        self._cache.setex(
            f"rate_limit_record:{service_name}:{uuid.uuid4()}",
            expire_time,
            duration_bytes,
        )
