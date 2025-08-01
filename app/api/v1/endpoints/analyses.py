"""文档分析API端点

提供基于AI的文档质量分析功能。
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.db_models import AnalysisModel, DocumentModel
from app.core.llm.gemini_client import GeminiClient, GeminiConfig
from app.core.schemas.gemini_schemas import GeminiQuickAssessmentSchema
from app.utils.exceptions import LLMError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# 请求/响应模型 - 简化版本


class AnalysisDetails(BaseModel):
    """分析详情"""

    completeness: Dict[str, Any] = Field(default_factory=dict, description="完整性分析")
    testability: Dict[str, Any] = Field(default_factory=dict, description="可测试性分析")
    consistency: Dict[str, Any] = Field(default_factory=dict, description="一致性分析")


class AnalysisIssue(BaseModel):
    """分析问题"""

    id: str = Field(..., description="问题ID")
    type: str = Field(..., description="问题类型")
    severity: str = Field(..., description="严重程度")
    endpoint: str = Field(..., description="相关端点")
    message: str = Field(..., description="问题描述")
    suggestion: str = Field(..., description="改进建议")


class AnalysisRecommendation(BaseModel):
    """分析建议"""

    priority: str = Field(..., description="优先级")
    category: str = Field(..., description="类别")
    action: str = Field(..., description="建议操作")
    impact: str = Field(..., description="影响描述")


class AnalysisResult(BaseModel):
    """分析结果"""

    quality_score: int = Field(..., description="质量评分")
    quality_level: str = Field(..., description="质量等级")
    analysis_details: AnalysisDetails = Field(..., description="分析详情")
    issues: List[AnalysisIssue] = Field(default_factory=list, description="问题列表")
    recommendations: List[AnalysisRecommendation] = Field(
        default_factory=list, description="建议列表"
    )


class NextStep(BaseModel):
    """下一步操作建议"""

    action: str = Field(..., description="建议操作")
    endpoint: str = Field(..., description="API端点")
    recommended_options: Dict[str, Any] = Field(
        default_factory=dict, description="推荐选项"
    )


class AnalyzeDocumentResponse(BaseModel):
    """文档分析响应"""

    success: bool = Field(..., description="是否成功")
    analysis_id: str = Field(..., description="分析ID")
    document_id: str = Field(..., description="文档ID")
    analysis: AnalysisResult = Field(..., description="分析结果")
    analysis_time: float = Field(..., description="分析耗时")
    next_step: NextStep = Field(..., description="下一步建议")


class AnalysisDetailResponse(BaseModel):
    """分析详情响应"""

    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    status: str = Field(..., description="分析状态")
    created_at: str = Field(..., description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    document_id: str = Field(..., description="源文档ID")
    quality_score: float = Field(..., description="质量评分")
    analysis_time: float = Field(..., description="分析耗时")
    related_resources: Dict[str, List[str]] = Field(
        default_factory=dict, description="关联资源"
    )


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


@router.post("/{document_id}/analyze", response_model=AnalyzeDocumentResponse)
async def analyze_document(
    document_id: str,
    db: AsyncSession = Depends(get_async_db),
    client: GeminiClient = Depends(get_gemini_client),
) -> AnalyzeDocumentResponse:
    """分析OpenAPI文档质量

    Args:
        document_id: 文档ID

    Returns:
        分析结果

    Raises:
        HTTPException: 文档不存在或分析失败
    """
    start_time = datetime.now()
    logger.info(f"Starting document analysis: {document_id}")

    try:
        # 解析文档ID并查询文档
        hex_id = document_id.replace("doc_", "")
        db_id = int(hex_id, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的文档ID格式")

    # 查询文档
    result = await db.execute(select(DocumentModel).where(DocumentModel.id == db_id))
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 获取文档内容
    analysis_result = document.analysis_result or {}
    openapi_content = analysis_result.get("content", "")

    if not openapi_content:
        raise HTTPException(status_code=400, detail="文档内容为空")

    try:
        # 构建简化的分析提示词
        prompt = f"""
        请分析这个OpenAPI文档的质量，重点评估：

        1. 完整性：描述、参数、响应是否完整
        2. 准确性：类型定义、状态码是否正确
        3. 可读性：描述是否清晰易懂
        4. 可测试性：是否有足够信息生成测试用例

        请特别注意：
        - 端点数量和复杂度评估
        - 缺失的描述、示例和Schema定义
        - 是否需要进一步详细分析
        - 对测试用例生成的影响

        OpenAPI文档：
        {openapi_content}
        """

        # 执行AI分析
        logger.info("Calling Gemini API for document analysis")
        gemini_result = await client.generate_structured(
            prompt=prompt, response_schema=GeminiQuickAssessmentSchema
        )

        # 计算分析耗时
        end_time = datetime.now()
        analysis_time = (end_time - start_time).total_seconds()

        # 转换Gemini结果为API响应格式
        quality_score = int(gemini_result.complexity_score * 100)

        # 创建分析记录
        analysis = AnalysisModel(
            document_id=db_id,
            analysis_type="quick",  # 默认使用快速分析
            quality_score=float(quality_score),
            analysis_result={
                "gemini_result": gemini_result.model_dump(),
                "analysis_time": analysis_time,
                "analyzed_at": datetime.now().isoformat(),
            },
            status="completed",
        )

        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)

        analysis_id = f"analysis_{analysis.id:08x}"

        # 构建响应
        response = AnalyzeDocumentResponse(
            success=True,
            analysis_id=analysis_id,
            document_id=document_id,
            analysis=AnalysisResult(
                quality_score=quality_score,
                quality_level=gemini_result.overall_impression,
                analysis_details=AnalysisDetails(
                    completeness={
                        "score": 85,
                        "missing_descriptions": len(
                            [
                                issue
                                for issue in gemini_result.quick_issues
                                if "描述" in issue
                            ]
                        ),
                        "missing_examples": len(
                            [
                                issue
                                for issue in gemini_result.quick_issues
                                if "示例" in issue
                            ]
                        ),
                        "missing_schemas": len(
                            [
                                issue
                                for issue in gemini_result.quick_issues
                                if "Schema" in issue
                            ]
                        ),
                    },
                    testability={
                        "score": quality_score,
                        "testable_endpoints": gemini_result.endpoint_count,
                        "complex_endpoints": max(0, gemini_result.endpoint_count - 10),
                        "estimated_test_coverage": min(100, quality_score + 10),
                    },
                    consistency={
                        "score": quality_score,
                        "naming_consistency": quality_score,
                        "response_format_consistency": quality_score,
                    },
                ),
                issues=[
                    AnalysisIssue(
                        id=f"issue_{i:03d}",
                        type="quality_issue",
                        severity="medium",
                        endpoint="multiple",
                        message=issue,
                        suggestion=f"建议解决：{issue}",
                    )
                    for i, issue in enumerate(gemini_result.quick_issues, 1)
                ],
                recommendations=[
                    AnalysisRecommendation(
                        priority="high",
                        category="testability",
                        action="改进文档质量",
                        impact="提高测试用例生成质量",
                    )
                ],
            ),
            analysis_time=analysis_time,
            next_step=NextStep(
                action="generate_test_cases",
                endpoint="/api/v1/test-cases/generate",
                recommended_options={
                    "test_types": ["normal", "edge"]
                    if quality_score > 70
                    else ["normal"],
                    "max_cases_per_endpoint": 5 if quality_score > 80 else 3,
                },
            ),
        )

        logger.info(
            f"Document analysis completed: {analysis_id}, score: {quality_score}"
        )
        return response

    except LLMError as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=503, detail=f"AI分析服务暂时不可用: {str(e)}")
    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"文档分析失败: {str(e)}")


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis_detail(
    analysis_id: str,
    db: AsyncSession = Depends(get_async_db),
) -> AnalysisDetailResponse:
    """获取分析详细信息

    Args:
        analysis_id: 分析ID

    Returns:
        分析详细信息

    Raises:
        HTTPException: 分析不存在
    """
    logger.info(f"Getting analysis detail: {analysis_id}")

    try:
        # 解析分析ID
        hex_id = analysis_id.replace("analysis_", "")
        db_id = int(hex_id, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的分析ID格式")

    # 查询分析记录
    result = await db.execute(select(AnalysisModel).where(AnalysisModel.id == db_id))
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    # 构建响应
    analysis_result = analysis.analysis_result or {}

    response = AnalysisDetailResponse(
        resource_type="analysis",
        resource_id=analysis_id,
        status=analysis.status,
        created_at=analysis.created_at.isoformat() if analysis.created_at else "",
        completed_at=analysis_result.get("analyzed_at"),
        document_id=f"doc_{analysis.document_id:08x}",
        quality_score=analysis.quality_score or 0.0,
        analysis_time=analysis_result.get("analysis_time", 0.0),
        related_resources={"test_cases": [], "test_code": []},
    )

    logger.info(f"Analysis detail retrieved: {analysis_id}")
    return response


@router.get("")
async def list_analyses(
    document_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
) -> Dict[str, Any]:
    """获取分析列表

    Args:
        document_id: 可选的文档ID过滤

    Returns:
        分析列表
    """
    logger.info(f"Listing analyses, document_id: {document_id}")

    # 构建查询
    query = select(AnalysisModel)
    if document_id:
        try:
            hex_id = document_id.replace("doc_", "")
            db_id = int(hex_id, 16)
            query = query.where(AnalysisModel.document_id == db_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的文档ID格式")

    # 执行查询
    result = await db.execute(query)
    analyses = result.scalars().all()

    analysis_list = []
    for analysis in analyses:
        analysis_result = analysis.analysis_result or {}
        analysis_list.append(
            {
                "id": f"analysis_{analysis.id:08x}",
                "document_id": f"doc_{analysis.document_id:08x}",
                "analysis_type": analysis.analysis_type,
                "quality_score": analysis.quality_score,
                "status": analysis.status,
                "created_at": analysis.created_at.isoformat()
                if analysis.created_at
                else None,
                "analysis_time": analysis_result.get("analysis_time", 0),
            }
        )

    logger.info(f"Found {len(analysis_list)} analyses")

    return {
        "analyses": analysis_list,
        "total": len(analysis_list),
    }
