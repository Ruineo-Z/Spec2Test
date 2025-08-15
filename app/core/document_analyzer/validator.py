"""
文档质量检查器

基于LLM对API文档进行智能质量分析和评估。
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from .models import (
    DocumentAnalysisResult, DocumentIssue, QualityMetrics,
    IssueType, IssueSeverity, QualityLevel, APIEndpoint
)
from app.core.shared.llm import LLMFactory
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


# LLM响应的数据模型
class LLMQualityIssue(BaseModel):
    """LLM返回的质量问题"""
    type: str
    severity: str
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


class LLMQualityAnalysis(BaseModel):
    """LLM返回的质量分析结果"""
    overall_score: float
    completeness_score: float
    consistency_score: float
    clarity_score: float
    usability_score: float
    issues: List[LLMQualityIssue]
    suggestions: List[str]


class DocumentValidator:
    """基于LLM的文档质量检查器

    使用大语言模型对API文档进行智能质量分析和评估。
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """初始化文档验证器

        Args:
            llm_config: LLM配置，如果为None则使用默认配置
        """
        self.logger = get_logger(f"{self.__class__.__name__}")

        # 初始化LLM客户端
        try:
            # 从配置中获取提供商，默认使用ollama（因为它是我们支持的）
            provider = (llm_config or {}).get("provider", "ollama")

            # 如果没有提供配置，使用可用的模型
            if not llm_config:
                llm_config = {
                    "base_url": "http://localhost:11434",
                    "model": "qwen2.5:3b",  # 使用可用的模型
                    "timeout": 300,
                    "temperature": 0.1
                }

            self.llm_client = LLMFactory.create_client(provider, llm_config)
            self.logger.info(f"LLM客户端初始化成功: {provider} ({llm_config.get('model', 'default')})")
        except Exception as e:
            self.logger.error(f"LLM客户端初始化失败: {e}")
            self.llm_client = None

        self.logger.info("基于LLM的文档质量检查器初始化完成")
    
    def validate_document(self, analysis_result: DocumentAnalysisResult) -> DocumentAnalysisResult:
        """使用LLM验证文档质量

        Args:
            analysis_result: 文档分析结果

        Returns:
            DocumentAnalysisResult: 更新后的分析结果

        Raises:
            Exception: LLM不可用或分析失败时抛出异常
        """
        self.logger.info("开始基于LLM的文档质量检查")

        # 检查LLM客户端是否可用
        if not self.llm_client:
            error_msg = "LLM客户端未初始化，无法进行智能文档质量分析"
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # 清空现有问题和建议
        analysis_result.issues = []
        analysis_result.suggestions = []

        try:
            # 准备文档内容用于LLM分析
            document_content = self._prepare_document_content(analysis_result)

            # 构建质量分析提示词
            prompt = self._build_quality_analysis_prompt(document_content)

            # 调用LLM进行质量分析
            llm_response = self.llm_client.generate_text(
                prompt=prompt,
                schema=LLMQualityAnalysis.model_json_schema()
            )

            # 解析LLM响应
            quality_analysis = self._parse_llm_response(llm_response)

            # 将LLM分析结果转换为标准格式
            analysis_result = self._convert_llm_analysis(analysis_result, quality_analysis)

            self.logger.info(f"LLM文档质量检查完成: 发现{len(analysis_result.issues)}个问题")
            return analysis_result

        except Exception as e:
            error_msg = f"LLM文档质量检查失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def _prepare_document_content(self, analysis_result: DocumentAnalysisResult) -> str:
        """准备用于LLM分析的文档内容

        Args:
            analysis_result: 文档分析结果

        Returns:
            str: 格式化的文档内容
        """
        content_parts = []

        # 基本信息
        content_parts.append("# API文档基本信息")
        content_parts.append(f"标题: {analysis_result.title or '未提供'}")
        content_parts.append(f"版本: {analysis_result.version or '未提供'}")
        content_parts.append(f"描述: {analysis_result.description or '未提供'}")
        content_parts.append(f"基础URL: {analysis_result.base_url or '未提供'}")
        content_parts.append("")

        # 端点信息
        content_parts.append("# API端点列表")
        if analysis_result.endpoints:
            for i, endpoint in enumerate(analysis_result.endpoints, 1):
                content_parts.append(f"## 端点 {i}: {endpoint.method} {endpoint.path}")
                content_parts.append(f"摘要: {endpoint.summary or '未提供'}")
                content_parts.append(f"描述: {endpoint.description or '未提供'}")
                content_parts.append(f"标签: {', '.join(endpoint.tags) if endpoint.tags else '未提供'}")

                # 参数信息
                if endpoint.parameters:
                    content_parts.append("参数:")
                    for param in endpoint.parameters:
                        if isinstance(param, dict):
                            name = param.get("name", "")
                            param_type = param.get("type", param.get("schema", {}).get("type", ""))
                            required = param.get("required", False)
                            description = param.get("description", "")
                            content_parts.append(f"  - {name} ({param_type}) {'[必需]' if required else '[可选]'}: {description}")

                # 响应信息
                if endpoint.responses:
                    content_parts.append("响应:")
                    for status_code, response in endpoint.responses.items():
                        if isinstance(response, dict):
                            description = response.get("description", "")
                            content_parts.append(f"  - {status_code}: {description}")

                content_parts.append("")
        else:
            content_parts.append("未定义任何API端点")

        # 安全方案
        if analysis_result.security_schemes:
            content_parts.append("# 安全方案")
            for scheme_name, scheme_info in analysis_result.security_schemes.items():
                content_parts.append(f"- {scheme_name}: {scheme_info}")
            content_parts.append("")

        return "\n".join(content_parts)

    def _build_quality_analysis_prompt(self, document_content: str) -> str:
        """构建质量分析提示词

        Args:
            document_content: 文档内容

        Returns:
            str: 质量分析提示词
        """
        prompt = f"""
你是一个专业的API文档质量分析专家。请对以下API文档进行全面的质量分析和评估。

## 文档内容
{document_content}

## 分析要求
请从以下维度对文档进行评估，并给出0-100分的评分：

1. **完整性评估** (completeness_score)
   - 基本信息是否完整（标题、版本、描述、基础URL）
   - 端点定义是否完整（摘要、描述、参数、响应）
   - 必要的安全方案是否定义

2. **一致性评估** (consistency_score)
   - 命名风格是否一致
   - 响应格式是否统一
   - 参数定义是否规范

3. **清晰度评估** (clarity_score)
   - 描述是否清晰易懂
   - 术语使用是否准确
   - 信息组织是否合理

4. **可用性评估** (usability_score)
   - 是否提供足够的示例
   - 是否便于开发者理解和使用
   - 是否包含必要的使用说明

## 问题识别
请识别文档中存在的具体问题，包括：
- 问题类型：missing_field, invalid_format, inconsistent_data, incomplete_info, security_issue, performance_issue
- 严重程度：critical, high, medium, low, info
- 问题描述和改进建议

## 输出格式
请严格按照以下JSON格式输出分析结果：

```json
{{
  "overall_score": 85.0,
  "completeness_score": 90.0,
  "consistency_score": 80.0,
  "clarity_score": 85.0,
  "usability_score": 85.0,
  "issues": [
    {{
      "type": "missing_field",
      "severity": "medium",
      "message": "缺少API描述",
      "location": "info.description",
      "suggestion": "添加详细的API功能描述"
    }}
  ],
  "suggestions": [
    "添加更多的请求和响应示例",
    "完善错误码说明",
    "提供SDK使用指南"
  ]
}}
```

请开始分析：
"""
        return prompt.strip()

    def _parse_llm_response(self, llm_response) -> LLMQualityAnalysis:
        """解析LLM响应

        Args:
            llm_response: LLM响应对象

        Returns:
            LLMQualityAnalysis: 解析后的质量分析结果
        """
        try:
            # 从LLM响应中提取内容
            if hasattr(llm_response, 'content'):
                content = llm_response.content
            elif hasattr(llm_response, 'text'):
                content = llm_response.text
            elif isinstance(llm_response, dict):
                content = llm_response.get("content", "")
            else:
                content = str(llm_response)

            # 尝试解析JSON
            if isinstance(content, str):
                # 提取JSON部分（去除可能的markdown格式）
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 尝试直接解析整个内容
                    json_str = content.strip()

                analysis_data = json.loads(json_str)
            else:
                analysis_data = content

            # 验证和转换数据
            return LLMQualityAnalysis(**analysis_data)

        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {e}")
            # 返回默认分析结果
            return LLMQualityAnalysis(
                overall_score=50.0,
                completeness_score=50.0,
                consistency_score=50.0,
                clarity_score=50.0,
                usability_score=50.0,
                issues=[
                    LLMQualityIssue(
                        type="invalid_format",
                        severity="high",
                        message="LLM分析响应解析失败",
                        suggestion="请检查文档格式或重试分析"
                    )
                ],
                suggestions=["建议重新分析文档"]
            )

    def _convert_llm_analysis(self, analysis_result: DocumentAnalysisResult,
                             quality_analysis: LLMQualityAnalysis) -> DocumentAnalysisResult:
        """将LLM分析结果转换为标准格式

        Args:
            analysis_result: 原始分析结果
            quality_analysis: LLM质量分析结果

        Returns:
            DocumentAnalysisResult: 更新后的分析结果
        """
        # 转换质量指标
        analysis_result.quality_metrics = QualityMetrics(
            overall_score=quality_analysis.overall_score,
            completeness_score=quality_analysis.completeness_score,
            consistency_score=quality_analysis.consistency_score,
            clarity_score=quality_analysis.clarity_score,
            usability_score=quality_analysis.usability_score
        )

        # 转换问题列表
        analysis_result.issues = []
        for llm_issue in quality_analysis.issues:
            try:
                # 映射问题类型
                issue_type = self._map_issue_type(llm_issue.type)
                severity = self._map_severity(llm_issue.severity)

                issue = DocumentIssue(
                    type=issue_type,
                    severity=severity,
                    message=llm_issue.message,
                    location=llm_issue.location,
                    suggestion=llm_issue.suggestion
                )
                analysis_result.issues.append(issue)

            except Exception as e:
                self.logger.warning(f"转换问题时出错: {e}, 跳过该问题")

        # 设置改进建议
        analysis_result.suggestions = quality_analysis.suggestions

        return analysis_result

    def _map_issue_type(self, llm_type: str) -> IssueType:
        """映射LLM返回的问题类型到标准枚举"""
        type_mapping = {
            "missing_field": IssueType.MISSING_FIELD,
            "invalid_format": IssueType.INVALID_FORMAT,
            "inconsistent_data": IssueType.INCONSISTENT_DATA,
            "incomplete_info": IssueType.INCOMPLETE_INFO,
            "deprecated_usage": IssueType.DEPRECATED_USAGE,
            "security_issue": IssueType.SECURITY_ISSUE,
            "performance_issue": IssueType.PERFORMANCE_ISSUE
        }
        return type_mapping.get(llm_type, IssueType.INVALID_FORMAT)

    def _map_severity(self, llm_severity: str) -> IssueSeverity:
        """映射LLM返回的严重程度到标准枚举"""
        severity_mapping = {
            "critical": IssueSeverity.CRITICAL,
            "high": IssueSeverity.HIGH,
            "medium": IssueSeverity.MEDIUM,
            "low": IssueSeverity.LOW,
            "info": IssueSeverity.INFO
        }
        return severity_mapping.get(llm_severity, IssueSeverity.MEDIUM)
