"""
数据库基础配置
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_size=10,
    max_overflow=20,
    echo=False,  # 设置为 True 可以打印 SQL 语句（调试用）
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

