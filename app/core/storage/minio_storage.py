"""
MinIO 对象存储服务
"""

import io
from pathlib import Path
from typing import Optional, BinaryIO
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error
from minio.commonconfig import REPLACE

from app.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    MINIO_BUCKET_NAME,
)
from app.core.utils.logger import setup_logger

# 延迟初始化 logger，避免模块导入时的 multiprocessing 问题
_logger_instance = None


def _get_logger():
    """获取 logger 实例（懒加载）"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = setup_logger("minio_storage")
    return _logger_instance


# 全局存储实例
_storage_instance: Optional["MinIOStorage"] = None


class MinIOStorage:
    """MinIO 对象存储服务"""

    def __init__(
        self,
        endpoint: str = MINIO_ENDPOINT,
        access_key: str = MINIO_ACCESS_KEY,
        secret_key: str = MINIO_SECRET_KEY,
        secure: bool = MINIO_SECURE,
        bucket_name: str = MINIO_BUCKET_NAME,
    ):
        """初始化 MinIO 客户端

        Args:
            endpoint: MinIO 服务端点（格式：host:port）
            access_key: 访问密钥
            secret_key: 秘密密钥
            secure: 是否使用 HTTPS
            bucket_name: 默认存储桶名称
        """
        # 解析 endpoint（移除协议前缀）
        if "://" in endpoint:
            parsed = urlparse(endpoint)
            endpoint = f"{parsed.hostname}:{parsed.port or (443 if secure else 9000)}"
        else:
            # 如果没有端口，添加默认端口
            if ":" not in endpoint:
                endpoint = f"{endpoint}:{443 if secure else 9000}"

        self.endpoint = endpoint
        self.bucket_name = bucket_name

        try:
            # MinIO 7.x 要求所有参数都是关键字参数
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            # 确保存储桶存在
            self._ensure_bucket_exists()
            _get_logger().info(
                f"MinIO 客户端初始化成功: endpoint={endpoint}, bucket={bucket_name}"
            )
        except Exception as e:
            _get_logger().error(f"MinIO 客户端初始化失败: {str(e)}", exc_info=True)
            raise

    def _ensure_bucket_exists(self):
        """确保存储桶存在，如果不存在则创建"""
        try:
            # MinIO 7.x 要求所有参数都是关键字参数
            if not self.client.bucket_exists(bucket_name=self.bucket_name):
                self.client.make_bucket(bucket_name=self.bucket_name)
                _get_logger().info(f"创建存储桶: {self.bucket_name}")
        except S3Error as e:
            _get_logger().error(f"检查/创建存储桶失败: {str(e)}", exc_info=True)
            raise

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """上传文件到 MinIO

        Args:
            file_path: 本地文件路径
            object_name: 对象名称（如果不提供，使用文件路径）
            bucket_name: 存储桶名称（如果不提供，使用默认存储桶）
            content_type: 内容类型（如果不提供，根据文件扩展名自动推断）

        Returns:
            对象名称（可用于后续访问）
        """
        bucket = bucket_name or self.bucket_name

        # 如果没有指定对象名称，使用文件路径（标准化）
        if object_name is None:
            object_name = str(Path(file_path)).replace("\\", "/").lstrip("/")

        # 自动推断内容类型
        if content_type is None:
            content_type = self._get_content_type(file_path)

        try:
            # MinIO 7.x 要求所有参数都是关键字参数
            self.client.fput_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
            )
            _get_logger().debug(f"文件上传成功: {file_path} -> {bucket}/{object_name}")
            return object_name
        except S3Error as e:
            _get_logger().error(
                f"文件上传失败: {file_path}, 错误: {str(e)}", exc_info=True
            )
            raise

    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """上传字节数据到 MinIO

        Args:
            data: 字节数据
            object_name: 对象名称
            bucket_name: 存储桶名称（如果不提供，使用默认存储桶）
            content_type: 内容类型

        Returns:
            对象名称
        """
        bucket = bucket_name or self.bucket_name

        # 自动推断内容类型
        if content_type is None:
            content_type = self._get_content_type(object_name)

        try:
            data_stream = io.BytesIO(data)
            # MinIO 7.x 要求所有参数都是关键字参数
            self.client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=data_stream,
                length=len(data),
                content_type=content_type,
            )
            _get_logger().debug(
                f"字节数据上传成功: {bucket}/{object_name}, 大小: {len(data)} 字节"
            )
            return object_name
        except S3Error as e:
            _get_logger().error(
                f"字节数据上传失败: {object_name}, 错误: {str(e)}", exc_info=True
            )
            raise

    def download_file(
        self,
        object_name: str,
        file_path: str,
        bucket_name: Optional[str] = None,
    ) -> str:
        """从 MinIO 下载文件到本地

        Args:
            object_name: 对象名称
            file_path: 本地文件路径
            bucket_name: 存储桶名称（如果不提供，使用默认存储桶）

        Returns:
            本地文件路径
        """
        bucket = bucket_name or self.bucket_name

        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # MinIO 7.x 要求所有参数都是关键字参数
            self.client.fget_object(
                bucket_name=bucket,
                object_name=object_name,
                file_path=file_path,
            )
            _get_logger().debug(f"文件下载成功: {bucket}/{object_name} -> {file_path}")
            return file_path
        except S3Error as e:
            _get_logger().error(
                f"文件下载失败: {object_name}, 错误: {str(e)}", exc_info=True
            )
            raise

    def download_bytes(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> bytes:
        """从 MinIO 下载对象为字节数据

        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称（如果不提供，使用默认存储桶）

        Returns:
            字节数据
        """
        bucket = bucket_name or self.bucket_name

        try:
            # MinIO 7.x 要求所有参数都是关键字参数
            response = self.client.get_object(
                bucket_name=bucket,
                object_name=object_name,
            )
            data = response.read()
            response.close()
            response.release_conn()
            _get_logger().debug(
                f"字节数据下载成功: {bucket}/{object_name}, 大小: {len(data)} 字节"
            )
            return data
        except S3Error as e:
            _get_logger().error(
                f"字节数据下载失败: {object_name}, 错误: {str(e)}", exc_info=True
            )
            raise

    def delete_file(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """从 MinIO 删除文件

        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称（如果不提供，使用默认存储桶）

        Returns:
            是否删除成功
        """
        bucket = bucket_name or self.bucket_name

        try:
            # MinIO 7.x 要求所有参数都是关键字参数
            self.client.remove_object(
                bucket_name=bucket,
                object_name=object_name,
            )
            _get_logger().debug(f"文件删除成功: {bucket}/{object_name}")
            return True
        except S3Error as e:
            _get_logger().error(
                f"文件删除失败: {object_name}, 错误: {str(e)}", exc_info=True
            )
            return False

    def file_exists(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
    ) -> bool:
        """检查文件是否存在

        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称（如果不提供，使用默认存储桶）

        Returns:
            文件是否存在
        """
        bucket = bucket_name or self.bucket_name

        try:
            # MinIO 7.x 要求所有参数都是关键字参数
            self.client.stat_object(
                bucket_name=bucket,
                object_name=object_name,
            )
            return True
        except S3Error:
            return False

    def get_file_url(
        self,
        object_name: str,
        bucket_name: Optional[str] = None,
        expires_seconds: int = 3600,
    ) -> str:
        """获取文件的预签名 URL（用于临时访问）

        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称（如果不提供，使用默认存储桶）
            expires_seconds: URL 过期时间（秒）

        Returns:
            预签名 URL
        """
        bucket = bucket_name or self.bucket_name

        try:
            url = self.client.presigned_get_object(
                bucket, object_name, expires=expires_seconds
            )
            return url
        except S3Error as e:
            _get_logger().error(
                f"生成预签名 URL 失败: {object_name}, 错误: {str(e)}", exc_info=True
            )
            raise

    def _get_content_type(self, file_path: str) -> str:
        """根据文件扩展名推断内容类型"""
        ext = Path(file_path).suffix.lower()
        content_types = {
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".wav": "audio/wav",
            ".srt": "text/plain",
            ".ass": "text/plain",
            ".vtt": "text/vtt",
            ".json": "application/json",
            ".txt": "text/plain",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
        }
        return content_types.get(ext, "application/octet-stream")


def get_storage() -> MinIOStorage:
    """获取全局 MinIOStorage 单例实例"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MinIOStorage()
    return _storage_instance
