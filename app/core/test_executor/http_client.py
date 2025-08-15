"""
测试执行器HTTP客户端

专门用于API测试用例执行的HTTP客户端，基于共享HTTP组件提供测试专用功能。
"""

import time
import json
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

from app.core.shared.http import HTTPClient, HTTPResponse
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class AssertionType(Enum):
    """断言类型枚举"""
    STATUS_CODE = "status_code"
    RESPONSE_TIME = "response_time"
    RESPONSE_SIZE = "response_size"
    HEADER_EXISTS = "header_exists"
    HEADER_VALUE = "header_value"
    BODY_CONTAINS = "body_contains"
    BODY_NOT_CONTAINS = "body_not_contains"
    JSON_PATH = "json_path"
    JSON_SCHEMA = "json_schema"
    REGEX_MATCH = "regex_match"


@dataclass
class TestAssertion:
    """测试断言"""
    type: AssertionType
    expected: Any
    actual: Optional[Any] = None
    passed: Optional[bool] = None
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type.value,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "message": self.message
        }


@dataclass
class TestRequest:
    """测试请求定义"""
    method: str
    url: str
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    json_data: Optional[Dict[str, Any]] = None
    form_data: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, Any]] = None
    timeout: Optional[float] = 30.0
    allow_redirects: bool = True
    verify_ssl: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "method": self.method,
            "url": self.url,
            "headers": self.headers or {},
            "params": self.params or {},
            "json_data": self.json_data,
            "form_data": self.form_data,
            "files": self.files,
            "timeout": self.timeout,
            "allow_redirects": self.allow_redirects,
            "verify_ssl": self.verify_ssl
        }


@dataclass
class TestResult:
    """测试执行结果"""
    test_id: str
    status: TestStatus
    request: TestRequest
    response: Optional[HTTPResponse] = None
    assertions: List[TestAssertion] = field(default_factory=list)
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def passed(self) -> bool:
        """是否通过"""
        return self.status == TestStatus.PASSED
    
    @property
    def failed(self) -> bool:
        """是否失败"""
        return self.status in [TestStatus.FAILED, TestStatus.ERROR]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_id": self.test_id,
            "status": self.status.value,
            "request": self.request.to_dict(),
            "response": {
                "status_code": self.response.status_code if self.response else None,
                "headers": dict(self.response.headers) if self.response else {},
                "content": self.response.content if self.response else None,
                "json_data": self.response.json_data if self.response else None,
                "elapsed_time": self.response.elapsed_time if self.response else None
            } if self.response else None,
            "assertions": [assertion.to_dict() for assertion in self.assertions],
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "passed": self.passed,
            "failed": self.failed
        }


class TestHTTPClient:
    """测试执行器HTTP客户端
    
    专门用于API测试用例执行，提供测试专用功能。
    """
    
    def __init__(self, base_url: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """初始化测试HTTP客户端
        
        Args:
            base_url: 基础URL
            config: 客户端配置
        """
        self.base_url = base_url
        self.config = config or {}
        
        # 创建底层HTTP客户端，配置为不抛出状态码异常
        http_config = config.copy() if config else {}
        http_config["raise_for_status"] = False  # 测试执行器需要处理所有状态码
        self.http_client = HTTPClient(base_url, http_config)
        
        # 测试配置
        self.default_timeout = self.config.get("default_timeout", 30.0)
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1.0)
        self.verify_ssl = self.config.get("verify_ssl", True)
        
        self.logger = get_logger(f"{self.__class__.__name__}")
        self.logger.info(f"测试HTTP客户端初始化完成: {base_url or 'No base URL'}")
    
    def execute_test_case(self, test_request: TestRequest, 
                         assertions: List[TestAssertion], 
                         test_id: str) -> TestResult:
        """执行单个测试用例
        
        Args:
            test_request: 测试请求
            assertions: 断言列表
            test_id: 测试ID
            
        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()
        
        result = TestResult(
            test_id=test_id,
            status=TestStatus.RUNNING,
            request=test_request,
            start_time=start_time
        )
        
        try:
            self.logger.info(f"开始执行测试用例: {test_id}")
            
            # 执行HTTP请求
            response = self._execute_request(test_request)
            result.response = response
            
            # 执行断言
            result.assertions = self._execute_assertions(response, assertions)
            
            # 判断测试结果
            all_passed = all(assertion.passed for assertion in result.assertions)
            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            
            end_time = time.time()
            result.end_time = end_time
            result.execution_time = end_time - start_time
            
            self.logger.info(f"测试用例执行完成: {test_id}, 状态: {result.status.value}")
            
        except Exception as e:
            end_time = time.time()
            result.end_time = end_time
            result.execution_time = end_time - start_time
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            
            self.logger.error(f"测试用例执行异常: {test_id}, 错误: {e}")
        
        return result
    
    def _execute_request(self, test_request: TestRequest) -> HTTPResponse:
        """执行HTTP请求

        Args:
            test_request: 测试请求

        Returns:
            HTTPResponse: HTTP响应
        """
        # 准备请求参数
        kwargs = {
            "headers": test_request.headers,
            "params": test_request.params,
            "timeout": test_request.timeout or self.default_timeout,
            "allow_redirects": test_request.allow_redirects,
            "verify": test_request.verify_ssl
        }

        # 添加请求体
        if test_request.json_data:
            kwargs["json"] = test_request.json_data
        elif test_request.form_data:
            kwargs["data"] = test_request.form_data

        if test_request.files:
            kwargs["files"] = test_request.files

        # 执行请求
        method = test_request.method.upper()

        if method == "GET":
            return self.http_client.get(test_request.url, **kwargs)
        elif method == "POST":
            return self.http_client.post(test_request.url, **kwargs)
        elif method == "PUT":
            return self.http_client.put(test_request.url, **kwargs)
        elif method == "DELETE":
            return self.http_client.delete(test_request.url, **kwargs)
        elif method == "PATCH":
            return self.http_client.patch(test_request.url, **kwargs)
        elif method == "HEAD":
            return self.http_client.head(test_request.url, **kwargs)
        elif method == "OPTIONS":
            return self.http_client.options(test_request.url, **kwargs)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
    
    def _execute_assertions(self, response: HTTPResponse, 
                          assertions: List[TestAssertion]) -> List[TestAssertion]:
        """执行断言
        
        Args:
            response: HTTP响应
            assertions: 断言列表
            
        Returns:
            List[TestAssertion]: 执行后的断言列表
        """
        executed_assertions = []
        
        for assertion in assertions:
            try:
                executed_assertion = self._execute_single_assertion(response, assertion)
                executed_assertions.append(executed_assertion)
            except Exception as e:
                assertion.passed = False
                assertion.message = f"断言执行异常: {str(e)}"
                executed_assertions.append(assertion)
                self.logger.error(f"断言执行异常: {assertion.type.value}, 错误: {e}")
        
        return executed_assertions
    
    def _execute_single_assertion(self, response: HTTPResponse, 
                                 assertion: TestAssertion) -> TestAssertion:
        """执行单个断言
        
        Args:
            response: HTTP响应
            assertion: 断言
            
        Returns:
            TestAssertion: 执行后的断言
        """
        assertion_type = assertion.type
        expected = assertion.expected
        
        if assertion_type == AssertionType.STATUS_CODE:
            actual = response.status_code
            assertion.actual = actual
            assertion.passed = actual == expected
            assertion.message = f"状态码断言: 期望 {expected}, 实际 {actual}"
            
        elif assertion_type == AssertionType.RESPONSE_TIME:
            actual = response.elapsed_time
            assertion.actual = actual
            assertion.passed = actual <= expected
            assertion.message = f"响应时间断言: 期望 <= {expected}s, 实际 {actual}s"
            
        elif assertion_type == AssertionType.RESPONSE_SIZE:
            actual = len(response.content) if response.content else 0
            assertion.actual = actual
            assertion.passed = actual <= expected
            assertion.message = f"响应大小断言: 期望 <= {expected} bytes, 实际 {actual} bytes"
            
        elif assertion_type == AssertionType.HEADER_EXISTS:
            actual = expected in response.headers
            assertion.actual = actual
            assertion.passed = actual
            assertion.message = f"响应头存在断言: 期望存在 '{expected}', 实际 {'存在' if actual else '不存在'}"
            
        elif assertion_type == AssertionType.HEADER_VALUE:
            header_name, expected_value = expected
            actual = response.headers.get(header_name)
            assertion.actual = actual
            assertion.passed = actual == expected_value
            assertion.message = f"响应头值断言: {header_name} 期望 '{expected_value}', 实际 '{actual}'"
            
        elif assertion_type == AssertionType.BODY_CONTAINS:
            content = response.content or ""
            actual = expected in content
            assertion.actual = actual
            assertion.passed = actual
            assertion.message = f"响应体包含断言: 期望包含 '{expected}', 实际 {'包含' if actual else '不包含'}"
            
        elif assertion_type == AssertionType.BODY_NOT_CONTAINS:
            content = response.content or ""
            actual = expected not in content
            assertion.actual = actual
            assertion.passed = actual
            assertion.message = f"响应体不包含断言: 期望不包含 '{expected}', 实际 {'不包含' if actual else '包含'}"
            
        elif assertion_type == AssertionType.JSON_PATH:
            json_path, expected_value = expected
            try:
                import jsonpath_ng
                jsonpath_expr = jsonpath_ng.parse(json_path)
                matches = jsonpath_expr.find(response.json_data or {})
                actual = matches[0].value if matches else None
                assertion.actual = actual
                assertion.passed = actual == expected_value
                assertion.message = f"JSON路径断言: {json_path} 期望 '{expected_value}', 实际 '{actual}'"
            except ImportError:
                assertion.passed = False
                assertion.message = "JSON路径断言需要安装 jsonpath-ng 库"
            except Exception as e:
                assertion.passed = False
                assertion.message = f"JSON路径断言执行失败: {str(e)}"
                
        elif assertion_type == AssertionType.REGEX_MATCH:
            import re
            content = response.content or ""
            pattern = expected
            actual = bool(re.search(pattern, content))
            assertion.actual = actual
            assertion.passed = actual
            assertion.message = f"正则匹配断言: 模式 '{pattern}', 实际 {'匹配' if actual else '不匹配'}"
            
        else:
            assertion.passed = False
            assertion.message = f"不支持的断言类型: {assertion_type.value}"
        
        return assertion
    
    def execute_test_suite(self, test_cases: List[Dict[str, Any]]) -> List[TestResult]:
        """执行测试套件
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            List[TestResult]: 测试结果列表
        """
        results = []
        
        self.logger.info(f"开始执行测试套件: {len(test_cases)} 个测试用例")
        
        for i, test_case in enumerate(test_cases):
            try:
                # 解析测试用例
                test_id = test_case.get("id", f"test_{i+1}")
                
                # 构建测试请求
                request_data = test_case.get("request", {})
                test_request = TestRequest(
                    method=request_data.get("method", "GET"),
                    url=request_data.get("url", ""),
                    headers=request_data.get("headers"),
                    params=request_data.get("params"),
                    json_data=request_data.get("json"),
                    form_data=request_data.get("data"),
                    files=request_data.get("files"),
                    timeout=request_data.get("timeout"),
                    allow_redirects=request_data.get("allow_redirects", True),
                    verify_ssl=request_data.get("verify_ssl", True)
                )
                
                # 构建断言列表
                assertions_data = test_case.get("assertions", [])
                assertions = []
                for assertion_data in assertions_data:
                    assertion = TestAssertion(
                        type=AssertionType(assertion_data["type"]),
                        expected=assertion_data["expected"]
                    )
                    assertions.append(assertion)
                
                # 执行测试用例
                result = self.execute_test_case(test_request, assertions, test_id)
                results.append(result)
                
            except Exception as e:
                # 创建错误结果
                error_result = TestResult(
                    test_id=test_case.get("id", f"test_{i+1}"),
                    status=TestStatus.ERROR,
                    request=TestRequest(method="GET", url=""),
                    error_message=f"测试用例解析失败: {str(e)}"
                )
                results.append(error_result)
                self.logger.error(f"测试用例解析失败: {e}")
        
        # 统计结果
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if r.failed)
        
        self.logger.info(f"测试套件执行完成: 总计 {len(results)}, 通过 {passed}, 失败 {failed}")
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            Dict[str, Any]: 性能统计信息
        """
        return self.http_client.get_performance_stats()
    
    def close(self):
        """关闭客户端"""
        if hasattr(self.http_client, 'close'):
            self.http_client.close()
        self.logger.info("测试HTTP客户端已关闭")
