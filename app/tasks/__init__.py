"""
Celery 任务模块
"""
from app.tasks.video_tasks import (
    download_audio_task,
)
from app.tasks.transcribe_tasks import (
    transcribe_task,
)
from app.tasks.subtitle_tasks import (
    subtitle_task,
)

__all__ = [
    "download_audio_task",
    "transcribe_task",
    "subtitle_task",
]


