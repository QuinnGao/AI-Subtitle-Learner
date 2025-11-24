"""
字幕处理相关路由
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from app.core.constants import TaskStatus
from app.schemas.subtitle import (
    DictionaryQueryRequest,
    DictionaryQueryResponse,
)
from app.services.task_manager import get_task_manager
from app.services.dictionary_service import DictionaryService
from app.core.utils.logger import setup_logger

router = APIRouter()
task_manager = get_task_manager()
dictionary_service = DictionaryService()
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


@router.post("/subtitle/dictionary/query", response_model=DictionaryQueryResponse)
async def query_dictionary(request: DictionaryQueryRequest):
    """查询单词的词典信息

    Args:
        request: 词典查询请求，包含单词文本、平假名、罗马字、词性等信息

    Returns:
        词典查询响应，包含单词的详细词典信息
    """
    logger.info(f"收到词典查询请求: word={request.word}")
    try:
        result = dictionary_service.query_word(
            word=request.word,
            furigana=request.furigana,
            romaji=request.romaji,
            part_of_speech=request.part_of_speech,
        )
        logger.info(f"成功查询单词: {request.word}")
        return DictionaryQueryResponse(**result)
    except Exception as e:
        logger.error(
            f"查询词典失败: word={request.word}, error={str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"查询词典失败: {str(e)}")
