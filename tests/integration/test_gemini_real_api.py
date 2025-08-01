"""Gemini真实API集成测试

使用真实的Gemini API测试结构化输出功能。
遵循TDD原则，使用真实数据进行测试。

注意：这些测试需要真实的Gemini API密钥，可能会产生费用。
"""

import asyncio
import os
from typing import Any, Dict

import pytest

from app.core.llm.gemini_client import GeminiClient, GeminiConfig
from app.core.schemas import QualityLevel, QuickAssessmentSchema
from app.utils.exceptions import LLMError

# 跳过集成测试，除非明确启用
pytestmark = pytest.mark.skipif(
    not os.getenv("ENABLE_GEMINI_INTEGRATION_TESTS"),
    reason="Gemini integration tests disabled. Set ENABLE_GEMINI_INTEGRATION_TESTS=1 to enable.",
)


@pytest.fixture
def real_gemini_config() -> GeminiConfig:
    """真实的Gemini配置"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY environment variable not set")

    return GeminiConfig(
        api_key=api_key,
        model_name="gemini-2.0-flash-exp",
        temperature=0.1,
        timeout_seconds=30,
    )


@pytest.fixture
def real_openapi_spec() -> Dict[str, Any]:
    """真实的OpenAPI文档示例"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "用户管理API",
            "version": "1.0.0",
            "description": "提供用户注册、登录、信息管理等功能",
        },
        "servers": [{"url": "https://api.example.com/v1", "description": "生产环境"}],
        "paths": {
            "/users": {
                "get": {
                    "summary": "获取用户列表",
                    "description": "分页获取系统中的用户列表，支持按角色筛选",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "description": "页码，从1开始",
                            "required": False,
                            "schema": {"type": "integer", "minimum": 1, "default": 1},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "每页数量，最大100",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 20,
                            },
                        },
                        {
                            "name": "role",
                            "in": "query",
                            "description": "按用户角色筛选",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "enum": ["admin", "user", "guest"],
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "成功返回用户列表",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "users": {
                                                "type": "array",
                                                "items": {
                                                    "$ref": "#/components/schemas/User"
                                                },
                                            },
                                            "total": {
                                                "type": "integer",
                                                "description": "总用户数",
                                            },
                                            "page": {
                                                "type": "integer",
                                                "description": "当前页码",
                                            },
                                            "limit": {
                                                "type": "integer",
                                                "description": "每页数量",
                                            },
                                        },
                                    },
                                    "example": {
                                        "users": [
                                            {
                                                "id": "123",
                                                "username": "john_doe",
                                                "email": "john@example.com",
                                                "role": "user",
                                                "created_at": "2024-01-01T00:00:00Z",
                                            }
                                        ],
                                        "total": 1,
                                        "page": 1,
                                        "limit": 20,
                                    },
                                }
                            },
                        },
                        "400": {
                            "description": "请求参数错误",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            },
                        },
                        "500": {"description": "服务器内部错误"},
                    },
                },
                "post": {
                    "summary": "创建新用户",
                    "description": "注册新用户账户",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "email", "password"],
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "minLength": 3,
                                            "maxLength": 50,
                                            "description": "用户名，3-50个字符",
                                        },
                                        "email": {
                                            "type": "string",
                                            "format": "email",
                                            "description": "邮箱地址",
                                        },
                                        "password": {
                                            "type": "string",
                                            "minLength": 8,
                                            "description": "密码，至少8个字符",
                                        },
                                        "role": {
                                            "type": "string",
                                            "enum": ["user", "admin"],
                                            "default": "user",
                                            "description": "用户角色",
                                        },
                                    },
                                },
                                "example": {
                                    "username": "new_user",
                                    "email": "newuser@example.com",
                                    "password": "securepassword123",
                                    "role": "user",
                                },
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "用户创建成功",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        },
                        "400": {"description": "请求数据无效"},
                        "409": {"description": "用户名或邮箱已存在"},
                    },
                },
            },
            "/users/{id}": {
                "get": {
                    "summary": "获取用户详情",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "用户ID",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功返回用户信息",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        },
                        "404": {"description": "用户不存在"},
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "用户唯一标识"},
                        "username": {"type": "string", "description": "用户名"},
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "邮箱",
                        },
                        "role": {
                            "type": "string",
                            "enum": ["admin", "user", "guest"],
                            "description": "用户角色",
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "创建时间",
                        },
                        "updated_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "更新时间",
                        },
                    },
                },
                "Error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "错误代码"},
                        "message": {"type": "string", "description": "错误信息"},
                        "details": {"type": "object", "description": "错误详情"},
                    },
                },
            }
        },
    }


class TestGeminiRealAPI:
    """真实Gemini API测试"""

    @pytest.mark.asyncio
    async def test_real_gemini_health_check(self, real_gemini_config):
        """测试真实Gemini API健康检查"""
        client = GeminiClient(real_gemini_config)

        status = await client.health_check()

        assert status["available"] is True
        assert status["model_name"] == "gemini-2.0-flash-exp"
        assert "Health check OK" in status["test_response"]
        print(f"✅ Gemini健康检查成功: {status}")

    @pytest.mark.asyncio
    async def test_real_structured_output_quick_assessment(
        self, real_gemini_config, real_openapi_spec
    ):
        """测试真实的结构化输出 - 快速评估"""
        client = GeminiClient(real_gemini_config)

        prompt = f"""
        请快速评估这个OpenAPI文档的质量。

        重点关注：
        1. 端点数量和复杂度
        2. 是否有明显的质量问题
        3. 是否需要详细分析
        4. 整体印象

        OpenAPI文档：
        {real_openapi_spec}
        """

        result = await client.generate_structured(
            prompt=prompt, response_schema=QuickAssessmentSchema
        )

        # 验证结果类型
        assert isinstance(result, QuickAssessmentSchema)

        # 验证基本字段
        assert result.endpoint_count > 0
        assert 0.0 <= result.complexity_score <= 1.0
        assert isinstance(result.has_quality_issues, bool)
        assert isinstance(result.needs_detailed_analysis, bool)
        assert result.estimated_analysis_time >= 0
        assert len(result.reason) > 0
        assert result.overall_impression in [
            QualityLevel.EXCELLENT,
            QualityLevel.GOOD,
            QualityLevel.FAIR,
            QualityLevel.POOR,
        ]

        # 打印结果用于验证
        print(f"✅ 快速评估结果:")
        print(f"   端点数量: {result.endpoint_count}")
        print(f"   复杂度评分: {result.complexity_score}")
        print(f"   有质量问题: {result.has_quality_issues}")
        print(f"   需要详细分析: {result.needs_detailed_analysis}")
        print(f"   预估分析时间: {result.estimated_analysis_time}秒")
        print(f"   整体印象: {result.overall_impression}")
        print(f"   原因: {result.reason}")
        if result.quick_issues:
            print(f"   快速发现的问题: {result.quick_issues}")

    @pytest.mark.asyncio
    async def test_real_structured_output_consistency(
        self, real_gemini_config, real_openapi_spec
    ):
        """测试结构化输出的一致性"""
        client = GeminiClient(real_gemini_config)

        prompt = f"""
        分析这个OpenAPI文档，给出质量评估。

        文档内容：{real_openapi_spec}
        """

        # 进行3次相同的分析
        results = []
        for i in range(3):
            result = await client.generate_structured(
                prompt=prompt, response_schema=QuickAssessmentSchema
            )
            results.append(result)

            # 避免API限流
            await asyncio.sleep(1)

        # 验证一致性（端点数量应该相同）
        endpoint_counts = [r.endpoint_count for r in results]
        assert len(set(endpoint_counts)) == 1, f"端点数量不一致: {endpoint_counts}"

        # 复杂度评分应该相近（差异不超过0.3）
        complexity_scores = [r.complexity_score for r in results]
        max_diff = max(complexity_scores) - min(complexity_scores)
        assert max_diff <= 0.3, f"复杂度评分差异过大: {complexity_scores}"

        print(f"✅ 一致性测试通过:")
        print(f"   端点数量: {endpoint_counts}")
        print(f"   复杂度评分: {complexity_scores}")
        print(f"   最大差异: {max_diff}")

    @pytest.mark.asyncio
    async def test_real_error_handling(self, real_gemini_config):
        """测试真实API的错误处理"""
        client = GeminiClient(real_gemini_config)

        # 测试无效的提示词（太短）
        with pytest.raises(LLMError):
            await client.generate_structured(
                prompt="", response_schema=QuickAssessmentSchema  # 空提示词
            )

        print("✅ 错误处理测试通过")


if __name__ == "__main__":
    # 运行集成测试的示例
    print("要运行Gemini集成测试，请设置环境变量：")
    print("export GEMINI_API_KEY=your_api_key")
    print("export ENABLE_GEMINI_INTEGRATION_TESTS=1")
    print("然后运行：pytest tests/integration/test_gemini_real_api.py -v")
