"""
数据库连接管理模块

提供数据库引擎、会话管理和连接池配置。
支持同步和异步数据库操作。
"""

from typing import Generator, AsyncGenerator, Optional
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from loguru import logger

from app.config import get_settings
from app.models.base import BaseModel


class DatabaseManager:
    """数据库管理器
    
    负责管理数据库连接、会话和连接池。
    支持同步和异步操作模式。
    """
    
    def __init__(self):
        """初始化数据库管理器"""
        self.settings = get_settings()
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        
    @property
    def engine(self) -> Engine:
        """获取同步数据库引擎"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def async_engine(self) -> AsyncEngine:
        """获取异步数据库引擎"""
        if self._async_engine is None:
            self._async_engine = self._create_async_engine()
        return self._async_engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """获取同步会话工厂"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._session_factory
    
    @property
    def async_session_factory(self) -> async_sessionmaker:
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._async_session_factory
    
    def _create_engine(self) -> Engine:
        """创建同步数据库引擎"""
        # 连接池配置
        pool_config = self._get_pool_config()
        
        engine = create_engine(
            self.settings.database.url,
            echo=self.settings.debug,  # 开发模式下显示SQL
            echo_pool=self.settings.debug,  # 开发模式下显示连接池信息
            future=True,  # 使用SQLAlchemy 2.0风格
            **pool_config
        )
        
        # 添加连接事件监听器
        self._setup_engine_events(engine)
        
        logger.info(f"创建同步数据库引擎: {self.settings.database.host}:{self.settings.database.port}")
        return engine
    
    def _create_async_engine(self) -> AsyncEngine:
        """创建异步数据库引擎"""
        # 异步连接池配置
        pool_config = self._get_pool_config()
        
        async_engine = create_async_engine(
            self.settings.database.async_url,
            echo=self.settings.debug,
            echo_pool=self.settings.debug,
            future=True,
            **pool_config
        )
        
        logger.info(f"创建异步数据库引擎: {self.settings.database.host}:{self.settings.database.port}")
        return async_engine
    
    def _get_pool_config(self) -> dict:
        """获取连接池配置"""
        if self.settings.environment == "testing":
            # 测试环境使用NullPool，每次创建新连接
            return {
                "poolclass": NullPool,
            }
        else:
            # 生产环境使用QueuePool
            return {
                "poolclass": QueuePool,
                "pool_size": 10,  # 连接池大小
                "max_overflow": 20,  # 最大溢出连接数
                "pool_timeout": 30,  # 获取连接超时时间（秒）
                "pool_recycle": 3600,  # 连接回收时间（秒）
                "pool_pre_ping": True,  # 连接前ping检查
            }
    
    def _setup_engine_events(self, engine: Engine) -> None:
        """设置引擎事件监听器"""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """SQLite特定配置"""
            if "sqlite" in str(engine.url):
                cursor = dbapi_connection.cursor()
                # 启用外键约束
                cursor.execute("PRAGMA foreign_keys=ON")
                # 设置WAL模式以提高并发性能
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出事件"""
            logger.debug("数据库连接检出")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接检入事件"""
            logger.debug("数据库连接检入")
    
    def create_tables(self) -> None:
        """创建所有数据表"""
        try:
            BaseModel.metadata.create_all(bind=self.engine)
            logger.info("数据表创建成功")
        except Exception as e:
            logger.error(f"数据表创建失败: {e}")
            raise
    
    def drop_tables(self) -> None:
        """删除所有数据表（谨慎使用）"""
        try:
            BaseModel.metadata.drop_all(bind=self.engine)
            logger.warning("所有数据表已删除")
        except Exception as e:
            logger.error(f"数据表删除失败: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取同步数据库会话上下文管理器"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取异步数据库会话上下文管理器"""
        async_session = self.async_session_factory()
        try:
            yield async_session
            await async_session.commit()
        except Exception as e:
            await async_session.rollback()
            logger.error(f"异步数据库会话错误: {e}")
            raise
        finally:
            await async_session.close()
    
    def get_session_for_dependency(self) -> Generator[Session, None, None]:
        """为FastAPI依赖注入提供会话"""
        session = self.session_factory()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"依赖注入会话错误: {e}")
            raise
        finally:
            session.close()
    
    def close_connections(self) -> None:
        """关闭所有数据库连接"""
        if self._engine:
            self._engine.dispose()
            logger.info("同步数据库连接已关闭")
        
        if self._async_engine:
            # 异步引擎需要在异步上下文中关闭
            logger.info("异步数据库连接标记为关闭")
    
    async def close_async_connections(self) -> None:
        """关闭异步数据库连接"""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("异步数据库连接已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的便捷函数
    
    用于FastAPI依赖注入
    
    Yields:
        数据库会话对象
    """
    yield from db_manager.get_session_for_dependency()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话的便捷函数
    
    Yields:
        异步数据库会话对象
    """
    async with db_manager.get_async_session() as session:
        yield session


def init_database() -> None:
    """初始化数据库
    
    创建所有数据表
    """
    logger.info("开始初始化数据库...")
    db_manager.create_tables()
    logger.info("数据库初始化完成")


def close_database() -> None:
    """关闭数据库连接"""
    logger.info("关闭数据库连接...")
    db_manager.close_connections()


async def close_async_database() -> None:
    """关闭异步数据库连接"""
    logger.info("关闭异步数据库连接...")
    await db_manager.close_async_connections()
