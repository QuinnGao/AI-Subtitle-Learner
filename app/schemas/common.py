"""
通用数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AudioStreamInfo(BaseModel):
    """音频流信息"""

    index: int = Field(..., description="音轨索引")
    codec: str = Field(..., description="音频编解码器")
    language: str = Field(default="", description="语言标签")
    title: str = Field(default="", description="音轨标题")


class VideoInfo(BaseModel):
    """视频信息"""

    file_name: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    width: int = Field(..., description="视频宽度")
    height: int = Field(..., description="视频高度")
    fps: float = Field(..., description="帧率")
    duration_seconds: float = Field(..., description="时长（秒）")
    bitrate_kbps: int = Field(..., description="比特率（kbps）")
    video_codec: str = Field(..., description="视频编解码器")
    audio_codec: str = Field(..., description="音频编解码器")
    audio_sampling_rate: int = Field(..., description="音频采样率")
    thumbnail_path: str = Field(default="", description="缩略图路径")
    audio_streams: list[AudioStreamInfo] = Field(
        default_factory=list, description="音频流列表"
    )


class TaskResponse(BaseModel):
    """任务响应基类"""

    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    queued_at: Optional[datetime] = Field(None, description="排队时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    message: str = Field(default="", description="状态消息")
    error: Optional[str] = Field(None, description="错误信息")
    output_path: Optional[str] = Field(None, description="输出文件路径")

