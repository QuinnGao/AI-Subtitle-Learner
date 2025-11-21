"""
视频合成相关数据模型
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TaskResponse


class VideoQuality(str, Enum):
    """视频质量"""

    ULTRA_HIGH = "ultra_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SynthesisConfig(BaseModel):
    """视频合成配置"""

    need_video: bool = Field(default=True, description="是否需要生成视频")
    soft_subtitle: bool = Field(default=True, description="是否使用软字幕")
    video_quality: VideoQuality = Field(
        default=VideoQuality.MEDIUM, description="视频质量"
    )


class SynthesisRequest(BaseModel):
    """视频合成请求"""

    video_path: str = Field(..., description="视频文件路径")
    subtitle_path: str = Field(..., description="字幕文件路径")
    output_path: Optional[str] = Field(None, description="输出文件路径（可选）")
    config: SynthesisConfig = Field(
        default_factory=SynthesisConfig, description="视频合成配置"
    )


class SynthesisResponse(TaskResponse):
    """视频合成响应"""

    pass

