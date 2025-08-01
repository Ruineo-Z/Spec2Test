"""Gemini专用的简化Schema定义

为了兼容Gemini的JSON Schema限制，创建简化版本的Schema。
"""

from typing import List

from pydantic import BaseModel, Field


class GeminiQuickAssessmentSchema(BaseModel):
    """Gemini专用的快速评估Schema - 简化版本"""

    endpoint_count: int = Field(..., description="端点总数")
    complexity_score: float = Field(..., description="复杂度评分 (0.0-1.0)")
    has_quality_issues: bool = Field(..., description="是否发现明显质量问题")
    needs_detailed_analysis: bool = Field(..., description="是否需要详细分析")
    estimated_analysis_time: int = Field(..., description="预估详细分析时间（秒）")
    reason: str = Field(..., description="需要详细分析的具体原因")
    quick_issues: List[str] = Field(default_factory=list, description="快速发现的问题列表")
    overall_impression: str = Field(..., description="整体印象: excellent|good|fair|poor")

    class Config:
        # 简化配置，避免复杂的Schema生成
        extra = "forbid"
        use_enum_values = True
