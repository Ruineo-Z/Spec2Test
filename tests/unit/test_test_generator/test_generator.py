"""
测试生成器单元测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.core.test_generator.generator import TestGenerator
from app.core.test_generator.models import (
    TestCase, TestSuite, TestType, AssertionType,
    GenerationConfig, TestGenerationRequest
)
from app.core.document_analyzer.models import (
    ParsedDocument, DocumentType, Endpoint, DocumentChunk
)


class TestTestGenerator:
    """测试测试生成器"""
    
    def setup_method(self):
        """测试前设置"""
        self.generator = TestGenerator()
    
    @pytest.fixture
    def sample_endpoint(self):
        """示例端点"""
        return Endpoint(
            path="/users/{id}",
            method="GET",
            summary="Get user by ID",
            description="Retrieve a specific user by their unique identifier",
            parameters=[
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "User ID"
                }
            ],
            responses={
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "404": {"description": "User not found"},
                "500": {"description": "Internal server error"}
            }
        )
    
    @pytest.fixture
    def sample_document_chunk(self, sample_endpoint):
        """示例文档分块"""
        return DocumentChunk(
            chunk_id="users_endpoint",
            title="User Operations",
            content="API endpoints for user management",
            chunk_type="endpoint",
            endpoints=[sample_endpoint],
            token_count=500
        )
    
    @pytest.fixture
    def generation_config(self):
        """生成配置"""
        return GenerationConfig(
            test_types=[TestType.POSITIVE, TestType.NEGATIVE, TestType.EDGE_CASE],
            include_performance_tests=True,
            include_security_tests=True,
            max_tests_per_endpoint=10,
            assertion_types=[AssertionType.STATUS_CODE, AssertionType.RESPONSE_SCHEMA, AssertionType.RESPONSE_TIME]
        )
    
    async def test_generate_tests_for_chunk_success(self, sample_document_chunk, generation_config):
        """测试成功为文档分块生成测试"""
        with patch.object(self.generator.llm_client, 'generate_completion', new_callable=AsyncMock) as mock_llm:
            # 模拟LLM返回
            mock_llm.return_value = {
                "test_cases": [
                    {
                        "name": "test_get_user_success",
                        "description": "Test successful user retrieval",
                        "test_type": "positive",
                        "endpoint": {
                            "path": "/users/{id}",
                            "method": "GET"
                        },
                        "request": {
                            "path_params": {"id": "123"},
                            "headers": {"Accept": "application/json"}
                        },
                        "expected_response": {
                            "status_code": 200,
                            "schema_validation": True
                        },
                        "assertions": [
                            {"type": "status_code", "expected": 200},
                            {"type": "response_schema", "schema": "user_schema"}
                        ]
                    },
                    {
                        "name": "test_get_user_not_found",
                        "description": "Test user not found scenario",
                        "test_type": "negative",
                        "endpoint": {
                            "path": "/users/{id}",
                            "method": "GET"
                        },
                        "request": {
                            "path_params": {"id": "nonexistent"},
                            "headers": {"Accept": "application/json"}
                        },
                        "expected_response": {
                            "status_code": 404
                        },
                        "assertions": [
                            {"type": "status_code", "expected": 404}
                        ]
                    }
                ]
            }
            
            test_suite = await self.generator.generate_tests_for_chunk(
                sample_document_chunk, generation_config
            )
            
            assert isinstance(test_suite, TestSuite)
            assert test_suite.name == "User Operations Tests"
            assert len(test_suite.test_cases) == 2
            
            # 检查第一个测试用例
            positive_test = test_suite.test_cases[0]
            assert positive_test.name == "test_get_user_success"
            assert positive_test.test_type == TestType.POSITIVE
            assert positive_test.endpoint.path == "/users/{id}"
            assert positive_test.endpoint.method == "GET"
            assert len(positive_test.assertions) == 2
            
            # 检查第二个测试用例
            negative_test = test_suite.test_cases[1]
            assert negative_test.name == "test_get_user_not_found"
            assert negative_test.test_type == TestType.NEGATIVE
            assert negative_test.expected_response.status_code == 404
    
    async def test_generate_tests_for_chunk_llm_error(self, sample_document_chunk, generation_config):
        """测试LLM调用失败的情况"""
        with patch.object(self.generator.llm_client, 'generate_completion', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("LLM service unavailable")
            
            with pytest.raises(Exception, match="LLM service unavailable"):
                await self.generator.generate_tests_for_chunk(
                    sample_document_chunk, generation_config
                )
    
    def test_create_prompt_for_chunk(self, sample_document_chunk, generation_config):
        """测试为文档分块创建提示"""
        prompt = self.generator._create_prompt_for_chunk(sample_document_chunk, generation_config)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        
        # 检查提示包含必要信息
        assert "User Operations" in prompt
        assert "/users/{id}" in prompt
        assert "GET" in prompt
        assert "positive" in prompt.lower()
        assert "negative" in prompt.lower()
        assert "edge_case" in prompt.lower()
    
    def test_parse_llm_response_valid(self):
        """测试解析有效的LLM响应"""
        llm_response = {
            "test_cases": [
                {
                    "name": "test_example",
                    "description": "Example test",
                    "test_type": "positive",
                    "endpoint": {
                        "path": "/test",
                        "method": "GET"
                    },
                    "request": {
                        "headers": {"Accept": "application/json"}
                    },
                    "expected_response": {
                        "status_code": 200
                    },
                    "assertions": [
                        {"type": "status_code", "expected": 200}
                    ]
                }
            ]
        }
        
        test_cases = self.generator._parse_llm_response(llm_response)
        
        assert len(test_cases) == 1
        test_case = test_cases[0]
        assert isinstance(test_case, TestCase)
        assert test_case.name == "test_example"
        assert test_case.test_type == TestType.POSITIVE
    
    def test_parse_llm_response_invalid_format(self):
        """测试解析无效格式的LLM响应"""
        invalid_response = {
            "invalid_key": "invalid_value"
        }
        
        with pytest.raises(ValueError, match="Invalid LLM response format"):
            self.generator._parse_llm_response(invalid_response)
    
    def test_parse_llm_response_missing_required_fields(self):
        """测试解析缺少必需字段的LLM响应"""
        invalid_response = {
            "test_cases": [
                {
                    "name": "test_example",
                    # 缺少description, test_type等必需字段
                }
            ]
        }
        
        with pytest.raises(ValueError):
            self.generator._parse_llm_response(invalid_response)
    
    def test_validate_test_case_valid(self):
        """测试验证有效的测试用例"""
        valid_test_case = {
            "name": "test_valid_case",
            "description": "A valid test case",
            "test_type": "positive",
            "endpoint": {
                "path": "/test",
                "method": "GET"
            },
            "request": {},
            "expected_response": {
                "status_code": 200
            },
            "assertions": [
                {"type": "status_code", "expected": 200}
            ]
        }
        
        # 应该不抛出异常
        self.generator._validate_test_case(valid_test_case)
    
    def test_validate_test_case_missing_name(self):
        """测试验证缺少名称的测试用例"""
        invalid_test_case = {
            # 缺少name
            "description": "A test case",
            "test_type": "positive",
            "endpoint": {"path": "/test", "method": "GET"},
            "request": {},
            "expected_response": {"status_code": 200},
            "assertions": []
        }
        
        with pytest.raises(ValueError, match="Missing required field: name"):
            self.generator._validate_test_case(invalid_test_case)
    
    def test_validate_test_case_invalid_test_type(self):
        """测试验证无效测试类型的测试用例"""
        invalid_test_case = {
            "name": "test_case",
            "description": "A test case",
            "test_type": "invalid_type",  # 无效类型
            "endpoint": {"path": "/test", "method": "GET"},
            "request": {},
            "expected_response": {"status_code": 200},
            "assertions": []
        }
        
        with pytest.raises(ValueError, match="Invalid test_type"):
            self.generator._validate_test_case(invalid_test_case)
    
    def test_validate_test_case_invalid_method(self):
        """测试验证无效HTTP方法的测试用例"""
        invalid_test_case = {
            "name": "test_case",
            "description": "A test case",
            "test_type": "positive",
            "endpoint": {
                "path": "/test",
                "method": "INVALID_METHOD"  # 无效方法
            },
            "request": {},
            "expected_response": {"status_code": 200},
            "assertions": []
        }
        
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            self.generator._validate_test_case(invalid_test_case)
    
    def test_create_test_case_from_dict(self):
        """测试从字典创建测试用例对象"""
        test_case_dict = {
            "name": "test_create_user",
            "description": "Test user creation",
            "test_type": "positive",
            "endpoint": {
                "path": "/users",
                "method": "POST"
            },
            "request": {
                "headers": {"Content-Type": "application/json"},
                "body": {"name": "John", "email": "john@example.com"}
            },
            "expected_response": {
                "status_code": 201,
                "schema_validation": True
            },
            "assertions": [
                {"type": "status_code", "expected": 201},
                {"type": "response_schema", "schema": "user_schema"}
            ]
        }
        
        test_case = self.generator._create_test_case_from_dict(test_case_dict)
        
        assert isinstance(test_case, TestCase)
        assert test_case.name == "test_create_user"
        assert test_case.description == "Test user creation"
        assert test_case.test_type == TestType.POSITIVE
        assert test_case.endpoint.path == "/users"
        assert test_case.endpoint.method == "POST"
        assert test_case.request.headers["Content-Type"] == "application/json"
        assert test_case.expected_response.status_code == 201
        assert len(test_case.assertions) == 2
    
    def test_enhance_test_cases_with_context(self, sample_endpoint):
        """测试使用上下文增强测试用例"""
        basic_test_cases = [
            TestCase(
                name="test_basic",
                description="Basic test",
                test_type=TestType.POSITIVE,
                endpoint=sample_endpoint,
                request={},
                expected_response={"status_code": 200},
                assertions=[]
            )
        ]
        
        enhanced_test_cases = self.generator._enhance_test_cases_with_context(
            basic_test_cases, sample_endpoint
        )
        
        assert len(enhanced_test_cases) == len(basic_test_cases)
        enhanced_test = enhanced_test_cases[0]
        
        # 检查是否添加了上下文信息
        assert enhanced_test.endpoint == sample_endpoint
        # 可能添加了更多断言或请求参数
    
    async def test_generate_performance_tests(self, sample_endpoint):
        """测试生成性能测试"""
        performance_tests = await self.generator._generate_performance_tests(sample_endpoint)
        
        assert isinstance(performance_tests, list)
        assert len(performance_tests) > 0
        
        # 检查性能测试特征
        perf_test = performance_tests[0]
        assert perf_test.test_type == TestType.PERFORMANCE
        assert any(assertion.assertion_type == AssertionType.RESPONSE_TIME for assertion in perf_test.assertions)
    
    async def test_generate_security_tests(self, sample_endpoint):
        """测试生成安全测试"""
        security_tests = await self.generator._generate_security_tests(sample_endpoint)
        
        assert isinstance(security_tests, list)
        assert len(security_tests) > 0
        
        # 检查安全测试特征
        sec_test = security_tests[0]
        assert sec_test.test_type == TestType.SECURITY
        # 可能包含SQL注入、XSS等安全测试场景
