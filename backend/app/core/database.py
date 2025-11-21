"""数据库配置和会话管理"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import DisconnectionError, OperationalError
from contextlib import contextmanager
from loguru import logger
import time
from app.core.config import settings

# 创建数据库引擎
# 增强的连接池配置，提高稳定性和性能
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,  # 连接前检查连接是否有效
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_timeout=30,  # 获取连接的超时时间（秒）
    pool_recycle=3600,  # 连接回收时间（1小时），防止连接过期
    pool_reset_on_return='commit',  # 返回连接时重置
    echo=False,  # 不打印SQL语句
    connect_args={
        "connect_timeout": 10,  # 连接超时（秒）
        "options": "-c statement_timeout=30000"  # 查询超时（30秒）
    } if "postgresql" in settings.DATABASE_URL else {}
)

# 添加连接池事件监听，记录连接状态
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """设置SQLite连接参数（如果使用SQLite）"""
    if "sqlite" in settings.DATABASE_URL:
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
        dbapi_conn.execute("PRAGMA journal_mode=WAL")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """连接从池中取出时的事件"""
    logger.debug("数据库连接从池中取出")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """连接返回池中时的事件"""
    logger.debug("数据库连接返回池中")

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # 提交后不过期对象，提高性能
)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """
    获取数据库会话（依赖注入）
    
    使用try-finally确保会话总是被关闭，即使发生异常
    """
    from fastapi import HTTPException
    db = SessionLocal()
    try:
        yield db
        db.commit()  # 正常情况提交事务
    except HTTPException:
        # HTTP异常（如401, 404等）不需要回滚，直接抛出
        db.rollback()
        raise
    except Exception as e:
        db.rollback()  # 异常时回滚事务
        logger.error(f"数据库操作异常，已回滚: {e}")
        raise
    finally:
        db.close()  # 确保会话关闭


@contextmanager
def get_db_context():
    """
    获取数据库会话（上下文管理器）
    
    用于需要手动管理事务的场景
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库操作异常，已回滚: {e}")
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except (DisconnectionError, OperationalError) as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False
    except Exception as e:
        logger.error(f"数据库连接检查异常: {e}")
        return False

