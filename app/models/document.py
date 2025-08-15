"""
文档模型

定义API文档相关的数据模型，支持OpenAPI和Markdown格式。
包含文档内容、元数据、解析状态等信息。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, Integer, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from .base import BaseModel


class DocumentType(str, Enum):
    """文档类型枚举"""
    OPENAPI = "openapi"
    MARKDOWN = "markdown"
    POSTMAN = "postman"
    SWAGGER = "swagger"


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADED = "uploaded"          # 已上传
    PARSING = "parsing"            # 解析中
    PARSED = "parsed"              # 解析完成
    PARSE_FAILED = "parse_failed"  # 解析失败
    VALIDATED = "validated"        # 验证通过
    INVALID = "invalid"            # 验证失败


class Document(BaseModel):
    """文档模型
    
    存储API文档的基本信息、内容和解析状态。
    支持多种文档格式的统一管理。
    """
    
    __tablename__ = "documents"
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="文档名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文档描述"
    )
    
    # 文档类型和状态
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        nullable=False,
        comment="文档类型"
    )
    
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
        comment="文档状态"
    )
    
    # 文件信息
    original_filename: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="原始文件名"
    )
    
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="文件存储路径"
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="文件大小（字节）"
    )
    
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="文件SHA256哈希值"
    )
    
    # 文档内容
    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文档原始内容"
    )
    
    # 解析结果
    parsed_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="解析后的结构化数据"
    )
    
    # 元数据信息
    doc_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="文档元数据（版本、作者等）"
    )
    
    # API信息（针对OpenAPI文档）
    api_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="API版本"
    )
    
    base_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API基础URL"
    )
    
    endpoints_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=0,
        nullable=True,
        comment="API端点数量"
    )
    
    # 解析和验证信息
    parse_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="解析错误信息"
    )
    
    validation_errors: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="验证错误详情"
    )
    
    parsed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="解析完成时间"
    )
    
    validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="验证完成时间"
    )
    
    # 关联关系
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="document",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Document(id={self.id}, name='{self.name}', type={self.document_type}, status={self.status})>"
    
    def is_parsed(self) -> bool:
        """检查文档是否已解析"""
        return self.status in [DocumentStatus.PARSED, DocumentStatus.VALIDATED]
    
    def is_valid(self) -> bool:
        """检查文档是否验证通过"""
        return self.status == DocumentStatus.VALIDATED
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return self.status in [DocumentStatus.PARSE_FAILED, DocumentStatus.INVALID]
    
    def get_error_summary(self) -> Optional[str]:
        """获取错误摘要"""
        if self.parse_error:
            return f"解析错误: {self.parse_error}"
        elif self.validation_errors:
            error_count = len(self.validation_errors.get('errors', []))
            return f"验证错误: {error_count}个问题"
        return None
    
    def update_status(self, new_status: DocumentStatus, error_message: Optional[str] = None) -> None:
        """更新文档状态
        
        Args:
            new_status: 新状态
            error_message: 错误信息（如果有）
        """
        self.status = new_status
        
        if new_status == DocumentStatus.PARSED:
            self.parsed_at = datetime.now()
            self.parse_error = None
        elif new_status == DocumentStatus.VALIDATED:
            self.validated_at = datetime.now()
            self.validation_errors = None
        elif new_status == DocumentStatus.PARSE_FAILED:
            self.parse_error = error_message
        elif new_status == DocumentStatus.INVALID:
            if error_message:
                self.validation_errors = {"errors": [error_message]}
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息摘要"""
        return {
            "name": self.name,
            "type": self.document_type,
            "version": self.api_version,
            "base_url": self.base_url,
            "endpoints_count": self.endpoints_count or 0,
            "status": self.status,
            "parsed_at": self.parsed_at.isoformat() if self.parsed_at else None
        }
