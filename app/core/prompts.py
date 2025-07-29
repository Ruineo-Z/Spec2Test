"""提示词工程模块

为AI测试用例生成提供专业的提示词模板和优化策略。
"""

from enum import Enum
from typing import Dict, List, Optional

from app.core.models import TestCaseType


class PromptType(str, Enum):
    """提示词类型"""

    NORMAL = "normal"
    ERROR = "error"
    EDGE = "edge"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"


class PromptTemplate:
    """提示词模板类"""

    def __init__(
        self,
        template: str,
        variables: List[str],
        description: str = "",
        examples: Optional[List[str]] = None,
    ):
        self.template = template
        self.variables = variables
        self.description = description
        self.examples = examples or []

    def format(self, **kwargs) -> str:
        """格式化提示词"""
        return self.template.format(**kwargs)

    def validate_variables(self, **kwargs) -> bool:
        """验证变量是否完整"""
        return all(var in kwargs for var in self.variables)


class PromptLibrary:
    """提示词库

    管理和提供各种类型的测试用例生成提示词模板。
    """

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """初始化提示词模板"""
        return {
            PromptType.NORMAL: PromptTemplate(
                template=self._get_normal_template(),
                variables=["endpoint_info", "custom_requirements"],
                description="生成正常流程测试用例的提示词",
                examples=[
                    "测试GET /api/users端点的正常获取用户列表功能",
                    "测试POST /api/orders端点的正常创建订单流程",
                ],
            ),
            PromptType.ERROR: PromptTemplate(
                template=self._get_error_template(),
                variables=["endpoint_info", "custom_requirements"],
                description="生成错误处理测试用例的提示词",
                examples=["测试无效参数时的400错误响应", "测试权限不足时的403错误响应"],
            ),
            PromptType.EDGE: PromptTemplate(
                template=self._get_edge_template(),
                variables=["endpoint_info", "custom_requirements"],
                description="生成边界值测试用例的提示词",
                examples=["测试字符串长度边界值", "测试数值范围边界值"],
            ),
            PromptType.SECURITY: PromptTemplate(
                template=self._get_security_template(),
                variables=["endpoint_info", "custom_requirements"],
                description="生成安全测试用例的提示词",
                examples=["测试SQL注入攻击防护", "测试XSS攻击防护"],
            ),
            PromptType.PERFORMANCE: PromptTemplate(
                template=self._get_performance_template(),
                variables=["endpoint_info", "custom_requirements"],
                description="生成性能测试用例的提示词",
                examples=["测试高并发场景下的响应时间", "测试大数据量处理性能"],
            ),
            PromptType.INTEGRATION: PromptTemplate(
                template=self._get_integration_template(),
                variables=["endpoint_info", "custom_requirements", "dependencies"],
                description="生成集成测试用例的提示词",
                examples=["测试与第三方服务的集成", "测试数据库事务一致性"],
            ),
        }

    def get_template(self, prompt_type: PromptType) -> Optional[PromptTemplate]:
        """获取指定类型的提示词模板"""
        return self.templates.get(prompt_type)

    def get_template_by_test_type(
        self, test_type: TestCaseType
    ) -> Optional[PromptTemplate]:
        """根据测试用例类型获取提示词模板"""
        mapping = {
            TestCaseType.NORMAL: PromptType.NORMAL,
            TestCaseType.ERROR: PromptType.ERROR,
            TestCaseType.EDGE: PromptType.EDGE,
            TestCaseType.SECURITY: PromptType.SECURITY,
        }

        prompt_type = mapping.get(test_type)
        return self.get_template(prompt_type) if prompt_type else None

    def _get_normal_template(self) -> str:
        """正常流程测试用例提示词模板"""
        return """
你是一个专业的API测试工程师，具有丰富的测试用例设计经验。请为以下API端点生成高质量的正常流程测试用例。

## API端点信息
{endpoint_info}

## 自定义需求
{custom_requirements}

## 任务要求
请生成3-5个覆盖正常业务流程的测试用例，确保：

### 测试覆盖范围
- 主要业务场景的正常执行路径
- 不同输入参数组合的有效场景
- 典型用户操作流程
- 数据创建、读取、更新、删除的正常流程

### 测试用例质量标准
1. **测试用例名称**：简洁明确，体现测试目标
2. **详细描述**：说明测试场景、预期行为和业务价值
3. **请求数据**：包含完整的路径参数、查询参数、请求头、请求体
4. **预期响应**：明确状态码、响应头、响应体结构和关键字段
5. **断言列表**：至少3个断言，覆盖状态码、数据格式、业务逻辑
6. **优先级**：1-5级，1为最高优先级

### 输出格式
请严格按照以下JSON格式返回：

```json
{{
  "test_cases": [
    {{
      "name": "测试用例名称",
      "description": "详细的测试场景描述，包括测试目标和预期行为",
      "request_data": {{
        "path_params": {{}},
        "query_params": {{}},
        "headers": {{}},
        "body": {{}}
      }},
      "expected_response": {{
        "status_code": 200,
        "headers": {{}},
        "body_schema": {{}},
        "key_fields": []
      }},
      "assertions": [
        "response.status_code == 200",
        "response.headers['content-type'] == 'application/json'",
        "具体的业务逻辑断言"
      ],
      "priority": 1,
      "tags": ["normal", "smoke"]
    }}
  ]
}}
```

### 注意事项
- 确保测试数据的真实性和有效性
- 考虑不同用户角色和权限场景
- 关注数据一致性和业务规则验证
- 避免过于复杂的测试场景，保持测试的可维护性
"""

    def _get_error_template(self) -> str:
        """错误处理测试用例提示词模板"""
        return """
你是一个专业的API测试工程师，专注于错误处理和异常场景测试。请为以下API端点生成全面的错误处理测试用例。

## API端点信息
{endpoint_info}

## 自定义需求
{custom_requirements}

## 任务要求
请生成3-5个覆盖各种错误场景的测试用例，重点关注：

### 错误场景分类
1. **客户端错误 (4xx)**
   - 400 Bad Request: 参数缺失、格式错误、类型不匹配
   - 401 Unauthorized: 认证失败、token无效
   - 403 Forbidden: 权限不足、资源访问被拒绝
   - 404 Not Found: 资源不存在、路径错误
   - 409 Conflict: 数据冲突、重复创建
   - 422 Unprocessable Entity: 业务规则验证失败

2. **服务端错误 (5xx)**
   - 500 Internal Server Error: 服务器内部错误
   - 503 Service Unavailable: 服务不可用

### 测试重点
- 参数验证：必填参数缺失、数据类型错误、格式不正确
- 业务规则：违反业务约束、数据完整性检查
- 权限控制：未授权访问、权限不足
- 资源状态：资源不存在、状态不允许操作
- 数据约束：唯一性冲突、外键约束

### 测试用例质量标准
1. **错误场景明确**：清楚说明触发错误的条件
2. **错误响应验证**：验证错误码、错误消息、错误详情
3. **边界条件**：测试临界值和极端情况
4. **安全考虑**：确保错误信息不泄露敏感数据

### 输出格式
```json
{{
  "test_cases": [
    {{
      "name": "错误场景测试用例名称",
      "description": "详细描述错误触发条件和预期的错误处理行为",
      "request_data": {{
        "path_params": {{}},
        "query_params": {{}},
        "headers": {{}},
        "body": {{}}
      }},
      "expected_response": {{
        "status_code": 400,
        "headers": {{}},
        "error_code": "VALIDATION_ERROR",
        "error_message": "参数验证失败",
        "error_details": {{}}
      }},
      "assertions": [
        "response.status_code == 400",
        "'error' in response.json()",
        "response.json()['error']['code'] == 'VALIDATION_ERROR'"
      ],
      "priority": 2,
      "tags": ["error", "validation"]
    }}
  ]
}}
```

### 注意事项
- 确保错误测试不会对系统造成负面影响
- 验证错误响应的一致性和标准化
- 关注错误信息的安全性，避免信息泄露
- 测试错误恢复和重试机制
"""

    def _get_edge_template(self) -> str:
        """边界值测试用例提示词模板"""
        return """
你是一个专业的API测试工程师，专精于边界值和极限场景测试。请为以下API端点生成全面的边界值测试用例。

## API端点信息
{endpoint_info}

## 自定义需求
{custom_requirements}

## 任务要求
请生成3-5个覆盖各种边界条件的测试用例，重点关注：

### 边界值类型
1. **数值边界**
   - 最小值/最大值 (min/max)
   - 零值和负值
   - 浮点数精度边界
   - 整数溢出边界

2. **字符串边界**
   - 空字符串和null值
   - 最小/最大长度
   - 特殊字符和Unicode字符
   - 格式边界（邮箱、URL、日期等）

3. **数组/集合边界**
   - 空数组/集合
   - 单元素数组
   - 最大元素数量
   - 嵌套结构深度

4. **时间边界**
   - 过去/未来时间
   - 时区边界
   - 日期格式边界
   - 时间精度边界

5. **业务边界**
   - 配额限制
   - 频率限制
   - 资源容量限制
   - 权限边界

### 测试策略
- **等价类划分**：识别有效和无效的等价类
- **边界值分析**：测试边界值及其邻近值
- **极值测试**：测试系统能处理的极限情况
- **组合测试**：多个边界条件的组合

### 输出格式
```json
{{
  "test_cases": [
    {{
      "name": "边界值测试用例名称",
      "description": "详细描述边界条件和测试目标",
      "request_data": {{
        "path_params": {{}},
        "query_params": {{}},
        "headers": {{}},
        "body": {{}}
      }},
      "expected_response": {{
        "status_code": 200,
        "headers": {{}},
        "body_schema": {{}},
        "boundary_validation": true
      }},
      "assertions": [
        "response.status_code in [200, 400]",
        "边界值处理正确性验证",
        "数据完整性检查"
      ],
      "priority": 3,
      "tags": ["edge", "boundary"],
      "boundary_type": "numeric|string|array|time|business"
    }}
  ]
}}
```

### 注意事项
- 确保边界测试覆盖所有关键参数
- 验证系统在边界条件下的稳定性
- 关注性能在边界条件下的表现
- 测试边界条件的组合效应
"""

    def _get_security_template(self) -> str:
        """安全测试用例提示词模板"""
        return """
你是一个专业的API安全测试工程师，具有丰富的安全漏洞发现和防护经验。请为以下API端点生成全面的安全测试用例。

## API端点信息
{endpoint_info}

## 自定义需求
{custom_requirements}

## 任务要求
请生成3-5个覆盖主要安全风险的测试用例，重点关注：

### 安全威胁分类
1. **注入攻击**
   - SQL注入 (SQLi)
   - NoSQL注入
   - 命令注入
   - LDAP注入
   - XPath注入

2. **跨站脚本攻击 (XSS)**
   - 反射型XSS
   - 存储型XSS
   - DOM型XSS

3. **认证和授权**
   - 认证绕过
   - 权限提升
   - 会话劫持
   - JWT攻击

4. **输入验证**
   - 缓冲区溢出
   - 格式字符串攻击
   - 路径遍历
   - 文件上传漏洞

5. **业务逻辑**
   - 竞态条件
   - 业务流程绕过
   - 价格篡改
   - 批量操作滥用

6. **信息泄露**
   - 敏感信息暴露
   - 错误信息泄露
   - 调试信息泄露

### 安全测试原则
- **最小权限原则**：验证权限控制的有效性
- **深度防御**：测试多层安全控制
- **安全默认**：验证默认配置的安全性
- **失败安全**：测试异常情况下的安全行为

### 输出格式
```json
{{
  "test_cases": [
    {{
      "name": "安全测试用例名称",
      "description": "详细描述安全威胁场景和测试目标",
      "attack_vector": "SQL_INJECTION|XSS|AUTH_BYPASS|...",
      "request_data": {{
        "path_params": {{}},
        "query_params": {{}},
        "headers": {{}},
        "body": {{}},
        "malicious_payload": "具体的攻击载荷"
      }},
      "expected_response": {{
        "status_code": 400,
        "security_headers": {{}},
        "no_sensitive_data": true,
        "attack_blocked": true
      }},
      "assertions": [
        "response.status_code in [400, 403, 422]",
        "攻击被成功阻止",
        "无敏感信息泄露",
        "安全日志记录正确"
      ],
      "priority": 1,
      "tags": ["security", "injection"],
      "risk_level": "HIGH|MEDIUM|LOW"
    }}
  ]
}}
```

### 安全注意事项
⚠️ **重要提醒**：
- 仅在授权的测试环境中执行安全测试
- 避免对生产环境造成实际危害
- 遵守负责任的漏洞披露原则
- 确保测试数据不包含真实的恶意代码
- 测试完成后清理所有测试数据

### 合规要求
- 遵循OWASP Top 10安全风险指南
- 符合相关行业安全标准
- 满足数据保护法规要求
"""

    def _get_performance_template(self) -> str:
        """性能测试用例提示词模板"""
        return """
你是一个专业的API性能测试工程师，专注于系统性能和可扩展性测试。请为以下API端点生成全面的性能测试用例。

## API端点信息
{endpoint_info}

## 自定义需求
{custom_requirements}

## 任务要求
请生成3-5个覆盖不同性能场景的测试用例，重点关注：

### 性能测试类型
1. **负载测试**
   - 正常负载下的性能表现
   - 预期用户数量的并发测试
   - 持续负载的稳定性测试

2. **压力测试**
   - 超出正常负载的极限测试
   - 系统崩溃点的确定
   - 恢复能力测试

3. **峰值测试**
   - 突发流量的处理能力
   - 短时间高并发测试
   - 流量峰值的响应时间

4. **容量测试**
   - 大数据量处理能力
   - 存储容量限制测试
   - 数据增长的性能影响

5. **稳定性测试**
   - 长时间运行的稳定性
   - 内存泄露检测
   - 资源使用监控

### 性能指标
- **响应时间**：平均、最大、95%分位数
- **吞吐量**：每秒请求数(RPS)、每秒事务数(TPS)
- **并发用户数**：同时在线用户数量
- **资源使用率**：CPU、内存、磁盘、网络
- **错误率**：请求失败率、超时率

### 输出格式
```json
{{
  "test_cases": [
    {{
      "name": "性能测试用例名称",
      "description": "详细描述性能测试场景和目标",
      "test_type": "LOAD|STRESS|SPIKE|VOLUME|ENDURANCE",
      "test_config": {{
        "concurrent_users": 100,
        "duration": "5m",
        "ramp_up_time": "1m",
        "data_size": "1MB"
      }},
      "request_data": {{
        "path_params": {{}},
        "query_params": {{}},
        "headers": {{}},
        "body": {{}}
      }},
      "performance_criteria": {{
        "max_response_time": "2s",
        "min_throughput": "100 RPS",
        "max_error_rate": "1%",
        "max_cpu_usage": "80%",
        "max_memory_usage": "70%"
      }},
      "assertions": [
        "平均响应时间 < 1s",
        "95%响应时间 < 2s",
        "错误率 < 1%",
        "吞吐量 >= 100 RPS"
      ],
      "priority": 2,
      "tags": ["performance", "load"]
    }}
  ]
}}
```

### 测试环境要求
- 使用与生产环境相似的硬件配置
- 确保网络环境的一致性
- 隔离其他系统的干扰
- 准备充足的测试数据

### 监控和分析
- 实时监控系统资源使用情况
- 记录详细的性能指标数据
- 分析性能瓶颈和优化建议
- 生成性能测试报告
"""

    def _get_integration_template(self) -> str:
        """集成测试用例提示词模板"""
        return """
你是一个专业的API集成测试工程师，专注于系统间集成和端到端测试。请为以下API端点生成全面的集成测试用例。

## API端点信息
{endpoint_info}

## 依赖服务信息
{dependencies}

## 自定义需求
{custom_requirements}

## 任务要求
请生成3-5个覆盖不同集成场景的测试用例，重点关注：

### 集成测试类型
1. **服务间集成**
   - 微服务之间的通信
   - API网关集成
   - 消息队列集成
   - 缓存系统集成

2. **数据库集成**
   - 数据一致性验证
   - 事务完整性测试
   - 数据同步测试
   - 备份恢复测试

3. **第三方服务集成**
   - 外部API调用
   - 支付网关集成
   - 认证服务集成
   - 通知服务集成

4. **端到端流程**
   - 完整业务流程测试
   - 用户旅程测试
   - 跨系统数据流测试

### 集成测试重点
- **数据一致性**：确保数据在系统间正确传递
- **事务完整性**：验证分布式事务的正确性
- **错误传播**：测试错误在系统间的传播和处理
- **性能影响**：评估集成对整体性能的影响
- **故障恢复**：测试系统故障时的恢复能力

### 输出格式
```json
{{
  "test_cases": [
    {{
      "name": "集成测试用例名称",
      "description": "详细描述集成场景和测试目标",
      "integration_type": "SERVICE|DATABASE|THIRD_PARTY|END_TO_END",
      "test_flow": [
        {{
          "step": 1,
          "action": "调用API端点",
          "service": "current_service",
          "request": {{}},
          "expected_result": "成功响应"
        }},
        {{
          "step": 2,
          "action": "验证下游服务调用",
          "service": "downstream_service",
          "verification": "数据正确传递"
        }}
      ],
      "request_data": {{
        "path_params": {{}},
        "query_params": {{}},
        "headers": {{}},
        "body": {{}}
      }},
      "expected_response": {{
        "status_code": 200,
        "headers": {{}},
        "body_schema": {{}}
      }},
      "integration_assertions": [
        "主服务响应正确",
        "下游服务调用成功",
        "数据一致性验证通过",
        "事务完整性保证"
      ],
      "dependencies": [
        {{
          "service": "user_service",
          "status": "available",
          "mock_required": false
        }}
      ],
      "priority": 2,
      "tags": ["integration", "e2e"]
    }}
  ]
}}
```

### 测试环境准备
- 确保所有依赖服务可用
- 准备测试数据和环境配置
- 配置服务间的网络连接
- 设置监控和日志收集

### 故障模拟
- 网络延迟和中断
- 服务不可用
- 数据库连接失败
- 第三方服务超时

### 数据管理
- 测试数据的创建和清理
- 数据隔离和并发控制
- 敏感数据的脱敏处理
"""


class PromptOptimizer:
    """提示词优化器

    根据API特征和历史生成效果优化提示词。
    """

    def __init__(self):
        self.optimization_rules = self._initialize_optimization_rules()

    def _initialize_optimization_rules(self) -> Dict[str, List[str]]:
        """初始化优化规则"""
        return {
            "api_complexity": [
                "对于复杂API，增加更多上下文信息",
                "对于简单API，简化提示词结构",
                "根据参数数量调整用例生成数量",
            ],
            "domain_specific": ["金融领域：强调数据精度和安全性", "电商领域：关注并发和一致性", "社交领域：重视隐私和权限控制"],
            "response_quality": ["根据历史生成质量调整温度参数", "优化示例和格式说明", "增强约束条件描述"],
        }

    def optimize_prompt(
        self,
        base_template: PromptTemplate,
        api_info: Dict,
        optimization_context: Optional[Dict] = None,
    ) -> PromptTemplate:
        """优化提示词模板

        Args:
            base_template: 基础模板
            api_info: API信息
            optimization_context: 优化上下文

        Returns:
            优化后的模板
        """
        optimized_template = base_template.template

        # 根据API复杂度优化
        if self._is_complex_api(api_info):
            optimized_template = self._add_complexity_guidance(optimized_template)

        # 根据领域特征优化
        domain = self._detect_domain(api_info)
        if domain:
            optimized_template = self._add_domain_guidance(optimized_template, domain)

        # 根据历史效果优化
        if optimization_context and "quality_feedback" in optimization_context:
            optimized_template = self._apply_quality_feedback(
                optimized_template, optimization_context["quality_feedback"]
            )

        return PromptTemplate(
            template=optimized_template,
            variables=base_template.variables,
            description=f"优化版本: {base_template.description}",
            examples=base_template.examples,
        )

    def _is_complex_api(self, api_info: Dict) -> bool:
        """判断API是否复杂"""
        complexity_indicators = [
            len(api_info.get("parameters", {})) > 5,
            len(api_info.get("responses", {})) > 3,
            "security" in api_info.get("tags", []),
            api_info.get("method", "").upper() in ["POST", "PUT", "PATCH"],
        ]
        return sum(complexity_indicators) >= 2

    def _detect_domain(self, api_info: Dict) -> Optional[str]:
        """检测API所属领域"""
        path = api_info.get("path", "").lower()
        description = api_info.get("description", "").lower()

        domain_keywords = {
            "finance": ["payment", "order", "transaction", "money", "price"],
            "social": ["user", "friend", "message", "post", "comment"],
            "ecommerce": ["product", "cart", "checkout", "inventory"],
            "content": ["article", "media", "upload", "download"],
        }

        for domain, keywords in domain_keywords.items():
            if any(keyword in path or keyword in description for keyword in keywords):
                return domain

        return None

    def _add_complexity_guidance(self, template: str) -> str:
        """为复杂API添加指导"""
        complexity_guidance = """

### 复杂API特别注意事项
- 仔细分析参数间的依赖关系
- 考虑多步骤操作的事务性
- 重点测试参数组合的有效性
- 增加对错误场景的覆盖
"""
        return template + complexity_guidance

    def _add_domain_guidance(self, template: str, domain: str) -> str:
        """添加领域特定指导"""
        domain_guidance = {
            "finance": """
### 金融领域特别要求
- 确保数值精度和货币格式正确
- 重点测试金额计算的准确性
- 验证交易的原子性和一致性
- 关注安全性和合规性要求
""",
            "social": """
### 社交领域特别要求
- 重点测试用户权限和隐私控制
- 验证内容审核和过滤机制
- 关注并发访问和数据一致性
- 测试通知和消息传递功能
""",
            "ecommerce": """
### 电商领域特别要求
- 重点测试库存管理和并发控制
- 验证价格计算和促销逻辑
- 关注订单状态流转的正确性
- 测试支付和物流集成
""",
        }

        guidance = domain_guidance.get(domain, "")
        return template + guidance

    def _apply_quality_feedback(self, template: str, feedback: Dict) -> str:
        """应用质量反馈优化"""
        if feedback.get("low_assertion_quality"):
            template += """

### 断言质量提升要求
- 每个测试用例至少包含5个具体的断言
- 断言应覆盖状态码、数据格式、业务逻辑
- 避免过于宽泛的断言，要具体和可验证
"""

        if feedback.get("insufficient_edge_cases"):
            template += """

### 边界场景增强要求
- 增加更多边界值和极限情况测试
- 考虑异常输入和错误处理
- 测试资源限制和性能边界
"""

        return template


# 全局提示词库实例
prompt_library = PromptLibrary()
prompt_optimizer = PromptOptimizer()


def get_optimized_prompt(
    test_type: TestCaseType, api_info: Dict, optimization_context: Optional[Dict] = None
) -> Optional[PromptTemplate]:
    """获取优化的提示词模板

    Args:
        test_type: 测试用例类型
        api_info: API信息
        optimization_context: 优化上下文

    Returns:
        优化后的提示词模板
    """
    base_template = prompt_library.get_template_by_test_type(test_type)
    if not base_template:
        return None

    return prompt_optimizer.optimize_prompt(
        base_template, api_info, optimization_context
    )
