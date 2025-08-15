"""
缓存存储实现

基于Redis的缓存存储，支持键值对存储和过期时间设置。
"""

import json
import pickle
import time
from typing import Dict, Any, Optional, List, Union
import redis
from redis.exceptions import RedisError, ConnectionError

from .base import BaseStorage, StorageType, StorageOperation, StorageResult, StorageMetadata, StorageError
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class CacheStorage(BaseStorage):
    """缓存存储实现
    
    基于Redis的缓存存储，支持键值对操作和过期时间管理。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化缓存存储
        
        Args:
            config: 缓存存储配置
                - host: Redis主机 (默认: localhost)
                - port: Redis端口 (默认: 6379)
                - db: Redis数据库编号 (默认: 0)
                - password: Redis密码 (可选)
                - prefix: 键前缀 (默认: spec2test:)
                - default_ttl: 默认过期时间(秒) (默认: 3600)
                - serializer: 序列化方式 (json/pickle, 默认: json)
        """
        super().__init__(config)
        
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.db = config.get("db", 0)
        self.password = config.get("password")
        self.prefix = config.get("prefix", "spec2test:")
        self.default_ttl = config.get("default_ttl", 3600)
        self.serializer = config.get("serializer", "json")
        
        # 创建Redis连接
        self.redis_client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=False,  # 保持二进制模式以支持pickle
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # 测试连接
        try:
            self.redis_client.ping()
            self.logger.info(f"缓存存储初始化完成: {self.host}:{self.port}/{self.db}")
        except ConnectionError as e:
            error_msg = f"Redis连接失败: {e}"
            self.logger.error(error_msg)
            raise StorageError(error_msg)
    
    def _get_storage_type(self) -> StorageType:
        """获取存储类型"""
        return StorageType.CACHE
    
    def _get_full_key(self, path: str) -> str:
        """获取完整的Redis键
        
        Args:
            path: 存储路径
            
        Returns:
            str: 完整的Redis键
        """
        # 移除开头的斜杠
        path = path.lstrip('/')
        return f"{self.prefix}{path}"
    
    def _serialize_data(self, data: Any) -> bytes:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            
        Returns:
            bytes: 序列化后的数据
        """
        try:
            if self.serializer == "json":
                return json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif self.serializer == "pickle":
                return pickle.dumps(data)
            else:
                raise ValueError(f"不支持的序列化方式: {self.serializer}")
        except Exception as e:
            raise StorageError(f"数据序列化失败: {e}")
    
    def _deserialize_data(self, data: bytes) -> Any:
        """反序列化数据
        
        Args:
            data: 序列化的数据
            
        Returns:
            Any: 反序列化后的数据
        """
        try:
            if self.serializer == "json":
                return json.loads(data.decode('utf-8'))
            elif self.serializer == "pickle":
                return pickle.loads(data)
            else:
                raise ValueError(f"不支持的序列化方式: {self.serializer}")
        except Exception as e:
            raise StorageError(f"数据反序列化失败: {e}")
    
    def exists(self, path: str) -> bool:
        """检查键是否存在
        
        Args:
            path: 存储路径
            
        Returns:
            bool: 是否存在
        """
        try:
            full_key = self._get_full_key(path)
            return bool(self.redis_client.exists(full_key))
        except RedisError as e:
            self.logger.error(f"检查键存在性失败: {e}")
            return False
    
    def read(self, path: str, **kwargs) -> StorageResult:
        """读取缓存数据
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
                - raw: 是否返回原始字节数据 (默认: False)
                
        Returns:
            StorageResult: 读取结果
        """
        try:
            full_key = self._get_full_key(path)
            
            # 检查键是否存在
            if not self.redis_client.exists(full_key):
                return StorageResult(
                    success=False,
                    error_message=f"键不存在: {path}",
                    operation=StorageOperation.READ,
                    storage_path=full_key
                )
            
            # 读取数据
            raw_data = self.redis_client.get(full_key)
            
            if raw_data is None:
                return StorageResult(
                    success=False,
                    error_message=f"读取数据为空: {path}",
                    operation=StorageOperation.READ,
                    storage_path=full_key
                )
            
            # 是否返回原始数据
            raw = kwargs.get("raw", False)
            if raw:
                data = raw_data
            else:
                data = self._deserialize_data(raw_data)
            
            # 获取TTL信息
            ttl = self.redis_client.ttl(full_key)
            metadata = StorageMetadata(
                size=len(raw_data),
                tags={"ttl": ttl, "serializer": self.serializer}
            )
            
            return StorageResult(
                success=True,
                data=data,
                metadata=metadata,
                operation=StorageOperation.READ,
                storage_path=full_key
            )
            
        except RedisError as e:
            error_msg = f"Redis读取失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.READ,
                storage_path=path
            )
        except Exception as e:
            error_msg = f"读取缓存数据失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.READ,
                storage_path=path
            )
    
    def write(self, path: str, data: Any, **kwargs) -> StorageResult:
        """写入缓存数据
        
        Args:
            path: 存储路径
            data: 要写入的数据
            **kwargs: 其他参数
                - ttl: 过期时间(秒) (默认: 使用default_ttl)
                - nx: 仅当键不存在时设置 (默认: False)
                - xx: 仅当键存在时设置 (默认: False)
                - raw: 数据是否为原始字节 (默认: False)
                
        Returns:
            StorageResult: 写入结果
        """
        try:
            full_key = self._get_full_key(path)
            ttl = kwargs.get("ttl", self.default_ttl)
            nx = kwargs.get("nx", False)
            xx = kwargs.get("xx", False)
            raw = kwargs.get("raw", False)
            
            # 序列化数据
            if raw:
                serialized_data = data if isinstance(data, bytes) else str(data).encode('utf-8')
            else:
                serialized_data = self._serialize_data(data)
            
            # 设置数据
            result = self.redis_client.set(
                full_key,
                serialized_data,
                ex=ttl if ttl > 0 else None,
                nx=nx,
                xx=xx
            )
            
            if result:
                metadata = StorageMetadata(
                    size=len(serialized_data),
                    tags={"ttl": ttl, "serializer": self.serializer}
                )
                
                return StorageResult(
                    success=True,
                    data={"key": full_key, "size": len(serialized_data)},
                    metadata=metadata,
                    operation=StorageOperation.WRITE,
                    storage_path=full_key
                )
            else:
                return StorageResult(
                    success=False,
                    error_message=f"写入失败，可能是由于nx/xx条件: {path}",
                    operation=StorageOperation.WRITE,
                    storage_path=full_key
                )
            
        except RedisError as e:
            error_msg = f"Redis写入失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.WRITE,
                storage_path=path
            )
        except Exception as e:
            error_msg = f"写入缓存数据失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.WRITE,
                storage_path=path
            )
    
    def delete(self, path: str, **kwargs) -> StorageResult:
        """删除缓存数据
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
                - pattern: 是否作为模式删除 (默认: False)
                
        Returns:
            StorageResult: 删除结果
        """
        try:
            pattern = kwargs.get("pattern", False)
            
            if pattern:
                # 模式删除
                full_pattern = self._get_full_key(path)
                keys = self.redis_client.keys(full_pattern)
                
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
                else:
                    deleted_count = 0
                
                return StorageResult(
                    success=True,
                    data={"deleted_count": deleted_count, "keys": [k.decode('utf-8') for k in keys]},
                    operation=StorageOperation.DELETE,
                    storage_path=full_pattern
                )
            else:
                # 单个键删除
                full_key = self._get_full_key(path)
                deleted_count = self.redis_client.delete(full_key)
                
                return StorageResult(
                    success=True,
                    data={"deleted_count": deleted_count},
                    operation=StorageOperation.DELETE,
                    storage_path=full_key
                )
            
        except RedisError as e:
            error_msg = f"Redis删除失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.DELETE,
                storage_path=path
            )
        except Exception as e:
            error_msg = f"删除缓存数据失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.DELETE,
                storage_path=path
            )
    
    def list(self, path: str = "", **kwargs) -> StorageResult:
        """列出缓存键
        
        Args:
            path: 存储路径模式
            **kwargs: 其他参数
                - limit: 限制返回数量 (默认: 1000)
                - include_ttl: 是否包含TTL信息 (默认: False)
                
        Returns:
            StorageResult: 列表结果
        """
        try:
            pattern = self._get_full_key(path + "*" if path else "*")
            limit = kwargs.get("limit", 1000)
            include_ttl = kwargs.get("include_ttl", False)
            
            # 获取匹配的键
            keys = []
            for key in self.redis_client.scan_iter(match=pattern, count=limit):
                key_str = key.decode('utf-8')
                # 移除前缀
                if key_str.startswith(self.prefix):
                    key_str = key_str[len(self.prefix):]
                keys.append(key_str)
                
                if len(keys) >= limit:
                    break
            
            # 是否包含TTL信息
            if include_ttl:
                key_info = []
                for key in keys:
                    full_key = self._get_full_key(key)
                    ttl = self.redis_client.ttl(full_key)
                    key_info.append({
                        "key": key,
                        "ttl": ttl
                    })
                data = key_info
            else:
                data = keys
            
            return StorageResult(
                success=True,
                data=data,
                operation=StorageOperation.LIST,
                storage_path=pattern
            )
            
        except RedisError as e:
            error_msg = f"Redis列表操作失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.LIST,
                storage_path=path
            )
        except Exception as e:
            error_msg = f"列出缓存键失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.LIST,
                storage_path=path
            )
    
    def get_metadata(self, path: str) -> Optional[StorageMetadata]:
        """获取缓存元数据
        
        Args:
            path: 存储路径
            
        Returns:
            Optional[StorageMetadata]: 元数据
        """
        try:
            full_key = self._get_full_key(path)
            
            if not self.redis_client.exists(full_key):
                return None
            
            # 获取数据大小
            size = self.redis_client.memory_usage(full_key)
            if size is None:
                # 如果memory_usage不可用，估算大小
                data = self.redis_client.get(full_key)
                size = len(data) if data else 0
            
            # 获取TTL
            ttl = self.redis_client.ttl(full_key)
            
            return StorageMetadata(
                size=size,
                tags={
                    "ttl": ttl,
                    "serializer": self.serializer,
                    "redis_key": full_key
                }
            )
            
        except Exception as e:
            self.logger.warning(f"获取缓存元数据失败: {e}")
            return None
    
    def set_ttl(self, path: str, ttl: int) -> StorageResult:
        """设置键的过期时间
        
        Args:
            path: 存储路径
            ttl: 过期时间(秒)
            
        Returns:
            StorageResult: 操作结果
        """
        try:
            full_key = self._get_full_key(path)
            
            if ttl > 0:
                result = self.redis_client.expire(full_key, ttl)
            else:
                result = self.redis_client.persist(full_key)
            
            return StorageResult(
                success=result,
                data={"ttl_set": result},
                storage_path=full_key
            )
            
        except RedisError as e:
            error_msg = f"设置TTL失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                storage_path=path
            )
    
    def clear_all(self, confirm: bool = False) -> StorageResult:
        """清空所有缓存数据
        
        Args:
            confirm: 确认清空操作
            
        Returns:
            StorageResult: 操作结果
        """
        if not confirm:
            return StorageResult(
                success=False,
                error_message="清空操作需要确认参数 confirm=True"
            )
        
        try:
            # 只删除带前缀的键
            pattern = f"{self.prefix}*"
            keys = list(self.redis_client.scan_iter(match=pattern))
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
            else:
                deleted_count = 0
            
            return StorageResult(
                success=True,
                data={"deleted_count": deleted_count},
                storage_path=pattern
            )
            
        except RedisError as e:
            error_msg = f"清空缓存失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg
            )
