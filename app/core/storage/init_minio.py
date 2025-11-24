"""
初始化 MinIO 存储桶
"""
from app.core.storage import get_storage
from app.core.utils.logger import setup_logger

logger = setup_logger("init_minio")


def init_minio():
    """初始化 MinIO（确保存储桶存在）"""
    try:
        storage = get_storage()
        logger.info("MinIO 初始化成功")
    except Exception as e:
        logger.error(f"MinIO 初始化失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    init_minio()


