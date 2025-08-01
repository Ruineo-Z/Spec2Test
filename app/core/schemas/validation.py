"""Schema验证工具

提供Schema验证、版本兼容性检查等功能。
"""

from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, ValidationError

from .base import BaseSchema, SchemaVersion


class ValidationResult(BaseModel):
    """验证结果"""

    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    schema_version: Optional[str] = None
    validated_data: Optional[Dict[str, Any]] = None


class SchemaValidator:
    """Schema验证器"""

    def __init__(self):
        self.supported_versions = ["1.0"]

    def validate_schema(
        self, data: Dict[str, Any], schema_class: Type[BaseSchema], strict: bool = True
    ) -> ValidationResult:
        """验证数据是否符合指定Schema

        Args:
            data: 要验证的数据
            schema_class: Schema类
            strict: 是否严格模式

        Returns:
            验证结果
        """
        result = ValidationResult(is_valid=False)

        try:
            # 检查Schema版本
            schema_version = data.get("schema_version", "1.0")
            if schema_version not in self.supported_versions:
                result.warnings.append(f"Unsupported schema version: {schema_version}")

            # 验证数据结构
            validated_instance = schema_class(**data)

            result.is_valid = True
            result.schema_version = schema_version
            result.validated_data = validated_instance.model_dump()

        except ValidationError as e:
            result.is_valid = False
            result.errors = [str(error) for error in e.errors()]

        except Exception as e:
            result.is_valid = False
            result.errors = [f"Validation failed: {str(e)}"]

        return result

    def validate_gemini_response(
        self, response_text: str, expected_schema: Type[BaseSchema]
    ) -> ValidationResult:
        """验证Gemini API响应

        Args:
            response_text: Gemini返回的JSON文本
            expected_schema: 期望的Schema类

        Returns:
            验证结果
        """
        import json

        result = ValidationResult(is_valid=False)

        try:
            # 解析JSON
            data = json.loads(response_text)

            # 验证Schema
            return self.validate_schema(data, expected_schema)

        except json.JSONDecodeError as e:
            result.errors = [f"Invalid JSON: {str(e)}"]
            return result

        except Exception as e:
            result.errors = [f"Response validation failed: {str(e)}"]
            return result

    def check_version_compatibility(
        self, schema_version: str, target_version: str = "1.0"
    ) -> bool:
        """检查版本兼容性

        Args:
            schema_version: 数据的Schema版本
            target_version: 目标版本

        Returns:
            是否兼容
        """
        # 简单的版本兼容性检查
        # 实际项目中可能需要更复杂的版本比较逻辑
        return schema_version in self.supported_versions

    def migrate_schema(
        self, data: Dict[str, Any], from_version: str, to_version: str
    ) -> Dict[str, Any]:
        """Schema版本迁移

        Args:
            data: 原始数据
            from_version: 源版本
            to_version: 目标版本

        Returns:
            迁移后的数据
        """
        # 目前只支持1.0版本，暂不需要迁移
        if from_version == to_version:
            return data

        # 未来可以在这里添加版本迁移逻辑
        raise NotImplementedError(
            f"Migration from {from_version} to {to_version} not implemented"
        )


# 全局验证器实例
_validator = SchemaValidator()


def validate_schema(
    data: Dict[str, Any], schema_class: Type[BaseSchema], strict: bool = True
) -> ValidationResult:
    """便捷的Schema验证函数

    Args:
        data: 要验证的数据
        schema_class: Schema类
        strict: 是否严格模式

    Returns:
        验证结果
    """
    return _validator.validate_schema(data, schema_class, strict)


def validate_gemini_response(
    response_text: str, expected_schema: Type[BaseSchema]
) -> ValidationResult:
    """便捷的Gemini响应验证函数

    Args:
        response_text: Gemini返回的JSON文本
        expected_schema: 期望的Schema类

    Returns:
        验证结果
    """
    return _validator.validate_gemini_response(response_text, expected_schema)
