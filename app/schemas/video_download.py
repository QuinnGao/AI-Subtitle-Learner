"""
视频下载相关数据模型
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TaskResponse


class VideoDownloadRequest(BaseModel):
    """视频下载请求"""

    url: str = Field(..., description="视频 URL")
    need_subtitle: bool = Field(default=True, description="是否需要下载字幕")
    need_thumbnail: bool = Field(default=False, description="是否需要下载缩略图")
    work_dir: Optional[str] = Field(None, description="工作目录（可选，默认使用配置的工作目录）")


class SubtitleTaskInfo(BaseModel):
    """字幕任务信息"""
    
    task_id: Optional[str] = Field(None, description="字幕任务ID")
    status: Optional[str] = Field(None, description="字幕任务状态")
    progress: Optional[int] = Field(None, description="字幕任务进度")
    message: Optional[str] = Field(None, description="字幕任务消息")
    output_path: Optional[str] = Field(None, description="字幕输出路径")


class TranscribeTaskInfo(BaseModel):
    """转录任务信息"""
    
    task_id: Optional[str] = Field(None, description="转录任务ID")
    status: Optional[str] = Field(None, description="转录任务状态")
    progress: Optional[int] = Field(None, description="转录任务进度")
    message: Optional[str] = Field(None, description="转录任务消息")


class VideoDownloadResponse(TaskResponse):
    """视频下载响应"""

    video_path: Optional[str] = Field(None, description="视频文件路径")
    subtitle_path: Optional[str] = Field(None, description="字幕文件路径")
    thumbnail_path: Optional[str] = Field(None, description="缩略图文件路径")
    transcribe_task: Optional[TranscribeTaskInfo] = Field(None, description="转录任务信息")
    subtitle_task: Optional[SubtitleTaskInfo] = Field(None, description="字幕处理任务信息")

