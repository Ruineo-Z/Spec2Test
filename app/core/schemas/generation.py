"""测试用例生成相关Schema定义

定义测试用例生成的所有输出结构。
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from .base import BaseSchema, SeverityLevel


class AssertionSchema(BaseSchema):
    """断言Schema"""

    type: str = Field(
        ..., description="断言类型 (status_code|response_time|json_schema|custom)"
    )
    description: str = Field(..., min_length=1, description="断言描述")
    expected_value: Any = Field(..., description="期望值")
    operator: str = Field(
        default="equals", description="比较操作符 (equals|greater_than|less_than|contains)"
    )


class TestStepSchema(BaseSchema):
    """测试步骤Schema"""

    step_number: int = Field(..., ge=1, description="步骤序号")
    action: str = Field(..., min_length=1, description="执行动作")
    description: str = Field(..., min_length=1, description="步骤描述")
    expected_result: Optional[str] = Field(None, description="预期结果")


class CaseSchema(BaseSchema):
    """单个测试用例Schema"""

    name: str = Field(..., min_length=1, max_length=200, description="测试用例名称")
    description: str = Field(..., min_length=1, description="测试用例详细描述")

    # 测试数据
    request_data: Dict[str, Any] = Field(
        default_factory=dict, description="请求数据（包括路径参数、查询参数、请求体）"
    )

    # 期望结果
    expected_status_code: int = Field(
        default=200, ge=100, le=599, description="期望的HTTP状态码"
    )
    expected_response: Dict[str, Any] = Field(
        default_factory=dict, description="期望的响应数据结构"
    )

    # 测试步骤和断言
    test_steps: List[TestStepSchema] = Field(default_factory=list, description="详细测试步骤")
    assertions: List[AssertionSchema] = Field(default_factory=list, description="断言列表")

    # 前置和后置条件
    preconditions: List[str] = Field(default_factory=list, description="前置条件")
    postconditions: List[str] = Field(default_factory=list, description="后置条件")

    # 元数据
    priority: int = Field(default=3, ge=1, le=5, description="优先级 (1=最高, 5=最低)")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    estimated_execution_time: Optional[int] = Field(None, ge=0, description="预估执行时间（秒）")

    # 测试类型特定信息
    test_scenario: str = Field(..., description="测试场景类型 (normal|error|edge|security)")
    risk_level: SeverityLevel = Field(default=SeverityLevel.MEDIUM, description="风险等级")


class GenerationResultSchema(BaseSchema):
    """测试用例生成结果Schema"""

    test_cases: List[CaseSchema] = Field(..., min_length=1, description="生成的测试用例列表")

    # 生成统计
    generation_summary: Dict[str, Any] = Field(
        default_factory=dict, description="生成统计信息"
    )

    # 质量评估
    overall_quality_score: float = Field(..., ge=0.0, le=100.0, description="整体质量评分")

    # 覆盖率分析
    coverage_analysis: Dict[str, Any] = Field(
        default_factory=dict, description="测试覆盖率分析"
    )

    # 建议和警告
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


class BatchResultSchema(BaseSchema):
    """批量生成结果Schema（用于多个端点的测试用例生成）"""

    endpoint_results: Dict[str, GenerationResultSchema] = Field(
        ..., description="按端点路径组织的生成结果"
    )

    # 整体统计
    total_test_cases: int = Field(..., ge=0, description="总测试用例数")
    total_endpoints: int = Field(..., ge=0, description="总端点数")
    average_quality_score: float = Field(..., ge=0.0, le=100.0, description="平均质量评分")

    # 整体分析
    overall_coverage: Dict[str, float] = Field(
        default_factory=dict, description="整体覆盖率分析"
    )
    global_recommendations: List[str] = Field(
        default_factory=list, description="全局改进建议"
    )

    # 生成元数据
    generation_time_seconds: float = Field(..., ge=0, description="总生成时间（秒）")
    failed_endpoints: List[str] = Field(default_factory=list, description="生成失败的端点列表")
