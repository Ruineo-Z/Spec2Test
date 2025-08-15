"""
存储工厂类

统一的存储客户端创建和管理工厂，支持多种存储类型。
"""

from typing import Dict, Any, Optional, List
from functools import lru_cache

from .base import BaseStorage, StorageType, StorageError
from .file_storage import FileStorage
from .db_storage import DatabaseStorage
from .cache_storage import CacheStorage
from app.config import get_settings
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class StorageFactory:
    """存储工厂类
    
    负责创建和管理各种类型的存储客户端实例。
    """
    
    # 存储客户端缓存
    _storage_cache: Dict[str, BaseStorage] = {}
    
    @classmethod
    def create_storage(cls, storage_type: str, config: Optional[Dict[str, Any]] = None) -> BaseStorage:
        """创建存储客户端
        
        Args:
            storage_type: 存储类型 (file/database/cache)
            config: 存储配置参数
            
        Returns:
            BaseStorage: 存储客户端实例
            
        Raises:
            StorageError: 创建失败时抛出
        """
        try:
            # 使用默认配置
            if config is None:
                config = cls._get_default_config(storage_type)
            
            # 生成缓存键
            cache_key = cls._generate_cache_key(storage_type, config)
            
            # 检查缓存
            if cache_key in cls._storage_cache:
                logger.debug(f"使用缓存的存储客户端: {storage_type}")
                return cls._storage_cache[cache_key]
            
            # 创建客户端实例
            if storage_type == StorageType.FILE.value:
                storage = FileStorage(config)
            elif storage_type == StorageType.DATABASE.value:
                storage = DatabaseStorage(config)
            elif storage_type == StorageType.CACHE.value:
                storage = CacheStorage(config)
            else:
                raise StorageError(f"不支持的存储类型: {storage_type}")
            
            # 缓存客户端
            cls._storage_cache[cache_key] = storage
            
            logger.info(f"存储客户端创建成功: {storage_type}")
            return storage
            
        except Exception as e:
            error_msg = f"创建存储客户端失败: {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg, storage_path=storage_type)
    
    @classmethod
    def _generate_cache_key(cls, storage_type: str, config: Dict[str, Any]) -> str:
        """生成缓存键
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            str: 缓存键
        """
        # 使用关键配置参数生成缓存键
        key_parts = [storage_type]
        
        if storage_type == StorageType.FILE.value:
            key_parts.append(str(config.get("base_path", "")))
        elif storage_type == StorageType.DATABASE.value:
            key_parts.append(str(config.get("session", "")))
        elif storage_type == StorageType.CACHE.value:
            key_parts.extend([
                config.get("host", "localhost"),
                str(config.get("port", 6379)),
                str(config.get("db", 0)),
                config.get("prefix", "")
            ])
        
        return ":".join(key_parts)
    
    @classmethod
    def _get_default_config(cls, storage_type: str) -> Dict[str, Any]:
        """获取默认配置
        
        Args:
            storage_type: 存储类型
            
        Returns:
            Dict[str, Any]: 默认配置
        """
        settings = get_settings()
        
        if storage_type == StorageType.FILE.value:
            return {
                "base_path": "./storage",
                "create_dirs": True,
                "file_permissions": 0o644,
                "dir_permissions": 0o755,
                "max_file_size": 100 * 1024 * 1024  # 100MB
            }
        elif storage_type == StorageType.DATABASE.value:
            return {
                "session": None,  # 使用全局会话
                "auto_commit": True,
                "batch_size": 1000
            }
        elif storage_type == StorageType.CACHE.value:
            return {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "password": None,
                "prefix": "spec2test:",
                "default_ttl": 3600,
                "serializer": "json"
            }
        else:
            return {}
    
    @classmethod
    def get_available_storage_types(cls) -> List[str]:
        """获取可用的存储类型列表
        
        Returns:
            List[str]: 存储类型列表
        """
        return [storage_type.value for storage_type in StorageType]
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        return {
            "cached_storages": len(cls._storage_cache),
            "cache_keys": list(cls._storage_cache.keys()),
            "storage_types": [storage.storage_type.value for storage in cls._storage_cache.values()]
        }
    
    @classmethod
    def clear_cache(cls, storage_type: Optional[str] = None) -> int:
        """清理存储客户端缓存
        
        Args:
            storage_type: 要清理的存储类型，None表示清理所有
            
        Returns:
            int: 清理的客户端数量
        """
        if storage_type is None:
            # 清理所有缓存
            count = len(cls._storage_cache)
            cls._storage_cache.clear()
            logger.info(f"清理所有存储客户端缓存: {count}个")
            return count
        else:
            # 清理指定类型的缓存
            keys_to_remove = [key for key in cls._storage_cache.keys() if key.startswith(storage_type)]
            for key in keys_to_remove:
                del cls._storage_cache[key]
            logger.info(f"清理{storage_type}存储客户端缓存: {len(keys_to_remove)}个")
            return len(keys_to_remove)
    
    @classmethod
    def test_storage_connection(cls, storage_type: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """测试存储连接
        
        Args:
            storage_type: 存储类型
            config: 存储配置
            
        Returns:
            bool: 连接是否成功
        """
        try:
            storage = cls.create_storage(storage_type, config)
            
            # 执行简单的测试操作
            if storage_type == StorageType.FILE.value:
                # 测试文件存储：检查基础路径
                return storage.exists("")
            elif storage_type == StorageType.DATABASE.value:
                # 测试数据库存储：列出表
                result = storage.list()
                return result.success
            elif storage_type == StorageType.CACHE.value:
                # 测试缓存存储：执行ping操作
                test_key = "test_connection"
                write_result = storage.write(test_key, "test", ttl=10)
                if write_result.success:
                    storage.delete(test_key)
                return write_result.success
            else:
                return False
                
        except Exception as e:
            logger.error(f"存储连接测试失败: {e}")
            return False


# 便捷函数
def get_file_storage(config: Optional[Dict[str, Any]] = None) -> FileStorage:
    """获取文件存储客户端
    
    Args:
        config: 文件存储配置
        
    Returns:
        FileStorage: 文件存储客户端
    """
    return StorageFactory.create_storage(StorageType.FILE.value, config)


def get_database_storage(config: Optional[Dict[str, Any]] = None) -> DatabaseStorage:
    """获取数据库存储客户端
    
    Args:
        config: 数据库存储配置
        
    Returns:
        DatabaseStorage: 数据库存储客户端
    """
    return StorageFactory.create_storage(StorageType.DATABASE.value, config)


def get_cache_storage(config: Optional[Dict[str, Any]] = None) -> CacheStorage:
    """获取缓存存储客户端
    
    Args:
        config: 缓存存储配置
        
    Returns:
        CacheStorage: 缓存存储客户端
    """
    return StorageFactory.create_storage(StorageType.CACHE.value, config)


def get_storage(storage_type: str, config: Optional[Dict[str, Any]] = None) -> BaseStorage:
    """获取存储客户端（通用接口）
    
    Args:
        storage_type: 存储类型
        config: 存储配置
        
    Returns:
        BaseStorage: 存储客户端
    """
    return StorageFactory.create_storage(storage_type, config)


# 存储管理器
class StorageManager:
    """存储管理器
    
    提供高级的存储管理功能，支持多存储协调操作。
    """
    
    def __init__(self):
        self.storages: Dict[str, BaseStorage] = {}
    
    def register_storage(self, name: str, storage: BaseStorage) -> None:
        """注册存储客户端
        
        Args:
            name: 存储名称
            storage: 存储客户端
        """
        self.storages[name] = storage
        logger.info(f"注册存储客户端: {name} ({storage.storage_type.value})")
    
    def get_storage(self, name: str) -> Optional[BaseStorage]:
        """获取存储客户端
        
        Args:
            name: 存储名称
            
        Returns:
            Optional[BaseStorage]: 存储客户端
        """
        return self.storages.get(name)
    
    def sync_data(self, source_name: str, dest_name: str, path: str) -> bool:
        """在存储间同步数据
        
        Args:
            source_name: 源存储名称
            dest_name: 目标存储名称
            path: 数据路径
            
        Returns:
            bool: 同步是否成功
        """
        try:
            source_storage = self.storages.get(source_name)
            dest_storage = self.storages.get(dest_name)
            
            if not source_storage or not dest_storage:
                logger.error(f"存储不存在: {source_name} 或 {dest_name}")
                return False
            
            # 从源存储读取数据
            read_result = source_storage.read(path)
            if not read_result.success:
                logger.error(f"从源存储读取失败: {read_result.error_message}")
                return False
            
            # 写入目标存储
            write_result = dest_storage.write(path, read_result.data)
            if not write_result.success:
                logger.error(f"写入目标存储失败: {write_result.error_message}")
                return False
            
            logger.info(f"数据同步成功: {source_name} -> {dest_name} ({path})")
            return True
            
        except Exception as e:
            logger.error(f"数据同步失败: {e}")
            return False
    
    def backup_data(self, source_name: str, backup_name: str, paths: List[str]) -> Dict[str, bool]:
        """备份数据到另一个存储
        
        Args:
            source_name: 源存储名称
            backup_name: 备份存储名称
            paths: 要备份的路径列表
            
        Returns:
            Dict[str, bool]: 每个路径的备份结果
        """
        results = {}
        
        for path in paths:
            success = self.sync_data(source_name, backup_name, path)
            results[path] = success
        
        success_count = sum(results.values())
        logger.info(f"备份完成: {success_count}/{len(paths)} 成功")
        
        return results
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取所有存储信息
        
        Returns:
            Dict[str, Any]: 存储信息
        """
        info = {}
        for name, storage in self.storages.items():
            info[name] = storage.get_info()
        
        return info
