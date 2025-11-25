"""
应用配置模块
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # 忽略未定义的额外字段
    )

    # 基础配置
    log_level: str = "INFO"

    # 工作目录
    work_dir: Path = Path("./workspace")
    model_dir: Path = Path("./models")
    log_dir: Path = Path("./logs")

    # LLM API 配置（从环境变量读取，支持 Docker 和本地运行）
    llm_api_base: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None

    # 兼容旧的环境变量名称
    openai_api_base: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None

    # 数据库配置
    database_url: str = "postgresql://subtitle:subtitle@localhost:5432/subtitle"

    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"

    # Celery 配置
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    # MinIO 配置
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_name: str = "subtitle-files"

    # 字幕配置（从环境变量读取）
    max_word_count_cjk: int = 25
    max_word_count_english: int = 20


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

# LLM API 配置（从环境变量读取，优先使用新名称，兼容旧名称）
LLM_API_BASE = (
    settings.llm_api_base
    or settings.openai_api_base
    or os.getenv("LLM_API_BASE")
    or os.getenv("OPENAI_API_BASE")
)
LLM_API_KEY = (
    settings.llm_api_key
    or settings.openai_api_key
    or os.getenv("LLM_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
LLM_MODEL = (
    settings.llm_model
    or settings.openai_model
    or os.getenv("LLM_MODEL")
    or os.getenv("OPENAI_MODEL")
)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", settings.database_url)

# Redis 配置
REDIS_URL = os.getenv("REDIS_URL", settings.redis_url)

# Celery 配置
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", settings.celery_broker_url)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND", settings.celery_result_backend
)

# MinIO 配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", settings.minio_endpoint)
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", settings.minio_access_key)
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", settings.minio_secret_key)
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", settings.minio_bucket_name)
