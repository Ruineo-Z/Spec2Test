"""
提示词构建器

为LLM构建专业的测试用例生成提示词。
"""

from typing import Dict, Any, List, Optional
from app.core.document_analyzer.models import DocumentAnalysisResult, APIEndpoint
from .models import GenerationConfig, TestCaseType, TestCasePriority
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """测试用例生成提示词构建器
    
    根据API文档分析结果和生成配置，构建专业的LLM提示词。
    """
    
    def __init__(self):
        """初始化提示词构建器"""
        self.logger = get_logger(f"{self.__class__.__name__}")
        self.logger.info("提示词构建器初始化完成")
    
    def build_test_generation_prompt(self, 
                                   analysis_result: DocumentAnalysisResult,
                                   endpoint: APIEndpoint,
                                   config: GenerationConfig) -> str:
        """构建测试用例生成提示词
        
        Args:
            analysis_result: 文档分析结果
            endpoint: API端点信息
            config: 生成配置
            
        Returns:
            str: 构建的提示词
        """
        try:
            self.logger.info(f"构建测试生成提示词: {endpoint.method} {endpoint.path}")
            
            # 构建提示词各部分
            context_section = self._build_context_section(analysis_result, endpoint)
            requirements_section = self._build_requirements_section(config)
            examples_section = self._build_examples_section(endpoint)
            output_format_section = self._build_output_format_section()
            
            # 组合完整提示词
            prompt = f"""
你是一个专业的API测试工程师，擅长设计全面、高质量的API测试用例。请根据以下API文档信息，为指定的端点生成详细的测试用例。

{context_section}

{requirements_section}

{examples_section}

{output_format_section}

请开始生成测试用例：
"""
            
            self.logger.debug(f"提示词构建完成，长度: {len(prompt)}字符")
            return prompt.strip()
            
        except Exception as e:
            error_msg = f"构建测试生成提示词失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_context_section(self, analysis_result: DocumentAnalysisResult, 
                              endpoint: APIEndpoint) -> str:
        """构建上下文信息部分"""
        context = []
        
        # API基本信息
        context.append("## API文档信息")
        context.append(f"**API名称**: {analysis_result.title or '未提供'}")
        context.append(f"**API版本**: {analysis_result.version or '未提供'}")
        context.append(f"**基础URL**: {analysis_result.base_url or '未提供'}")
        context.append("")
        
        # 目标端点信息
        context.append("## 目标端点信息")
        context.append(f"**端点**: {endpoint.method.upper()} {endpoint.path}")
        context.append(f"**摘要**: {endpoint.summary or '未提供'}")
        context.append(f"**描述**: {endpoint.description or '未提供'}")
        
        if endpoint.tags:
            context.append(f"**标签**: {', '.join(endpoint.tags)}")
        
        # 参数信息
        if endpoint.parameters:
            context.append("\n**请求参数**:")
            for param in endpoint.parameters:
                if isinstance(param, dict):
                    name = param.get("name", "")
                    param_type = param.get("type", param.get("schema", {}).get("type", ""))
                    required = param.get("required", False)
                    description = param.get("description", "")
                    param_in = param.get("in", "")
                    
                    required_text = "必需" if required else "可选"
                    context.append(f"- `{name}` ({param_type}, {param_in}, {required_text}): {description}")
        
        # 请求体信息
        if endpoint.request_body:
            context.append("\n**请求体**:")
            if isinstance(endpoint.request_body, dict):
                content = endpoint.request_body.get("content", {})
                for media_type, schema in content.items():
                    context.append(f"- 内容类型: {media_type}")
                    if "schema" in schema:
                        context.append(f"- Schema: {schema['schema']}")
        
        # 响应信息
        if endpoint.responses:
            context.append("\n**响应定义**:")
            for status_code, response in endpoint.responses.items():
                if isinstance(response, dict):
                    description = response.get("description", "")
                    context.append(f"- `{status_code}`: {description}")
        
        # 安全要求
        if endpoint.security:
            context.append("\n**安全要求**:")
            for security in endpoint.security:
                context.append(f"- {security}")
        
        return "\n".join(context)
    
    def _build_requirements_section(self, config: GenerationConfig) -> str:
        """构建测试要求部分"""
        requirements = []
        
        requirements.append("## 测试用例生成要求")
        
        # 用例类型要求
        case_types = []
        if config.include_positive:
            case_types.append("正向测试用例（正常流程）")
        if config.include_negative:
            case_types.append("负向测试用例（异常流程）")
        if config.include_boundary:
            case_types.append("边界测试用例（边界值）")
        if config.include_security:
            case_types.append("安全测试用例（安全漏洞）")
        if config.include_performance:
            case_types.append("性能测试用例（性能验证）")
        
        if case_types:
            requirements.append("**包含的用例类型**:")
            for case_type in case_types:
                requirements.append(f"- {case_type}")
        
        # 数据测试要求
        data_requirements = []
        if config.include_invalid_data:
            data_requirements.append("无效数据测试")
        if config.include_null_data:
            data_requirements.append("空值/null数据测试")
        if config.include_special_chars:
            data_requirements.append("特殊字符数据测试")
        
        if data_requirements:
            requirements.append("\n**数据测试要求**:")
            for req in data_requirements:
                requirements.append(f"- {req}")
        
        # 其他要求
        requirements.append(f"\n**其他要求**:")
        requirements.append(f"- 每个端点最多生成 {config.max_cases_per_endpoint} 个测试用例")
        requirements.append("- 测试用例应该覆盖主要的业务场景")
        requirements.append("- 包含详细的断言验证")
        requirements.append("- 提供清晰的测试步骤")
        requirements.append("- 设置合理的优先级")
        
        return "\n".join(requirements)
    
    def _build_examples_section(self, endpoint: APIEndpoint) -> str:
        """构建示例部分"""
        examples = []
        
        examples.append("## 测试用例设计指导")
        
        # 根据HTTP方法提供指导
        method = endpoint.method.upper()
        
        if method == "GET":
            examples.append("**GET请求测试重点**:")
            examples.append("- 验证查询参数的各种组合")
            examples.append("- 测试分页参数（如果有）")
            examples.append("- 验证过滤和排序功能")
            examples.append("- 测试无效参数的处理")
            
        elif method == "POST":
            examples.append("**POST请求测试重点**:")
            examples.append("- 验证必需字段的存在性")
            examples.append("- 测试数据格式验证")
            examples.append("- 验证业务规则约束")
            examples.append("- 测试重复提交处理")
            
        elif method == "PUT":
            examples.append("**PUT请求测试重点**:")
            examples.append("- 验证完整资源更新")
            examples.append("- 测试不存在资源的处理")
            examples.append("- 验证数据一致性")
            examples.append("- 测试并发更新冲突")
            
        elif method == "DELETE":
            examples.append("**DELETE请求测试重点**:")
            examples.append("- 验证资源删除成功")
            examples.append("- 测试不存在资源的处理")
            examples.append("- 验证级联删除（如果有）")
            examples.append("- 测试删除权限验证")
        
        # 通用测试指导
        examples.append("\n**通用测试要点**:")
        examples.append("- 验证HTTP状态码的正确性")
        examples.append("- 检查响应数据格式和结构")
        examples.append("- 验证错误消息的清晰性")
        examples.append("- 测试认证和授权（如果需要）")
        examples.append("- 验证响应时间在合理范围内")
        
        return "\n".join(examples)
    
    def _build_output_format_section(self) -> str:
        """构建输出格式部分"""
        format_section = """
## 输出格式要求

请严格按照以下JSON格式输出测试用例：

```json
{
  "test_cases": [
    {
      "title": "测试用例标题",
      "description": "详细的测试用例描述，说明测试目的和预期行为",
      "case_type": "positive|negative|boundary|security|performance",
      "priority": "critical|high|medium|low",
      "request_data": {
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer token"
        },
        "params": {
          "param1": "value1",
          "param2": "value2"
        },
        "body": {
          "field1": "value1",
          "field2": "value2"
        }
      },
      "expected_status_code": 200,
      "expected_response": {
        "code": 200,
        "message": "success",
        "data": {}
      },
      "assertions": [
        {
          "type": "status_code",
          "expected": 200,
          "description": "验证响应状态码为200"
        },
        {
          "type": "response_body",
          "field": "data.id",
          "expected": "not_null",
          "description": "验证返回的ID不为空"
        }
      ],
      "tags": ["smoke", "regression"]
    }
  ],
  "summary": "生成的测试用例总结",
  "recommendations": [
    "测试建议1",
    "测试建议2"
  ]
}
```

**重要说明**:
- case_type必须是: positive, negative, boundary, security, performance 之一
- priority必须是: critical, high, medium, low 之一
- request_data中只包含实际需要的字段（headers, params, body）
- assertions数组包含具体的验证点
- 每个测试用例都要有清晰的title和description
- tags用于标记测试用例的分类
"""
        
        return format_section.strip()
    
    def build_batch_generation_prompt(self, 
                                    analysis_result: DocumentAnalysisResult,
                                    endpoints: List[APIEndpoint],
                                    config: GenerationConfig) -> str:
        """构建批量测试用例生成提示词
        
        Args:
            analysis_result: 文档分析结果
            endpoints: API端点列表
            config: 生成配置
            
        Returns:
            str: 构建的批量生成提示词
        """
        try:
            self.logger.info(f"构建批量测试生成提示词: {len(endpoints)}个端点")
            
            # API基本信息
            context = []
            context.append("## API文档信息")
            context.append(f"**API名称**: {analysis_result.title or '未提供'}")
            context.append(f"**API版本**: {analysis_result.version or '未提供'}")
            context.append(f"**基础URL**: {analysis_result.base_url or '未提供'}")
            context.append("")
            
            # 端点列表
            context.append("## 需要生成测试用例的端点")
            for i, endpoint in enumerate(endpoints, 1):
                context.append(f"### 端点 {i}: {endpoint.method.upper()} {endpoint.path}")
                context.append(f"**摘要**: {endpoint.summary or '未提供'}")
                context.append(f"**描述**: {endpoint.description or '未提供'}")
                
                if endpoint.parameters:
                    context.append("**参数**:")
                    for param in endpoint.parameters[:3]:  # 只显示前3个参数
                        if isinstance(param, dict):
                            name = param.get("name", "")
                            param_type = param.get("type", "")
                            required = "必需" if param.get("required", False) else "可选"
                            context.append(f"- {name} ({param_type}, {required})")
                
                context.append("")
            
            # 生成要求
            requirements = self._build_requirements_section(config)
            
            # 输出格式
            output_format = """
## 输出格式要求

请为每个端点生成测试用例，按照以下JSON格式输出：

```json
{
  "test_suites": [
    {
      "endpoint": "GET /api/users",
      "test_cases": [
        {
          "title": "获取用户列表-正常情况",
          "description": "验证正常获取用户列表的功能",
          "case_type": "positive",
          "priority": "high",
          "request_data": {
            "params": {"page": 1, "limit": 10}
          },
          "expected_status_code": 200,
          "assertions": [
            {
              "type": "status_code",
              "expected": 200,
              "description": "验证状态码为200"
            }
          ],
          "tags": ["smoke"]
        }
      ]
    }
  ],
  "summary": "批量生成的测试用例总结",
  "recommendations": ["建议1", "建议2"]
}
```
"""
            
            prompt = f"""
你是一个专业的API测试工程师，需要为多个API端点生成全面的测试用例。

{chr(10).join(context)}

{requirements}

{output_format}

请开始为所有端点生成测试用例：
"""
            
            self.logger.debug(f"批量提示词构建完成，长度: {len(prompt)}字符")
            return prompt.strip()
            
        except Exception as e:
            error_msg = f"构建批量测试生成提示词失败: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
