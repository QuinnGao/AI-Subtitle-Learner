"""
应用配置模块
"""
import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    app_name: str = "视频字幕处理 API"
    debug: bool = False
    log_level: str = "INFO"

    # 工作目录
    work_dir: Path = Path("./workspace")
    model_dir: Path = Path("./models")
    log_dir: Path = Path("./logs")

    # 文件上传配置
    max_upload_size: int = 1024 * 1024 * 1024 * 5  # 5GB
    allowed_video_extensions: list[str] = [
        ".mp4", ".webm", ".ogm", ".mov", ".mkv", ".avi",
        ".wmv", ".flv", ".m4v", ".ts", ".mpg", ".mpeg"
    ]
    allowed_audio_extensions: list[str] = [
        ".aac", ".ac3", ".aiff", ".amr", ".ape", ".au",
        ".flac", ".m4a", ".mp2", ".mp3", ".mka", ".oga",
        ".ogg", ".opus", ".ra", ".wav", ".wma"
    ]
    allowed_subtitle_extensions: list[str] = [".srt", ".ass", ".vtt"]

    # 任务配置
    max_concurrent_tasks: int = 5
    task_timeout: int = 3600  # 1小时

    # 默认配置
    default_transcribe_model: str = "faster_whisper"
    default_transcribe_language: str = "auto"
    default_output_format: str = "srt"

    # LLM API 配置（从环境变量读取，支持 Docker 和本地运行）
    llm_api_base: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    
    # 兼容旧的环境变量名称
    openai_api_base: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None

    # 字幕配置（从环境变量读取）
    max_word_count_cjk: int = 25
    max_word_count_english: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# 确保目录存在
settings.work_dir.mkdir(parents=True, exist_ok=True)
settings.model_dir.mkdir(parents=True, exist_ok=True)
settings.log_dir.mkdir(parents=True, exist_ok=True)

# 导出路径常量（供 core 模块使用）
CACHE_PATH = settings.work_dir / "cache"
LOG_PATH = settings.log_dir
MODEL_PATH = settings.model_dir
RESOURCE_PATH = Path("./resources")  # 资源文件路径
ASSETS_PATH = RESOURCE_PATH / "assets"  # 资源文件路径
SUBTITLE_STYLE_PATH = Path("./resources/subtitle_styles")  # 字幕样式路径

# 确保缓存目录存在
CACHE_PATH.mkdir(parents=True, exist_ok=True)
RESOURCE_PATH.mkdir(parents=True, exist_ok=True)
ASSETS_PATH.mkdir(parents=True, exist_ok=True)
SUBTITLE_STYLE_PATH.mkdir(parents=True, exist_ok=True)

# 日志级别（供 core 模块使用）
LOG_LEVEL = settings.log_level

# 版本号（供 core 模块使用）
VERSION = "1.0.0"

# LLM API 配置（从环境变量读取，优先使用新名称，兼容旧名称）
LLM_API_BASE = settings.llm_api_base or settings.openai_api_base or os.getenv("LLM_API_BASE") or os.getenv("OPENAI_API_BASE")
LLM_API_KEY = settings.llm_api_key or settings.openai_api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
LLM_MODEL = settings.llm_model or settings.openai_model or os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL")

