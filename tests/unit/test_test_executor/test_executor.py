"""
测试执行器单元测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from datetime import datetime

from app.core.test_executor.executor import TestExecutor
from app.core.test_executor.models import (
    TestExecution, ExecutionStatus, ExecutionConfig,
    TestResult, AssertionResult, ExecutionRequest
)
from app.core.test_generator.models import (
    TestCase, TestSuite, TestType, AssertionType, Assertion
)
from app.core.document_analyzer.models import Endpoint


class TestTestExecutor:
    """测试测试执行器"""
    
    def setup_method(self):
        """测试前设置"""
        self.executor = TestExecutor()
    
    @pytest.fixture
    def sample_test_case(self):
        """示例测试用例"""
        return TestCase(
            name="test_get_user",
            description="Test getting user by ID",
            test_type=TestType.POSITIVE,
            endpoint=Endpoint(
                path="/users/{id}",
                method="GET",
                responses={"200": {"description": "Success"}}
            ),
            request={
                "path_params": {"id": "123"},
                "headers": {"Accept": "application/json"}
            },
            expected_response={
                "status_code": 200,
                "schema_validation": True
            },
            assertions=[
                Assertion(
                    assertion_type=AssertionType.STATUS_CODE,
                    expected_value=200,
                    description="Status code should be 200"
                ),
                Assertion(
                    assertion_type=AssertionType.RESPONSE_SCHEMA,
                    expected_value="user_schema",
                    description="Response should match user schema"
                )
            ]
        )
    
    @pytest.fixture
    def sample_test_suite(self, sample_test_case):
        """示例测试套件"""
        return TestSuite(
            name="User API Tests",
            description="Tests for user API endpoints",
            test_cases=[sample_test_case]
        )
    
    @pytest.fixture
    def execution_config(self):
        """执行配置"""
        return ExecutionConfig(
            base_url="https://api.example.com",
            timeout=30,
            max_retries=3,
            parallel_execution=True,
            max_concurrent_requests=10,
            headers={"Authorization": "Bearer test-token"}
        )
    
    async def test_execute_test_case_success(self, sample_test_case, execution_config):
        """测试成功执行单个测试用例"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value='{"id": "123", "name": "John"}')
        mock_response.json = AsyncMock(return_value={"id": "123", "name": "John"})
        
        with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await self.executor.execute_test_case(sample_test_case, execution_config)
            
            assert isinstance(result, TestResult)
            assert result.test_case_name == "test_get_user"
            assert result.status == ExecutionStatus.PASSED
            assert result.response_time > 0
            assert result.actual_response.status_code == 200
            assert len(result.assertion_results) == 2
            
            # 检查断言结果
            status_assertion = next(
                (ar for ar in result.assertion_results if ar.assertion_type == AssertionType.STATUS_CODE),
                None
            )
            assert status_assertion is not None
            assert status_assertion.passed is True
    
    async def test_execute_test_case_http_error(self, sample_test_case, execution_config):
        """测试HTTP请求错误的情况"""
        with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = aiohttp.ClientError("Connection failed")
            
            result = await self.executor.execute_test_case(sample_test_case, execution_config)
            
            assert result.status == ExecutionStatus.ERROR
            assert "Connection failed" in result.error_message
    
    async def test_execute_test_case_assertion_failure(self, sample_test_case, execution_config):
        """测试断言失败的情况"""
        # 修改测试用例期望状态码为201，但实际返回200
        sample_test_case.assertions[0].expected_value = 201
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value='{"id": "123"}')
        mock_response.json = AsyncMock(return_value={"id": "123"})
        
        with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await self.executor.execute_test_case(sample_test_case, execution_config)
            
            assert result.status == ExecutionStatus.FAILED
            
            # 检查失败的断言
            status_assertion = next(
                (ar for ar in result.assertion_results if ar.assertion_type == AssertionType.STATUS_CODE),
                None
            )
            assert status_assertion is not None
            assert status_assertion.passed is False
            assert "Expected: 201, Actual: 200" in status_assertion.error_message
    
    async def test_execute_test_suite_success(self, sample_test_suite, execution_config):
        """测试成功执行测试套件"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value='{"id": "123", "name": "John"}')
        mock_response.json = AsyncMock(return_value={"id": "123", "name": "John"})
        
        with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            execution = await self.executor.execute_test_suite(sample_test_suite, execution_config)
            
            assert isinstance(execution, TestExecution)
            assert execution.test_suite_name == "User API Tests"
            assert execution.status == ExecutionStatus.COMPLETED
            assert len(execution.test_results) == 1
            assert execution.total_tests == 1
            assert execution.passed_tests == 1
            assert execution.failed_tests == 0
    
    async def test_execute_test_suite_parallel(self, execution_config):
        """测试并行执行测试套件"""
        # 创建多个测试用例
        test_cases = []
        for i in range(5):
            test_case = TestCase(
                name=f"test_case_{i}",
                description=f"Test case {i}",
                test_type=TestType.POSITIVE,
                endpoint=Endpoint(path=f"/test{i}", method="GET"),
                request={},
                expected_response={"status_code": 200},
                assertions=[
                    Assertion(
                        assertion_type=AssertionType.STATUS_CODE,
                        expected_value=200
                    )
                ]
            )
            test_cases.append(test_case)
        
        test_suite = TestSuite(
            name="Parallel Test Suite",
            description="Test parallel execution",
            test_cases=test_cases
        )
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_response.text = AsyncMock(return_value='{}')
        mock_response.json = AsyncMock(return_value={})
        
        with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value.__aenter__.return_value = mock_response
            
            start_time = datetime.utcnow()
            execution = await self.executor.execute_test_suite(test_suite, execution_config)
            end_time = datetime.utcnow()
            
            # 并行执行应该比串行执行快
            execution_time = (end_time - start_time).total_seconds()
            assert execution_time < 5  # 假设串行执行需要更长时间
            
            assert execution.status == ExecutionStatus.COMPLETED
            assert len(execution.test_results) == 5
    
    def test_build_request_url_simple_path(self, execution_config):
        """测试构建简单路径的请求URL"""
        endpoint = Endpoint(path="/users", method="GET")
        request_data = {}
        
        url = self.executor._build_request_url(endpoint, request_data, execution_config)
        
        assert url == "https://api.example.com/users"
    
    def test_build_request_url_with_path_params(self, execution_config):
        """测试构建带路径参数的请求URL"""
        endpoint = Endpoint(path="/users/{id}/posts/{post_id}", method="GET")
        request_data = {
            "path_params": {"id": "123", "post_id": "456"}
        }
        
        url = self.executor._build_request_url(endpoint, request_data, execution_config)
        
        assert url == "https://api.example.com/users/123/posts/456"
    
    def test_build_request_url_with_query_params(self, execution_config):
        """测试构建带查询参数的请求URL"""
        endpoint = Endpoint(path="/users", method="GET")
        request_data = {
            "query_params": {"limit": "10", "offset": "20"}
        }
        
        url = self.executor._build_request_url(endpoint, request_data, execution_config)
        
        # URL应该包含查询参数（顺序可能不同）
        assert "https://api.example.com/users?" in url
        assert "limit=10" in url
        assert "offset=20" in url
    
    def test_prepare_request_headers(self, execution_config):
        """测试准备请求头"""
        request_data = {
            "headers": {"Content-Type": "application/json", "X-Custom": "value"}
        }
        
        headers = self.executor._prepare_request_headers(request_data, execution_config)
        
        # 应该合并配置中的头和请求中的头
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Custom"] == "value"
    
    def test_prepare_request_body_json(self):
        """测试准备JSON请求体"""
        request_data = {
            "body": {"name": "John", "email": "john@example.com"},
            "headers": {"Content-Type": "application/json"}
        }
        
        body = self.executor._prepare_request_body(request_data)
        
        assert isinstance(body, str)
        assert '"name": "John"' in body
        assert '"email": "john@example.com"' in body
    
    def test_prepare_request_body_form_data(self):
        """测试准备表单数据请求体"""
        request_data = {
            "body": {"name": "John", "email": "john@example.com"},
            "headers": {"Content-Type": "application/x-www-form-urlencoded"}
        }
        
        body = self.executor._prepare_request_body(request_data)
        
        # 应该是表单编码格式
        assert "name=John" in body
        assert "email=john%40example.com" in body
    
    def test_prepare_request_body_text(self):
        """测试准备文本请求体"""
        request_data = {
            "body": "plain text content",
            "headers": {"Content-Type": "text/plain"}
        }
        
        body = self.executor._prepare_request_body(request_data)
        
        assert body == "plain text content"
    
    async def test_execute_assertions_status_code(self):
        """测试执行状态码断言"""
        assertion = Assertion(
            assertion_type=AssertionType.STATUS_CODE,
            expected_value=200,
            description="Status should be 200"
        )
        
        actual_response = {
            "status_code": 200,
            "headers": {},
            "body": "{}"
        }
        
        result = await self.executor._execute_assertion(assertion, actual_response)
        
        assert isinstance(result, AssertionResult)
        assert result.assertion_type == AssertionType.STATUS_CODE
        assert result.passed is True
        assert result.expected_value == 200
        assert result.actual_value == 200
    
    async def test_execute_assertions_response_time(self):
        """测试执行响应时间断言"""
        assertion = Assertion(
            assertion_type=AssertionType.RESPONSE_TIME,
            expected_value=1000,  # 1秒
            description="Response time should be less than 1 second"
        )
        
        actual_response = {
            "status_code": 200,
            "headers": {},
            "body": "{}",
            "response_time": 500  # 0.5秒
        }
        
        result = await self.executor._execute_assertion(assertion, actual_response)
        
        assert result.passed is True
        assert result.actual_value == 500
    
    async def test_execute_assertions_response_contains(self):
        """测试执行响应内容包含断言"""
        assertion = Assertion(
            assertion_type=AssertionType.RESPONSE_CONTAINS,
            expected_value="success",
            description="Response should contain 'success'"
        )
        
        actual_response = {
            "status_code": 200,
            "headers": {},
            "body": '{"status": "success", "data": {}}'
        }
        
        result = await self.executor._execute_assertion(assertion, actual_response)
        
        assert result.passed is True
    
    async def test_execute_assertions_header_exists(self):
        """测试执行响应头存在断言"""
        assertion = Assertion(
            assertion_type=AssertionType.HEADER_EXISTS,
            expected_value="Content-Type",
            description="Content-Type header should exist"
        )
        
        actual_response = {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": "{}"
        }
        
        result = await self.executor._execute_assertion(assertion, actual_response)
        
        assert result.passed is True
    
    def test_calculate_execution_summary(self):
        """测试计算执行摘要"""
        test_results = [
            TestResult(
                test_case_name="test1",
                status=ExecutionStatus.PASSED,
                response_time=100,
                actual_response={},
                assertion_results=[]
            ),
            TestResult(
                test_case_name="test2", 
                status=ExecutionStatus.FAILED,
                response_time=200,
                actual_response={},
                assertion_results=[]
            ),
            TestResult(
                test_case_name="test3",
                status=ExecutionStatus.ERROR,
                response_time=0,
                actual_response={},
                assertion_results=[],
                error_message="Connection error"
            )
        ]
        
        summary = self.executor._calculate_execution_summary(test_results)
        
        assert summary["total_tests"] == 3
        assert summary["passed_tests"] == 1
        assert summary["failed_tests"] == 1
        assert summary["error_tests"] == 1
        assert summary["success_rate"] == 33.33
        assert summary["avg_response_time"] == 100.0  # (100 + 200 + 0) / 3
