"""Gemini客户端封装

提供结构化输出支持的Gemini API客户端。
"""

import asyncio
import json
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from app.utils.exceptions import LLMError
from app.utils.logger import get_logger

from ..schemas.base import BaseSchema

logger = get_logger(__name__)


class GeminiConfig(BaseModel):
    """Gemini配置"""

    api_key: str = Field(..., description="Gemini API密钥")
    model_name: str = Field(default="gemini-2.0-flash-exp", description="模型名称")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="温度参数")
    max_output_tokens: int = Field(default=8192, ge=1, description="最大输出token数")
    timeout_seconds: int = Field(default=30, ge=1, description="请求超时时间")


class GeminiClient:
    """Gemini客户端，支持结构化输出"""

    def __init__(self, config: GeminiConfig):
        """初始化Gemini客户端

        Args:
            config: Gemini配置

        Raises:
            LLMError: 初始化失败
        """
        if not GEMINI_AVAILABLE:
            raise LLMError(
                "Gemini library not available. Please install: pip install google-generativeai"
            )

        self.config = config
        self.model = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """初始化Gemini客户端"""
        try:
            genai.configure(api_key=self.config.api_key)
            self.model = genai.GenerativeModel(self.config.model_name)
            logger.info(
                f"Gemini client initialized with model: {self.config.model_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise LLMError(f"Gemini客户端初始化失败: {e}")

    async def generate_structured(
        self, prompt: str, response_schema: Type[BaseSchema], **kwargs
    ) -> BaseSchema:
        """生成结构化输出

        Args:
            prompt: 提示词
            response_schema: 响应Schema类
            **kwargs: 额外的生成配置

        Returns:
            结构化响应对象

        Raises:
            LLMError: 生成失败
        """
        if not self.model:
            raise LLMError("Gemini client not initialized")

        try:
            # 构建生成配置
            # 手动构建简化的JSON Schema，避免Pydantic生成的复杂Schema
            if (
                hasattr(response_schema, "__name__")
                and response_schema.__name__ == "GeminiQuickAssessmentSchema"
            ):
                # 为GeminiQuickAssessmentSchema手动构建简单Schema
                schema = {
                    "type": "object",
                    "properties": {
                        "endpoint_count": {"type": "integer"},
                        "complexity_score": {"type": "number"},
                        "has_quality_issues": {"type": "boolean"},
                        "needs_detailed_analysis": {"type": "boolean"},
                        "estimated_analysis_time": {"type": "integer"},
                        "reason": {"type": "string"},
                        "quick_issues": {"type": "array", "items": {"type": "string"}},
                        "overall_impression": {"type": "string"},
                    },
                    "required": [
                        "endpoint_count",
                        "complexity_score",
                        "has_quality_issues",
                        "needs_detailed_analysis",
                        "estimated_analysis_time",
                        "reason",
                        "overall_impression",
                    ],
                }
            else:
                # 其他Schema使用原来的方法
                schema = response_schema.model_json_schema()
                # 移除Gemini不支持的字段
                schema.pop("$defs", None)
                schema.pop("$schema", None)
                schema.pop("additionalProperties", None)

            generation_config = GenerationConfig(
                temperature=kwargs.get("temperature", self.config.temperature),
                max_output_tokens=kwargs.get(
                    "max_output_tokens", self.config.max_output_tokens
                ),
                response_mime_type="application/json",
                response_schema=schema,
            )

            logger.info(
                f"Generating structured output with schema: {response_schema.__name__}"
            )
            logger.debug(f"Prompt length: {len(prompt)} characters")

            # 异步调用Gemini API
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=generation_config,
                ),
                timeout=self.config.timeout_seconds,
            )

            # 验证响应
            if not response or not response.text:
                raise LLMError("Gemini returned empty response")

            # 检查是否被安全过滤器阻止
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    if candidate.finish_reason == 3:  # SAFETY
                        raise LLMError("Response blocked by Gemini safety filter")
                    elif candidate.finish_reason == 4:  # RECITATION
                        raise LLMError("Response blocked by Gemini recitation filter")

            # 解析结构化响应
            response_data = json.loads(response.text)
            structured_response = response_schema(**response_data)

            logger.info("Structured output generated successfully")
            return structured_response

        except asyncio.TimeoutError:
            raise LLMError(
                f"Gemini API call timed out after {self.config.timeout_seconds} seconds"
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            logger.debug(f"Response text: {response.text[:500]}...")
            raise LLMError(f"Gemini返回的不是有效的JSON格式: {e}")

        except Exception as e:
            logger.error(f"Gemini structured generation failed: {e}")
            raise LLMError(f"Gemini结构化生成失败: {e}")

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """生成普通文本输出

        Args:
            prompt: 提示词
            **kwargs: 额外的生成配置

        Returns:
            生成的文本

        Raises:
            LLMError: 生成失败
        """
        if not self.model:
            raise LLMError("Gemini client not initialized")

        try:
            generation_config = GenerationConfig(
                temperature=kwargs.get("temperature", self.config.temperature),
                max_output_tokens=kwargs.get(
                    "max_output_tokens", self.config.max_output_tokens
                ),
            )

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=generation_config,
                ),
                timeout=self.config.timeout_seconds,
            )

            if not response or not response.text:
                raise LLMError("Gemini returned empty response")

            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini text generation failed: {e}")
            raise LLMError(f"Gemini文本生成失败: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查

        Returns:
            健康状态信息
        """
        status = {
            "available": False,
            "model_name": self.config.model_name,
            "timestamp": None,
        }

        try:
            # 简单的测试调用
            test_response = await self.generate_text(
                "Please respond with exactly: 'Health check OK'", max_output_tokens=50
            )

            status["available"] = "Health check OK" in test_response
            status["test_response"] = test_response

        except Exception as e:
            status["error"] = str(e)

        return status
