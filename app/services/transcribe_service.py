"""
转录服务
"""

import asyncio
import sys
from pathlib import Path

from app.schemas.transcribe import TranscribeRequest
from app.services.task_manager import get_task_manager
from app.core.asr import transcribe
from app.core.entities import TranscribeConfig as CoreTranscribeConfig
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger

task_manager = get_task_manager()
logger = setup_logger("transcribe_service")


class TranscribeService:
    """转录服务"""

    def __init__(self):
        self.task_manager = task_manager

    async def process_transcribe_task(self, task_id: str, request: TranscribeRequest):
        """处理转录任务"""
        logger.info(f"[任务 {task_id}] 开始处理转录任务")
        sys.stderr.flush()

        try:
            logger.info(f"[任务 {task_id}] 更新任务状态为 running")
            self.task_manager.update_task(
                task_id, status=TaskStatus.RUNNING, message="开始转录"
            )
            sys.stderr.flush()

            # 验证文件
            file_path = Path(request.file_path)
            logger.info(f"[任务 {task_id}] 验证文件: {file_path}")
            sys.stderr.flush()

            if not file_path.exists():
                error_msg = f"文件不存在: {file_path}"
                logger.error(f"[任务 {task_id}] {error_msg}")
                sys.stderr.flush()
                raise ValueError(error_msg)

            logger.info(f"[任务 {task_id}] 文件验证通过: {file_path}")
            sys.stderr.flush()

            # 转换配置
            logger.info(
                f"[任务 {task_id}] 转换配置: model={request.config.transcribe_model}, "
                f"language={request.config.transcribe_language}, "
                f"need_word_time_stamp={request.config.need_word_time_stamp}"
            )
            sys.stderr.flush()

            core_config = self._convert_config(request.config)
            logger.info(
                f"[任务 {task_id}] 配置转换完成: model={core_config.transcribe_model}, "
                f"language={core_config.transcribe_language}"
            )
            sys.stderr.flush()

            # 直接使用音频文件，无需转换为 WAV（ASR 支持 MP3 等格式）
            audio_path = str(file_path)
            logger.info(f"[任务 {task_id}] 直接使用音频文件: {audio_path}")
            sys.stderr.flush()

            # 进行转录（在线程池中执行，避免阻塞事件循环）
            logger.info(
                f"[任务 {task_id}] 开始转录: model={core_config.transcribe_model}, "
                f"language={core_config.transcribe_language}"
            )
            sys.stderr.flush()

            self.task_manager.update_task(task_id, progress=10, message="语音转录中")

            asr_data = await asyncio.to_thread(
                transcribe,
                audio_path,
                core_config,
                lambda value, msg: self._progress_callback(task_id, value, msg),
            )

            logger.info(
                f"[任务 {task_id}] 转录完成，共 {len(asr_data.segments)} 条字幕"
            )
            sys.stderr.flush()

            # 保存字幕文件（在线程池中执行）
            output_path = request.output_path or str(
                file_path.parent / f"{file_path.stem}.srt"
            )
            logger.info(f"[任务 {task_id}] 保存字幕文件到: {output_path}")
            sys.stderr.flush()

            await asyncio.to_thread(asr_data.save, output_path)

            # 验证文件是否保存成功
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                logger.info(
                    f"[任务 {task_id}] 字幕文件保存成功: {output_path}, 大小: {file_size} 字节"
                )
            else:
                logger.warning(f"[任务 {task_id}] 字幕文件保存后不存在: {output_path}")
            sys.stderr.flush()

            logger.info(f"[任务 {task_id}] 更新任务状态为 completed")
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                message="转录完成",
                output_path=output_path,
            )
            sys.stderr.flush()

            logger.info(f"[任务 {task_id}] 转录任务完成: {output_path}")
            sys.stderr.flush()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[任务 {task_id}] 转录任务失败: {error_msg}", exc_info=True)
            sys.stderr.flush()

            self.task_manager.update_task(
                task_id, status=TaskStatus.FAILED, error=error_msg, message="转录失败"
            )
            logger.error(f"[任务 {task_id}] 任务状态已更新为 failed")
            sys.stderr.flush()

    def _convert_config(self, config) -> CoreTranscribeConfig:
        """转换配置格式"""
        # 这里需要将 API 的配置转换为 core 模块的配置格式
        # 由于 core 模块使用的是枚举类型，需要进行映射
        from app.core.entities import (
            TranscribeModelEnum,
            TranscribeOutputFormatEnum,
        )

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
