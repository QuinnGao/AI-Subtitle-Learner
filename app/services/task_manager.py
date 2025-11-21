"""
任务管理服务
"""

import uuid
import sys
from datetime import datetime
from typing import Optional

from app.schemas.common import TaskResponse, TaskStatus
from app.core.utils.logger import setup_logger

logger = setup_logger("task_manager")

# 全局单例实例
_task_manager_instance: Optional["TaskManager"] = None


class TaskManager:
    """任务管理器（单例模式）"""

    def __init__(self):
        self.tasks: dict[str, TaskResponse] = {}
        # 存储任务关联关系：{task_id: {"transcribe_task_id": "...", "subtitle_task_id": "..."}}
        self.task_relations: dict[str, dict[str, str]] = {}

    def __new__(cls):
        """单例模式实现"""
        global _task_manager_instance
        if _task_manager_instance is None:
            _task_manager_instance = super().__new__(cls)
        return _task_manager_instance

    def create_task(self) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        task = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            queued_at=datetime.now(),
        )
        self.tasks[task_id] = task
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """获取任务"""
        return self.tasks.get(task_id)

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
        task = self.tasks.get(task_id)
        if not task:
            return

        if status:
            task.status = status
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.now()

        if progress is not None:
            task.progress = progress

        if message:
            task.message = message

        if error:
            task.error = error
            task.status = TaskStatus.FAILED

        if output_path:
            task.output_path = output_path

        # 打印所有保存的任务
        self._print_all_tasks()

    def set_task_relation(self, task_id: str, relation_type: str, related_task_id: str):
        """设置任务关联关系

        Args:
            task_id: 主任务ID
            relation_type: 关联类型（如 "transcribe_task_id", "subtitle_task_id"）
            related_task_id: 关联的任务ID
        """
        if task_id not in self.task_relations:
            self.task_relations[task_id] = {}
        self.task_relations[task_id][relation_type] = related_task_id

    def set_task_relations(self, task_id: str, relations: dict[str, str]):
        """批量设置任务关联关系

        Args:
            task_id: 主任务ID
            relations: 关联关系字典，格式如 {"transcribe_task_id": "...", "subtitle_task_id": "..."}
        """
        if task_id not in self.task_relations:
            self.task_relations[task_id] = {}
        self.task_relations[task_id].update(relations)

    def get_task_relation(self, task_id: str, relation_type: str) -> Optional[str]:
        """获取任务关联关系

        Args:
            task_id: 主任务ID
            relation_type: 关联类型（如 "transcribe_task_id", "subtitle_task_id"）

        Returns:
            关联的任务ID，如果不存在返回 None
        """
        if task_id not in self.task_relations:
            return None
        return self.task_relations[task_id].get(relation_type)

    def get_task_relations(self, task_id: str) -> dict[str, str]:
        """获取任务的所有关联关系

        Args:
            task_id: 主任务ID

        Returns:
            关联关系字典
        """
        return self.task_relations.get(task_id, {})

    def _print_all_tasks(self):
        """打印所有保存的任务信息"""
        if not self.tasks:
            logger.debug("[TaskManager] 当前没有保存的任务")
            return

        logger.info("=" * 80)
        logger.info(f"[TaskManager] 当前所有任务 (共 {len(self.tasks)} 个):")
        logger.info("-" * 80)

        for task_id, task in self.tasks.items():
            # 获取关联关系
            relations = self.task_relations.get(task_id, {})
            relations_str = (
                ", ".join([f"{k}={v}" for k, v in relations.items()])
                if relations
                else "无"
            )

            # 格式化时间
            queued_at_str = (
                task.queued_at.strftime("%Y-%m-%d %H:%M:%S")
                if task.queued_at
                else "N/A"
            )
            started_at_str = (
                task.started_at.strftime("%Y-%m-%d %H:%M:%S")
                if task.started_at
                else "N/A"
            )
            completed_at_str = (
                task.completed_at.strftime("%Y-%m-%d %H:%M:%S")
                if task.completed_at
                else "N/A"
            )

            logger.info(f"  任务ID: {task_id}")
            logger.info(
                f"    状态: {task.status.value if hasattr(task.status, 'value') else task.status}"
            )
            logger.info(f"    进度: {task.progress}%")
            logger.info(f"    消息: {task.message or 'N/A'}")
            logger.info(f"    错误: {task.error or 'N/A'}")
            logger.info(f"    输出路径: {task.output_path or 'N/A'}")
            logger.info(f"    排队时间: {queued_at_str}")
            logger.info(f"    开始时间: {started_at_str}")
            logger.info(f"    完成时间: {completed_at_str}")
            logger.info(f"    关联关系: {relations_str}")
            logger.info("-" * 80)

        logger.info("=" * 80)
        sys.stderr.flush()

    def delete_task(self, task_id: str):
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
        if task_id in self.task_relations:
            del self.task_relations[task_id]


def get_task_manager() -> TaskManager:
    """获取全局 TaskManager 单例实例"""
    return TaskManager()
