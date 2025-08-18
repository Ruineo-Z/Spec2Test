"""
文档解析器单元测试
"""

import pytest
import json
import yaml
from pathlib import Path

from app.core.document_analyzer.parser import DocumentParser
from app.core.document_analyzer.models import DocumentType, DocumentFormat, ParsedDocument


class TestDocumentParser:
    """测试文档解析器"""
    
    def setup_method(self):
        """测试前设置"""
        self.parser = DocumentParser()
    
    def test_parse_openapi_json_document(self):
        """测试解析OpenAPI JSON文档"""
        content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        })

        result = self.parser.parse_document(content, "test.json")
        assert result.document_type == DocumentType.OPENAPI_JSON
        assert result.document_format == DocumentFormat.JSON
    
    def test_parse_openapi_yaml_document(self):
        """测试解析OpenAPI YAML文档"""
        content = """
        openapi: 3.0.0
        info:
          title: Test API
          version: 1.0.0
        paths: {}
        """

        result = self.parser.parse_document(content, "test.yaml")
        assert result.document_type == DocumentType.OPENAPI_YAML
        assert result.document_format == DocumentFormat.YAML
    
    def test_parse_swagger_document(self):
        """测试解析Swagger文档"""
        content = json.dumps({
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        })

        result = self.parser.parse_document(content, "test.json")
        assert result.document_type == DocumentType.OPENAPI  # Swagger被识别为OpenAPI
        assert result.document_format == DocumentFormat.JSON

    def test_parse_markdown_document(self):
        """测试解析Markdown文档"""
        content = """
        # API Documentation

        This is a markdown document.

        ## Endpoints

        ### GET /users
        """

        result = self.parser.parse_document(content, "test.md")
        assert result.document_type == DocumentType.MARKDOWN
        assert result.document_format == DocumentFormat.MARKDOWN

    def test_parse_unknown_document(self):
        """测试解析未知文档类型"""
        content = "This is just plain text"

        result = self.parser.parse_document(content, "test.txt")
        assert result.document_type == DocumentType.UNKNOWN
        assert result.document_format == DocumentFormat.TEXT
    
    def test_parse_openapi_json_success(self):
        """测试成功解析OpenAPI JSON文档"""
        content = json.dumps({
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0",
                "description": "A test API"
            },
            "servers": [
                {"url": "https://api.example.com"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
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
                    }
                }
            }
        })
        
        result = self.parser.parse_openapi(content)
        
        assert isinstance(result, ParsedDocument)
        assert result.document_type == DocumentType.OPENAPI
        assert result.title == "Test API"
        assert result.version == "1.0.0"
        assert result.description == "A test API"
        assert len(result.servers) == 1
        assert result.servers[0] == "https://api.example.com"
        assert len(result.endpoints) == 1
        
        endpoint = result.endpoints[0]
        assert endpoint.path == "/users"
        assert endpoint.method == "GET"
        assert endpoint.summary == "Get users"
    
    def test_parse_openapi_yaml_success(self):
        """测试成功解析OpenAPI YAML文档"""
        content = """
        openapi: 3.0.0
        info:
          title: Test API
          version: 1.0.0
          description: A test API
        servers:
          - url: https://api.example.com
        paths:
          /users:
            get:
              summary: Get users
              responses:
                '200':
                  description: Success
                  content:
                    application/json:
                      schema:
                        type: array
                        items:
                          type: object
        """
        
        result = self.parser.parse_openapi(content)
        
        assert isinstance(result, ParsedDocument)
        assert result.document_type == DocumentType.OPENAPI
        assert result.title == "Test API"
        assert result.version == "1.0.0"
        assert len(result.endpoints) == 1
    
    def test_parse_openapi_invalid_json(self):
        """测试解析无效JSON"""
        content = "{ invalid json"
        
        with pytest.raises(Exception):
            self.parser.parse_openapi(content)
    
    def test_parse_openapi_missing_required_fields(self):
        """测试解析缺少必需字段的OpenAPI文档"""
        content = json.dumps({
            "openapi": "3.0.0"
            # 缺少info字段
        })
        
        with pytest.raises(Exception):
            self.parser.parse_openapi(content)
    
    def test_parse_markdown_success(self):
        """测试成功解析Markdown文档"""
        content = """
        # Test API Documentation
        
        This is a test API documentation.
        
        ## Overview
        
        The API provides user management functionality.
        
        ## Endpoints
        
        ### GET /users
        
        Get all users.
        
        **Parameters:**
        - limit: number of users to return
        
        **Response:**
        ```json
        {
          "users": []
        }
        ```
        
        ### POST /users
        
        Create a new user.
        """
        
        result = self.parser.parse_markdown(content)
        
        assert isinstance(result, ParsedDocument)
        assert result.document_type == DocumentType.MARKDOWN
        assert result.title == "Test API Documentation"
        assert "user management functionality" in result.description
        assert len(result.endpoints) >= 2
        
        # 检查解析出的端点
        get_endpoint = next((ep for ep in result.endpoints if ep.method == "GET"), None)
        assert get_endpoint is not None
        assert get_endpoint.path == "/users"
        
        post_endpoint = next((ep for ep in result.endpoints if ep.method == "POST"), None)
        assert post_endpoint is not None
        assert post_endpoint.path == "/users"
    
    def test_parse_markdown_no_endpoints(self):
        """测试解析没有端点的Markdown文档"""
        content = """
        # Documentation
        
        This is just general documentation without API endpoints.
        """
        
        result = self.parser.parse_markdown(content)
        
        assert isinstance(result, ParsedDocument)
        assert result.document_type == DocumentType.MARKDOWN
        assert result.title == "Documentation"
        assert len(result.endpoints) == 0
    
    def test_parse_document_openapi(self):
        """测试解析OpenAPI文档的通用方法"""
        content = json.dumps({
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        })
        
        result = self.parser.parse_document(content, "test.json")
        
        assert isinstance(result, ParsedDocument)
        assert result.document_type == DocumentType.OPENAPI
        assert result.title == "Test API"
    
    def test_parse_document_markdown(self):
        """测试解析Markdown文档的通用方法"""
        content = """
        # Test Documentation
        
        This is a test document.
        """
        
        result = self.parser.parse_document(content, "test.md")
        
        assert isinstance(result, ParsedDocument)
        assert result.document_type == DocumentType.MARKDOWN
        assert result.title == "Test Documentation"
    
    def test_parse_document_unknown_type(self):
        """测试解析未知类型文档"""
        content = "Plain text content"
        
        with pytest.raises(ValueError, match="Unsupported document type"):
            self.parser.parse_document(content, "test.txt")
    
    def test_extract_endpoints_from_openapi_complex(self):
        """测试从复杂OpenAPI文档提取端点"""
        openapi_spec = {
            "paths": {
                "/users": {
                    "get": {
                        "summary": "List users",
                        "parameters": [
                            {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                        ],
                        "responses": {"200": {"description": "Success"}}
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
                        "responses": {"201": {"description": "Created"}}
                    }
                },
                "/users/{id}": {
                    "get": {
                        "summary": "Get user by ID",
                        "parameters": [
                            {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                        ],
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        endpoints = self.parser._extract_endpoints_from_openapi(openapi_spec)
        
        assert len(endpoints) == 3
        
        # 检查GET /users
        get_users = next((ep for ep in endpoints if ep.path == "/users" and ep.method == "GET"), None)
        assert get_users is not None
        assert get_users.summary == "List users"
        assert len(get_users.parameters) == 1
        assert get_users.parameters[0]["name"] == "limit"
        
        # 检查POST /users
        post_users = next((ep for ep in endpoints if ep.path == "/users" and ep.method == "POST"), None)
        assert post_users is not None
        assert post_users.summary == "Create user"
        assert post_users.request_body is not None
        
        # 检查GET /users/{id}
        get_user = next((ep for ep in endpoints if ep.path == "/users/{id}"), None)
        assert get_user is not None
        assert get_user.summary == "Get user by ID"
        assert len(get_user.parameters) == 1
        assert get_user.parameters[0]["name"] == "id"
        assert get_user.parameters[0]["required"] is True
