"""
测试执行器模块

专门用于API测试用例执行的模块，提供测试专用的HTTP客户端和相关功能。
"""

from .http_client import (
    TestHTTPClient, TestRequest, TestResult, TestAssertion,
    TestStatus, AssertionType
)
from .models import (
    TestExecutionResult, TestSuiteExecutionResult, ExecutionConfig,
    AssertionResult, TestTask, TaskScheduleConfig
)
from .runner import TestRunner
from .scheduler import TestTaskScheduler, TaskPriority

__all__ = [
    # 核心类
    "TestHTTPClient",
    "TestRequest",
    "TestResult",
    "TestAssertion",

    # 枚举类
    "TestStatus",
    "AssertionType",

    # 新增模型类
    "TestExecutionResult",
    "TestSuiteExecutionResult",
    "ExecutionConfig",
    "AssertionResult",
    "TestTask",
    "TaskScheduleConfig",

    # 新增执行器类
    "TestRunner",
    "TestTaskScheduler",
    "TaskPriority"
]
