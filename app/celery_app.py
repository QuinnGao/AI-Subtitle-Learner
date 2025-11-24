"""
Celery 应用配置
"""
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from app.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
from app.core.utils.logger import setup_logger

logger = setup_logger("celery_app")

# 创建 Celery 应用
celery_app = Celery(
    "ai_subtitle_learner",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"],  # 包含任务模块
)

# Celery 配置
celery_app.conf.update(
    # 任务确认机制：任务完成后才从队列移除
    task_acks_late=True,
    # Worker 预取任务数（防止任务堆积在 Worker 中）
    worker_prefetch_multiplier=1,
    # 任务序列化
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["pickle", "json"],
    # 时区
    timezone="UTC",
    enable_utc=True,
    # 任务重试配置
    task_default_retry_delay=60,  # 默认重试延迟 60 秒
    task_max_retries=3,  # 最大重试次数
    # 任务超时
    task_time_limit=3600,  # 任务硬超时 1 小时
    task_soft_time_limit=3300,  # 任务软超时 55 分钟
    # 结果过期时间
    result_expires=3600,  # 结果保留 1 小时
    # 死信队列配置
    task_reject_on_worker_lost=True,
    task_acks_on_failure_or_timeout=False,
    # 路由配置
    task_routes={
        "app.tasks.video.*": {"queue": "video"},
        "app.tasks.transcribe.*": {"queue": "transcribe"},
        "app.tasks.subtitle.*": {"queue": "subtitle"},
    },
    # 默认队列
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """任务执行前处理"""
    logger.info(f"[Celery] 任务开始执行: task_id={task_id}, task={task.name}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """任务执行后处理"""
    logger.info(f"[Celery] 任务执行完成: task_id={task_id}, task={task.name}, state={state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """任务失败处理"""
    logger.error(
        f"[Celery] 任务执行失败: task_id={task_id}, exception={str(exception)}",
        exc_info=einfo,
    )


if __name__ == "__main__":
    celery_app.start()


