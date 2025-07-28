"""数据库ORM模型

定义与数据库表对应的SQLAlchemy模型。
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, JSON,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from app.core.database import Base
from app.core.models import TestCaseType, HttpMethod, TestStatus, DocumentQuality


class DocumentModel(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100))
    
    # 文档类型和版本
    document_type = Column(String(50), nullable=False)  # openapi, swagger, etc.
    version = Column(String(20))  # 3.0.0, 2.0, etc.
    
    # 质量评估
    quality_score = Column(Float, default=0.0)
    quality_level = Column(SQLEnum(DocumentQuality), default=DocumentQuality.POOR)
    
    # 统计信息
    total_endpoints = Column(Integer, default=0)
    documented_endpoints = Column(Integer, default=0)
    missing_descriptions = Column(Integer, default=0)
    missing_examples = Column(Integer, default=0)
    missing_schemas = Column(Integer, default=0)
    
    # 分析结果
    analysis_result = Column(JSON)  # 存储完整的分析结果
    issues = Column(JSON)  # 发现的问题列表
    suggestions = Column(JSON)  # 改进建议列表
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    analyzed_at = Column(DateTime(timezone=True))
    
    # 关系
    endpoints = relationship("EndpointModel", back_populates="document", cascade="all, delete-orphan")
    test_suites = relationship("TestSuiteModel", back_populates="document")
    
    # 索引
    __table_args__ = (
        Index('idx_document_hash_type', 'file_hash', 'document_type'),
        Index('idx_document_quality', 'quality_level', 'quality_score'),
    )


class EndpointModel(Base):
    """API端点模型"""
    __tablename__ = "endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # 端点信息
    path = Column(String(500), nullable=False, index=True)
    method = Column(SQLEnum(HttpMethod), nullable=False)
    operation_id = Column(String(255), index=True)
    
    # 描述信息
    summary = Column(String(500))
    description = Column(Text)
    tags = Column(JSON)  # 标签列表
    
    # 参数定义
    path_parameters = Column(JSON)
    query_parameters = Column(JSON)
    header_parameters = Column(JSON)
    
    # 请求体
    request_body = Column(JSON)
    request_examples = Column(JSON)
    
    # 响应定义
    responses = Column(JSON)
    response_examples = Column(JSON)
    
    # 安全和其他
    security = Column(JSON)
    deprecated = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    document = relationship("DocumentModel", back_populates="endpoints")
    test_cases = relationship("TestCaseModel", back_populates="endpoint")
    
    # 索引
    __table_args__ = (
        Index('idx_endpoint_path_method', 'path', 'method'),
        Index('idx_endpoint_document', 'document_id'),
        UniqueConstraint('document_id', 'path', 'method', name='uq_endpoint_path_method'),
    )


class TestSuiteModel(Base):
    """测试套件模型"""
    __tablename__ = "test_suites"
    
    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 关联文档
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    # 配置信息
    base_url = Column(String(500))
    environment = Column(String(50), default="test")
    timeout = Column(Integer, default=30)
    
    # 执行配置
    parallel_execution = Column(Boolean, default=False)
    max_workers = Column(Integer, default=4)
    retry_count = Column(Integer, default=0)
    
    # 元数据
    tags = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    document = relationship("DocumentModel", back_populates="test_suites")
    test_cases = relationship("TestCaseModel", back_populates="test_suite", cascade="all, delete-orphan")
    test_reports = relationship("TestReportModel", back_populates="test_suite")
    
    # 索引
    __table_args__ = (
        Index('idx_test_suite_environment', 'environment'),
        Index('idx_test_suite_document', 'document_id'),
    )


class TestCaseModel(Base):
    """测试用例模型"""
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(TestCaseType), nullable=False)
    
    # 关联
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id"), nullable=False)
    
    # 测试数据
    test_data = Column(JSON)
    expected_status_code = Column(Integer, default=200)
    expected_response = Column(JSON)
    
    # 条件和步骤
    preconditions = Column(JSON)
    postconditions = Column(JSON)
    test_steps = Column(JSON)
    
    # 元数据
    priority = Column(Integer, default=1)
    tags = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    test_suite = relationship("TestSuiteModel", back_populates="test_cases")
    endpoint = relationship("EndpointModel", back_populates="test_cases")
    test_results = relationship("TestResultModel", back_populates="test_case")
    
    # 索引
    __table_args__ = (
        Index('idx_test_case_type_priority', 'type', 'priority'),
        Index('idx_test_case_suite', 'test_suite_id'),
        Index('idx_test_case_endpoint', 'endpoint_id'),
    )


class TestResultModel(Base):
    """测试结果模型"""
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # 关联
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    test_report_id = Column(Integer, ForeignKey("test_reports.id"))
    
    # 执行状态
    status = Column(SQLEnum(TestStatus), nullable=False)
    
    # 执行时间
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration = Column(Float)  # 秒
    
    # 结果详情
    actual_status_code = Column(Integer)
    actual_response = Column(JSON)
    
    # 错误信息
    error_message = Column(Text)
    error_details = Column(JSON)
    stack_trace = Column(Text)
    
    # 断言结果
    assertions = Column(JSON)
    
    # 性能指标
    response_time = Column(Float)  # 毫秒
    memory_usage = Column(Float)  # MB
    
    # 附件
    screenshots = Column(JSON)  # 截图路径列表
    logs = Column(JSON)  # 日志信息列表
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    test_case = relationship("TestCaseModel", back_populates="test_results")
    test_report = relationship("TestReportModel", back_populates="test_results")
    
    # 索引
    __table_args__ = (
        Index('idx_test_result_status_time', 'status', 'start_time'),
        Index('idx_test_result_case', 'test_case_id'),
        Index('idx_test_result_report', 'test_report_id'),
    )


class TestReportModel(Base):
    """测试报告模型"""
    __tablename__ = "test_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # 关联
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    
    # 执行信息
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration = Column(Float)  # 秒
    
    # 统计信息
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)
    
    # 成功率
    success_rate = Column(Float, default=0.0)
    
    # 性能统计
    avg_response_time = Column(Float)
    max_response_time = Column(Float)
    min_response_time = Column(Float)
    
    # 环境信息
    environment = Column(String(50), default="test")
    base_url = Column(String(500))
    
    # 报告文件路径
    html_report_path = Column(String(500))
    json_report_path = Column(String(500))
    xml_report_path = Column(String(500))
    
    # 元数据
    tags = Column(JSON)
    
    # 时间戳
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    test_suite = relationship("TestSuiteModel", back_populates="test_reports")
    test_results = relationship("TestResultModel", back_populates="test_report", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_test_report_suite_time', 'test_suite_id', 'start_time'),
        Index('idx_test_report_success_rate', 'success_rate'),
        Index('idx_test_report_environment', 'environment'),
    )


class ExecutionHistoryModel(Base):
    """执行历史模型"""
    __tablename__ = "execution_history"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # 执行类型
    execution_type = Column(String(50), nullable=False)  # test_suite, single_test, etc.
    target_id = Column(String(255), nullable=False)  # 目标ID（测试套件ID或测试用例ID）
    
    # 执行状态
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    
    # 执行信息
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    duration = Column(Float)
    
    # 执行参数
    execution_params = Column(JSON)
    
    # 结果摘要
    result_summary = Column(JSON)
    
    # 错误信息
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 索引
    __table_args__ = (
        Index('idx_execution_type_status', 'execution_type', 'status'),
        Index('idx_execution_target', 'target_id'),
        Index('idx_execution_time', 'start_time'),
    )


# 导出所有模型
__all__ = [
    "DocumentModel",
    "EndpointModel",
    "TestSuiteModel",
    "TestCaseModel",
    "TestResultModel",
    "TestReportModel",
    "ExecutionHistoryModel",
]