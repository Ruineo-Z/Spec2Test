"""核心模块

提供自动化测试流水线的核心功能和数据模型。
"""

from .models import (  # 枚举类型; 数据模型
    APIEndpoint,
    DocumentAnalysis,
    DocumentQuality,
    HttpMethod,
    RiskCategory,
    RiskItem,
    RiskLevel,
    TestCase,
    TestCaseType,
    TestReport,
    TestResult,
    TestStatus,
    TestSuite,
)

__all__ = [
    # 枚举类型
    "TestCaseType",
    "HttpMethod",
    "TestStatus",
    "DocumentQuality",
    "RiskLevel",
    "RiskCategory",
    # 数据模型
    "APIEndpoint",
    "TestCase",
    "TestResult",
    "DocumentAnalysis",
    "RiskItem",
    "TestSuite",
    "TestReport",
]

__version__ = "0.1.0"
