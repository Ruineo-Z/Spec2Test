"""
数据库存储实现

基于SQLAlchemy的数据库存储，支持结构化数据的CRUD操作。
"""

import json
from typing import Dict, Any, Optional, List, Union, Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, inspect

from .base import BaseStorage, StorageType, StorageOperation, StorageResult, StorageMetadata, StorageError
from app.database import get_db
from app.models.base import BaseModel
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseStorage(BaseStorage):
    """数据库存储实现
    
    基于SQLAlchemy的数据库存储，支持模型的CRUD操作。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化数据库存储
        
        Args:
            config: 数据库存储配置
                - session: 数据库会话 (可选，默认使用全局会话)
                - auto_commit: 是否自动提交 (默认: True)
                - batch_size: 批量操作大小 (默认: 1000)
        """
        super().__init__(config)
        
        self.session = config.get("session")
        self.auto_commit = config.get("auto_commit", True)
        self.batch_size = config.get("batch_size", 1000)
        
        self.logger.info("数据库存储初始化完成")
    
    def _get_storage_type(self) -> StorageType:
        """获取存储类型"""
        return StorageType.DATABASE
    
    def _get_session(self) -> Session:
        """获取数据库会话

        Returns:
            Session: 数据库会话
        """
        if self.session:
            return self.session
        return next(get_db())
    
    def _parse_path(self, path: str) -> Dict[str, Any]:
        """解析存储路径
        
        Args:
            path: 存储路径，格式: table_name/id 或 table_name
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        parts = path.strip('/').split('/')
        
        if len(parts) == 1:
            return {
                "table_name": parts[0],
                "record_id": None,
                "is_collection": True
            }
        elif len(parts) == 2:
            return {
                "table_name": parts[0],
                "record_id": parts[1],
                "is_collection": False
            }
        else:
            raise StorageError(f"无效的路径格式: {path}")
    
    def _get_model_class(self, table_name: str) -> Optional[Type[BaseModel]]:
        """根据表名获取模型类
        
        Args:
            table_name: 表名
            
        Returns:
            Optional[Type[BaseModel]]: 模型类
        """
        # 这里需要根据实际的模型映射来实现
        # 简化实现，实际项目中可能需要一个模型注册表
        model_map = {
            "documents": "app.models.document.Document",
            "test_cases": "app.models.test_case.TestCase",
            "test_results": "app.models.test_result.TestResult",
            "reports": "app.models.report.Report"
        }
        
        model_path = model_map.get(table_name)
        if not model_path:
            return None
        
        try:
            module_path, class_name = model_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            self.logger.error(f"无法导入模型类 {model_path}: {e}")
            return None
    
    def exists(self, path: str) -> bool:
        """检查记录是否存在
        
        Args:
            path: 存储路径
            
        Returns:
            bool: 是否存在
        """
        try:
            path_info = self._parse_path(path)
            
            if path_info["is_collection"]:
                # 检查表是否存在
                session = self._get_session()
                inspector = inspect(session.bind)
                return path_info["table_name"] in inspector.get_table_names()
            else:
                # 检查记录是否存在
                model_class = self._get_model_class(path_info["table_name"])
                if not model_class:
                    return False
                
                session = self._get_session()
                record = session.query(model_class).filter(
                    model_class.id == path_info["record_id"]
                ).first()
                return record is not None
                
        except Exception as e:
            self.logger.error(f"检查存在性失败: {e}")
            return False
    
    def read(self, path: str, **kwargs) -> StorageResult:
        """读取数据库记录
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
                - filters: 查询过滤条件
                - limit: 限制返回数量
                - offset: 偏移量
                - order_by: 排序字段
                
        Returns:
            StorageResult: 读取结果
        """
        try:
            path_info = self._parse_path(path)
            model_class = self._get_model_class(path_info["table_name"])
            
            if not model_class:
                return StorageResult(
                    success=False,
                    error_message=f"未找到模型类: {path_info['table_name']}",
                    operation=StorageOperation.READ,
                    storage_path=path
                )
            
            session = self._get_session()
            
            if path_info["is_collection"]:
                # 查询集合
                query = session.query(model_class)
                
                # 应用过滤条件
                filters = kwargs.get("filters", {})
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(getattr(model_class, field) == value)
                
                # 应用排序
                order_by = kwargs.get("order_by")
                if order_by and hasattr(model_class, order_by):
                    query = query.order_by(getattr(model_class, order_by))
                
                # 应用分页
                offset = kwargs.get("offset", 0)
                limit = kwargs.get("limit")
                
                if offset > 0:
                    query = query.offset(offset)
                if limit:
                    query = query.limit(limit)
                
                records = query.all()
                data = [record.to_dict() if hasattr(record, 'to_dict') else record.__dict__ for record in records]
                
            else:
                # 查询单个记录
                record = session.query(model_class).filter(
                    model_class.id == path_info["record_id"]
                ).first()
                
                if not record:
                    return StorageResult(
                        success=False,
                        error_message=f"记录不存在: {path}",
                        operation=StorageOperation.READ,
                        storage_path=path
                    )
                
                data = record.to_dict() if hasattr(record, 'to_dict') else record.__dict__
            
            return StorageResult(
                success=True,
                data=data,
                operation=StorageOperation.READ,
                storage_path=path
            )
            
        except Exception as e:
            error_msg = f"读取数据库记录失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.READ,
                storage_path=path
            )
    
    def write(self, path: str, data: Any, **kwargs) -> StorageResult:
        """写入数据库记录
        
        Args:
            path: 存储路径
            data: 要写入的数据
            **kwargs: 其他参数
                - update_if_exists: 如果存在则更新 (默认: True)
                
        Returns:
            StorageResult: 写入结果
        """
        try:
            path_info = self._parse_path(path)
            model_class = self._get_model_class(path_info["table_name"])
            
            if not model_class:
                return StorageResult(
                    success=False,
                    error_message=f"未找到模型类: {path_info['table_name']}",
                    operation=StorageOperation.WRITE,
                    storage_path=path
                )
            
            session = self._get_session()
            update_if_exists = kwargs.get("update_if_exists", True)
            
            if path_info["is_collection"]:
                # 批量插入
                if not isinstance(data, list):
                    data = [data]
                
                records = []
                for item in data:
                    if isinstance(item, dict):
                        record = model_class(**item)
                    else:
                        record = item
                    records.append(record)
                
                session.add_all(records)
                
            else:
                # 单个记录操作
                existing_record = session.query(model_class).filter(
                    model_class.id == path_info["record_id"]
                ).first()
                
                if existing_record:
                    if update_if_exists:
                        # 更新现有记录
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if hasattr(existing_record, key):
                                    setattr(existing_record, key, value)
                        record = existing_record
                    else:
                        return StorageResult(
                            success=False,
                            error_message=f"记录已存在且不允许更新: {path}",
                            operation=StorageOperation.WRITE,
                            storage_path=path
                        )
                else:
                    # 创建新记录
                    if isinstance(data, dict):
                        data["id"] = path_info["record_id"]
                        record = model_class(**data)
                    else:
                        record = data
                        record.id = path_info["record_id"]
                    
                    session.add(record)
            
            if self.auto_commit:
                session.commit()
            
            return StorageResult(
                success=True,
                data={"affected_rows": len(data) if isinstance(data, list) else 1},
                operation=StorageOperation.WRITE,
                storage_path=path
            )
            
        except SQLAlchemyError as e:
            if self.auto_commit:
                session.rollback()
            error_msg = f"数据库操作失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.WRITE,
                storage_path=path
            )
        except Exception as e:
            error_msg = f"写入数据库记录失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.WRITE,
                storage_path=path
            )
    
    def delete(self, path: str, **kwargs) -> StorageResult:
        """删除数据库记录
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
                - soft_delete: 是否软删除 (默认: True)
                - filters: 删除过滤条件 (用于集合删除)
                
        Returns:
            StorageResult: 删除结果
        """
        try:
            path_info = self._parse_path(path)
            model_class = self._get_model_class(path_info["table_name"])
            
            if not model_class:
                return StorageResult(
                    success=False,
                    error_message=f"未找到模型类: {path_info['table_name']}",
                    operation=StorageOperation.DELETE,
                    storage_path=path
                )
            
            session = self._get_session()
            soft_delete = kwargs.get("soft_delete", True)
            
            if path_info["is_collection"]:
                # 批量删除
                query = session.query(model_class)
                
                # 应用过滤条件
                filters = kwargs.get("filters", {})
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(getattr(model_class, field) == value)
                
                if soft_delete and hasattr(model_class, 'is_deleted'):
                    # 软删除
                    affected_rows = query.update({"is_deleted": True})
                else:
                    # 硬删除
                    affected_rows = query.delete()
                
            else:
                # 单个记录删除
                record = session.query(model_class).filter(
                    model_class.id == path_info["record_id"]
                ).first()
                
                if not record:
                    return StorageResult(
                        success=False,
                        error_message=f"记录不存在: {path}",
                        operation=StorageOperation.DELETE,
                        storage_path=path
                    )
                
                if soft_delete and hasattr(record, 'is_deleted'):
                    # 软删除
                    record.is_deleted = True
                    affected_rows = 1
                else:
                    # 硬删除
                    session.delete(record)
                    affected_rows = 1
            
            if self.auto_commit:
                session.commit()
            
            return StorageResult(
                success=True,
                data={"affected_rows": affected_rows},
                operation=StorageOperation.DELETE,
                storage_path=path
            )
            
        except SQLAlchemyError as e:
            if self.auto_commit:
                session.rollback()
            error_msg = f"数据库删除操作失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.DELETE,
                storage_path=path
            )
        except Exception as e:
            error_msg = f"删除数据库记录失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.DELETE,
                storage_path=path
            )
    
    def list(self, path: str = "", **kwargs) -> StorageResult:
        """列出数据库表或记录
        
        Args:
            path: 存储路径
            **kwargs: 其他参数
                - include_metadata: 是否包含元数据 (默认: False)
                
        Returns:
            StorageResult: 列表结果
        """
        try:
            if not path:
                # 列出所有表
                session = self._get_session()
                inspector = inspect(session.bind)
                tables = inspector.get_table_names()
                
                return StorageResult(
                    success=True,
                    data=tables,
                    operation=StorageOperation.LIST,
                    storage_path="/"
                )
            
            path_info = self._parse_path(path)
            model_class = self._get_model_class(path_info["table_name"])
            
            if not model_class:
                return StorageResult(
                    success=False,
                    error_message=f"未找到模型类: {path_info['table_name']}",
                    operation=StorageOperation.LIST,
                    storage_path=path
                )
            
            session = self._get_session()
            
            # 获取记录ID列表
            query = session.query(model_class.id)
            
            # 如果支持软删除，排除已删除的记录
            if hasattr(model_class, 'is_deleted'):
                query = query.filter(model_class.is_deleted == False)
            
            record_ids = [str(row[0]) for row in query.all()]
            
            return StorageResult(
                success=True,
                data=record_ids,
                operation=StorageOperation.LIST,
                storage_path=path
            )
            
        except Exception as e:
            error_msg = f"列出数据库内容失败: {str(e)}"
            self.logger.error(error_msg)
            return StorageResult(
                success=False,
                error_message=error_msg,
                operation=StorageOperation.LIST,
                storage_path=path
            )
