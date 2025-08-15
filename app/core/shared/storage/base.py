"""
存储抽象基类

定义统一的存储接口，支持文件存储、数据库存储、缓存存储等多种存储方式。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, BinaryIO
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class StorageType(Enum):
    """存储类型枚举"""
    FILE = "file"
    DATABASE = "database"
    CACHE = "cache"
    MEMORY = "memory"
    CLOUD = "cloud"


class StorageOperation(Enum):
    """存储操作类型枚举"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    LIST = "list"
    EXISTS = "exists"
    COPY = "copy"
    MOVE = "move"


@dataclass
class StorageMetadata:
    """存储元数据"""
    size: Optional[int] = None
    created_at: Optional[float] = None
    modified_at: Optional[float] = None
    content_type: Optional[str] = None
    encoding: Optional[str] = None
    checksum: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "size": self.size,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "content_type": self.content_type,
            "encoding": self.encoding,
            "checksum": self.checksum,
            "tags": self.tags or {}
        }


@dataclass
class StorageResult:
    """存储操作结果"""
    success: bool
    data: Optional[Any] = None
    metadata: Optional[StorageMetadata] = None
    error_message: Optional[str] = None
    operation: Optional[StorageOperation] = None
    storage_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "error_message": self.error_message,
            "operation": self.operation.value if self.operation else None,
            "storage_path": self.storage_path
        }


class StorageError(Exception):
    """存储操作异常"""
    
    def __init__(self, message: str, operation: Optional[StorageOperation] = None, 
                 storage_path: Optional[str] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.operation = operation
        self.storage_path = storage_path
        self.original_error = original_error


class BaseStorage(ABC):
    """存储抽象基类
    
    定义所有存储实现必须遵循的接口。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化存储
        
        Args:
            config: 存储配置参数
        """
        self.config = config
        self.storage_type = self._get_storage_type()
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    @abstractmethod
    def _get_storage_type(self) -> StorageType:
        """获取存储类型"""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """检查路径是否存在
        
        Args:
            path: 存储路径
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def read(self, path: str, **kwargs) -> StorageResult:
        """读取数据
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 读取结果
        """
        pass
    
    @abstractmethod
    def write(self, path: str, data: Any, **kwargs) -> StorageResult:
        """写入数据
        
        Args:
            path: 存储路径
            data: 要写入的数据
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 写入结果
        """
        pass
    
    @abstractmethod
    def delete(self, path: str, **kwargs) -> StorageResult:
        """删除数据
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 删除结果
        """
        pass
    
    @abstractmethod
    def list(self, path: str = "", **kwargs) -> StorageResult:
        """列出路径下的内容
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 列表结果
        """
        pass
    
    def get_metadata(self, path: str) -> Optional[StorageMetadata]:
        """获取元数据
        
        Args:
            path: 存储路径
            
        Returns:
            Optional[StorageMetadata]: 元数据
        """
        # 默认实现，子类可以重写
        return None
    
    def copy(self, source_path: str, dest_path: str, **kwargs) -> StorageResult:
        """复制数据
        
        Args:
            source_path: 源路径
            dest_path: 目标路径
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 复制结果
        """
        try:
            # 默认实现：读取后写入
            read_result = self.read(source_path)
            if not read_result.success:
                return StorageResult(
                    success=False,
                    error_message=f"读取源文件失败: {read_result.error_message}",
                    operation=StorageOperation.COPY,
                    storage_path=source_path
                )
            
            write_result = self.write(dest_path, read_result.data, **kwargs)
            if write_result.success:
                write_result.operation = StorageOperation.COPY
                write_result.storage_path = f"{source_path} -> {dest_path}"
            
            return write_result
            
        except Exception as e:
            error_msg = f"复制操作失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.COPY,
                storage_path=f"{source_path} -> {dest_path}"
            )
    
    def move(self, source_path: str, dest_path: str, **kwargs) -> StorageResult:
        """移动数据
        
        Args:
            source_path: 源路径
            dest_path: 目标路径
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 移动结果
        """
        try:
            # 默认实现：复制后删除
            copy_result = self.copy(source_path, dest_path, **kwargs)
            if not copy_result.success:
                return copy_result
            
            delete_result = self.delete(source_path)
            if not delete_result.success:
                # 复制成功但删除失败，记录警告
                self.logger.warning(f"移动操作：复制成功但删除源文件失败: {delete_result.error_message}")
            
            return StorageResult(
                success=True,
                data=copy_result.data,
                metadata=copy_result.metadata,
                operation=StorageOperation.MOVE,
                storage_path=f"{source_path} -> {dest_path}"
            )
            
        except Exception as e:
            error_msg = f"移动操作失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.MOVE,
                storage_path=f"{source_path} -> {dest_path}"
            )
    
    def read_text(self, path: str, encoding: str = "utf-8", **kwargs) -> StorageResult:
        """读取文本数据
        
        Args:
            path: 存储路径
            encoding: 文本编码
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 读取结果
        """
        result = self.read(path, **kwargs)
        if result.success and isinstance(result.data, bytes):
            try:
                result.data = result.data.decode(encoding)
            except UnicodeDecodeError as e:
                result.success = False
                result.error_message = f"文本解码失败: {str(e)}"
        
        return result
    
    def write_text(self, path: str, text: str, encoding: str = "utf-8", **kwargs) -> StorageResult:
        """写入文本数据
        
        Args:
            path: 存储路径
            text: 文本内容
            encoding: 文本编码
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 写入结果
        """
        try:
            data = text.encode(encoding)
            return self.write(path, data, **kwargs)
        except UnicodeEncodeError as e:
            error_msg = f"文本编码失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.WRITE,
                storage_path=path
            )
    
    def read_json(self, path: str, **kwargs) -> StorageResult:
        """读取JSON数据
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 读取结果
        """
        result = self.read_text(path, **kwargs)
        if result.success:
            try:
                result.data = json.loads(result.data)
            except json.JSONDecodeError as e:
                result.success = False
                result.error_message = f"JSON解析失败: {str(e)}"
        
        return result
    
    def write_json(self, path: str, data: Any, indent: int = 2, **kwargs) -> StorageResult:
        """写入JSON数据
        
        Args:
            path: 存储路径
            data: 要写入的数据
            indent: JSON缩进
            **kwargs: 其他参数
            
        Returns:
            StorageResult: 写入结果
        """
        try:
            json_text = json.dumps(data, indent=indent, ensure_ascii=False)
            return self.write_text(path, json_text, **kwargs)
        except (TypeError, ValueError) as e:
            error_msg = f"JSON序列化失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.WRITE,
                storage_path=path
            )
    
    def get_info(self) -> Dict[str, Any]:
        """获取存储信息
        
        Returns:
            Dict[str, Any]: 存储信息
        """
        return {
            "storage_type": self.storage_type.value,
            "config": self.config,
            "class_name": self.__class__.__name__
        }
