"""
转录服务
"""

import asyncio
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

            # 2. 验证文件
            file_path = self._validate_file(task_id, request.file_path)

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

    def _validate_file(self, task_id: str, file_path: str) -> Path:
        """验证文件是否存在"""
        file_path_obj = Path(file_path)
        logger.info(f"[任务 {task_id}] 验证文件: {file_path_obj}")

        if not file_path_obj.exists():
            error_msg = f"文件不存在: {file_path_obj}"
            logger.error(f"[任务 {task_id}] {error_msg}")
            raise ValueError(error_msg)

        logger.info(f"[任务 {task_id}] 文件验证通过: {file_path_obj}")
        return file_path_obj

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

        直接使用音频文件，无需转换为 WAV（ASR 支持 MP3 等格式）
        """
        audio_path = str(file_path)
        logger.info(f"[任务 {task_id}] 直接使用音频文件: {audio_path}")
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
        """保存字幕文件"""
        output_path = output_path or str(file_path.parent / f"{file_path.stem}.srt")
        logger.info(f"[任务 {task_id}] 保存字幕文件到: {output_path}")

        await asyncio.to_thread(asr_data.save, output_path)

        # 验证文件是否保存成功
        if Path(output_path).exists():
            file_size = Path(output_path).stat().st_size
            logger.info(
                f"[任务 {task_id}] 字幕文件保存成功: {output_path}, 大小: {file_size} 字节"
            )
        else:
            logger.warning(f"[任务 {task_id}] 字幕文件保存后不存在: {output_path}")

        return output_path

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
