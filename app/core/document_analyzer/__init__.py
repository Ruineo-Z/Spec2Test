"""
文档分析器模块

提供完整的API文档分析功能，包括解析、质量检查、分块等。
"""

from .models import (
    DocumentType, DocumentFormat, QualityLevel, IssueType, IssueSeverity,
    DocumentMetadata, DocumentIssue, APIEndpoint, DocumentChunk,
    QualityMetrics, DocumentAnalysisResult, ParsedDocument, ChunkingStrategy
)
from .parser import DocumentParser
from .validator import DocumentValidator
from .chunker import DocumentChunker
from .analyzer import DocumentAnalyzer, AnalysisConfig

__all__ = [
    # 数据模型
    "DocumentType",
    "DocumentFormat", 
    "QualityLevel",
    "IssueType",
    "IssueSeverity",
    "DocumentMetadata",
    "DocumentIssue",
    "APIEndpoint",
    "DocumentChunk",
    "QualityMetrics",
    "DocumentAnalysisResult",
    "ParsedDocument",
    "ChunkingStrategy",
    
    # 核心组件
    "DocumentParser",
    "DocumentValidator",
    "DocumentChunker",
    "DocumentAnalyzer",
    "AnalysisConfig"
]
