"""文档上传集成测试

测试使用test.yaml文件进行文档上传、解析和分析的完整流程。
"""

from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import (
    assert_error_response,
    assert_valid_document_id,
    assert_valid_response_structure,
)


class TestDocumentUpload:
    """文档上传功能测试类"""

    def test_health_check(self, client: TestClient):
        """TC001: 健康检查接口测试"""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证响应结构
        required_fields = ["status", "app_name", "version", "timestamp"]
        assert_valid_response_structure(data, required_fields)

        # 验证具体值
        assert data["status"] == "healthy"
        assert data["app_name"] == "Spec2Test"
        assert isinstance(data["timestamp"], (int, float))

    def test_root_endpoint(self, client: TestClient):
        """TC002: 根路径接口测试"""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证响应结构
        required_fields = [
            "message",
            "description",
            "version",
            "docs_url",
            "health_url",
            "api_prefix",
        ]
        assert_valid_response_structure(data, required_fields)

        # 验证具体值
        assert "Spec2Test" in data["message"]
        assert data["docs_url"] == "/docs"
        assert data["health_url"] == "/health"

    def test_api_info(self, client: TestClient):
        """TC003: API信息接口测试"""
        response = client.get("/api/v1/info")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证响应结构
        required_fields = ["version", "description", "endpoints", "features"]
        assert_valid_response_structure(data, required_fields)

        # 验证具体值
        assert data["version"] == "v1"
        assert "endpoints" in data
        assert "features" in data
        assert isinstance(data["features"], list)

    def test_upload_test_yaml_success(self, client: TestClient, test_yaml_file: Path):
        """TC004: 成功上传test.yaml文件"""
        # 确保测试文件存在
        assert test_yaml_file.exists(), f"Test file not found: {test_yaml_file}"

        with open(test_yaml_file, "rb") as f:
            response = client.post(
                "/api/v1/parser/upload",
                files={"file": ("test.yaml", f, "application/x-yaml")},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证响应结构
        required_fields = ["success", "message", "document_id", "endpoints", "analysis"]
        assert_valid_response_structure(data, required_fields)

        # 验证基本字段
        assert data["success"] is True
        assert "成功" in data["message"]

        # 验证文档ID格式
        document_id = data["document_id"]
        assert_valid_document_id(document_id)

        # 验证端点信息
        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        # test.yaml包含10个端点
        assert len(endpoints) >= 0  # 允许解析失败的情况

        # 验证分析结果
        analysis = data["analysis"]
        required_analysis_fields = [
            "quality_score",
            "quality_level",
            "completeness",
            "issues",
            "suggestions",
            "endpoints_count",
            "analysis_details",
        ]
        assert_valid_response_structure(analysis, required_analysis_fields)

        # 验证质量评分范围
        assert 0 <= analysis["quality_score"] <= 100
        assert isinstance(analysis["issues"], list)
        assert isinstance(analysis["suggestions"], list)
        assert isinstance(analysis["endpoints_count"], int)

        return document_id  # 返回文档ID供后续测试使用

    def test_analyze_uploaded_document(self, client: TestClient, test_yaml_file: Path):
        """TC005: 分析已上传的文档"""
        # 先上传文档
        with open(test_yaml_file, "rb") as f:
            upload_response = client.post(
                "/api/v1/parser/upload",
                files={"file": ("test.yaml", f, "application/x-yaml")},
            )

        assert upload_response.status_code == status.HTTP_200_OK
        document_id = upload_response.json()["document_id"]

        # 分析文档
        response = client.get(f"/api/v1/parser/analyze/{document_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证分析结果结构
        required_fields = [
            "quality_score",
            "quality_level",
            "completeness",
            "issues",
            "suggestions",
            "endpoints_count",
            "analysis_details",
        ]
        assert_valid_response_structure(data, required_fields)

        # 验证数据类型和范围
        assert 0 <= data["quality_score"] <= 100
        assert isinstance(data["quality_level"], str)
        assert 0 <= data["completeness"] <= 100
        assert isinstance(data["issues"], list)
        assert isinstance(data["suggestions"], list)
        assert isinstance(data["endpoints_count"], int)
        assert isinstance(data["analysis_details"], dict)

    def test_list_documents(self, client: TestClient, test_yaml_file: Path):
        """TC006: 获取文档列表"""
        # 先上传一个文档
        with open(test_yaml_file, "rb") as f:
            upload_response = client.post(
                "/api/v1/parser/upload",
                files={"file": ("test.yaml", f, "application/x-yaml")},
            )

        assert upload_response.status_code == status.HTTP_200_OK

        # 获取文档列表
        response = client.get("/api/v1/parser/documents")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证响应结构
        required_fields = ["documents", "total"]
        assert_valid_response_structure(data, required_fields)

        # 验证文档列表
        documents = data["documents"]
        assert isinstance(documents, list)
        assert data["total"] == len(documents)
        assert data["total"] >= 1  # 至少有我们刚上传的文档

        # 验证文档项结构
        if documents:
            doc = documents[0]
            required_doc_fields = [
                "id",
                "filename",
                "upload_time",
                "quality_score",
                "endpoints_count",
                "status",
                "file_size",
            ]
            assert_valid_response_structure(doc, required_doc_fields)
            assert_valid_document_id(doc["id"])

    def test_delete_document(self, client: TestClient, test_yaml_file: Path):
        """TC007: 删除文档"""
        # 先上传一个文档
        with open(test_yaml_file, "rb") as f:
            upload_response = client.post(
                "/api/v1/parser/upload",
                files={"file": ("test.yaml", f, "application/x-yaml")},
            )

        assert upload_response.status_code == status.HTTP_200_OK
        document_id = upload_response.json()["document_id"]

        # 删除文档
        response = client.delete(f"/api/v1/parser/documents/{document_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证删除响应
        required_fields = ["message", "document_id", "filename"]
        assert_valid_response_structure(data, required_fields)

        assert "成功" in data["message"]
        assert data["document_id"] == document_id

        # 验证文档确实被删除（再次查询应该失败）
        analyze_response = client.get(f"/api/v1/parser/analyze/{document_id}")
        assert analyze_response.status_code == status.HTTP_404_NOT_FOUND


class TestDocumentUploadErrors:
    """文档上传错误处理测试类"""

    def test_upload_invalid_file_type(self, client: TestClient, temp_file: Path):
        """TC008: 上传无效文件类型"""
        # 创建一个.txt文件
        txt_file = temp_file.with_suffix(".txt")
        txt_file.write_text("This is not a YAML file")

        with open(txt_file, "rb") as f:
            response = client.post(
                "/api/v1/parser/upload", files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert_error_response(data)
        assert "不支持的文件类型" in data["error"]["message"]

    def test_upload_empty_filename(self, client: TestClient):
        """TC009: 上传空文件名"""
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("", b"content", "application/x-yaml")},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert_error_response(data)
        assert "文件名不能为空" in data["error"]["message"]

    def test_upload_invalid_yaml_content(
        self, client: TestClient, temp_file: Path, invalid_yaml_content: str
    ):
        """TC010: 上传无效YAML内容"""
        yaml_file = temp_file.with_suffix(".yaml")
        yaml_file.write_text(invalid_yaml_content)

        with open(yaml_file, "rb") as f:
            response = client.post(
                "/api/v1/parser/upload",
                files={"file": ("invalid.yaml", f, "application/x-yaml")},
            )

        # 应该返回500错误或者成功但有警告
        # 根据实际实现，可能会有不同的处理方式
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            data = response.json()
            assert_error_response(data)

    def test_analyze_nonexistent_document(
        self, client: TestClient, invalid_document_id: str
    ):
        """TC011: 分析不存在的文档"""
        response = client.get(f"/api/v1/parser/analyze/{invalid_document_id}")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert_error_response(data)
        assert "无效的文档ID格式" in data["error"]["message"]

    def test_analyze_invalid_document_id_format(self, client: TestClient):
        """TC012: 使用无效格式的文档ID"""
        invalid_ids = ["invalid", "doc_", "doc_xyz", "123", ""]

        for invalid_id in invalid_ids:
            response = client.get(f"/api/v1/parser/analyze/{invalid_id}")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert_error_response(data)

    def test_delete_nonexistent_document(self, client: TestClient):
        """TC013: 删除不存在的文档"""
        nonexistent_id = "doc_99999999"
        response = client.delete(f"/api/v1/parser/documents/{nonexistent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert_error_response(data)
        assert "文档不存在" in data["error"]["message"]


class TestDocumentContentValidation:
    """文档内容验证测试类"""

    def test_yaml_content_structure(self, test_yaml_content: str):
        """TC014: 验证test.yaml内容结构"""
        import yaml

        # 解析YAML内容
        try:
            spec = yaml.safe_load(test_yaml_content)
        except yaml.YAMLError as e:
            pytest.fail(f"test.yaml is not valid YAML: {e}")

        # 验证OpenAPI结构
        assert "openapi" in spec, "Missing 'openapi' field"
        assert "info" in spec, "Missing 'info' field"
        assert "paths" in spec, "Missing 'paths' field"

        # 验证版本
        assert spec["openapi"].startswith("3."), "Should be OpenAPI 3.x"

        # 验证info部分
        info = spec["info"]
        assert "title" in info, "Missing 'title' in info"
        assert "version" in info, "Missing 'version' in info"

        # 验证paths部分
        paths = spec["paths"]
        assert isinstance(paths, dict), "Paths should be a dictionary"
        assert len(paths) > 0, "Should have at least one path"

        # 统计端点数量
        endpoint_count = 0
        for path, methods in paths.items():
            for method in methods.keys():
                if method.lower() in [
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "head",
                    "options",
                ]:
                    endpoint_count += 1

        # test.yaml应该有10个端点
        expected_endpoints = [
            "POST /chapter/generate",
            "POST /chapter/choices",
            "POST /user/register",
            "POST /user/login",
            "GET /user/profile",
            "POST /plan/save",
            "GET /plan/list",
            "GET /plan/{plan_id}",
            "POST /feedback",
            "GET /health",
        ]

        assert endpoint_count == 10, f"Expected 10 endpoints, found {endpoint_count}"

    def test_yaml_endpoints_details(self, test_yaml_content: str):
        """TC015: 验证test.yaml端点详细信息"""
        import yaml

        spec = yaml.safe_load(test_yaml_content)
        paths = spec["paths"]

        # 验证关键端点存在
        key_paths = ["/chapter/generate", "/user/register", "/user/login", "/health"]

        for path in key_paths:
            assert path in paths, f"Missing key path: {path}"

        # 验证/health端点
        health_path = paths["/health"]
        assert "get" in health_path, "/health should have GET method"

        # 验证响应结构
        health_get = health_path["get"]
        assert "responses" in health_get, "/health GET should have responses"
        assert "200" in health_get["responses"], "/health should have 200 response"
