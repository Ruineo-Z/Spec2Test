"""
LLM抽象层包

基于LangChain + Instructor提供统一的大语言模型接口，支持结构化输出。
"""

from .base import BaseLLMClient, LLMResponse, LLMError
from .factory import LLMFactory, get_llm_client
from .langchain_client import OllamaLangChainClient, OpenAILangChainClient
from .models import (
    APITestCase, TestSuite, DocumentAnalysis, ValidationResult,
    CodeGeneration, PerformanceAnalysis, SecurityAnalysis
)

__all__ = [
    # 核心接口
    "BaseLLMClient",
    "LLMResponse",
    "LLMError",
    "LLMFactory",
    "get_llm_client",

    # LangChain客户端
    "OllamaLangChainClient",
    "OpenAILangChainClient",

    # 结构化输出模型
    "APITestCase",
    "TestSuite",
    "DocumentAnalysis",
    "ValidationResult",
    "CodeGeneration",
    "PerformanceAnalysis",
    "SecurityAnalysis"
]
