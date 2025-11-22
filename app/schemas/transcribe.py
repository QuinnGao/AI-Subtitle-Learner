"""
转录相关数据模型
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TaskResponse


class TranscribeModel(str, Enum):
    """转录模型"""

    BIJIAN = "bijian"
    JIANYING = "jianying"
    WHISPER_API = "whisper_api"
    FASTER_WHISPER = "faster_whisper"
    WHISPER_CPP = "whisper_cpp"
    WHISPERX = "whisperx"


class WhisperModel(str, Enum):
    """Whisper 模型"""

    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V1 = "large-v1"
    LARGE_V2 = "large-v2"


class FasterWhisperModel(str, Enum):
    """Faster Whisper 模型"""

    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V1 = "large-v1"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"
    LARGE_V3_TURBO = "large-v3-turbo"


class VadMethod(str, Enum):
    """VAD 方法"""

    SILERO_V3 = "silero_v3"
    SILERO_V4 = "silero_v4"
    SILERO_V5 = "silero_v5"
    SILERO_V4_FW = "silero_v4_fw"
    PYANNOTE_V3 = "pyannote_v3"
    PYANNOTE_ONNX_V3 = "pyannote_onnx_v3"
    WEBRTC = "webrtc"
    AUDITOK = "auditok"


class TranscribeOutputFormat(str, Enum):
    """转录输出格式"""

    SRT = "srt"
    ASS = "ass"
    VTT = "vtt"
    TXT = "txt"
    ALL = "all"


class TranscribeConfig(BaseModel):
    """转录配置"""

    transcribe_model: TranscribeModel = Field(
        default=TranscribeModel.FASTER_WHISPER, description="转录模型"
    )
    transcribe_language: str = Field(
        default="auto", description="转录语言（auto 为自动检测）"
    )
    need_word_time_stamp: bool = Field(
        default=True, description="是否需要词级时间戳"
    )
    output_format: TranscribeOutputFormat = Field(
        default=TranscribeOutputFormat.SRT, description="输出格式"
    )

    # Whisper Cpp 配置
    whisper_model: Optional[WhisperModel] = Field(
        None, description="Whisper 模型"
    )

    # Whisper API 配置
    whisper_api_key: Optional[str] = Field(None, description="Whisper API Key")
    whisper_api_base: Optional[str] = Field(None, description="Whisper API Base URL")
    whisper_api_model: Optional[str] = Field(None, description="Whisper API 模型")
    whisper_api_prompt: Optional[str] = Field(None, description="Whisper API 提示词")

    # Faster Whisper 配置
    faster_whisper_program: Optional[str] = Field(
        None, description="Faster Whisper 程序路径"
    )
    faster_whisper_model: Optional[FasterWhisperModel] = Field(
        None, description="Faster Whisper 模型"
    )
    faster_whisper_model_dir: Optional[str] = Field(
        None, description="Faster Whisper 模型目录"
    )
    faster_whisper_device: str = Field(
        default="cuda", description="设备（cuda/cpu）"
    )
    faster_whisper_vad_filter: bool = Field(
        default=True, description="是否启用 VAD 过滤"
    )
    faster_whisper_vad_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="VAD 阈值"
    )
    faster_whisper_vad_method: Optional[VadMethod] = Field(
        default=VadMethod.SILERO_V3, description="VAD 方法"
    )
    faster_whisper_ff_mdx_kim2: bool = Field(
        default=False, description="是否使用 ff_mdx_kim2"
    )
    faster_whisper_one_word: bool = Field(
        default=True, description="是否一个词一个片段"
    )
    faster_whisper_prompt: Optional[str] = Field(
        None, description="Faster Whisper 提示词"
    )

    # WhisperX 配置
    whisperx_model: Optional[str] = Field(
        default="large-v3", description="WhisperX 模型名称"
    )
    whisperx_device: str = Field(
        default="cpu", description="WhisperX 设备（cuda/cpu，默认 cpu）"
    )
    whisperx_compute_type: str = Field(
        default="float32", description="WhisperX 计算类型（float16/float32/int8，默认 float32）"
    )
    whisperx_batch_size: int = Field(
        default=16, description="WhisperX 批处理大小"
    )

    # 音轨选择
    selected_audio_track_index: int = Field(
        default=0, ge=0, description="选中的音轨索引"
    )


class TranscribeRequest(BaseModel):
    """转录请求"""

    file_path: str = Field(..., description="视频/音频文件路径")
    output_path: Optional[str] = Field(None, description="输出文件路径（可选）")
    config: TranscribeConfig = Field(
        default_factory=TranscribeConfig, description="转录配置"
    )



