"""
测试用例模型

定义API测试用例的数据模型，包含测试参数、期望结果等信息。
支持正常、边界、异常等多种测试场景。
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from .base import BaseModel


class TestCaseType(str, Enum):
    """测试用例类型枚举"""
    NORMAL = "normal"        # 正常用例
    BOUNDARY = "boundary"    # 边界用例
    EXCEPTION = "exception"  # 异常用例
    SECURITY = "security"    # 安全用例
    PERFORMANCE = "performance"  # 性能用例


class TestCasePriority(str, Enum):
    """测试用例优先级枚举"""
    LOW = "low"         # 低优先级
    MEDIUM = "medium"   # 中优先级
    HIGH = "high"       # 高优先级
    CRITICAL = "critical"  # 关键优先级


class HTTPMethod(str, Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class TestCase(BaseModel):
    """测试用例模型
    
    存储API测试用例的详细信息，包括请求参数、期望响应等。
    支持多种测试类型和优先级管理。
    """
    
    __tablename__ = "test_cases"
    
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
        comment="测试用例名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="测试用例描述"
    )
    
    # 测试分类
    test_type: Mapped[TestCaseType] = mapped_column(
        SQLEnum(TestCaseType),
        default=TestCaseType.NORMAL,
        nullable=False,
        comment="测试用例类型"
    )
    
    priority: Mapped[TestCasePriority] = mapped_column(
        SQLEnum(TestCasePriority),
        default=TestCasePriority.MEDIUM,
        nullable=False,
        comment="测试优先级"
    )
    
    # API端点信息
    endpoint_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="API端点路径"
    )
    
    http_method: Mapped[HTTPMethod] = mapped_column(
        SQLEnum(HTTPMethod),
        nullable=False,
        comment="HTTP请求方法"
    )
    
    # 请求参数
    request_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="请求头参数"
    )
    
    request_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="查询参数"
    )
    
    request_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="请求体数据"
    )
    
    path_variables: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="路径变量"
    )
    
    # 认证信息
    auth_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="认证类型"
    )
    
    auth_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="认证数据"
    )
    
    # 期望结果
    expected_status_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="期望HTTP状态码"
    )
    
    expected_response_headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="期望响应头"
    )
    
    expected_response_body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="期望响应体"
    )
    
    expected_response_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="期望响应Schema"
    )
    
    # 验证规则
    validation_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="自定义验证规则"
    )
    
    # 性能要求
    max_response_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="最大响应时间（秒）"
    )
    
    # 测试标签和分组
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="测试标签"
    )
    
    test_group: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="测试分组"
    )
    
    # 依赖关系
    depends_on: Mapped[Optional[List[int]]] = mapped_column(
        JSON,
        nullable=True,
        comment="依赖的测试用例ID列表"
    )
    
    # 执行配置
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="重试次数"
    )
    
    timeout: Mapped[Optional[float]] = mapped_column(
        Float,
        default=30.0,
        nullable=True,
        comment="超时时间（秒）"
    )
    
    # 是否启用
    is_enabled: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="是否启用此测试用例"
    )
    
    # 关联关系
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="test_cases"
    )
    
    test_results: Mapped[list["TestResult"]] = relationship(
        "TestResult",
        back_populates="test_case",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<TestCase(id={self.id}, name='{self.name}', method={self.http_method}, path='{self.endpoint_path}')>"
    
    def get_full_url(self, base_url: str) -> str:
        """获取完整URL
        
        Args:
            base_url: 基础URL
            
        Returns:
            完整的请求URL
        """
        base_url = base_url.rstrip('/')
        path = self.endpoint_path.lstrip('/')
        return f"{base_url}/{path}"
    
    def has_dependencies(self) -> bool:
        """检查是否有依赖"""
        return bool(self.depends_on)
    
    def is_performance_test(self) -> bool:
        """检查是否为性能测试"""
        return self.test_type == TestCaseType.PERFORMANCE
    
    def get_request_summary(self) -> Dict[str, Any]:
        """获取请求摘要"""
        return {
            "method": self.http_method,
            "path": self.endpoint_path,
            "type": self.test_type,
            "priority": self.priority,
            "enabled": self.is_enabled,
            "has_auth": bool(self.auth_type),
            "has_body": bool(self.request_body),
            "expected_status": self.expected_status_code
        }
