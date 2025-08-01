"""AI文档分析API端点

提供基于Gemini的智能文档质量分析功能。
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.llm.gemini_client import GeminiClient, GeminiConfig
from app.core.schemas import DocumentAnalysisSchema, QuickAssessmentSchema
from app.utils.exceptions import LLMError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# 请求/响应模型
class AnalyzeDocumentRequest(BaseModel):
    """文档分析请求模型"""

    openapi_spec: Dict[str, Any] = Field(..., description="OpenAPI文档内容")
    analysis_type: str = Field(default="quick", description="分析类型: quick|detailed")
    custom_requirements: Optional[str] = Field(None, description="自定义分析要求")


class AnalyzeDocumentResponse(BaseModel):
    """文档分析响应模型"""

    success: bool = Field(..., description="分析是否成功")
    analysis_type: str = Field(..., description="实际使用的分析类型")
    analysis_time_seconds: float = Field(..., description="分析耗时（秒）")

    # 快速评估结果
    endpoint_count: int = Field(..., description="端点总数")
    complexity_score: float = Field(..., description="复杂度评分(0-1)")
    has_quality_issues: bool = Field(..., description="是否有质量问题")
    needs_detailed_analysis: bool = Field(..., description="是否需要详细分析")
    overall_impression: str = Field(..., description="整体印象")
    quick_issues: list = Field(default_factory=list, description="快速发现的问题")

    # 详细分析结果（可选）
    detailed_analysis: Optional[Dict[str, Any]] = Field(None, description="详细分析结果")

    # 元数据
    gemini_model: str = Field(..., description="使用的Gemini模型")
    analysis_timestamp: str = Field(..., description="分析时间戳")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""

    gemini_available: bool = Field(..., description="Gemini API是否可用")
    model_name: str = Field(..., description="模型名称")
    test_response: Optional[str] = Field(None, description="测试响应")
    error: Optional[str] = Field(None, description="错误信息")


# 依赖函数
def get_gemini_client() -> GeminiClient:
    """获取Gemini客户端"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503, detail="Gemini API密钥未配置。请设置GEMINI_API_KEY环境变量。"
        )

    config = GeminiConfig(
        api_key=api_key,
        model_name="gemini-2.0-flash-exp",
        temperature=0.1,
        timeout_seconds=30,
    )

    return GeminiClient(config)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """检查Gemini AI分析服务健康状态

    Returns:
        服务健康状态信息
    """
    logger.info("Checking Gemini AI service health")

    try:
        client = get_gemini_client()
        status = await client.health_check()

        return HealthCheckResponse(
            gemini_available=status["available"],
            model_name=status["model_name"],
            test_response=status.get("test_response"),
            error=status.get("error"),
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            gemini_available=False, model_name="unknown", error=str(e)
        )


@router.post("/analyze", response_model=AnalyzeDocumentResponse)
async def analyze_document_with_ai(
    request: AnalyzeDocumentRequest, client: GeminiClient = Depends(get_gemini_client)
) -> AnalyzeDocumentResponse:
    """使用AI分析OpenAPI文档质量

    Args:
        request: 分析请求，包含OpenAPI文档内容

    Returns:
        AI分析结果

    Raises:
        HTTPException: 分析失败或API不可用
    """
    start_time = datetime.now()
    logger.info(f"Starting AI document analysis, type: {request.analysis_type}")

    try:
        # 构建分析提示词
        prompt = f"""
        请分析这个OpenAPI文档的质量，重点评估：

        1. 完整性：描述、参数、响应是否完整
        2. 准确性：类型定义、状态码是否正确
        3. 可读性：描述是否清晰易懂
        4. 可测试性：是否有足够信息生成测试用例

        请特别关注：
        - 端点数量和复杂度评估
        - 缺失的描述、示例和Schema定义
        - 是否需要进一步详细分析
        - 对测试用例生成的影响

        {f"自定义要求：{request.custom_requirements}" if request.custom_requirements else ""}

        OpenAPI文档：
        {json.dumps(request.openapi_spec, ensure_ascii=False, indent=2)}
        """

        # 执行AI分析
        logger.info("Calling Gemini API for document analysis")
        result = await client.generate_structured(
            prompt=prompt, response_schema=QuickAssessmentSchema
        )

        # 计算分析耗时
        end_time = datetime.now()
        analysis_time = (end_time - start_time).total_seconds()

        logger.info(f"AI analysis completed in {analysis_time:.2f} seconds")

        # 构建响应
        response = AnalyzeDocumentResponse(
            success=True,
            analysis_type="quick",  # 目前只支持快速分析
            analysis_time_seconds=analysis_time,
            endpoint_count=result.endpoint_count,
            complexity_score=result.complexity_score,
            has_quality_issues=result.has_quality_issues,
            needs_detailed_analysis=result.needs_detailed_analysis,
            overall_impression=result.overall_impression,
            quick_issues=result.quick_issues,
            gemini_model="gemini-2.0-flash-exp",
            analysis_timestamp=result.generated_at,
        )

        logger.info(
            f"Document analysis successful: score={result.complexity_score:.2f}, issues={len(result.quick_issues)}"
        )
        return response

    except LLMError as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=503, detail=f"AI分析服务暂时不可用: {str(e)}")
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"文档分析失败: {str(e)}")


@router.post("/analyze-file", response_model=AnalyzeDocumentResponse)
async def analyze_uploaded_file(
    file: UploadFile = File(..., description="OpenAPI文档文件(JSON/YAML)"),
    analysis_type: str = "quick",
    custom_requirements: Optional[str] = None,
    client: GeminiClient = Depends(get_gemini_client),
) -> AnalyzeDocumentResponse:
    """上传文件并进行AI分析

    Args:
        file: OpenAPI文档文件
        analysis_type: 分析类型
        custom_requirements: 自定义分析要求

    Returns:
        AI分析结果

    Raises:
        HTTPException: 文件格式错误或分析失败
    """
    logger.info(f"Analyzing uploaded file: {file.filename}")

    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["json", "yaml", "yml"]:
        raise HTTPException(
            status_code=400, detail=f"不支持的文件类型: {file_ext}。支持的类型: json, yaml, yml"
        )

    try:
        # 读取文件内容
        content = await file.read()
        content_str = content.decode("utf-8")

        # 解析文件内容
        if file_ext == "json":
            openapi_spec = json.loads(content_str)
        else:  # yaml/yml
            import yaml

            openapi_spec = yaml.safe_load(content_str)

        # 验证是否为有效的OpenAPI文档
        if not isinstance(openapi_spec, dict) or "openapi" not in openapi_spec:
            raise HTTPException(status_code=400, detail="无效的OpenAPI文档格式，缺少'openapi'字段")

        # 创建分析请求
        request = AnalyzeDocumentRequest(
            openapi_spec=openapi_spec,
            analysis_type=analysis_type,
            custom_requirements=custom_requirements,
        )

        # 执行分析
        return await analyze_document_with_ai(request, client)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON格式错误: {str(e)}")
    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"文件分析失败: {str(e)}")


@router.get("/demo-spec")
async def get_demo_openapi_spec() -> Dict[str, Any]:
    """获取演示用的OpenAPI文档

    Returns:
        示例OpenAPI文档，可用于测试分析功能
    """
    logger.info("Providing demo OpenAPI specification")

    demo_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "用户管理API",
            "version": "1.0.0",
            "description": "提供用户注册、登录、信息管理等功能的演示API",
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
                                            "total": {"type": "integer"},
                                        },
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "创建新用户",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["username", "email"],
                                    "properties": {
                                        "username": {"type": "string", "minLength": 3},
                                        "email": {"type": "string", "format": "email"},
                                    },
                                }
                            }
                        },
                    },
                    "responses": {
                        "201": {"description": "用户创建成功"},
                        "400": {"description": "请求数据无效"},
                    },
                },
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "username": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                }
            }
        },
    }

    return {
        "message": "演示OpenAPI文档",
        "spec": demo_spec,
        "usage": "可以将此文档复制到 /api/v1/analyzer/analyze 接口进行测试",
    }
