"""
测试运行器

管理测试用例的执行，支持单个测试、批量测试和并发控制。
"""

import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.core.shared.utils.logger import get_logger
from app.core.test_generator.models import TestCase, TestSuite
from .http_client import TestHTTPClient, TestRequest, TestAssertion, TestResult, TestStatus, AssertionType
from .models import TestExecutionResult, TestSuiteExecutionResult, ExecutionConfig, AssertionResult


class TestRunner:
    """测试运行器
    
    负责执行测试用例，支持单个和批量执行，以及并发控制。
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        """初始化测试运行器
        
        Args:
            config: 执行配置
        """
        self.config = config or ExecutionConfig()
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 创建HTTP客户端
        self.http_client = TestHTTPClient(
            base_url=None,  # 测试运行器不需要固定的base_url
            config={
                "default_timeout": self.config.request_timeout,
                "max_retries": self.config.max_retries,
                "retry_delay": self.config.retry_delay,
                "verify_ssl": self.config.verify_ssl
            }
        )
        
        self.logger.info(f"测试运行器初始化完成: 最大并发={self.config.max_concurrent_tests}")
    
    def execute_test_case(self, test_case: TestCase, base_url: Optional[str] = None) -> TestExecutionResult:
        """执行单个测试用例
        
        Args:
            test_case: 测试用例
            base_url: 基础URL，如果不提供则使用测试用例中的完整URL
            
        Returns:
            TestExecutionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始执行测试用例: {test_case.title}")
            
            # 构建请求URL
            if base_url:
                url = f"{base_url.rstrip('/')}{test_case.endpoint_path}"
            else:
                url = test_case.endpoint_path
            
            # 创建测试请求
            test_request = TestRequest(
                method=test_case.http_method.upper(),
                url=url,
                headers=test_case.request_headers or {},
                params=test_case.request_params or {},
                json_data=test_case.request_body,
                timeout=self.config.request_timeout
            )
            
            # 转换断言
            assertions = self._convert_test_assertions(test_case.assertions)
            
            # 执行测试
            test_result = self.http_client.execute_test_case(
                test_request, assertions, test_case.case_id
            )
            
            # 转换为标准执行结果
            execution_result = self._convert_to_execution_result(test_case, test_result, start_time)
            
            self.logger.info(f"测试用例执行完成: {test_case.title} - {execution_result.status}")
            return execution_result
            
        except Exception as e:
            error_msg = f"测试用例执行失败: {str(e)}"
            self.logger.error(error_msg)
            
            # 创建错误结果
            execution_result = TestExecutionResult(
                test_id=test_case.case_id,
                status=TestStatus.ERROR,
                request_url=test_case.endpoint_path,
                request_method=test_case.http_method,
                error_message=error_msg,
                started_at=datetime.fromtimestamp(start_time),
                completed_at=datetime.now(),
                duration=time.time() - start_time
            )
            
            return execution_result
    
    def execute_test_suite(self, test_suite: TestSuite, base_url: Optional[str] = None) -> TestSuiteExecutionResult:
        """执行测试套件
        
        Args:
            test_suite: 测试套件
            base_url: 基础URL
            
        Returns:
            TestSuiteExecutionResult: 套件执行结果
        """
        start_time = time.time()
        
        self.logger.info(f"开始执行测试套件: {test_suite.name} ({len(test_suite.test_cases)}个测试用例)")
        
        # 创建套件执行结果
        suite_result = TestSuiteExecutionResult(
            suite_id=test_suite.suite_id,
            suite_name=test_suite.name,
            started_at=datetime.fromtimestamp(start_time)
        )
        
        # 使用基础URL或套件中的URL
        effective_base_url = base_url or test_suite.base_url
        
        try:
            if self.config.max_concurrent_tests > 1 and len(test_suite.test_cases) > 1:
                # 并发执行
                test_results = self._execute_concurrent(test_suite.test_cases, effective_base_url)
            else:
                # 串行执行
                test_results = self._execute_sequential(test_suite.test_cases, effective_base_url)
            
            # 添加所有测试结果
            for result in test_results:
                suite_result.add_test_result(result)
            
            # 完成执行
            suite_result.completed_at = datetime.now()
            suite_result.total_duration = time.time() - start_time
            
            self.logger.info(f"测试套件执行完成: {suite_result.suite_name}")
            self.logger.info(f"  总测试数: {suite_result.total_tests}")
            self.logger.info(f"  通过: {suite_result.passed_tests}")
            self.logger.info(f"  失败: {suite_result.failed_tests}")
            self.logger.info(f"  错误: {suite_result.error_tests}")
            self.logger.info(f"  成功率: {suite_result.success_rate:.1%}")
            self.logger.info(f"  总耗时: {suite_result.total_duration:.2f}秒")
            
            return suite_result
            
        except Exception as e:
            error_msg = f"测试套件执行失败: {str(e)}"
            self.logger.error(error_msg)
            
            suite_result.completed_at = datetime.now()
            suite_result.total_duration = time.time() - start_time
            
            return suite_result
    
    def _execute_sequential(self, test_cases: List[TestCase], base_url: Optional[str]) -> List[TestExecutionResult]:
        """串行执行测试用例"""
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            if self.config.verbose:
                self.logger.info(f"执行测试 {i}/{len(test_cases)}: {test_case.title}")
            
            result = self.execute_test_case(test_case, base_url)
            results.append(result)
        
        return results
    
    def _execute_concurrent(self, test_cases: List[TestCase], base_url: Optional[str]) -> List[TestExecutionResult]:
        """并发执行测试用例"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_tests) as executor:
            # 提交所有任务
            future_to_test = {
                executor.submit(self.execute_test_case, test_case, base_url): test_case
                for test_case in test_cases
            }
            
            # 收集结果
            for future in as_completed(future_to_test):
                test_case = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if self.config.verbose:
                        self.logger.info(f"并发测试完成: {test_case.title} - {result.status}")
                        
                except Exception as e:
                    self.logger.error(f"并发测试执行异常: {test_case.title} - {e}")
                    
                    # 创建错误结果
                    error_result = TestExecutionResult(
                        test_id=test_case.case_id,
                        status=TestStatus.ERROR,
                        request_url=test_case.endpoint_path,
                        request_method=test_case.http_method,
                        error_message=str(e),
                        started_at=datetime.now(),
                        completed_at=datetime.now(),
                        duration=0.0
                    )
                    results.append(error_result)
        
        return results
    
    def _convert_test_assertions(self, test_assertions: List) -> List[TestAssertion]:
        """转换测试断言格式"""
        assertions = []
        
        for assertion in test_assertions:
            if hasattr(assertion, 'assertion_type'):
                # 从TestAssertion对象转换
                assertion_type = self._map_assertion_type(assertion.assertion_type)
                test_assertion = TestAssertion(
                    type=assertion_type,
                    expected=assertion.expected_value
                )
                assertions.append(test_assertion)
        
        return assertions
    
    def _map_assertion_type(self, assertion_type: str) -> AssertionType:
        """映射断言类型"""
        mapping = {
            "status_code": AssertionType.STATUS_CODE,
            "response_time": AssertionType.RESPONSE_TIME,
            "response_body": AssertionType.BODY_CONTAINS,
            "header_exists": AssertionType.HEADER_EXISTS,
            "header_value": AssertionType.HEADER_VALUE,
            "json_path": AssertionType.JSON_PATH
        }
        return mapping.get(assertion_type, AssertionType.STATUS_CODE)
    
    def _convert_to_execution_result(self, test_case: TestCase, test_result: TestResult, start_time: float) -> TestExecutionResult:
        """转换为标准执行结果格式"""
        
        # 转换断言结果
        assertion_results = []
        for assertion in test_result.assertions:
            assertion_result = AssertionResult(
                assertion_type=assertion.type.value,
                expected=assertion.expected,
                actual=assertion.actual,
                passed=assertion.passed or False,
                message=assertion.message or ""
            )
            assertion_results.append(assertion_result)
        
        # 创建执行结果
        execution_result = TestExecutionResult(
            test_id=test_case.case_id,
            status=test_result.status,
            request_url=test_result.request.url,
            request_method=test_result.request.method,
            request_headers=test_result.request.headers,
            request_body=test_result.request.json_data,
            response_status_code=test_result.response.status_code if test_result.response else None,
            response_headers=dict(test_result.response.headers) if test_result.response else None,
            response_body=test_result.response.text if test_result.response else None,
            response_time=test_result.response_time,
            assertion_results=assertion_results,
            error_message=test_result.error_message,
            started_at=datetime.fromtimestamp(start_time),
            completed_at=datetime.fromtimestamp(test_result.end_time) if test_result.end_time else datetime.now(),
            duration=test_result.duration
        )
        
        return execution_result
