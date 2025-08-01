"""结构化输出管理器

管理LLM结构化输出的生成、验证和处理。
"""

from typing import Any, Dict, Type

from app.core.schemas.base import BaseSchema


class StructuredOutputManager:
    """结构化输出管理器"""

    def __init__(self):
        pass

    def validate_output(
        self, data: Dict[str, Any], schema: Type[BaseSchema]
    ) -> BaseSchema:
        """验证输出数据"""
        return schema(**data)

    def convert_to_json_schema(self, schema: Type[BaseSchema]) -> Dict[str, Any]:
        """转换为JSON Schema"""
        return schema.model_json_schema()
