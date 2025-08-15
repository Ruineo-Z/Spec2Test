"""
数据模型包

包含所有数据库模型定义。
"""

from .base import BaseModel, TimestampMixin, SoftDeleteMixin, AuditMixin
from .document import Document, DocumentType, DocumentStatus
from .test_case import TestCase, TestCaseType, TestCasePriority, HTTPMethod
from .test_result import TestResult, TestStatus, FailureType
from .report import Report, ReportType, ReportStatus, ReportFormat

__all__ = [
    # 基础模型
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",

    # 核心模型
    "Document",
    "TestCase",
    "TestResult",
    "Report",

    # 枚举类型
    "DocumentType",
    "DocumentStatus",
    "TestCaseType",
    "TestCasePriority",
    "HTTPMethod",
    "TestStatus",
    "FailureType",
    "ReportType",
    "ReportStatus",
    "ReportFormat"
]
