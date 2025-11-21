"""
WhisperX ASR 实现
提供精准的字词级时间戳
"""

from pathlib import Path
from typing import Callable, Optional

try:
    import whisperx
    import torch

    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False

from ..utils.logger import setup_logger
from .asr_data import ASRDataSeg
from .base import BaseASR

logger = setup_logger("whisperx")


class WhisperXASR(BaseASR):
    """WhisperX ASR 实现，提供精准的字词级时间戳"""

    def __init__(
        self,
        audio_path: Optional[str] = None,
        use_cache: bool = False,
        need_word_time_stamp: bool = True,
        language: str = "auto",
        model: str = "large-v3",
        device: str = "cpu",
        compute_type: str = "float32",
        batch_size: int = 16,
        model_dir: Optional[str] = None,
    ):
        """初始化 WhisperX ASR

        Args:
            audio_path: 音频文件路径
            use_cache: 是否使用缓存
            need_word_time_stamp: 是否需要词级时间戳（WhisperX 总是提供）
            language: 语言代码（auto 为自动检测）
            model: Whisper 模型名称或 Hugging Face 模型 ID
            device: 设备（cuda/cpu，默认 cpu）
            compute_type: 计算类型（float16/float32/int8，默认 float32）
            batch_size: 批处理大小
            model_dir: 模型存储目录（可选，如果指定则从本地加载）
        """
        if not WHISPERX_AVAILABLE:
            raise ImportError("WhisperX 未安装。请运行: pip install whisperx")

        super().__init__(audio_path, use_cache, need_word_time_stamp=True)
        self.language = language
        self.model = model
        self.device = device
        self.compute_type = compute_type
        self.batch_size = batch_size
        self.model_dir = model_dir

        # 自动选择设备
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA 不可用，使用 CPU")
            self.device = "cpu"
            self.compute_type = "float32"

        # 如果使用 CPU，确保 compute_type 为 float32
        if self.device == "cpu" and self.compute_type != "float32":
            logger.info(
                f"CPU 模式下强制使用 float32，忽略 compute_type={self.compute_type}"
            )
            self.compute_type = "float32"

    def _get_key(self) -> str:
        """生成缓存键，包含模型和语言信息"""
        key_parts = [
            self.crc32_hex,
            self.model,
            self.language,
            self.device,
            self.compute_type,
        ]
        return ":".join(key_parts)

    def _run(
        self, callback: Optional[Callable[[int, str], None]] = None, **kwargs
    ) -> dict:
        """执行 WhisperX 转录

        Args:
            callback: 进度回调函数
            **kwargs: 额外参数

        Returns:
            转录结果字典
        """
        if callback:
            callback(10, "加载 WhisperX 模型...")

        # 确定模型目录（download_root）
        download_root = None
        if self.model_dir:
            download_root = Path(self.model_dir)
            download_root.mkdir(parents=True, exist_ok=True)
            logger.info(f"[WhisperX] 使用自定义模型目录: {download_root}")
        else:
            # 使用项目根目录下的 models/whisperx 文件夹
            from ...config import MODEL_PATH

            download_root = Path(MODEL_PATH) / "whisperx"
            download_root.mkdir(parents=True, exist_ok=True)
            logger.info(f"[WhisperX] 使用默认模型目录: {download_root}")

        # 加载模型
        logger.info(
            f"[WhisperX] 加载模型: model={self.model}, device={self.device}, "
            f"compute_type={self.compute_type}, download_root={download_root}"
        )

        model = whisperx.load_model(
            self.model,
            self.device,
            compute_type=self.compute_type,
            language=None if self.language == "auto" else self.language,
            download_root=str(download_root),
        )

        logger.info("[WhisperX] 模型加载完成")

        if callback:
            callback(30, "转录音频...")

        # 转录音频
        audio = whisperx.load_audio(self.audio_path)
        result = model.transcribe(
            audio,
            batch_size=self.batch_size,
            language=None if self.language == "auto" else self.language,
        )

        if callback:
            callback(60, "对齐时间戳...")

        # 对齐模型（用于获取精准的字词级时间戳）
        # 对齐模型也使用相同的模型目录
        if self.model_dir:
            align_download_root = Path(self.model_dir)
        else:
            from ...config import MODEL_PATH

            align_download_root = Path(MODEL_PATH) / "whisperx"

        logger.info(
            f"[WhisperX] 加载对齐模型: language={result['language']}, "
            f"download_root={align_download_root}"
        )

        model_a, metadata = whisperx.load_align_model(
            language_code=result["language"],
            device=self.device,
        )

        logger.info("[WhisperX] 对齐模型加载完成")
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            self.device,
            return_char_alignments=False,
        )

        if callback:
            callback(100, "转录完成")

        return result

    def _make_segments(self, resp_data: dict) -> list[ASRDataSeg]:
        """将 WhisperX 结果转换为 ASRDataSeg 列表

        WhisperX 提供精确的词级时间戳，直接使用这些时间戳创建词级字幕段。

        Args:
            resp_data: WhisperX 转录结果，包含 segments 和每个 segment 的 words

        Returns:
            ASRDataSeg 列表（词级时间戳）
        """
        segments = []

        for segment in resp_data.get("segments", []):
            # WhisperX 对齐后的结果包含 words 数组，每个 word 都有精确的时间戳
            words = segment.get("words", [])

            if words:
                # 如果有词级时间戳，直接使用（这是最精确的方式）
                for word in words:
                    word_text = word.get("word", "").strip()
                    if not word_text:
                        continue

                    # WhisperX 返回的时间戳是秒，需要转换为毫秒
                    start_time = int(float(word.get("start", 0)) * 1000)
                    end_time = int(float(word.get("end", 0)) * 1000)

                    segments.append(
                        ASRDataSeg(
                            text=word_text,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )
            else:
                # 如果没有词级时间戳（理论上不应该发生），回退到句子级
                start_time = int(segment.get("start", 0) * 1000)  # 转换为毫秒
                end_time = int(segment.get("end", 0) * 1000)
                text = segment.get("text", "").strip()

                if text:
                    segments.append(
                        ASRDataSeg(
                            text=text,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )

        return segments
