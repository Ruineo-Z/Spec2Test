"""
文件存储实现

基于本地文件系统的存储实现，支持文件和目录操作。
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, BinaryIO
import time

from .base import BaseStorage, StorageType, StorageOperation, StorageResult, StorageMetadata, StorageError
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class FileStorage(BaseStorage):
    """文件存储实现
    
    基于本地文件系统的存储，支持文件和目录的完整操作。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件存储
        
        Args:
            config: 文件存储配置
                - base_path: 基础存储路径
                - create_dirs: 是否自动创建目录 (默认: True)
                - file_permissions: 文件权限 (默认: 0o644)
                - dir_permissions: 目录权限 (默认: 0o755)
                - max_file_size: 最大文件大小 (字节，默认: 100MB)
        """
        super().__init__(config)
        
        self.base_path = Path(config.get("base_path", "./storage"))
        self.create_dirs = config.get("create_dirs", True)
        self.file_permissions = config.get("file_permissions", 0o644)
        self.dir_permissions = config.get("dir_permissions", 0o755)
        self.max_file_size = config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        
        # 确保基础路径存在
        if self.create_dirs:
            self.base_path.mkdir(parents=True, exist_ok=True)
            os.chmod(self.base_path, self.dir_permissions)
        
        self.logger.info(f"文件存储初始化完成: {self.base_path}")
    
    def _get_storage_type(self) -> StorageType:
        """获取存储类型"""
        return StorageType.FILE
    
    def _get_full_path(self, path: str) -> Path:
        """获取完整路径
        
        Args:
            path: 相对路径
            
        Returns:
            Path: 完整路径
        """
        # 移除开头的斜杠，确保是相对路径
        path = path.lstrip('/')
        return self.base_path / path
    
    def _ensure_parent_dir(self, file_path: Path) -> None:
        """确保父目录存在
        
        Args:
            file_path: 文件路径
        """
        if self.create_dirs:
            parent_dir = file_path.parent
            if not parent_dir.exists():
                parent_dir.mkdir(parents=True, exist_ok=True)
                os.chmod(parent_dir, self.dir_permissions)
    
    def _calculate_checksum(self, file_path: Path) -> Optional[str]:
        """计算文件校验和
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[str]: MD5校验和
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.warning(f"计算校验和失败: {e}")
            return None
    
    def exists(self, path: str) -> bool:
        """检查路径是否存在
        
        Args:
            path: 存储路径
            
        Returns:
            bool: 是否存在
        """
        try:
            full_path = self._get_full_path(path)
            return full_path.exists()
        except Exception as e:
            self.logger.error(f"检查路径存在性失败: {e}")
            return False
    
    def read(self, path: str, **kwargs) -> StorageResult:
        """读取文件数据
        
        Args:
            path: 文件路径
            **kwargs: 其他参数
                - binary: 是否以二进制模式读取 (默认: True)
                
        Returns:
            StorageResult: 读取结果
        """
        try:
            full_path = self._get_full_path(path)
            
            if not full_path.exists():
                return StorageResult(
                    success=False,
                    error_message=f"文件不存在: {path}",
                    operation=StorageOperation.READ,
                    storage_path=str(full_path)
                )
            
            if not full_path.is_file():
                return StorageResult(
                    success=False,
                    error_message=f"路径不是文件: {path}",
                    operation=StorageOperation.READ,
                    storage_path=str(full_path)
                )
            
            # 检查文件大小
            file_size = full_path.stat().st_size
            if file_size > self.max_file_size:
                return StorageResult(
                    success=False,
                    error_message=f"文件过大: {file_size} > {self.max_file_size}",
                    operation=StorageOperation.READ,
                    storage_path=str(full_path)
                )
            
            # 读取文件
            binary = kwargs.get("binary", True)
            mode = "rb" if binary else "r"
            encoding = kwargs.get("encoding", "utf-8") if not binary else None
            
            with open(full_path, mode, encoding=encoding) as f:
                data = f.read()
            
            # 获取元数据
            metadata = self.get_metadata(path)
            
            return StorageResult(
                success=True,
                data=data,
                metadata=metadata,
                operation=StorageOperation.READ,
                storage_path=str(full_path)
            )
            
        except Exception as e:
            error_msg = f"读取文件失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.READ,
                storage_path=path
            )
    
    def write(self, path: str, data: Any, **kwargs) -> StorageResult:
        """写入文件数据
        
        Args:
            path: 文件路径
            data: 要写入的数据
            **kwargs: 其他参数
                - binary: 是否以二进制模式写入 (默认: 根据数据类型判断)
                - overwrite: 是否覆盖已存在的文件 (默认: True)
                
        Returns:
            StorageResult: 写入结果
        """
        try:
            full_path = self._get_full_path(path)
            
            # 检查是否允许覆盖
            overwrite = kwargs.get("overwrite", True)
            if full_path.exists() and not overwrite:
                return StorageResult(
                    success=False,
                    error_message=f"文件已存在且不允许覆盖: {path}",
                    operation=StorageOperation.WRITE,
                    storage_path=str(full_path)
                )
            
            # 确保父目录存在
            self._ensure_parent_dir(full_path)
            
            # 判断写入模式
            binary = kwargs.get("binary")
            if binary is None:
                binary = isinstance(data, (bytes, bytearray))
            
            mode = "wb" if binary else "w"
            encoding = kwargs.get("encoding", "utf-8") if not binary else None
            
            # 写入文件
            with open(full_path, mode, encoding=encoding) as f:
                f.write(data)
            
            # 设置文件权限
            os.chmod(full_path, self.file_permissions)
            
            # 获取元数据
            metadata = self.get_metadata(path)
            
            self.logger.info(f"文件写入成功: {path}")
            return StorageResult(
                success=True,
                data=len(data) if isinstance(data, (str, bytes)) else None,
                metadata=metadata,
                operation=StorageOperation.WRITE,
                storage_path=str(full_path)
            )
            
        except Exception as e:
            error_msg = f"写入文件失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.WRITE,
                storage_path=path
            )
    
    def delete(self, path: str, **kwargs) -> StorageResult:
        """删除文件或目录
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
                - recursive: 是否递归删除目录 (默认: False)
                
        Returns:
            StorageResult: 删除结果
        """
        try:
            full_path = self._get_full_path(path)
            
            if not full_path.exists():
                return StorageResult(
                    success=False,
                    error_message=f"路径不存在: {path}",
                    operation=StorageOperation.DELETE,
                    storage_path=str(full_path)
                )
            
            recursive = kwargs.get("recursive", False)
            
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                if recursive:
                    shutil.rmtree(full_path)
                else:
                    full_path.rmdir()  # 只删除空目录
            else:
                return StorageResult(
                    success=False,
                    error_message=f"未知的路径类型: {path}",
                    operation=StorageOperation.DELETE,
                    storage_path=str(full_path)
                )
            
            self.logger.info(f"删除成功: {path}")
            return StorageResult(
                success=True,
                operation=StorageOperation.DELETE,
                storage_path=str(full_path)
            )
            
        except Exception as e:
            error_msg = f"删除失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.DELETE,
                storage_path=path
            )
    
    def list(self, path: str = "", **kwargs) -> StorageResult:
        """列出目录内容
        
        Args:
            path: 目录路径
            **kwargs: 其他参数
                - recursive: 是否递归列出 (默认: False)
                - include_files: 是否包含文件 (默认: True)
                - include_dirs: 是否包含目录 (默认: True)
                
        Returns:
            StorageResult: 列表结果
        """
        try:
            full_path = self._get_full_path(path)
            
            if not full_path.exists():
                return StorageResult(
                    success=False,
                    error_message=f"路径不存在: {path}",
                    operation=StorageOperation.LIST,
                    storage_path=str(full_path)
                )
            
            if not full_path.is_dir():
                return StorageResult(
                    success=False,
                    error_message=f"路径不是目录: {path}",
                    operation=StorageOperation.LIST,
                    storage_path=str(full_path)
                )
            
            recursive = kwargs.get("recursive", False)
            include_files = kwargs.get("include_files", True)
            include_dirs = kwargs.get("include_dirs", True)
            
            items = []
            
            if recursive:
                pattern = "**/*" if include_files and include_dirs else ("**/*" if include_files else "**/")
                for item in full_path.rglob(pattern):
                    if (include_files and item.is_file()) or (include_dirs and item.is_dir()):
                        rel_path = item.relative_to(self.base_path)
                        items.append(str(rel_path))
            else:
                for item in full_path.iterdir():
                    if (include_files and item.is_file()) or (include_dirs and item.is_dir()):
                        rel_path = item.relative_to(self.base_path)
                        items.append(str(rel_path))
            
            return StorageResult(
                success=True,
                data=sorted(items),
                operation=StorageOperation.LIST,
                storage_path=str(full_path)
            )
            
        except Exception as e:
            error_msg = f"列出目录内容失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.LIST,
                storage_path=path
            )
    
    def get_metadata(self, path: str) -> Optional[StorageMetadata]:
        """获取文件元数据
        
        Args:
            path: 文件路径
            
        Returns:
            Optional[StorageMetadata]: 文件元数据
        """
        try:
            full_path = self._get_full_path(path)
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            
            # 获取内容类型
            content_type = None
            if full_path.is_file():
                suffix = full_path.suffix.lower()
                content_type_map = {
                    '.txt': 'text/plain',
                    '.json': 'application/json',
                    '.xml': 'application/xml',
                    '.yaml': 'application/yaml',
                    '.yml': 'application/yaml',
                    '.md': 'text/markdown',
                    '.html': 'text/html',
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.py': 'text/x-python',
                    '.pdf': 'application/pdf',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif'
                }
                content_type = content_type_map.get(suffix, 'application/octet-stream')
            
            # 计算校验和（仅对文件）
            checksum = None
            if full_path.is_file() and stat.st_size < 10 * 1024 * 1024:  # 小于10MB才计算
                checksum = self._calculate_checksum(full_path)
            
            return StorageMetadata(
                size=stat.st_size,
                created_at=stat.st_ctime,
                modified_at=stat.st_mtime,
                content_type=content_type,
                encoding='utf-8' if content_type and content_type.startswith('text/') else None,
                checksum=checksum
            )
            
        except Exception as e:
            self.logger.warning(f"获取元数据失败: {e}")
            return None
