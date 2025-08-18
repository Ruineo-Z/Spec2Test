"""
文档相关API端点集成测试
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app
from app.core.document_analyzer.models import DocumentType, ParsedDocument, Endpoint


class TestDocumentEndpoints:
    """测试文档相关API端点"""
    
    def setup_method(self):
        """测试前设置"""
        self.client = TestClient(app)
    
    @pytest.fixture
    def sample_openapi_document(self):
        """示例OpenAPI文档"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "A test API for integration testing"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get all users",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "summary": "Create user",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Created"}
                        }
                    }
                }
            }
        }
    
    def test_upload_document_success(self, sample_openapi_document):
        """测试成功上传文档"""
        # 准备文件数据
        file_content = json.dumps(sample_openapi_document)
        files = {
            "file": ("test_api.json", file_content, "application/json")
        }
        
        with patch('app.core.document_analyzer.parser.DocumentParser.parse_document') as mock_parse:
            # 模拟解析结果
            mock_parse.return_value = ParsedDocument(
                document_type=DocumentType.OPENAPI,
                title="Test API",
                version="1.0.0",
                description="A test API for integration testing",
                servers=["https://api.example.com"],
                endpoints=[
                    Endpoint(
                        path="/users",
                        method="GET",
                        summary="Get all users"
                    ),
                    Endpoint(
                        path="/users",
                        method="POST",
                        summary="Create user"
                    )
                ]
            )
            
            response = self.client.post("/api/v1/documents/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            
            assert "document_id" in data
            assert data["document_type"] == "openapi"
            assert data["title"] == "Test API"
            assert data["version"] == "1.0.0"
            assert len(data["endpoints"]) == 2
    
    def test_upload_document_invalid_file(self):
        """测试上传无效文件"""
        files = {
            "file": ("invalid.txt", "This is not a valid API document", "text/plain")
        }
        
        response = self.client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_upload_document_missing_file(self):
        """测试缺少文件的上传请求"""
        response = self.client.post("/api/v1/documents/upload")
        
        assert response.status_code == 422  # Validation error
    
    def test_get_document_success(self):
        """测试成功获取文档"""
        # 首先上传一个文档
        sample_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        
        files = {
            "file": ("test.json", json.dumps(sample_doc), "application/json")
        }
        
        with patch('app.core.document_analyzer.parser.DocumentParser.parse_document') as mock_parse:
            mock_parse.return_value = ParsedDocument(
                document_type=DocumentType.OPENAPI,
                title="Test API",
                version="1.0.0",
                endpoints=[]
            )
            
            # 上传文档
            upload_response = self.client.post("/api/v1/documents/upload", files=files)
            document_id = upload_response.json()["document_id"]
            
            # 获取文档
            get_response = self.client.get(f"/api/v1/documents/{document_id}")
            
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["document_id"] == document_id
            assert data["title"] == "Test API"
    
    def test_get_document_not_found(self):
        """测试获取不存在的文档"""
        response = self.client.get("/api/v1/documents/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_list_documents(self):
        """测试列出文档"""
        response = self.client.get("/api/v1/documents/")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)
    
    def test_list_documents_with_pagination(self):
        """测试带分页的文档列表"""
        response = self.client.get("/api/v1/documents/?limit=5&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 5
        assert data["offset"] == 0
    
    def test_delete_document_success(self):
        """测试成功删除文档"""
        # 首先上传一个文档
        sample_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        
        files = {
            "file": ("test.json", json.dumps(sample_doc), "application/json")
        }
        
        with patch('app.core.document_analyzer.parser.DocumentParser.parse_document') as mock_parse:
            mock_parse.return_value = ParsedDocument(
                document_type=DocumentType.OPENAPI,
                title="Test API",
                version="1.0.0",
                endpoints=[]
            )
            
            # 上传文档
            upload_response = self.client.post("/api/v1/documents/upload", files=files)
            document_id = upload_response.json()["document_id"]
            
            # 删除文档
            delete_response = self.client.delete(f"/api/v1/documents/{document_id}")
            
            assert delete_response.status_code == 200
            data = delete_response.json()
            assert data["message"] == "Document deleted successfully"
            
            # 验证文档已被删除
            get_response = self.client.get(f"/api/v1/documents/{document_id}")
            assert get_response.status_code == 404
    
    def test_delete_document_not_found(self):
        """测试删除不存在的文档"""
        response = self.client.delete("/api/v1/documents/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_validate_document_success(self, sample_openapi_document):
        """测试成功验证文档"""
        with patch('app.core.document_analyzer.validator.DocumentValidator.validate_document') as mock_validate:
            # 模拟验证结果
            from app.core.document_analyzer.models import ValidationResult
            mock_validate.return_value = ValidationResult(
                is_valid=True,
                score=0.95,
                issues=[],
                suggestions=["Add more examples"]
            )
            
            response = self.client.post(
                "/api/v1/documents/validate",
                json=sample_openapi_document
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["score"] == 0.95
            assert isinstance(data["issues"], list)
            assert isinstance(data["suggestions"], list)
    
    def test_validate_document_invalid(self):
        """测试验证无效文档"""
        invalid_doc = {
            "openapi": "3.0.0"
            # 缺少必需的info字段
        }
        
        with patch('app.core.document_analyzer.validator.DocumentValidator.validate_document') as mock_validate:
            from app.core.document_analyzer.models import ValidationResult, ValidationIssue, IssueSeverity, IssueType
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                score=0.3,
                issues=[
                    ValidationIssue(
                        issue_type=IssueType.MISSING_DESCRIPTION,
                        severity=IssueSeverity.HIGH,
                        message="Missing info section",
                        location="root"
                    )
                ],
                suggestions=["Add info section with title and version"]
            )
            
            response = self.client.post(
                "/api/v1/documents/validate",
                json=invalid_doc
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert data["score"] == 0.3
            assert len(data["issues"]) == 1
    
    def test_chunk_document_success(self):
        """测试成功分块文档"""
        # 首先上传一个文档
        sample_doc = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {"summary": "Get users"}},
                "/posts": {"get": {"summary": "Get posts"}}
            }
        }
        
        files = {
            "file": ("test.json", json.dumps(sample_doc), "application/json")
        }
        
        with patch('app.core.document_analyzer.parser.DocumentParser.parse_document') as mock_parse, \
             patch('app.core.document_analyzer.chunker.DocumentChunker.chunk_document') as mock_chunk:
            
            # 模拟解析结果
            mock_parse.return_value = ParsedDocument(
                document_type=DocumentType.OPENAPI,
                title="Test API",
                version="1.0.0",
                endpoints=[
                    Endpoint(path="/users", method="GET", summary="Get users"),
                    Endpoint(path="/posts", method="GET", summary="Get posts")
                ]
            )
            
            # 模拟分块结果
            from app.core.document_analyzer.models import DocumentChunk
            mock_chunk.return_value = [
                DocumentChunk(
                    chunk_id="users_chunk",
                    title="Users Endpoints",
                    content="Users related endpoints",
                    chunk_type="endpoint",
                    endpoints=[Endpoint(path="/users", method="GET", summary="Get users")],
                    token_count=100
                ),
                DocumentChunk(
                    chunk_id="posts_chunk",
                    title="Posts Endpoints", 
                    content="Posts related endpoints",
                    chunk_type="endpoint",
                    endpoints=[Endpoint(path="/posts", method="GET", summary="Get posts")],
                    token_count=100
                )
            ]
            
            # 上传文档
            upload_response = self.client.post("/api/v1/documents/upload", files=files)
            document_id = upload_response.json()["document_id"]
            
            # 分块文档
            chunk_response = self.client.post(
                f"/api/v1/documents/{document_id}/chunk",
                json={"strategy": "by_endpoint", "max_tokens": 1000}
            )
            
            assert chunk_response.status_code == 200
            data = chunk_response.json()
            assert "chunks" in data
            assert len(data["chunks"]) == 2
            assert data["chunks"][0]["title"] == "Users Endpoints"
            assert data["chunks"][1]["title"] == "Posts Endpoints"
