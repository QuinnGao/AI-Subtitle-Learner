"""
批量处理相关数据模型
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TaskResponse
from app.schemas.subtitle import SubtitleConfig
from app.schemas.synthesis import SynthesisConfig
from app.schemas.transcribe import TranscribeConfig


class BatchTaskType(str, Enum):
    """批量处理任务类型"""

    TRANSCRIBE = "transcribe"
    SUBTITLE = "subtitle"
    TRANS_SUB = "trans_sub"
    FULL_PROCESS = "full_process"


class BatchTaskRequest(BaseModel):
    """批量处理请求"""

    task_type: BatchTaskType = Field(..., description="任务类型")
    file_paths: list[str] = Field(..., min_items=1, description="文件路径列表")
    output_dir: Optional[str] = Field(None, description="输出目录（可选）")

    # 配置（根据任务类型选择）
    transcribe_config: Optional[TranscribeConfig] = Field(
        None, description="转录配置"
    )
    subtitle_config: Optional[SubtitleConfig] = Field(None, description="字幕配置")
    synthesis_config: Optional[SynthesisConfig] = Field(
        None, description="合成配置"
    )


class BatchTaskResponse(TaskResponse):
    """批量处理响应"""

    total_files: int = Field(..., description="总文件数")
    completed_files: int = Field(default=0, description="已完成文件数")
    failed_files: int = Field(default=0, description="失败文件数")
    file_results: list[dict] = Field(
        default_factory=list, description="文件处理结果列表"
    )

