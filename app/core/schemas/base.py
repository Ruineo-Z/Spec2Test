"""基础Schema定义

定义所有LLM输出Schema的基础类型和通用组件。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SchemaVersion(str, Enum):
    """Schema版本枚举"""

    V1_0 = "1.0"


class QualityLevel(str, Enum):
    """质量等级枚举"""

    EXCELLENT = "excellent"  # 优秀 (90-100分)
    GOOD = "good"  # 良好 (70-89分)
    FAIR = "fair"  # 一般 (50-69分)
    POOR = "poor"  # 较差 (0-49分)


class AnalysisType(str, Enum):
    """分析类型枚举"""

    QUICK = "quick"  # 快速评估
    DETAILED = "detailed"  # 详细分析
    BATCH = "batch"  # 分批分析


class SeverityLevel(str, Enum):
    """严重程度枚举"""

    HIGH = "high"  # 高严重性
    MEDIUM = "medium"  # 中等严重性
    LOW = "low"  # 低严重性


class IssueCategory(str, Enum):
    """问题类别枚举"""

    COMPLETENESS = "completeness"  # 完整性问题
    ACCURACY = "accuracy"  # 准确性问题
    READABILITY = "readability"  # 可读性问题
    TESTABILITY = "testability"  # 可测试性问题


class BaseSchema(BaseModel):
    """所有LLM输出Schema的基础类"""

    schema_version: SchemaVersion = Field(
        default=SchemaVersion.V1_0, description="Schema版本"
    )

    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="生成时间戳"
    )

    class Config:
        """Pydantic配置"""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class DimensionScore(BaseModel):
    """维度评分"""

    completeness: int = Field(..., ge=0, le=25, description="完整性评分 (0-25)")
    accuracy: int = Field(..., ge=0, le=25, description="准确性评分 (0-25)")
    readability: int = Field(..., ge=0, le=25, description="可读性评分 (0-25)")
    testability: int = Field(..., ge=0, le=25, description="可测试性评分 (0-25)")

    @property
    def total_score(self) -> int:
        """计算总分"""
        return self.completeness + self.accuracy + self.readability + self.testability


class StatisticsInfo(BaseModel):
    """统计信息"""

    total_endpoints: int = Field(..., ge=0, description="端点总数")
    endpoints_by_method: Dict[str, int] = Field(
        default_factory=dict, description="按HTTP方法统计的端点数"
    )
    endpoints_by_tag: Dict[str, int] = Field(
        default_factory=dict, description="按标签统计的端点数"
    )
    missing_descriptions: int = Field(default=0, ge=0, description="缺少描述的端点数")
    missing_examples: int = Field(default=0, ge=0, description="缺少示例的端点数")
    missing_schemas: int = Field(default=0, ge=0, description="缺少模式的端点数")


class TestingReadiness(BaseModel):
    """测试就绪性评估"""

    can_generate_basic_tests: bool = Field(..., description="能否生成基础测试")
    can_generate_edge_cases: bool = Field(..., description="能否生成边界测试")
    can_generate_error_tests: bool = Field(..., description="能否生成错误测试")
    missing_for_complete_testing: List[str] = Field(
        default_factory=list, description="完整测试所缺失的信息"
    )
    estimated_test_coverage: int = Field(..., ge=0, le=100, description="预估测试覆盖率百分比")
