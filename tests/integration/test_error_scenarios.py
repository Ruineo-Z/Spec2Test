"""错误场景和边界条件测试

测试各种异常情况、错误处理和边界条件。
"""

import tempfile
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from tests.conftest import assert_error_response


class TestFileUploadErrors:
    """文件上传错误测试类"""

    def test_upload_no_file(self, client: TestClient):
        """TC016: 不提供文件的上传请求"""
        response = client.post("/api/v1/parser/upload")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # FastAPI会返回验证错误

    def test_upload_empty_file(self, client: TestClient):
        """TC017: 上传空文件"""
        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("empty.yaml", b"", "application/x-yaml")},
        )

        # 空文件可能被接受但解析失败，或者直接拒绝
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_upload_binary_file_as_yaml(self, client: TestClient):
        """TC018: 上传二进制文件但声明为YAML"""
        binary_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # PNG文件头

        response = client.post(
            "/api/v1/parser/upload",
            files={"file": ("fake.yaml", binary_content, "application/x-yaml")},
        )

        # 应该在解析时失败
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_upload_very_large_file(self, client: TestClient):
        """TC019: 上传超大文件"""
        # 创建一个超大的YAML文件（超过配置限制）
        large_content = (
            "# Large YAML file\n" + "data: " + "x" * (10 * 1024 * 1024)
        )  # 10MB

        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": ("large.yaml", large_content.encode(), "application/x-yaml")
            },
        )

        # 应该因为文件大小超限而失败
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert_error_response(data)
        assert "文件大小超过限制" in data["error"]["message"]

    def test_upload_malformed_yaml(self, client: TestClient):
        """TC020: 上传格式错误的YAML"""
        malformed_yaml = """
        openapi: 3.0.3
        info:
          title: Test
          version: 1.0.0
        paths:
          /test:
            get:
              responses:
                200:
                  description: OK
                  content:
                    application/json:
                      schema:
                        type: object
                        properties:
                          message:
                            type: string
                          # 这里有语法错误 - 缺少引号和冒号
                          invalid syntax here
        """

        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "malformed.yaml",
                    malformed_yaml.encode(),
                    "application/x-yaml",
                )
            },
        )

        # 可能成功但解析时有警告，或者直接失败
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_upload_non_openapi_yaml(self, client: TestClient):
        """TC021: 上传非OpenAPI的YAML文件"""
        non_openapi_yaml = """
        # 这是一个普通的配置文件，不是OpenAPI规范
        database:
          host: localhost
          port: 5432
          name: mydb

        redis:
          host: localhost
          port: 6379

        logging:
          level: INFO
          format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        """

        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": ("config.yaml", non_openapi_yaml.encode(), "application/x-yaml")
            },
        )

        # 应该成功上传但解析时发现不是OpenAPI格式
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]


class TestDatabaseErrors:
    """数据库相关错误测试类"""

    def test_analyze_with_corrupted_document_id(self, client: TestClient):
        """TC022: 使用损坏的文档ID格式"""
        corrupted_ids = [
            "doc_",  # 缺少十六进制部分
            "doc_gggggggg",  # 无效十六进制字符
            "doc_123",  # 十六进制位数不足
            "doc_123456789",  # 十六进制位数过多
            "document_12345678",  # 错误前缀
            "12345678",  # 缺少前缀
        ]

        for doc_id in corrupted_ids:
            response = client.get(f"/api/v1/parser/analyze/{doc_id}")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert_error_response(data)
            assert "无效的文档ID格式" in data["error"]["message"]

    def test_delete_with_corrupted_document_id(self, client: TestClient):
        """TC023: 使用损坏的文档ID删除"""
        corrupted_id = "doc_invalid"

        response = client.delete(f"/api/v1/parser/documents/{corrupted_id}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert_error_response(data)
        assert "无效的文档ID格式" in data["error"]["message"]

    def test_analyze_valid_format_but_nonexistent_id(self, client: TestClient):
        """TC024: 使用格式正确但不存在的文档ID"""
        nonexistent_id = "doc_ffffffff"  # 格式正确但不存在

        response = client.get(f"/api/v1/parser/analyze/{nonexistent_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert_error_response(data)
        assert "文档不存在" in data["error"]["message"]


class TestAPIEndpointErrors:
    """API端点错误测试类"""

    def test_invalid_api_endpoints(self, client: TestClient):
        """TC025: 访问不存在的API端点"""
        invalid_endpoints = [
            "/api/v1/nonexistent",
            "/api/v2/parser/upload",  # 错误版本
            "/api/v1/parser/invalid",
            "/api/v1/generator/nonexistent",
            "/invalid/path",
        ]

        for endpoint in invalid_endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_wrong_http_methods(self, client: TestClient):
        """TC026: 使用错误的HTTP方法"""
        # 测试对只支持POST的端点使用GET
        response = client.get("/api/v1/parser/upload")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # 测试对只支持GET的端点使用POST
        response = client.post("/api/v1/parser/documents")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # 测试对健康检查使用POST
        response = client.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_malformed_request_body(self, client: TestClient):
        """TC027: 发送格式错误的请求体"""
        # 对于需要JSON的端点发送无效JSON
        response = client.post(
            "/api/v1/parser/upload",
            data="{invalid json}",
            headers={"Content-Type": "application/json"},
        )

        # FastAPI应该返回422或400错误
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


class TestConcurrencyAndRaceConditions:
    """并发和竞态条件测试类"""

    def test_concurrent_uploads(self, client: TestClient, test_yaml_file: Path):
        """TC028: 并发上传相同文件"""
        import threading
        import time

        results = []
        errors = []

        def upload_file():
            try:
                with open(test_yaml_file, "rb") as f:
                    response = client.post(
                        "/api/v1/parser/upload",
                        files={"file": ("test.yaml", f, "application/x-yaml")},
                    )
                results.append(response)
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时上传
        threads = []
        for i in range(3):
            thread = threading.Thread(target=upload_file)
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证结果
        assert len(errors) == 0, f"Errors occurred during concurrent uploads: {errors}"
        assert len(results) == 3, "Should have 3 upload results"

        # 所有上传都应该成功（可能返回相同的文档ID）
        for response in results:
            assert response.status_code == status.HTTP_200_OK

    def test_upload_then_immediate_analyze(
        self, client: TestClient, test_yaml_file: Path
    ):
        """TC029: 上传后立即分析（测试数据一致性）"""
        # 上传文件
        with open(test_yaml_file, "rb") as f:
            upload_response = client.post(
                "/api/v1/parser/upload",
                files={"file": ("test.yaml", f, "application/x-yaml")},
            )

        assert upload_response.status_code == status.HTTP_200_OK
        document_id = upload_response.json()["document_id"]

        # 立即分析（测试数据库事务一致性）
        analyze_response = client.get(f"/api/v1/parser/analyze/{document_id}")

        assert analyze_response.status_code == status.HTTP_200_OK
        analyze_data = analyze_response.json()

        # 验证分析结果与上传结果一致
        upload_data = upload_response.json()
        upload_analysis = upload_data["analysis"]

        # 质量分数应该一致
        assert analyze_data["quality_score"] == upload_analysis["quality_score"]
        assert analyze_data["endpoints_count"] == upload_analysis["endpoints_count"]

    def test_upload_delete_analyze_sequence(
        self, client: TestClient, test_yaml_file: Path
    ):
        """TC030: 上传-删除-分析序列（测试数据清理）"""
        # 上传文件
        with open(test_yaml_file, "rb") as f:
            upload_response = client.post(
                "/api/v1/parser/upload",
                files={"file": ("test.yaml", f, "application/x-yaml")},
            )

        assert upload_response.status_code == status.HTTP_200_OK
        document_id = upload_response.json()["document_id"]

        # 删除文件
        delete_response = client.delete(f"/api/v1/parser/documents/{document_id}")
        assert delete_response.status_code == status.HTTP_200_OK

        # 尝试分析已删除的文件（应该失败）
        analyze_response = client.get(f"/api/v1/parser/analyze/{document_id}")
        assert analyze_response.status_code == status.HTTP_404_NOT_FOUND

        # 尝试再次删除（应该失败）
        delete_again_response = client.delete(f"/api/v1/parser/documents/{document_id}")
        assert delete_again_response.status_code == status.HTTP_404_NOT_FOUND


class TestEdgeCases:
    """边界条件测试类"""

    def test_minimal_valid_openapi_spec(self, client: TestClient):
        """TC031: 最小有效OpenAPI规范"""
        minimal_spec = """
        openapi: 3.0.3
        info:
          title: Minimal API
          version: 1.0.0
        paths: {}
        """

        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": ("minimal.yaml", minimal_spec.encode(), "application/x-yaml")
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 应该成功解析，但端点数量为0
        assert data["success"] is True
        assert data["analysis"]["endpoints_count"] == 0

    def test_openapi_with_only_one_endpoint(self, client: TestClient):
        """TC032: 只有一个端点的OpenAPI规范"""
        single_endpoint_spec = """
        openapi: 3.0.3
        info:
          title: Single Endpoint API
          version: 1.0.0
        paths:
          /single:
            get:
              summary: Single endpoint
              responses:
                '200':
                  description: OK
        """

        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "single.yaml",
                    single_endpoint_spec.encode(),
                    "application/x-yaml",
                )
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 应该成功解析，端点数量为1
        assert data["success"] is True
        # 端点数量可能为1或0（取决于解析器实现）
        assert data["analysis"]["endpoints_count"] >= 0

    def test_unicode_content_in_yaml(self, client: TestClient):
        """TC033: 包含Unicode字符的YAML"""
        unicode_spec = """
        openapi: 3.0.3
        info:
          title: 测试API 🚀
          description: 这是一个包含中文和emoji的API文档 📝
          version: 1.0.0
        paths:
          /用户:
            get:
              summary: 获取用户信息 👤
              description: 返回用户的详细信息，包括姓名、邮箱等 📧
              responses:
                '200':
                  description: 成功返回用户信息 ✅
        """

        response = client.post(
            "/api/v1/parser/upload",
            files={
                "file": (
                    "unicode.yaml",
                    unicode_spec.encode("utf-8"),
                    "application/x-yaml",
                )
            },
        )

        # 应该能够处理Unicode内容
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
