"""
视频服务
"""
import tempfile
from pathlib import Path

from app.schemas.common import VideoInfo, AudioStreamInfo
from app.core.utils.video_utils import get_video_info as core_get_video_info
from app.core.entities import VideoInfo as CoreVideoInfo


class VideoService:
    """视频服务"""

    async def get_video_info(self, file_path: str) -> VideoInfo:
        """获取视频信息"""
        # 生成缩略图到临时文件
        temp_dir = tempfile.gettempdir()
        file_name = Path(file_path).stem
        thumbnail_path = f"{temp_dir}/{file_name}_thumbnail.jpg"

        # 使用 core 模块的函数
        core_video_info: CoreVideoInfo = core_get_video_info(
            file_path, thumbnail_path=thumbnail_path
        )

        # 转换格式
        audio_streams = [
            AudioStreamInfo(
                index=stream.index,
                codec=stream.codec,
                language=stream.language,
                title=stream.title,
            )
            for stream in core_video_info.audio_streams
        ]

        return VideoInfo(
            file_name=core_video_info.file_name,
            file_path=core_video_info.file_path,
            width=core_video_info.width,
            height=core_video_info.height,
            fps=core_video_info.fps,
            duration_seconds=core_video_info.duration_seconds,
            bitrate_kbps=core_video_info.bitrate_kbps,
            video_codec=core_video_info.video_codec,
            audio_codec=core_video_info.audio_codec,
            audio_sampling_rate=core_video_info.audio_sampling_rate,
            thumbnail_path=core_video_info.thumbnail_path,
            audio_streams=audio_streams,
        )

