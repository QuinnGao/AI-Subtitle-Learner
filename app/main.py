"""
FastAPI 应用主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.routers import (
    health,
    subtitle,
    video,
)
from app.core.llm.health_check import get_health_checker, _global_health_checker
from app.core.utils.logger import setup_logger

logger = setup_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    health_checker = get_health_checker(check_interval=60)  # 1分钟检查一次

    # 第一次启动时直接执行一次健康检查
    try:
        health_checker.ensure_healthy(force=True)
        logger.info("启动时健康检查成功")
    except Exception as e:
        logger.warning(f"启动时健康检查失败: {e}，将在首次使用时重试")

    yield
    # 关闭时执行

    if _global_health_checker:
        _global_health_checker.stop_periodic_check()


app = FastAPI(
    title="AI Subtitle Learner API",
    description="AI-powered subtitle learning system backend service",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,  # 使用 orjson 提升 JSON 序列化性能
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, tags=["健康检查"])
app.include_router(subtitle.router, prefix="/api/v1", tags=["字幕处理"])
app.include_router(video.router, prefix="/api/v1", tags=["视频"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI Subtitle Learner API",
        "version": "1.0.0",
        "docs": "/docs",
    }
