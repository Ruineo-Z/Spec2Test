"""OpenAPI文档解析器

实现OpenAPI/Swagger文档的解析和质量分析功能。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

import yaml
from loguru import logger

from app.core.models import (
    APIEndpoint,
    DocumentAnalysis,
    DocumentQuality,
    HttpMethod,
    RiskCategory,
    RiskItem,
    RiskLevel,
)
from app.utils.exceptions import DocumentParseError, DocumentValidationError


class OpenAPIParser:
    """OpenAPI文档解析器

    支持OpenAPI 3.0规范的文档解析、端点提取和质量分析。
    """

    SUPPORTED_VERSIONS = ["3.0.0", "3.0.1", "3.0.2", "3.0.3"]
    SUPPORTED_METHODS = ["get", "post", "put", "delete", "patch", "head", "options"]

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
                    f"File not found: {file_path}", file_name=str(file_path)
                )

            # 读取文件内容
            with open(file_path, "r", encoding="utf-8") as f:
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
                details={"error": str(e)},
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
                        details={"json_error": str(json_err)},
                    )

            # 验证基本结构
            self._validate_basic_structure(spec)

            return spec

        except DocumentParseError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to parse content: {e}")
            raise DocumentParseError(
                f"Content parsing failed: {e}", details={"error": str(e)}
            )

    def _validate_basic_structure(self, spec: Dict[str, Any]) -> None:
        """验证OpenAPI文档的基本结构

        Args:
            spec: 解析后的文档字典

        Raises:
            DocumentValidationError: 文档结构无效
        """
        # 检查必需字段
        required_fields = ["openapi", "info", "paths"]
        missing_fields = [field for field in required_fields if field not in spec]

        if missing_fields:
            raise DocumentValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                validation_errors=missing_fields,
            )

        # 检查OpenAPI版本
        openapi_version = spec.get("openapi", "")
        if not any(openapi_version.startswith(v) for v in self.SUPPORTED_VERSIONS):
            raise DocumentValidationError(
                f"Unsupported OpenAPI version: {openapi_version}. "
                f"Supported versions: {', '.join(self.SUPPORTED_VERSIONS)}",
                details={"version": openapi_version},
            )

        # 检查info字段
        info = spec.get("info", {})
        if not isinstance(info, dict):
            raise DocumentValidationError("'info' field must be an object")

        info_required = ["title", "version"]
        missing_info = [field for field in info_required if field not in info]
        if missing_info:
            raise DocumentValidationError(
                f"Missing required info fields: {', '.join(missing_info)}",
                validation_errors=missing_info,
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
            paths = spec.get("paths", {})

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
                f"Endpoint extraction failed: {e}", details={"error": str(e)}
            )

    def _create_endpoint(
        self, path: str, method: str, operation: Dict[str, Any], spec: Dict[str, Any]
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
            summary=operation.get("summary"),
            description=operation.get("description"),
            tags=operation.get("tags", []),
            operation_id=operation.get("operationId"),
            deprecated=operation.get("deprecated", False),
        )

        # 提取参数
        parameters = operation.get("parameters", [])
        if isinstance(parameters, list):
            for param in parameters:
                if not isinstance(param, dict):
                    continue

                param_name = param.get("name")
                param_in = param.get("in")

                if not param_name or not param_in:
                    continue

                param_info = {
                    "name": param_name,
                    "required": param.get("required", False),
                    "schema": param.get("schema", {}),
                    "description": param.get("description"),
                }

                if param_in == "path":
                    endpoint.path_parameters[param_name] = param_info
                elif param_in == "query":
                    endpoint.query_parameters[param_name] = param_info
                elif param_in == "header":
                    endpoint.header_parameters[param_name] = param_info

        # 提取请求体
        request_body = operation.get("requestBody")
        if isinstance(request_body, dict):
            endpoint.request_body = request_body

            # 提取请求示例
            content = request_body.get("content", {})
            examples = []
            for media_type, media_info in content.items():
                if isinstance(media_info, dict):
                    media_examples = media_info.get("examples", {})
                    for example_name, example_data in media_examples.items():
                        if isinstance(example_data, dict):
                            examples.append(
                                {
                                    "name": example_name,
                                    "media_type": media_type,
                                    "value": example_data.get("value"),
                                    "summary": example_data.get("summary"),
                                }
                            )
            endpoint.request_examples = examples

        # 提取响应
        responses = operation.get("responses", {})
        if isinstance(responses, dict):
            endpoint.responses = responses

            # 提取响应示例
            response_examples = {}
            for status_code, response_info in responses.items():
                if not isinstance(response_info, dict):
                    continue

                content = response_info.get("content", {})
                examples = []
                for media_type, media_info in content.items():
                    if isinstance(media_info, dict):
                        media_examples = media_info.get("examples", {})
                        for example_name, example_data in media_examples.items():
                            if isinstance(example_data, dict):
                                examples.append(
                                    {
                                        "name": example_name,
                                        "media_type": media_type,
                                        "value": example_data.get("value"),
                                        "summary": example_data.get("summary"),
                                    }
                                )

                if examples:
                    response_examples[status_code] = examples

            endpoint.response_examples = response_examples

        # 提取安全要求
        security = operation.get("security", [])
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
                analyzed_at=datetime.now(),
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

            # 风险评估
            self._assess_risks(spec, endpoints, analysis)

            self.logger.info(
                f"Quality analysis completed. Score: {analysis.quality_score}, "
                f"Level: {analysis.quality_level}, Risks: {len(analysis.risks)}"
            )

            return analysis

        except DocumentValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Quality analysis failed: {e}")
            raise DocumentValidationError(
                f"Quality analysis failed: {e}", details={"error": str(e)}
            )

    def _analyze_completeness(
        self,
        spec: Dict[str, Any],
        endpoints: List[APIEndpoint],
        analysis: DocumentAnalysis,
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
                endpoint.request_examples or any(endpoint.response_examples.values())
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
            content = endpoint.request_body.get("content", {})
            for media_info in content.values():
                if isinstance(media_info, dict) and "schema" in media_info:
                    return True

        # 检查响应模式
        for response_info in endpoint.responses.values():
            if isinstance(response_info, dict):
                content = response_info.get("content", {})
                for media_info in content.values():
                    if isinstance(media_info, dict) and "schema" in media_info:
                        return True

        return False

    def _analyze_quality_issues(
        self,
        spec: Dict[str, Any],
        endpoints: List[APIEndpoint],
        analysis: DocumentAnalysis,
    ) -> None:
        """分析质量问题"""
        issues = []

        # 检查基本信息
        info = spec.get("info", {})
        if not info.get("description"):
            issues.append(
                {
                    "type": "missing_info_description",
                    "severity": "medium",
                    "message": "API description is missing in info section",
                }
            )

        if not info.get("contact"):
            issues.append(
                {
                    "type": "missing_contact",
                    "severity": "low",
                    "message": "Contact information is missing",
                }
            )

        # 检查服务器配置
        if not spec.get("servers"):
            issues.append(
                {
                    "type": "missing_servers",
                    "severity": "medium",
                    "message": "Server configuration is missing",
                }
            )

        # 检查组件定义
        if not spec.get("components"):
            issues.append(
                {
                    "type": "missing_components",
                    "severity": "medium",
                    "message": "Components section is missing",
                }
            )

        # 检查端点问题
        for endpoint in endpoints:
            endpoint_id = f"{endpoint.method.value} {endpoint.path}"

            # 检查缺少描述
            if not endpoint.summary and not endpoint.description:
                issues.append(
                    {
                        "type": "missing_endpoint_description",
                        "severity": "medium",
                        "message": f"Endpoint {endpoint_id} lacks description",
                        "endpoint": endpoint_id,
                    }
                )

            # 检查缺少标签
            if not endpoint.tags:
                issues.append(
                    {
                        "type": "missing_tags",
                        "severity": "low",
                        "message": f"Endpoint {endpoint_id} has no tags",
                        "endpoint": endpoint_id,
                    }
                )

            # 检查缺少错误响应
            response_codes = set(endpoint.responses.keys())
            if not any(
                code.startswith("4") or code.startswith("5") for code in response_codes
            ):
                issues.append(
                    {
                        "type": "missing_error_responses",
                        "severity": "medium",
                        "message": f"Endpoint {endpoint_id} lacks error response definitions",
                        "endpoint": endpoint_id,
                    }
                )

        analysis.issues = issues

    def _generate_statistics(
        self, endpoints: List[APIEndpoint], analysis: DocumentAnalysis
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
        examples_ratio = max(
            0, 1 - (analysis.missing_examples / analysis.total_endpoints)
        )
        score += examples_ratio * 20

        # 模式定义覆盖率 (20%)
        schemas_ratio = max(
            0, 1 - (analysis.missing_schemas / analysis.total_endpoints)
        )
        score += schemas_ratio * 20

        # 问题扣分 (20%)
        issue_penalty = 0
        for issue in analysis.issues:
            severity = issue.get("severity", "low")
            if severity == "high":
                issue_penalty += 5
            elif severity == "medium":
                issue_penalty += 2
            else:  # low
                issue_penalty += 1

        # 最多扣20分
        issue_penalty = min(issue_penalty, 20)
        score += 20 - issue_penalty

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
        high_severity_issues = [
            i for i in analysis.issues if i.get("severity") == "high"
        ]
        if high_severity_issues:
            suggestions.append(
                f"Address {len(high_severity_issues)} high-severity issues "
                "to improve API reliability"
            )

        medium_severity_issues = [
            i for i in analysis.issues if i.get("severity") == "medium"
        ]
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

    def _assess_risks(
        self,
        spec: Dict[str, Any],
        endpoints: List[APIEndpoint],
        analysis: DocumentAnalysis,
    ) -> None:
        """评估文档风险

        Args:
            spec: OpenAPI规范字典
            endpoints: 端点列表
            analysis: 分析结果对象
        """
        risks = []

        # 安全风险评估
        security_risks = self._assess_security_risks(spec, endpoints)
        risks.extend(security_risks)

        # 兼容性风险评估
        compatibility_risks = self._assess_compatibility_risks(spec, endpoints)
        risks.extend(compatibility_risks)

        # 可靠性风险评估
        reliability_risks = self._assess_reliability_risks(spec, endpoints)
        risks.extend(reliability_risks)

        # 可维护性风险评估
        maintainability_risks = self._assess_maintainability_risks(spec, endpoints)
        risks.extend(maintainability_risks)

        # 可用性风险评估
        usability_risks = self._assess_usability_risks(spec, endpoints)
        risks.extend(usability_risks)

        # 性能风险评估
        performance_risks = self._assess_performance_risks(spec, endpoints)
        risks.extend(performance_risks)

        # 设置风险信息
        analysis.risks = risks

        # 生成风险统计
        self._generate_risk_summary(analysis)

        # 计算整体风险等级
        self._calculate_overall_risk_level(analysis)

    def _assess_security_risks(
        self, spec: Dict[str, Any], endpoints: List[APIEndpoint]
    ) -> List[RiskItem]:
        """评估安全风险"""
        risks = []

        # 检查是否缺少全局安全定义
        security_schemes = spec.get("components", {}).get("securitySchemes", {})
        global_security = spec.get("security", [])

        if not security_schemes and not global_security:
            risks.append(
                RiskItem(
                    id="SEC001",
                    title="缺少安全配置",
                    description="API文档中未定义任何安全认证机制",
                    category=RiskCategory.SECURITY,
                    level=RiskLevel.HIGH,
                    impact="API可能暴露在未授权访问风险中，存在数据泄露和恶意操作的可能",
                    recommendation="添加适当的安全认证机制，如API Key、OAuth2或JWT",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}" for ep in endpoints
                    ],
                    details={"missing_schemes": True, "missing_global_security": True},
                )
            )

        # 检查敏感端点的安全配置
        sensitive_paths = ["password", "token", "auth", "login", "admin", "user"]
        for endpoint in endpoints:
            path_lower = endpoint.path.lower()
            if any(sensitive in path_lower for sensitive in sensitive_paths):
                if not endpoint.security and not global_security:
                    risks.append(
                        RiskItem(
                            id=f"SEC002_{endpoint.path}_{endpoint.method.value}",
                            title="敏感端点缺少安全保护",
                            description=f"敏感端点 {endpoint.method.value.upper()} {endpoint.path} 未配置安全认证",
                            category=RiskCategory.SECURITY,
                            level=RiskLevel.CRITICAL,
                            impact="敏感操作可能被未授权用户访问，造成严重安全风险",
                            recommendation="为敏感端点添加适当的安全认证要求",
                            affected_endpoints=[
                                f"{endpoint.method.value.upper()} {endpoint.path}"
                            ],
                            details={
                                "endpoint_path": endpoint.path,
                                "method": endpoint.method.value,
                            },
                        )
                    )

        # 检查是否使用了不安全的HTTP方法
        for endpoint in endpoints:
            if (
                endpoint.method in [HttpMethod.DELETE]
                and not endpoint.security
                and not global_security
            ):
                risks.append(
                    RiskItem(
                        id=f"SEC003_{endpoint.path}_{endpoint.method.value}",
                        title="危险操作缺少安全保护",
                        description=f"DELETE操作 {endpoint.path} 未配置安全认证",
                        category=RiskCategory.SECURITY,
                        level=RiskLevel.HIGH,
                        impact="删除操作可能被恶意调用，导致数据丢失",
                        recommendation="为DELETE操作添加严格的安全认证和权限控制",
                        affected_endpoints=[
                            f"{endpoint.method.value.upper()} {endpoint.path}"
                        ],
                        details={"method": "DELETE", "path": endpoint.path},
                    )
                )

        return risks

    def _assess_compatibility_risks(
        self, spec: Dict[str, Any], endpoints: List[APIEndpoint]
    ) -> List[RiskItem]:
        """评估兼容性风险"""
        risks = []

        # 检查OpenAPI版本兼容性
        openapi_version = spec.get("openapi", "")
        if openapi_version not in self.SUPPORTED_VERSIONS:
            risks.append(
                RiskItem(
                    id="COMP001",
                    title="OpenAPI版本兼容性问题",
                    description=f"使用的OpenAPI版本 {openapi_version} 可能存在兼容性问题",
                    category=RiskCategory.COMPATIBILITY,
                    level=RiskLevel.MEDIUM,
                    impact="可能导致某些工具无法正确解析文档或生成代码",
                    recommendation=f"建议升级到支持的版本: {', '.join(self.SUPPORTED_VERSIONS)}",
                    affected_endpoints=[],
                    details={
                        "current_version": openapi_version,
                        "supported_versions": self.SUPPORTED_VERSIONS,
                    },
                )
            )

        # 检查废弃的端点
        deprecated_endpoints = [ep for ep in endpoints if ep.deprecated]
        if deprecated_endpoints:
            risks.append(
                RiskItem(
                    id="COMP002",
                    title="存在废弃的API端点",
                    description=f"发现 {len(deprecated_endpoints)} 个已废弃的API端点",
                    category=RiskCategory.COMPATIBILITY,
                    level=RiskLevel.MEDIUM,
                    impact="废弃的端点可能在未来版本中被移除，影响客户端兼容性",
                    recommendation="制定废弃端点的迁移计划，并在文档中明确废弃时间表",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in deprecated_endpoints
                    ],
                    details={"deprecated_count": len(deprecated_endpoints)},
                )
            )

        return risks

    def _assess_reliability_risks(
        self, spec: Dict[str, Any], endpoints: List[APIEndpoint]
    ) -> List[RiskItem]:
        """评估可靠性风险"""
        risks = []

        # 检查错误响应定义
        endpoints_without_error_responses = []
        for endpoint in endpoints:
            has_error_responses = any(
                status_code.startswith(("4", "5"))
                for status_code in endpoint.responses.keys()
            )
            if not has_error_responses:
                endpoints_without_error_responses.append(endpoint)

        if endpoints_without_error_responses:
            risks.append(
                RiskItem(
                    id="REL001",
                    title="缺少错误响应定义",
                    description=f"{len(endpoints_without_error_responses)} 个端点未定义错误响应",
                    category=RiskCategory.RELIABILITY,
                    level=RiskLevel.MEDIUM,
                    impact="客户端无法正确处理错误情况，可能导致应用崩溃或用户体验差",
                    recommendation="为所有端点添加适当的4xx和5xx错误响应定义",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in endpoints_without_error_responses
                    ],
                    details={
                        "missing_error_responses_count": len(
                            endpoints_without_error_responses
                        )
                    },
                )
            )

        # 检查参数验证
        endpoints_without_validation = []
        for endpoint in endpoints:
            has_validation = False
            # 检查路径参数
            for param in endpoint.path_parameters.values():
                if isinstance(param, dict) and (
                    "pattern" in param or "minimum" in param or "maximum" in param
                ):
                    has_validation = True
                    break
            # 检查查询参数
            if not has_validation:
                for param in endpoint.query_parameters.values():
                    if isinstance(param, dict) and (
                        "pattern" in param or "minimum" in param or "maximum" in param
                    ):
                        has_validation = True
                        break

            if not has_validation and (
                endpoint.path_parameters or endpoint.query_parameters
            ):
                endpoints_without_validation.append(endpoint)

        if endpoints_without_validation:
            risks.append(
                RiskItem(
                    id="REL002",
                    title="参数验证不足",
                    description=f"{len(endpoints_without_validation)} 个端点的参数缺少验证规则",
                    category=RiskCategory.RELIABILITY,
                    level=RiskLevel.MEDIUM,
                    impact="可能接收无效参数导致服务器错误或安全问题",
                    recommendation="为参数添加适当的验证规则，如格式、范围、长度限制等",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in endpoints_without_validation
                    ],
                    details={
                        "missing_validation_count": len(endpoints_without_validation)
                    },
                )
            )

        return risks

    def _assess_maintainability_risks(
        self, spec: Dict[str, Any], endpoints: List[APIEndpoint]
    ) -> List[RiskItem]:
        """评估可维护性风险"""
        risks = []

        # 检查文档描述完整性
        missing_descriptions = [
            ep for ep in endpoints if not ep.description and not ep.summary
        ]
        if len(missing_descriptions) > len(endpoints) * 0.3:  # 超过30%的端点缺少描述
            risks.append(
                RiskItem(
                    id="MAINT001",
                    title="文档描述不完整",
                    description=f"{len(missing_descriptions)} 个端点缺少描述信息",
                    category=RiskCategory.MAINTAINABILITY,
                    level=RiskLevel.MEDIUM,
                    impact="缺少描述会增加开发和维护成本，影响团队协作效率",
                    recommendation="为所有端点添加清晰的描述信息，说明功能和用途",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in missing_descriptions
                    ],
                    details={"missing_descriptions_count": len(missing_descriptions)},
                )
            )

        # 检查标签使用
        untagged_endpoints = [ep for ep in endpoints if not ep.tags]
        if len(untagged_endpoints) > len(endpoints) * 0.5:  # 超过50%的端点没有标签
            risks.append(
                RiskItem(
                    id="MAINT002",
                    title="端点分类不清晰",
                    description=f"{len(untagged_endpoints)} 个端点未使用标签进行分类",
                    category=RiskCategory.MAINTAINABILITY,
                    level=RiskLevel.LOW,
                    impact="缺少标签会使API文档难以组织和导航，影响可读性",
                    recommendation="使用标签对端点进行逻辑分组，提高文档组织性",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in untagged_endpoints
                    ],
                    details={"untagged_count": len(untagged_endpoints)},
                )
            )

        # 检查操作ID
        missing_operation_ids = [ep for ep in endpoints if not ep.operation_id]
        if missing_operation_ids:
            risks.append(
                RiskItem(
                    id="MAINT003",
                    title="缺少操作ID",
                    description=f"{len(missing_operation_ids)} 个端点缺少operationId",
                    category=RiskCategory.MAINTAINABILITY,
                    level=RiskLevel.LOW,
                    impact="缺少operationId会影响代码生成工具的使用，降低开发效率",
                    recommendation="为所有端点添加唯一的operationId，便于代码生成和引用",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in missing_operation_ids
                    ],
                    details={"missing_operation_ids_count": len(missing_operation_ids)},
                )
            )

        return risks

    def _assess_usability_risks(
        self, spec: Dict[str, Any], endpoints: List[APIEndpoint]
    ) -> List[RiskItem]:
        """评估可用性风险"""
        risks = []

        # 检查示例完整性
        missing_examples = [
            ep
            for ep in endpoints
            if not ep.request_examples and not any(ep.response_examples.values())
        ]
        if len(missing_examples) > len(endpoints) * 0.4:  # 超过40%的端点缺少示例
            risks.append(
                RiskItem(
                    id="USAB001",
                    title="缺少使用示例",
                    description=f"{len(missing_examples)} 个端点缺少请求或响应示例",
                    category=RiskCategory.USABILITY,
                    level=RiskLevel.MEDIUM,
                    impact="缺少示例会增加开发者的学习成本，降低API的易用性",
                    recommendation="为端点添加典型的请求和响应示例，帮助开发者理解API用法",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in missing_examples
                    ],
                    details={"missing_examples_count": len(missing_examples)},
                )
            )

        # 检查服务器信息
        servers = spec.get("servers", [])
        if not servers:
            risks.append(
                RiskItem(
                    id="USAB002",
                    title="缺少服务器信息",
                    description="文档中未定义服务器地址信息",
                    category=RiskCategory.USABILITY,
                    level=RiskLevel.LOW,
                    impact="开发者无法直接测试API，需要额外查找服务器地址",
                    recommendation="添加服务器地址信息，包括开发、测试和生产环境",
                    affected_endpoints=[],
                    details={"servers_defined": False},
                )
            )

        # 检查联系信息
        info = spec.get("info", {})
        contact = info.get("contact", {})
        if not contact:
            risks.append(
                RiskItem(
                    id="USAB003",
                    title="缺少联系信息",
                    description="文档中未提供API维护者的联系信息",
                    category=RiskCategory.USABILITY,
                    level=RiskLevel.LOW,
                    impact="开发者遇到问题时无法联系API维护者，影响问题解决效率",
                    recommendation="添加API维护者的联系信息，如邮箱、网站或支持渠道",
                    affected_endpoints=[],
                    details={"contact_provided": False},
                )
            )

        return risks

    def _assess_performance_risks(
        self, spec: Dict[str, Any], endpoints: List[APIEndpoint]
    ) -> List[RiskItem]:
        """评估性能风险"""
        risks = []

        # 检查大数据传输端点
        potential_large_data_endpoints = []
        for endpoint in endpoints:
            # 检查是否有文件上传
            if endpoint.request_body:
                content = endpoint.request_body.get("content", {})
                if any(
                    "multipart" in media_type or "octet-stream" in media_type
                    for media_type in content.keys()
                ):
                    potential_large_data_endpoints.append(endpoint)

            # 检查是否有列表查询端点但缺少分页
            if endpoint.method == HttpMethod.GET and (
                "list" in endpoint.path.lower() or "search" in endpoint.path.lower()
            ):
                has_pagination = any(
                    param_name in ["page", "limit", "offset", "size", "per_page"]
                    for param_name in endpoint.query_parameters.keys()
                )
                if not has_pagination:
                    potential_large_data_endpoints.append(endpoint)

        if potential_large_data_endpoints:
            risks.append(
                RiskItem(
                    id="PERF001",
                    title="潜在的性能问题",
                    description=f"{len(potential_large_data_endpoints)} 个端点可能存在性能风险",
                    category=RiskCategory.PERFORMANCE,
                    level=RiskLevel.MEDIUM,
                    impact="大数据传输或无分页的列表查询可能导致性能问题和超时",
                    recommendation="为文件上传添加大小限制，为列表查询添加分页参数",
                    affected_endpoints=[
                        f"{ep.method.value.upper()} {ep.path}"
                        for ep in potential_large_data_endpoints
                    ],
                    details={
                        "potential_performance_issues_count": len(
                            potential_large_data_endpoints
                        )
                    },
                )
            )

        return risks

    def _generate_risk_summary(self, analysis: DocumentAnalysis) -> None:
        """生成风险统计摘要"""
        risk_summary = {
            "total": len(analysis.risks),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for risk in analysis.risks:
            if risk.level == RiskLevel.CRITICAL:
                risk_summary["critical"] += 1
            elif risk.level == RiskLevel.HIGH:
                risk_summary["high"] += 1
            elif risk.level == RiskLevel.MEDIUM:
                risk_summary["medium"] += 1
            elif risk.level == RiskLevel.LOW:
                risk_summary["low"] += 1

        # 按类别统计
        for category in RiskCategory:
            category_risks = [r for r in analysis.risks if r.category == category]
            risk_summary[f"{category.value}_count"] = len(category_risks)

        analysis.risk_summary = risk_summary

    def _calculate_overall_risk_level(self, analysis: DocumentAnalysis) -> None:
        """计算整体风险等级"""
        if not analysis.risks:
            analysis.overall_risk_level = RiskLevel.LOW
            return

        # 根据风险统计确定整体风险等级
        critical_count = analysis.risk_summary.get("critical", 0)
        high_count = analysis.risk_summary.get("high", 0)
        medium_count = analysis.risk_summary.get("medium", 0)

        if critical_count > 0:
            analysis.overall_risk_level = RiskLevel.CRITICAL
        elif high_count >= 3 or (high_count >= 1 and medium_count >= 3):
            analysis.overall_risk_level = RiskLevel.HIGH
        elif high_count >= 1 or medium_count >= 2:
            analysis.overall_risk_level = RiskLevel.MEDIUM
        else:
            analysis.overall_risk_level = RiskLevel.LOW
