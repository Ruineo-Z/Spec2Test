"""核心数据模型

定义自动化测试流水线的核心数据结构。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class RiskLevel(str, Enum):
    """风险等级"""

    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


class RiskCategory(str, Enum):
    """风险类别"""

    SECURITY = "security"  # 安全风险
    COMPATIBILITY = "compatibility"  # 兼容性风险
    PERFORMANCE = "performance"  # 性能风险
    MAINTAINABILITY = "maintainability"  # 可维护性风险
    USABILITY = "usability"  # 可用性风险
    RELIABILITY = "reliability"  # 可靠性风险


class TestCaseType(str, Enum):
    """测试用例类型"""

    NORMAL = "normal"  # 正常流程测试
    ERROR = "error"  # 错误处理测试
    EDGE = "edge"  # 边界条件测试
    SECURITY = "security"  # 安全测试


class HttpMethod(str, Enum):
    """HTTP方法"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class TestStatus(str, Enum):
    """测试状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    PASSED = "passed"  # 通过
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过
    ERROR = "error"  # 错误


class DocumentQuality(str, Enum):
    """文档质量等级"""

    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    FAIR = "fair"  # 一般
    POOR = "poor"  # 较差


class APIEndpoint(BaseModel):
    """API端点信息"""

    path: str = Field(..., description="API路径")
    method: HttpMethod = Field(..., description="HTTP方法")
    summary: Optional[str] = Field(None, description="端点摘要")
    description: Optional[str] = Field(None, description="详细描述")
    tags: List[str] = Field(default_factory=list, description="标签")

    # 参数信息
    path_parameters: Dict[str, Any] = Field(default_factory=dict, description="路径参数")
    query_parameters: Dict[str, Any] = Field(default_factory=dict, description="查询参数")
    header_parameters: Dict[str, Any] = Field(default_factory=dict, description="请求头参数")

    # 请求体
    request_body: Optional[Dict[str, Any]] = Field(None, description="请求体结构")
    request_examples: List[Dict[str, Any]] = Field(
        default_factory=list, description="请求示例"
    )

    # 响应信息
    responses: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="响应定义"
    )
    response_examples: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict, description="响应示例"
    )

    # 安全信息
    security: List[Dict[str, Any]] = Field(default_factory=list, description="安全要求")

    # 元数据
    deprecated: bool = Field(False, description="是否已废弃")
    operation_id: Optional[str] = Field(None, description="操作ID")

    class Config:
        json_encoders = {HttpMethod: lambda v: v.value}


class TestCase(BaseModel):
    """测试用例"""

    id: str = Field(..., description="测试用例ID")
    name: str = Field(..., description="测试用例名称")
    description: Optional[str] = Field(None, description="测试描述")
    type: TestCaseType = Field(..., description="测试类型")

    # 关联的API端点
    endpoint: APIEndpoint = Field(..., description="关联的API端点")

    # 测试数据
    test_data: Dict[str, Any] = Field(default_factory=dict, description="测试数据")
    expected_status_code: int = Field(200, description="期望状态码")
    expected_response: Optional[Dict[str, Any]] = Field(None, description="期望响应")

    # 前置和后置条件
    preconditions: List[str] = Field(default_factory=list, description="前置条件")
    postconditions: List[str] = Field(default_factory=list, description="后置条件")

    # 测试步骤
    test_steps: List[Dict[str, Any]] = Field(default_factory=list, description="测试步骤")

    # 元数据
    priority: int = Field(1, description="优先级（1-5）")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("优先级必须在1-5之间")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            TestCaseType: lambda v: v.value,
        }


class TestResult(BaseModel):
    """测试结果"""

    test_case_id: str = Field(..., description="测试用例ID")
    status: TestStatus = Field(..., description="测试状态")

    # 执行信息
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="执行时长（秒）")

    # 结果详情
    actual_status_code: Optional[int] = Field(None, description="实际状态码")
    actual_response: Optional[Dict[str, Any]] = Field(None, description="实际响应")

    # 错误信息
    error_message: Optional[str] = Field(None, description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")

    # 断言结果
    assertions: List[Dict[str, Any]] = Field(default_factory=list, description="断言结果")

    # 性能指标
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    memory_usage: Optional[float] = Field(None, description="内存使用（MB）")

    # 截图和日志
    screenshots: List[str] = Field(default_factory=list, description="截图路径")
    logs: List[str] = Field(default_factory=list, description="日志信息")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            TestStatus: lambda v: v.value,
        }


class RiskItem(BaseModel):
    """风险项"""

    id: str = Field(..., description="风险ID")
    title: str = Field(..., description="风险标题")
    description: str = Field(..., description="风险描述")
    category: RiskCategory = Field(..., description="风险类别")
    level: RiskLevel = Field(..., description="风险等级")
    impact: str = Field(..., description="潜在影响")
    recommendation: str = Field(..., description="建议措施")
    affected_endpoints: List[str] = Field(default_factory=list, description="受影响的端点")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class DocumentAnalysis(BaseModel):
    """文档分析结果"""

    document_path: str = Field(..., description="文档路径")
    document_type: str = Field(..., description="文档类型")

    # 质量评估
    quality_score: float = Field(..., description="质量评分（0-100）")
    quality_level: DocumentQuality = Field(..., description="质量等级")

    # 完整性分析
    total_endpoints: int = Field(0, description="总端点数")
    documented_endpoints: int = Field(0, description="已文档化端点数")
    missing_descriptions: int = Field(0, description="缺少描述的端点数")
    missing_examples: int = Field(0, description="缺少示例的端点数")
    missing_schemas: int = Field(0, description="缺少模式的端点数")

    # 详细问题
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")

    # 风险评估
    risks: List[RiskItem] = Field(default_factory=list, description="识别的风险")
    risk_summary: Dict[str, int] = Field(default_factory=dict, description="风险统计")
    overall_risk_level: RiskLevel = Field(RiskLevel.LOW, description="整体风险等级")

    # 统计信息
    endpoints_by_method: Dict[str, int] = Field(
        default_factory=dict, description="按方法统计端点"
    )
    endpoints_by_tag: Dict[str, int] = Field(
        default_factory=dict, description="按标签统计端点"
    )

    # 分析时间
    analyzed_at: datetime = Field(default_factory=datetime.now, description="分析时间")

    @field_validator("quality_score")
    @classmethod
    def validate_quality_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("质量评分必须在0-100之间")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            DocumentQuality: lambda v: v.value,
        }


class TestSuite(BaseModel):
    """测试套件"""

    id: str = Field(..., description="测试套件ID")
    name: str = Field(..., description="测试套件名称")
    description: Optional[str] = Field(None, description="套件描述")

    # 测试用例
    test_cases: List[TestCase] = Field(default_factory=list, description="测试用例列表")

    # 配置信息
    base_url: Optional[str] = Field(None, description="基础URL")
    environment: str = Field("test", description="测试环境")
    timeout: int = Field(30, description="超时时间（秒）")

    # 执行配置
    parallel_execution: bool = Field(False, description="是否并行执行")
    max_workers: int = Field(4, description="最大工作线程数")
    retry_count: int = Field(0, description="重试次数")

    # 元数据
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 关联的文档分析
    document_analysis: Optional[DocumentAnalysis] = Field(None, description="文档分析结果")

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("超时时间必须大于0")
        return v

    @field_validator("max_workers")
    @classmethod
    def validate_max_workers(cls, v):
        if v <= 0:
            raise ValueError("最大工作线程数必须大于0")
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TestReport(BaseModel):
    """测试报告"""

    id: str = Field(..., description="报告ID")
    test_suite_id: str = Field(..., description="测试套件ID")
    name: str = Field(..., description="报告名称")

    # 执行信息
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[float] = Field(None, description="总执行时长（秒）")

    # 测试结果
    test_results: List[TestResult] = Field(default_factory=list, description="测试结果列表")

    # 统计信息
    total_tests: int = Field(0, description="总测试数")
    passed_tests: int = Field(0, description="通过测试数")
    failed_tests: int = Field(0, description="失败测试数")
    skipped_tests: int = Field(0, description="跳过测试数")
    error_tests: int = Field(0, description="错误测试数")

    # 成功率
    success_rate: float = Field(0.0, description="成功率（0-100）")

    # 性能统计
    avg_response_time: Optional[float] = Field(None, description="平均响应时间（毫秒）")
    max_response_time: Optional[float] = Field(None, description="最大响应时间（毫秒）")
    min_response_time: Optional[float] = Field(None, description="最小响应时间（毫秒）")

    # 环境信息
    environment: str = Field("test", description="测试环境")
    base_url: Optional[str] = Field(None, description="基础URL")

    # 报告文件
    html_report_path: Optional[str] = Field(None, description="HTML报告路径")
    json_report_path: Optional[str] = Field(None, description="JSON报告路径")
    xml_report_path: Optional[str] = Field(None, description="XML报告路径")

    # 元数据
    tags: List[str] = Field(default_factory=list, description="标签")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")

    @field_validator("success_rate")
    @classmethod
    def validate_success_rate(cls, v):
        if not 0 <= v <= 100:
            raise ValueError("成功率必须在0-100之间")
        return v

    def calculate_statistics(self):
        """计算统计信息"""
        self.total_tests = len(self.test_results)

        status_counts = {}
        for result in self.test_results:
            status = result.status
            status_counts[status] = status_counts.get(status, 0) + 1

        self.passed_tests = status_counts.get(TestStatus.PASSED, 0)
        self.failed_tests = status_counts.get(TestStatus.FAILED, 0)
        self.skipped_tests = status_counts.get(TestStatus.SKIPPED, 0)
        self.error_tests = status_counts.get(TestStatus.ERROR, 0)

        # 计算成功率
        if self.total_tests > 0:
            self.success_rate = (self.passed_tests / self.total_tests) * 100
        else:
            self.success_rate = 0.0

        # 计算响应时间统计
        response_times = [
            r.response_time for r in self.test_results if r.response_time is not None
        ]
        if response_times:
            self.avg_response_time = sum(response_times) / len(response_times)
            self.max_response_time = max(response_times)
            self.min_response_time = min(response_times)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# 导出所有模型
__all__ = [
    "TestCaseType",
    "HttpMethod",
    "TestStatus",
    "DocumentQuality",
    "APIEndpoint",
    "TestCase",
    "TestResult",
    "DocumentAnalysis",
    "TestSuite",
    "TestReport",
]
