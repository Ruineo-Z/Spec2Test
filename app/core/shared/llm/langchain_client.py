"""
LangChain + Instructor集成LLM客户端

使用LangChain和Instructor提供统一的LLM接口，支持结构化输出。
"""

import json
from typing import Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel

from .base import BaseLLMClient, LLMProvider, LLMResponse, LLMError, LLMTaskType
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)

# 泛型类型
T = TypeVar('T', bound=BaseModel)

# 检查依赖是否可用
try:
    import instructor
    from langchain_community.llms import Ollama
    from langchain_community.chat_models import ChatOllama
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage
    from openai import OpenAI
    HAS_LANGCHAIN = True
except ImportError as e:
    logger.warning(f"LangChain依赖不可用: {e}")
    HAS_LANGCHAIN = False


class LangChainLLMClient(BaseLLMClient):
    """基于LangChain的LLM客户端基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化LangChain LLM客户端
        
        Args:
            config: LLM配置参数
        """
        if not HAS_LANGCHAIN:
            raise LLMError("LangChain依赖不可用，请安装: pip install langchain instructor")
        
        super().__init__(config)
        self.llm = None
        self.instructor_client = None
        self._setup_clients()
    
    def _setup_clients(self):
        """设置LangChain和Instructor客户端"""
        # 子类实现具体的客户端设置
        pass
    
    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的文本响应
        """
        try:
            if not self.llm:
                raise LLMError("LLM客户端未初始化")
            
            # 使用LangChain生成文本
            response = self.llm.invoke(prompt)
            
            # 构建响应
            return self._create_response(
                content=response,
                metadata={"prompt_length": len(prompt)},
                task_type=LLMTaskType.TEXT_GENERATION.value
            )
            
        except Exception as e:
            error_msg = f"LangChain文本生成失败: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_response(error_msg, LLMTaskType.TEXT_GENERATION.value)
    
    def generate_structured(self, prompt: str, response_model: Type[T], **kwargs) -> T:
        """生成结构化输出
        
        Args:
            prompt: 输入提示词
            response_model: Pydantic模型类
            **kwargs: 其他参数
            
        Returns:
            T: 结构化输出对象
        """
        try:
            if not self.instructor_client:
                raise LLMError("Instructor客户端未初始化")
            
            # 使用Instructor生成结构化输出
            response = self.instructor_client.chat.completions.create(
                model=self.model,
                response_model=response_model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            return response
            
        except Exception as e:
            error_msg = f"结构化输出生成失败: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg, provider=self.provider.value)
    
    def analyze_document(self, content: str, document_type: str = "auto", **kwargs) -> LLMResponse:
        """分析文档内容
        
        Args:
            content: 文档内容
            document_type: 文档类型
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 文档分析结果
        """
        try:
            # 构建文档分析提示词
            prompt = f"""
请分析以下{document_type}文档内容，并提供详细的分析结果：

文档内容：
{content}

请从以下几个方面进行分析：
1. 文档类型和格式识别
2. 主要内容结构分析
3. API端点信息提取（如果是API文档）
4. 数据模型定义分析
5. 潜在问题识别
6. 改进建议

请以结构化的JSON格式返回分析结果。
"""
            
            response = self.generate_text(prompt, **kwargs)
            if response.success:
                response.task_type = LLMTaskType.DOCUMENT_ANALYSIS.value
                response.metadata["document_type"] = document_type
                response.metadata["content_length"] = len(content)
            
            return response
            
        except Exception as e:
            error_msg = f"文档分析失败: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_response(error_msg, LLMTaskType.DOCUMENT_ANALYSIS.value)
    
    def generate_test_cases(self, api_spec: Dict[str, Any], **kwargs) -> LLMResponse:
        """生成测试用例
        
        Args:
            api_spec: API规范
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的测试用例
        """
        try:
            # 构建测试用例生成提示词
            api_spec_json = json.dumps(api_spec, indent=2, ensure_ascii=False)
            
            prompt = f"""
基于以下API规范，生成全面的测试用例：

API规范：
{api_spec_json}

请生成以下类型的测试用例：
1. 正常流程测试用例（Happy Path）
2. 边界值测试用例（Boundary Testing）
3. 异常情况测试用例（Error Handling）
4. 安全性测试用例（Security Testing）
5. 性能测试用例（Performance Testing）

每个测试用例应包含：
- 测试名称和描述
- HTTP方法和路径
- 请求参数和请求体
- 期望的响应状态码和响应体
- 验证规则和断言

请以JSON格式返回测试用例列表。
"""
            
            response = self.generate_text(prompt, **kwargs)
            if response.success:
                response.task_type = LLMTaskType.TEST_GENERATION.value
                response.metadata["api_spec_size"] = len(api_spec_json)
            
            return response
            
        except Exception as e:
            error_msg = f"测试用例生成失败: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_response(error_msg, LLMTaskType.TEST_GENERATION.value)
    
    def validate_response(self, response: Dict[str, Any], schema: Dict[str, Any], **kwargs) -> LLMResponse:
        """验证响应数据
        
        Args:
            response: 响应数据
            schema: 验证Schema
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 验证结果
        """
        try:
            # 构建验证提示词
            response_json = json.dumps(response, indent=2, ensure_ascii=False)
            schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
            
            prompt = f"""
请验证以下响应数据是否符合指定的JSON Schema：

响应数据：
{response_json}

JSON Schema：
{schema_json}

请检查：
1. 数据类型是否正确
2. 必需字段是否存在
3. 字段值是否符合约束条件
4. 数据格式是否正确
5. 枚举值是否有效

请以JSON格式返回验证结果，包含：
- is_valid: 是否有效 (boolean)
- errors: 错误列表 (array)
- warnings: 警告列表 (array)
- suggestions: 改进建议 (array)
"""
            
            response_obj = self.generate_text(prompt, **kwargs)
            if response_obj.success:
                response_obj.task_type = LLMTaskType.VALIDATION.value
                response_obj.metadata["response_size"] = len(response_json)
                response_obj.metadata["schema_size"] = len(schema_json)
            
            return response_obj
            
        except Exception as e:
            error_msg = f"响应验证失败: {str(e)}"
            self.logger.error(error_msg)
            return self._create_error_response(error_msg, LLMTaskType.VALIDATION.value)


class OllamaLangChainClient(LangChainLLMClient):
    """基于LangChain的Ollama客户端"""
    
    def _get_provider(self) -> LLMProvider:
        """获取LLM提供商类型"""
        return LLMProvider.OLLAMA
    
    def _setup_clients(self):
        """设置Ollama客户端"""
        try:
            base_url = self.config.get("base_url", "http://localhost:11434")
            
            # 设置LangChain Ollama客户端
            self.llm = Ollama(
                model=self.model,
                base_url=base_url,
                temperature=self.config.get("temperature", 0.7)
            )
            
            # 设置Instructor客户端（通过OpenAI兼容接口）
            openai_client = OpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama"  # Ollama不需要真实API密钥
            )
            self.instructor_client = instructor.patch(openai_client)
            
            self.logger.info(f"Ollama LangChain客户端初始化成功: {base_url}")
            
        except Exception as e:
            error_msg = f"Ollama客户端初始化失败: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg, provider="ollama")
    
    def test_connection(self) -> bool:
        """测试Ollama连接"""
        try:
            test_response = self.generate_text("请回复'Ollama连接测试成功'")
            return test_response.success and "成功" in test_response.content
        except Exception as e:
            self.logger.error(f"Ollama连接测试失败: {e}")
            return False


class OpenAILangChainClient(LangChainLLMClient):
    """基于LangChain的OpenAI客户端"""
    
    def _get_provider(self) -> LLMProvider:
        """获取LLM提供商类型"""
        return LLMProvider.OPENAI
    
    def _setup_clients(self):
        """设置OpenAI客户端"""
        try:
            api_key = self.config.get("api_key")
            if not api_key:
                raise LLMError("OpenAI API密钥未配置", provider="openai")
            
            # 设置LangChain OpenAI客户端
            self.llm = ChatOpenAI(
                model=self.model,
                openai_api_key=api_key,
                temperature=self.config.get("temperature", 0.7),
                max_tokens=self.config.get("max_tokens", 2048)
            )
            
            # 设置Instructor客户端
            openai_client = OpenAI(api_key=api_key)
            self.instructor_client = instructor.patch(openai_client)
            
            self.logger.info(f"OpenAI LangChain客户端初始化成功")
            
        except Exception as e:
            error_msg = f"OpenAI客户端初始化失败: {str(e)}"
            self.logger.error(error_msg)
            raise LLMError(error_msg, provider="openai")
    
    def test_connection(self) -> bool:
        """测试OpenAI连接"""
        try:
            test_response = self.generate_text("请回复'OpenAI连接测试成功'")
            return test_response.success and "成功" in test_response.content
        except Exception as e:
            self.logger.error(f"OpenAI连接测试失败: {e}")
            return False
