"""
转录相关 Celery 任务
"""

import asyncio

from app.celery import celery_app
from app.celery.services.transcribe_service import TranscribeService
from app.services.task_manager import get_task_manager
from app.celery.tasks.subtitle_tasks import subtitle_task
from app.schemas.transcribe import TranscribeRequest
from app.schemas.subtitle import SubtitleRequest, SubtitleConfig
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger
from app.core.storage import get_storage

logger = setup_logger("transcribe_tasks")
task_manager = get_task_manager()
transcribe_service = TranscribeService()


@celery_app.task(
    name="app.celery.tasks.transcribe.transcribe",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def transcribe_task(self, task_id: str, request_dict: dict):
    """转录任务（Celery 任务）

    Args:
        task_id: 任务ID
        request_dict: TranscribeRequest 的字典表示
    """
    try:
        logger.info(f"[Celery Task] 开始执行转录任务: task_id={task_id}")

        # 从字典重建 TranscribeRequest 对象
        request = TranscribeRequest(**request_dict)

        # 在事件循环中运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                transcribe_service.process_transcribe_task(task_id, request)
            )
        finally:
            loop.close()

        logger.info(f"[Celery Task] 转录任务完成: task_id={task_id}")

        # 转录任务完成后，检查是否有关联的视频任务，如果有则创建字幕任务
        video_task_id = task_manager.get_task_relation(task_id, "video_task_id")
        if video_task_id:
            transcribe_task_obj = task_manager.get_task(task_id)
            if (
                transcribe_task_obj
                and transcribe_task_obj.status == TaskStatus.COMPLETED
            ):
                # 从视频任务获取音频文件路径（MinIO 路径）
                video_task = task_manager.get_task(video_task_id)
                if video_task and video_task.output_path:
                    audio_file_path = video_task.output_path
                    # 检查 MinIO 中是否存在该文件
                    storage = get_storage()
                    if storage.file_exists(audio_file_path):
                        logger.info(
                            f"[Celery Task] 转录任务完成，开始创建字幕处理任务: "
                            f"transcribe_task_id={task_id}, video_task_id={video_task_id}, "
                            f"audio_file_path={audio_file_path}"
                        )
                        _create_subtitle_task(video_task_id, task_id, audio_file_path)

    except Exception as e:
        logger.error(
            f"[Celery Task] 转录任务失败: task_id={task_id}, error={str(e)}",
            exc_info=True,
        )
        # 更新任务状态为失败
        try:
            task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                message="转录任务失败",
            )
        except Exception as update_error:
            logger.error(
                f"[Celery Task] 更新任务状态失败: task_id={task_id}, error={str(update_error)}",
                exc_info=True,
            )
        # 重新抛出异常以触发重试
        raise


def _create_subtitle_task(
    video_task_id: str, transcribe_task_id: str, audio_file_path: str
):
    """创建字幕处理任务"""
    try:
        # 创建字幕处理任务
        subtitle_task_id = task_manager.create_task(task_type="subtitle")

        # 建立任务关联关系
        task_manager.set_task_relations(
            video_task_id,
            {
                "subtitle_task_id": subtitle_task_id,
            },
        )
        task_manager.set_task_relations(
            subtitle_task_id,
            {
                "video_task_id": video_task_id,
                "transcribe_task_id": transcribe_task_id,
            },
        )

        logger.info(
            f"[Celery Task] 创建字幕处理任务: subtitle_task_id={subtitle_task_id}, "
            f"video_task_id={video_task_id}"
        )

        # 更新视频任务消息
        task_manager.update_task(
            video_task_id,
            message="音频下载和转录完成，等待字幕处理...",
        )

        # 创建字幕处理请求（默认启用优化和分割，启用翻译）
        subtitle_config = SubtitleConfig(
            need_optimize=True,  # 启用AI优化
            need_translate=True,  # 启用翻译
            need_split=True,  # 启用分割
        )

        subtitle_request = SubtitleRequest(
            output_path=None,  # 自动生成输出路径（MinIO 路径）
            config=subtitle_config,
        )

        # 发送 Celery 任务到队列
        subtitle_task.delay(
            subtitle_task_id,
            subtitle_request.model_dump(),  # 转换为字典
        )

        logger.info(
            f"[Celery Task] 字幕处理任务已发送到队列: subtitle_task_id={subtitle_task_id}"
        )
    except Exception as e:
        logger.error(
            f"[Celery Task] 创建字幕处理任务失败: {str(e)}",
            exc_info=True,
        )
