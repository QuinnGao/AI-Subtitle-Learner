"""
字幕处理相关路由
"""

import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.constants import TaskStatus
from app.core.storage import get_storage
from app.core.utils.logger import setup_logger
from app.services.task_manager import get_task_manager

router = APIRouter()
task_manager = get_task_manager()
logger = setup_logger("subtitle_router")


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
        logger.warning(f"获取字幕内容失败，输出文件路径不存在: task_id={task_id}")
        raise HTTPException(status_code=404, detail="输出文件路径不存在")

    try:
        output_path = task.output_path
        storage = get_storage()

        # 检查文件是否在 MinIO 中
        if not storage.file_exists(output_path):
            logger.warning(f"文件不存在于 MinIO: task_id={task_id}, path={output_path}")
            raise HTTPException(status_code=404, detail="文件不存在于 MinIO")

        # 从 MinIO 下载到临时文件
        logger.info(f"从 MinIO 下载字幕文件: task_id={task_id}, path={output_path}")
        tmp_file = tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".json", encoding="utf-8"
        )
        tmp_path = tmp_file.name
        tmp_file.close()

        try:
            storage.download_file(output_path, tmp_path)
            logger.info(
                f"字幕文件已下载到临时文件: task_id={task_id}, tmp_path={tmp_path}"
            )

            with open(tmp_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            logger.info(
                f"成功从 MinIO 读取 JSON 文件: task_id={task_id}, path={output_path}"
            )
            return {
                "task_id": task_id,
                "content": content,
            }
        finally:
            # 清理临时文件
            if tmp_path and Path(tmp_path).exists():
                Path(tmp_path).unlink(missing_ok=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"读取字幕文件失败: task_id={task_id}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"读取字幕文件失败: {str(e)}")
