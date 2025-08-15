"""
Pydantic Schema单元测试

测试所有Schema的数据验证功能。
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas import (
    DocumentCreate, DocumentResponse,
    TestCaseCreate, TestCaseResponse,
    TestResultCreate, TestResultResponse,
    ReportCreate, ReportResponse
)
from app.models import (
    DocumentType, DocumentStatus,
    TestCaseType, HTTPMethod, TestCasePriority,
    TestStatus, FailureType,
    ReportType, ReportFormat
)


class TestDocumentSchemas:
    """测试文档Schema"""
    
    def test_document_create_valid(self):
        """测试有效的文档创建Schema"""
        data = {
            "name": "测试API文档",
            "description": "这是一个测试文档",
            "document_type": DocumentType.OPENAPI,
            "original_filename": "api.yaml",
            "content": "openapi: 3.0.0\ninfo:\n  title: Test API"
        }
        
        schema = DocumentCreate(**data)
        assert schema.name == "测试API文档"
        assert schema.document_type == DocumentType.OPENAPI
        assert schema.original_filename == "api.yaml"
    
    def test_document_create_invalid(self):
        """测试无效的文档创建Schema"""
        # 缺少必需字段
        with pytest.raises(ValidationError):
            DocumentCreate(description="缺少名称")
        
        # 名称过长
        with pytest.raises(ValidationError):
            DocumentCreate(
                name="x" * 300,  # 超过255字符限制
                document_type=DocumentType.OPENAPI
            )
    
    def test_document_response(self):
        """测试文档响应Schema"""
        data = {
            "id": 1,
            "name": "测试文档",
            "description": "测试描述",
            "document_type": DocumentType.OPENAPI,
            "status": DocumentStatus.PARSED,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        schema = DocumentResponse(**data)
        assert schema.id == 1
        assert schema.status == DocumentStatus.PARSED


class TestTestCaseSchemas:
    """测试测试用例Schema"""
    
    def test_test_case_create_valid(self):
        """测试有效的测试用例创建Schema"""
        data = {
            "document_id": 1,
            "name": "测试用例1",
            "description": "GET用户列表",
            "test_type": TestCaseType.NORMAL,
            "priority": TestCasePriority.HIGH,
            "endpoint_path": "/api/users",
            "http_method": HTTPMethod.GET,
            "expected_status_code": 200,
            "max_response_time": 2.0,
            "retry_count": 3,
            "timeout": 30.0,
            "is_enabled": True
        }
        
        schema = TestCaseCreate(**data)
        assert schema.document_id == 1
        assert schema.name == "测试用例1"
        assert schema.http_method == HTTPMethod.GET
        assert schema.expected_status_code == 200
        assert schema.max_response_time == 2.0
    
    def test_test_case_create_invalid(self):
        """测试无效的测试用例创建Schema"""
        # 缺少必需字段
        with pytest.raises(ValidationError):
            TestCaseCreate(name="测试用例")
        
        # 无效的重试次数
        with pytest.raises(ValidationError):
            TestCaseCreate(
                document_id=1,
                name="测试用例",
                endpoint_path="/api/test",
                http_method=HTTPMethod.GET,
                retry_count=15  # 超过最大值10
            )
        
        # 无效的超时时间
        with pytest.raises(ValidationError):
            TestCaseCreate(
                document_id=1,
                name="测试用例",
                endpoint_path="/api/test",
                http_method=HTTPMethod.GET,
                timeout=500  # 超过最大值300
            )
    
    def test_test_case_response(self):
        """测试测试用例响应Schema"""
        data = {
            "id": 1,
            "document_id": 1,
            "name": "测试用例1",
            "description": "测试描述",
            "test_type": TestCaseType.NORMAL,
            "priority": TestCasePriority.MEDIUM,
            "endpoint_path": "/api/users",
            "http_method": HTTPMethod.GET,
            "retry_count": 0,
            "is_enabled": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        schema = TestCaseResponse(**data)
        assert schema.id == 1
        assert schema.http_method == HTTPMethod.GET


class TestTestResultSchemas:
    """测试测试结果Schema"""
    
    def test_test_result_create_valid(self):
        """测试有效的测试结果创建Schema"""
        data = {
            "test_case_id": 1,
            "status": TestStatus.PASSED,
            "execution_id": "exec_123",
            "actual_request_url": "https://api.example.com/users",
            "response_status_code": 200,
            "response_time": 0.5,
            "dns_lookup_time": 0.1,
            "tcp_connect_time": 0.2,
            "assertions_passed": 5,
            "assertions_failed": 0,
            "retry_count": 0,
            "is_retry": False,
            "environment": "test"
        }
        
        schema = TestResultCreate(**data)
        assert schema.test_case_id == 1
        assert schema.status == TestStatus.PASSED
        assert schema.response_time == 0.5
        assert schema.assertions_passed == 5
    
    def test_test_result_create_invalid(self):
        """测试无效的测试结果创建Schema"""
        # 负数的响应时间
        with pytest.raises(ValidationError):
            TestResultCreate(
                test_case_id=1,
                status=TestStatus.PASSED,
                response_time=-1.0  # 不能为负数
            )
        
        # 负数的断言数量
        with pytest.raises(ValidationError):
            TestResultCreate(
                test_case_id=1,
                status=TestStatus.PASSED,
                assertions_passed=-1  # 不能为负数
            )
    
    def test_test_result_response(self):
        """测试测试结果响应Schema"""
        data = {
            "id": 1,
            "test_case_id": 1,
            "status": TestStatus.PASSED,
            "execution_id": "exec_123",
            "retry_count": 0,
            "is_retry": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        schema = TestResultResponse(**data)
        assert schema.id == 1
        assert schema.status == TestStatus.PASSED


class TestReportSchemas:
    """测试报告Schema"""
    
    def test_report_create_valid(self):
        """测试有效的报告创建Schema"""
        data = {
            "document_id": 1,
            "name": "执行摘要报告",
            "description": "测试执行的摘要报告",
            "report_type": ReportType.EXECUTION_SUMMARY,
            "format": ReportFormat.HTML,
            "execution_id": "exec_123"
        }
        
        schema = ReportCreate(**data)
        assert schema.document_id == 1
        assert schema.name == "执行摘要报告"
        assert schema.report_type == ReportType.EXECUTION_SUMMARY
        assert schema.format == ReportFormat.HTML
    
    def test_report_create_invalid(self):
        """测试无效的报告创建Schema"""
        # 缺少必需字段
        with pytest.raises(ValidationError):
            ReportCreate(name="报告名称")
        
        # 名称过长
        with pytest.raises(ValidationError):
            ReportCreate(
                document_id=1,
                name="x" * 300,  # 超过255字符限制
                report_type=ReportType.EXECUTION_SUMMARY
            )
    
    def test_report_response(self):
        """测试报告响应Schema"""
        data = {
            "id": 1,
            "document_id": 1,
            "name": "测试报告",
            "description": "测试描述",
            "report_type": ReportType.EXECUTION_SUMMARY,
            "format": ReportFormat.HTML,
            "status": "completed",
            "total_test_cases": 10,
            "passed_count": 8,
            "failed_count": 2,
            "error_count": 0,
            "skipped_count": 0,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        schema = ReportResponse(**data)
        assert schema.id == 1
        assert schema.total_test_cases == 10
        assert schema.passed_count == 8


class TestSchemaValidation:
    """测试Schema验证功能"""
    
    def test_nested_validation(self):
        """测试嵌套验证"""
        # 测试包含复杂数据的Schema
        data = {
            "document_id": 1,
            "name": "复杂测试用例",
            "endpoint_path": "/api/users",
            "http_method": HTTPMethod.POST,
            "request_headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer token123"
            },
            "request_body": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30
            },
            "expected_response_body": {
                "id": 1,
                "name": "John Doe",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
        
        schema = TestCaseCreate(**data)
        assert schema.request_headers["Content-Type"] == "application/json"
        assert schema.request_body["name"] == "John Doe"
        assert schema.expected_response_body["id"] == 1
    
    def test_optional_fields(self):
        """测试可选字段"""
        # 最小化数据
        minimal_data = {
            "document_id": 1,
            "name": "最小测试用例",
            "endpoint_path": "/api/test",
            "http_method": HTTPMethod.GET
        }
        
        schema = TestCaseCreate(**minimal_data)
        assert schema.description is None
        assert schema.request_headers is None
        assert schema.expected_status_code is None
    
    def test_enum_validation(self):
        """测试枚举验证"""
        # 有效枚举值
        data = {
            "document_id": 1,
            "name": "枚举测试",
            "endpoint_path": "/api/test",
            "http_method": HTTPMethod.POST,
            "test_type": TestCaseType.BOUNDARY,
            "priority": TestCasePriority.CRITICAL
        }
        
        schema = TestCaseCreate(**data)
        assert schema.http_method == HTTPMethod.POST
        assert schema.test_type == TestCaseType.BOUNDARY
        assert schema.priority == TestCasePriority.CRITICAL
