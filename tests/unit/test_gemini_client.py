"""Gemini客户端测试

测试Gemini结构化输出功能的正确性。
遵循TDD原则，使用真实数据进行测试。
"""

import json
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.llm.gemini_client import GeminiClient, GeminiConfig
from app.core.schemas import DocumentAnalysisSchema, QualityLevel, QuickAssessmentSchema
from app.utils.exceptions import LLMError


class TestGeminiConfig:
    """测试Gemini配置"""

    def test_valid_gemini_config_creation(self):
        """测试创建有效的Gemini配置"""
        config = GeminiConfig(
            api_key="test-api-key",
            model_name="gemini-2.0-flash-exp",
            temperature=0.1,
            max_output_tokens=8192,
            timeout_seconds=30,
        )

        assert config.api_key == "test-api-key"
        assert config.model_name == "gemini-2.0-flash-exp"
        assert config.temperature == 0.1
        assert config.max_output_tokens == 8192
        assert config.timeout_seconds == 30

    def test_gemini_config_defaults(self):
        """测试Gemini配置的默认值"""
        config = GeminiConfig(api_key="test-key")

        assert config.model_name == "gemini-2.0-flash-exp"
        assert config.temperature == 0.1
        assert config.max_output_tokens == 8192
        assert config.timeout_seconds == 30

    def test_gemini_config_validation_errors(self):
        """测试Gemini配置验证错误"""
        # 测试无效温度
        with pytest.raises(ValueError):
            GeminiConfig(api_key="test-key", temperature=3.0)  # 超出0-2范围

        # 测试无效token数
        with pytest.raises(ValueError):
            GeminiConfig(api_key="test-key", max_output_tokens=0)  # 必须大于0


class TestGeminiClient:
    """测试Gemini客户端"""

    @pytest.fixture
    def gemini_config(self) -> GeminiConfig:
        """Gemini配置fixture"""
        return GeminiConfig(
            api_key="test-api-key",
            model_name="gemini-2.0-flash-exp",
            temperature=0.1,
            timeout_seconds=10,
        )

    @pytest.fixture
    def mock_gemini_response(self) -> MagicMock:
        """模拟Gemini响应"""
        response = MagicMock()
        response.text = json.dumps(
            {
                "endpoint_count": 15,
                "complexity_score": 0.7,
                "has_quality_issues": True,
                "needs_detailed_analysis": True,
                "estimated_analysis_time": 20,
                "reason": "发现多个端点缺少描述和示例",
                "quick_issues": ["5个端点缺少描述", "8个端点缺少请求示例"],
                "overall_impression": "fair",
            }
        )
        response.candidates = []
        return response

    @pytest.fixture
    def sample_openapi_prompt(self) -> str:
        """示例OpenAPI分析提示词"""
        return """
        分析这个OpenAPI文档的质量。

        重点评估：
        1. 完整性：描述、参数、响应是否完整
        2. 准确性：类型定义、状态码是否正确
        3. 可读性：描述是否清晰易懂
        4. 可测试性：是否有足够信息生成测试用例

        OpenAPI文档：
        {
          "openapi": "3.0.0",
          "info": {"title": "Test API", "version": "1.0.0"},
          "paths": {
            "/users": {
              "get": {
                "summary": "获取用户列表",
                "responses": {
                  "200": {"description": "成功"}
                }
              }
            }
          }
        }
        """

    def test_gemini_client_initialization_success(self, gemini_config):
        """测试Gemini客户端成功初始化"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                mock_model = MagicMock()
                mock_genai.GenerativeModel.return_value = mock_model

                client = GeminiClient(gemini_config)

                assert client.config == gemini_config
                assert client.model == mock_model
                mock_genai.configure.assert_called_once_with(api_key="test-api-key")
                mock_genai.GenerativeModel.assert_called_once_with(
                    "gemini-2.0-flash-exp"
                )

    def test_gemini_client_initialization_failure_no_library(self, gemini_config):
        """测试Gemini库不可用时的初始化失败"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", False):
            with pytest.raises(LLMError) as exc_info:
                GeminiClient(gemini_config)

            assert "Gemini library not available" in str(exc_info.value)

    def test_gemini_client_initialization_failure_api_error(self, gemini_config):
        """测试API错误时的初始化失败"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                mock_genai.configure.side_effect = Exception("API key invalid")

                with pytest.raises(LLMError) as exc_info:
                    GeminiClient(gemini_config)

                assert "Gemini客户端初始化失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_structured_success(
        self, gemini_config, mock_gemini_response, sample_openapi_prompt
    ):
        """测试结构化输出生成成功"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                # 设置mock
                mock_model = MagicMock()
                mock_model.generate_content.return_value = mock_gemini_response
                mock_genai.GenerativeModel.return_value = mock_model

                # 创建客户端
                client = GeminiClient(gemini_config)

                # 测试结构化生成
                result = await client.generate_structured(
                    prompt=sample_openapi_prompt, response_schema=QuickAssessmentSchema
                )

                # 验证结果
                assert isinstance(result, QuickAssessmentSchema)
                assert result.endpoint_count == 15
                assert result.complexity_score == 0.7
                assert result.has_quality_issues is True
                assert result.overall_impression == QualityLevel.FAIR

                # 验证API调用
                mock_model.generate_content.assert_called_once()
                call_args = mock_model.generate_content.call_args
                assert call_args[0][0] == sample_openapi_prompt  # prompt参数

                # 验证生成配置
                generation_config = call_args[1]["generation_config"]
                assert generation_config.response_mime_type == "application/json"
                assert generation_config.temperature == 0.1

    @pytest.mark.asyncio
    async def test_generate_structured_empty_response(
        self, gemini_config, sample_openapi_prompt
    ):
        """测试空响应的错误处理"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                # 设置空响应
                mock_response = MagicMock()
                mock_response.text = ""

                mock_model = MagicMock()
                mock_model.generate_content.return_value = mock_response
                mock_genai.GenerativeModel.return_value = mock_model

                client = GeminiClient(gemini_config)

                with pytest.raises(LLMError) as exc_info:
                    await client.generate_structured(
                        prompt=sample_openapi_prompt,
                        response_schema=QuickAssessmentSchema,
                    )

                assert "empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_structured_invalid_json(
        self, gemini_config, sample_openapi_prompt
    ):
        """测试无效JSON响应的错误处理"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                # 设置无效JSON响应
                mock_response = MagicMock()
                mock_response.text = "这不是有效的JSON格式"
                mock_response.candidates = []

                mock_model = MagicMock()
                mock_model.generate_content.return_value = mock_response
                mock_genai.GenerativeModel.return_value = mock_model

                client = GeminiClient(gemini_config)

                with pytest.raises(LLMError) as exc_info:
                    await client.generate_structured(
                        prompt=sample_openapi_prompt,
                        response_schema=QuickAssessmentSchema,
                    )

                assert "不是有效的JSON格式" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_structured_timeout(
        self, gemini_config, sample_openapi_prompt
    ):
        """测试超时错误处理"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                mock_model = MagicMock()
                mock_genai.GenerativeModel.return_value = mock_model

                client = GeminiClient(gemini_config)

                # 模拟超时
                with patch(
                    "app.core.llm.gemini_client.asyncio.wait_for"
                ) as mock_wait_for:
                    mock_wait_for.side_effect = TimeoutError()

                    with pytest.raises(LLMError) as exc_info:
                        await client.generate_structured(
                            prompt=sample_openapi_prompt,
                            response_schema=QuickAssessmentSchema,
                        )

                    assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_text_success(self, gemini_config):
        """测试普通文本生成成功"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                # 设置mock响应
                mock_response = MagicMock()
                mock_response.text = "这是生成的文本响应"

                mock_model = MagicMock()
                mock_model.generate_content.return_value = mock_response
                mock_genai.GenerativeModel.return_value = mock_model

                client = GeminiClient(gemini_config)

                result = await client.generate_text("测试提示词")

                assert result == "这是生成的文本响应"
                mock_model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, gemini_config):
        """测试健康检查成功"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                # 设置mock响应
                mock_response = MagicMock()
                mock_response.text = "Health check OK"

                mock_model = MagicMock()
                mock_model.generate_content.return_value = mock_response
                mock_genai.GenerativeModel.return_value = mock_model

                client = GeminiClient(gemini_config)

                status = await client.health_check()

                assert status["available"] is True
                assert status["model_name"] == "gemini-2.0-flash-exp"
                assert "Health check OK" in status["test_response"]

    @pytest.mark.asyncio
    async def test_health_check_failure(self, gemini_config):
        """测试健康检查失败"""
        with patch("app.core.llm.gemini_client.GEMINI_AVAILABLE", True):
            with patch("app.core.llm.gemini_client.genai") as mock_genai:
                mock_model = MagicMock()
                mock_model.generate_content.side_effect = Exception("API Error")
                mock_genai.GenerativeModel.return_value = mock_model

                client = GeminiClient(gemini_config)

                status = await client.health_check()

                assert status["available"] is False
                assert "error" in status
                assert "API Error" in status["error"]
