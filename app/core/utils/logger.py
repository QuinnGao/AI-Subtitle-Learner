"""
使用 loguru 的日志配置模块
"""

import os
import sys
from pathlib import Path
from typing import Optional, TextIO

from loguru import logger

from ...config import LOG_LEVEL, LOG_PATH


def _should_disable_enqueue() -> bool:
    """检测是否应该禁用 enqueue（避免 multiprocessing 问题）

    在以下情况下禁用 enqueue：
    1. 环境变量 LOGURU_DISABLE_ENQUEUE=true
    2. 检测到 VSCode debug 环境（VSCODE_PID 存在）
    3. 检测到 multiprocessing 环境（multiprocessing.current_process().name != 'MainProcess'）
    """
    # 检查环境变量
    if os.getenv("LOGURU_DISABLE_ENQUEUE", "").lower() == "true":
        return True

    # 检查 VSCode debug 环境
    if os.getenv("VSCODE_PID") is not None:
        return True

    # 检查是否在 multiprocessing 子进程中
    try:
        import multiprocessing

        if multiprocessing.current_process().name != "MainProcess":
            return True
    except (ImportError, AttributeError):
        pass

    return False


class AutoFlushStream:
    """自动刷新的流包装器，确保日志立即输出

    这个类包装了 sys.stderr，在每次写入时自动刷新，
    避免在代码中频繁调用 sys.stderr.flush()
    """

    def __init__(self, stream: TextIO):
        self.stream = stream

    def write(self, message: str) -> int:
        """写入消息并自动刷新"""
        result = self.stream.write(message)
        self.stream.flush()
        return result

    def flush(self) -> None:
        """刷新流"""
        self.stream.flush()

    def __getattr__(self, name: str):
        """代理其他属性和方法到原始流

        这确保 loguru 可以访问流的所有属性（如 isatty, fileno 等）
        """
        return getattr(self.stream, name)


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
    log_file: Optional[str] = None,
    console_output: bool = True,
):
    """
    创建并配置一个 loguru 日志记录器。

    参数：
    - name: 日志记录器的名称（用于标识日志来源）
    - level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
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
                message = (
                    str(record.get("message", ""))
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
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

        # 检测是否应该禁用 enqueue（避免在 VSCode debug 等环境中的 multiprocessing 问题）
        use_enqueue = not _should_disable_enqueue()

        # 添加控制台输出
        if console_output:
            # 使用自动刷新的流包装器，确保日志立即输出
            # 这样就不需要在代码中频繁调用 sys.stderr.flush()
            auto_flush_stderr = AutoFlushStream(sys.stderr)
            logger.add(
                auto_flush_stderr,
                format=format_console,
                level=log_level,
                colorize=True,
                backtrace=True,
                diagnose=True,
                enqueue=use_enqueue,  # 线程安全，但在某些环境下可能有问题
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
            enqueue=use_enqueue,  # 线程安全，但在某些环境下可能有问题
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
