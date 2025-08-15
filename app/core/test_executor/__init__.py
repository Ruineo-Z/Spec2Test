"""
测试执行器模块

专门用于API测试用例执行的模块，提供测试专用的HTTP客户端和相关功能。
"""

from .http_client import (
    TestHTTPClient, TestRequest, TestResult, TestAssertion,
    TestStatus, AssertionType
)

__all__ = [
    # 核心类
    "TestHTTPClient",
    "TestRequest", 
    "TestResult",
    "TestAssertion",
    
    # 枚举类
    "TestStatus",
    "AssertionType"
]
