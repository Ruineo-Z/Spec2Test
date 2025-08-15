"""
LLM工厂类

提供统一的LLM客户端创建和管理功能。
"""

from typing import Dict, Any, Optional, List
from functools import lru_cache

from .base import BaseLLMClient, LLMProvider, LLMError
from .langchain_client import OllamaLangChainClient, OpenAILangChainClient
from app.config import get_settings
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class LLMFactory:
    """LLM工厂类
    
    负责创建和管理不同类型的LLM客户端实例。
    """
    
    _clients: Dict[str, BaseLLMClient] = {}
    
    @classmethod
    def create_client(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> BaseLLMClient:
        """创建LLM客户端
        
        Args:
            provider: LLM提供商名称
            config: 客户端配置，如果为None则使用默认配置
            
        Returns:
            BaseLLMClient: LLM客户端实例
            
        Raises:
            LLMError: 不支持的提供商或配置错误
        """
        try:
            # 标准化提供商名称
            provider = provider.lower()
            
            # 获取配置
            if config is None:
                config = cls._get_default_config(provider)
            
            # 创建客户端实例（全部使用LangChain集成）
            if provider == LLMProvider.OLLAMA.value:
                return OllamaLangChainClient(config)
            elif provider == LLMProvider.OPENAI.value:
                return OpenAILangChainClient(config)
            elif provider == LLMProvider.GEMINI.value:
                raise LLMError("Gemini暂不支持LangChain集成，请使用Ollama或OpenAI")
            else:
                raise LLMError(f"不支持的LLM提供商: {provider}")
                
        except Exception as e:
            logger.error(f"创建LLM客户端失败: {e}")
            raise LLMError(f"创建LLM客户端失败: {str(e)}", provider=provider)
    
    @classmethod
    def get_client(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> BaseLLMClient:
        """获取LLM客户端（带缓存）
        
        Args:
            provider: LLM提供商名称
            config: 客户端配置
            
        Returns:
            BaseLLMClient: LLM客户端实例
        """
        # 生成缓存键
        cache_key = cls._generate_cache_key(provider, config)
        
        # 检查缓存
        if cache_key in cls._clients:
            return cls._clients[cache_key]
        
        # 创建新客户端
        client = cls.create_client(provider, config)
        cls._clients[cache_key] = client
        
        logger.info(f"创建并缓存LLM客户端: {provider}")
        return client
    
    @classmethod
    def _generate_cache_key(cls, provider: str, config: Optional[Dict[str, Any]]) -> str:
        """生成缓存键
        
        Args:
            provider: LLM提供商名称
            config: 客户端配置
            
        Returns:
            str: 缓存键
        """
        import hashlib
        import json
        
        config_str = json.dumps(config or {}, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]
        
        return f"{provider}_{config_hash}"
    
    @classmethod
    def _get_default_config(cls, provider: str) -> Dict[str, Any]:
        """获取默认配置
        
        Args:
            provider: LLM提供商名称
            
        Returns:
            Dict[str, Any]: 默认配置
        """
        settings = get_settings()
        
        if provider == LLMProvider.OLLAMA.value:
            return {
                "base_url": settings.llm.ollama.base_url,
                "model": settings.llm.ollama.model,
                "timeout": settings.llm.ollama.timeout,
                "max_retries": settings.llm.ollama.max_retries,
                "temperature": settings.llm.ollama.temperature
            }
        elif provider == LLMProvider.OPENAI.value:
            return {
                "api_key": settings.llm.openai.api_key,
                "model": settings.llm.openai.model,
                "timeout": settings.llm.openai.timeout,
                "max_retries": settings.llm.openai.max_retries,
                "temperature": settings.llm.openai.temperature
            }
        else:
            return {}
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """获取可用的LLM提供商列表

        Returns:
            List[str]: 提供商列表
        """
        # 只返回支持LangChain集成的提供商
        return [LLMProvider.OLLAMA.value, LLMProvider.OPENAI.value]
    
    @classmethod
    def test_provider(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """测试LLM提供商连接
        
        Args:
            provider: LLM提供商名称
            config: 客户端配置
            
        Returns:
            bool: 连接是否成功
        """
        try:
            client = cls.create_client(provider, config)
            return client.test_connection()
        except Exception as e:
            logger.error(f"测试LLM提供商连接失败: {e}")
            return False
    
    @classmethod
    def clear_cache(cls):
        """清空客户端缓存"""
        cls._clients.clear()
        logger.info("LLM客户端缓存已清空")
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        return {
            "cached_clients": len(cls._clients),
            "cache_keys": list(cls._clients.keys())
        }


@lru_cache(maxsize=None)
def get_llm_client(provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> BaseLLMClient:
    """获取LLM客户端的便捷函数
    
    Args:
        provider: LLM提供商名称，如果为None则使用默认提供商
        config: 客户端配置
        
    Returns:
        BaseLLMClient: LLM客户端实例
    """
    if provider is None:
        settings = get_settings()
        provider = settings.llm.default_provider
    
    return LLMFactory.get_client(provider, config)


def get_default_llm_client() -> BaseLLMClient:
    """获取默认LLM客户端
    
    Returns:
        BaseLLMClient: 默认LLM客户端实例
    """
    settings = get_settings()
    return get_llm_client(settings.llm.default_provider)


def create_llm_client_from_settings(provider_name: str) -> BaseLLMClient:
    """从设置创建LLM客户端
    
    Args:
        provider_name: 提供商名称
        
    Returns:
        BaseLLMClient: LLM客户端实例
    """
    return LLMFactory.create_client(provider_name)


def test_all_providers() -> Dict[str, bool]:
    """测试所有配置的LLM提供商
    
    Returns:
        Dict[str, bool]: 各提供商的连接测试结果
    """
    results = {}
    providers = LLMFactory.get_available_providers()
    
    for provider in providers:
        try:
            results[provider] = LLMFactory.test_provider(provider)
        except Exception as e:
            logger.error(f"测试提供商 {provider} 失败: {e}")
            results[provider] = False
    
    return results
