"""
测试结果相关的Pydantic Schema

定义测试结果模型的输入输出Schema，用于API请求响应的数据验证。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.test_result import TestStatus, FailureType


class TestResultBase(BaseModel):
    """测试结果基础Schema"""
    status: TestStatus = Field(..., description="测试状态")
    execution_id: Optional[str] = Field(None, description="执行批次ID", max_length=100)


class TestResultCreate(TestResultBase):
    """创建测试结果Schema"""
    test_case_id: int = Field(..., description="关联测试用例ID")
    
    # 请求信息
    actual_request_url: Optional[str] = Field(None, description="实际请求URL", max_length=1000)
    actual_request_headers: Optional[Dict[str, Any]] = Field(None, description="实际请求头")
    actual_request_body: Optional[Dict[str, Any]] = Field(None, description="实际请求体")
    
    # 响应信息
    response_status_code: Optional[int] = Field(None, description="响应状态码")
    response_headers: Optional[Dict[str, Any]] = Field(None, description="响应头")
    response_body: Optional[Dict[str, Any]] = Field(None, description="响应体")
    response_size: Optional[int] = Field(None, description="响应大小（字节）", ge=0)
    
    # 性能指标
    response_time: Optional[float] = Field(None, description="响应时间（秒）", ge=0)
    dns_lookup_time: Optional[float] = Field(None, description="DNS查询时间（秒）", ge=0)
    tcp_connect_time: Optional[float] = Field(None, description="TCP连接时间（秒）", ge=0)
    ssl_handshake_time: Optional[float] = Field(None, description="SSL握手时间（秒）", ge=0)
    first_byte_time: Optional[float] = Field(None, description="首字节时间（秒）", ge=0)
    
    # 验证结果
    validation_results: Optional[Dict[str, Any]] = Field(None, description="验证结果详情")
    assertions_passed: Optional[int] = Field(0, description="通过的断言数量", ge=0)
    assertions_failed: Optional[int] = Field(0, description="失败的断言数量", ge=0)
    
    # 错误信息
    failure_type: Optional[FailureType] = Field(None, description="失败类型")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="错误堆栈")
    
    # 重试信息
    retry_count: int = Field(0, description="重试次数", ge=0)
    is_retry: bool = Field(False, description="是否为重试执行")
    
    # 环境信息
    environment: Optional[str] = Field(None, description="执行环境", max_length=50)
    user_agent: Optional[str] = Field(None, description="用户代理", max_length=500)


class TestResultUpdate(BaseModel):
    """更新测试结果Schema"""
    status: Optional[TestStatus] = Field(None, description="测试状态")
    error_message: Optional[str] = Field(None, description="错误消息")
    retry_count: Optional[int] = Field(None, description="重试次数", ge=0)


class TestResultResponse(TestResultBase):
    """测试结果响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="测试结果ID")
    test_case_id: int = Field(..., description="关联测试用例ID")
    
    # 时间信息
    started_at: Optional[datetime] = Field(None, description="开始执行时间")
    completed_at: Optional[datetime] = Field(None, description="完成执行时间")
    
    # 请求信息
    actual_request_url: Optional[str] = Field(None, description="实际请求URL")
    
    # 响应信息
    response_status_code: Optional[int] = Field(None, description="响应状态码")
    response_size: Optional[int] = Field(None, description="响应大小（字节）")
    
    # 性能指标
    response_time: Optional[float] = Field(None, description="响应时间（秒）")
    
    # 验证结果
    assertions_passed: Optional[int] = Field(None, description="通过的断言数量")
    assertions_failed: Optional[int] = Field(None, description="失败的断言数量")
    
    # 错误信息
    failure_type: Optional[FailureType] = Field(None, description="失败类型")
    error_message: Optional[str] = Field(None, description="错误消息")
    
    # 重试信息
    retry_count: int = Field(..., description="重试次数")
    is_retry: bool = Field(..., description="是否为重试执行")
    
    # 环境信息
    environment: Optional[str] = Field(None, description="执行环境")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class TestResultDetail(TestResultResponse):
    """测试结果详情Schema"""
    # 完整请求信息
    actual_request_headers: Optional[Dict[str, Any]] = Field(None, description="实际请求头")
    actual_request_body: Optional[Dict[str, Any]] = Field(None, description="实际请求体")
    
    # 完整响应信息
    response_headers: Optional[Dict[str, Any]] = Field(None, description="响应头")
    response_body: Optional[Dict[str, Any]] = Field(None, description="响应体")
    
    # 详细性能指标
    dns_lookup_time: Optional[float] = Field(None, description="DNS查询时间（秒）")
    tcp_connect_time: Optional[float] = Field(None, description="TCP连接时间（秒）")
    ssl_handshake_time: Optional[float] = Field(None, description="SSL握手时间（秒）")
    first_byte_time: Optional[float] = Field(None, description="首字节时间（秒）")
    
    # 详细验证结果
    validation_results: Optional[Dict[str, Any]] = Field(None, description="验证结果详情")
    
    # 详细错误信息
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="错误堆栈")
    
    # 用户代理
    user_agent: Optional[str] = Field(None, description="用户代理")


class TestResultList(BaseModel):
    """测试结果列表Schema"""
    items: List[TestResultResponse] = Field(..., description="测试结果列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class TestResultSummary(BaseModel):
    """测试结果摘要Schema"""
    execution_id: str = Field(..., description="执行批次ID")
    total_tests: int = Field(..., description="总测试数量")
    passed_count: int = Field(..., description="通过数量")
    failed_count: int = Field(..., description="失败数量")
    error_count: int = Field(..., description="错误数量")
    skipped_count: int = Field(..., description="跳过数量")
    success_rate: float = Field(..., description="成功率（百分比）")
    total_execution_time: Optional[float] = Field(None, description="总执行时间（秒）")
    average_response_time: Optional[float] = Field(None, description="平均响应时间（秒）")


class TestResultStats(BaseModel):
    """测试结果统计Schema"""
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    by_failure_type: Dict[str, int] = Field(..., description="按失败类型统计")
    performance_stats: Dict[str, float] = Field(..., description="性能统计")
    recent_executions: int = Field(..., description="最近执行数量")


class TestResultComparison(BaseModel):
    """测试结果对比Schema"""
    baseline_result_id: int = Field(..., description="基准测试结果ID")
    current_result_id: int = Field(..., description="当前测试结果ID")
    status_changed: bool = Field(..., description="状态是否改变")
    performance_diff: Dict[str, float] = Field(..., description="性能差异")
    response_diff: Dict[str, Any] = Field(..., description="响应差异")
    improvement_suggestions: List[str] = Field(..., description="改进建议")


class TestResultExport(BaseModel):
    """测试结果导出Schema"""
    format: str = Field(..., description="导出格式", pattern="^(json|csv|excel|pdf)$")
    test_result_ids: List[int] = Field(..., description="要导出的测试结果ID列表", min_items=1)
    include_details: bool = Field(True, description="是否包含详细信息")
    include_performance: bool = Field(True, description="是否包含性能数据")


class TestResultFilter(BaseModel):
    """测试结果筛选Schema"""
    status: Optional[List[TestStatus]] = Field(None, description="状态筛选")
    execution_id: Optional[str] = Field(None, description="执行批次ID")
    test_case_ids: Optional[List[int]] = Field(None, description="测试用例ID列表")
    failure_types: Optional[List[FailureType]] = Field(None, description="失败类型筛选")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    min_response_time: Optional[float] = Field(None, description="最小响应时间", ge=0)
    max_response_time: Optional[float] = Field(None, description="最大响应时间", ge=0)
