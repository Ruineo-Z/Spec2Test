"""
文档相关的Pydantic Schema

定义文档模型的输入输出Schema，用于API请求响应的数据验证。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.document import DocumentType, DocumentStatus


class DocumentBase(BaseModel):
    """文档基础Schema"""
    name: str = Field(..., description="文档名称", max_length=255)
    description: Optional[str] = Field(None, description="文档描述")
    document_type: DocumentType = Field(..., description="文档类型")


class DocumentCreate(DocumentBase):
    """创建文档Schema"""
    original_filename: Optional[str] = Field(None, description="原始文件名", max_length=255)
    content: Optional[str] = Field(None, description="文档内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")


class DocumentUpdate(BaseModel):
    """更新文档Schema"""
    name: Optional[str] = Field(None, description="文档名称", max_length=255)
    description: Optional[str] = Field(None, description="文档描述")
    status: Optional[DocumentStatus] = Field(None, description="文档状态")
    api_version: Optional[str] = Field(None, description="API版本", max_length=50)
    base_url: Optional[str] = Field(None, description="API基础URL", max_length=500)
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")


class DocumentResponse(DocumentBase):
    """文档响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="文档ID")
    status: DocumentStatus = Field(..., description="文档状态")
    original_filename: Optional[str] = Field(None, description="原始文件名")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    file_hash: Optional[str] = Field(None, description="文件哈希值")
    api_version: Optional[str] = Field(None, description="API版本")
    base_url: Optional[str] = Field(None, description="API基础URL")
    endpoints_count: Optional[int] = Field(None, description="API端点数量")
    parsed_at: Optional[datetime] = Field(None, description="解析完成时间")
    validated_at: Optional[datetime] = Field(None, description="验证完成时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DocumentDetail(DocumentResponse):
    """文档详情Schema"""
    content: Optional[str] = Field(None, description="文档内容")
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="解析后的数据")
    metadata: Optional[Dict[str, Any]] = Field(None, description="文档元数据")
    parse_error: Optional[str] = Field(None, description="解析错误信息")
    validation_errors: Optional[Dict[str, Any]] = Field(None, description="验证错误详情")


class DocumentList(BaseModel):
    """文档列表Schema"""
    items: List[DocumentResponse] = Field(..., description="文档列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class DocumentUpload(BaseModel):
    """文档上传Schema"""
    name: str = Field(..., description="文档名称", max_length=255)
    description: Optional[str] = Field(None, description="文档描述")
    document_type: DocumentType = Field(..., description="文档类型")
    auto_parse: bool = Field(True, description="是否自动解析")


class DocumentParseRequest(BaseModel):
    """文档解析请求Schema"""
    force_reparse: bool = Field(False, description="是否强制重新解析")
    validation_level: str = Field("standard", description="验证级别", pattern="^(basic|standard|strict)$")


class DocumentParseResponse(BaseModel):
    """文档解析响应Schema"""
    success: bool = Field(..., description="解析是否成功")
    message: str = Field(..., description="解析结果消息")
    endpoints_count: Optional[int] = Field(None, description="解析出的端点数量")
    warnings: Optional[List[str]] = Field(None, description="解析警告")
    errors: Optional[List[str]] = Field(None, description="解析错误")


class DocumentStats(BaseModel):
    """文档统计Schema"""
    total_documents: int = Field(..., description="文档总数")
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    by_status: Dict[str, int] = Field(..., description="按状态统计")
    recent_uploads: int = Field(..., description="最近上传数量")
    total_endpoints: int = Field(..., description="总端点数量")
