"""
视频合成相关路由
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from app.schemas.synthesis import SynthesisRequest, SynthesisResponse
from app.services.task_manager import TaskManager, get_task_manager
from app.services.synthesis_service import SynthesisService

router = APIRouter()
task_manager = get_task_manager()
synthesis_service = SynthesisService()


@router.post("/synthesis", response_model=SynthesisResponse)
async def create_synthesis_task(
    request: SynthesisRequest, background_tasks: BackgroundTasks
):
    """创建视频合成任务"""
    try:
        task_id = task_manager.create_task()
        task_response = SynthesisResponse(
            task_id=task_id,
            status="pending",
            message="任务已创建",
        )

        # 在后台执行视频合成任务
        background_tasks.add_task(
            synthesis_service.process_synthesis_task,
            task_id,
            request,
        )

        return task_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/synthesis/{task_id}", response_model=SynthesisResponse)
async def get_synthesis_task(task_id: str):
    """获取视频合成任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/synthesis/{task_id}/download")
async def download_synthesis_result(task_id: str):
    """下载视频合成结果"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.output_path:
        raise HTTPException(status_code=404, detail="输出文件不存在")

    return FileResponse(
        task.output_path,
        media_type="video/mp4",
        filename=task.output_path.split("/")[-1],
    )

