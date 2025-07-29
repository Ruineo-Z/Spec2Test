"""Spec2Test - AI驱动的自动化测试流水线

从API规范文档到测试报告的全流程自动化工具。
"""

__version__ = "0.1.0"
__author__ = "Sean"
__email__ = "sean@deepractice.ai"
__description__ = "AI-driven automated testing pipeline from API specs to test reports"

# 导出核心组件
from app.core.models import (
    APIEndpoint,
    DocumentAnalysis,
    TestCase,
    TestReport,
    TestResult,
    TestSuite,
)

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "APIEndpoint",
    "TestCase",
    "TestResult",
    "TestSuite",
    "TestReport",
    "DocumentAnalysis",
]
