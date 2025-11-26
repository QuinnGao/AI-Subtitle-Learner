"""
视频相关路由
"""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.video_download import (
    AnalyzeResponse,
    SubtitleTaskInfo,
)
from app.services.task_manager import get_task_manager
from app.celery.tasks.video_tasks import download_audio_task
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger

router = APIRouter()
task_manager = get_task_manager()
logger = setup_logger("video_router")


@router.post("/video/analyze", response_model=AnalyzeResponse)
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
        message = "Task created, starting audio download..."

        # 发送 Celery 任务到队列
        download_audio_task.delay(task_id, url, None)
        logger.info(f"任务 {task_id} 已发送到 Celery 队列")

        task_response = AnalyzeResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message=message,
        )

        return task_response
    except Exception as e:
        logger.error(f"创建音频下载任务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/analyze/{task_id}", response_model=AnalyzeResponse)
async def get_video_analyze_task_status(task_id: str):
    """获取视频分析任务状态（传统轮询方式）

    注意：推荐使用 `/video/analyze/{task_id}/stream` SSE 端点以获得更好的性能和实时性。
    """
    logger.debug(f"查询任务状态: task_id={task_id}")
    return await _get_task_status_data(task_id)


async def _get_task_status_data(task_id: str) -> AnalyzeResponse:
    """获取任务状态数据（内部函数，用于轮询和 SSE）

    统一计算整个 analyze 任务的进度：
    - 视频下载阶段：0-30%
    - 转录阶段：30-70%
    - 字幕处理阶段：70-100%
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 从 TaskManager 获取关联的转录任务ID和字幕任务ID（从数据库字段获取）
    transcribe_task_id = task_manager.get_task_relation(task_id, "transcribe_task_id")
    subtitle_task_id = task_manager.get_task_relation(task_id, "subtitle_task_id")

    # 解析 message 中的其他信息（兼容旧格式，但不包含任务ID）
    video_path = task.output_path
    subtitle_path = None
    thumbnail_path = None
    subtitle_task = None

    # 统一计算整个 analyze 任务的进度
    unified_progress = task.progress
    unified_message = task.message

    # 获取转录任务状态
    transcribe_task_obj = None
    if transcribe_task_id:
        transcribe_task_obj = task_manager.get_task(transcribe_task_id)

    # 获取字幕任务状态
    subtitle_task_obj = None
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
            if (
                subtitle_task_obj.status == TaskStatus.COMPLETED
                and subtitle_task_obj.output_path
            ):
                subtitle_path = subtitle_task_obj.output_path

    # 根据子任务状态统一计算进度
    # 视频下载阶段：0-30%，转录阶段：30-70%，字幕处理阶段：70-100%

    # 检查失败状态（优先级最高）
    failed_task = next(
        (
            (t, base_progress, error_msg)
            for t, base_progress, error_msg in [
                (task, 0, "任务失败"),
                (subtitle_task_obj, 70, "字幕处理失败"),
                (transcribe_task_obj, 30, "转录失败"),
            ]
            if t and t.status == TaskStatus.FAILED
        ),
        None,
    )

    if failed_task:
        task_obj, base_progress, default_msg = failed_task
        unified_progress = task_obj.progress or base_progress
        unified_message = (
            task_obj.error or task_obj.message or unified_message or default_msg
        )
        final_status = TaskStatus.FAILED
        final_error = task_obj.error or task.error
    # 检查完成状态
    elif task.status == TaskStatus.COMPLETED or (
        subtitle_task_obj and subtitle_task_obj.status == TaskStatus.COMPLETED
    ):
        unified_progress = 100
        unified_message = unified_message or "Analysis completed"
        final_status = TaskStatus.COMPLETED
    # 检查运行中状态
    elif subtitle_task_obj and subtitle_task_obj.status == TaskStatus.RUNNING:
        # 字幕处理中：70% + 字幕任务进度的30%
        subtitle_progress = subtitle_task_obj.progress or 0
        unified_progress = min(70 + int(subtitle_progress * 0.3), 99)
        unified_message = (
            subtitle_task_obj.message or unified_message or "Processing subtitles"
        )
        final_status = task.status
    elif transcribe_task_obj and transcribe_task_obj.status == TaskStatus.COMPLETED:
        # 转录完成
        unified_progress = 70 if subtitle_task_id else 100
        unified_message = unified_message or (
            "Transcription completed, waiting for subtitle processing"
            if subtitle_task_id
            else "Transcription completed"
        )
        final_status = task.status
    elif transcribe_task_obj and transcribe_task_obj.status == TaskStatus.RUNNING:
        # 转录中：30% + 转录任务进度的40%
        transcribe_progress = transcribe_task_obj.progress or 0
        unified_progress = min(30 + int(transcribe_progress * 0.4), 69)
        unified_message = (
            transcribe_task_obj.message or unified_message or "Transcribing"
        )
        final_status = task.status
    elif task.status == TaskStatus.RUNNING:
        # 视频下载中：0-30%
        video_progress = task.progress or 0
        unified_progress = min(int(video_progress * 0.3), 29)
        unified_message = unified_message or "Downloading audio"
        final_status = task.status
    elif task.status == TaskStatus.PENDING:
        unified_progress = 0
        unified_message = unified_message or "Task created, waiting for processing"
        final_status = task.status
    else:
        # 其他状态
        unified_progress = task.progress or 0
        final_status = task.status

    # 统一设置错误信息（失败状态已在上面处理）
    final_error = task.error

    return AnalyzeResponse(
        task_id=task.task_id,
        status=final_status,
        queued_at=task.queued_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        progress=unified_progress,  # 使用统一计算的进度
        message=unified_message,
        error=final_error,
        output_path=task.output_path,
        video_path=video_path,
        subtitle_path=subtitle_path,
        thumbnail_path=thumbnail_path,
        subtitle_task=subtitle_task,
    )


async def _stream_task_status(task_id: str) -> AsyncGenerator[str, None]:
    """流式推送任务状态更新（SSE）"""
    last_status = None
    last_progress = -1
    first_message = True  # 标记是否是第一次发送消息

    try:
        while True:
            try:
                status_data = await _get_task_status_data(task_id)

                # 第一次连接时立即发送当前状态，或者状态/进度变化时发送更新
                if (
                    first_message
                    or status_data.status != last_status
                    or status_data.progress != last_progress
                ):
                    # SSE 格式：data: {json}\n\n
                    # 使用 mode='json' 确保 datetime 对象被正确序列化为 ISO 格式字符串
                    data_json = status_data.model_dump_json(exclude_none=True)
                    yield f"data: {data_json}\n\n"

                    first_message = False
                    last_status = status_data.status
                    last_progress = status_data.progress

                    # 如果任务完成或失败，停止推送
                    if status_data.status in (
                        TaskStatus.COMPLETED,
                        TaskStatus.FAILED,
                        TaskStatus.CANCELLED,
                    ):
                        logger.info(
                            f"任务 {task_id} 状态为 {status_data.status}，停止 SSE 推送"
                        )
                        break

                # 等待 1 秒后再次检查
                await asyncio.sleep(1)

            except HTTPException as e:
                # 任务不存在，发送错误并停止
                error_data = {"error": e.detail}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                break
            except Exception as e:
                logger.error(f"SSE 推送错误: {task_id}, error={str(e)}", exc_info=True)
                error_data = {"error": str(e)}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(1)

    except asyncio.CancelledError:
        logger.info(f"SSE 连接已取消: {task_id}")
    except Exception as e:
        logger.error(f"SSE 流异常: {task_id}, error={str(e)}", exc_info=True)


@router.get("/video/analyze/{task_id}/stream")
async def stream_video_analyze_task_status(task_id: str):
    """通过 Server-Sent Events (SSE) 流式推送任务状态更新

    这是一个更高效的替代轮询的方案。客户端可以使用 EventSource API 接收实时更新。

    示例（JavaScript）:
    ```javascript
    const eventSource = new EventSource('/api/v1/video/analyze/{task_id}/stream');
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('任务状态:', data);
    };
    ```
    """
    logger.info(f"SSE 连接建立: task_id={task_id}")

    return StreamingResponse(
        _stream_task_status(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )
