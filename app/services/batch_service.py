"""
批量处理服务
"""
from pathlib import Path

from app.schemas.batch import BatchTaskRequest, BatchTaskType
from app.schemas.transcribe import TranscribeRequest
from app.schemas.subtitle import SubtitleRequest
from app.schemas.synthesis import SynthesisRequest
from app.services.task_manager import TaskManager, get_task_manager
from app.services.transcribe_service import TranscribeService
from app.services.subtitle_service import SubtitleService
from app.services.synthesis_service import SynthesisService

task_manager = get_task_manager()


class BatchService:
    """批量处理服务"""

    def __init__(self):
        self.task_manager = task_manager
        self.transcribe_service = TranscribeService()
        self.subtitle_service = SubtitleService()
        self.synthesis_service = SynthesisService()

    async def process_batch_task(self, task_id: str, request: BatchTaskRequest):
        """处理批量任务"""
        try:
            self.task_manager.update_task(
                task_id, status="running", message="开始批量处理"
            )

            total_files = len(request.file_paths)
            completed_files = 0
            failed_files = 0
            file_results = []

            for idx, file_path in enumerate(request.file_paths):
                try:
                    progress = int((idx / total_files) * 100)
                    self.task_manager.update_task(
                        task_id,
                        progress=progress,
                        message=f"处理文件 {idx + 1}/{total_files}",
                    )

                    # 根据任务类型处理
                    if request.task_type == BatchTaskType.TRANSCRIBE:
                        result = await self._process_transcribe(
                            file_path, request, idx
                        )
                    elif request.task_type == BatchTaskType.SUBTITLE:
                        result = await self._process_subtitle(
                            file_path, request, idx
                        )
                    elif request.task_type == BatchTaskType.TRANS_SUB:
                        result = await self._process_trans_sub(
                            file_path, request, idx
                        )
                    elif request.task_type == BatchTaskType.FULL_PROCESS:
                        result = await self._process_full(
                            file_path, request, idx
                        )
                    else:
                        raise ValueError(f"不支持的任务类型: {request.task_type}")

                    file_results.append(result)
                    completed_files += 1

                except Exception as e:
                    failed_files += 1
                    file_results.append(
                        {
                            "file_path": file_path,
                            "status": "failed",
                            "error": str(e),
                        }
                    )

            # 更新任务状态
            task = self.task_manager.get_task(task_id)
            if task:
                task.completed_files = completed_files
                task.failed_files = failed_files
                task.file_results = file_results

            self.task_manager.update_task(
                task_id,
                status="completed",
                progress=100,
                message="批量处理完成",
            )

        except Exception as e:
            self.task_manager.update_task(
                task_id, status="failed", error=str(e), message="批量处理失败"
            )

    async def _process_transcribe(self, file_path, request, idx):
        """处理转录任务"""
        from app.schemas.transcribe import TranscribeRequest, TranscribeConfig
        
        transcribe_request = TranscribeRequest(
            file_path=file_path,
            output_path=None,
            config=request.transcribe_config or TranscribeConfig(),
        )
        
        # 创建子任务ID
        sub_task_id = self.task_manager.create_task()
        
        try:
            await self.transcribe_service.process_transcribe_task(
                sub_task_id, transcribe_request
            )
            task = self.task_manager.get_task(sub_task_id)
            return {
                "file_path": file_path,
                "status": "completed" if task and task.status == "completed" else "failed",
                "output_path": task.output_path if task else None,
            }
        except Exception as e:
            return {
                "file_path": file_path,
                "status": "failed",
                "error": str(e),
            }

    async def _process_subtitle(self, file_path, request, idx):
        """处理字幕任务"""
        from app.schemas.subtitle import SubtitleRequest, SubtitleConfig
        
        subtitle_request = SubtitleRequest(
            subtitle_path=file_path,
            video_path=None,
            output_path=None,
            config=request.subtitle_config or SubtitleConfig(),
        )
        
        import uuid
        sub_task_id = str(uuid.uuid4())
        self.task_manager.create_task()
        
        try:
            await self.subtitle_service.process_subtitle_task(
                sub_task_id, subtitle_request
            )
            task = self.task_manager.get_task(sub_task_id)
            return {
                "file_path": file_path,
                "status": "completed" if task and task.status == "completed" else "failed",
                "output_path": task.output_path if task else None,
            }
        except Exception as e:
            return {
                "file_path": file_path,
                "status": "failed",
                "error": str(e),
            }

    async def _process_trans_sub(self, file_path, request, idx):
        """处理转录+字幕任务"""
        # 1. 先转录
        transcribe_result = await self._process_transcribe(file_path, request, idx)
        if transcribe_result["status"] != "completed":
            return transcribe_result
        
        # 2. 再处理字幕
        subtitle_result = await self._process_subtitle(
            transcribe_result.get("output_path", file_path), request, idx
        )
        
        return {
            "file_path": file_path,
            "status": subtitle_result["status"],
            "transcribe_output": transcribe_result.get("output_path"),
            "subtitle_output": subtitle_result.get("output_path"),
            "error": subtitle_result.get("error"),
        }

    async def _process_full(self, file_path, request, idx):
        """处理完整流程任务（转录+字幕+合成）"""
        # 1. 转录
        transcribe_result = await self._process_transcribe(file_path, request, idx)
        if transcribe_result["status"] != "completed":
            return transcribe_result
        
        # 2. 字幕处理
        subtitle_result = await self._process_subtitle(
            transcribe_result.get("output_path", file_path), request, idx
        )
        if subtitle_result["status"] != "completed":
            return subtitle_result
        
        # 3. 视频合成
        from app.schemas.synthesis import SynthesisRequest, SynthesisConfig
        
        synthesis_request = SynthesisRequest(
            video_path=file_path,
            subtitle_path=subtitle_result.get("output_path", ""),
            output_path=None,
            config=request.synthesis_config or SynthesisConfig(),
        )
        
        sub_task_id = self.task_manager.create_task()
        
        try:
            await self.synthesis_service.process_synthesis_task(
                sub_task_id, synthesis_request
            )
            task = self.task_manager.get_task(sub_task_id)
            return {
                "file_path": file_path,
                "status": "completed" if task and task.status == "completed" else "failed",
                "transcribe_output": transcribe_result.get("output_path"),
                "subtitle_output": subtitle_result.get("output_path"),
                "synthesis_output": task.output_path if task else None,
            }
        except Exception as e:
            return {
                "file_path": file_path,
                "status": "failed",
                "error": str(e),
            }

