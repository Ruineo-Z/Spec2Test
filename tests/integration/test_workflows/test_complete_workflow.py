"""
完整工作流程集成测试

测试从文档上传到测试报告生成的完整流程
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock

from app.main import app


class TestCompleteWorkflow:
    """测试完整工作流程"""
    
    def setup_method(self):
        """测试前设置"""
        self.client = TestClient(app)
    
    @pytest.fixture
    def comprehensive_openapi_doc(self):
        """综合的OpenAPI文档"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "User Management API",
                "version": "1.0.0",
                "description": "A comprehensive API for user management"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get all users",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "schema": {"type": "integer", "default": 10}
                            },
                            {
                                "name": "offset", 
                                "in": "query",
                                "schema": {"type": "integer", "default": 0}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "users": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "id": {"type": "string"},
                                                            "name": {"type": "string"},
                                                            "email": {"type": "string"}
                                                        }
                                                    }
                                                },
                                                "total": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            },
                            "400": {"description": "Bad Request"},
                            "500": {"description": "Internal Server Error"}
                        }
                    },
                    "post": {
                        "summary": "Create a new user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "required": ["name", "email"],
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string", "format": "email"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "User created successfully"},
                            "400": {"description": "Invalid input"},
                            "409": {"description": "User already exists"}
                        }
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "User found"},
                            "404": {"description": "User not found"}
                        }
                    },
                    "put": {
                        "summary": "Update user",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path", 
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {"description": "User updated"},
                            "404": {"description": "User not found"}
                        }
                    },
                    "delete": {
                        "summary": "Delete user",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "204": {"description": "User deleted"},
                            "404": {"description": "User not found"}
                        }
                    }
                }
            }
        }
    
    def test_complete_workflow_success(self, comprehensive_openapi_doc):
        """测试完整成功的工作流程"""
        
        # 步骤1: 上传文档
        files = {
            "file": ("user_api.json", json.dumps(comprehensive_openapi_doc), "application/json")
        }
        
        with patch('app.core.document_analyzer.parser.DocumentParser.parse_document') as mock_parse, \
             patch('app.core.document_analyzer.chunker.DocumentChunker.chunk_document') as mock_chunk, \
             patch('app.core.test_generator.generator.TestGenerator.generate_tests_for_chunk', new_callable=AsyncMock) as mock_generate, \
             patch('app.core.test_executor.executor.TestExecutor.execute_test_suite', new_callable=AsyncMock) as mock_execute, \
             patch('app.core.report_analyzer.analyzer.ReportAnalyzer.analyze_test_execution') as mock_analyze:
            
            # 模拟文档解析
            from app.core.document_analyzer.models import ParsedDocument, DocumentType, Endpoint
            mock_parse.return_value = ParsedDocument(
                document_type=DocumentType.OPENAPI,
                title="User Management API",
                version="1.0.0",
                description="A comprehensive API for user management",
                servers=["https://api.example.com"],
                endpoints=[
                    Endpoint(path="/users", method="GET", summary="Get all users"),
                    Endpoint(path="/users", method="POST", summary="Create a new user"),
                    Endpoint(path="/users/{id}", method="GET", summary="Get user by ID"),
                    Endpoint(path="/users/{id}", method="PUT", summary="Update user"),
                    Endpoint(path="/users/{id}", method="DELETE", summary="Delete user")
                ]
            )
            
            # 模拟文档分块
            from app.core.document_analyzer.models import DocumentChunk
            mock_chunk.return_value = [
                DocumentChunk(
                    chunk_id="users_collection",
                    title="Users Collection",
                    content="Users collection endpoints",
                    chunk_type="endpoint_group",
                    endpoints=[
                        Endpoint(path="/users", method="GET", summary="Get all users"),
                        Endpoint(path="/users", method="POST", summary="Create a new user")
                    ],
                    token_count=500
                ),
                DocumentChunk(
                    chunk_id="user_individual",
                    title="Individual User",
                    content="Individual user endpoints",
                    chunk_type="endpoint_group",
                    endpoints=[
                        Endpoint(path="/users/{id}", method="GET", summary="Get user by ID"),
                        Endpoint(path="/users/{id}", method="PUT", summary="Update user"),
                        Endpoint(path="/users/{id}", method="DELETE", summary="Delete user")
                    ],
                    token_count=600
                )
            ]
            
            # 模拟测试生成
            from app.core.test_generator.models import TestSuite, TestCase, TestType, AssertionType, Assertion
            mock_generate.return_value = TestSuite(
                name="User Management API Tests",
                description="Generated tests for User Management API",
                test_cases=[
                    TestCase(
                        name="test_get_users_success",
                        description="Test successful retrieval of users",
                        test_type=TestType.POSITIVE,
                        endpoint=Endpoint(path="/users", method="GET"),
                        request={"query_params": {"limit": 10}},
                        expected_response={"status_code": 200},
                        assertions=[
                            Assertion(
                                assertion_type=AssertionType.STATUS_CODE,
                                expected_value=200
                            )
                        ]
                    ),
                    TestCase(
                        name="test_create_user_success",
                        description="Test successful user creation",
                        test_type=TestType.POSITIVE,
                        endpoint=Endpoint(path="/users", method="POST"),
                        request={
                            "body": {"name": "John Doe", "email": "john@example.com"},
                            "headers": {"Content-Type": "application/json"}
                        },
                        expected_response={"status_code": 201},
                        assertions=[
                            Assertion(
                                assertion_type=AssertionType.STATUS_CODE,
                                expected_value=201
                            )
                        ]
                    )
                ]
            )
            
            # 模拟测试执行
            from app.core.test_executor.models import TestExecution, TestResult, ExecutionStatus, AssertionResult
            mock_execute.return_value = TestExecution(
                execution_id="exec_123",
                test_suite_name="User Management API Tests",
                status=ExecutionStatus.COMPLETED,
                test_results=[
                    TestResult(
                        test_case_name="test_get_users_success",
                        status=ExecutionStatus.PASSED,
                        response_time=150,
                        actual_response={
                            "status_code": 200,
                            "body": '{"users": [], "total": 0}'
                        },
                        assertion_results=[
                            AssertionResult(
                                assertion_type=AssertionType.STATUS_CODE,
                                passed=True,
                                expected_value=200,
                                actual_value=200
                            )
                        ]
                    ),
                    TestResult(
                        test_case_name="test_create_user_success",
                        status=ExecutionStatus.PASSED,
                        response_time=200,
                        actual_response={
                            "status_code": 201,
                            "body": '{"id": "123", "name": "John Doe", "email": "john@example.com"}'
                        },
                        assertion_results=[
                            AssertionResult(
                                assertion_type=AssertionType.STATUS_CODE,
                                passed=True,
                                expected_value=201,
                                actual_value=201
                            )
                        ]
                    )
                ],
                total_tests=2,
                passed_tests=2,
                failed_tests=0,
                error_tests=0
            )
            
            # 模拟报告分析
            from app.core.report_analyzer.models import TestReport, ReportSummary, PerformanceMetrics, IssueAnalysis
            mock_analyze.return_value = TestReport(
                execution_id="exec_123",
                test_suite_name="User Management API Tests",
                summary=ReportSummary(
                    total_tests=2,
                    passed_tests=2,
                    failed_tests=0,
                    error_tests=0,
                    success_rate=100.0
                ),
                performance_metrics=PerformanceMetrics(
                    total_requests=2,
                    avg_response_time=175.0,
                    max_response_time=200,
                    min_response_time=150
                ),
                issue_analysis=IssueAnalysis(
                    failed_tests=[],
                    performance_issues=[],
                    assertion_failures=[]
                ),
                recommendations=["Consider adding more edge case tests"]
            )
            
            # 执行完整流程
            
            # 1. 上传文档
            upload_response = self.client.post("/api/v1/documents/upload", files=files)
            assert upload_response.status_code == 200
            document_id = upload_response.json()["document_id"]
            
            # 2. 分块文档
            chunk_response = self.client.post(
                f"/api/v1/documents/{document_id}/chunk",
                json={"strategy": "by_path", "max_tokens": 1000}
            )
            assert chunk_response.status_code == 200
            chunks = chunk_response.json()["chunks"]
            assert len(chunks) == 2
            
            # 3. 生成测试
            generate_response = self.client.post(
                f"/api/v1/documents/{document_id}/generate-tests",
                json={
                    "test_types": ["positive", "negative"],
                    "include_performance_tests": True,
                    "max_tests_per_endpoint": 5
                }
            )
            assert generate_response.status_code == 200
            test_suite_id = generate_response.json()["test_suite_id"]
            
            # 4. 执行测试
            execute_response = self.client.post(
                f"/api/v1/test-suites/{test_suite_id}/execute",
                json={
                    "base_url": "https://api.example.com",
                    "timeout": 30,
                    "parallel_execution": True
                }
            )
            assert execute_response.status_code == 200
            execution_id = execute_response.json()["execution_id"]
            
            # 5. 获取执行状态
            status_response = self.client.get(f"/api/v1/executions/{execution_id}/status")
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "completed"
            
            # 6. 生成报告
            report_response = self.client.post(
                f"/api/v1/executions/{execution_id}/report",
                json={
                    "format": "json",
                    "include_performance_analysis": True,
                    "include_recommendations": True
                }
            )
            assert report_response.status_code == 200
            report_data = report_response.json()
            
            # 验证报告内容
            assert report_data["summary"]["total_tests"] == 2
            assert report_data["summary"]["success_rate"] == 100.0
            assert "performance_metrics" in report_data
            assert "recommendations" in report_data
    
    def test_workflow_with_test_failures(self, comprehensive_openapi_doc):
        """测试包含测试失败的工作流程"""
        
        files = {
            "file": ("user_api.json", json.dumps(comprehensive_openapi_doc), "application/json")
        }
        
        with patch('app.core.document_analyzer.parser.DocumentParser.parse_document') as mock_parse, \
             patch('app.core.test_executor.executor.TestExecutor.execute_test_suite', new_callable=AsyncMock) as mock_execute:
            
            # 模拟文档解析
            from app.core.document_analyzer.models import ParsedDocument, DocumentType, Endpoint
            mock_parse.return_value = ParsedDocument(
                document_type=DocumentType.OPENAPI,
                title="User Management API",
                version="1.0.0",
                endpoints=[
                    Endpoint(path="/users", method="GET", summary="Get all users")
                ]
            )
            
            # 模拟测试执行（包含失败）
            from app.core.test_executor.models import TestExecution, TestResult, ExecutionStatus, AssertionResult
            mock_execute.return_value = TestExecution(
                execution_id="exec_456",
                test_suite_name="User Management API Tests",
                status=ExecutionStatus.COMPLETED,
                test_results=[
                    TestResult(
                        test_case_name="test_get_users_success",
                        status=ExecutionStatus.FAILED,
                        response_time=150,
                        actual_response={
                            "status_code": 500,  # 期望200但得到500
                            "body": '{"error": "Internal server error"}'
                        },
                        assertion_results=[
                            AssertionResult(
                                assertion_type=AssertionType.STATUS_CODE,
                                passed=False,
                                expected_value=200,
                                actual_value=500,
                                error_message="Expected 200 but got 500"
                            )
                        ]
                    )
                ],
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                error_tests=0
            )
            
            # 执行流程
            upload_response = self.client.post("/api/v1/documents/upload", files=files)
            document_id = upload_response.json()["document_id"]
            
            generate_response = self.client.post(
                f"/api/v1/documents/{document_id}/generate-tests",
                json={"test_types": ["positive"]}
            )
            test_suite_id = generate_response.json()["test_suite_id"]
            
            execute_response = self.client.post(
                f"/api/v1/test-suites/{test_suite_id}/execute",
                json={"base_url": "https://api.example.com"}
            )
            execution_id = execute_response.json()["execution_id"]
            
            # 检查执行结果
            status_response = self.client.get(f"/api/v1/executions/{execution_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "completed"
            assert status_data["passed_tests"] == 0
            assert status_data["failed_tests"] == 1
    
    def test_workflow_error_handling(self):
        """测试工作流程中的错误处理"""
        
        # 测试上传无效文档
        files = {
            "file": ("invalid.txt", "This is not a valid document", "text/plain")
        }
        
        response = self.client.post("/api/v1/documents/upload", files=files)
        assert response.status_code == 400
        
        # 测试访问不存在的文档
        response = self.client.get("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404
        
        # 测试为不存在的文档生成测试
        response = self.client.post(
            "/api/v1/documents/nonexistent-id/generate-tests",
            json={"test_types": ["positive"]}
        )
        assert response.status_code == 404
