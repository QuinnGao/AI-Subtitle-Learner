"""
初始化数据库表
"""
from app.database.base import Base, engine
from app.core.utils.logger import setup_logger

logger = setup_logger("init_db")


def init_db():
    """初始化数据库表"""
    try:
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表失败: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    init_db()


