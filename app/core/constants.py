"""
任务状态常量
"""
from app.schemas.common import TaskStatus

# 任务状态常量（从 TaskStatus 枚举导出，方便使用）
TASK_STATUS_PENDING = TaskStatus.PENDING
TASK_STATUS_RUNNING = TaskStatus.RUNNING
TASK_STATUS_COMPLETED = TaskStatus.COMPLETED
TASK_STATUS_FAILED = TaskStatus.FAILED
TASK_STATUS_CANCELLED = TaskStatus.CANCELLED

# 也可以直接导出 TaskStatus 枚举类
__all__ = [
    "TaskStatus",
    "TASK_STATUS_PENDING",
    "TASK_STATUS_RUNNING",
    "TASK_STATUS_COMPLETED",
    "TASK_STATUS_FAILED",
    "TASK_STATUS_CANCELLED",
]

