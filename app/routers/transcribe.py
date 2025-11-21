"""
转录相关路由
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from app.schemas.transcribe import TranscribeRequest, TranscribeResponse
from app.services.task_manager import TaskManager, get_task_manager
from app.services.transcribe_service import TranscribeService

router = APIRouter()
task_manager = get_task_manager()
transcribe_service = TranscribeService()


@router.post("/transcribe", response_model=TranscribeResponse)
async def create_transcribe_task(
    request: TranscribeRequest, background_tasks: BackgroundTasks
):
    """创建转录任务"""
    try:
        task_id = task_manager.create_task()
        task_response = TranscribeResponse(
            task_id=task_id,
            status="pending",
            message="任务已创建",
        )

        # 在后台执行转录任务
        background_tasks.add_task(
            transcribe_service.process_transcribe_task,
            task_id,
            request,
        )

        return task_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transcribe/{task_id}", response_model=TranscribeResponse)
async def get_transcribe_task(task_id: str):
    """获取转录任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/transcribe/{task_id}/download")
async def download_transcribe_result(task_id: str):
    """下载转录结果"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.output_path:
        raise HTTPException(status_code=404, detail="输出文件不存在")

    return FileResponse(
        task.output_path,
        media_type="application/octet-stream",
        filename=task.output_path.split("/")[-1],
    )

