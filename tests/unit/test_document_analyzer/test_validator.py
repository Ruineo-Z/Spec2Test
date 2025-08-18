"""
文档质量检查器单元测试
"""

import pytest
from app.core.document_analyzer.validator import DocumentValidator
from app.core.document_analyzer.models import (
    ParsedDocument, DocumentType, Endpoint, ValidationResult, 
    ValidationIssue, IssueSeverity, IssueType
)


class TestDocumentValidator:
    """测试文档质量检查器"""
    
    def setup_method(self):
        """测试前设置"""
        self.validator = DocumentValidator()
    
    def test_validate_document_complete(self):
        """测试验证完整文档"""
        # 创建完整的文档
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                summary="Get all users",
                description="Retrieve a list of all users",
                parameters=[
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                ],
                responses={
                    "200": {"description": "Success", "content": {"application/json": {}}}
                }
            ),
            Endpoint(
                path="/users",
                method="POST",
                summary="Create user",
                description="Create a new user",
                request_body={"content": {"application/json": {}}},
                responses={
                    "201": {"description": "Created"},
                    "400": {"description": "Bad Request"}
                }
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="User API",
            version="1.0.0",
            description="API for user management",
            servers=["https://api.example.com"],
            endpoints=endpoints
        )
        
        result = self.validator.validate_document(document)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.score >= 0.8  # 高质量文档
        assert len(result.issues) == 0  # 没有严重问题
    
    def test_validate_document_missing_info(self):
        """测试验证缺少信息的文档"""
        # 创建缺少信息的文档
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                # 缺少summary和description
                responses={"200": {"description": "Success"}}
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="API",  # 标题太短
            # 缺少version和description
            endpoints=endpoints
        )
        
        result = self.validator.validate_document(document)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert result.score < 0.6  # 低质量文档
        assert len(result.issues) > 0
        
        # 检查具体问题
        issue_types = [issue.issue_type for issue in result.issues]
        assert IssueType.MISSING_DESCRIPTION in issue_types
        assert IssueType.MISSING_VERSION in issue_types
    
    def test_validate_document_inconsistent_responses(self):
        """测试验证响应不一致的文档"""
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                summary="Get users",
                responses={"200": {"description": "Success"}}
            ),
            Endpoint(
                path="/posts",
                method="GET", 
                summary="Get posts",
                responses={"200": {"description": "OK"}}  # 不同的描述
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Test API",
            version="1.0.0",
            endpoints=endpoints
        )
        
        result = self.validator.validate_document(document)
        
        # 检查是否发现不一致问题
        inconsistency_issues = [
            issue for issue in result.issues 
            if issue.issue_type == IssueType.INCONSISTENT_RESPONSES
        ]
        assert len(inconsistency_issues) > 0
    
    def test_check_completeness_missing_fields(self):
        """测试检查完整性 - 缺少字段"""
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="API",
            # 缺少version, description等
            endpoints=[]
        )
        
        issues = self.validator._check_completeness(document)
        
        issue_types = [issue.issue_type for issue in issues]
        assert IssueType.MISSING_VERSION in issue_types
        assert IssueType.MISSING_DESCRIPTION in issue_types
        assert IssueType.MISSING_ENDPOINTS in issue_types
    
    def test_check_completeness_endpoint_missing_info(self):
        """测试检查端点完整性"""
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                # 缺少summary, description, responses
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Test API",
            version="1.0.0",
            endpoints=endpoints
        )
        
        issues = self.validator._check_completeness(document)
        
        # 应该发现端点缺少信息的问题
        endpoint_issues = [
            issue for issue in issues 
            if "endpoint" in issue.message.lower()
        ]
        assert len(endpoint_issues) > 0
    
    def test_check_consistency_response_descriptions(self):
        """测试检查响应描述一致性"""
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                summary="Get users",
                responses={
                    "200": {"description": "Success"},
                    "404": {"description": "Not Found"}
                }
            ),
            Endpoint(
                path="/posts", 
                method="GET",
                summary="Get posts",
                responses={
                    "200": {"description": "OK"},  # 不一致
                    "404": {"description": "Not found"}  # 不一致
                }
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Test API",
            version="1.0.0",
            endpoints=endpoints
        )
        
        issues = self.validator._check_consistency(document)
        
        # 应该发现响应描述不一致的问题
        response_issues = [
            issue for issue in issues
            if issue.issue_type == IssueType.INCONSISTENT_RESPONSES
        ]
        assert len(response_issues) > 0
    
    def test_check_consistency_parameter_naming(self):
        """测试检查参数命名一致性"""
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                summary="Get users",
                parameters=[
                    {"name": "page_size", "in": "query"},  # snake_case
                    {"name": "pageNumber", "in": "query"}  # camelCase - 不一致
                ]
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Test API", 
            version="1.0.0",
            endpoints=endpoints
        )
        
        issues = self.validator._check_consistency(document)
        
        # 应该发现参数命名不一致的问题
        naming_issues = [
            issue for issue in issues
            if "naming" in issue.message.lower()
        ]
        assert len(naming_issues) > 0
    
    def test_generate_suggestions_missing_examples(self):
        """测试生成改进建议 - 缺少示例"""
        endpoints = [
            Endpoint(
                path="/users",
                method="POST",
                summary="Create user",
                request_body={"content": {"application/json": {}}},
                responses={"201": {"description": "Created"}}
                # 缺少请求和响应示例
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Test API",
            version="1.0.0", 
            endpoints=endpoints
        )
        
        suggestions = self.validator._generate_suggestions(document)
        
        # 应该建议添加示例
        example_suggestions = [
            suggestion for suggestion in suggestions
            if "example" in suggestion.lower()
        ]
        assert len(example_suggestions) > 0
    
    def test_generate_suggestions_missing_error_responses(self):
        """测试生成改进建议 - 缺少错误响应"""
        endpoints = [
            Endpoint(
                path="/users/{id}",
                method="GET",
                summary="Get user by ID",
                parameters=[{"name": "id", "in": "path"}],
                responses={"200": {"description": "Success"}}
                # 缺少404等错误响应
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Test API",
            version="1.0.0",
            endpoints=endpoints
        )
        
        suggestions = self.validator._generate_suggestions(document)
        
        # 应该建议添加错误响应
        error_suggestions = [
            suggestion for suggestion in suggestions
            if "error" in suggestion.lower() or "404" in suggestion
        ]
        assert len(error_suggestions) > 0
    
    def test_calculate_quality_score_high_quality(self):
        """测试计算高质量文档的分数"""
        # 创建高质量文档（完整信息，无问题）
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Comprehensive User API",
            version="1.0.0",
            description="A comprehensive API for user management with detailed documentation",
            servers=["https://api.example.com"],
            endpoints=[
                Endpoint(
                    path="/users",
                    method="GET",
                    summary="Get all users",
                    description="Retrieve a paginated list of all users",
                    parameters=[
                        {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer"}}
                    ],
                    responses={
                        "200": {"description": "Success"},
                        "400": {"description": "Bad Request"},
                        "500": {"description": "Internal Server Error"}
                    }
                )
            ]
        )
        
        issues = []  # 无问题
        score = self.validator._calculate_quality_score(document, issues)
        
        assert score >= 0.8  # 高质量分数
    
    def test_calculate_quality_score_low_quality(self):
        """测试计算低质量文档的分数"""
        # 创建低质量文档（信息不完整，有问题）
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="API",  # 标题太短
            endpoints=[
                Endpoint(
                    path="/users",
                    method="GET"
                    # 缺少大部分信息
                )
            ]
        )
        
        issues = [
            ValidationIssue(
                issue_type=IssueType.MISSING_DESCRIPTION,
                severity=IssueSeverity.HIGH,
                message="Missing description",
                location="document"
            ),
            ValidationIssue(
                issue_type=IssueType.MISSING_VERSION,
                severity=IssueSeverity.HIGH,
                message="Missing version",
                location="document"
            )
        ]
        
        score = self.validator._calculate_quality_score(document, issues)
        
        assert score < 0.5  # 低质量分数
