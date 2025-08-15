"""
测试结果模型

定义API测试执行结果的数据模型，包含执行状态、响应数据、性能指标等信息。
支持详细的测试结果分析和报告生成。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from .base import BaseModel


class TestStatus(str, Enum):
    """测试状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    PASSED = "passed"        # 通过
    FAILED = "failed"        # 失败
    ERROR = "error"          # 错误
    SKIPPED = "skipped"      # 跳过
    TIMEOUT = "timeout"      # 超时


class FailureType(str, Enum):
    """失败类型枚举"""
    STATUS_CODE_MISMATCH = "status_code_mismatch"      # 状态码不匹配
    RESPONSE_BODY_MISMATCH = "response_body_mismatch"  # 响应体不匹配
    RESPONSE_SCHEMA_ERROR = "response_schema_error"    # 响应Schema错误
    TIMEOUT_ERROR = "timeout_error"                    # 超时错误
    CONNECTION_ERROR = "connection_error"              # 连接错误
    AUTHENTICATION_ERROR = "authentication_error"      # 认证错误
    VALIDATION_ERROR = "validation_error"              # 验证错误
    UNKNOWN_ERROR = "unknown_error"                    # 未知错误


class TestResult(BaseModel):
    """测试结果模型
    
    存储API测试的执行结果，包括请求响应数据、性能指标、错误信息等。
    支持详细的测试分析和问题诊断。
    """
    
    __tablename__ = "test_results"
    
    # 关联测试用例
    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联测试用例ID"
    )
    
    # 执行信息
    execution_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="执行批次ID"
    )
    
    status: Mapped[TestStatus] = mapped_column(
        SQLEnum(TestStatus),
        default=TestStatus.PENDING,
        nullable=False,
        comment="测试状态"
    )
    
    # 时间信息
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始执行时间"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成执行时间"
    )
    
    # 请求信息
    actual_request_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="实际请求URL"
    )
    
    actual_request_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="实际请求头"
    )
    
    actual_request_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="实际请求体"
    )
    
    # 响应信息
    response_status_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="响应状态码"
    )
    
    response_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="响应头"
    )
    
    response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="响应体"
    )
    
    response_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="响应大小（字节）"
    )
    
    # 性能指标
    response_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="响应时间（秒）"
    )
    
    dns_lookup_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="DNS查询时间（秒）"
    )
    
    tcp_connect_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="TCP连接时间（秒）"
    )
    
    ssl_handshake_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="SSL握手时间（秒）"
    )
    
    first_byte_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="首字节时间（秒）"
    )
    
    # 验证结果
    validation_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="验证结果详情"
    )
    
    assertions_passed: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        comment="通过的断言数量"
    )
    
    assertions_failed: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        comment="失败的断言数量"
    )
    
    # 错误信息
    failure_type: Mapped[Optional[FailureType]] = mapped_column(
        SQLEnum(FailureType),
        nullable=True,
        comment="失败类型"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误消息"
    )
    
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="错误详情"
    )
    
    stack_trace: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误堆栈"
    )
    
    # 重试信息
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="重试次数"
    )
    
    is_retry: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="是否为重试执行"
    )
    
    # 环境信息
    environment: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="执行环境"
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="用户代理"
    )
    
    # 关联关系
    test_case: Mapped["TestCase"] = relationship(
        "TestCase",
        back_populates="test_results"
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<TestResult(id={self.id}, test_case_id={self.test_case_id}, status={self.status})>"
    
    def is_successful(self) -> bool:
        """检查测试是否成功"""
        return self.status == TestStatus.PASSED
    
    def is_failed(self) -> bool:
        """检查测试是否失败"""
        return self.status in [TestStatus.FAILED, TestStatus.ERROR, TestStatus.TIMEOUT]
    
    def get_duration(self) -> Optional[float]:
        """获取执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        return {
            "response_time": self.response_time,
            "dns_lookup_time": self.dns_lookup_time,
            "tcp_connect_time": self.tcp_connect_time,
            "ssl_handshake_time": self.ssl_handshake_time,
            "first_byte_time": self.first_byte_time,
            "response_size": self.response_size,
            "duration": self.get_duration()
        }
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        total_assertions = (self.assertions_passed or 0) + (self.assertions_failed or 0)
        success_rate = (self.assertions_passed or 0) / total_assertions if total_assertions > 0 else 0
        
        return {
            "status": self.status,
            "assertions_passed": self.assertions_passed or 0,
            "assertions_failed": self.assertions_failed or 0,
            "total_assertions": total_assertions,
            "success_rate": success_rate,
            "has_errors": bool(self.error_message),
            "failure_type": self.failure_type
        }
    
    def mark_as_started(self) -> None:
        """标记为开始执行"""
        self.status = TestStatus.RUNNING
        self.started_at = datetime.now()
    
    def mark_as_completed(self, status: TestStatus, error_message: Optional[str] = None) -> None:
        """标记为执行完成
        
        Args:
            status: 最终状态
            error_message: 错误消息（如果有）
        """
        self.status = status
        self.completed_at = datetime.now()
        if error_message:
            self.error_message = error_message
