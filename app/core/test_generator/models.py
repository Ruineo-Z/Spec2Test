"""
测试生成器数据模型

定义测试用例生成过程中使用的数据结构和模型。
"""

import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


def _get_concurrent_workers_from_config() -> int:
    """从配置或环境变量获取最大并发工作线程数"""
    try:
        from app.config import get_performance_config
        return get_performance_config().max_concurrent_workers
    except ImportError:
        # 如果无法导入配置，直接从环境变量获取
        return int(os.getenv("SPEC2TEST_MAX_CONCURRENT_WORKERS", "8"))


def _get_concurrent_threshold_from_config() -> int:
    """从配置或环境变量获取并发阈值"""
    try:
        from app.config import get_performance_config
        return get_performance_config().concurrent_threshold
    except ImportError:
        # 如果无法导入配置，直接从环境变量获取
        return int(os.getenv("SPEC2TEST_CONCURRENT_THRESHOLD", "3"))


class TestCaseType(str, Enum):
    """测试用例类型枚举"""
    POSITIVE = "positive"      # 正向测试用例
    NEGATIVE = "negative"      # 负向测试用例
    BOUNDARY = "boundary"      # 边界测试用例
    SECURITY = "security"      # 安全测试用例
    PERFORMANCE = "performance" # 性能测试用例
    INTEGRATION = "integration" # 集成测试用例


class TestCasePriority(str, Enum):
    """测试用例优先级枚举"""
    CRITICAL = "critical"      # 关键
    HIGH = "high"             # 高
    MEDIUM = "medium"         # 中
    LOW = "low"              # 低


class TestDataType(str, Enum):
    """测试数据类型枚举"""
    VALID = "valid"           # 有效数据
    INVALID = "invalid"       # 无效数据
    BOUNDARY = "boundary"     # 边界数据
    NULL = "null"            # 空值数据
    SPECIAL = "special"       # 特殊字符数据


class GenerationStrategy(str, Enum):
    """生成策略枚举"""
    COMPREHENSIVE = "comprehensive"  # 全面生成
    FOCUSED = "focused"             # 重点生成
    MINIMAL = "minimal"             # 最小生成
    CUSTOM = "custom"               # 自定义生成


class TestStep(BaseModel):
    """测试步骤"""
    step_number: int = Field(description="步骤序号")
    action: str = Field(description="执行动作")
    description: str = Field(description="步骤描述")
    expected_result: str = Field(description="预期结果")
    data: Optional[Dict[str, Any]] = Field(default=None, description="测试数据")
    
    class Config:
        arbitrary_types_allowed = True


class TestAssertion(BaseModel):
    """测试断言"""
    assertion_type: str = Field(description="断言类型")
    field_path: Optional[str] = Field(default=None, description="字段路径")
    expected_value: Any = Field(description="期望值")
    operator: str = Field(default="equals", description="比较操作符")
    description: str = Field(description="断言描述")
    
    class Config:
        arbitrary_types_allowed = True


class TestCase(BaseModel):
    """测试用例"""
    case_id: str = Field(description="用例ID")
    title: str = Field(description="用例标题")
    description: str = Field(description="用例描述")
    
    # 分类信息
    case_type: TestCaseType = Field(description="用例类型")
    priority: TestCasePriority = Field(description="优先级")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    # API信息
    endpoint_path: str = Field(description="端点路径")
    http_method: str = Field(description="HTTP方法")
    
    # 测试数据
    request_headers: Optional[Dict[str, str]] = Field(default=None, description="请求头")
    request_params: Optional[Dict[str, Any]] = Field(default=None, description="请求参数")
    request_body: Optional[Dict[str, Any]] = Field(default=None, description="请求体")
    
    # 预期结果
    expected_status_code: int = Field(description="预期状态码")
    expected_response: Optional[Dict[str, Any]] = Field(default=None, description="预期响应")
    
    # 测试步骤和断言
    test_steps: List[TestStep] = Field(default_factory=list, description="测试步骤")
    assertions: List[TestAssertion] = Field(default_factory=list, description="断言列表")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    estimated_duration: Optional[float] = Field(default=None, description="预估执行时间(秒)")
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @property
    def case_identifier(self) -> str:
        """用例唯一标识"""
        return f"{self.http_method.upper()}:{self.endpoint_path}:{self.case_id}"


class TestSuite(BaseModel):
    """测试套件"""
    suite_id: str = Field(description="套件ID")
    name: str = Field(description="套件名称")
    description: str = Field(description="套件描述")
    
    # 测试用例
    test_cases: List[TestCase] = Field(default_factory=list, description="测试用例列表")
    
    # 套件配置
    base_url: Optional[str] = Field(default=None, description="基础URL")
    global_headers: Optional[Dict[str, str]] = Field(default=None, description="全局请求头")
    setup_steps: List[TestStep] = Field(default_factory=list, description="前置步骤")
    teardown_steps: List[TestStep] = Field(default_factory=list, description="后置步骤")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    total_cases: int = Field(default=0, description="用例总数")
    estimated_duration: Optional[float] = Field(default=None, description="预估执行时间(秒)")
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_test_case(self, test_case: TestCase):
        """添加测试用例"""
        self.test_cases.append(test_case)
        self.total_cases = len(self.test_cases)
        
        # 更新预估执行时间
        if test_case.estimated_duration:
            if self.estimated_duration is None:
                self.estimated_duration = 0
            self.estimated_duration += test_case.estimated_duration
    
    def get_cases_by_type(self, case_type: TestCaseType) -> List[TestCase]:
        """根据类型获取测试用例"""
        return [case for case in self.test_cases if case.case_type == case_type]
    
    def get_cases_by_priority(self, priority: TestCasePriority) -> List[TestCase]:
        """根据优先级获取测试用例"""
        return [case for case in self.test_cases if case.priority == priority]
    
    def get_cases_by_endpoint(self, endpoint_path: str, method: Optional[str] = None) -> List[TestCase]:
        """根据端点获取测试用例"""
        cases = [case for case in self.test_cases if case.endpoint_path == endpoint_path]
        if method:
            cases = [case for case in cases if case.http_method.upper() == method.upper()]
        return cases


class GenerationConfig(BaseModel):
    """测试生成配置"""
    strategy: GenerationStrategy = Field(default=GenerationStrategy.COMPREHENSIVE, description="生成策略")

    # 用例类型配置
    include_positive: bool = Field(default=True, description="包含正向用例")
    include_negative: bool = Field(default=True, description="包含负向用例")
    include_boundary: bool = Field(default=True, description="包含边界用例")
    include_security: bool = Field(default=False, description="包含安全用例")
    include_performance: bool = Field(default=False, description="包含性能用例")

    # 数据生成配置
    max_cases_per_endpoint: int = Field(default=10, description="每个端点最大用例数")
    include_invalid_data: bool = Field(default=True, description="包含无效数据测试")
    include_null_data: bool = Field(default=True, description="包含空值数据测试")
    include_special_chars: bool = Field(default=True, description="包含特殊字符测试")

    # LLM配置
    llm_temperature: float = Field(default=0.3, description="LLM温度参数")
    llm_max_tokens: int = Field(default=4000, description="LLM最大Token数")

    # 并发配置
    enable_concurrent: bool = Field(default=True, description="启用并发生成")
    max_concurrent_workers: int = Field(
        default_factory=lambda: _get_concurrent_workers_from_config(),
        description="最大并发工作线程数"
    )
    concurrent_threshold: int = Field(
        default_factory=lambda: _get_concurrent_threshold_from_config(),
        description="启用并发的端点数量阈值"
    )

    # 输出配置
    output_format: str = Field(default="json", description="输出格式")
    include_documentation: bool = Field(default=True, description="包含文档说明")

    class Config:
        use_enum_values = True


class GenerationResult(BaseModel):
    """测试生成结果"""
    success: bool = Field(description="是否成功")
    test_suite: Optional[TestSuite] = Field(default=None, description="生成的测试套件")
    
    # 统计信息
    total_cases_generated: int = Field(default=0, description="生成的用例总数")
    cases_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计的用例数")
    cases_by_priority: Dict[str, int] = Field(default_factory=dict, description="按优先级统计的用例数")
    
    # 生成信息
    generation_duration: Optional[float] = Field(default=None, description="生成耗时(秒)")
    llm_calls_count: int = Field(default=0, description="LLM调用次数")
    
    # 错误信息
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    
    # 元数据
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    config_used: Optional[GenerationConfig] = Field(default=None, description="使用的配置")
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0
    
    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(warning)


# LLM响应的数据模型
class LLMTestCase(BaseModel):
    """LLM返回的测试用例"""
    title: str
    description: str
    case_type: str
    priority: str
    request_data: Dict[str, Any]
    expected_status_code: int
    expected_response: Optional[Dict[str, Any]] = None
    assertions: List[Dict[str, Any]]
    tags: List[str] = Field(default_factory=list)


class LLMGenerationResponse(BaseModel):
    """LLM返回的生成响应"""
    test_cases: List[LLMTestCase]
    summary: str
    recommendations: List[str] = Field(default_factory=list)
