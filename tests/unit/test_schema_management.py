"""Schema管理测试

测试Schema架构设计的正确性和完整性。
遵循TDD原则，先写测试，后实现功能。
"""

import json
from typing import Any, Dict

import pytest

from app.core.schemas import (
    AnalysisType,
    CaseSchema,
    DocumentAnalysisSchema,
    GenerationResultSchema,
    QualityLevel,
    QuickAssessmentSchema,
    get_schema_info,
    validate_schema,
)


class TestSchemaArchitecture:
    """测试Schema架构设计"""

    def test_schema_module_imports(self):
        """测试Schema模块导入正确性"""
        # 验证所有必要的Schema都能正确导入
        assert QuickAssessmentSchema is not None
        assert DocumentAnalysisSchema is not None
        assert CaseSchema is not None
        assert GenerationResultSchema is not None

        # 验证枚举类型导入
        assert QualityLevel.EXCELLENT == "excellent"
        assert AnalysisType.QUICK == "quick"

    def test_schema_version_info(self):
        """测试Schema版本信息"""
        info = get_schema_info()

        assert "version" in info
        assert "supported_versions" in info
        assert "schemas" in info

        # 验证版本格式
        assert isinstance(info["version"], str)
        assert len(info["supported_versions"]) > 0

        # 验证Schema分类
        assert "analysis" in info["schemas"]
        assert "generation" in info["schemas"]


class TestQuickAssessmentSchema:
    """测试快速评估Schema"""

    def test_valid_quick_assessment_creation(self, valid_quick_assessment_data):
        """测试创建有效的快速评估Schema"""
        schema = QuickAssessmentSchema(**valid_quick_assessment_data)

        assert schema.endpoint_count == 15
        assert schema.complexity_score == 0.7
        assert schema.has_quality_issues is True
        assert schema.needs_detailed_analysis is True
        assert schema.overall_impression == QualityLevel.FAIR

        # 验证自动生成的字段
        assert schema.schema_version is not None
        assert schema.generated_at is not None

    def test_quick_assessment_validation_errors(self):
        """测试快速评估Schema验证错误"""
        # 测试负数端点数
        with pytest.raises(ValueError):
            QuickAssessmentSchema(
                endpoint_count=-1,
                complexity_score=0.5,
                has_quality_issues=False,
                needs_detailed_analysis=False,
                estimated_analysis_time=10,
                reason="测试",
            )

        # 测试复杂度评分超出范围
        with pytest.raises(ValueError):
            QuickAssessmentSchema(
                endpoint_count=10,
                complexity_score=1.5,  # 超出0-1范围
                has_quality_issues=False,
                needs_detailed_analysis=False,
                estimated_analysis_time=10,
                reason="测试",
            )

    def test_quick_assessment_json_serialization(self, valid_quick_assessment_data):
        """测试快速评估Schema的JSON序列化"""
        schema = QuickAssessmentSchema(**valid_quick_assessment_data)

        # 测试序列化
        json_data = schema.model_dump()
        assert isinstance(json_data, dict)

        # 测试JSON字符串化
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)

        # 测试反序列化
        parsed_data = json.loads(json_str)
        recreated_schema = QuickAssessmentSchema(**parsed_data)
        assert recreated_schema.endpoint_count == schema.endpoint_count


@pytest.fixture
def valid_quick_assessment_data() -> Dict[str, Any]:
    """有效的快速评估数据"""
    return {
        "endpoint_count": 15,
        "complexity_score": 0.7,
        "has_quality_issues": True,
        "needs_detailed_analysis": True,
        "estimated_analysis_time": 20,
        "reason": "发现多个端点缺少描述和示例",
        "quick_issues": ["5个端点缺少描述", "8个端点缺少请求示例"],
        "overall_impression": "fair",
    }


class TestDocumentAnalysisSchema:
    """测试文档分析Schema"""

    @pytest.fixture
    def valid_document_analysis_data(
        self, valid_quick_assessment_data
    ) -> Dict[str, Any]:
        """有效的文档分析数据"""
        return {
            "document_path": "/path/to/openapi.yaml",
            "document_type": "openapi",
            "analysis_method": "detailed",
            "quick_assessment": valid_quick_assessment_data,
            "detailed_analysis": {
                "overall_score": 75,
                "quality_level": "good",
                "dimension_scores": {
                    "completeness": 20,
                    "accuracy": 22,
                    "readability": 18,
                    "testability": 15,
                },
                "detailed_issues": [],
                "testing_readiness": {
                    "can_generate_basic_tests": True,
                    "can_generate_edge_cases": True,
                    "can_generate_error_tests": False,
                    "missing_for_complete_testing": ["错误响应定义"],
                    "estimated_test_coverage": 80,
                },
                "improvement_suggestions": [],
                "statistics": {
                    "total_endpoints": 15,
                    "endpoints_by_method": {"GET": 8, "POST": 5, "DELETE": 2},
                    "endpoints_by_tag": {"users": 6, "orders": 9},
                    "missing_descriptions": 3,
                    "missing_examples": 5,
                    "missing_schemas": 2,
                },
            },
            "final_score": 75,
            "final_quality_level": "good",
            "analysis_time_seconds": 12.5,
        }

    def test_valid_document_analysis_creation(self, valid_document_analysis_data):
        """测试创建有效的文档分析Schema"""
        schema = DocumentAnalysisSchema(**valid_document_analysis_data)

        assert schema.document_path == "/path/to/openapi.yaml"
        assert schema.analysis_method == AnalysisType.DETAILED
        assert schema.final_score == 75
        assert schema.final_quality_level == QualityLevel.GOOD

        # 测试属性方法
        assert schema.has_detailed_analysis is True
        assert len(schema.primary_issues) == 0  # 当前测试数据中没有问题
        assert len(schema.primary_suggestions) == 0  # 当前测试数据中没有建议

    def test_document_analysis_without_detailed_analysis(
        self, valid_quick_assessment_data
    ):
        """测试只有快速评估的文档分析"""
        data = {
            "document_path": "/path/to/simple.yaml",
            "analysis_method": "quick",
            "quick_assessment": valid_quick_assessment_data,
            "final_score": 60,
            "final_quality_level": "fair",
            "analysis_time_seconds": 3.2,
        }

        schema = DocumentAnalysisSchema(**data)

        assert schema.has_detailed_analysis is False
        assert schema.detailed_analysis is None
        assert len(schema.primary_issues) == 0
        assert len(schema.primary_suggestions) == 0


class TestCaseSchemaTests:
    """测试测试用例Schema"""

    @pytest.fixture
    def valid_test_case_data(self) -> Dict[str, Any]:
        """有效的测试用例数据"""
        return {
            "name": "测试获取用户信息接口",
            "description": "验证GET /users/{id}接口能正确返回用户信息",
            "request_data": {
                "path_params": {"id": "123"},
                "query_params": {"include": "profile"},
            },
            "expected_status_code": 200,
            "expected_response": {
                "id": "123",
                "name": "测试用户",
                "email": "test@example.com",
            },
            "test_steps": [
                {
                    "step_number": 1,
                    "action": "发送GET请求",
                    "description": "向/users/123发送GET请求",
                }
            ],
            "assertions": [
                {
                    "type": "status_code",
                    "description": "验证状态码为200",
                    "expected_value": 200,
                }
            ],
            "test_scenario": "normal",
            "priority": 2,
        }

    def test_valid_test_case_creation(self, valid_test_case_data):
        """测试创建有效的测试用例Schema"""
        schema = CaseSchema(**valid_test_case_data)

        assert schema.name == "测试获取用户信息接口"
        assert schema.expected_status_code == 200
        assert schema.priority == 2
        assert schema.test_scenario == "normal"

        # 验证嵌套Schema
        assert len(schema.test_steps) == 1
        assert schema.test_steps[0].step_number == 1

        assert len(schema.assertions) == 1
        assert schema.assertions[0].type == "status_code"

    def test_test_case_validation_errors(self):
        """测试测试用例Schema验证错误"""
        # 测试空名称
        with pytest.raises(ValueError):
            CaseSchema(name="", description="测试描述", test_scenario="normal")  # 空名称

        # 测试无效状态码
        with pytest.raises(ValueError):
            CaseSchema(
                name="测试用例",
                description="测试描述",
                expected_status_code=999,  # 无效状态码
                test_scenario="normal",
            )

        # 测试无效优先级
        with pytest.raises(ValueError):
            CaseSchema(
                name="测试用例",
                description="测试描述",
                priority=10,  # 超出1-5范围
                test_scenario="normal",
            )


class TestSchemaValidation:
    """测试Schema验证功能"""

    def test_validate_schema_function(self, valid_quick_assessment_data):
        """测试Schema验证函数"""
        # 测试有效数据验证
        result = validate_schema(valid_quick_assessment_data, QuickAssessmentSchema)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.validated_data is not None

    def test_validate_invalid_schema(self):
        """测试无效Schema验证"""
        invalid_data = {
            "endpoint_count": "not_a_number",  # 类型错误
            "complexity_score": 0.5,
            "has_quality_issues": False,
            "needs_detailed_analysis": False,
            "estimated_analysis_time": 10,
            "reason": "测试",
        }

        result = validate_schema(invalid_data, QuickAssessmentSchema)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.validated_data is None
