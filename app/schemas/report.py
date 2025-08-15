"""
报告相关的Pydantic Schema

定义报告模型的输入输出Schema，用于API请求响应的数据验证。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.report import ReportType, ReportStatus, ReportFormat


class ReportBase(BaseModel):
    """报告基础Schema"""
    name: str = Field(..., description="报告名称", max_length=255)
    description: Optional[str] = Field(None, description="报告描述")
    report_type: ReportType = Field(..., description="报告类型")
    format: ReportFormat = Field(ReportFormat.HTML, description="报告格式")


class ReportCreate(ReportBase):
    """创建报告Schema"""
    document_id: int = Field(..., description="关联文档ID")
    execution_id: Optional[str] = Field(None, description="关联的执行批次ID", max_length=100)
    generation_config: Optional[Dict[str, Any]] = Field(None, description="报告生成配置")


class ReportUpdate(BaseModel):
    """更新报告Schema"""
    name: Optional[str] = Field(None, description="报告名称", max_length=255)
    description: Optional[str] = Field(None, description="报告描述")
    status: Optional[ReportStatus] = Field(None, description="报告状态")


class ReportResponse(ReportBase):
    """报告响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="报告ID")
    document_id: int = Field(..., description="关联文档ID")
    status: ReportStatus = Field(..., description="报告状态")
    execution_id: Optional[str] = Field(None, description="关联的执行批次ID")
    generated_at: Optional[datetime] = Field(None, description="报告生成时间")
    
    # 测试统计
    total_test_cases: int = Field(..., description="总测试用例数")
    passed_count: int = Field(..., description="通过的测试数量")
    failed_count: int = Field(..., description="失败的测试数量")
    error_count: int = Field(..., description="错误的测试数量")
    skipped_count: int = Field(..., description="跳过的测试数量")
    
    # 性能统计
    total_execution_time: Optional[float] = Field(None, description="总执行时间（秒）")
    average_response_time: Optional[float] = Field(None, description="平均响应时间（秒）")
    
    # 覆盖率统计
    endpoint_coverage: Optional[float] = Field(None, description="端点覆盖率（百分比）")
    method_coverage: Optional[float] = Field(None, description="HTTP方法覆盖率（百分比）")
    
    # 文件信息
    file_path: Optional[str] = Field(None, description="报告文件路径")
    file_size: Optional[int] = Field(None, description="报告文件大小（字节）")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ReportDetail(ReportResponse):
    """报告详情Schema"""
    # 详细统计数据
    test_results_summary: Optional[Dict[str, Any]] = Field(None, description="测试结果摘要")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标详情")
    failure_analysis: Optional[Dict[str, Any]] = Field(None, description="失败分析数据")
    coverage_details: Optional[Dict[str, Any]] = Field(None, description="覆盖率详情")
    
    # 可视化数据
    charts_data: Optional[Dict[str, Any]] = Field(None, description="图表数据")
    
    # 建议和改进
    recommendations: Optional[List[str]] = Field(None, description="改进建议")
    issues_found: Optional[List[Dict[str, Any]]] = Field(None, description="发现的问题")
    
    # 性能详细统计
    min_response_time: Optional[float] = Field(None, description="最小响应时间（秒）")
    max_response_time: Optional[float] = Field(None, description="最大响应时间（秒）")
    status_code_coverage: Optional[float] = Field(None, description="状态码覆盖率（百分比）")
    
    # 配置信息
    generation_config: Optional[Dict[str, Any]] = Field(None, description="报告生成配置")


class ReportList(BaseModel):
    """报告列表Schema"""
    items: List[ReportResponse] = Field(..., description="报告列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class ReportGenerate(BaseModel):
    """报告生成请求Schema"""
    document_id: int = Field(..., description="文档ID")
    report_type: ReportType = Field(..., description="报告类型")
    format: ReportFormat = Field(ReportFormat.HTML, description="报告格式")
    execution_id: Optional[str] = Field(None, description="执行批次ID")
    
    # 生成配置
    include_charts: bool = Field(True, description="是否包含图表")
    include_details: bool = Field(True, description="是否包含详细信息")
    include_recommendations: bool = Field(True, description="是否包含改进建议")
    
    # 筛选条件
    test_case_ids: Optional[List[int]] = Field(None, description="指定测试用例ID列表")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")


class ReportStats(BaseModel):
    """报告统计Schema"""
    total_reports: int = Field(..., description="报告总数")
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    by_format: Dict[str, int] = Field(..., description="按格式统计")
    recent_generated: int = Field(..., description="最近生成数量")
    total_file_size: int = Field(..., description="总文件大小（字节）")


class ReportTemplate(BaseModel):
    """报告模板Schema"""
    name: str = Field(..., description="模板名称", max_length=100)
    description: Optional[str] = Field(None, description="模板描述")
    report_type: ReportType = Field(..., description="适用的报告类型")
    template_config: Dict[str, Any] = Field(..., description="模板配置")
    is_default: bool = Field(False, description="是否为默认模板")


class ReportExport(BaseModel):
    """报告导出Schema"""
    report_id: int = Field(..., description="报告ID")
    export_format: str = Field(..., description="导出格式", pattern="^(pdf|excel|csv|json)$")
    include_charts: bool = Field(True, description="是否包含图表")
    include_raw_data: bool = Field(False, description="是否包含原始数据")


class ReportComparison(BaseModel):
    """报告对比Schema"""
    baseline_report_id: int = Field(..., description="基准报告ID")
    current_report_id: int = Field(..., description="当前报告ID")
    comparison_metrics: List[str] = Field(..., description="对比指标列表")


class ReportComparisonResult(BaseModel):
    """报告对比结果Schema"""
    baseline_report: ReportResponse = Field(..., description="基准报告")
    current_report: ReportResponse = Field(..., description="当前报告")
    
    # 对比结果
    success_rate_diff: float = Field(..., description="成功率差异（百分比）")
    performance_diff: Dict[str, float] = Field(..., description="性能差异")
    coverage_diff: Dict[str, float] = Field(..., description="覆盖率差异")
    
    # 趋势分析
    trend_analysis: Dict[str, str] = Field(..., description="趋势分析")
    improvement_areas: List[str] = Field(..., description="改进领域")
    regression_issues: List[str] = Field(..., description="回归问题")


class ReportSchedule(BaseModel):
    """报告调度Schema"""
    name: str = Field(..., description="调度任务名称", max_length=100)
    document_id: int = Field(..., description="文档ID")
    report_type: ReportType = Field(..., description="报告类型")
    format: ReportFormat = Field(..., description="报告格式")
    
    # 调度配置
    cron_expression: str = Field(..., description="Cron表达式")
    is_active: bool = Field(True, description="是否激活")
    
    # 通知配置
    email_recipients: Optional[List[str]] = Field(None, description="邮件接收者列表")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    
    # 生成配置
    generation_config: Optional[Dict[str, Any]] = Field(None, description="报告生成配置")


class ReportFilter(BaseModel):
    """报告筛选Schema"""
    document_ids: Optional[List[int]] = Field(None, description="文档ID列表")
    report_types: Optional[List[ReportType]] = Field(None, description="报告类型列表")
    statuses: Optional[List[ReportStatus]] = Field(None, description="状态列表")
    formats: Optional[List[ReportFormat]] = Field(None, description="格式列表")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    execution_id: Optional[str] = Field(None, description="执行批次ID")
