"""AI测试用例生成器

基于LLM的智能测试用例生成，支持多种测试类型和质量控制。
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

# 移除LangChain依赖，直接使用OpenAI和Gemini
LANGCHAIN_AVAILABLE = False

try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from pydantic import BaseModel, Field

from app.config.settings import settings
from app.core.models import APIEndpoint, TestCase, TestCaseType
from app.core.prompts import PromptTemplate, get_optimized_prompt, prompt_library
from app.core.quality_control import QualityController, QualityReport
from app.utils.exceptions import LLMError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TestCaseGenerationRequest(BaseModel):
    """测试用例生成请求"""

    endpoint: APIEndpoint
    test_types: List[TestCaseType] = Field(
        default=[TestCaseType.NORMAL, TestCaseType.ERROR]
    )
    max_cases_per_type: int = Field(default=3, ge=1, le=10)
    include_edge_cases: bool = Field(default=True)
    include_security_tests: bool = Field(default=False)
    custom_requirements: Optional[str] = None


class GenerationResult(BaseModel):
    """生成结果"""

    test_cases: List[TestCase]
    generation_stats: Dict
    quality_score: float
    ai_analysis: str
    quality_summary: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class AITestCaseGenerator:
    """AI测试用例生成器

    基于LLM的智能测试用例生成，支持：
    - OpenAI GPT模型集成
    - LangChain调用链
    - 提示词工程
    - 用例质量控制
    - 去重和优先级排序
    """

    def __init__(self):
        """初始化生成器"""
        # 检查依赖可用性
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available")
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini library not available")
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain library not available")

        self.openai_client = None
        self.gemini_model = None
        self._initialize_llm()

        # 提示词模板
        self.prompt_templates = self._load_prompt_templates()

        # 初始化质量控制器
        self.quality_controller = QualityController(
            similarity_threshold=0.8,
            min_quality_threshold=getattr(settings, "MIN_QUALITY_THRESHOLD", 60.0),
        )

        # 质量控制配置
        self.quality_config = {
            "min_assertions": 2,
            "max_assertions": 8,
            "required_fields": [
                "name",
                "description",
                "request_data",
                "expected_response",
            ],
            "similarity_threshold": 0.8,
            "priority_weights": {
                TestCaseType.SECURITY: 1.0,
                TestCaseType.ERROR: 0.8,
                TestCaseType.EDGE: 0.6,
                TestCaseType.NORMAL: 0.4,
            },
        }

        # 生成统计
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_test_cases": 0,
            "average_quality_score": 0.0,
            "quality_distribution": {},
            "duplicate_count": 0,
            "filtered_count": 0,
        }

    def _initialize_llm(self) -> None:
        """初始化LLM客户端"""
        try:
            provider = settings.llm.provider

            if provider == "gemini":
                # 初始化Gemini客户端
                gemini_api_key = settings.llm.gemini_api_key
                if gemini_api_key and GEMINI_AVAILABLE:
                    import google.generativeai as genai

                    genai.configure(api_key=gemini_api_key)
                    model_name = settings.llm.gemini_model
                    self.gemini_model = genai.GenerativeModel(model_name)
                    logger.info(
                        f"Gemini client initialized successfully with model: {model_name}"
                    )
                elif not GEMINI_AVAILABLE:
                    logger.warning("Gemini library not available")
                else:
                    logger.warning("No Gemini API key found")

            elif provider == "openai":
                # 初始化OpenAI客户端
                openai_api_key = settings.llm.openai_api_key
                if openai_api_key and OPENAI_AVAILABLE:
                    self.openai_client = AsyncOpenAI(
                        api_key=openai_api_key, base_url=settings.llm.openai_base_url
                    )
                    logger.info("OpenAI client initialized successfully")
                elif not OPENAI_AVAILABLE:
                    logger.warning("OpenAI library not available")
                else:
                    logger.warning("No OpenAI API key found")

            else:
                logger.warning(f"Unknown LLM provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise LLMError(f"LLM初始化失败: {e}")

    def _load_prompt_templates(self) -> Dict[str, str]:
        """加载提示词模板"""
        templates = {
            "normal": """
你是一个专业的API测试工程师。请为以下API端点生成正常流程的测试用例。

API端点信息：
{endpoint_info}

自定义需求：
{custom_requirements}

请生成3-5个测试用例，每个测试用例应包含：
1. 测试用例名称
2. 详细描述
3. 请求数据（包括路径参数、查询参数、请求体）
4. 预期响应（状态码、响应体结构）
5. 断言列表
6. 优先级（1-5，1最高）

请以JSON格式返回，格式如下：
{
  "test_cases": [
    {
      "name": "测试用例名称",
      "description": "详细描述",
      "request_data": {},
      "expected_response": {},
      "assertions": [],
      "priority": 1
    }
  ]
}
""",
            "error": """
你是一个专业的API测试工程师。请为以下API端点生成错误处理的测试用例。

API端点信息：
{endpoint_info}

自定义需求：
{custom_requirements}

请重点关注以下错误场景：
- 参数缺失或无效
- 数据类型错误
- 权限不足
- 资源不存在
- 请求体格式错误

请生成3-5个错误测试用例，每个测试用例应包含：
1. 测试用例名称
2. 详细描述
3. 错误的请求数据
4. 预期的错误响应
5. 断言列表
6. 优先级

请以JSON格式返回。
""",
            "edge": """
你是一个专业的API测试工程师。请为以下API端点生成边界值测试用例。

API端点信息：
{endpoint_info}

自定义需求：
{custom_requirements}

请重点关注以下边界场景：
- 最大/最小值
- 空值和null
- 超长字符串
- 特殊字符
- 数组边界（空数组、单元素、大数组）

请生成3-5个边界测试用例，每个测试用例应包含：
1. 测试用例名称
2. 详细描述
3. 边界值请求数据
4. 预期响应
5. 断言列表
6. 优先级

请以JSON格式返回。
""",
            "security": """
你是一个专业的API安全测试工程师。请为以下API端点生成安全测试用例。

API端点信息：
{endpoint_info}

自定义需求：
{custom_requirements}

请重点关注以下安全场景：
- SQL注入
- XSS攻击
- 权限绕过
- 敏感信息泄露
- 输入验证绕过
- CSRF攻击

请生成3-5个安全测试用例，每个测试用例应包含：
1. 测试用例名称
2. 详细描述
3. 攻击载荷请求数据
4. 预期的安全响应
5. 安全断言列表
6. 高优先级

请以JSON格式返回。
""",
        }

        return templates

    async def generate_test_cases(
        self, request: TestCaseGenerationRequest
    ) -> GenerationResult:
        """生成测试用例

        Args:
            request: 生成请求

        Returns:
            生成结果

        Raises:
            LLMError: LLM调用失败
        """
        logger.info(f"Generating test cases for endpoint: {request.endpoint.path}")

        try:
            all_test_cases = []
            generation_stats = {
                "start_time": datetime.now(),
                "endpoint_path": request.endpoint.path,
                "method": request.endpoint.method,
                "requested_types": [t.value for t in request.test_types],
                "generated_by_type": {},
            }

            # 为每种测试类型生成用例
            for test_type in request.test_types:
                logger.info(f"Generating {test_type.value} test cases")

                type_cases, details = await self._generate_cases_by_type(
                    request.endpoint,
                    test_type,
                    request.max_cases_per_type,
                    request.custom_requirements,
                )

                all_test_cases.extend(type_cases)
                generation_stats["generated_by_type"][test_type.value] = len(type_cases)

            # 质量控制和优化
            (
                processed_cases,
                quality_reports,
                processing_stats,
            ) = self.quality_controller.process_test_cases(all_test_cases)

            # 计算质量评分
            quality_score = processing_stats["average_quality_score"]

            # 生成AI分析
            ai_analysis = await self._generate_analysis(
                request.endpoint, processed_cases, quality_reports
            )

            # 完成统计
            generation_stats.update(
                {
                    "end_time": datetime.now(),
                    "total_generated": len(all_test_cases),
                    "after_processing": len(processed_cases),
                    "duplicate_removed": processing_stats["duplicate_count"],
                    "low_quality_filtered": processing_stats["low_quality_count"],
                    "final_count": len(processed_cases),
                    "quality_score": quality_score,
                    "generation_time": (
                        datetime.now() - generation_stats["start_time"]
                    ).total_seconds(),
                }
            )

            logger.info(
                f"Generated {len(processed_cases)} test cases with quality score {quality_score:.2f}"
            )

            return GenerationResult(
                test_cases=processed_cases,
                generation_stats=generation_stats,
                quality_score=quality_score,
                ai_analysis=ai_analysis,
                quality_summary=self.quality_controller.generate_quality_summary(
                    quality_reports, processing_stats
                ),
            )

        except Exception as e:
            logger.error(f"Failed to generate test cases: {e}")
            raise LLMError(f"测试用例生成失败: {e}")

    async def _generate_cases_by_type(
        self,
        endpoint: APIEndpoint,
        test_type: TestCaseType,
        max_cases: int,
        custom_requirements: Optional[str],
    ) -> Tuple[List[TestCase], Dict]:
        """按类型生成测试用例

        Returns:
            (测试用例列表, 生成详情)
        """
        generation_details = {
            "test_type": test_type,
            "requested_count": max_cases,
            "actual_count": 0,
            "prompt_used": None,
            "llm_response_length": 0,
            "parsing_errors": [],
        }

        # 获取优化的提示词模板
        prompt_template = get_optimized_prompt(
            test_type=test_type,
            api_info=self._get_endpoint_dict(endpoint),
            optimization_context={"quality_feedback": self._get_quality_feedback()},
        )

        if not prompt_template:
            template_key = test_type.value
            if template_key not in self.prompt_templates:
                logger.warning(f"No template found for test type: {test_type}")
                return [], generation_details
            prompt_template = self.prompt_templates[template_key]

        # 准备端点信息
        endpoint_info = self._format_endpoint_info(endpoint)

        # 构建提示词
        if hasattr(prompt_template, "format"):
            prompt = prompt_template.format(
                endpoint_info=endpoint_info,
                custom_requirements=custom_requirements or "无特殊要求",
            )
        else:
            prompt = str(prompt_template)

        generation_details["prompt_used"] = (
            prompt[:200] + "..." if len(prompt) > 200 else prompt
        )

        # 检查LLM是否可用
        if not self.is_available():
            provider = settings.llm.provider
            if provider == "gemini":
                if not settings.llm.gemini_api_key:
                    raise ValueError("缺少Gemini API Key，请在.env文件中配置GEMINI_API_KEY")
                elif not GEMINI_AVAILABLE:
                    raise ValueError("Gemini库未安装，请运行: pip install google-generativeai")
                else:
                    raise ValueError("Gemini客户端初始化失败，请检查API Key是否正确")
            elif provider == "openai":
                if not settings.llm.openai_api_key:
                    raise ValueError("缺少OpenAI API Key，请在.env文件中配置OPENAI_API_KEY")
                elif not OPENAI_AVAILABLE:
                    raise ValueError("OpenAI库未安装，请运行: pip install openai")
                else:
                    raise ValueError("OpenAI客户端初始化失败，请检查API Key是否正确")
            else:
                raise ValueError(f"不支持的LLM提供商: {provider}，请配置正确的LLM服务")

        # 调用LLM生成测试用例
        try:
            response = await self._call_llm(prompt)
            generation_details["llm_response_length"] = len(response)

            # 解析响应
            test_cases, parsing_errors = self._parse_llm_response(
                response, endpoint, test_type
            )
            generation_details["parsing_errors"] = parsing_errors
            
            # 检查生成质量，如果解析错误太多或测试用例为空，说明接口文档不够清晰
            if len(parsing_errors) > 0 or len(test_cases) == 0:
                error_msg = "接口文档信息不够清晰，LLM无法准确生成测试用例。请提供更详细和准确的接口文档，包括：\n"
                error_msg += "1. 完整的请求参数定义和类型\n"
                error_msg += "2. 详细的响应结构说明\n"
                error_msg += "3. 必要的示例数据\n"
                if parsing_errors:
                    error_msg += f"\n解析错误详情: {'; '.join(parsing_errors)}"
                raise ValueError(error_msg)

        except ValueError as e:
            # 重新抛出配置错误和文档质量错误
            raise e
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise ValueError(f"LLM服务调用失败，请检查网络连接和API配置: {str(e)}")

        generation_details["actual_count"] = len(test_cases)

        # 限制数量
        return test_cases[:max_cases], generation_details

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM API（支持OpenAI和Gemini）"""
        provider = settings.llm.provider

        if provider == "gemini":
            return await self._call_gemini(prompt)
        elif provider == "openai":
            return await self._call_openai(prompt)
        else:
            raise LLMError(f"Unsupported LLM provider: {provider}")

    async def _call_gemini(self, prompt: str) -> str:
        """调用Gemini API"""
        if not self.gemini_model:
            raise LLMError("Gemini client not initialized")

        try:
            # 构建完整的提示词
            full_prompt = f"""你是一个专业的API测试工程师，擅长生成高质量的测试用例。

{prompt}"""
            
            logger.info(f"Calling Gemini API with prompt length: {len(full_prompt)}")
            logger.debug(f"Prompt preview: {full_prompt[:200]}...")

            # 调用Gemini API（带超时）
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.gemini_model.generate_content,
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=settings.llm.temperature,
                        max_output_tokens=settings.llm.max_tokens,
                    ),
                ),
                timeout=settings.llm.timeout  # 使用配置的超时时间
            )
            
            logger.info("Gemini API call completed")

            # 检查响应是否有效
            if not response:
                raise LLMError("Gemini返回空响应对象")

            # 检查是否被安全过滤器阻止
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    # finish_reason: 1=STOP(正常), 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION, 5=OTHER
                    if candidate.finish_reason == 3:  # SAFETY
                        raise LLMError("响应被Gemini安全过滤器阻止")
                    elif candidate.finish_reason == 4:  # RECITATION
                        raise LLMError("响应被Gemini重复内容过滤器阻止")

            # 获取响应文本
            if hasattr(response, "text") and response.text:
                return response.text
            else:
                # 如果response.text为空，尝试从candidates中获取
                if hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, "content") and candidate.content:
                        if (
                            hasattr(candidate.content, "parts")
                            and candidate.content.parts
                        ):
                            part = candidate.content.parts[0]
                            if hasattr(part, "text") and part.text:
                                return part.text

                raise LLMError("Gemini返回空文本响应")

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise LLMError(f"Gemini API调用失败: {e}")

    async def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API"""
        if not self.openai_client:
            raise LLMError("OpenAI client not initialized")

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.llm.openai_model,
                messages=[
                    {"role": "system", "content": "你是一个专业的API测试工程师，擅长生成高质量的测试用例。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise LLMError(f"OpenAI API调用失败: {e}")

    def _get_endpoint_dict(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """获取端点信息字典"""
        endpoint_dict = {
            "path": endpoint.path,
            "method": endpoint.method.value
            if hasattr(endpoint.method, "value")
            else str(endpoint.method),
            "description": endpoint.description or "无描述",
            "tags": getattr(endpoint, "tags", []),
            "parameters": {},
            "responses": getattr(endpoint, "responses", {}),
        }

        # 合并所有参数
        if hasattr(endpoint, "path_parameters") and endpoint.path_parameters:
            endpoint_dict["parameters"].update(endpoint.path_parameters)
        if hasattr(endpoint, "query_parameters") and endpoint.query_parameters:
            endpoint_dict["parameters"].update(endpoint.query_parameters)
        if hasattr(endpoint, "header_parameters") and endpoint.header_parameters:
            endpoint_dict["parameters"].update(endpoint.header_parameters)

        # 添加请求体信息
        if hasattr(endpoint, "request_body") and endpoint.request_body:
            endpoint_dict["request_body"] = endpoint.request_body

        return endpoint_dict

    def _format_endpoint_info(self, endpoint: APIEndpoint) -> str:
        """格式化端点信息"""
        info = f"""
路径: {endpoint.path}
方法: {endpoint.method}
描述: {endpoint.description or '无描述'}
"""

        # 格式化参数信息
        if endpoint.path_parameters:
            info += f"\n路径参数: {json.dumps(endpoint.path_parameters, indent=2, ensure_ascii=False)}"

        if endpoint.query_parameters:
            info += f"\n查询参数: {json.dumps(endpoint.query_parameters, indent=2, ensure_ascii=False)}"

        if endpoint.header_parameters:
            info += f"\n请求头参数: {json.dumps(endpoint.header_parameters, indent=2, ensure_ascii=False)}"

        if endpoint.request_body:
            info += f"\n请求体: {json.dumps(endpoint.request_body, indent=2, ensure_ascii=False)}"

        if endpoint.responses:
            info += (
                f"\n响应: {json.dumps(endpoint.responses, indent=2, ensure_ascii=False)}"
            )

        return info

    def _generate_mock_test_cases(
        self, endpoint: APIEndpoint, test_type: TestCaseType, max_cases: int
    ) -> List[TestCase]:
        """生成模拟测试用例（当AI生成器不可用时使用）"""
        test_cases = []

        for i in range(min(max_cases, 3)):  # 最多生成3个模拟用例
            case_id = str(uuid4())

            if test_type == TestCaseType.NORMAL:
                test_case = TestCase(
                    id=case_id,
                    name=f"正常流程测试_{i+1}",
                    description=f"测试{endpoint.path}的正常请求流程",
                    type=test_type,
                    endpoint=endpoint,
                    test_data=self._generate_mock_request_data(endpoint, "normal"),
                    expected_response={"status": "success", "data": {}},
                    expected_status_code=200,
                    test_steps=[
                        {
                            "step": 1,
                            "action": "发送正常请求",
                            "description": "向API端点发送正常的请求数据",
                        },
                        {
                            "step": 2,
                            "action": "验证响应状态码",
                            "description": "检查返回的HTTP状态码是否为200",
                        },
                        {
                            "step": 3,
                            "action": "验证响应数据格式",
                            "description": "验证响应数据的结构和内容",
                        },
                    ],
                    preconditions=["API服务正常运行"],
                    postconditions=["数据状态正确更新"],
                    priority=2,
                    tags=[test_type.value, "mock"],
                    created_at=datetime.now(),
                )
            elif test_type == TestCaseType.ERROR:
                test_case = TestCase(
                    id=case_id,
                    name=f"错误处理测试_{i+1}",
                    description=f"测试{endpoint.path}的错误处理逻辑",
                    type=test_type,
                    endpoint=endpoint,
                    test_data=self._generate_mock_request_data(endpoint, "error"),
                    expected_response={"error": "Invalid request", "code": 400},
                    expected_status_code=400,
                    test_steps=[
                        {
                            "step": 1,
                            "action": "发送无效请求",
                            "description": "向API端点发送无效的请求数据",
                        },
                        {
                            "step": 2,
                            "action": "验证错误响应",
                            "description": "检查返回的HTTP错误状态码",
                        },
                        {
                            "step": 3,
                            "action": "验证错误信息格式",
                            "description": "验证错误响应的格式和内容",
                        },
                    ],
                    preconditions=["API服务正常运行"],
                    postconditions=["系统状态保持稳定"],
                    priority=3,
                    tags=[test_type.value, "mock"],
                    created_at=datetime.now(),
                )
            elif test_type == TestCaseType.EDGE:
                test_case = TestCase(
                    id=case_id,
                    name=f"边界值测试_{i+1}",
                    description=f"测试{endpoint.path}的边界值处理",
                    type=test_type,
                    endpoint=endpoint,
                    test_data=self._generate_mock_request_data(endpoint, "edge"),
                    expected_response={"status": "success", "data": {}},
                    expected_status_code=200,
                    test_steps=[
                        {
                            "step": 1,
                            "action": "发送边界值请求",
                            "description": "向API端点发送边界值数据",
                        },
                        {
                            "step": 2,
                            "action": "验证边界值处理",
                            "description": "检查系统对边界值的处理逻辑",
                        },
                        {
                            "step": 3,
                            "action": "验证响应正确性",
                            "description": "验证边界值场景下的响应正确性",
                        },
                    ],
                    preconditions=["API服务正常运行"],
                    postconditions=["边界值正确处理"],
                    priority=3,
                    tags=[test_type.value, "mock"],
                    created_at=datetime.now(),
                )
            else:  # SECURITY
                test_case = TestCase(
                    id=case_id,
                    name=f"安全测试_{i+1}",
                    description=f"测试{endpoint.path}的安全防护",
                    type=test_type,
                    endpoint=endpoint,
                    test_data=self._generate_mock_request_data(endpoint, "security"),
                    expected_response={"error": "Unauthorized", "code": 401},
                    expected_status_code=401,
                    test_steps=[
                        {
                            "step": 1,
                            "action": "发送恶意请求",
                            "description": "向API端点发送潜在恶意的请求",
                        },
                        {"step": 2, "action": "验证安全防护", "description": "检查系统的安全防护机制"},
                        {"step": 3, "action": "验证拒绝访问", "description": "验证系统正确拒绝恶意访问"},
                    ],
                    preconditions=["API服务正常运行"],
                    postconditions=["安全防护生效"],
                    priority=1,
                    tags=[test_type.value, "mock"],
                    created_at=datetime.now(),
                )

            test_cases.append(test_case)

        return test_cases

    def _generate_mock_request_data(
        self, endpoint: APIEndpoint, scenario: str
    ) -> Dict[str, Any]:
        """生成模拟请求数据"""
        mock_data = {}

        # 基于端点的请求体生成模拟数据
        if endpoint.request_body and isinstance(endpoint.request_body, dict):
            properties = endpoint.request_body.get("properties", {})
            if properties:  # 只有当properties不为空时才使用
                for field_name, field_info in properties.items():
                    if scenario == "normal":
                        mock_data[field_name] = self._generate_mock_field_value(
                            field_info, "normal"
                        )
                    elif scenario == "error":
                        mock_data[field_name] = self._generate_mock_field_value(
                            field_info, "invalid"
                        )
                    elif scenario == "edge":
                        mock_data[field_name] = self._generate_mock_field_value(
                            field_info, "edge"
                        )
                    elif scenario == "security":
                        mock_data[field_name] = self._generate_mock_field_value(
                            field_info, "malicious"
                        )
            else:
                # request_body存在但properties为空，使用智能生成
                logger.info(f"Empty properties in request_body for {endpoint.path}, using smart mock data")
                mock_data = self._generate_smart_mock_data(endpoint, scenario)
        else:
            # 当没有明确的请求体定义时，根据端点路径和方法智能生成数据
            logger.info(f"No request_body found for {endpoint.path}, using smart mock data")
            mock_data = self._generate_smart_mock_data(endpoint, scenario)

        return mock_data

    def _generate_smart_mock_data(
        self, endpoint: APIEndpoint, scenario: str
    ) -> Dict[str, Any]:
        """根据端点路径和方法智能生成模拟数据"""
        logger.info(f"Generating smart mock data for {endpoint.path} ({scenario})")
        mock_data = {}
        path = endpoint.path.lower()
        method = endpoint.method.value.upper()
        
        # 根据端点路径推断数据结构
        if "/chapter/generate" in path:
            if scenario == "normal":
                mock_data = {
                    "prompt": "请生成一个关于勇敢冒险的小说章节",
                    "max_tokens": 2000
                }
            elif scenario == "error":
                mock_data = {
                    "prompt": "",  # 空提示词
                    "max_tokens": -1  # 无效值
                }
        elif "/chapter/choices" in path:
            if scenario == "normal":
                mock_data = {
                    "chapter_id": "chapter_123456"
                }
            elif scenario == "error":
                mock_data = {
                    "chapter_id": ""  # 空ID
                }
        elif "/user/register" in path:
            if scenario == "normal":
                mock_data = {
                    "email": "test@example.com",
                    "password": "SecurePass123!"
                }
            elif scenario == "error":
                mock_data = {
                    "email": "invalid-email",  # 无效邮箱格式
                    "password": "123"  # 密码太短
                }
        elif "/user/login" in path:
            if scenario == "normal":
                mock_data = {
                    "email": "test@example.com",
                    "password": "SecurePass123!"
                }
            elif scenario == "error":
                mock_data = {
                    "email": "wrong@example.com",
                    "password": "wrongpassword"
                }
        elif "/plan/save" in path:
            if scenario == "normal":
                mock_data = {
                    "title": "我的小说创作计划",
                    "summary": "这是一个关于科幻冒险的小说创作计划"
                }
            elif scenario == "error":
                mock_data = {
                    "title": "",  # 空标题
                    "summary": ""  # 空摘要
                }
        elif "/feedback" in path:
            if scenario == "normal":
                mock_data = {
                    "message": "产品很好用，希望能增加更多功能",
                    "email": "user@example.com"
                }
            elif scenario == "error":
                mock_data = {
                    "message": "",  # 空反馈
                    "email": "invalid-email"
                }
        else:
            # 通用数据生成逻辑
            if method in ["POST", "PUT", "PATCH"]:
                if scenario == "normal":
                    mock_data = {
                        "name": "测试数据",
                        "description": "这是一个测试描述",
                        "value": 123
                    }
                elif scenario == "error":
                    mock_data = {
                        "name": "",  # 空名称
                        "value": "invalid"  # 无效值
                    }
        
        return mock_data

    def _generate_mock_field_value(
        self, field_info: Dict[str, Any], scenario: str
    ) -> Any:
        """生成模拟字段值"""
        field_type = field_info.get("type", "string")

        if scenario == "normal":
            if field_type == "string":
                return "test_value"
            elif field_type == "integer":
                return 123
            elif field_type == "number":
                return 123.45
            elif field_type == "boolean":
                return True
            elif field_type == "array":
                return ["item1", "item2"]
            else:
                return "test_value"
        elif scenario == "invalid":
            if field_type == "string":
                return None  # 无效值
            elif field_type == "integer":
                return "not_a_number"  # 类型错误
            elif field_type == "number":
                return "not_a_number"
            elif field_type == "boolean":
                return "not_a_boolean"
            else:
                return None
        elif scenario == "edge":
            if field_type == "string":
                return ""  # 空字符串
            elif field_type == "integer":
                return 0  # 边界值
            elif field_type == "number":
                return 0.0
            elif field_type == "boolean":
                return False
            elif field_type == "array":
                return []  # 空数组
            else:
                return ""
        elif scenario == "malicious":
            if field_type == "string":
                return "<script>alert('xss')</script>"  # XSS攻击
            elif field_type == "integer":
                return 999999999  # 超大数值
            elif field_type == "number":
                return 999999999.99
            else:
                return "../../../etc/passwd"  # 路径遍历攻击

        return "test_value"

    def _parse_llm_response(
        self, response: str, endpoint: APIEndpoint, test_type: TestCaseType
    ) -> Tuple[List[TestCase], List[str]]:
        """解析LLM响应

        Returns:
            (测试用例列表, 解析错误列表)
        """
        parsing_errors = []

        try:
            # 清理响应文本
            cleaned_response = self._clean_llm_response(response)

            # 尝试直接解析清理后的响应
            try:
                data = json.loads(cleaned_response)
            except json.JSONDecodeError:
                # 如果直接解析失败，尝试提取JSON部分
                json_match = re.search(r"\{.*\}", cleaned_response, re.DOTALL)
                if not json_match:
                    parsing_errors.append("No JSON found in LLM response")
                    logger.warning(
                        f"No JSON found in LLM response. Response: {response[:200]}..."
                    )
                    return [], parsing_errors

                data = json.loads(json_match.group())
            test_cases = []

            for i, case_data in enumerate(data.get("test_cases", [])):
                try:
                    # 验证必要字段
                    if not case_data.get("name"):
                        parsing_errors.append(f"Test case {i+1}: Missing name")
                        continue

                    if not case_data.get("description"):
                        parsing_errors.append(f"Test case {i+1}: Missing description")

                    test_case = TestCase(
                        id=str(uuid4()),
                        name=case_data.get("name", f"Test case for {endpoint.path}"),
                        description=case_data.get("description", ""),
                        type=test_type,
                        endpoint=endpoint,
                        test_data=case_data.get("request_data", {}),
                        expected_response=case_data.get("expected_response", {}),
                        expected_status_code=case_data.get("expected_status_code", 200),
                        test_steps=case_data.get("test_steps", []),
                        preconditions=case_data.get("preconditions", []),
                        postconditions=case_data.get("postconditions", []),
                        priority=case_data.get("priority", 3),
                        tags=case_data.get("tags", [test_type.value]),
                        created_at=datetime.now(),
                    )
                    test_cases.append(test_case)

                except Exception as e:
                    parsing_errors.append(f"Test case {i+1}: {str(e)}")
                    continue

            return test_cases, parsing_errors

        except json.JSONDecodeError as e:
            parsing_errors.append(f"JSON parsing failed: {str(e)}")
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return [], parsing_errors
        except Exception as e:
            parsing_errors.append(f"Response parsing failed: {str(e)}")
            logger.error(f"Error parsing LLM response: {e}")
            return [], parsing_errors

    def _clean_llm_response(self, response: str) -> str:
        """清理LLM响应文本"""
        # 移除代码块标记
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        # 查找JSON内容
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1

        if start_idx != -1 and end_idx > start_idx:
            response = response[start_idx:end_idx]

        return response.strip()

    def _get_quality_feedback(self) -> Dict:
        """获取质量反馈用于提示词优化"""
        feedback = {}

        # 基于历史统计生成反馈
        if self.generation_stats["total_test_cases"] > 0:
            avg_quality = self.generation_stats["average_quality_score"]

            if avg_quality < 70:
                feedback["low_assertion_quality"] = True
                feedback["insufficient_edge_cases"] = True

            # 基于质量分布调整
            quality_dist = self.generation_stats.get("quality_distribution", {})
            poor_ratio = quality_dist.get("poor", 0) + quality_dist.get(
                "unacceptable", 0
            )
            total_cases = sum(quality_dist.values()) if quality_dist else 1

            if poor_ratio / total_cases > 0.3:
                feedback["improve_specificity"] = True
                feedback["enhance_clarity"] = True

        return feedback

    def _remove_duplicates(self, test_cases: List[TestCase]) -> List[TestCase]:
        """去重"""
        unique_cases = []
        seen_signatures = set()

        for case in test_cases:
            # 创建用例签名
            signature = self._create_case_signature(case)

            if signature not in seen_signatures:
                unique_cases.append(case)
                seen_signatures.add(signature)
            else:
                logger.debug(f"Duplicate test case removed: {case.name}")

        return unique_cases

    def _create_case_signature(self, test_case: TestCase) -> str:
        """创建用例签名用于去重"""
        return f"{test_case.endpoint_path}:{test_case.method}:{test_case.test_type.value}:{hash(str(test_case.request_data))}"

    def _sort_by_priority(self, test_cases: List[TestCase]) -> List[TestCase]:
        """按优先级排序"""

        def priority_key(case: TestCase) -> Tuple[float, int]:
            type_weight = self.quality_config["priority_weights"].get(
                case.test_type, 0.5
            )
            return (type_weight, -case.priority)  # 负号使高优先级排在前面

        return sorted(test_cases, key=priority_key, reverse=True)

    def _calculate_quality_score(self, test_cases: List[TestCase]) -> float:
        """计算质量评分"""
        if not test_cases:
            return 0.0

        total_score = 0.0

        for case in test_cases:
            score = 0.0

            # 基础分数
            score += 20

            # 描述质量
            if len(case.description) > 10:
                score += 15

            # 测试步骤数量（替代断言数量）
            steps_count = len(case.test_steps) if case.test_steps else 0
            if steps_count >= 2:  # 至少需要2个测试步骤
                score += min(steps_count * 5, 25)

            # 测试数据完整性
            if case.test_data:
                score += 15

            # 预期响应完整性
            if case.expected_response:
                score += 15

            # 优先级合理性
            if 1 <= case.priority <= 5:
                score += 10

            total_score += score

        return min(total_score / len(test_cases), 100.0)

    async def _generate_analysis(
        self,
        endpoint: APIEndpoint,
        test_cases: List[TestCase],
        quality_reports: List[QualityReport] = None,
    ) -> str:
        """生成AI分析"""
        try:
            quality_summary = ""
            if quality_reports:
                avg_quality = sum(r.overall_score for r in quality_reports) / len(
                    quality_reports
                )
                quality_summary = f"\n平均质量分数: {avg_quality:.1f}"

            analysis_prompt = f"""
请分析以下API端点的测试用例生成结果：

端点: {endpoint.path} ({endpoint.method})
生成的测试用例数量: {len(test_cases)}
测试类型分布: {self._get_type_distribution(test_cases)}{quality_summary}

请提供：
1. 测试覆盖率评估
2. 潜在遗漏的测试场景
3. 测试用例质量评价
4. 改进建议

请用中文回答，控制在200字以内。
"""

            if self.is_available():
                response = await self._call_llm(analysis_prompt)
                return response.strip()
            else:
                return "基于生成的测试用例，覆盖了主要的功能场景。建议补充更多边界值和异常情况的测试。"

        except Exception as e:
            logger.error(f"Failed to generate analysis: {e}")
            return "AI分析生成失败，但测试用例已成功生成。"

    def _get_type_distribution(self, test_cases: List[TestCase]) -> Dict[str, int]:
        """获取测试类型分布"""
        distribution = {}
        for case in test_cases:
            type_name = case.type.value
            distribution[type_name] = distribution.get(type_name, 0) + 1
        return distribution

    def is_available(self) -> bool:
        """检查生成器是否可用"""
        provider = settings.llm.provider
        if provider == "gemini":
            # 检查API Key是否配置
            if not settings.llm.gemini_api_key:
                return False
            # 检查库是否可用
            if not GEMINI_AVAILABLE:
                return False
            return self.gemini_model is not None
        elif provider == "openai":
            # 检查API Key是否配置
            if not settings.llm.openai_api_key:
                return False
            # 检查库是否可用
            if not OPENAI_AVAILABLE:
                return False
            return self.openai_client is not None
        return False

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        provider = settings.llm.provider

        status = {
            "available": self.is_available(),
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
        }

        if provider == "gemini":
            status["gemini_model"] = self.gemini_model is not None
            status["model_name"] = settings.llm.gemini_model
        elif provider == "openai":
            status["openai_client"] = self.openai_client is not None
            status["model_name"] = settings.llm.openai_model

        if self.is_available():
            try:
                # 简单的测试调用
                test_response = await self._call_llm(
                    "Hello, this is a test. Please respond with 'OK'."
                )
                status["test_call"] = "success" if "OK" in test_response else "partial"
            except Exception as e:
                status["test_call"] = f"failed: {str(e)}"

        return status
