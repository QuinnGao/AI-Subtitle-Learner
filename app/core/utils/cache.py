"""Redis cache utility for API responses and computation results.

This module provides a simple interface for caching using Redis.
Can be used by translation, ASR, and other modules that need caching.
"""

import functools
import hashlib
import json
import pickle
from dataclasses import asdict, is_dataclass
from typing import Any, Optional

import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.config import REDIS_URL
from app.core.utils.logger import setup_logger

logger = setup_logger("cache")

# Global cache switch
_cache_enabled = True

# Redis 连接池
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def _get_redis_client() -> redis.Redis:
    """获取 Redis 客户端（单例）"""
    global _redis_pool, _redis_client
    
    if _redis_client is None:
        try:
            _redis_pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                decode_responses=False,  # 使用二进制模式，支持 pickle
                max_connections=50,
            )
            _redis_client = redis.Redis(connection_pool=_redis_pool)
            # 测试连接
            _redis_client.ping()
            logger.info(f"Redis 连接成功: {REDIS_URL}")
        except RedisConnectionError as e:
            logger.error(f"Redis 连接失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"初始化 Redis 客户端失败: {str(e)}", exc_info=True)
            raise
    
    return _redis_client


def enable_cache() -> None:
    """Enable caching globally."""
    global _cache_enabled
    _cache_enabled = True


def disable_cache() -> None:
    """Disable caching globally."""
    global _cache_enabled
    _cache_enabled = False


def is_cache_enabled() -> bool:
    """Check if caching is enabled."""
    return _cache_enabled


# 缓存键前缀
CACHE_PREFIX_LLM = "cache:llm:"
CACHE_PREFIX_ASR = "cache:asr:"
CACHE_PREFIX_TRANSLATE = "cache:translate:"
CACHE_PREFIX_TTS = "cache:tts:"
CACHE_PREFIX_VERSION = "cache:version:"


def _get_cache_key(prefix: str, key: str) -> str:
    """生成缓存键"""
    return f"{prefix}{key}"


def get_llm_cache() -> redis.Redis:
    """Get LLM translation cache instance (返回 Redis 客户端，用于兼容性)"""
    return _get_redis_client()


def get_asr_cache() -> redis.Redis:
    """Get ASR results cache instance (返回 Redis 客户端，用于兼容性)"""
    return _get_redis_client()


def get_translate_cache() -> redis.Redis:
    """Get translate cache instance (返回 Redis 客户端，用于兼容性)"""
    return _get_redis_client()


def get_tts_cache() -> redis.Redis:
    """Get TTS audio cache instance (返回 Redis 客户端，用于兼容性)"""
    return _get_redis_client()


def get_version_state_cache() -> redis.Redis:
    """Get version check state cache instance (返回 Redis 客户端，用于兼容性)"""
    return _get_redis_client()


def memoize(cache_instance: redis.Redis, prefix: str = "", expire: int = 3600, typed: bool = True):
    """Decorator to cache function results with global switch support.

    This is a wrapper around Redis caching that respects the global cache enable/disable setting.

    Args:
        cache_instance: Redis client instance (from get_llm_cache(), etc.)
        prefix: Cache key prefix (e.g., "llm:", "asr:")
        expire: Cache expiration time in seconds (default: 3600)
        typed: Whether to include argument types in cache key (default: True)

    Returns:
        Decorated function

    Examples:
        @memoize(get_llm_cache(), prefix="llm:", expire=3600, typed=True)
        def call_api(prompt: str):
            response = client.chat.completions.create(...)
            if not response.choices:
                raise ValueError("Invalid response")  # Exceptions are not cached
            return response
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            if not _cache_enabled:
                return func(*args, **kw)
            
            # 生成缓存键
            cache_key = _generate_cache_key_from_args(func, args, kw, prefix, typed)
            
            try:
                redis_client = _get_redis_client()
                # 尝试从缓存获取
                cached_value = redis_client.get(cache_key)
                if cached_value is not None:
                    try:
                        return pickle.loads(cached_value)
                    except Exception as e:
                        logger.warning(f"反序列化缓存值失败: {cache_key}, 错误: {e}")
                        # 缓存损坏，删除它
                        redis_client.delete(cache_key)
                
                # 执行函数
                result = func(*args, **kw)
                
                # 保存到缓存
                try:
                    serialized_value = pickle.dumps(result)
                    redis_client.setex(cache_key, expire, serialized_value)
                except Exception as e:
                    logger.warning(f"保存缓存失败: {cache_key}, 错误: {e}")
                
                return result
            except RedisConnectionError as e:
                logger.warning(f"Redis 连接失败，跳过缓存: {str(e)}")
                return func(*args, **kw)
            except Exception as e:
                logger.warning(f"缓存操作失败: {str(e)}")
                return func(*args, **kw)
        
        return wrapper
    return decorator


def _generate_cache_key_from_args(
    func, args, kw, prefix: str, typed: bool
) -> str:
    """从函数参数生成缓存键"""
    # 使用函数名和参数生成键
    key_parts = [func.__module__, func.__name__]
    
    # 添加位置参数
    for arg in args:
        key_parts.append(_serialize_for_key(arg))
    
    # 添加关键字参数
    if kw:
        sorted_kw = sorted(kw.items())
        for k, v in sorted_kw:
            key_parts.append(f"{k}={_serialize_for_key(v)}")
    
    # 如果启用类型检查，添加类型信息
    if typed:
        key_parts.append(f"types={tuple(type(a).__name__ for a in args)}")
    
    key_str = ":".join(str(p) for p in key_parts)
    key_hash = hashlib.sha256(key_str.encode()).hexdigest()
    
    return _get_cache_key(prefix, key_hash)


def _serialize_for_key(obj: Any) -> Any:
    """序列化对象用于缓存键生成"""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_key(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _serialize_for_key(v) for k, v in sorted(obj.items())}
    else:
        return obj


def generate_cache_key(data: Any) -> str:
    """Generate cache key from data (supports dataclasses, dicts, lists).

    Args:
        data: Data to generate key from

    Returns:
        SHA256 hash of the data
    """
    def _serialize(obj: Any) -> Any:
        """Recursively serialize object to JSON-serializable format"""
        if is_dataclass(obj) and not isinstance(obj, type):
            return asdict(obj)
        elif isinstance(obj, list):
            return [_serialize(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        else:
            return obj

    serialized_data = _serialize(data)
    data_str = json.dumps(serialized_data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()


# 兼容旧的文件缓存接口（用于 ASR 缓存）
def get_cache_value(key: str, prefix: str = CACHE_PREFIX_ASR) -> Optional[Any]:
    """获取缓存值"""
    if not _cache_enabled:
        return None
    
    try:
        redis_client = _get_redis_client()
        cache_key = _get_cache_key(prefix, key)
        cached_value = redis_client.get(cache_key)
        if cached_value is not None:
            return pickle.loads(cached_value)
        return None
    except Exception as e:
        logger.warning(f"获取缓存失败: {key}, 错误: {e}")
        return None


def set_cache_value(key: str, value: Any, prefix: str = CACHE_PREFIX_ASR, expire: int = 3600):
    """设置缓存值"""
    if not _cache_enabled:
        return
    
    try:
        redis_client = _get_redis_client()
        cache_key = _get_cache_key(prefix, key)
        serialized_value = pickle.dumps(value)
        redis_client.setex(cache_key, expire, serialized_value)
    except Exception as e:
        logger.warning(f"设置缓存失败: {key}, 错误: {e}")
