"""
视频相关路由
"""

from fastapi import APIRouter, HTTPException

from app.schemas.video_download import (
    VideoDownloadResponse,
    SubtitleTaskInfo,
    TranscribeTaskInfo,
)
from app.services.task_manager import get_task_manager
from app.celery.tasks.video_tasks import download_audio_task
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger

router = APIRouter()
task_manager = get_task_manager()
logger = setup_logger("video_router")


@router.post("/video/analyze", response_model=VideoDownloadResponse)
async def start_analysis(url: str):
    """开始任务分析接口

    通过 URL 开始分析任务（下载音频并转录）。

    Args:
        url: YouTube URL
    """
    try:
        logger.info(f"收到音频下载请求（通过URL）: url={url}")

        # 创建下载任务
        task_id = task_manager.create_task(
            task_type="video_download",
            video_url=url,
        )
        logger.info(f"创建音频下载任务: task_id={task_id}")

        # 构建消息
        message = "任务已创建，开始下载音频..."

        # 发送 Celery 任务到队列
        download_audio_task.delay(task_id, url, None)
        logger.info(f"任务 {task_id} 已发送到 Celery 队列")

        task_response = VideoDownloadResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message=message,
        )

        return task_response
    except Exception as e:
        logger.error(f"创建音频下载任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/analyze/{task_id}", response_model=VideoDownloadResponse)
async def get_video_analyze_task_status(task_id: str):
    """获取视频分析任务状态"""

    logger.debug(f"查询任务状态: task_id={task_id}")
    task = task_manager.get_task(task_id)
    if not task:
        logger.warning(f"任务不存在: task_id={task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    logger.debug(
        f"任务状态: task_id={task_id}, status={task.status}, progress={task.progress}"
    )

    # 首先从 TaskManager 获取关联的转录任务ID和字幕任务ID
    transcribe_task_id = task_manager.get_task_relation(task_id, "transcribe_task_id")
    subtitle_task_id = task_manager.get_task_relation(task_id, "subtitle_task_id")

    # 解析 message 中的信息（兼容旧格式）
    # 格式：视频下载完成|transcribe_task_id|subtitle_task_id|video_path|subtitle_path|thumbnail_path
    video_path = task.output_path
    subtitle_path = None
    thumbnail_path = None
    subtitle_task = None

    if task.message and "|" in task.message:
        parts = task.message.split("|")
        base_message = parts[0]  # 基础消息（如"视频下载完成"）

        # 新格式：包含任务ID
        if len(parts) >= 6:
            # 格式：视频下载完成|transcribe_task_id|subtitle_task_id|video_path|subtitle_path|thumbnail_path
            # 如果 TaskManager 中没有，从 message 中获取（兼容）
            if not transcribe_task_id:
                transcribe_task_id = parts[1] if parts[1] else None
            if not subtitle_task_id:
                subtitle_task_id = parts[2] if parts[2] else None
            video_path = parts[3] if parts[3] else task.output_path
            subtitle_path = parts[4] if parts[4] else None
            thumbnail_path = parts[5] if parts[5] else None
        elif len(parts) >= 4:
            # 旧格式兼容：视频下载完成|video_path|subtitle_path|thumbnail_path
            video_path = parts[1] if parts[1] else task.output_path
            subtitle_path = parts[2] if parts[2] else None
            thumbnail_path = parts[3] if parts[3] else None

    # 获取转录任务状态（如果存在）
    transcribe_task = None
    if transcribe_task_id:
        transcribe_task_obj = task_manager.get_task(transcribe_task_id)
        if transcribe_task_obj:
            transcribe_task = TranscribeTaskInfo(
                task_id=transcribe_task_id,
                status=transcribe_task_obj.status,
                progress=transcribe_task_obj.progress,
                message=transcribe_task_obj.message,
            )
            logger.debug(
                f"[任务 {task_id}] 关联转录任务状态: "
                f"transcribe_task_id={transcribe_task_id}, status={transcribe_task_obj.status}"
            )
        else:
            logger.warning(f"转录任务不存在: transcribe_task_id={transcribe_task_id}")

    # 获取字幕任务状态
    if subtitle_task_id:
        subtitle_task_obj = task_manager.get_task(subtitle_task_id)
        if subtitle_task_obj:
            subtitle_task = SubtitleTaskInfo(
                task_id=subtitle_task_id,
                status=subtitle_task_obj.status,
                progress=subtitle_task_obj.progress,
                message=subtitle_task_obj.message,
                output_path=subtitle_task_obj.output_path,
            )
            # 如果字幕任务已完成，更新 subtitle_path
            if (
                subtitle_task_obj.status == TaskStatus.COMPLETED
                and subtitle_task_obj.output_path
            ):
                subtitle_path = subtitle_task_obj.output_path
        else:
            logger.warning(f"字幕任务不存在: subtitle_task_id={subtitle_task_id}")

    # 转换为 VideoDownloadResponse
    return VideoDownloadResponse(
        task_id=task.task_id,
        status=task.status,
        queued_at=task.queued_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        progress=task.progress,
        message=base_message if task.message and "|" in task.message else task.message,
        error=task.error,
        output_path=task.output_path,
        video_path=video_path,
        subtitle_path=subtitle_path,
        thumbnail_path=thumbnail_path,
        transcribe_task=transcribe_task,
        subtitle_task=subtitle_task,
    )
