"""
转录服务
"""

import asyncio
import tempfile
from pathlib import Path

from app.schemas.transcribe import TranscribeRequest
from app.services.task_manager import get_task_manager
from app.core.asr import transcribe
from app.core.entities import TranscribeConfig as CoreTranscribeConfig
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger
from app.core.entities import (
    TranscribeModelEnum,
    TranscribeOutputFormatEnum,
)
from app.core.storage import get_storage

task_manager = get_task_manager()
logger = setup_logger("transcribe_service")


class TranscribeService:
    """转录服务"""

    def __init__(self):
        self.task_manager = task_manager

    async def process_transcribe_task(self, task_id: str, request: TranscribeRequest):
        """处理转录任务"""
        logger.info(f"[任务 {task_id}] 开始处理转录任务")

        try:
            # 1. 更新任务状态为 running
            self._update_task_running(task_id)

            # 2. 从数据库获取文件路径（优先从关联的视频任务获取）
            file_path = self._get_file_path_from_db(task_id, None)

            # 3. 转换配置
            core_config = self._prepare_config(task_id, request.config)

            # 4. 准备音频文件路径
            audio_path = self._prepare_audio_path(task_id, file_path)

            # 5. 执行转录
            asr_data = await self._execute_transcribe(task_id, audio_path, core_config)

            # 6. 保存字幕文件
            output_path = await self._save_subtitle_file(
                task_id, file_path, asr_data, request.output_path
            )

            # 7. 更新任务状态为 completed
            self._update_task_completed(task_id, output_path)

            logger.info(f"[任务 {task_id}] 转录任务完成: {output_path}")

        except Exception as e:
            self._handle_error(task_id, e)

    def _update_task_running(self, task_id: str) -> None:
        """更新任务状态为 running"""
        logger.info(f"[任务 {task_id}] 更新任务状态为 running")
        self.task_manager.update_task(
            task_id, status=TaskStatus.RUNNING, message="开始转录"
        )

    def _get_file_path_from_db(
        self, task_id: str, fallback_file_path: str | None
    ) -> Path:
        """从数据库获取文件路径

        优先从关联的视频任务的 output_path 获取文件路径
        如果没有关联的视频任务，则使用 fallback_file_path
        """
        # 1. 尝试从关联的视频任务获取文件路径
        video_task_id = self.task_manager.get_task_relation(task_id, "video_task_id")
        if video_task_id:
            video_task = self.task_manager.get_task(video_task_id)
            if video_task and video_task.output_path:
                file_path = video_task.output_path
                logger.info(
                    f"[任务 {task_id}] 从关联视频任务获取文件路径: "
                    f"video_task_id={video_task_id}, file_path={file_path}"
                )
                file_path_obj = Path(file_path)
                # 验证文件是否存在（本地文件或 MinIO）
                if self._validate_file_path(file_path_obj):
                    return file_path_obj
                else:
                    logger.warning(
                        f"[任务 {task_id}] 关联视频任务的文件路径不存在，尝试使用备用路径"
                    )

        # 2. 如果没有关联的视频任务或文件不存在，使用 fallback_file_path
        if fallback_file_path:
            logger.info(f"[任务 {task_id}] 使用备用文件路径: {fallback_file_path}")
            file_path_obj = Path(fallback_file_path)
            if not self._validate_file_path(file_path_obj):
                error_msg = f"文件不存在: {file_path_obj}"
                logger.error(f"[任务 {task_id}] {error_msg}")
                raise ValueError(error_msg)
            return file_path_obj

        # 3. 如果都没有，抛出错误
        error_msg = (
            f"无法获取文件路径: task_id={task_id}, 没有关联的视频任务且没有提供文件路径"
        )
        logger.error(f"[任务 {task_id}] {error_msg}")
        raise ValueError(error_msg)

    def _validate_file_path(self, file_path: Path) -> bool:
        """验证文件路径是否存在（本地文件或 MinIO）"""
        file_path_str = str(file_path)

        # 先检查是否是本地文件
        if file_path.exists():
            return True

        # 再检查是否是 MinIO 对象
        storage = get_storage()
        if storage.file_exists(file_path_str):
            return True

        return False

    def _prepare_config(self, task_id: str, config) -> CoreTranscribeConfig:
        """准备并转换配置"""
        logger.info(
            f"[任务 {task_id}] 转换配置: model={config.transcribe_model}, "
            f"language={config.transcribe_language}, "
            f"need_word_time_stamp={config.need_word_time_stamp}"
        )

        core_config = self._convert_config(config)
        logger.info(
            f"[任务 {task_id}] 配置转换完成: model={core_config.transcribe_model}, "
            f"language={core_config.transcribe_language}"
        )
        return core_config

    def _prepare_audio_path(self, task_id: str, file_path: Path) -> str:
        """准备音频文件路径

        如果文件路径是 MinIO 对象名称，则下载到临时文件
        否则直接使用本地文件路径
        """
        file_path_str = str(file_path)

        # 检查是否是 MinIO 对象（通过检查文件是否存在来判断）
        storage = get_storage()
        if storage.file_exists(file_path_str):
            # 是 MinIO 对象，下载到临时文件
            logger.info(f"[任务 {task_id}] 从 MinIO 下载音频文件: {file_path_str}")
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(file_path_str).suffix
            ) as tmp_file:
                tmp_path = tmp_file.name
            storage.download_file(file_path_str, tmp_path)
            logger.info(f"[任务 {task_id}] 音频文件已下载到临时文件: {tmp_path}")
            return tmp_path
        else:
            # 是本地文件路径
            audio_path = file_path_str
            logger.info(f"[任务 {task_id}] 直接使用本地音频文件: {audio_path}")
            return audio_path

    async def _execute_transcribe(
        self, task_id: str, audio_path: str, core_config: CoreTranscribeConfig
    ):
        """执行转录"""
        logger.info(
            f"[任务 {task_id}] 开始转录: model={core_config.transcribe_model}, "
            f"language={core_config.transcribe_language}"
        )

        self.task_manager.update_task(task_id, progress=10, message="语音转录中")

        asr_data = await asyncio.to_thread(
            transcribe,
            audio_path,
            core_config,
            lambda value, msg: self._progress_callback(task_id, value, msg),
        )

        logger.info(f"[任务 {task_id}] 转录完成，共 {len(asr_data.segments)} 条字幕")
        return asr_data

    async def _save_subtitle_file(
        self, task_id: str, file_path: Path, asr_data, output_path: str | None
    ) -> str:
        """保存字幕文件到 MinIO"""
        output_path = output_path or str(file_path.parent / f"{file_path.stem}.srt")
        logger.info(f"[任务 {task_id}] 保存字幕文件到 MinIO: {output_path}")

        # 保存到 MinIO（save 方法内部会处理）
        final_path = await asyncio.to_thread(asr_data.save, output_path, use_minio=True)

        # 验证文件是否保存成功（检查 MinIO）
        storage = get_storage()
        if storage.file_exists(final_path):
            logger.info(f"[任务 {task_id}] 字幕文件保存成功到 MinIO: {final_path}")
        else:
            logger.warning(
                f"[任务 {task_id}] 字幕文件保存后不存在于 MinIO: {final_path}"
            )

        return final_path

    def _update_task_completed(self, task_id: str, output_path: str) -> None:
        """更新任务状态为 completed"""
        logger.info(f"[任务 {task_id}] 更新任务状态为 completed")
        self.task_manager.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message="转录完成",
            output_path=output_path,
        )

    def _handle_error(self, task_id: str, error: Exception) -> None:
        """处理错误"""
        error_msg = str(error)
        logger.error(f"[任务 {task_id}] 转录任务失败: {error_msg}", exc_info=True)

        self.task_manager.update_task(
            task_id, status=TaskStatus.FAILED, error=error_msg, message="转录失败"
        )
        logger.error(f"[任务 {task_id}] 任务状态已更新为 failed")

    def _convert_config(self, config) -> CoreTranscribeConfig:
        """转换配置格式"""
        # 这里需要将 API 的配置转换为 core 模块的配置格式
        # 由于 core 模块使用的是枚举类型，需要进行映射

        return CoreTranscribeConfig(
            transcribe_model=TranscribeModelEnum[config.transcribe_model.value.upper()],
            transcribe_language=config.transcribe_language,
            need_word_time_stamp=config.need_word_time_stamp,
            output_format=TranscribeOutputFormatEnum[
                config.output_format.value.upper()
            ],
            whisperx_model=config.whisperx_model,
            whisperx_device=config.whisperx_device or "cpu",  # 默认使用 CPU
            whisperx_compute_type=config.whisperx_compute_type
            or "float32",  # CPU 默认 float32
            whisperx_batch_size=config.whisperx_batch_size,
        )

    def _progress_callback(self, task_id: str, value: float, message: str):
        """转录进度回调函数"""
        progress = 10 + int(value * 0.8)  # 调整进度范围：10% - 90%
        self.task_manager.update_task(task_id, progress=progress, message=message)
        logger.debug(f"[任务 {task_id}] 转录进度: {progress}% - {message}")
