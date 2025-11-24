"""
数据库模型
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.database.base import Base
from app.schemas.common import TaskStatus


class Task(Base):
    """任务表"""

    __tablename__ = "tasks"

    task_id = Column(String(36), primary_key=True, index=True)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    progress = Column(Integer, default=0, nullable=False)
    message = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    output_path = Column(String(512), nullable=True)

    # 任务类型和关联信息
    task_type = Column(
        String(50), nullable=True
    )  # video_download, transcribe, subtitle
    video_url = Column(
        String(512), nullable=True
    )  # 视频 URL（用于 video_download 任务）

    # 关联关系
    # 明确指定使用 TaskRelation.task_id 作为外键（因为 TaskRelation 有两个外键都指向 Task）
    relations = relationship(
        "TaskRelation",
        foreign_keys="TaskRelation.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Task(task_id={self.task_id}, status={self.status.value})>"


class TaskRelation(Base):
    """任务关联关系表"""

    __tablename__ = "task_relations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(
        String(36),
        ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type = Column(
        String(50), nullable=False
    )  # transcribe_task_id, subtitle_task_id, video_task_id
    related_task_id = Column(
        String(36),
        ForeignKey("tasks.task_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    task = relationship("Task", foreign_keys=[task_id], back_populates="relations")
    related_task = relationship("Task", foreign_keys=[related_task_id])

    def __repr__(self):
        return f"<TaskRelation(task_id={self.task_id}, relation_type={self.relation_type}, related_task_id={self.related_task_id})>"
