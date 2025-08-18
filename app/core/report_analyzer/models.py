"""
结果分析器数据模型

定义测试结果分析过程中使用的数据结构和模型。
"""

import os
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    """失败类别枚举"""
    NETWORK_ERROR = "network_error"          # 网络错误
    TIMEOUT_ERROR = "timeout_error"          # 超时错误
    HTTP_ERROR = "http_error"                # HTTP状态码错误
    ASSERTION_ERROR = "assertion_error"      # 断言失败
    AUTHENTICATION_ERROR = "auth_error"      # 认证错误
    VALIDATION_ERROR = "validation_error"    # 数据验证错误
    SERVER_ERROR = "server_error"            # 服务器内部错误
    CLIENT_ERROR = "client_error"            # 客户端错误
    UNKNOWN_ERROR = "unknown_error"          # 未知错误


class SeverityLevel(str, Enum):
    """严重程度枚举"""
    CRITICAL = "critical"    # 严重 - 阻塞性问题
    HIGH = "high"           # 高 - 重要功能问题
    MEDIUM = "medium"       # 中 - 一般功能问题
    LOW = "low"             # 低 - 轻微问题
    INFO = "info"           # 信息 - 仅供参考


class FailurePattern(BaseModel):
    """失败模式"""
    pattern_id: str = Field(description="模式ID")
    category: FailureCategory = Field(description="失败类别")
    pattern_name: str = Field(description="模式名称")
    description: str = Field(description="模式描述")
    
    # 匹配条件
    status_codes: Optional[List[int]] = Field(default=None, description="匹配的状态码")
    error_keywords: Optional[List[str]] = Field(default=None, description="错误关键词")
    response_time_threshold: Optional[float] = Field(default=None, description="响应时间阈值")
    
    # 统计信息
    occurrence_count: int = Field(default=0, description="出现次数")
    affected_endpoints: List[str] = Field(default_factory=list, description="受影响的端点")
    
    class Config:
        use_enum_values = True


class FailureAnalysis(BaseModel):
    """失败分析结果"""
    test_id: str = Field(description="测试ID")
    endpoint_path: str = Field(description="端点路径")
    http_method: str = Field(description="HTTP方法")
    
    # 失败信息
    failure_category: FailureCategory = Field(description="失败类别")
    severity_level: SeverityLevel = Field(description="严重程度")
    failure_reason: str = Field(description="失败原因")
    error_message: str = Field(description="错误消息")
    
    # 匹配的模式
    matched_patterns: List[str] = Field(default_factory=list, description="匹配的失败模式ID")
    
    # 修复建议
    fix_suggestions: List[str] = Field(default_factory=list, description="修复建议")
    
    # 相关信息
    response_status_code: Optional[int] = Field(default=None, description="响应状态码")
    response_time: Optional[float] = Field(default=None, description="响应时间")
    
    class Config:
        use_enum_values = True


class PerformanceMetrics(BaseModel):
    """性能指标"""
    # 基础统计
    total_tests: int = Field(description="总测试数")
    passed_tests: int = Field(description="通过测试数")
    failed_tests: int = Field(description="失败测试数")
    error_tests: int = Field(description="错误测试数")
    skipped_tests: int = Field(description="跳过测试数")
    
    # 成功率
    success_rate: float = Field(description="成功率")
    failure_rate: float = Field(description="失败率")
    
    # 性能指标
    avg_response_time: float = Field(description="平均响应时间")
    min_response_time: float = Field(description="最小响应时间")
    max_response_time: float = Field(description="最大响应时间")
    p95_response_time: float = Field(description="95%分位响应时间")
    p99_response_time: float = Field(description="99%分位响应时间")
    
    # 执行时间
    total_execution_time: float = Field(description="总执行时间")
    avg_test_duration: float = Field(description="平均测试时长")
    
    class Config:
        arbitrary_types_allowed = True


class EndpointAnalysis(BaseModel):
    """端点分析结果"""
    endpoint_path: str = Field(description="端点路径")
    http_method: str = Field(description="HTTP方法")
    
    # 测试统计
    total_tests: int = Field(description="总测试数")
    passed_tests: int = Field(description="通过测试数")
    failed_tests: int = Field(description="失败测试数")
    success_rate: float = Field(description="成功率")
    
    # 性能统计
    avg_response_time: float = Field(description="平均响应时间")
    min_response_time: float = Field(description="最小响应时间")
    max_response_time: float = Field(description="最大响应时间")
    
    # 失败分析
    failure_analyses: List[FailureAnalysis] = Field(default_factory=list, description="失败分析列表")
    common_failures: List[str] = Field(default_factory=list, description="常见失败原因")
    
    # 建议
    recommendations: List[str] = Field(default_factory=list, description="优化建议")
    
    class Config:
        arbitrary_types_allowed = True


class TrendData(BaseModel):
    """趋势数据"""
    timestamp: datetime = Field(description="时间戳")
    success_rate: float = Field(description="成功率")
    avg_response_time: float = Field(description="平均响应时间")
    total_tests: int = Field(description="总测试数")
    failed_tests: int = Field(description="失败测试数")
    
    class Config:
        arbitrary_types_allowed = True


class AnalysisReport(BaseModel):
    """分析报告"""
    report_id: str = Field(description="报告ID")
    report_name: str = Field(description="报告名称")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    
    # 基础信息
    suite_id: str = Field(description="测试套件ID")
    suite_name: str = Field(description="测试套件名称")
    execution_time: datetime = Field(description="执行时间")
    
    # 整体性能指标
    overall_metrics: PerformanceMetrics = Field(description="整体性能指标")
    
    # 端点分析
    endpoint_analyses: List[EndpointAnalysis] = Field(default_factory=list, description="端点分析列表")
    
    # 失败模式分析
    failure_patterns: List[FailurePattern] = Field(default_factory=list, description="失败模式列表")
    top_failure_categories: List[Dict[str, Any]] = Field(default_factory=list, description="主要失败类别")
    
    # 趋势分析
    trend_data: List[TrendData] = Field(default_factory=list, description="趋势数据")
    
    # 总结和建议
    summary: str = Field(description="分析总结")
    key_findings: List[str] = Field(default_factory=list, description="关键发现")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    
    # 风险评估
    risk_level: SeverityLevel = Field(description="风险等级")
    critical_issues: List[str] = Field(default_factory=list, description="关键问题")
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class AnalysisConfig(BaseModel):
    """分析配置"""
    # 失败分析配置
    enable_failure_analysis: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_ENABLE_FAILURE_ANALYSIS", "true").lower() == "true",
        description="启用失败分析"
    )
    
    # 性能分析配置
    enable_performance_analysis: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_ENABLE_PERFORMANCE_ANALYSIS", "true").lower() == "true",
        description="启用性能分析"
    )
    
    # 趋势分析配置
    enable_trend_analysis: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_ENABLE_TREND_ANALYSIS", "false").lower() == "true",
        description="启用趋势分析"
    )
    
    # 阈值配置
    slow_response_threshold: float = Field(
        default_factory=lambda: float(os.getenv("SPEC2TEST_SLOW_RESPONSE_THRESHOLD", "2.0")),
        description="慢响应阈值(秒)"
    )
    
    low_success_rate_threshold: float = Field(
        default_factory=lambda: float(os.getenv("SPEC2TEST_LOW_SUCCESS_RATE_THRESHOLD", "0.8")),
        description="低成功率阈值"
    )
    
    # 报告配置
    include_detailed_failures: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_INCLUDE_DETAILED_FAILURES", "true").lower() == "true",
        description="包含详细失败信息"
    )
    
    max_failure_examples: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_MAX_FAILURE_EXAMPLES", "10")),
        description="最大失败示例数"
    )
    
    # 可视化配置
    enable_charts: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_ENABLE_CHARTS", "true").lower() == "true",
        description="启用图表生成"
    )
    
    chart_width: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_CHART_WIDTH", "800")),
        description="图表宽度"
    )
    
    chart_height: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_CHART_HEIGHT", "600")),
        description="图表高度"
    )
    
    class Config:
        arbitrary_types_allowed = True


class ComparisonReport(BaseModel):
    """对比报告"""
    comparison_id: str = Field(description="对比ID")
    comparison_name: str = Field(description="对比名称")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    
    # 对比的报告
    baseline_report: AnalysisReport = Field(description="基线报告")
    current_report: AnalysisReport = Field(description="当前报告")
    
    # 对比结果
    performance_changes: Dict[str, float] = Field(default_factory=dict, description="性能变化")
    new_failures: List[str] = Field(default_factory=list, description="新增失败")
    resolved_failures: List[str] = Field(default_factory=list, description="已解决失败")
    regression_issues: List[str] = Field(default_factory=list, description="回归问题")
    
    # 总体评估
    overall_change: str = Field(description="总体变化评估")  # improved, degraded, stable
    change_summary: str = Field(description="变化总结")
    
    class Config:
        arbitrary_types_allowed = True
