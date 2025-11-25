"""
字幕处理相关 Celery 任务
"""

import asyncio

from app.celery import celery_app
from app.celery.services.subtitle_service import SubtitleService
from app.services.task_manager import get_task_manager
from app.schemas.subtitle import SubtitleRequest
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger

logger = setup_logger("subtitle_tasks")
task_manager = get_task_manager()
subtitle_service = SubtitleService()


@celery_app.task(
    name="app.celery.tasks.subtitle.process",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def subtitle_task(self, task_id: str, request_dict: dict):
    """字幕处理任务（Celery 任务）

    Args:
        task_id: 任务ID
        request_dict: SubtitleRequest 的字典表示
    """
    try:
        logger.info(f"[Celery Task] 开始执行字幕处理任务: task_id={task_id}")

        # 从字典重建 SubtitleRequest 对象
        from app.schemas.subtitle import SubtitleRequest, SubtitleConfig

        request = SubtitleRequest(**request_dict)

        # 在事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                subtitle_service.process_subtitle_task(task_id, request)
            )
        finally:
            loop.close()

        logger.info(f"[Celery Task] 字幕处理任务完成: task_id={task_id}")

        # 字幕任务完成后，更新视频任务状态
        video_task_id = task_manager.get_task_relation(task_id, "video_task_id")
        if video_task_id:
            subtitle_task_obj = task_manager.get_task(task_id)
            if subtitle_task_obj and subtitle_task_obj.status == TaskStatus.COMPLETED:
                video_task = task_manager.get_task(video_task_id)
                if video_task:
                    task_manager.update_task(
                        video_task_id,
                        status=TaskStatus.COMPLETED,
                        progress=100,
                        message="音频下载、转录和字幕处理完成",
                        output_path=video_task.output_path,
                    )
                    logger.info(
                        f"[Celery Task] 视频任务完成: video_task_id={video_task_id}"
                    )
    except Exception as e:
        logger.error(
            f"[Celery Task] 字幕处理任务失败: task_id={task_id}, error={str(e)}",
            exc_info=True,
        )
        # 更新任务状态为失败
        task_manager.update_task(
            task_id,
            error=str(e),
            message="字幕处理任务失败",
        )
        # 重新抛出异常以触发重试
        raise

