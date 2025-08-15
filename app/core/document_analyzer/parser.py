"""
文档解析器

支持多种API文档格式的解析，包括OpenAPI、Swagger、Markdown等。
"""

import json
import yaml
import re
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import hashlib
from datetime import datetime

from .models import (
    DocumentType, DocumentFormat, ParsedDocument, DocumentMetadata,
    APIEndpoint, DocumentAnalysisResult
)
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """文档解析器
    
    支持多种API文档格式的自动检测和解析。
    """
    
    def __init__(self):
        """初始化文档解析器"""
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 支持的文件扩展名映射
        self.extension_mapping = {
            '.json': DocumentFormat.JSON,
            '.yaml': DocumentFormat.YAML,
            '.yml': DocumentFormat.YAML,
            '.md': DocumentFormat.MARKDOWN,
            '.txt': DocumentFormat.TEXT,
            '.xml': DocumentFormat.XML
        }
        
        self.logger.info("文档解析器初始化完成")
    
    def parse_document(self, content: str, file_path: Optional[str] = None) -> ParsedDocument:
        """解析文档
        
        Args:
            content: 文档内容
            file_path: 文件路径（可选）
            
        Returns:
            ParsedDocument: 解析结果
        """
        try:
            self.logger.info(f"开始解析文档: {file_path or 'content'}")
            
            # 检测文档格式
            document_format = self._detect_format(content, file_path)
            
            # 解析内容
            parsed_content, parse_errors = self._parse_content(content, document_format)
            
            # 检测文档类型
            document_type = self._detect_document_type(parsed_content, document_format)
            
            # 生成元数据
            metadata = self._generate_metadata(content, file_path)
            
            result = ParsedDocument(
                raw_content=content,
                parsed_content=parsed_content,
                document_type=document_type,
                document_format=document_format,
                metadata=metadata,
                parse_errors=parse_errors
            )
            
            self.logger.info(f"文档解析完成: 类型={document_type.value}, 格式={document_format.value}")
            return result
            
        except Exception as e:
            error_msg = f"文档解析失败: {str(e)}"
            self.logger.error(error_msg)
            
            return ParsedDocument(
                raw_content=content,
                parsed_content={},
                document_type=DocumentType.UNKNOWN,
                document_format=DocumentFormat.TEXT,
                metadata={},
                parse_errors=[error_msg]
            )
    
    def _detect_format(self, content: str, file_path: Optional[str] = None) -> DocumentFormat:
        """检测文档格式
        
        Args:
            content: 文档内容
            file_path: 文件路径
            
        Returns:
            DocumentFormat: 文档格式
        """
        # 首先根据文件扩展名判断
        if file_path:
            path = Path(file_path)
            extension = path.suffix.lower()
            if extension in self.extension_mapping:
                return self.extension_mapping[extension]
        
        # 根据内容特征判断
        content_stripped = content.strip()
        
        # JSON格式检测
        if content_stripped.startswith(('{', '[')):
            try:
                json.loads(content)
                return DocumentFormat.JSON
            except json.JSONDecodeError:
                pass
        
        # YAML格式检测
        if any(line.strip().endswith(':') for line in content_stripped.split('\n')[:10]):
            try:
                yaml.safe_load(content)
                return DocumentFormat.YAML
            except yaml.YAMLError:
                pass
        
        # Markdown格式检测
        if content_stripped.startswith('#') or '##' in content:
            return DocumentFormat.MARKDOWN
        
        # XML格式检测
        if content_stripped.startswith('<?xml') or content_stripped.startswith('<'):
            return DocumentFormat.XML
        
        # 默认为文本格式
        return DocumentFormat.TEXT
    
    def _parse_content(self, content: str, document_format: DocumentFormat) -> tuple[Dict[str, Any], List[str]]:
        """解析内容
        
        Args:
            content: 文档内容
            document_format: 文档格式
            
        Returns:
            tuple: (解析后的内容, 错误列表)
        """
        errors = []
        
        try:
            if document_format == DocumentFormat.JSON:
                return json.loads(content), errors
            
            elif document_format == DocumentFormat.YAML:
                return yaml.safe_load(content), errors
            
            elif document_format == DocumentFormat.MARKDOWN:
                return self._parse_markdown(content), errors
            
            elif document_format == DocumentFormat.XML:
                return self._parse_xml(content), errors
            
            else:
                # 文本格式，尝试提取结构化信息
                return self._parse_text(content), errors
                
        except json.JSONDecodeError as e:
            errors.append(f"JSON解析错误: {str(e)}")
        except yaml.YAMLError as e:
            errors.append(f"YAML解析错误: {str(e)}")
        except Exception as e:
            errors.append(f"内容解析错误: {str(e)}")
        
        return {}, errors
    
    def _parse_markdown(self, content: str) -> Dict[str, Any]:
        """解析Markdown内容
        
        Args:
            content: Markdown内容
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        result = {
            "type": "markdown",
            "sections": [],
            "headers": [],
            "code_blocks": [],
            "links": []
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 标题检测
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                
                header = {
                    "level": level,
                    "title": title,
                    "line": line
                }
                result["headers"].append(header)
                
                if current_section:
                    result["sections"].append(current_section)
                
                current_section = {
                    "title": title,
                    "level": level,
                    "content": []
                }
            
            # 代码块检测
            elif line.startswith('```'):
                language = line[3:].strip()
                result["code_blocks"].append({
                    "language": language,
                    "line": line
                })
            
            # 链接检测
            elif '[' in line and '](' in line:
                links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
                for text, url in links:
                    result["links"].append({
                        "text": text,
                        "url": url,
                        "line": line
                    })
            
            # 添加到当前节
            if current_section:
                current_section["content"].append(line)
        
        # 添加最后一个节
        if current_section:
            result["sections"].append(current_section)
        
        return result
    
    def _parse_xml(self, content: str) -> Dict[str, Any]:
        """解析XML内容
        
        Args:
            content: XML内容
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            def element_to_dict(element):
                result = {}
                
                # 添加属性
                if element.attrib:
                    result["@attributes"] = element.attrib
                
                # 添加文本内容
                if element.text and element.text.strip():
                    result["text"] = element.text.strip()
                
                # 添加子元素
                for child in element:
                    child_dict = element_to_dict(child)
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_dict)
                    else:
                        result[child.tag] = child_dict
                
                return result
            
            return {
                "type": "xml",
                "root_tag": root.tag,
                "content": element_to_dict(root)
            }
            
        except Exception as e:
            self.logger.warning(f"XML解析失败，使用文本解析: {e}")
            return self._parse_text(content)
    
    def _parse_text(self, content: str) -> Dict[str, Any]:
        """解析纯文本内容
        
        Args:
            content: 文本内容
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        lines = content.split('\n')
        
        return {
            "type": "text",
            "line_count": len(lines),
            "char_count": len(content),
            "word_count": len(content.split()),
            "lines": lines[:100]  # 只保留前100行
        }
    
    def _detect_document_type(self, parsed_content: Dict[str, Any], 
                            document_format: DocumentFormat) -> DocumentType:
        """检测文档类型
        
        Args:
            parsed_content: 解析后的内容
            document_format: 文档格式
            
        Returns:
            DocumentType: 文档类型
        """
        if not parsed_content:
            return DocumentType.UNKNOWN
        
        # OpenAPI/Swagger检测
        if isinstance(parsed_content, dict):
            # OpenAPI 3.x
            if "openapi" in parsed_content:
                if document_format == DocumentFormat.JSON:
                    return DocumentType.OPENAPI_JSON
                else:
                    return DocumentType.OPENAPI_YAML
            
            # Swagger 2.x
            elif "swagger" in parsed_content:
                if document_format == DocumentFormat.JSON:
                    return DocumentType.SWAGGER_JSON
                else:
                    return DocumentType.SWAGGER_YAML
            
            # Postman Collection
            elif "info" in parsed_content and "item" in parsed_content:
                return DocumentType.POSTMAN_COLLECTION
            
            # Insomnia Collection
            elif "resources" in parsed_content and "_type" in parsed_content:
                return DocumentType.INSOMNIA_COLLECTION
        
        # Markdown文档
        if document_format == DocumentFormat.MARKDOWN:
            return DocumentType.MARKDOWN
        
        return DocumentType.UNKNOWN
    
    def _generate_metadata(self, content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """生成文档元数据
        
        Args:
            content: 文档内容
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 元数据
        """
        metadata = {
            "content_size": len(content),
            "content_hash": hashlib.md5(content.encode()).hexdigest(),
            "line_count": len(content.split('\n')),
            "word_count": len(content.split()),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        if file_path:
            path = Path(file_path)
            metadata.update({
                "file_name": path.name,
                "file_extension": path.suffix,
                "file_stem": path.stem
            })
            
            # 如果文件存在，获取文件信息
            if path.exists():
                stat = path.stat()
                metadata.update({
                    "file_size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return metadata
    
    def extract_api_info(self, parsed_doc: ParsedDocument) -> DocumentAnalysisResult:
        """从解析的文档中提取API信息
        
        Args:
            parsed_doc: 解析后的文档
            
        Returns:
            DocumentAnalysisResult: 分析结果
        """
        try:
            self.logger.info("开始提取API信息")
            
            result = DocumentAnalysisResult(
                document_type=parsed_doc.document_type,
                document_format=parsed_doc.document_format,
                metadata=parsed_doc.metadata
            )
            
            if parsed_doc.document_type in [
                DocumentType.OPENAPI_JSON, DocumentType.OPENAPI_YAML,
                DocumentType.SWAGGER_JSON, DocumentType.SWAGGER_YAML
            ]:
                self._extract_openapi_info(parsed_doc.parsed_content, result)
            
            elif parsed_doc.document_type == DocumentType.POSTMAN_COLLECTION:
                self._extract_postman_info(parsed_doc.parsed_content, result)
            
            elif parsed_doc.document_type == DocumentType.MARKDOWN:
                self._extract_markdown_info(parsed_doc.parsed_content, result)
            
            result.total_endpoints = len(result.endpoints)
            
            self.logger.info(f"API信息提取完成: {result.total_endpoints}个端点")
            return result
            
        except Exception as e:
            error_msg = f"API信息提取失败: {str(e)}"
            self.logger.error(error_msg)
            
            result = DocumentAnalysisResult(
                document_type=parsed_doc.document_type,
                document_format=parsed_doc.document_format,
                metadata=parsed_doc.metadata
            )
            return result
    
    def _extract_openapi_info(self, content: Dict[str, Any], result: DocumentAnalysisResult):
        """提取OpenAPI/Swagger信息"""
        # 基本信息
        info = content.get("info", {})
        result.title = info.get("title")
        result.version = info.get("version")
        result.description = info.get("description")
        
        # 服务器信息
        servers = content.get("servers", [])
        if servers:
            result.base_url = servers[0].get("url")
        elif "host" in content:  # Swagger 2.x
            scheme = content.get("schemes", ["http"])[0]
            result.base_url = f"{scheme}://{content['host']}"
        
        # 安全方案
        result.security_schemes = content.get("securityDefinitions", {}) or content.get("components", {}).get("securitySchemes", {})
        
        # 数据模型
        result.schemas = content.get("definitions", {}) or content.get("components", {}).get("schemas", {})
        
        # 提取端点
        paths = content.get("paths", {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch", "head", "options"]:
                    endpoint = APIEndpoint(
                        path=path,
                        method=method.upper(),
                        summary=operation.get("summary"),
                        description=operation.get("description"),
                        tags=operation.get("tags", []),
                        parameters=operation.get("parameters", []),
                        request_body=operation.get("requestBody"),
                        responses=operation.get("responses", {}),
                        security=operation.get("security", []),
                        deprecated=operation.get("deprecated", False)
                    )
                    result.endpoints.append(endpoint)
    
    def _extract_postman_info(self, content: Dict[str, Any], result: DocumentAnalysisResult):
        """提取Postman Collection信息"""
        info = content.get("info", {})
        result.title = info.get("name")
        result.description = info.get("description")
        
        # 递归提取请求
        def extract_requests(items, folder_path=""):
            for item in items:
                if "request" in item:
                    # 这是一个请求
                    request = item["request"]
                    url = request.get("url", {})
                    
                    if isinstance(url, str):
                        path = url
                    else:
                        path = "/".join(url.get("path", []))
                    
                    endpoint = APIEndpoint(
                        path=f"{folder_path}/{path}" if folder_path else path,
                        method=request.get("method", "GET"),
                        summary=item.get("name"),
                        description=item.get("description"),
                        tags=[folder_path] if folder_path else []
                    )
                    result.endpoints.append(endpoint)
                
                elif "item" in item:
                    # 这是一个文件夹
                    folder_name = item.get("name", "")
                    new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                    extract_requests(item["item"], new_path)
        
        items = content.get("item", [])
        extract_requests(items)
    
    def _extract_markdown_info(self, content: Dict[str, Any], result: DocumentAnalysisResult):
        """提取Markdown文档信息"""
        headers = content.get("headers", [])
        
        # 尝试从标题中提取API信息
        if headers:
            result.title = headers[0].get("title")
        
        # 简单的API端点检测（基于常见模式）
        sections = content.get("sections", [])
        for section in sections:
            section_content = "\n".join(section.get("content", []))
            
            # 检测HTTP方法和路径
            http_patterns = [
                r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)',
                r'`(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)`',
                r'### (GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)'
            ]
            
            for pattern in http_patterns:
                matches = re.findall(pattern, section_content, re.IGNORECASE)
                for method, path in matches:
                    endpoint = APIEndpoint(
                        path=path,
                        method=method.upper(),
                        summary=section.get("title"),
                        description=section_content[:200] + "..." if len(section_content) > 200 else section_content
                    )
                    result.endpoints.append(endpoint)
