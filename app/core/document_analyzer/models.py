"""
文档分析器数据模型

定义文档分析过程中使用的数据结构和模型。
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """文档类型枚举"""
    OPENAPI_JSON = "openapi_json"
    OPENAPI_YAML = "openapi_yaml"
    SWAGGER_JSON = "swagger_json"
    SWAGGER_YAML = "swagger_yaml"
    MARKDOWN = "markdown"
    POSTMAN_COLLECTION = "postman_collection"
    INSOMNIA_COLLECTION = "insomnia_collection"
    UNKNOWN = "unknown"


class DocumentFormat(str, Enum):
    """文档格式枚举"""
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"
    XML = "xml"


class QualityLevel(str, Enum):
    """质量等级枚举"""
    EXCELLENT = "excellent"  # 90-100分
    GOOD = "good"           # 70-89分
    FAIR = "fair"           # 50-69分
    POOR = "poor"           # 30-49分
    VERY_POOR = "very_poor" # 0-29分


class IssueType(str, Enum):
    """问题类型枚举"""
    MISSING_FIELD = "missing_field"
    INVALID_FORMAT = "invalid_format"
    INCONSISTENT_DATA = "inconsistent_data"
    INCOMPLETE_INFO = "incomplete_info"
    DEPRECATED_USAGE = "deprecated_usage"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"


class IssueSeverity(str, Enum):
    """问题严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class DocumentMetadata:
    """文档元数据"""
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    encoding: Optional[str] = None
    content_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "encoding": self.encoding,
            "content_type": self.content_type
        }


class DocumentIssue(BaseModel):
    """文档问题"""
    type: IssueType = Field(description="问题类型")
    severity: IssueSeverity = Field(description="严重程度")
    message: str = Field(description="问题描述")
    location: Optional[str] = Field(default=None, description="问题位置")
    suggestion: Optional[str] = Field(default=None, description="修复建议")
    
    class Config:
        use_enum_values = True


class APIEndpoint(BaseModel):
    """API端点信息"""
    path: str = Field(description="端点路径")
    method: str = Field(description="HTTP方法")
    summary: Optional[str] = Field(default=None, description="端点摘要")
    description: Optional[str] = Field(default=None, description="端点描述")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="参数列表")
    request_body: Optional[Dict[str, Any]] = Field(default=None, description="请求体")
    responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="响应定义")
    security: List[Dict[str, Any]] = Field(default_factory=list, description="安全要求")
    deprecated: bool = Field(default=False, description="是否已弃用")
    
    @property
    def endpoint_id(self) -> str:
        """端点唯一标识"""
        return f"{self.method.upper()}:{self.path}"


class DocumentChunk(BaseModel):
    """文档分块"""
    chunk_id: str = Field(description="分块ID")
    content: str = Field(description="分块内容")
    chunk_type: str = Field(description="分块类型")
    token_count: int = Field(description="Token数量")
    endpoints: List[str] = Field(default_factory=list, description="包含的端点ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="分块元数据")
    
    class Config:
        arbitrary_types_allowed = True


class QualityMetrics(BaseModel):
    """质量指标"""
    overall_score: float = Field(description="总体评分", ge=0, le=100)
    completeness_score: float = Field(description="完整性评分", ge=0, le=100)
    consistency_score: float = Field(description="一致性评分", ge=0, le=100)
    clarity_score: float = Field(description="清晰度评分", ge=0, le=100)
    usability_score: float = Field(description="可用性评分", ge=0, le=100)
    
    @property
    def quality_level(self) -> QualityLevel:
        """质量等级"""
        if self.overall_score >= 90:
            return QualityLevel.EXCELLENT
        elif self.overall_score >= 70:
            return QualityLevel.GOOD
        elif self.overall_score >= 50:
            return QualityLevel.FAIR
        elif self.overall_score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.VERY_POOR


class DocumentAnalysisResult(BaseModel):
    """文档分析结果"""
    document_type: DocumentType = Field(description="文档类型")
    document_format: DocumentFormat = Field(description="文档格式")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    
    # 基本信息
    title: Optional[str] = Field(default=None, description="文档标题")
    version: Optional[str] = Field(default=None, description="API版本")
    description: Optional[str] = Field(default=None, description="文档描述")
    base_url: Optional[str] = Field(default=None, description="基础URL")
    
    # 端点信息
    endpoints: List[APIEndpoint] = Field(default_factory=list, description="API端点列表")
    total_endpoints: int = Field(default=0, description="端点总数")
    
    # 数据模型
    schemas: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="数据模型定义")
    
    # 安全信息
    security_schemes: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="安全方案")
    
    # 质量分析
    quality_metrics: Optional[QualityMetrics] = Field(default=None, description="质量指标")
    issues: List[DocumentIssue] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    
    # 分块信息
    chunks: List[DocumentChunk] = Field(default_factory=list, description="文档分块")
    
    # 分析元数据
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="分析时间")
    analysis_duration: Optional[float] = Field(default=None, description="分析耗时(秒)")
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @property
    def has_issues(self) -> bool:
        """是否有问题"""
        return len(self.issues) > 0
    
    @property
    def critical_issues(self) -> List[DocumentIssue]:
        """严重问题列表"""
        return [issue for issue in self.issues if issue.severity == IssueSeverity.CRITICAL]
    
    @property
    def high_issues(self) -> List[DocumentIssue]:
        """高优先级问题列表"""
        return [issue for issue in self.issues if issue.severity == IssueSeverity.HIGH]
    
    def get_issues_by_type(self, issue_type: IssueType) -> List[DocumentIssue]:
        """根据类型获取问题"""
        return [issue for issue in self.issues if issue.type == issue_type]
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[DocumentIssue]:
        """根据严重程度获取问题"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_endpoints_by_tag(self, tag: str) -> List[APIEndpoint]:
        """根据标签获取端点"""
        return [endpoint for endpoint in self.endpoints if tag in endpoint.tags]
    
    def get_endpoints_by_method(self, method: str) -> List[APIEndpoint]:
        """根据HTTP方法获取端点"""
        return [endpoint for endpoint in self.endpoints if endpoint.method.upper() == method.upper()]
    
    def get_deprecated_endpoints(self) -> List[APIEndpoint]:
        """获取已弃用的端点"""
        return [endpoint for endpoint in self.endpoints if endpoint.deprecated]


class ParsedDocument(BaseModel):
    """解析后的文档"""
    raw_content: str = Field(description="原始内容")
    parsed_content: Dict[str, Any] = Field(description="解析后的内容")
    document_type: DocumentType = Field(description="文档类型")
    document_format: DocumentFormat = Field(description="文档格式")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    parse_errors: List[str] = Field(default_factory=list, description="解析错误")
    
    class Config:
        use_enum_values = True
    
    @property
    def is_valid(self) -> bool:
        """是否解析成功"""
        return len(self.parse_errors) == 0
    
    @property
    def content_size(self) -> int:
        """内容大小"""
        return len(self.raw_content)


class ChunkingStrategy(BaseModel):
    """分块策略"""
    max_tokens: int = Field(default=4000, description="最大Token数")
    overlap_tokens: int = Field(default=200, description="重叠Token数")
    chunk_by_endpoint: bool = Field(default=True, description="按端点分块")
    preserve_structure: bool = Field(default=True, description="保持结构完整性")
    min_chunk_size: int = Field(default=100, description="最小分块大小")
    
    def validate_settings(self) -> List[str]:
        """验证设置"""
        errors = []
        
        if self.max_tokens <= 0:
            errors.append("max_tokens必须大于0")
        
        if self.overlap_tokens < 0:
            errors.append("overlap_tokens不能小于0")
        
        if self.overlap_tokens >= self.max_tokens:
            errors.append("overlap_tokens不能大于等于max_tokens")
        
        if self.min_chunk_size <= 0:
            errors.append("min_chunk_size必须大于0")
        
        if self.min_chunk_size >= self.max_tokens:
            errors.append("min_chunk_size不能大于等于max_tokens")
        
        return errors
