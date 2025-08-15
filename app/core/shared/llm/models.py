"""
LLM结构化输出的Pydantic模型

定义用于LLM结构化输出的Pydantic模型，确保类型安全和数据验证。
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class TestCaseType(str, Enum):
    """测试用例类型枚举"""
    NORMAL = "normal"
    BOUNDARY = "boundary"
    EXCEPTION = "exception"
    SECURITY = "security"
    PERFORMANCE = "performance"


class HTTPMethod(str, Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class APITestCase(BaseModel):
    """API测试用例结构化模型"""
    name: str = Field(description="测试用例名称")
    description: str = Field(description="测试用例描述")
    test_type: TestCaseType = Field(description="测试用例类型")
    priority: str = Field(description="测试优先级", default="medium")
    
    # HTTP请求信息
    method: HTTPMethod = Field(description="HTTP请求方法")
    endpoint: str = Field(description="API端点路径")
    headers: Optional[Dict[str, str]] = Field(default=None, description="请求头")
    query_params: Optional[Dict[str, Any]] = Field(default=None, description="查询参数")
    path_params: Optional[Dict[str, Any]] = Field(default=None, description="路径参数")
    request_body: Optional[Dict[str, Any]] = Field(default=None, description="请求体")
    
    # 期望结果
    expected_status_code: int = Field(description="期望的HTTP状态码")
    expected_response_headers: Optional[Dict[str, str]] = Field(default=None, description="期望的响应头")
    expected_response_body: Optional[Dict[str, Any]] = Field(default=None, description="期望的响应体")
    expected_response_schema: Optional[Dict[str, Any]] = Field(default=None, description="期望的响应Schema")
    
    # 验证规则
    assertions: List[str] = Field(default_factory=list, description="断言列表")
    validation_rules: Optional[Dict[str, Any]] = Field(default=None, description="自定义验证规则")
    
    # 测试配置
    timeout: Optional[float] = Field(default=30.0, description="超时时间（秒）")
    retry_count: Optional[int] = Field(default=0, description="重试次数")
    tags: List[str] = Field(default_factory=list, description="测试标签")


class TestSuite(BaseModel):
    """测试套件结构化模型"""
    name: str = Field(description="测试套件名称")
    description: str = Field(description="测试套件描述")
    version: str = Field(default="1.0.0", description="版本号")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    
    # 全局配置
    global_headers: Optional[Dict[str, str]] = Field(default=None, description="全局请求头")
    global_timeout: Optional[float] = Field(default=30.0, description="全局超时时间")
    
    # 测试用例
    test_cases: List[APITestCase] = Field(description="测试用例列表")
    
    # 统计信息
    total_cases: Optional[int] = Field(default=None, description="总测试用例数")
    setup_scripts: Optional[List[str]] = Field(default=None, description="前置脚本")
    teardown_scripts: Optional[List[str]] = Field(default=None, description="后置脚本")


class DocumentAnalysis(BaseModel):
    """文档分析结果结构化模型"""
    document_type: str = Field(description="文档类型")
    format_version: Optional[str] = Field(default=None, description="格式版本")
    title: Optional[str] = Field(default=None, description="文档标题")
    description: Optional[str] = Field(default=None, description="文档描述")
    
    # API信息
    api_version: Optional[str] = Field(default=None, description="API版本")
    base_url: Optional[str] = Field(default=None, description="API基础URL")
    
    # 端点信息
    endpoints: List[Dict[str, Any]] = Field(default_factory=list, description="API端点列表")
    total_endpoints: int = Field(default=0, description="端点总数")
    
    # 数据模型
    schemas: Optional[Dict[str, Any]] = Field(default=None, description="数据模型定义")
    
    # 认证信息
    authentication: Optional[Dict[str, Any]] = Field(default=None, description="认证方式")
    
    # 质量评估
    quality_score: Optional[float] = Field(default=None, description="文档质量评分（0-10）")
    completeness: Optional[float] = Field(default=None, description="完整性评分（0-1）")
    
    # 问题和建议
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    missing_elements: List[str] = Field(default_factory=list, description="缺失的元素")


class ValidationResult(BaseModel):
    """验证结果结构化模型"""
    is_valid: bool = Field(description="是否验证通过")
    overall_score: float = Field(description="总体评分（0-1）")
    
    # 详细验证结果
    type_validation: Dict[str, bool] = Field(description="类型验证结果")
    required_fields: Dict[str, bool] = Field(description="必需字段验证结果")
    format_validation: Dict[str, bool] = Field(description="格式验证结果")
    constraint_validation: Dict[str, bool] = Field(description="约束验证结果")
    
    # 错误和警告
    errors: List[str] = Field(default_factory=list, description="验证错误列表")
    warnings: List[str] = Field(default_factory=list, description="验证警告列表")
    suggestions: List[str] = Field(default_factory=list, description="改进建议列表")
    
    # 统计信息
    total_checks: int = Field(description="总检查项数")
    passed_checks: int = Field(description="通过的检查项数")
    failed_checks: int = Field(description="失败的检查项数")


class CodeGeneration(BaseModel):
    """代码生成结果结构化模型"""
    language: str = Field(description="编程语言")
    framework: Optional[str] = Field(default=None, description="使用的框架")
    
    # 生成的代码
    code: str = Field(description="生成的代码")
    imports: List[str] = Field(default_factory=list, description="需要的导入语句")
    dependencies: List[str] = Field(default_factory=list, description="依赖包列表")
    
    # 代码说明
    description: str = Field(description="代码功能描述")
    usage_example: Optional[str] = Field(default=None, description="使用示例")
    notes: List[str] = Field(default_factory=list, description="注意事项")
    
    # 质量指标
    complexity_score: Optional[float] = Field(default=None, description="复杂度评分（0-10）")
    maintainability_score: Optional[float] = Field(default=None, description="可维护性评分（0-10）")


class PerformanceAnalysis(BaseModel):
    """性能分析结果结构化模型"""
    overall_score: float = Field(description="总体性能评分（0-10）")
    
    # 响应时间分析
    avg_response_time: float = Field(description="平均响应时间（毫秒）")
    min_response_time: float = Field(description="最小响应时间（毫秒）")
    max_response_time: float = Field(description="最大响应时间（毫秒）")
    p95_response_time: float = Field(description="95%响应时间（毫秒）")
    
    # 性能问题
    bottlenecks: List[str] = Field(default_factory=list, description="性能瓶颈")
    slow_endpoints: List[Dict[str, Any]] = Field(default_factory=list, description="慢端点列表")
    
    # 优化建议
    optimization_suggestions: List[str] = Field(default_factory=list, description="优化建议")
    priority_fixes: List[str] = Field(default_factory=list, description="优先修复项")
    
    # 资源使用
    cpu_usage: Optional[float] = Field(default=None, description="CPU使用率")
    memory_usage: Optional[float] = Field(default=None, description="内存使用率")
    network_usage: Optional[float] = Field(default=None, description="网络使用率")


class SecurityAnalysis(BaseModel):
    """安全分析结果结构化模型"""
    security_score: float = Field(description="安全评分（0-10）")
    risk_level: str = Field(description="风险等级", default="medium")
    
    # 安全问题
    vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list, description="发现的漏洞")
    security_issues: List[str] = Field(default_factory=list, description="安全问题列表")
    
    # 认证和授权
    auth_analysis: Dict[str, Any] = Field(default_factory=dict, description="认证分析")
    authorization_issues: List[str] = Field(default_factory=list, description="授权问题")
    
    # 数据保护
    data_exposure_risks: List[str] = Field(default_factory=list, description="数据暴露风险")
    encryption_status: Dict[str, bool] = Field(default_factory=dict, description="加密状态")
    
    # 修复建议
    security_recommendations: List[str] = Field(default_factory=list, description="安全建议")
    immediate_actions: List[str] = Field(default_factory=list, description="立即行动项")
    long_term_improvements: List[str] = Field(default_factory=list, description="长期改进项")
