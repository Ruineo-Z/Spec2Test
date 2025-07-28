"""OpenAPI文档解析器

实现OpenAPI/Swagger文档的解析和质量分析功能。
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Union, Optional
from datetime import datetime
import re

from loguru import logger

from app.core.models import (
    APIEndpoint, DocumentAnalysis, HttpMethod, DocumentQuality
)
from app.utils.exceptions import (
    DocumentParseError, DocumentValidationError
)


class OpenAPIParser:
    """OpenAPI文档解析器
    
    支持OpenAPI 3.0规范的文档解析、端点提取和质量分析。
    """
    
    SUPPORTED_VERSIONS = ['3.0.0', '3.0.1', '3.0.2', '3.0.3']
    SUPPORTED_METHODS = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
    
    def __init__(self):
        """初始化解析器"""
        self.logger = logger.bind(component="OpenAPIParser")
    
    def parse_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """解析OpenAPI文档文件
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            解析后的文档字典
            
        Raises:
            DocumentParseError: 文件解析失败
        """
        file_path = Path(file_path)
        
        try:
            # 检查文件是否存在
            if not file_path.exists():
                raise DocumentParseError(
                    f"File not found: {file_path}",
                    file_name=str(file_path)
                )
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"Parsing OpenAPI file: {file_path}")
            return self.parse_content(content)
            
        except DocumentParseError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path}: {e}")
            raise DocumentParseError(
                f"Failed to parse file: {e}",
                file_name=str(file_path),
                details={"error": str(e)}
            )
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """解析OpenAPI文档内容
        
        Args:
            content: 文档内容字符串
            
        Returns:
            解析后的文档字典
            
        Raises:
            DocumentParseError: 内容解析失败
        """
        try:
            # 尝试解析为YAML
            try:
                spec = yaml.safe_load(content)
                self.logger.debug("Content parsed as YAML")
            except yaml.YAMLError:
                # 如果YAML解析失败，尝试JSON
                try:
                    spec = json.loads(content)
                    self.logger.debug("Content parsed as JSON")
                except json.JSONDecodeError as json_err:
                    raise DocumentParseError(
                        f"Invalid YAML/JSON format: {json_err}",
                        details={"json_error": str(json_err)}
                    )
            
            # 验证基本结构
            self._validate_basic_structure(spec)
            
            return spec
            
        except DocumentParseError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse content: {e}")
            raise DocumentParseError(
                f"Content parsing failed: {e}",
                details={"error": str(e)}
            )
    
    def _validate_basic_structure(self, spec: Dict[str, Any]) -> None:
        """验证OpenAPI文档的基本结构
        
        Args:
            spec: 解析后的文档字典
            
        Raises:
            DocumentValidationError: 文档结构无效
        """
        # 检查必需字段
        required_fields = ['openapi', 'info', 'paths']
        missing_fields = [field for field in required_fields if field not in spec]
        
        if missing_fields:
            raise DocumentValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                validation_errors=missing_fields
            )
        
        # 检查OpenAPI版本
        openapi_version = spec.get('openapi', '')
        if not any(openapi_version.startswith(v) for v in self.SUPPORTED_VERSIONS):
            raise DocumentValidationError(
                f"Unsupported OpenAPI version: {openapi_version}. "
                f"Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}",
                details={"version": openapi_version}
            )
        
        # 检查info字段
        info = spec.get('info', {})
        if not isinstance(info, dict):
            raise DocumentValidationError("'info' field must be an object")
        
        info_required = ['title', 'version']
        missing_info = [field for field in info_required if field not in info]
        if missing_info:
            raise DocumentValidationError(
                f"Missing required info fields: {', '.join(missing_info)}",
                validation_errors=missing_info
            )
    
    def extract_endpoints(self, spec: Dict[str, Any]) -> List[APIEndpoint]:
        """从OpenAPI文档中提取API端点
        
        Args:
            spec: 解析后的文档字典
            
        Returns:
            API端点列表
            
        Raises:
            DocumentValidationError: 文档验证失败
        """
        try:
            # 验证文档结构
            self._validate_basic_structure(spec)
            
            endpoints = []
            paths = spec.get('paths', {})
            
            for path, path_item in paths.items():
                if not isinstance(path_item, dict):
                    continue
                
                for method, operation in path_item.items():
                    if method.lower() not in self.SUPPORTED_METHODS:
                        continue
                    
                    if not isinstance(operation, dict):
                        continue
                    
                    try:
                        endpoint = self._create_endpoint(
                            path, method.upper(), operation, spec
                        )
                        endpoints.append(endpoint)
                        
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to parse endpoint {method.upper()} {path}: {e}"
                        )
                        continue
            
            self.logger.info(f"Extracted {len(endpoints)} endpoints")
            return endpoints
            
        except DocumentValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to extract endpoints: {e}")
            raise DocumentValidationError(
                f"Endpoint extraction failed: {e}",
                details={"error": str(e)}
            )
    
    def _create_endpoint(
        self, 
        path: str, 
        method: str, 
        operation: Dict[str, Any],
        spec: Dict[str, Any]
    ) -> APIEndpoint:
        """创建API端点对象
        
        Args:
            path: API路径
            method: HTTP方法
            operation: 操作定义
            spec: 完整的OpenAPI规范
            
        Returns:
            API端点对象
        """
        # 基本信息
        endpoint = APIEndpoint(
            path=path,
            method=HttpMethod(method),
            summary=operation.get('summary'),
            description=operation.get('description'),
            tags=operation.get('tags', []),
            operation_id=operation.get('operationId'),
            deprecated=operation.get('deprecated', False)
        )
        
        # 提取参数
        parameters = operation.get('parameters', [])
        if isinstance(parameters, list):
            for param in parameters:
                if not isinstance(param, dict):
                    continue
                
                param_name = param.get('name')
                param_in = param.get('in')
                
                if not param_name or not param_in:
                    continue
                
                param_info = {
                    'name': param_name,
                    'required': param.get('required', False),
                    'schema': param.get('schema', {}),
                    'description': param.get('description')
                }
                
                if param_in == 'path':
                    endpoint.path_parameters[param_name] = param_info
                elif param_in == 'query':
                    endpoint.query_parameters[param_name] = param_info
                elif param_in == 'header':
                    endpoint.header_parameters[param_name] = param_info
        
        # 提取请求体
        request_body = operation.get('requestBody')
        if isinstance(request_body, dict):
            endpoint.request_body = request_body
            
            # 提取请求示例
            content = request_body.get('content', {})
            examples = []
            for media_type, media_info in content.items():
                if isinstance(media_info, dict):
                    media_examples = media_info.get('examples', {})
                    for example_name, example_data in media_examples.items():
                        if isinstance(example_data, dict):
                            examples.append({
                                'name': example_name,
                                'media_type': media_type,
                                'value': example_data.get('value'),
                                'summary': example_data.get('summary')
                            })
            endpoint.request_examples = examples
        
        # 提取响应
        responses = operation.get('responses', {})
        if isinstance(responses, dict):
            endpoint.responses = responses
            
            # 提取响应示例
            response_examples = {}
            for status_code, response_info in responses.items():
                if not isinstance(response_info, dict):
                    continue
                
                content = response_info.get('content', {})
                examples = []
                for media_type, media_info in content.items():
                    if isinstance(media_info, dict):
                        media_examples = media_info.get('examples', {})
                        for example_name, example_data in media_examples.items():
                            if isinstance(example_data, dict):
                                examples.append({
                                    'name': example_name,
                                    'media_type': media_type,
                                    'value': example_data.get('value'),
                                    'summary': example_data.get('summary')
                                })
                
                if examples:
                    response_examples[status_code] = examples
            
            endpoint.response_examples = response_examples
        
        # 提取安全要求
        security = operation.get('security', [])
        if isinstance(security, list):
            endpoint.security = security
        
        return endpoint
    
    def analyze_quality(self, spec: Dict[str, Any]) -> DocumentAnalysis:
        """分析OpenAPI文档质量
        
        Args:
            spec: 解析后的文档字典
            
        Returns:
            文档分析结果
            
        Raises:
            DocumentValidationError: 文档验证失败
        """
        try:
            # 提取端点信息
            endpoints = self.extract_endpoints(spec)
            
            self.logger.info("Starting document quality analysis")
            
            # 基本信息
            analysis = DocumentAnalysis(
                document_path="",  # 将在调用方设置
                document_type="openapi",
                total_endpoints=len(endpoints),
                documented_endpoints=0,
                missing_descriptions=0,
                missing_examples=0,
                missing_schemas=0,
                quality_score=0.0,
                quality_level=DocumentQuality.POOR,
                issues=[],
                suggestions=[],
                endpoints_by_method={},
                endpoints_by_tag={},
                analyzed_at=datetime.now()
            )
            
            # 分析完整性
            self._analyze_completeness(spec, endpoints, analysis)
            
            # 分析质量问题
            self._analyze_quality_issues(spec, endpoints, analysis)
            
            # 生成统计信息
            self._generate_statistics(endpoints, analysis)
            
            # 计算质量评分
            self._calculate_quality_score(analysis)
            
            # 生成改进建议
            self._generate_suggestions(analysis)
            
            self.logger.info(
                f"Quality analysis completed. Score: {analysis.quality_score}, "
                f"Level: {analysis.quality_level}"
            )
            
            return analysis
            
        except DocumentValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Quality analysis failed: {e}")
            raise DocumentValidationError(
                f"Quality analysis failed: {e}",
                details={"error": str(e)}
            )
    
    def _analyze_completeness(
        self, 
        spec: Dict[str, Any], 
        endpoints: List[APIEndpoint], 
        analysis: DocumentAnalysis
    ) -> None:
        """分析文档完整性"""
        documented_count = 0
        missing_descriptions = 0
        missing_examples = 0
        missing_schemas = 0
        
        for endpoint in endpoints:
            # 检查是否有描述
            has_description = bool(endpoint.summary or endpoint.description)
            if has_description:
                documented_count += 1
            else:
                missing_descriptions += 1
            
            # 检查是否有示例
            has_examples = bool(
                endpoint.request_examples or 
                any(endpoint.response_examples.values())
            )
            if not has_examples:
                missing_examples += 1
            
            # 检查是否有模式定义
            has_schemas = self._has_schemas(endpoint)
            if not has_schemas:
                missing_schemas += 1
        
        # 设置分析结果的属性
        analysis.documented_endpoints = documented_count
        analysis.missing_descriptions = missing_descriptions
        analysis.missing_examples = missing_examples
        analysis.missing_schemas = missing_schemas
    
    def _has_schemas(self, endpoint: APIEndpoint) -> bool:
        """检查端点是否有模式定义"""
        # 检查请求体模式
        if endpoint.request_body:
            content = endpoint.request_body.get('content', {})
            for media_info in content.values():
                if isinstance(media_info, dict) and 'schema' in media_info:
                    return True
        
        # 检查响应模式
        for response_info in endpoint.responses.values():
            if isinstance(response_info, dict):
                content = response_info.get('content', {})
                for media_info in content.values():
                    if isinstance(media_info, dict) and 'schema' in media_info:
                        return True
        
        return False
    
    def _analyze_quality_issues(
        self, 
        spec: Dict[str, Any], 
        endpoints: List[APIEndpoint], 
        analysis: DocumentAnalysis
    ) -> None:
        """分析质量问题"""
        issues = []
        
        # 检查基本信息
        info = spec.get('info', {})
        if not info.get('description'):
            issues.append({
                'type': 'missing_info_description',
                'severity': 'medium',
                'message': 'API description is missing in info section'
            })
        
        if not info.get('contact'):
            issues.append({
                'type': 'missing_contact',
                'severity': 'low',
                'message': 'Contact information is missing'
            })
        
        # 检查服务器配置
        if not spec.get('servers'):
            issues.append({
                'type': 'missing_servers',
                'severity': 'medium',
                'message': 'Server configuration is missing'
            })
        
        # 检查组件定义
        if not spec.get('components'):
            issues.append({
                'type': 'missing_components',
                'severity': 'medium',
                'message': 'Components section is missing'
            })
        
        # 检查端点问题
        for endpoint in endpoints:
            endpoint_id = f"{endpoint.method.value} {endpoint.path}"
            
            # 检查缺少描述
            if not endpoint.summary and not endpoint.description:
                issues.append({
                    'type': 'missing_endpoint_description',
                    'severity': 'medium',
                    'message': f'Endpoint {endpoint_id} lacks description',
                    'endpoint': endpoint_id
                })
            
            # 检查缺少标签
            if not endpoint.tags:
                issues.append({
                    'type': 'missing_tags',
                    'severity': 'low',
                    'message': f'Endpoint {endpoint_id} has no tags',
                    'endpoint': endpoint_id
                })
            
            # 检查缺少错误响应
            response_codes = set(endpoint.responses.keys())
            if not any(code.startswith('4') or code.startswith('5') for code in response_codes):
                issues.append({
                    'type': 'missing_error_responses',
                    'severity': 'medium',
                    'message': f'Endpoint {endpoint_id} lacks error response definitions',
                    'endpoint': endpoint_id
                })
        
        analysis.issues = issues
    
    def _generate_statistics(
        self, 
        endpoints: List[APIEndpoint], 
        analysis: DocumentAnalysis
    ) -> None:
        """生成统计信息"""
        # 按方法统计
        methods_count = {}
        for endpoint in endpoints:
            method = endpoint.method.value
            methods_count[method] = methods_count.get(method, 0) + 1
        analysis.endpoints_by_method = methods_count
        
        # 按标签统计
        tags_count = {}
        for endpoint in endpoints:
            for tag in endpoint.tags:
                tags_count[tag] = tags_count.get(tag, 0) + 1
        analysis.endpoints_by_tag = tags_count
    
    def _calculate_quality_score(self, analysis: DocumentAnalysis) -> None:
        """计算质量评分"""
        if analysis.total_endpoints == 0:
            analysis.quality_score = 0.0
            analysis.quality_level = DocumentQuality.POOR
            return
        
        score = 0.0
        
        # 完整性评分 (40%)
        completeness_ratio = analysis.documented_endpoints / analysis.total_endpoints
        score += completeness_ratio * 40
        
        # 示例覆盖率 (20%)
        examples_ratio = max(0, 1 - (analysis.missing_examples / analysis.total_endpoints))
        score += examples_ratio * 20
        
        # 模式定义覆盖率 (20%)
        schemas_ratio = max(0, 1 - (analysis.missing_schemas / analysis.total_endpoints))
        score += schemas_ratio * 20
        
        # 问题扣分 (20%)
        issue_penalty = 0
        for issue in analysis.issues:
            severity = issue.get('severity', 'low')
            if severity == 'high':
                issue_penalty += 5
            elif severity == 'medium':
                issue_penalty += 2
            else:  # low
                issue_penalty += 1
        
        # 最多扣20分
        issue_penalty = min(issue_penalty, 20)
        score += (20 - issue_penalty)
        
        # 确保评分在0-100之间
        analysis.quality_score = max(0.0, min(100.0, score))
        
        # 确定质量等级
        if analysis.quality_score >= 90:
            analysis.quality_level = DocumentQuality.EXCELLENT
        elif analysis.quality_score >= 70:
            analysis.quality_level = DocumentQuality.GOOD
        elif analysis.quality_score >= 50:
            analysis.quality_level = DocumentQuality.FAIR
        else:
            analysis.quality_level = DocumentQuality.POOR
    
    def _generate_suggestions(self, analysis: DocumentAnalysis) -> None:
        """生成改进建议"""
        suggestions = []
        
        # 基于缺失描述的建议
        if analysis.missing_descriptions > 0:
            suggestions.append(
                f"Add descriptions to {analysis.missing_descriptions} endpoints "
                "to improve documentation clarity"
            )
        
        # 基于缺失示例的建议
        if analysis.missing_examples > 0:
            suggestions.append(
                f"Add request/response examples to {analysis.missing_examples} endpoints "
                "to help developers understand the API"
            )
        
        # 基于缺失模式的建议
        if analysis.missing_schemas > 0:
            suggestions.append(
                f"Define schemas for {analysis.missing_schemas} endpoints "
                "to improve type safety and validation"
            )
        
        # 基于问题的建议
        high_severity_issues = [i for i in analysis.issues if i.get('severity') == 'high']
        if high_severity_issues:
            suggestions.append(
                f"Address {len(high_severity_issues)} high-severity issues "
                "to improve API reliability"
            )
        
        medium_severity_issues = [i for i in analysis.issues if i.get('severity') == 'medium']
        if medium_severity_issues:
            suggestions.append(
                f"Consider fixing {len(medium_severity_issues)} medium-severity issues "
                "to enhance documentation quality"
            )
        
        # 通用建议
        if analysis.quality_score < 70:
            suggestions.append(
                "Consider using OpenAPI linting tools to identify and fix "
                "additional documentation issues"
            )
        
        analysis.suggestions = suggestions