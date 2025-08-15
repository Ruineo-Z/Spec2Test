"""
存储抽象层包

提供统一的存储接口，支持文件存储、数据库存储、缓存存储等多种存储方式。
"""

from .base import (
    BaseStorage, StorageType, StorageOperation, 
    StorageResult, StorageMetadata, StorageError
)
from .file_storage import FileStorage
from .db_storage import DatabaseStorage
from .cache_storage import CacheStorage
from .factory import (
    StorageFactory, StorageManager,
    get_file_storage, get_database_storage, get_cache_storage, get_storage
)

__all__ = [
    # 核心接口
    "BaseStorage",
    "StorageType",
    "StorageOperation", 
    "StorageResult",
    "StorageMetadata",
    "StorageError",
    
    # 存储实现
    "FileStorage",
    "DatabaseStorage", 
    "CacheStorage",
    
    # 工厂和管理器
    "StorageFactory",
    "StorageManager",
    
    # 便捷函数
    "get_file_storage",
    "get_database_storage",
    "get_cache_storage",
    "get_storage"
]
