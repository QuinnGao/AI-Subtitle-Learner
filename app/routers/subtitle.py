"""
字幕处理相关路由
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from app.core.constants import TaskStatus
from app.schemas.subtitle import SubtitleResponse, TranscribeTaskInfo, VideoTaskInfo
from app.services.task_manager import get_task_manager
from app.core.utils.logger import setup_logger

router = APIRouter()
task_manager = get_task_manager()
logger = setup_logger("subtitle_router")


@router.get("/subtitle/{task_id}", response_model=SubtitleResponse)
async def get_subtitle_task(task_id: str):
    """获取字幕处理任务状态"""
    logger.info(f"查询任务状态: task_id={task_id}")
    task = task_manager.get_task(task_id)
    if not task:
        logger.warning(f"任务不存在: task_id={task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")
    logger.info(
        f"任务状态: task_id={task_id}, status={task.status}, progress={task.progress}"
    )

    # 从 TaskManager 获取关联的转录任务ID和视频下载任务ID
    transcribe_task_id = task_manager.get_task_relation(task_id, "transcribe_task_id")
    video_task_id = task_manager.get_task_relation(task_id, "video_task_id")

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

    # 获取视频下载任务状态（如果存在）
    video_task = None
    if video_task_id:
        video_task_obj = task_manager.get_task(video_task_id)
        if video_task_obj:
            video_task = VideoTaskInfo(
                task_id=video_task_id,
                status=video_task_obj.status,
                progress=video_task_obj.progress,
                message=video_task_obj.message,
            )
            logger.debug(
                f"[任务 {task_id}] 关联视频下载任务状态: "
                f"video_task_id={video_task_id}, status={video_task_obj.status}"
            )
        else:
            logger.warning(f"视频下载任务不存在: video_task_id={video_task_id}")

    # 转换为 SubtitleResponse
    return SubtitleResponse(
        task_id=task.task_id,
        status=task.status,
        queued_at=task.queued_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        progress=task.progress,
        message=task.message,
        error=task.error,
        output_path=task.output_path,
        transcribe_task=transcribe_task,
        video_task=video_task,
    )


@router.get("/subtitle/{task_id}/content")
async def get_subtitle_content(task_id: str):
    """获取字幕文件内容（JSON 格式）

    Args:
        task_id: 任务ID

    Returns:
        包含 task_id 和 content（JSON 数组）的字典
    """

    logger.info(f"获取字幕内容请求: task_id={task_id}")
    task = task_manager.get_task(task_id)
    if not task:
        logger.warning(f"获取字幕内容失败，任务不存在: task_id={task_id}")
        raise HTTPException(status_code=404, detail="任务不存在")

    # 如果任务失败或取消，返回错误
    if task.status == TaskStatus.FAILED or task.status == TaskStatus.CANCELLED:
        error_msg = task.error or "任务失败"
        logger.warning(
            f"获取字幕内容失败，任务已失败或取消: task_id={task_id}, status={task.status}, error={error_msg}"
        )
        raise HTTPException(status_code=400, detail=f"任务失败: {error_msg}")

    # 如果任务未完成（pending 或 running），继续等待或返回空内容
    if task.status != TaskStatus.COMPLETED:
        logger.info(
            f"任务尚未完成，返回空内容: task_id={task_id}, status={task.status}"
        )
        return {
            "task_id": task_id,
            "content": [],
        }

    if not task.output_path:
        logger.warning(f"获取字幕内容失败，缓存文件路径不存在: task_id={task_id}")
        raise HTTPException(status_code=404, detail="缓存文件路径不存在")

    try:
        cache_path = Path(task.output_path)

        if not cache_path.exists():
            logger.warning(f"缓存文件不存在: {cache_path}")
            raise HTTPException(status_code=404, detail="缓存文件不存在")

        with open(cache_path, "r", encoding="utf-8") as f:
            content = json.load(f)
        logger.info(f"成功从缓存读取 JSON 文件: task_id={task_id}, file={cache_path}")
        return {
            "task_id": task_id,
            "content": content,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"从缓存读取 JSON 文件失败: task_id={task_id}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"从缓存读取 JSON 文件失败: {str(e)}"
        )
