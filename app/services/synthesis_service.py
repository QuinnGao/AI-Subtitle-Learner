"""
视频合成服务
"""

from pathlib import Path

from app.schemas.synthesis import SynthesisRequest
from app.services.task_manager import TaskManager, get_task_manager
from app.core.utils.video_utils import add_subtitles
from app.core.entities import VideoQualityEnum

task_manager = get_task_manager()


class SynthesisService:
    """视频合成服务"""

    def __init__(self):
        self.task_manager = task_manager

    async def process_synthesis_task(self, task_id: str, request: SynthesisRequest):
        """处理视频合成任务"""
        try:
            self.task_manager.update_task(
                task_id, status="running", message="开始合成视频"
            )

            # 验证文件
            video_path = Path(request.video_path)
            subtitle_path = Path(request.subtitle_path)

            if not video_path.exists():
                raise ValueError("视频文件不存在")
            if not subtitle_path.exists():
                raise ValueError("字幕文件不存在")

            # 检查是否需要生成视频
            if not request.config.need_video:
                self.task_manager.update_task(
                    task_id,
                    status="completed",
                    progress=100,
                    message="不需要合成视频，跳过",
                )
                return

            # 确定输出路径
            output_path = request.output_path or str(
                video_path.parent / f"【卡卡】{video_path.stem}.mp4"
            )

            # 获取视频质量参数
            # 将字符串转换为枚举值
            quality_map = {
                "ultra_high": VideoQualityEnum.ULTRA_HIGH,
                "high": VideoQualityEnum.HIGH,
                "medium": VideoQualityEnum.MEDIUM,
                "low": VideoQualityEnum.LOW,
            }
            video_quality_enum = quality_map.get(
                request.config.video_quality.value, VideoQualityEnum.MEDIUM
            )
            crf = video_quality_enum.get_crf()
            preset = video_quality_enum.get_preset()

            # 调用视频合成函数
            self.task_manager.update_task(task_id, progress=5, message="正在合成视频")

            add_subtitles(
                str(video_path),
                str(subtitle_path),
                output_path,
                crf=crf,
                preset=preset,
                soft_subtitle=request.config.soft_subtitle,
                progress_callback=lambda value, msg: self._progress_callback(
                    task_id, value, msg
                ),
            )

            self.task_manager.update_task(
                task_id,
                status="completed",
                progress=100,
                message="视频合成完成",
                output_path=output_path,
            )

        except Exception as e:
            self.task_manager.update_task(
                task_id, status="failed", error=str(e), message="视频合成失败"
            )

    def _progress_callback(self, task_id: str, value, message: str):
        """视频合成进度回调函数"""
        try:
            progress_value = int(value)
            # 将进度映射到 5-100 范围（5% 开始，95% 结束）
            mapped_progress = min(5 + int(progress_value * 0.95), 100)
            self.task_manager.update_task(
                task_id,
                progress=mapped_progress,
                message=message or "正在合成",
            )
        except (ValueError, TypeError):
            # 如果 value 不是数字，使用默认进度
            self.task_manager.update_task(
                task_id, message=message or "正在合成"
            )
