"""
文档分块器单元测试
"""

import pytest
from app.core.document_analyzer.chunker import DocumentChunker
from app.core.document_analyzer.models import (
    ParsedDocument, DocumentType, Endpoint, DocumentChunk
)


class TestDocumentChunker:
    """测试文档分块器"""
    
    def setup_method(self):
        """测试前设置"""
        self.chunker = DocumentChunker()
    
    def test_chunk_document_by_endpoint(self):
        """测试按端点分块文档"""
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                summary="Get all users",
                description="Retrieve a list of all users with pagination support",
                parameters=[
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}},
                    {"name": "offset", "in": "query", "schema": {"type": "integer"}}
                ],
                responses={
                    "200": {"description": "Success", "content": {"application/json": {}}},
                    "400": {"description": "Bad Request"}
                }
            ),
            Endpoint(
                path="/users",
                method="POST", 
                summary="Create user",
                description="Create a new user account",
                request_body={"content": {"application/json": {}}},
                responses={
                    "201": {"description": "Created"},
                    "400": {"description": "Bad Request"}
                }
            ),
            Endpoint(
                path="/users/{id}",
                method="GET",
                summary="Get user by ID",
                description="Retrieve a specific user by their ID",
                parameters=[
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                responses={
                    "200": {"description": "Success"},
                    "404": {"description": "Not Found"}
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
        
        chunks = self.chunker.chunk_document(document, strategy="by_endpoint")
        
        assert len(chunks) == 3  # 每个端点一个分块
        
        # 检查第一个分块
        chunk1 = chunks[0]
        assert isinstance(chunk1, DocumentChunk)
        assert chunk1.chunk_type == "endpoint"
        assert chunk1.title == "GET /users"
        assert "Get all users" in chunk1.content
        assert len(chunk1.endpoints) == 1
        assert chunk1.endpoints[0].path == "/users"
        assert chunk1.endpoints[0].method == "GET"
        
        # 检查分块包含完整的上下文信息
        assert document.title in chunk1.content
        assert document.description in chunk1.content
    
    def test_chunk_document_by_path(self):
        """测试按路径分块文档"""
        endpoints = [
            Endpoint(path="/users", method="GET", summary="Get users"),
            Endpoint(path="/users", method="POST", summary="Create user"),
            Endpoint(path="/users/{id}", method="GET", summary="Get user"),
            Endpoint(path="/users/{id}", method="PUT", summary="Update user"),
            Endpoint(path="/posts", method="GET", summary="Get posts"),
            Endpoint(path="/posts/{id}", method="GET", summary="Get post")
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="API",
            version="1.0.0",
            endpoints=endpoints
        )
        
        chunks = self.chunker.chunk_document(document, strategy="by_path")
        
        # 应该按路径分组：/users, /users/{id}, /posts, /posts/{id}
        assert len(chunks) == 4
        
        # 检查/users分块
        users_chunk = next((c for c in chunks if "/users" in c.title and "{id}" not in c.title), None)
        assert users_chunk is not None
        assert len(users_chunk.endpoints) == 2  # GET和POST
        
        # 检查/posts分块
        posts_chunk = next((c for c in chunks if "/posts" in c.title and "{id}" not in c.title), None)
        assert posts_chunk is not None
        assert len(posts_chunk.endpoints) == 1  # 只有GET
    
    def test_chunk_document_by_tag(self):
        """测试按标签分块文档"""
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                summary="Get users",
                tags=["Users", "Public"]
            ),
            Endpoint(
                path="/users",
                method="POST",
                summary="Create user", 
                tags=["Users", "Admin"]
            ),
            Endpoint(
                path="/posts",
                method="GET",
                summary="Get posts",
                tags=["Posts", "Public"]
            ),
            Endpoint(
                path="/admin/settings",
                method="GET",
                summary="Get settings",
                tags=["Admin"]
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="API",
            version="1.0.0",
            endpoints=endpoints
        )
        
        chunks = self.chunker.chunk_document(document, strategy="by_tag")
        
        # 应该按主要标签分组
        assert len(chunks) >= 3  # Users, Posts, Admin
        
        # 检查Users分块
        users_chunk = next((c for c in chunks if "Users" in c.title), None)
        assert users_chunk is not None
        assert len(users_chunk.endpoints) == 2
    
    def test_chunk_document_by_size(self):
        """测试按大小分块文档"""
        # 创建多个端点，每个都有详细描述
        endpoints = []
        for i in range(10):
            endpoint = Endpoint(
                path=f"/endpoint{i}",
                method="GET",
                summary=f"Endpoint {i}",
                description="A" * 500,  # 长描述
                responses={"200": {"description": "Success"}}
            )
            endpoints.append(endpoint)
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="Large API",
            version="1.0.0",
            endpoints=endpoints
        )
        
        # 设置较小的分块大小
        chunks = self.chunker.chunk_document(document, strategy="by_size", max_tokens=2000)
        
        # 应该创建多个分块
        assert len(chunks) > 1
        
        # 每个分块的token数应该在合理范围内
        for chunk in chunks:
            estimated_tokens = self.chunker.estimate_tokens(chunk.content)
            assert estimated_tokens <= 2500  # 允许一些超出，因为需要保持完整性
    
    def test_estimate_tokens(self):
        """测试token数量估算"""
        # 测试英文文本
        english_text = "This is a test sentence with multiple words."
        tokens = self.chunker.estimate_tokens(english_text)
        assert tokens > 0
        assert tokens < len(english_text.split()) * 2  # 粗略估算
        
        # 测试空文本
        empty_tokens = self.chunker.estimate_tokens("")
        assert empty_tokens == 0
        
        # 测试长文本
        long_text = "word " * 1000
        long_tokens = self.chunker.estimate_tokens(long_text)
        assert long_tokens > 500  # 应该有相当数量的token
    
    def test_create_chunk_from_endpoints(self):
        """测试从端点创建分块"""
        endpoints = [
            Endpoint(
                path="/users",
                method="GET",
                summary="Get users",
                description="Retrieve all users"
            ),
            Endpoint(
                path="/users",
                method="POST",
                summary="Create user",
                description="Create a new user"
            )
        ]
        
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="User API",
            version="1.0.0",
            description="API for user management",
            endpoints=endpoints
        )
        
        chunk = self.chunker._create_chunk_from_endpoints(
            endpoints, document, "Users", "user_operations"
        )
        
        assert isinstance(chunk, DocumentChunk)
        assert chunk.title == "Users"
        assert chunk.chunk_id == "user_operations"
        assert chunk.chunk_type == "endpoint_group"
        assert len(chunk.endpoints) == 2
        assert chunk.token_count > 0
        
        # 检查内容包含必要信息
        assert "User API" in chunk.content
        assert "Get users" in chunk.content
        assert "Create user" in chunk.content
    
    def test_group_endpoints_by_path(self):
        """测试按路径分组端点"""
        endpoints = [
            Endpoint(path="/users", method="GET"),
            Endpoint(path="/users", method="POST"),
            Endpoint(path="/users/{id}", method="GET"),
            Endpoint(path="/users/{id}", method="PUT"),
            Endpoint(path="/posts", method="GET"),
            Endpoint(path="/posts/{id}", method="DELETE")
        ]
        
        groups = self.chunker._group_endpoints_by_path(endpoints)
        
        assert len(groups) == 4  # /users, /users/{id}, /posts, /posts/{id}
        assert "/users" in groups
        assert "/users/{id}" in groups
        assert "/posts" in groups
        assert "/posts/{id}" in groups
        
        assert len(groups["/users"]) == 2  # GET和POST
        assert len(groups["/users/{id}"]) == 2  # GET和PUT
        assert len(groups["/posts"]) == 1  # GET
        assert len(groups["/posts/{id}"]) == 1  # DELETE
    
    def test_group_endpoints_by_tag(self):
        """测试按标签分组端点"""
        endpoints = [
            Endpoint(path="/users", method="GET", tags=["Users"]),
            Endpoint(path="/users", method="POST", tags=["Users", "Admin"]),
            Endpoint(path="/posts", method="GET", tags=["Posts"]),
            Endpoint(path="/settings", method="GET", tags=["Admin"]),
            Endpoint(path="/public", method="GET", tags=[])  # 无标签
        ]
        
        groups = self.chunker._group_endpoints_by_tag(endpoints)
        
        assert "Users" in groups
        assert "Posts" in groups
        assert "Admin" in groups
        assert "Untagged" in groups  # 无标签的端点
        
        assert len(groups["Users"]) == 2
        assert len(groups["Posts"]) == 1
        assert len(groups["Admin"]) == 2  # POST /users 和 GET /settings
        assert len(groups["Untagged"]) == 1
    
    def test_chunk_document_invalid_strategy(self):
        """测试无效的分块策略"""
        document = ParsedDocument(
            document_type=DocumentType.OPENAPI,
            title="API",
            version="1.0.0",
            endpoints=[]
        )
        
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            self.chunker.chunk_document(document, strategy="invalid_strategy")
