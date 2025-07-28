"""核心模块

提供自动化测试流水线的核心功能和数据模型。
"""

from .models import (
    # 枚举类型
    TestCaseType,
    HttpMethod,
    TestStatus,
    DocumentQuality,
    
    # 数据模型
    APIEndpoint,
    TestCase,
    TestResult,
    DocumentAnalysis,
    TestSuite,
    TestReport,
)

__all__ = [
    # 枚举类型
    "TestCaseType",
    "HttpMethod",
    "TestStatus",
    "DocumentQuality",
    
    # 数据模型
    "APIEndpoint",
    "TestCase",
    "TestResult",
    "DocumentAnalysis",
    "TestSuite",
    "TestReport",
]

__version__ = "0.1.0"