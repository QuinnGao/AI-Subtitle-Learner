"""
LLM 健康检查服务
定时监控 LLM 配置的健康状态
"""

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from app.core.llm.check_llm import check_llm_connection
from app.core.utils.logger import setup_logger
from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL

logger = setup_logger("llm_health_check")


@dataclass
class LLMHealthStatus:
    """LLM 健康状态"""

    base_url: str
    api_key: str
    model: str
    is_healthy: bool
    message: Optional[str]
    last_check_time: datetime
    check_count: int = 0


class LLMHealthChecker:
    """LLM 健康检查器"""

    def __init__(self, check_interval: int = 60):
        """
        初始化健康检查器

        Args:
            check_interval: 检查间隔（秒），默认 1 分钟
        """
        self.check_interval = check_interval
        self.health_status: dict[str, LLMHealthStatus] = {}
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def _get_config_key(self, base_url: str, api_key: str, model: str) -> str:
        """生成配置的唯一标识"""
        # 使用 base_url, api_key 的前8位, model 作为 key
        api_key_prefix = api_key[:8] if api_key else ""
        return f"{base_url}|{api_key_prefix}|{model}"

    def check_health(
        self, base_url: str, api_key: str, model: str, force: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        检查 LLM 健康状态

        Args:
            base_url: API 基础 URL
            api_key: API 密钥
            model: 模型名称
            force: 是否强制检查（忽略缓存）

        Returns:
            (是否健康, 消息)
        """
        config_key = self._get_config_key(base_url, api_key, model)

        with self.lock:
            status = self.health_status.get(config_key)

            # 如果存在缓存且未过期，且不是强制检查，则返回缓存结果
            if status and not force:
                # 检查是否在有效期内（检查间隔内）
                time_since_check = datetime.now() - status.last_check_time
                if time_since_check < timedelta(seconds=self.check_interval):
                    logger.debug(
                        f"使用缓存的健康检查结果: {config_key}, "
                        f"健康状态: {status.is_healthy}, "
                        f"距离上次检查: {time_since_check.total_seconds():.1f}秒"
                    )
                    return status.is_healthy, status.message

            # 执行健康检查
            logger.info(f"执行 LLM 健康检查: base_url={base_url}, model={model}")
            is_healthy, message = check_llm_connection(base_url, api_key, model)

            # 更新状态
            if status:
                status.is_healthy = is_healthy
                status.message = message
                status.last_check_time = datetime.now()
                status.check_count += 1
            else:
                status = LLMHealthStatus(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    is_healthy=is_healthy,
                    message=message,
                    last_check_time=datetime.now(),
                    check_count=1,
                )
                self.health_status[config_key] = status

            logger.info(
                f"LLM 健康检查完成: {config_key}, "
                f"健康状态: {is_healthy}, "
                f"消息: {message or 'OK'}"
            )

            return is_healthy, message

    def check_and_setup(
        self, base_url: str, api_key: str, model: str, force: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        检查 LLM 健康状态并设置环境变量（全局统一处理）

        Args:
            base_url: API 基础 URL
            api_key: API 密钥
            model: 模型名称
            force: 是否强制检查（忽略缓存）

        Returns:
            (是否健康, 消息)
        """
        # 执行健康检查（自动处理缓存）
        is_healthy, message = self.check_health(base_url, api_key, model, force=force)

        # 如果健康，设置环境变量（全局统一）
        if is_healthy:
            import os

            os.environ["OPENAI_BASE_URL"] = base_url
            os.environ["OPENAI_API_KEY"] = api_key
            logger.debug(
                f"已设置 LLM 环境变量: OPENAI_BASE_URL={base_url}, "
                f"OPENAI_API_KEY已设置（已隐藏）"
            )

        return is_healthy, message

    def ensure_healthy(self, force: bool = False) -> None:
        """
        确保 LLM 配置健康（验证配置、检查健康状态、设置环境变量）
        从默认配置获取配置，如果配置不完整或健康检查失败，抛出异常

        Args:
            force: 是否强制检查（忽略缓存）

        Raises:
            ValueError: 配置不完整
            Exception: 健康检查失败
        """
        # 从默认配置获取
        base_url = (LLM_API_BASE or "").strip()
        api_key = (LLM_API_KEY or "").strip()
        model = (LLM_MODEL or "").strip()

        # 验证配置是否完整
        if not base_url or not api_key or not model:
            error_msg = "LLM API 未配置, 请检查配置或环境变量"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 执行健康检查并设置环境变量
        is_healthy, message = self.check_and_setup(
            base_url, api_key, model, force=force
        )

        # 如果健康检查失败，抛出异常
        if not is_healthy:
            error_msg = f"LLM API 测试失败: {message or ''}"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info(f"LLM 连接验证成功: base_url={base_url}, model={model}")

    def get_health_status(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[LLMHealthStatus]:
        """获取健康状态（不执行检查）

        Args:
            base_url: API 基础 URL，如果为 None 则从默认配置获取
            api_key: API 密钥，如果为 None 则从默认配置获取
            model: 模型名称，如果为 None 则从默认配置获取

        Returns:
            健康状态，如果未找到则返回 None
        """
        # 如果参数未提供，从默认配置获取
        if not base_url or not api_key or not model:
            try:
                from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL
            except ImportError:
                # 如果导入失败，回退到环境变量
                import os

                if not base_url:
                    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
                if not api_key:
                    api_key = os.getenv("OPENAI_API_KEY", "").strip()
                if not model:
                    model = os.getenv("OPENAI_MODEL", "").strip()
            else:
                if not base_url:
                    base_url = (LLM_API_BASE or "").strip()
                if not api_key:
                    api_key = (LLM_API_KEY or "").strip()
                if not model:
                    model = (LLM_MODEL or "").strip()

        if not base_url or not api_key or not model:
            return None

        config_key = self._get_config_key(base_url, api_key, model)
        with self.lock:
            return self.health_status.get(config_key)

    def start_periodic_check(self):
        """启动定时检查"""
        if self.running:
            logger.warning("健康检查已在运行")
            return

        self.running = True
        self.thread = threading.Thread(target=self._periodic_check_loop, daemon=True)
        self.thread.start()
        logger.info(f"LLM 健康检查已启动，检查间隔: {self.check_interval}秒")

    def stop_periodic_check(self):
        """停止定时检查"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("LLM 健康检查已停止")

    def _periodic_check_loop(self):
        """定时检查循环"""
        while self.running:
            try:
                with self.lock:
                    # 复制当前的状态列表，避免在迭代时修改
                    configs_to_check = list(self.health_status.values())

                # 检查所有已缓存的配置
                for status in configs_to_check:
                    if not self.running:
                        break

                    try:
                        logger.debug(
                            f"定时检查 LLM 健康状态: "
                            f"base_url={status.base_url}, model={status.model}"
                        )
                        self.check_health(
                            status.base_url, status.api_key, status.model, force=True
                        )
                    except Exception as e:
                        logger.error(f"定时健康检查失败: {e}", exc_info=True)

                # 等待检查间隔
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"健康检查循环出错: {e}", exc_info=True)
                time.sleep(60)  # 出错后等待1分钟再继续

    def clear_cache(self, base_url: str = None, api_key: str = None, model: str = None):
        """
        清除缓存

        Args:
            base_url: 如果提供，只清除匹配的配置
            api_key: 如果提供，只清除匹配的配置
            model: 如果提供，只清除匹配的配置
        """
        with self.lock:
            if base_url or api_key or model:
                # 清除匹配的配置
                keys_to_remove = []
                for key, status in self.health_status.items():
                    if (
                        (not base_url or status.base_url == base_url)
                        and (not api_key or status.api_key == api_key)
                        and (not model or status.model == model)
                    ):
                        keys_to_remove.append(key)
                for key in keys_to_remove:
                    del self.health_status[key]
                logger.info(f"已清除 {len(keys_to_remove)} 个健康检查缓存")
            else:
                # 清除所有缓存
                count = len(self.health_status)
                self.health_status.clear()
                logger.info(f"已清除所有健康检查缓存（{count} 个）")


# 全局健康检查器实例
_global_health_checker: Optional[LLMHealthChecker] = None


def get_health_checker(check_interval: int = 60) -> LLMHealthChecker:
    """
    获取全局健康检查器实例

    Args:
        check_interval: 检查间隔（秒），默认 1 分钟，仅在首次创建时生效

    Returns:
        健康检查器实例
    """
    global _global_health_checker
    if _global_health_checker is None:
        _global_health_checker = LLMHealthChecker(check_interval=check_interval)
        # 自动启动定时检查
        _global_health_checker.start_periodic_check()
    return _global_health_checker
