"""数据库配置和连接管理

提供数据库连接、会话管理和基础模型。
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from loguru import logger
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.utils.exceptions import ConfigurationError

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()

# 全局变量
engine = None
async_engine = None
SessionLocal = None
AsyncSessionLocal = None


def get_database_url(async_mode: bool = False) -> str:
    """获取数据库连接URL

    Args:
        async_mode: 是否为异步模式

    Returns:
        数据库连接URL
    """
    # settings已经在模块顶部导入

    if not settings.database:
        raise ConfigurationError("数据库配置未设置")

    # 构建基础URL
    if settings.database.driver == "sqlite":
        if async_mode:
            return f"sqlite+aiosqlite:///{settings.database.name}"
        else:
            return f"sqlite:///{settings.database.name}"

    elif settings.database.driver == "postgresql":
        base_url = (
            f"{settings.database.user}:{settings.database.password}"
            f"@{settings.database.host}:{settings.database.port}"
            f"/{settings.database.name}"
        )

        if async_mode:
            return f"postgresql+asyncpg://{base_url}"
        else:
            return f"postgresql://{base_url}"

    elif settings.database.driver == "mysql":
        base_url = (
            f"{settings.database.user}:{settings.database.password}"
            f"@{settings.database.host}:{settings.database.port}"
            f"/{settings.database.name}"
        )

        if async_mode:
            return f"mysql+aiomysql://{base_url}"
        else:
            return f"mysql+pymysql://{base_url}"

    else:
        raise ConfigurationError(f"不支持的数据库驱动: {settings.database.driver}")


def init_database():
    """初始化数据库连接"""
    global engine, async_engine, SessionLocal, AsyncSessionLocal

    try:
        # settings已经在模块顶部导入

        # 同步引擎
        sync_url = get_database_url(async_mode=False)
        engine = create_engine(
            sync_url,
            pool_pre_ping=True,
            pool_recycle=settings.database.pool_recycle if settings.database else 3600,
            echo=settings.database.echo if settings.database else False,
        )

        # 异步引擎
        async_url = get_database_url(async_mode=True)
        async_engine = create_async_engine(
            async_url,
            pool_pre_ping=True,
            pool_recycle=settings.database.pool_recycle if settings.database else 3600,
            echo=settings.database.echo if settings.database else False,
        )

        # 会话工厂
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        AsyncSessionLocal = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )

        logger.info(
            f"数据库连接初始化成功: {settings.database.driver if settings.database else 'sqlite'}"
        )

    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        raise ConfigurationError(f"数据库连接初始化失败: {e}")


async def create_tables():
    """创建数据库表"""
    try:
        if async_engine is None:
            raise ConfigurationError("数据库引擎未初始化")

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("数据库表创建成功")

    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise


async def drop_tables():
    """删除数据库表"""
    try:
        if async_engine is None:
            raise ConfigurationError("数据库引擎未初始化")

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.info("数据库表删除成功")

    except Exception as e:
        logger.error(f"数据库表删除失败: {e}")
        raise


def get_db() -> Session:
    """获取同步数据库会话

    Returns:
        数据库会话
    """
    if SessionLocal is None:
        raise ConfigurationError("数据库会话工厂未初始化")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话

    Returns:
        异步数据库会话
    """
    if AsyncSessionLocal is None:
        raise ConfigurationError("异步数据库会话工厂未初始化")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncSession:
    """获取数据库会话上下文管理器

    Returns:
        异步数据库会话
    """
    if AsyncSessionLocal is None:
        raise ConfigurationError("异步数据库会话工厂未初始化")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """检查数据库连接状态

    Returns:
        连接是否正常
    """
    try:
        if async_engine is None:
            return False

        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        return True

    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


async def close_database_connections():
    """关闭数据库连接"""
    global engine, async_engine

    try:
        if async_engine:
            await async_engine.dispose()
            logger.info("异步数据库连接已关闭")

        if engine:
            engine.dispose()
            logger.info("同步数据库连接已关闭")

    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.session_local = None
        self.async_session_local = None

    async def initialize(self):
        """初始化数据库管理器"""
        init_database()
        self.engine = engine
        self.async_engine = async_engine
        self.session_local = SessionLocal
        self.async_session_local = AsyncSessionLocal

    async def create_tables(self):
        """创建数据库表"""
        await create_tables()

    async def drop_tables(self):
        """删除数据库表"""
        await drop_tables()

    async def check_connection(self) -> bool:
        """检查数据库连接"""
        return await check_database_connection()

    async def close_connections(self):
        """关闭数据库连接"""
        await close_database_connections()

    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        async with get_db_session() as session:
            yield session


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 数据库生命周期管理
@asynccontextmanager
async def database_lifespan():
    """数据库生命周期管理"""
    try:
        # 启动时初始化数据库
        await db_manager.initialize()
        await db_manager.create_tables()

        # 检查连接
        if await db_manager.check_connection():
            logger.info("数据库连接正常")
        else:
            logger.warning("数据库连接异常")

        yield

    finally:
        # 关闭时清理连接
        await db_manager.close_connections()


# 导出
__all__ = [
    "Base",
    "metadata",
    "init_database",
    "create_tables",
    "drop_tables",
    "get_db",
    "get_async_db",
    "get_db_session",
    "check_database_connection",
    "close_database_connections",
    "DatabaseManager",
    "db_manager",
    "database_lifespan",
]
