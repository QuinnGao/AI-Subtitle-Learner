"""
FastAPI 应用主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    health,
    transcribe,
    subtitle,
    synthesis,
    video,
    batch,
)
from app.core.llm.health_check import get_health_checker, _global_health_checker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    get_health_checker(check_interval=60)  # 1分钟检查一次
    yield
    # 关闭时执行

    if _global_health_checker:
        _global_health_checker.stop_periodic_check()


app = FastAPI(
    title="视频字幕处理 API",
    description="基于 FastAPI 的视频字幕处理后端服务",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(transcribe.router, prefix="/api/v1", tags=["转录"])
app.include_router(subtitle.router, prefix="/api/v1", tags=["字幕处理"])
app.include_router(synthesis.router, prefix="/api/v1", tags=["视频合成"])
app.include_router(video.router, prefix="/api/v1", tags=["视频"])
app.include_router(batch.router, prefix="/api/v1", tags=["批量处理"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "视频字幕处理 API",
        "version": "1.0.0",
        "docs": "/docs",
    }
