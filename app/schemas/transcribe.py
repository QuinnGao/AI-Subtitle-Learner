"""
转录相关数据模型
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TranscribeModel(str, Enum):
    """转录模型"""

    WHISPERX = "whisperx"


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
        default=TranscribeModel.WHISPERX, description="转录模型"
    )
    transcribe_language: str = Field(
        default="auto", description="转录语言（auto 为自动检测）"
    )
    need_word_time_stamp: bool = Field(default=True, description="是否需要词级时间戳")
    output_format: TranscribeOutputFormat = Field(
        default=TranscribeOutputFormat.SRT, description="输出格式"
    )

    # WhisperX 配置
    whisperx_model: Optional[str] = Field(
        default="large-v3", description="WhisperX 模型名称"
    )
    whisperx_device: str = Field(
        default="cpu", description="WhisperX 设备（cuda/cpu，默认 cpu）"
    )
    whisperx_compute_type: str = Field(
        default="float32",
        description="WhisperX 计算类型（float16/float32/int8，默认 float32）",
    )
    whisperx_batch_size: int = Field(default=16, description="WhisperX 批处理大小")


class TranscribeRequest(BaseModel):
    """转录请求"""

    output_path: Optional[str] = Field(
        None, description="输出文件路径（可选，MinIO 路径）"
    )
    config: TranscribeConfig = Field(
        default_factory=TranscribeConfig, description="转录配置"
    )
