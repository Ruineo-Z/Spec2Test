"""Schema管理器

管理LLM输出Schema的注册、验证和转换。
"""

from typing import Any, Dict, Type

from app.core.schemas.base import BaseSchema


class SchemaManager:
    """Schema管理器"""

    def __init__(self):
        self._schemas: Dict[str, Type[BaseSchema]] = {}

    def register_schema(self, name: str, schema_class: Type[BaseSchema]) -> None:
        """注册Schema"""
        self._schemas[name] = schema_class

    def get_schema(self, name: str) -> Type[BaseSchema]:
        """获取Schema"""
        if name not in self._schemas:
            raise ValueError(f"Schema '{name}' not found")
        return self._schemas[name]

    def list_schemas(self) -> Dict[str, Type[BaseSchema]]:
        """列出所有Schema"""
        return self._schemas.copy()
