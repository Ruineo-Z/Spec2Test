"""LLM输出Schema管理模块

统一管理所有LLM结构化输出的Schema定义，确保：
1. Schema版本控制
2. 类型安全
3. 向后兼容性
4. 清晰的模块分离
"""

from .analysis import (
    DetailedAnalysisSchema,
    DocumentAnalysisSchema,
    IssueSchema,
    QuickAssessmentSchema,
    SuggestionSchema,
)
from .base import AnalysisType, BaseSchema, QualityLevel, SchemaVersion
from .generation import (
    AssertionSchema,
    BatchResultSchema,
    CaseSchema,
    GenerationResultSchema,
    TestStepSchema,
)
from .validation import SchemaValidator, ValidationResult, validate_schema

__all__ = [
    # Base schemas
    "BaseSchema",
    "QualityLevel",
    "AnalysisType",
    "SchemaVersion",
    # Analysis schemas
    "QuickAssessmentSchema",
    "DocumentAnalysisSchema",
    "DetailedAnalysisSchema",
    "IssueSchema",
    "SuggestionSchema",
    # Generation schemas
    "CaseSchema",
    "GenerationResultSchema",
    "BatchResultSchema",
    "TestStepSchema",
    "AssertionSchema",
    # Validation
    "SchemaValidator",
    "ValidationResult",
    "validate_schema",
]

# Schema版本信息
SCHEMA_VERSION = "1.0.0"
SUPPORTED_VERSIONS = ["1.0.0"]


def get_schema_info():
    """获取Schema版本信息"""
    return {
        "version": SCHEMA_VERSION,
        "supported_versions": SUPPORTED_VERSIONS,
        "schemas": {
            "analysis": [
                "QuickAssessmentSchema",
                "DocumentAnalysisSchema",
                "DetailedAnalysisSchema",
            ],
            "generation": ["TestCaseSchema", "TestCaseGenerationSchema"],
        },
    }
