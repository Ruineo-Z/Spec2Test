"""
HTTP认证处理器

提供多种HTTP认证方式的支持。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import base64
from requests.auth import AuthBase

from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class AuthHandler:
    """认证处理器
    
    负责创建和管理不同类型的HTTP认证。
    """
    
    def create_auth(self, auth_config: Dict[str, Any]) -> Optional[AuthBase]:
        """创建认证对象
        
        Args:
            auth_config: 认证配置
                - type: 认证类型 (bearer, basic, api_key)
                - token: Bearer token
                - username: 用户名 (Basic认证)
                - password: 密码 (Basic认证)
                - api_key: API密钥
                - header_name: API密钥头名称 (默认: X-API-Key)
                
        Returns:
            Optional[AuthBase]: 认证对象
        """
        auth_type = auth_config.get("type", "").lower()
        
        if auth_type == "bearer":
            token = auth_config.get("token")
            if token:
                return BearerTokenAuth(token)
        
        elif auth_type == "basic":
            username = auth_config.get("username")
            password = auth_config.get("password")
            if username and password:
                return BasicAuth(username, password)
        
        elif auth_type == "api_key":
            api_key = auth_config.get("api_key")
            header_name = auth_config.get("header_name", "X-API-Key")
            if api_key:
                return APIKeyAuth(api_key, header_name)
        
        logger.warning(f"不支持的认证类型或配置不完整: {auth_type}")
        return None


class BearerTokenAuth(AuthBase):
    """Bearer Token认证"""
    
    def __init__(self, token: str):
        """初始化Bearer Token认证
        
        Args:
            token: Bearer token
        """
        self.token = token
    
    def __call__(self, r):
        """添加认证头到请求"""
        r.headers['Authorization'] = f'Bearer {self.token}'
        return r


class BasicAuth(AuthBase):
    """Basic认证"""
    
    def __init__(self, username: str, password: str):
        """初始化Basic认证
        
        Args:
            username: 用户名
            password: 密码
        """
        self.username = username
        self.password = password
    
    def __call__(self, r):
        """添加认证头到请求"""
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
        r.headers['Authorization'] = f'Basic {encoded_credentials}'
        return r


class APIKeyAuth(AuthBase):
    """API Key认证"""
    
    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        """初始化API Key认证
        
        Args:
            api_key: API密钥
            header_name: 头名称
        """
        self.api_key = api_key
        self.header_name = header_name
    
    def __call__(self, r):
        """添加认证头到请求"""
        r.headers[self.header_name] = self.api_key
        return r


class OAuth2Auth(AuthBase):
    """OAuth2认证"""
    
    def __init__(self, access_token: str, token_type: str = "Bearer"):
        """初始化OAuth2认证
        
        Args:
            access_token: 访问令牌
            token_type: 令牌类型
        """
        self.access_token = access_token
        self.token_type = token_type
    
    def __call__(self, r):
        """添加认证头到请求"""
        r.headers['Authorization'] = f'{self.token_type} {self.access_token}'
        return r


class CustomHeaderAuth(AuthBase):
    """自定义头认证"""
    
    def __init__(self, headers: Dict[str, str]):
        """初始化自定义头认证
        
        Args:
            headers: 自定义认证头
        """
        self.headers = headers
    
    def __call__(self, r):
        """添加认证头到请求"""
        for key, value in self.headers.items():
            r.headers[key] = value
        return r


def create_auth_from_config(auth_config: Dict[str, Any]) -> Optional[AuthBase]:
    """从配置创建认证对象的便捷函数
    
    Args:
        auth_config: 认证配置
        
    Returns:
        Optional[AuthBase]: 认证对象
    """
    handler = AuthHandler()
    return handler.create_auth(auth_config)


def create_bearer_auth(token: str) -> BearerTokenAuth:
    """创建Bearer Token认证的便捷函数
    
    Args:
        token: Bearer token
        
    Returns:
        BearerTokenAuth: Bearer认证对象
    """
    return BearerTokenAuth(token)


def create_basic_auth(username: str, password: str) -> BasicAuth:
    """创建Basic认证的便捷函数
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        BasicAuth: Basic认证对象
    """
    return BasicAuth(username, password)


def create_api_key_auth(api_key: str, header_name: str = "X-API-Key") -> APIKeyAuth:
    """创建API Key认证的便捷函数
    
    Args:
        api_key: API密钥
        header_name: 头名称
        
    Returns:
        APIKeyAuth: API Key认证对象
    """
    return APIKeyAuth(api_key, header_name)
