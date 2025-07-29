"""OpenAPI解析器单元测试

遵循TDD原则，先编写失败的测试用例。
"""

import json
from pathlib import Path

import pytest
import yaml

from app.core.models import APIEndpoint, DocumentAnalysis, DocumentQuality, HttpMethod
from app.utils.exceptions import DocumentParseError, DocumentValidationError

# 移除未使用的导入


# 这些导入会失败，因为我们还没有实现OpenAPIParser
# 这正是TDD的Red阶段 - 测试应该失败
try:
    from app.core.parser.openapi_parser import OpenAPIParser
except ImportError:
    # 在实现之前，这个导入会失败
    OpenAPIParser = None


class TestOpenAPIParser:
    """OpenAPI解析器测试类"""

    @pytest.fixture
    def sample_openapi_file(self):
        """样例OpenAPI文档文件路径"""
        return Path(__file__).parent.parent / "fixtures" / "sample_openapi.yaml"

    @pytest.fixture
    def poor_quality_file(self):
        """质量较差的OpenAPI文档文件路径"""
        return Path(__file__).parent.parent / "fixtures" / "poor_quality_openapi.yaml"

    @pytest.fixture
    def sample_openapi_content(self, sample_openapi_file):
        """样例OpenAPI文档内容"""
        with open(sample_openapi_file, "r", encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def parser(self):
        """OpenAPI解析器实例"""
        if OpenAPIParser is None:
            pytest.skip("OpenAPIParser not implemented yet")
        return OpenAPIParser()

    # ==================== 基础解析功能测试 ====================

    def test_parser_initialization(self, parser):
        """测试解析器初始化"""
        assert parser is not None
        assert hasattr(parser, "parse_file")
        assert hasattr(parser, "parse_content")
        assert hasattr(parser, "extract_endpoints")
        assert hasattr(parser, "analyze_quality")

    def test_parse_yaml_file_success(self, parser, sample_openapi_file):
        """测试成功解析YAML文件"""
        result = parser.parse_file(sample_openapi_file)

        # 验证返回的是字典
        assert isinstance(result, dict)

        # 验证基本结构
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result

        # 验证版本信息
        assert result["openapi"] == "3.0.3"
        assert result["info"]["title"] == "Sample Pet Store API"
        assert result["info"]["version"] == "1.0.0"

    def test_parse_yaml_content_success(self, parser, sample_openapi_content):
        """测试成功解析YAML内容"""
        result = parser.parse_content(sample_openapi_content)

        assert isinstance(result, dict)
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result

    def test_parse_json_content_success(self, parser, sample_openapi_content):
        """测试成功解析JSON内容"""
        # 将YAML转换为JSON
        yaml_data = yaml.safe_load(sample_openapi_content)
        json_content = json.dumps(yaml_data)

        result = parser.parse_content(json_content)

        assert isinstance(result, dict)
        assert "openapi" in result
        assert "info" in result
        assert "paths" in result

    def test_parse_nonexistent_file_raises_error(self, parser):
        """测试解析不存在的文件抛出异常"""
        nonexistent_file = Path("/nonexistent/file.yaml")

        with pytest.raises(DocumentParseError) as exc_info:
            parser.parse_file(nonexistent_file)

        assert (
            "File not found" in str(exc_info.value)
            or "not found" in str(exc_info.value).lower()
        )

    def test_parse_invalid_yaml_raises_error(self, parser):
        """测试解析无效YAML内容抛出异常"""
        invalid_yaml = """
        openapi: 3.0.3
        info:
          title: Test
          version: 1.0.0
        paths:
          /test:
            get:
              responses:
                '200':
                  description: OK
              # 无效的YAML缩进
            invalid_indent
        """

        with pytest.raises(DocumentParseError):
            parser.parse_content(invalid_yaml)

    def test_parse_invalid_json_raises_error(self, parser):
        """测试解析无效JSON内容抛出异常"""
        invalid_json = '{"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}, "paths": {"invalid": }'

        with pytest.raises(DocumentParseError):
            parser.parse_content(invalid_json)

    # ==================== 端点提取测试 ====================

    def test_extract_endpoints_success(self, parser, sample_openapi_file):
        """测试成功提取API端点"""
        spec = parser.parse_file(sample_openapi_file)
        endpoints = parser.extract_endpoints(spec)

        # 验证返回的是列表
        assert isinstance(endpoints, list)
        assert len(endpoints) > 0

        # 验证每个端点都是APIEndpoint实例
        for endpoint in endpoints:
            assert isinstance(endpoint, APIEndpoint)
            assert endpoint.path is not None
            assert endpoint.method is not None
            assert isinstance(endpoint.method, HttpMethod)

    def test_extract_endpoints_contains_expected_paths(
        self, parser, sample_openapi_file
    ):
        """测试提取的端点包含预期的路径"""
        spec = parser.parse_file(sample_openapi_file)
        endpoints = parser.extract_endpoints(spec)

        # 提取所有路径和方法的组合
        path_method_pairs = [(ep.path, ep.method.value) for ep in endpoints]

        # 验证包含预期的端点
        expected_pairs = [
            ("/pets", "GET"),
            ("/pets", "POST"),
            ("/pets/{petId}", "GET"),
            ("/pets/{petId}", "PUT"),
            ("/pets/{petId}", "DELETE"),
        ]

        for expected_pair in expected_pairs:
            assert expected_pair in path_method_pairs

    def test_extract_endpoints_with_parameters(self, parser, sample_openapi_file):
        """测试提取端点参数信息"""
        spec = parser.parse_file(sample_openapi_file)
        endpoints = parser.extract_endpoints(spec)

        # 找到GET /pets端点
        get_pets_endpoint = next(
            (
                ep
                for ep in endpoints
                if ep.path == "/pets" and ep.method == HttpMethod.GET
            ),
            None,
        )

        assert get_pets_endpoint is not None
        assert len(get_pets_endpoint.query_parameters) > 0
        assert "limit" in get_pets_endpoint.query_parameters
        assert "offset" in get_pets_endpoint.query_parameters

    def test_extract_endpoints_with_path_parameters(self, parser, sample_openapi_file):
        """测试提取路径参数信息"""
        spec = parser.parse_file(sample_openapi_file)
        endpoints = parser.extract_endpoints(spec)

        # 找到GET /pets/{petId}端点
        get_pet_endpoint = next(
            (
                ep
                for ep in endpoints
                if ep.path == "/pets/{petId}" and ep.method == HttpMethod.GET
            ),
            None,
        )

        assert get_pet_endpoint is not None
        assert len(get_pet_endpoint.path_parameters) > 0
        assert "petId" in get_pet_endpoint.path_parameters

    def test_extract_endpoints_with_request_body(self, parser, sample_openapi_file):
        """测试提取请求体信息"""
        spec = parser.parse_file(sample_openapi_file)
        endpoints = parser.extract_endpoints(spec)

        # 找到POST /pets端点
        post_pets_endpoint = next(
            (
                ep
                for ep in endpoints
                if ep.path == "/pets" and ep.method == HttpMethod.POST
            ),
            None,
        )

        assert post_pets_endpoint is not None
        assert post_pets_endpoint.request_body is not None
        assert len(post_pets_endpoint.request_examples) > 0

    def test_extract_endpoints_with_responses(self, parser, sample_openapi_file):
        """测试提取响应信息"""
        spec = parser.parse_file(sample_openapi_file)
        endpoints = parser.extract_endpoints(spec)

        # 验证所有端点都有响应定义
        for endpoint in endpoints:
            assert len(endpoint.responses) > 0
            assert (
                "200" in endpoint.responses
                or "201" in endpoint.responses
                or "204" in endpoint.responses
            )

    # ==================== 文档质量分析测试 ====================

    def test_analyze_quality_good_document(self, parser, sample_openapi_file):
        """测试分析高质量文档"""
        spec = parser.parse_file(sample_openapi_file)
        analysis = parser.analyze_quality(spec)

        # 验证返回DocumentAnalysis实例
        assert isinstance(analysis, DocumentAnalysis)

        # 验证基本信息
        assert analysis.document_type == "openapi"
        assert analysis.total_endpoints > 0

        # 高质量文档应该有较高的评分
        assert analysis.quality_score >= 70
        assert analysis.quality_level in [
            DocumentQuality.GOOD,
            DocumentQuality.EXCELLENT,
        ]

    def test_analyze_quality_poor_document(self, parser, poor_quality_file):
        """测试分析低质量文档"""
        spec = parser.parse_file(poor_quality_file)
        analysis = parser.analyze_quality(spec)

        # 验证返回DocumentAnalysis实例
        assert isinstance(analysis, DocumentAnalysis)

        # 低质量文档应该有较低的评分
        assert analysis.quality_score < 70
        assert analysis.quality_level in [DocumentQuality.POOR, DocumentQuality.FAIR]

        # 应该发现问题
        assert len(analysis.issues) > 0
        assert len(analysis.suggestions) > 0

    def test_analyze_quality_missing_descriptions(self, parser, poor_quality_file):
        """测试检测缺少描述的问题"""
        spec = parser.parse_file(poor_quality_file)
        analysis = parser.analyze_quality(spec)

        # 应该检测到缺少描述的端点
        assert analysis.missing_descriptions > 0

    def test_analyze_quality_missing_examples(self, parser, poor_quality_file):
        """测试检测缺少示例的问题"""
        spec = parser.parse_file(poor_quality_file)
        analysis = parser.analyze_quality(spec)

        # 应该检测到缺少示例的端点
        assert analysis.missing_examples > 0

    def test_analyze_quality_missing_schemas(self, parser, poor_quality_file):
        """测试检测缺少模式定义的问题"""
        spec = parser.parse_file(poor_quality_file)
        analysis = parser.analyze_quality(spec)

        # 应该检测到缺少模式定义的端点
        assert analysis.missing_schemas > 0

    def test_analyze_quality_statistics(self, parser, sample_openapi_file):
        """测试统计信息生成"""
        spec = parser.parse_file(sample_openapi_file)
        analysis = parser.analyze_quality(spec)

        # 验证统计信息
        assert isinstance(analysis.endpoints_by_method, dict)
        assert isinstance(analysis.endpoints_by_tag, dict)

        # 验证方法统计
        assert "GET" in analysis.endpoints_by_method
        assert "POST" in analysis.endpoints_by_method

        # 验证标签统计
        assert "pets" in analysis.endpoints_by_tag

    # ==================== 错误处理测试 ====================

    def test_validate_openapi_version_invalid(self, parser):
        """测试验证无效的OpenAPI版本"""
        invalid_spec = {
            "openapi": "2.0",  # 不支持的版本
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }

        with pytest.raises(DocumentValidationError) as exc_info:
            parser.extract_endpoints(invalid_spec)

        assert "version" in str(exc_info.value).lower()

    def test_validate_missing_required_fields(self, parser):
        """测试验证缺少必需字段"""
        invalid_spec = {
            "openapi": "3.0.3",
            # 缺少info字段
            "paths": {},
        }

        with pytest.raises(DocumentValidationError):
            parser.extract_endpoints(invalid_spec)

    def test_extract_endpoints_empty_paths(self, parser):
        """测试提取空路径的端点"""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }

        endpoints = parser.extract_endpoints(spec)
        assert isinstance(endpoints, list)
        assert len(endpoints) == 0

    # ==================== 边界条件测试 ====================

    def test_parse_large_document(self, parser):
        """测试解析大型文档的性能"""
        # 创建一个包含大量端点的文档
        large_spec = {
            "openapi": "3.0.3",
            "info": {"title": "Large API", "version": "1.0.0"},
            "paths": {},
        }

        # 生成100个端点
        for i in range(100):
            path = f"/resource{i}"
            large_spec["paths"][path] = {
                "get": {
                    "summary": f"Get resource {i}",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {"schema": {"type": "object"}}
                            },
                        }
                    },
                }
            }

        # 测试解析性能（应该在合理时间内完成）
        import time

        start_time = time.time()

        endpoints = parser.extract_endpoints(large_spec)
        analysis = parser.analyze_quality(large_spec)

        end_time = time.time()

        # 验证结果
        assert len(endpoints) == 100
        assert isinstance(analysis, DocumentAnalysis)

        # 性能要求：处理100个端点应该在5秒内完成
        assert (end_time - start_time) < 5.0

    def test_parse_document_with_special_characters(self, parser):
        """测试解析包含特殊字符的文档"""
        spec_with_special_chars = {
            "openapi": "3.0.3",
            "info": {
                "title": "API with 特殊字符 and émojis 🚀",
                "version": "1.0.0",
                "description": "This API contains special characters: @#$%^&*()",
            },
            "paths": {
                "/users/{user-id}": {
                    "get": {
                        "summary": "Get user with special chars in path",
                        "parameters": [
                            {
                                "name": "user-id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Success with 中文 description",
                                "content": {
                                    "application/json": {"schema": {"type": "object"}}
                                },
                            }
                        },
                    }
                }
            },
        }

        endpoints = parser.extract_endpoints(spec_with_special_chars)
        analysis = parser.analyze_quality(spec_with_special_chars)

        assert len(endpoints) == 1
        assert endpoints[0].path == "/users/{user-id}"
        assert isinstance(analysis, DocumentAnalysis)
