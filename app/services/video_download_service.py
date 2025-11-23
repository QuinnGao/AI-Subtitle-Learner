"""
视频下载服务
"""

import asyncio
import os
import re
from pathlib import Path
from typing import Optional

import yt_dlp

from app.config import settings
from app.services.task_manager import get_task_manager
from app.services.transcribe_service import TranscribeService
from app.services.subtitle_service import SubtitleService
from app.schemas.transcribe import TranscribeRequest, TranscribeConfig, TranscribeModel
from app.schemas.subtitle import SubtitleRequest, SubtitleConfig
from app.core.constants import TaskStatus
from app.core.utils.logger import setup_logger

task_manager = get_task_manager()
logger = setup_logger("video_download_service")


class VideoDownloadService:
    """视频下载服务"""

    def __init__(self):
        self.task_manager = task_manager
        self.transcribe_service = TranscribeService()
        self.subtitle_service = SubtitleService()

    def sanitize_filename(self, name: str, replacement: str = "_") -> str:
        """清理文件名中不允许的字符"""
        # 定义不允许的字符
        forbidden_chars = r'<>:"/\\|?*'

        # 替换不允许的字符
        sanitized = re.sub(f"[{re.escape(forbidden_chars)}]", replacement, name)

        # 移除控制字符
        sanitized = re.sub(r"[\0-\31]", "", sanitized)

        # 去除文件名末尾的空格和点
        sanitized = sanitized.rstrip(" .")

        # 限制文件名长度
        max_length = 255
        if len(sanitized) > max_length:
            base, ext = os.path.splitext(sanitized)
            base_max_length = max_length - len(ext)
            sanitized = base[:base_max_length] + ext

        # 处理Windows保留名称
        windows_reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        name_without_ext = os.path.splitext(sanitized)[0].upper()
        if name_without_ext in windows_reserved_names:
            sanitized = f"{sanitized}_"

        # 如果文件名为空，返回默认名称
        if not sanitized:
            sanitized = "default_filename"

        return sanitized

    def _check_existing_audio(self, work_dir: Path, video_title: str) -> Optional[Path]:
        """检查是否已存在音频文件

        Args:
            work_dir: 工作目录
            video_title: 视频标题

        Returns:
            如果找到已存在的音频文件，返回文件路径；否则返回 None
        """
        if not work_dir.exists():
            return None

        # 支持的音频文件扩展名
        audio_extensions = [".mp3", ".m4a", ".mp4", ".webm", ".ogg", ".opus"]

        # 查找工作目录中的所有音频文件
        for ext in audio_extensions:
            # 尝试精确匹配文件名
            potential_file = work_dir / f"{video_title}{ext}"
            if potential_file.exists() and potential_file.is_file():
                return potential_file

            # 尝试查找包含视频标题的文件
            for file_path in work_dir.glob(f"*{video_title}*{ext}"):
                if file_path.is_file():
                    return file_path

        # 如果找不到精确匹配，查找工作目录中所有音频文件
        # 按修改时间排序，返回最新的
        all_audio_files = []
        for ext in audio_extensions:
            all_audio_files.extend(work_dir.glob(f"*{ext}"))

        if all_audio_files:
            # 按修改时间排序，返回最新的
            all_audio_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            logger.info(
                f"在工作目录中找到 {len(all_audio_files)} 个音频文件，使用最新的: {all_audio_files[0]}"
            )
            return all_audio_files[0]

        return None

    def progress_hook(self, d, task_id: str):
        """下载进度回调函数"""
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "0%")
            speed = d.get("_speed_str", "0B/s")

            # 提取百分比和速度的纯文本
            clean_percent = (
                percent.replace("\x1b[0;94m", "")
                .replace("\x1b[0m", "")
                .strip()
                .replace("%", "")
            )
            clean_speed = speed.replace("\x1b[0;32m", "").replace("\x1b[0m", "").strip()

            try:
                progress = int(float(clean_percent))
                message = f"下载进度: {clean_percent}%  速度: {clean_speed}"
                self.task_manager.update_task(
                    task_id, progress=progress, message=message
                )
            except (ValueError, TypeError):
                pass

    async def download_audio_task(
        self,
        task_id: str,
        url: str,
        work_dir: Optional[str] = None,
    ):
        """下载音频任务"""
        logger.info(f"[任务 {task_id}] 开始下载音频: {url}")

        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.RUNNING,
                message="开始下载音频",
            )

            # 使用配置的工作目录或提供的目录
            if work_dir is None:
                work_dir = str(settings.work_dir)

            # 初始化 ydl 选项
            initial_ydl_opts = {
                "outtmpl": {
                    "default": "%(title).200s.%(ext)s",  # 限制文件名最长200个字符
                },
                "progress_hooks": [
                    lambda d: self.progress_hook(d, task_id)
                ],  # 下载进度钩子
                "quiet": True,  # 禁用日志输出
                "no_warnings": True,  # 禁用警告信息
                "noprogress": True,
                "ignoreerrors": True,
                # 只下载音频：选择最佳音频格式，优先 m4a/mp3
                "format": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best",
                # 添加后处理器：转换为 mp3 格式
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

            # 在线程池中执行同步阻塞操作，避免阻塞事件循环
            logger.info(f"[任务 {task_id}] 在线程池中执行音频下载...")
            download_result = await asyncio.to_thread(
                self._download_video_sync,
                task_id,
                url,
                work_dir,
                initial_ydl_opts,
            )

            video_file_path = download_result["video_file_path"]

            logger.info(f"[任务 {task_id}] 音频下载完成: {video_file_path}")

            # 更新任务状态为运行中（等待转录任务完成）
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.RUNNING,
                progress=50,
                message="音频下载完成，等待转录...",
                output_path=video_file_path,
            )

            # 使用 WhisperX 进行转录，获取精准时间戳
            # 只有转录任务完成，音频下载任务才算完成
            if video_file_path and Path(video_file_path).exists():
                try:
                    logger.info(
                        f"[任务 {task_id}] 开始使用 WhisperX 进行转录，获取精准时间戳"
                    )

                    # 创建转录任务
                    transcribe_task_id = self.task_manager.create_task()

                    # 批量绑定关联关系：音频下载任务 -> 转录任务
                    self.task_manager.set_task_relations(
                        task_id,
                        {
                            "transcribe_task_id": transcribe_task_id,
                        },
                    )
                    # 转录任务 -> 音频下载任务（反向关联）
                    self.task_manager.set_task_relations(
                        transcribe_task_id,
                        {
                            "video_task_id": task_id,
                        },
                    )

                    logger.info(
                        f"[任务 {task_id}] 创建转录任务关联: "
                        f"video_task_id={task_id}, transcribe_task_id={transcribe_task_id}"
                    )

                    # 更新音频下载任务消息，包含转录任务ID
                    task = self.task_manager.get_task(task_id)
                    if task:
                        task.message = f"音频下载完成，等待转录...|{transcribe_task_id}||{video_file_path or ''}"

                    # 创建转录请求，使用 WhisperX（默认使用 CPU）
                    transcribe_config = TranscribeConfig(
                        transcribe_model=TranscribeModel.WHISPERX,
                        transcribe_language="auto",
                        need_word_time_stamp=True,  # WhisperX 总是提供词级时间戳
                        whisperx_model="large-v3",
                        whisperx_device="cpu",  # 默认使用 CPU
                        whisperx_compute_type="float32",  # CPU 使用 float32
                        whisperx_batch_size=16,
                    )

                    transcribe_request = TranscribeRequest(
                        file_path=video_file_path,
                        output_path=None,  # 自动生成输出路径
                        config=transcribe_config,
                    )

                    # 在后台执行转录任务（FastAPI 环境下总是有事件循环）
                    asyncio.create_task(
                        self._process_transcribe_task(
                            task_id,
                            transcribe_task_id,
                            transcribe_request,
                        )
                    )

                    logger.info(
                        f"[任务 {task_id}] WhisperX 转录任务已创建: {transcribe_task_id}"
                    )
                except Exception as e:
                    logger.error(
                        f"[任务 {task_id}] 创建 WhisperX 转录任务失败: {str(e)}",
                        exc_info=True,
                    )
                    # 转录任务创建失败，标记音频下载任务为失败
                    self.task_manager.update_task(
                        task_id,
                        status=TaskStatus.FAILED,
                        error=f"创建转录任务失败: {str(e)}",
                        message="音频下载完成，但创建转录任务失败",
                    )
            else:
                # 音频文件不存在，标记为失败
                self.task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    progress=0,
                    message="音频下载失败：文件不存在",
                    error="音频文件下载失败",
                )
                logger.error(f"[任务 {task_id}] 音频文件不存在: {video_file_path}")
                return

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[任务 {task_id}] 音频下载失败: {error_msg}", exc_info=True)
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=error_msg,
                message="音频下载失败",
            )

    async def _process_transcribe_task(
        self,
        task_id: str,
        transcribe_task_id: str,
        transcribe_request: TranscribeRequest,
    ):
        """处理转录任务"""
        try:
            # 1. 执行转录
            logger.info(
                f"[任务 {task_id}] 开始执行 WhisperX 转录任务: {transcribe_task_id}"
            )

            await self.transcribe_service.process_transcribe_task(
                transcribe_task_id, transcribe_request
            )

            # 轮询等待任务完成
            max_wait_time = 3600  # 最多等待1小时
            poll_interval = 0.5  # 每0.5秒检查一次
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                transcribe_task = self.task_manager.get_task(transcribe_task_id)

                if not transcribe_task:
                    logger.error(
                        f"[任务 {task_id}] 转录任务不存在: {transcribe_task_id}"
                    )
                    return

                # 检查任务状态
                if transcribe_task.status == TaskStatus.FAILED:
                    error_msg = transcribe_task.error or "转录失败"
                    logger.error(f"[任务 {task_id}] WhisperX 转录失败: {error_msg}")
                    # 转录失败，标记音频下载任务为失败
                    self.task_manager.update_task(
                        task_id,
                        status=TaskStatus.FAILED,
                        error=f"转录失败: {error_msg}",
                        message="音频下载完成，但转录失败",
                    )
                    return

                if (
                    transcribe_task.status == TaskStatus.COMPLETED
                    and transcribe_task.output_path
                ):
                    subtitle_file_path = transcribe_task.output_path

                    # 验证文件是否存在
                    if not Path(subtitle_file_path).exists():
                        logger.error(
                            f"[任务 {task_id}] 转录输出文件不存在: {subtitle_file_path}"
                        )
                        return

                    logger.info(
                        f"[任务 {task_id}] WhisperX 转录完成: {subtitle_file_path}"
                    )
                    break

                # 如果任务还在运行或等待中，继续等待
                if transcribe_task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    await asyncio.sleep(poll_interval)
                    elapsed_time += poll_interval
                    continue

                # 其他状态，记录警告并退出
                logger.warning(
                    f"[任务 {task_id}] 转录任务状态异常: "
                    f"status={transcribe_task.status}, "
                    f"output_path={transcribe_task.output_path}, "
                    f"message={transcribe_task.message}"
                )
                return

            # 检查是否超时
            if elapsed_time >= max_wait_time:
                logger.error(f"[任务 {task_id}] 转录任务超时: {transcribe_task_id}")
                # 转录超时，标记音频下载任务为失败
                self.task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error="转录任务超时",
                    message="音频下载完成，但转录超时",
                )
                return

            # 再次获取任务，确保获取到最终结果
            transcribe_task = self.task_manager.get_task(transcribe_task_id)

            if (
                not transcribe_task
                or transcribe_task.status != TaskStatus.COMPLETED
                or not transcribe_task.output_path
            ):
                logger.error(
                    f"[任务 {task_id}] 无法获取转录结果: "
                    f"task_exists={transcribe_task is not None}, "
                    f"status={transcribe_task.status if transcribe_task else 'None'}, "
                    f"output_path={transcribe_task.output_path if transcribe_task else 'None'}"
                )
                # 无法获取转录结果，标记音频下载任务为失败
                self.task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error="无法获取转录结果",
                    message="音频下载完成，但无法获取转录结果",
                )
                return

            # 转录任务完成，创建字幕处理任务（AI优化、翻译等）
            logger.info(f"[任务 {task_id}] 转录任务完成，开始创建字幕处理任务")

            subtitle_file_path = transcribe_task.output_path

            # 创建字幕处理任务
            subtitle_task_id = self.task_manager.create_task()

            # 建立任务关联关系
            self.task_manager.set_task_relations(
                task_id,
                {
                    "subtitle_task_id": subtitle_task_id,
                },
            )
            self.task_manager.set_task_relations(
                subtitle_task_id,
                {
                    "video_task_id": task_id,
                    "transcribe_task_id": transcribe_task_id,
                },
            )

            logger.info(
                f"[任务 {task_id}] 创建字幕处理任务: subtitle_task_id={subtitle_task_id}"
            )

            # 更新音频下载任务消息，包含字幕任务ID
            audio_task = self.task_manager.get_task(task_id)
            if audio_task:
                audio_task.message = f"音频下载和转录完成，等待字幕处理...|{transcribe_task_id}|{subtitle_task_id}||{audio_task.output_path or ''}"

            # 创建字幕处理请求（默认启用优化和分割，不启用翻译）
            subtitle_config = SubtitleConfig(
                need_optimize=True,  # 启用AI优化
                need_translate=True,  # 不启用翻译
                need_split=True,  # 启用分割
            )

            subtitle_request = SubtitleRequest(
                subtitle_path=subtitle_file_path,
                video_path=None,  # 音频文件，不需要视频路径
                output_path=None,  # 自动生成输出路径
                config=subtitle_config,
            )

            # 在后台执行字幕处理任务
            asyncio.create_task(
                self._process_subtitle_task(
                    task_id,
                    subtitle_task_id,
                    subtitle_request,
                )
            )

            logger.info(f"[任务 {task_id}] 字幕处理任务已创建: {subtitle_task_id}")
        except Exception as e:
            logger.error(
                f"[任务 {task_id}] 转录处理失败: {str(e)}",
                exc_info=True,
            )
            # 转录失败，标记音频下载任务为失败
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=f"转录失败: {str(e)}",
                message="音频下载完成，但转录失败",
            )

    async def _process_subtitle_task(
        self,
        task_id: str,
        subtitle_task_id: str,
        subtitle_request: SubtitleRequest,
    ):
        """处理字幕任务"""
        try:
            # 执行字幕处理
            logger.info(f"[任务 {task_id}] 开始执行字幕处理任务: {subtitle_task_id}")

            await self.subtitle_service.process_subtitle_task(
                subtitle_task_id, subtitle_request
            )

            # 轮询等待任务完成
            max_wait_time = 3600  # 最多等待1小时
            poll_interval = 0.5  # 每0.5秒检查一次
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                subtitle_task = self.task_manager.get_task(subtitle_task_id)

                if not subtitle_task:
                    logger.error(f"[任务 {task_id}] 字幕任务不存在: {subtitle_task_id}")
                    return

                # 检查任务状态
                if subtitle_task.status == TaskStatus.FAILED:
                    error_msg = subtitle_task.error or "字幕处理失败"
                    logger.error(f"[任务 {task_id}] 字幕处理失败: {error_msg}")
                    # 字幕处理失败，但转录已完成，标记音频下载任务为完成（带警告）
                    audio_task = self.task_manager.get_task(task_id)
                    audio_file_path = audio_task.output_path if audio_task else None
                    self.task_manager.update_task(
                        task_id,
                        status=TaskStatus.COMPLETED,
                        progress=100,
                        message=f"音频下载和转录完成，但字幕处理失败: {error_msg}",
                        output_path=audio_file_path,
                    )
                    return

                if (
                    subtitle_task.status == TaskStatus.COMPLETED
                    and subtitle_task.output_path
                ):
                    logger.info(
                        f"[任务 {task_id}] 字幕处理完成: {subtitle_task.output_path}"
                    )
                    break

                # 如果任务还在运行或等待中，继续等待
                if subtitle_task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    await asyncio.sleep(poll_interval)
                    elapsed_time += poll_interval
                    continue

                # 其他状态，记录警告并退出
                logger.warning(
                    f"[任务 {task_id}] 字幕任务状态异常: "
                    f"status={subtitle_task.status}, "
                    f"output_path={subtitle_task.output_path}, "
                    f"message={subtitle_task.message}"
                )
                return

            # 检查是否超时
            if elapsed_time >= max_wait_time:
                logger.error(f"[任务 {task_id}] 字幕任务超时: {subtitle_task_id}")
                # 字幕超时，但转录已完成，标记音频下载任务为完成（带警告）
                audio_task = self.task_manager.get_task(task_id)
                audio_file_path = audio_task.output_path if audio_task else None
                self.task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="音频下载和转录完成，但字幕处理超时",
                    output_path=audio_file_path,
                )
                return

            # 再次获取任务，确保获取到最终结果
            subtitle_task = self.task_manager.get_task(subtitle_task_id)

            if (
                not subtitle_task
                or subtitle_task.status != TaskStatus.COMPLETED
                or not subtitle_task.output_path
            ):
                logger.error(
                    f"[任务 {task_id}] 无法获取字幕处理结果: "
                    f"task_exists={subtitle_task is not None}, "
                    f"status={subtitle_task.status if subtitle_task else 'None'}, "
                    f"output_path={subtitle_task.output_path if subtitle_task else 'None'}"
                )
                # 无法获取字幕结果，但转录已完成，标记音频下载任务为完成（带警告）
                audio_task = self.task_manager.get_task(task_id)
                audio_file_path = audio_task.output_path if audio_task else None
                self.task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    message="音频下载和转录完成，但无法获取字幕处理结果",
                    output_path=audio_file_path,
                )
                return

            # 字幕处理任务完成，标记音频下载任务为完成
            logger.info(f"[任务 {task_id}] 字幕处理任务完成，标记音频下载任务为完成")

            # 获取音频文件路径
            audio_task = self.task_manager.get_task(task_id)
            audio_file_path = audio_task.output_path if audio_task else None

            self.task_manager.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                message="音频下载、转录和字幕处理完成",
                output_path=audio_file_path,
            )
        except Exception as e:
            logger.error(
                f"[任务 {task_id}] 字幕处理失败: {str(e)}",
                exc_info=True,
            )
            # 字幕处理失败，但转录已完成，标记音频下载任务为完成（带警告）
            audio_task = self.task_manager.get_task(task_id)
            audio_file_path = audio_task.output_path if audio_task else None
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                message=f"音频下载和转录完成，但字幕处理失败: {str(e)}",
                output_path=audio_file_path,
            )

    def _download_video_sync(
        self, task_id: str, url: str, work_dir: str, initial_ydl_opts: dict
    ):
        """同步下载音频的函数，包含所有阻塞操作"""
        with yt_dlp.YoutubeDL(initial_ydl_opts) as ydl:
            # 提取视频信息（不下载）
            logger.info(f"[任务 {task_id}] 提取视频信息...")
            info_dict = ydl.extract_info(url, download=False)

            # 设置动态下载文件夹为视频标题
            video_title = self.sanitize_filename(info_dict.get("title", "MyVideo"))
            video_work_dir = Path(work_dir) / self.sanitize_filename(video_title)
            video_work_dir.mkdir(parents=True, exist_ok=True)

            # 检查是否已存在音频文件
            logger.info(f"[任务 {task_id}] 检查是否已存在音频文件...")
            existing_audio = self._check_existing_audio(video_work_dir, video_title)
            if existing_audio:
                logger.info(f"[任务 {task_id}] 发现已存在的音频文件: {existing_audio}")
                return {
                    "video_file_path": str(existing_audio),
                    "subtitle_file_path": None,
                    "thumbnail_file_path": None,
                }

            # 设置 yt-dlp 下载选项
            ydl_opts = {
                "paths": {
                    "home": str(video_work_dir),
                },
            }
            # 更新 yt-dlp 的配置
            ydl.params.update(ydl_opts)

            # 使用 process_info 进行下载
            logger.info(f"[任务 {task_id}] 开始下载文件...")
            ydl.process_info(info_dict)

            # 获取文件路径（可能是视频或音频）
            # 如果使用了 postprocessors（如音频转换），文件名可能会改变
            video_file_path = Path(ydl.prepare_filename(info_dict))

            # 如果文件不存在，可能是被 postprocessors 转换了（如 .m4a -> .mp3）
            if not video_file_path.exists():
                # 尝试查找转换后的文件（如 .mp3）
                base_path = video_file_path.parent / video_file_path.stem
                for ext in [".mp3", ".m4a", ".mp4", ".webm"]:
                    potential_path = base_path.with_suffix(ext)
                    if potential_path.exists():
                        video_file_path = potential_path
                        break
                else:
                    # 如果还是找不到，尝试在工作目录中查找最新的音频/视频文件
                    work_dir_path = Path(work_dir)
                    all_files = list(work_dir_path.rglob("*"))
                    # 按修改时间排序，找到最新的音频或视频文件
                    media_files = [
                        f
                        for f in all_files
                        if f.is_file()
                        and f.suffix.lower()
                        in [".mp3", ".m4a", ".mp4", ".webm", ".mkv"]
                    ]
                    if media_files:
                        media_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        video_file_path = media_files[0]

            if video_file_path.exists():
                video_file_path = str(video_file_path)
            else:
                video_file_path = None

            return {
                "video_file_path": video_file_path,
                "subtitle_file_path": None,
                "thumbnail_file_path": None,
            }
