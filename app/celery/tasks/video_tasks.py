"""
视频下载相关 Celery 任务
"""

import asyncio
from pathlib import Path

from app.celery import celery_app
from app.celery.services.video_download_service import VideoDownloadService
from app.services.task_manager import get_task_manager
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger

logger = setup_logger("video_tasks")
task_manager = get_task_manager()
video_download_service = VideoDownloadService()


@celery_app.task(
    name="app.celery.tasks.video.download_audio",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def download_audio_task(self, task_id: str, url: str, work_dir: str = None):
    """下载音频任务（Celery 任务）

    Args:
        task_id: 任务ID
        url: 视频URL
        work_dir: 工作目录（可选）
    """
    try:
        logger.info(f"[Celery Task] 开始执行下载音频任务: task_id={task_id}, url={url}")

        # 在事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                video_download_service.download_audio_task(task_id, url, work_dir)
            )
        finally:
            loop.close()

        logger.info(f"[Celery Task] 下载音频任务完成: task_id={task_id}")
    except Exception as e:
        logger.error(
            f"[Celery Task] 下载音频任务失败: task_id={task_id}, error={str(e)}",
            exc_info=True,
        )
        # 更新任务状态为失败
        try:
            task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                message="下载音频任务失败",
            )
        except Exception as update_error:
            logger.error(
                f"[Celery Task] 更新任务状态失败: task_id={task_id}, error={str(update_error)}",
                exc_info=True,
            )
        # 重新抛出异常以触发重试
        raise

