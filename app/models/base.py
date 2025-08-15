"""
数据库基础模型模块

定义所有数据模型的基类，提供通用字段和方法。
包含时间戳、主键、软删除等基础功能。
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Boolean, Integer, func, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.ext.declarative import declared_attr


class BaseModel(DeclarativeBase):
    """数据库基础模型类
    
    所有数据模型的基类，提供通用字段和方法：
    - id: 主键字段
    - created_at: 创建时间（UTC）
    - updated_at: 更新时间（UTC）
    - is_deleted: 软删除标记
    """
    
    # 主键字段
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="主键ID"
    )
    
    # 时间戳字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )
    
    # 软删除字段
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="软删除标记"
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名
        
        将类名转换为下划线格式作为表名
        例如：UserProfile -> user_profile
        """
        import re
        # 将驼峰命名转换为下划线命名
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def to_dict(self, exclude_fields: Optional[set] = None) -> Dict[str, Any]:
        """将模型转换为字典
        
        Args:
            exclude_fields: 要排除的字段集合
            
        Returns:
            模型字典表示
        """
        exclude_fields = exclude_fields or set()
        result = {}
        
        for column in self.__table__.columns:
            field_name = column.name
            if field_name not in exclude_fields:
                value = getattr(self, field_name)
                # 处理datetime对象
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                else:
                    result[field_name] = value
                    
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: Optional[set] = None) -> None:
        """从字典更新模型属性
        
        Args:
            data: 包含更新数据的字典
            exclude_fields: 要排除的字段集合
        """
        exclude_fields = exclude_fields or {'id', 'created_at'}
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
    
    def soft_delete(self) -> None:
        """软删除记录
        
        设置is_deleted为True，不实际删除数据
        """
        self.is_deleted = True
        self.updated_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        """恢复软删除的记录
        
        设置is_deleted为False
        """
        self.is_deleted = False
        self.updated_at = datetime.now(timezone.utc)
    
    @classmethod
    def get_table_name(cls) -> str:
        """获取表名
        
        Returns:
            表名字符串
        """
        return cls.__tablename__
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"


# 事件监听器：自动更新updated_at字段
@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """在更新前自动设置updated_at字段"""
    target.updated_at = datetime.now(timezone.utc)


class TimestampMixin:
    """时间戳混入类
    
    为不继承BaseModel的类提供时间戳功能
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )


class SoftDeleteMixin:
    """软删除混入类
    
    为不继承BaseModel的类提供软删除功能
    """
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="软删除标记"
    )
    
    def soft_delete(self) -> None:
        """软删除记录"""
        self.is_deleted = True
        if hasattr(self, 'updated_at'):
            self.updated_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        """恢复软删除的记录"""
        self.is_deleted = False
        if hasattr(self, 'updated_at'):
            self.updated_at = datetime.now(timezone.utc)


class AuditMixin:
    """审计混入类
    
    提供创建者和更新者追踪功能
    """
    
    created_by: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        comment="创建者"
    )
    
    updated_by: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        comment="更新者"
    )
    
    def set_creator(self, user_id: str) -> None:
        """设置创建者"""
        self.created_by = user_id
    
    def set_updater(self, user_id: str) -> None:
        """设置更新者"""
        self.updated_by = user_id
