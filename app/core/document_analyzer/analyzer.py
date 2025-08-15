"""
文档分析器主类

整合文档解析、质量检查、分块等功能的主要分析器。
"""

import time
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .models import DocumentAnalysisResult, ChunkingStrategy
from .parser import DocumentParser
from .validator import DocumentValidator
from .chunker import DocumentChunker
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentAnalyzer:
    """文档分析器主类
    
    提供完整的API文档分析功能，包括解析、质量检查、分块等。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化文档分析器
        
        Args:
            config: 分析器配置
        """
        self.config = config or {}
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 初始化子组件
        self.parser = DocumentParser()
        self.validator = DocumentValidator()
        self.chunker = DocumentChunker()
        
        # 配置参数
        self.enable_validation = self.config.get("enable_validation", True)
        self.enable_chunking = self.config.get("enable_chunking", False)
        self.default_chunking_strategy = ChunkingStrategy(
            max_tokens=self.config.get("max_tokens", 4000),
            overlap_tokens=self.config.get("overlap_tokens", 200),
            chunk_by_endpoint=self.config.get("chunk_by_endpoint", True)
        )
        
        self.logger.info("文档分析器初始化完成")
    
    def analyze_file(self, file_path: Union[str, Path], 
                    chunking_strategy: Optional[ChunkingStrategy] = None) -> DocumentAnalysisResult:
        """分析文档文件
        
        Args:
            file_path: 文档文件路径
            chunking_strategy: 分块策略（可选）
            
        Returns:
            DocumentAnalysisResult: 分析结果
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            self.logger.info(f"开始分析文档文件: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分析内容
            return self.analyze_content(content, str(file_path), chunking_strategy)
            
        except Exception as e:
            error_msg = f"文档文件分析失败: {str(e)}"
            self.logger.error(error_msg)
            
            # 返回错误结果
            from .models import DocumentIssue, IssueType, IssueSeverity

            result = DocumentAnalysisResult(
                document_type="unknown",
                document_format="text"
            )
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INVALID_FORMAT,
                    severity=IssueSeverity.CRITICAL,
                    message=error_msg,
                    suggestion="请检查文件路径和格式是否正确"
                )
            )
            
            return result
    
    def analyze_content(self, content: str, 
                       source_name: Optional[str] = None,
                       chunking_strategy: Optional[ChunkingStrategy] = None) -> DocumentAnalysisResult:
        """分析文档内容
        
        Args:
            content: 文档内容
            source_name: 来源名称（可选）
            chunking_strategy: 分块策略（可选）
            
        Returns:
            DocumentAnalysisResult: 分析结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始分析文档内容: {source_name or 'content'}")
            
            # 1. 解析文档
            parsed_doc = self.parser.parse_document(content, source_name)
            
            if not parsed_doc.is_valid:
                self.logger.warning(f"文档解析有错误: {parsed_doc.parse_errors}")
            
            # 2. 提取API信息
            analysis_result = self.parser.extract_api_info(parsed_doc)
            
            # 3. 质量检查
            if self.enable_validation:
                analysis_result = self.validator.validate_document(analysis_result)
            
            # 4. 文档分块
            if self.enable_chunking:
                strategy = chunking_strategy or self.default_chunking_strategy
                analysis_result = self.chunker.chunk_document(analysis_result, strategy)
            
            # 5. 设置分析时间
            end_time = time.time()
            analysis_result.analysis_duration = end_time - start_time
            
            self.logger.info(f"文档分析完成: 耗时{analysis_result.analysis_duration:.2f}秒")
            
            return analysis_result
            
        except Exception as e:
            error_msg = f"文档内容分析失败: {str(e)}"
            self.logger.error(error_msg)
            
            # 返回错误结果
            from .models import DocumentIssue, IssueType, IssueSeverity

            result = DocumentAnalysisResult(
                document_type="unknown",
                document_format="text"
            )
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INVALID_FORMAT,
                    severity=IssueSeverity.CRITICAL,
                    message=error_msg,
                    suggestion="请检查文档内容格式是否正确"
                )
            )
            
            end_time = time.time()
            result.analysis_duration = end_time - start_time
            
            return result
    
    def analyze_url(self, url: str, 
                   chunking_strategy: Optional[ChunkingStrategy] = None) -> DocumentAnalysisResult:
        """分析在线文档
        
        Args:
            url: 文档URL
            chunking_strategy: 分块策略（可选）
            
        Returns:
            DocumentAnalysisResult: 分析结果
        """
        try:
            self.logger.info(f"开始分析在线文档: {url}")
            
            # 使用HTTP客户端获取内容
            from app.core.shared.http import HTTPClient
            
            http_client = HTTPClient()
            response = http_client.get(url)
            
            if not response.success:
                raise Exception(f"无法获取文档内容: {response.error_message}")
            
            content = response.content
            if not content:
                raise Exception("文档内容为空")
            
            # 分析内容
            return self.analyze_content(content, url, chunking_strategy)
            
        except Exception as e:
            error_msg = f"在线文档分析失败: {str(e)}"
            self.logger.error(error_msg)
            
            # 返回错误结果
            from .models import DocumentIssue, IssueType, IssueSeverity

            result = DocumentAnalysisResult(
                document_type="unknown",
                document_format="text"
            )
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INVALID_FORMAT,
                    severity=IssueSeverity.CRITICAL,
                    message=error_msg,
                    suggestion="请检查URL是否可访问"
                )
            )
            
            return result
    
    def get_analysis_summary(self, result: DocumentAnalysisResult) -> Dict[str, Any]:
        """获取分析摘要
        
        Args:
            result: 分析结果
            
        Returns:
            Dict[str, Any]: 分析摘要
        """
        summary = {
            "document_info": {
                "type": result.document_type,
                "format": result.document_format,
                "title": result.title,
                "version": result.version,
                "base_url": result.base_url
            },
            "api_info": {
                "total_endpoints": result.total_endpoints,
                "methods": self._get_method_distribution(result),
                "tags": self._get_tag_distribution(result),
                "deprecated_count": len(result.get_deprecated_endpoints())
            },
            "quality_info": {
                "overall_score": result.quality_metrics.overall_score if result.quality_metrics else 0,
                "quality_level": result.quality_metrics.quality_level if result.quality_metrics else "unknown",
                "total_issues": len(result.issues),
                "critical_issues": len(result.critical_issues),
                "high_issues": len(result.high_issues)
            },
            "analysis_info": {
                "analysis_duration": result.analysis_duration,
                "chunk_count": len(result.chunks),
                "suggestions_count": len(result.suggestions)
            }
        }
        
        return summary
    
    def _get_method_distribution(self, result: DocumentAnalysisResult) -> Dict[str, int]:
        """获取HTTP方法分布"""
        method_count = {}
        for endpoint in result.endpoints:
            method = endpoint.method.upper()
            method_count[method] = method_count.get(method, 0) + 1
        
        return method_count
    
    def _get_tag_distribution(self, result: DocumentAnalysisResult) -> Dict[str, int]:
        """获取标签分布"""
        tag_count = {}
        for endpoint in result.endpoints:
            for tag in endpoint.tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        return tag_count
    
    def export_analysis_report(self, result: DocumentAnalysisResult, 
                              output_path: Union[str, Path],
                              format: str = "json") -> bool:
        """导出分析报告
        
        Args:
            result: 分析结果
            output_path: 输出路径
            format: 导出格式（json/markdown）
            
        Returns:
            bool: 是否成功
        """
        try:
            output_path = Path(output_path)
            
            if format.lower() == "json":
                return self._export_json_report(result, output_path)
            elif format.lower() == "markdown":
                return self._export_markdown_report(result, output_path)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
        except Exception as e:
            self.logger.error(f"导出分析报告失败: {e}")
            return False
    
    def _export_json_report(self, result: DocumentAnalysisResult, output_path: Path) -> bool:
        """导出JSON格式报告"""
        import json
        
        try:
            # 转换为可序列化的字典
            report_data = result.model_dump()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"JSON报告导出成功: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON报告导出失败: {e}")
            return False
    
    def _export_markdown_report(self, result: DocumentAnalysisResult, output_path: Path) -> bool:
        """导出Markdown格式报告"""
        try:
            content = []
            
            # 标题
            content.append(f"# API文档分析报告")
            content.append(f"**分析时间**: {result.analysis_timestamp}")
            content.append("")
            
            # 基本信息
            content.append("## 基本信息")
            content.append(f"- **文档类型**: {result.document_type}")
            content.append(f"- **文档格式**: {result.document_format}")
            if result.title:
                content.append(f"- **标题**: {result.title}")
            if result.version:
                content.append(f"- **版本**: {result.version}")
            if result.base_url:
                content.append(f"- **基础URL**: {result.base_url}")
            content.append("")
            
            # API统计
            content.append("## API统计")
            content.append(f"- **端点总数**: {result.total_endpoints}")
            
            method_dist = self._get_method_distribution(result)
            if method_dist:
                content.append("- **HTTP方法分布**:")
                for method, count in method_dist.items():
                    content.append(f"  - {method}: {count}")
            content.append("")
            
            # 质量评估
            if result.quality_metrics:
                content.append("## 质量评估")
                content.append(f"- **总体评分**: {result.quality_metrics.overall_score:.1f}/100")
                content.append(f"- **质量等级**: {result.quality_metrics.quality_level}")
                content.append(f"- **完整性**: {result.quality_metrics.completeness_score:.1f}/100")
                content.append(f"- **一致性**: {result.quality_metrics.consistency_score:.1f}/100")
                content.append("")
            
            # 问题列表
            if result.issues:
                content.append("## 发现的问题")
                for issue in result.issues:
                    severity_icon = {
                        "critical": "🔴",
                        "high": "🟠", 
                        "medium": "🟡",
                        "low": "🟢",
                        "info": "ℹ️"
                    }.get(issue.severity, "❓")
                    
                    content.append(f"### {severity_icon} {issue.message}")
                    if issue.location:
                        content.append(f"**位置**: {issue.location}")
                    if issue.suggestion:
                        content.append(f"**建议**: {issue.suggestion}")
                    content.append("")
            
            # 改进建议
            if result.suggestions:
                content.append("## 改进建议")
                for i, suggestion in enumerate(result.suggestions, 1):
                    content.append(f"{i}. {suggestion}")
                content.append("")
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.info(f"Markdown报告导出成功: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Markdown报告导出失败: {e}")
            return False
