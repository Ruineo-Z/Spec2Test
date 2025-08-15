"""
LLM基础接口定义

定义统一的大语言模型接口，支持多种LLM提供商的统一调用和结构化输出。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Type, TypeVar
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from app.core.shared.utils.logger import get_logger

# 泛型类型，用于结构化输出
T = TypeVar('T', bound=BaseModel)

logger = get_logger(__name__)


class LLMProvider(Enum):
    """LLM提供商枚举"""
    GEMINI = "gemini"
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"


class LLMTaskType(Enum):
    """LLM任务类型枚举"""
    TEXT_GENERATION = "text_generation"
    DOCUMENT_ANALYSIS = "document_analysis"
    TEST_GENERATION = "test_generation"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"
    SUMMARIZATION = "summarization"


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    metadata: Dict[str, Any]
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    task_type: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class LLMError(Exception):
    """LLM相关异常"""
    
    def __init__(self, message: str, provider: Optional[str] = None, 
                 error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.details = details or {}


class BaseLLMClient(ABC):
    """LLM客户端基础抽象类
    
    定义所有LLM客户端必须实现的接口方法。
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化LLM客户端
        
        Args:
            config: LLM配置参数
        """
        self.config = config
        self.provider = self._get_provider()
        self.model = config.get("model", "default")
        self.logger = get_logger(f"{self.__class__.__name__}")
        
    @abstractmethod
    def _get_provider(self) -> LLMProvider:
        """获取LLM提供商类型"""
        pass
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> LLMResponse:
        """生成文本
        
        Args:
            prompt: 输入提示词
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的文本响应
            
        Raises:
            LLMError: LLM调用失败时抛出
        """
        pass
    
    @abstractmethod
    def analyze_document(self, content: str, document_type: str = "auto", **kwargs) -> LLMResponse:
        """分析文档内容
        
        Args:
            content: 文档内容
            document_type: 文档类型
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 文档分析结果
            
        Raises:
            LLMError: LLM调用失败时抛出
        """
        pass
    
    @abstractmethod
    def generate_test_cases(self, api_spec: Dict[str, Any], **kwargs) -> LLMResponse:
        """生成测试用例
        
        Args:
            api_spec: API规范
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的测试用例
            
        Raises:
            LLMError: LLM调用失败时抛出
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: Dict[str, Any], schema: Dict[str, Any], **kwargs) -> LLMResponse:
        """验证响应数据

        Args:
            response: 响应数据
            schema: 验证Schema
            **kwargs: 其他参数

        Returns:
            LLMResponse: 验证结果

        Raises:
            LLMError: LLM调用失败时抛出
        """
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, response_model: Type[T], **kwargs) -> T:
        """生成结构化输出

        Args:
            prompt: 输入提示词
            response_model: Pydantic模型类，定义期望的输出结构
            **kwargs: 其他参数

        Returns:
            T: 结构化输出对象，类型为response_model

        Raises:
            LLMError: LLM调用失败时抛出
        """
        pass
    
    def generate_structured_output(self, prompt: str, schema: Dict[str, Any], **kwargs) -> LLMResponse:
        """生成结构化输出
        
        Args:
            prompt: 输入提示词
            schema: 输出Schema
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 结构化输出结果
        """
        # 默认实现，子类可以重写
        enhanced_prompt = self._enhance_prompt_with_schema(prompt, schema)
        return self.generate_text(enhanced_prompt, **kwargs)
    
    def _enhance_prompt_with_schema(self, prompt: str, schema: Dict[str, Any]) -> str:
        """使用Schema增强提示词
        
        Args:
            prompt: 原始提示词
            schema: 输出Schema
            
        Returns:
            str: 增强后的提示词
        """
        schema_description = self._format_schema_description(schema)
        enhanced_prompt = f"""
{prompt}

请按照以下JSON Schema格式返回结果：
{schema_description}

确保返回的结果是有效的JSON格式，并严格遵循上述Schema结构。
"""
        return enhanced_prompt
    
    def _format_schema_description(self, schema: Dict[str, Any]) -> str:
        """格式化Schema描述
        
        Args:
            schema: JSON Schema
            
        Returns:
            str: 格式化的Schema描述
        """
        import json
        return json.dumps(schema, indent=2, ensure_ascii=False)
    
    def test_connection(self) -> bool:
        """测试LLM连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            test_prompt = "请回复'连接测试成功'"
            response = self.generate_text(test_prompt)
            return response.success
        except Exception as e:
            self.logger.error(f"LLM连接测试失败: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "provider": self.provider.value,
            "model": self.model,
            "config": self.config
        }
    
    def _create_response(self, content: str, metadata: Dict[str, Any] = None, 
                        usage: Dict[str, Any] = None, task_type: str = None) -> LLMResponse:
        """创建LLM响应对象
        
        Args:
            content: 响应内容
            metadata: 元数据
            usage: 使用统计
            task_type: 任务类型
            
        Returns:
            LLMResponse: 响应对象
        """
        return LLMResponse(
            content=content,
            metadata=metadata or {},
            usage=usage,
            model=self.model,
            provider=self.provider.value,
            task_type=task_type,
            success=True
        )
    
    def _create_error_response(self, error_message: str, task_type: str = None) -> LLMResponse:
        """创建错误响应对象
        
        Args:
            error_message: 错误消息
            task_type: 任务类型
            
        Returns:
            LLMResponse: 错误响应对象
        """
        return LLMResponse(
            content="",
            metadata={},
            model=self.model,
            provider=self.provider.value,
            task_type=task_type,
            success=False,
            error_message=error_message
        )
