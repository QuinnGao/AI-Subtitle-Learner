"""
批量处理相关路由
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.schemas.batch import BatchTaskRequest, BatchTaskResponse
from app.services.task_manager import TaskManager, get_task_manager
from app.services.batch_service import BatchService

router = APIRouter()
task_manager = get_task_manager()
batch_service = BatchService()


@router.post("/batch", response_model=BatchTaskResponse)
async def create_batch_task(
    request: BatchTaskRequest, background_tasks: BackgroundTasks
):
    """创建批量处理任务"""
    try:
        task_id = task_manager.create_task()
        task_response = BatchTaskResponse(
            task_id=task_id,
            status="pending",
            message="批量任务已创建",
            total_files=len(request.file_paths),
        )

        # 在后台执行批量处理任务
        background_tasks.add_task(
            batch_service.process_batch_task,
            task_id,
            request,
        )

        return task_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{task_id}", response_model=BatchTaskResponse)
async def get_batch_task(task_id: str):
    """获取批量处理任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

