"""
文档质量检查器

对API文档进行完整性检查、一致性验证和质量评估。
"""

import re
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict

from .models import (
    DocumentAnalysisResult, DocumentIssue, QualityMetrics,
    IssueType, IssueSeverity, QualityLevel, APIEndpoint
)
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentValidator:
    """文档质量检查器
    
    对API文档进行全面的质量检查和评估。
    """
    
    def __init__(self):
        """初始化文档验证器"""
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 必需字段定义
        self.required_openapi_fields = {
            "info": ["title", "version"],
            "paths": [],
            "endpoint": ["responses"]
        }
        
        # HTTP状态码定义
        self.standard_status_codes = {
            200, 201, 202, 204, 301, 302, 304, 400, 401, 403, 404, 405, 409, 422, 429, 500, 502, 503
        }
        
        # 常见HTTP方法
        self.standard_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        
        self.logger.info("文档质量检查器初始化完成")
    
    def validate_document(self, analysis_result: DocumentAnalysisResult) -> DocumentAnalysisResult:
        """验证文档质量
        
        Args:
            analysis_result: 文档分析结果
            
        Returns:
            DocumentAnalysisResult: 更新后的分析结果
        """
        try:
            self.logger.info("开始文档质量检查")
            
            # 清空现有问题和建议
            analysis_result.issues = []
            analysis_result.suggestions = []
            
            # 执行各种检查
            self._check_completeness(analysis_result)
            self._check_consistency(analysis_result)
            self._check_clarity(analysis_result)
            self._check_usability(analysis_result)
            self._check_security(analysis_result)
            self._check_performance(analysis_result)
            
            # 计算质量指标
            analysis_result.quality_metrics = self._calculate_quality_metrics(analysis_result)
            
            # 生成改进建议
            self._generate_suggestions(analysis_result)
            
            self.logger.info(f"文档质量检查完成: 发现{len(analysis_result.issues)}个问题")
            return analysis_result
            
        except Exception as e:
            error_msg = f"文档质量检查失败: {str(e)}"
            self.logger.error(error_msg)
            
            # 添加检查失败的问题
            analysis_result.issues.append(
                DocumentIssue(
                    type=IssueType.INVALID_FORMAT,
                    severity=IssueSeverity.HIGH,
                    message=error_msg,
                    suggestion="请检查文档格式是否正确"
                )
            )
            
            return analysis_result
    
    def _check_completeness(self, result: DocumentAnalysisResult):
        """检查完整性"""
        self.logger.debug("检查文档完整性")
        
        # 检查基本信息
        if not result.title:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.MISSING_FIELD,
                    severity=IssueSeverity.HIGH,
                    message="缺少文档标题",
                    location="info.title",
                    suggestion="添加清晰的API文档标题"
                )
            )
        
        if not result.version:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.MISSING_FIELD,
                    severity=IssueSeverity.MEDIUM,
                    message="缺少API版本信息",
                    location="info.version",
                    suggestion="添加API版本号，如'1.0.0'"
                )
            )
        
        if not result.description:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.MISSING_FIELD,
                    severity=IssueSeverity.MEDIUM,
                    message="缺少API描述",
                    location="info.description",
                    suggestion="添加API的详细描述"
                )
            )
        
        if not result.base_url:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.MISSING_FIELD,
                    severity=IssueSeverity.MEDIUM,
                    message="缺少服务器URL",
                    location="servers",
                    suggestion="添加API服务器地址"
                )
            )
        
        # 检查端点完整性
        if not result.endpoints:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.MISSING_FIELD,
                    severity=IssueSeverity.CRITICAL,
                    message="文档中没有定义任何API端点",
                    location="paths",
                    suggestion="添加API端点定义"
                )
            )
        else:
            self._check_endpoint_completeness(result)
    
    def _check_endpoint_completeness(self, result: DocumentAnalysisResult):
        """检查端点完整性"""
        for endpoint in result.endpoints:
            endpoint_id = endpoint.endpoint_id
            
            # 检查端点描述
            if not endpoint.summary and not endpoint.description:
                result.issues.append(
                    DocumentIssue(
                        type=IssueType.MISSING_FIELD,
                        severity=IssueSeverity.MEDIUM,
                        message=f"端点缺少描述: {endpoint_id}",
                        location=f"paths.{endpoint.path}.{endpoint.method.lower()}",
                        suggestion="添加端点的摘要或描述"
                    )
                )
            
            # 检查响应定义
            if not endpoint.responses:
                result.issues.append(
                    DocumentIssue(
                        type=IssueType.MISSING_FIELD,
                        severity=IssueSeverity.HIGH,
                        message=f"端点缺少响应定义: {endpoint_id}",
                        location=f"paths.{endpoint.path}.{endpoint.method.lower()}.responses",
                        suggestion="添加至少一个响应状态码定义"
                    )
                )
            else:
                # 检查是否有成功响应
                success_codes = [code for code in endpoint.responses.keys() if code.startswith('2')]
                if not success_codes:
                    result.issues.append(
                        DocumentIssue(
                            type=IssueType.MISSING_FIELD,
                            severity=IssueSeverity.MEDIUM,
                            message=f"端点缺少成功响应定义: {endpoint_id}",
                            location=f"paths.{endpoint.path}.{endpoint.method.lower()}.responses",
                            suggestion="添加2xx成功响应状态码"
                        )
                    )
            
            # 检查POST/PUT/PATCH是否有请求体
            if endpoint.method in ["POST", "PUT", "PATCH"] and not endpoint.request_body:
                result.issues.append(
                    DocumentIssue(
                        type=IssueType.MISSING_FIELD,
                        severity=IssueSeverity.MEDIUM,
                        message=f"{endpoint.method}端点缺少请求体定义: {endpoint_id}",
                        location=f"paths.{endpoint.path}.{endpoint.method.lower()}.requestBody",
                        suggestion="添加请求体Schema定义"
                    )
                )
    
    def _check_consistency(self, result: DocumentAnalysisResult):
        """检查一致性"""
        self.logger.debug("检查文档一致性")
        
        # 检查路径命名一致性
        self._check_path_naming_consistency(result)
        
        # 检查响应格式一致性
        self._check_response_consistency(result)
        
        # 检查参数命名一致性
        self._check_parameter_consistency(result)
        
        # 检查标签使用一致性
        self._check_tag_consistency(result)
    
    def _check_path_naming_consistency(self, result: DocumentAnalysisResult):
        """检查路径命名一致性"""
        path_patterns = defaultdict(list)
        
        for endpoint in result.endpoints:
            # 提取路径模式（去除参数）
            path_pattern = re.sub(r'\{[^}]+\}', '{param}', endpoint.path)
            path_patterns[path_pattern].append(endpoint)
        
        # 检查命名风格
        snake_case_paths = []
        kebab_case_paths = []
        camel_case_paths = []
        
        for endpoint in result.endpoints:
            path = endpoint.path
            if '_' in path:
                snake_case_paths.append(path)
            elif '-' in path:
                kebab_case_paths.append(path)
            elif any(c.isupper() for c in path):
                camel_case_paths.append(path)
        
        # 如果混用了多种命名风格
        styles_used = sum([
            len(snake_case_paths) > 0,
            len(kebab_case_paths) > 0,
            len(camel_case_paths) > 0
        ])
        
        if styles_used > 1:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INCONSISTENT_DATA,
                    severity=IssueSeverity.MEDIUM,
                    message="路径命名风格不一致",
                    suggestion="统一使用一种命名风格（推荐kebab-case）"
                )
            )
    
    def _check_response_consistency(self, result: DocumentAnalysisResult):
        """检查响应格式一致性"""
        response_structures = defaultdict(set)
        
        for endpoint in result.endpoints:
            for status_code, response in endpoint.responses.items():
                if isinstance(response, dict) and "content" in response:
                    content_types = set(response["content"].keys())
                    response_structures[status_code].update(content_types)
        
        # 检查相同状态码是否使用一致的内容类型
        for status_code, content_types in response_structures.items():
            if len(content_types) > 2:  # 允许一定的灵活性
                result.issues.append(
                    DocumentIssue(
                        type=IssueType.INCONSISTENT_DATA,
                        severity=IssueSeverity.LOW,
                        message=f"状态码{status_code}的响应内容类型不一致",
                        suggestion="统一相同状态码的响应格式"
                    )
                )
    
    def _check_parameter_consistency(self, result: DocumentAnalysisResult):
        """检查参数命名一致性"""
        parameter_names = defaultdict(set)
        
        for endpoint in result.endpoints:
            for param in endpoint.parameters:
                if isinstance(param, dict):
                    name = param.get("name")
                    param_type = param.get("in", "unknown")
                    if name:
                        parameter_names[param_type].add(name)
        
        # 检查参数命名风格
        for param_type, names in parameter_names.items():
            snake_case = [name for name in names if '_' in name]
            camel_case = [name for name in names if any(c.isupper() for c in name)]
            
            if len(snake_case) > 0 and len(camel_case) > 0:
                result.issues.append(
                    DocumentIssue(
                        type=IssueType.INCONSISTENT_DATA,
                        severity=IssueSeverity.LOW,
                        message=f"{param_type}参数命名风格不一致",
                        suggestion="统一参数命名风格"
                    )
                )
    
    def _check_tag_consistency(self, result: DocumentAnalysisResult):
        """检查标签使用一致性"""
        all_tags = set()
        for endpoint in result.endpoints:
            all_tags.update(endpoint.tags)
        
        # 检查标签命名
        if len(all_tags) > 20:  # 标签过多
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INCONSISTENT_DATA,
                    severity=IssueSeverity.LOW,
                    message=f"标签数量过多({len(all_tags)}个)",
                    suggestion="合并相关标签，保持标签数量适中"
                )
            )
    
    def _check_clarity(self, result: DocumentAnalysisResult):
        """检查清晰度"""
        self.logger.debug("检查文档清晰度")
        
        # 检查描述质量
        if result.description and len(result.description) < 50:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INCOMPLETE_INFO,
                    severity=IssueSeverity.LOW,
                    message="API描述过于简短",
                    suggestion="提供更详细的API功能描述"
                )
            )
        
        # 检查端点描述质量
        short_descriptions = 0
        for endpoint in result.endpoints:
            if endpoint.summary and len(endpoint.summary) < 10:
                short_descriptions += 1
        
        if short_descriptions > len(result.endpoints) * 0.3:  # 超过30%的端点描述过短
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INCOMPLETE_INFO,
                    severity=IssueSeverity.MEDIUM,
                    message="多个端点的描述过于简短",
                    suggestion="为端点提供更详细的功能描述"
                )
            )
    
    def _check_usability(self, result: DocumentAnalysisResult):
        """检查可用性"""
        self.logger.debug("检查文档可用性")
        
        # 检查示例
        endpoints_with_examples = 0
        for endpoint in result.endpoints:
            has_example = False
            
            # 检查请求体示例
            if endpoint.request_body and isinstance(endpoint.request_body, dict):
                content = endpoint.request_body.get("content", {})
                for media_type, schema in content.items():
                    if "example" in schema or "examples" in schema:
                        has_example = True
                        break
            
            # 检查响应示例
            for response in endpoint.responses.values():
                if isinstance(response, dict) and "content" in response:
                    content = response["content"]
                    for media_type, schema in content.items():
                        if "example" in schema or "examples" in schema:
                            has_example = True
                            break
            
            if has_example:
                endpoints_with_examples += 1
        
        if result.endpoints and endpoints_with_examples / len(result.endpoints) < 0.5:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.INCOMPLETE_INFO,
                    severity=IssueSeverity.MEDIUM,
                    message="缺少足够的请求/响应示例",
                    suggestion="为主要端点添加请求和响应示例"
                )
            )
    
    def _check_security(self, result: DocumentAnalysisResult):
        """检查安全性"""
        self.logger.debug("检查文档安全性")
        
        # 检查安全方案定义
        if not result.security_schemes:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.SECURITY_ISSUE,
                    severity=IssueSeverity.HIGH,
                    message="未定义安全认证方案",
                    suggestion="添加API认证方式定义"
                )
            )
        
        # 检查端点安全配置
        unsecured_endpoints = 0
        for endpoint in result.endpoints:
            if not endpoint.security and endpoint.method in ["POST", "PUT", "DELETE", "PATCH"]:
                unsecured_endpoints += 1
        
        if unsecured_endpoints > 0:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.SECURITY_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    message=f"{unsecured_endpoints}个修改操作端点未配置安全认证",
                    suggestion="为修改操作的端点添加安全认证要求"
                )
            )
    
    def _check_performance(self, result: DocumentAnalysisResult):
        """检查性能相关"""
        self.logger.debug("检查性能相关问题")
        
        # 检查分页支持
        get_endpoints = [ep for ep in result.endpoints if ep.method == "GET"]
        list_endpoints = [ep for ep in get_endpoints if "list" in ep.path.lower() or ep.path.endswith("s")]
        
        paginated_endpoints = 0
        for endpoint in list_endpoints:
            has_pagination = False
            for param in endpoint.parameters:
                if isinstance(param, dict):
                    name = param.get("name", "").lower()
                    if name in ["page", "limit", "offset", "size", "per_page"]:
                        has_pagination = True
                        break
            
            if has_pagination:
                paginated_endpoints += 1
        
        if list_endpoints and paginated_endpoints / len(list_endpoints) < 0.5:
            result.issues.append(
                DocumentIssue(
                    type=IssueType.PERFORMANCE_ISSUE,
                    severity=IssueSeverity.MEDIUM,
                    message="列表端点缺少分页参数",
                    suggestion="为列表查询端点添加分页参数"
                )
            )
    
    def _calculate_quality_metrics(self, result: DocumentAnalysisResult) -> QualityMetrics:
        """计算质量指标"""
        # 基础分数
        base_score = 100.0
        
        # 根据问题严重程度扣分
        for issue in result.issues:
            if issue.severity == IssueSeverity.CRITICAL:
                base_score -= 20
            elif issue.severity == IssueSeverity.HIGH:
                base_score -= 10
            elif issue.severity == IssueSeverity.MEDIUM:
                base_score -= 5
            elif issue.severity == IssueSeverity.LOW:
                base_score -= 2
        
        # 确保分数不低于0
        overall_score = max(0, base_score)
        
        # 计算各维度分数
        completeness_score = self._calculate_completeness_score(result)
        consistency_score = self._calculate_consistency_score(result)
        clarity_score = self._calculate_clarity_score(result)
        usability_score = self._calculate_usability_score(result)
        
        return QualityMetrics(
            overall_score=overall_score,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            clarity_score=clarity_score,
            usability_score=usability_score
        )
    
    def _calculate_completeness_score(self, result: DocumentAnalysisResult) -> float:
        """计算完整性分数"""
        score = 100.0
        
        # 基本信息完整性
        if not result.title:
            score -= 15
        if not result.version:
            score -= 10
        if not result.description:
            score -= 10
        if not result.base_url:
            score -= 10
        
        # 端点完整性
        if result.endpoints:
            incomplete_endpoints = 0
            for endpoint in result.endpoints:
                if not endpoint.summary and not endpoint.description:
                    incomplete_endpoints += 1
                if not endpoint.responses:
                    incomplete_endpoints += 1
            
            if incomplete_endpoints > 0:
                score -= (incomplete_endpoints / len(result.endpoints)) * 30
        else:
            score = 0  # 没有端点，完整性为0
        
        return max(0, score)
    
    def _calculate_consistency_score(self, result: DocumentAnalysisResult) -> float:
        """计算一致性分数"""
        score = 100.0
        
        # 根据一致性问题扣分
        consistency_issues = [issue for issue in result.issues if issue.type == IssueType.INCONSISTENT_DATA]
        score -= len(consistency_issues) * 10
        
        return max(0, score)
    
    def _calculate_clarity_score(self, result: DocumentAnalysisResult) -> float:
        """计算清晰度分数"""
        score = 100.0
        
        # 根据清晰度问题扣分
        clarity_issues = [issue for issue in result.issues if issue.type == IssueType.INCOMPLETE_INFO]
        score -= len(clarity_issues) * 8
        
        return max(0, score)
    
    def _calculate_usability_score(self, result: DocumentAnalysisResult) -> float:
        """计算可用性分数"""
        score = 100.0
        
        # 检查示例覆盖率
        if result.endpoints:
            endpoints_with_examples = 0
            for endpoint in result.endpoints:
                # 简化的示例检查
                if endpoint.description and len(endpoint.description) > 50:
                    endpoints_with_examples += 1
            
            example_coverage = endpoints_with_examples / len(result.endpoints)
            if example_coverage < 0.5:
                score -= (0.5 - example_coverage) * 40
        
        return max(0, score)
    
    def _generate_suggestions(self, result: DocumentAnalysisResult):
        """生成改进建议"""
        suggestions = []
        
        # 根据质量等级生成建议
        if result.quality_metrics:
            quality_level = result.quality_metrics.quality_level
            
            if quality_level == QualityLevel.VERY_POOR:
                suggestions.append("文档质量较差，建议重新整理文档结构")
                suggestions.append("添加完整的API基本信息（标题、版本、描述）")
                suggestions.append("为所有端点添加详细的描述和示例")
            
            elif quality_level == QualityLevel.POOR:
                suggestions.append("文档需要大幅改进")
                suggestions.append("补充缺失的必要信息")
                suggestions.append("统一文档格式和命名规范")
            
            elif quality_level == QualityLevel.FAIR:
                suggestions.append("文档基本可用，但仍有改进空间")
                suggestions.append("添加更多的使用示例")
                suggestions.append("完善错误响应的描述")
            
            elif quality_level == QualityLevel.GOOD:
                suggestions.append("文档质量良好，可以考虑以下优化")
                suggestions.append("添加更详细的业务场景说明")
                suggestions.append("提供SDK或代码示例")
            
            elif quality_level == QualityLevel.EXCELLENT:
                suggestions.append("文档质量优秀！")
                suggestions.append("可以考虑添加交互式文档")
                suggestions.append("定期更新和维护文档")
        
        # 根据具体问题生成建议
        critical_issues = result.critical_issues
        if critical_issues:
            suggestions.append("优先解决严重问题，确保文档基本可用")
        
        high_issues = result.high_issues
        if high_issues:
            suggestions.append("解决高优先级问题，提升文档质量")
        
        result.suggestions = suggestions
