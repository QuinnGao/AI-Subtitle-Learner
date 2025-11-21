"""
使用 loguru 的日志配置模块
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from ...config import LOG_LEVEL, LOG_PATH


def _get_log_level(level: str) -> str:
    """将日志级别转换为 loguru 格式"""
    level_map = {
        "DEBUG": "DEBUG",
        "INFO": "INFO",
        "WARNING": "WARNING",
        "ERROR": "ERROR",
        "CRITICAL": "CRITICAL",
    }
    return level_map.get(str(level).upper(), "INFO")


# 全局日志配置标志
_logger_configured = False


def setup_logger(
    name: str,
    level: Optional[str] = None,
    info_fmt: Optional[str] = None,  # 保留参数以兼容旧代码
    default_fmt: Optional[str] = None,  # 保留参数以兼容旧代码
    datefmt: Optional[str] = None,  # 保留参数以兼容旧代码
    log_file: Optional[str] = None,
    console_output: bool = True,
):
    """
    创建并配置一个 loguru 日志记录器。

    参数：
    - name: 日志记录器的名称（用于标识日志来源）
    - level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - info_fmt: 保留参数，loguru 使用统一格式
    - default_fmt: 保留参数，loguru 使用统一格式
    - datefmt: 保留参数，loguru 使用统一格式
    - log_file: 日志文件路径（默认使用 LOG_PATH/app.log）
    - console_output: 是否输出到控制台（默认 True）

    返回：
    - loguru.Logger: 配置好的日志记录器
    """
    global _logger_configured

    # 只配置一次全局 logger
    if not _logger_configured:
        # 移除默认的 handler
        logger.remove()

        # 获取日志级别
        log_level = _get_log_level(level or LOG_LEVEL)

        # 控制台输出格式（简化，只显示必要信息）
        def format_console(record):
            try:
                time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S")
                # 获取消息并转义 HTML 标签，避免 loguru 误解析
                message = str(record.get("message", "")).replace("<", "&lt;").replace(">", "&gt;")
                # 只显示时间和消息，错误级别才显示级别
                if record["level"].name in ["ERROR", "CRITICAL", "WARNING"]:
                    level_name = record["level"].name
                    return f"<green>{time_str}</green> | <level>{level_name}</level> | {message}\n"
                else:
                    return f"<green>{time_str}</green> | {message}\n"
            except Exception:
                return "{time} | {level} | {message}\n"

        # 文件输出格式（简化，只显示必要信息）
        def format_file(record):
            try:
                time_str = record["time"].strftime("%Y-%m-%d %H:%M:%S")
                level_name = record["level"].name
                message = record.get("message", "")
                # 只显示时间、级别和消息
                return f"{time_str} | {level_name} | {message}\n"
            except Exception:
                return "{time} | {level} | {message}\n"

        # 添加控制台输出
        if console_output:

            logger.add(
                sys.stderr,
                format=format_console,
                level=log_level,
                colorize=True,
                backtrace=True,
                diagnose=True,
                enqueue=True,  # 线程安全，确保后台任务日志能正确输出
            )

        # 添加文件输出
        if log_file is None:
            log_file = str(LOG_PATH / "app.log")

        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_file,
            format=format_file,
            level=log_level,
            rotation="10 MB",  # 文件大小达到 10MB 时轮转
            retention="5 days",  # 保留 5 天的日志
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            backtrace=True,
            diagnose=True,
            enqueue=True,  # 线程安全，确保后台任务日志能正确写入文件
            colorize=False,  # 文件输出不需要颜色
        )

        # 禁用第三方库的日志以减少噪音
        logger.disable("urllib3")
        logger.disable("requests")
        logger.disable("openai")
        logger.disable("httpx")
        logger.disable("httpcore")
        logger.disable("ssl")
        logger.disable("certifi")

        _logger_configured = True

    # 返回带名称绑定的 logger（使用 bind 来标识日志来源）
    # 如果 name 不在 extra 中，使用默认值
    return logger.bind(name=name) if name else logger
