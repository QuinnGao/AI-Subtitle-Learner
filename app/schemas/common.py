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
