"""
任务管理服务（使用数据库持久化）
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from app.database.base import SessionLocal
from app.database.models import Task, TaskRelation
from app.schemas.common import TaskResponse, TaskStatus
from app.core.utils.logger import setup_logger

logger = setup_logger("task_manager")


def _task_to_response(task: Task) -> TaskResponse:
    """将数据库 Task 模型转换为 TaskResponse"""
    return TaskResponse(
        task_id=task.task_id,
        status=task.status,
        queued_at=task.queued_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        progress=task.progress,
        message=task.message or "",
        error=task.error,
        output_path=task.output_path,
    )


class TaskManager:
    """任务管理器（使用数据库持久化）"""

    def __init__(self):
        self._db: Optional[Session] = None

    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def create_task(
        self,
        task_type: Optional[str] = None,
        video_url: Optional[str] = None,
    ) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        db = self._get_db()
        try:
            task = Task(
                task_id=task_id,
                status=TaskStatus.PENDING,
                queued_at=datetime.utcnow(),
                task_type=task_type,
                video_url=video_url,
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            logger.info(f"创建任务: task_id={task_id}, task_type={task_type}")
            return task_id
        except Exception as e:
            db.rollback()
            logger.error(f"创建任务失败: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
            self._db = None

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """获取任务"""
        db = self._get_db()
        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                return _task_to_response(task)
            return None
        finally:
            db.close()
            self._db = None

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
        output_path: Optional[str] = None,
    ):
        """更新任务状态"""
        db = self._get_db()
        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if not task:
                logger.warning(f"任务不存在: task_id={task_id}")
                return

            if status:
                task.status = status
                if status == TaskStatus.RUNNING and not task.started_at:
                    task.started_at = datetime.utcnow()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = datetime.utcnow()

            if progress is not None:
                task.progress = progress

            if message is not None:
                task.message = message

            if error is not None:
                task.error = error
                if error:
                    task.status = TaskStatus.FAILED
                    if not task.completed_at:
                        task.completed_at = datetime.utcnow()

            if output_path is not None:
                task.output_path = output_path

            db.commit()
            db.refresh(task)
            logger.debug(
                f"更新任务: task_id={task_id}, status={task.status}, progress={task.progress}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"更新任务失败: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
            self._db = None

    def set_task_relation(self, task_id: str, relation_type: str, related_task_id: str):
        """设置任务关联关系

        Args:
            task_id: 主任务ID
            relation_type: 关联类型（如 "transcribe_task_id", "subtitle_task_id"）
            related_task_id: 关联的任务ID
        """
        db = self._get_db()
        try:
            # 检查是否已存在相同的关联关系
            existing = (
                db.query(TaskRelation)
                .filter(
                    TaskRelation.task_id == task_id,
                    TaskRelation.relation_type == relation_type,
                )
                .first()
            )
            if existing:
                existing.related_task_id = related_task_id
            else:
                relation = TaskRelation(
                    task_id=task_id,
                    relation_type=relation_type,
                    related_task_id=related_task_id,
                )
                db.add(relation)
            db.commit()
            logger.debug(
                f"设置任务关联: task_id={task_id}, relation_type={relation_type}, "
                f"related_task_id={related_task_id}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"设置任务关联失败: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
            self._db = None

    def set_task_relations(self, task_id: str, relations: dict[str, str]):
        """批量设置任务关联关系

        Args:
            task_id: 主任务ID
            relations: 关联关系字典，格式如 {"transcribe_task_id": "...", "subtitle_task_id": "..."}
        """
        db = self._get_db()
        try:
            for relation_type, related_task_id in relations.items():
                # 检查是否已存在相同的关联关系
                existing = (
                    db.query(TaskRelation)
                    .filter(
                        TaskRelation.task_id == task_id,
                        TaskRelation.relation_type == relation_type,
                    )
                    .first()
                )
                if existing:
                    existing.related_task_id = related_task_id
                else:
                    relation = TaskRelation(
                        task_id=task_id,
                        relation_type=relation_type,
                        related_task_id=related_task_id,
                    )
                    db.add(relation)
            db.commit()
            logger.debug(f"批量设置任务关联: task_id={task_id}, relations={relations}")
        except Exception as e:
            db.rollback()
            logger.error(f"批量设置任务关联失败: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
            self._db = None

    def get_task_relation(self, task_id: str, relation_type: str) -> Optional[str]:
        """获取任务关联关系

        Args:
            task_id: 主任务ID
            relation_type: 关联类型（如 "transcribe_task_id", "subtitle_task_id"）

        Returns:
            关联的任务ID，如果不存在返回 None
        """
        db = self._get_db()
        try:
            relation = (
                db.query(TaskRelation)
                .filter(
                    TaskRelation.task_id == task_id,
                    TaskRelation.relation_type == relation_type,
                )
                .first()
            )
            if relation:
                return relation.related_task_id
            return None
        finally:
            db.close()
            self._db = None

    def get_task_relations(self, task_id: str) -> dict[str, str]:
        """获取任务的所有关联关系

        Args:
            task_id: 主任务ID

        Returns:
            关联关系字典
        """
        db = self._get_db()
        try:
            relations = (
                db.query(TaskRelation).filter(TaskRelation.task_id == task_id).all()
            )
            return {rel.relation_type: rel.related_task_id for rel in relations}
        finally:
            db.close()
            self._db = None

    def delete_task(self, task_id: str):
        """删除任务（级联删除关联关系）"""
        db = self._get_db()
        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                db.delete(task)
                db.commit()
                logger.info(f"删除任务: task_id={task_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"删除任务失败: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
            self._db = None


# 全局单例实例
_task_manager_instance: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取全局 TaskManager 单例实例"""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance
