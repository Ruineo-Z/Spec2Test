"""
报告模型

定义测试报告的数据模型，包含测试统计、分析结果、可视化数据等信息。
支持多种报告格式和详细的测试分析。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from .base import BaseModel


class ReportType(str, Enum):
    """报告类型枚举"""
    EXECUTION_SUMMARY = "execution_summary"    # 执行摘要报告
    DETAILED_ANALYSIS = "detailed_analysis"    # 详细分析报告
    PERFORMANCE_REPORT = "performance_report"  # 性能报告
    FAILURE_ANALYSIS = "failure_analysis"      # 失败分析报告
    COVERAGE_REPORT = "coverage_report"        # 覆盖率报告
    TREND_ANALYSIS = "trend_analysis"          # 趋势分析报告


class ReportStatus(str, Enum):
    """报告状态枚举"""
    GENERATING = "generating"    # 生成中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"           # 生成失败
    ARCHIVED = "archived"       # 已归档


class ReportFormat(str, Enum):
    """报告格式枚举"""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    EXCEL = "excel"
    CSV = "csv"


class Report(BaseModel):
    """报告模型
    
    存储测试报告的基本信息、统计数据和分析结果。
    支持多种报告类型和格式的生成。
    """
    
    __tablename__ = "reports"
    
    # 关联文档
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联文档ID"
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="报告名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="报告描述"
    )
    
    # 报告类型和状态
    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType),
        nullable=False,
        comment="报告类型"
    )
    
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus),
        default=ReportStatus.GENERATING,
        nullable=False,
        comment="报告状态"
    )
    
    format: Mapped[ReportFormat] = mapped_column(
        SQLEnum(ReportFormat),
        default=ReportFormat.HTML,
        nullable=False,
        comment="报告格式"
    )
    
    # 执行信息
    execution_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="关联的执行批次ID"
    )
    
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="报告生成时间"
    )
    
    # 测试统计
    total_test_cases: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="总测试用例数"
    )
    
    passed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="通过的测试数量"
    )
    
    failed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="失败的测试数量"
    )
    
    error_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="错误的测试数量"
    )
    
    skipped_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="跳过的测试数量"
    )
    
    # 性能统计
    total_execution_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="总执行时间（秒）"
    )
    
    average_response_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="平均响应时间（秒）"
    )
    
    min_response_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="最小响应时间（秒）"
    )
    
    max_response_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="最大响应时间（秒）"
    )
    
    # 覆盖率统计
    endpoint_coverage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="端点覆盖率（百分比）"
    )
    
    method_coverage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="HTTP方法覆盖率（百分比）"
    )
    
    status_code_coverage: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="状态码覆盖率（百分比）"
    )
    
    # 详细数据
    test_results_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="测试结果摘要"
    )
    
    performance_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="性能指标详情"
    )
    
    failure_analysis: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="失败分析数据"
    )
    
    coverage_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="覆盖率详情"
    )
    
    # 可视化数据
    charts_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="图表数据"
    )
    
    # 建议和改进
    recommendations: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="改进建议"
    )
    
    issues_found: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="发现的问题"
    )
    
    # 文件信息
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="报告文件路径"
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="报告文件大小（字节）"
    )
    
    # 配置信息
    generation_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="报告生成配置"
    )
    
    # 关联关系
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="reports"
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Report(id={self.id}, name='{self.name}', type={self.report_type}, status={self.status})>"
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_test_cases == 0:
            return 0.0
        return (self.passed_count / self.total_test_cases) * 100
    
    def get_failure_rate(self) -> float:
        """获取失败率"""
        if self.total_test_cases == 0:
            return 0.0
        return ((self.failed_count + self.error_count) / self.total_test_cases) * 100
    
    def is_completed(self) -> bool:
        """检查报告是否已完成"""
        return self.status == ReportStatus.COMPLETED
    
    def has_failures(self) -> bool:
        """检查是否有失败的测试"""
        return (self.failed_count + self.error_count) > 0
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """获取统计摘要"""
        return {
            "total_tests": self.total_test_cases,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "errors": self.error_count,
            "skipped": self.skipped_count,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "execution_time": self.total_execution_time,
            "avg_response_time": self.average_response_time
        }
    
    def get_coverage_stats(self) -> Dict[str, Any]:
        """获取覆盖率统计"""
        return {
            "endpoint_coverage": self.endpoint_coverage or 0.0,
            "method_coverage": self.method_coverage or 0.0,
            "status_code_coverage": self.status_code_coverage or 0.0
        }
    
    def mark_as_completed(self, file_path: Optional[str] = None, file_size: Optional[int] = None) -> None:
        """标记报告为已完成
        
        Args:
            file_path: 报告文件路径
            file_size: 报告文件大小
        """
        self.status = ReportStatus.COMPLETED
        self.generated_at = datetime.now()
        if file_path:
            self.file_path = file_path
        if file_size:
            self.file_size = file_size
    
    def mark_as_failed(self, error_message: str) -> None:
        """标记报告生成失败
        
        Args:
            error_message: 错误消息
        """
        self.status = ReportStatus.FAILED
        if not self.issues_found:
            self.issues_found = []
        self.issues_found.append({
            "type": "generation_error",
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        })
