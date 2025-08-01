"""文档分析相关Schema定义

定义文档质量分析的所有输出结构。
"""

from typing import Dict, List, Optional

from pydantic import Field

from .base import (
    AnalysisType,
    BaseSchema,
    DimensionScore,
    IssueCategory,
    QualityLevel,
    SeverityLevel,
    StatisticsInfo,
    TestingReadiness,
)


class IssueSchema(BaseSchema):
    """问题描述Schema"""

    category: IssueCategory = Field(..., description="问题类别")
    severity: SeverityLevel = Field(..., description="严重程度")
    title: str = Field(..., min_length=1, description="问题标题")
    description: str = Field(..., min_length=1, description="问题详细描述")
    affected_endpoints: List[str] = Field(
        default_factory=list, description="受影响的端点路径列表"
    )
    impact_on_testing: str = Field(..., description="对测试用例生成的影响")


class SuggestionSchema(BaseSchema):
    """改进建议Schema"""

    action: str = Field(..., min_length=1, description="具体改进行动")
    priority: SeverityLevel = Field(..., description="优先级")
    effort: str = Field(..., description="实施难度 (easy|medium|hard)")
    impact: str = Field(..., description="对测试质量的影响描述")
    example: Optional[str] = Field(None, description="改进示例")


class QuickAssessmentSchema(BaseSchema):
    """快速评估结果Schema"""

    endpoint_count: int = Field(..., ge=0, description="端点总数")
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="复杂度评分 (0.0-1.0)")
    has_quality_issues: bool = Field(..., description="是否发现明显质量问题")
    needs_detailed_analysis: bool = Field(..., description="是否需要详细分析")
    estimated_analysis_time: int = Field(..., ge=0, description="预估详细分析时间（秒）")
    reason: str = Field(..., description="需要详细分析的具体原因")
    quick_issues: List[str] = Field(default_factory=list, description="快速发现的问题列表")
    overall_impression: QualityLevel = Field(..., description="整体印象")


class DetailedAnalysisSchema(BaseSchema):
    """详细分析结果Schema"""

    overall_score: int = Field(..., ge=0, le=100, description="总体质量评分")
    quality_level: QualityLevel = Field(..., description="质量等级")
    dimension_scores: DimensionScore = Field(..., description="各维度详细评分")

    # 详细问题分析
    detailed_issues: List[IssueSchema] = Field(
        default_factory=list, description="详细问题列表"
    )

    # 测试就绪性评估
    testing_readiness: TestingReadiness = Field(..., description="测试就绪性评估")

    # 改进建议
    improvement_suggestions: List[SuggestionSchema] = Field(
        default_factory=list, description="优先级排序的改进建议"
    )

    # 统计信息
    statistics: StatisticsInfo = Field(..., description="详细统计信息")


class DocumentAnalysisSchema(BaseSchema):
    """完整文档分析结果Schema（智能分层分析的最终输出）"""

    # 基本信息
    document_path: str = Field(..., description="文档路径")
    document_type: str = Field(default="openapi", description="文档类型")
    analysis_method: AnalysisType = Field(..., description="使用的分析方法")

    # 快速评估结果（总是包含）
    quick_assessment: QuickAssessmentSchema = Field(..., description="快速评估结果")

    # 详细分析结果（可选，取决于是否进行了详细分析）
    detailed_analysis: Optional[DetailedAnalysisSchema] = Field(
        None, description="详细分析结果（仅在进行详细分析时包含）"
    )

    # 最终综合结果
    final_score: int = Field(..., ge=0, le=100, description="最终综合评分")
    final_quality_level: QualityLevel = Field(..., description="最终质量等级")

    # 分析元数据
    analysis_time_seconds: float = Field(..., ge=0, description="分析耗时（秒）")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token使用统计")

    @property
    def has_detailed_analysis(self) -> bool:
        """是否包含详细分析"""
        return self.detailed_analysis is not None

    @property
    def primary_issues(self) -> List[IssueSchema]:
        """获取主要问题（优先显示详细分析的问题）"""
        if self.detailed_analysis:
            return self.detailed_analysis.detailed_issues
        return []

    @property
    def primary_suggestions(self) -> List[SuggestionSchema]:
        """获取主要建议（优先显示详细分析的建议）"""
        if self.detailed_analysis:
            return self.detailed_analysis.improvement_suggestions
        return []
