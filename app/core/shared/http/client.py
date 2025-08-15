"""
HTTP客户端实现

提供功能完整的HTTP请求客户端，支持认证、重试、性能监控等特性。
"""

import time
import json
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .auth import AuthHandler
from .performance import PerformanceMonitor, RequestMetrics
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class HTTPMethod(Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class HTTPResponse:
    """HTTP响应数据类"""
    status_code: int
    headers: Dict[str, str]
    content: str
    json_data: Optional[Dict[str, Any]] = None
    url: str = ""
    method: str = ""
    elapsed_time: float = 0.0
    metrics: Optional[RequestMetrics] = None
    success: bool = True
    error_message: Optional[str] = None


class HTTPError(Exception):
    """HTTP请求异常"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response: Optional[HTTPResponse] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class HTTPClient:
    """HTTP客户端
    
    提供统一的HTTP请求接口，支持认证、重试、性能监控等功能。
    """
    
    def __init__(self, base_url: str = "", config: Optional[Dict[str, Any]] = None):
        """初始化HTTP客户端
        
        Args:
            base_url: 基础URL
            config: 客户端配置
                - timeout: 请求超时时间 (默认: 30)
                - max_retries: 最大重试次数 (默认: 3)
                - retry_backoff_factor: 重试退避因子 (默认: 1)
                - verify_ssl: 是否验证SSL证书 (默认: True)
                - user_agent: 用户代理 (默认: Spec2Test-HTTPClient/1.0)
        """
        self.base_url = base_url.rstrip('/')
        self.config = config or {}
        
        # 配置参数
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_backoff_factor = self.config.get("retry_backoff_factor", 1)
        self.verify_ssl = self.config.get("verify_ssl", True)
        self.user_agent = self.config.get("user_agent", "Spec2Test-HTTPClient/1.0")
        
        # 初始化组件
        self.auth_handler = AuthHandler()
        self.performance_monitor = PerformanceMonitor()
        
        # 创建会话
        self.session = self._create_session()
        
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def _create_session(self) -> requests.Session:
        """创建HTTP会话
        
        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置默认请求头
        session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        # SSL验证设置
        session.verify = self.verify_ssl
        
        return session
    
    def request(self, method: Union[str, HTTPMethod], url: str, 
                headers: Optional[Dict[str, str]] = None,
                params: Optional[Dict[str, Any]] = None,
                data: Optional[Union[str, Dict[str, Any]]] = None,
                json_data: Optional[Dict[str, Any]] = None,
                auth: Optional[Dict[str, Any]] = None,
                timeout: Optional[float] = None,
                **kwargs) -> HTTPResponse:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            params: 查询参数
            data: 请求体数据
            json_data: JSON数据
            auth: 认证信息
            timeout: 超时时间
            **kwargs: 其他参数
            
        Returns:
            HTTPResponse: HTTP响应
            
        Raises:
            HTTPError: 请求失败时抛出
        """
        try:
            # 标准化方法名
            if isinstance(method, HTTPMethod):
                method = method.value
            method = method.upper()
            
            # 构建完整URL
            full_url = self._build_url(url)
            
            # 准备请求参数
            request_kwargs = self._prepare_request_kwargs(
                headers, params, data, json_data, auth, timeout, **kwargs
            )
            
            # 开始性能监控
            start_time = time.time()
            
            # 发送请求
            self.logger.debug(f"发送HTTP请求: {method} {full_url}")
            response = self.session.request(method, full_url, **request_kwargs)
            
            # 计算响应时间
            elapsed_time = time.time() - start_time
            
            # 创建性能指标
            metrics = self.performance_monitor.create_metrics(
                method=method,
                url=full_url,
                status_code=response.status_code,
                response_time=elapsed_time,
                request_size=self._calculate_request_size(request_kwargs),
                response_size=len(response.content) if response.content else 0
            )
            
            # 构建响应对象
            http_response = self._build_response(response, method, full_url, elapsed_time, metrics)
            
            # 记录性能指标
            self.performance_monitor.record_request(metrics)
            
            # 检查响应状态
            if not response.ok:
                error_msg = f"HTTP请求失败: {response.status_code} - {response.reason}"
                self.logger.error(error_msg)
                http_response.success = False
                http_response.error_message = error_msg
                
                if self.config.get("raise_for_status", True):
                    raise HTTPError(error_msg, response.status_code, http_response)
            
            return http_response
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP请求异常: {str(e)}"
            self.logger.error(error_msg)
            
            # 创建错误响应
            error_response = HTTPResponse(
                status_code=0,
                headers={},
                content="",
                url=full_url if 'full_url' in locals() else url,
                method=method,
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0,
                success=False,
                error_message=error_msg
            )
            
            raise HTTPError(error_msg, response=error_response)
        except Exception as e:
            error_msg = f"HTTP请求未知异常: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPError(error_msg)
    
    def get(self, url: str, **kwargs) -> HTTPResponse:
        """发送GET请求"""
        return self.request(HTTPMethod.GET, url, **kwargs)
    
    def post(self, url: str, **kwargs) -> HTTPResponse:
        """发送POST请求"""
        return self.request(HTTPMethod.POST, url, **kwargs)
    
    def put(self, url: str, **kwargs) -> HTTPResponse:
        """发送PUT请求"""
        return self.request(HTTPMethod.PUT, url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> HTTPResponse:
        """发送DELETE请求"""
        return self.request(HTTPMethod.DELETE, url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> HTTPResponse:
        """发送PATCH请求"""
        return self.request(HTTPMethod.PATCH, url, **kwargs)
    
    def head(self, url: str, **kwargs) -> HTTPResponse:
        """发送HEAD请求"""
        return self.request(HTTPMethod.HEAD, url, **kwargs)
    
    def options(self, url: str, **kwargs) -> HTTPResponse:
        """发送OPTIONS请求"""
        return self.request(HTTPMethod.OPTIONS, url, **kwargs)
    
    def _build_url(self, url: str) -> str:
        """构建完整URL
        
        Args:
            url: 相对或绝对URL
            
        Returns:
            str: 完整URL
        """
        if url.startswith(('http://', 'https://')):
            return url
        
        if self.base_url:
            return f"{self.base_url}/{url.lstrip('/')}"
        
        return url
    
    def _prepare_request_kwargs(self, headers: Optional[Dict[str, str]], 
                               params: Optional[Dict[str, Any]],
                               data: Optional[Union[str, Dict[str, Any]]],
                               json_data: Optional[Dict[str, Any]],
                               auth: Optional[Dict[str, Any]],
                               timeout: Optional[float],
                               **kwargs) -> Dict[str, Any]:
        """准备请求参数
        
        Returns:
            Dict[str, Any]: 请求参数
        """
        request_kwargs = kwargs.copy()
        
        # 设置超时
        request_kwargs["timeout"] = timeout or self.timeout
        
        # 设置请求头
        if headers:
            request_kwargs["headers"] = headers
        
        # 设置查询参数
        if params:
            request_kwargs["params"] = params
        
        # 设置请求体
        if json_data:
            request_kwargs["json"] = json_data
        elif data:
            if isinstance(data, dict):
                request_kwargs["json"] = data
            else:
                request_kwargs["data"] = data
        
        # 设置认证
        if auth:
            auth_obj = self.auth_handler.create_auth(auth)
            if auth_obj:
                request_kwargs["auth"] = auth_obj
        
        return request_kwargs
    
    def _build_response(self, response: requests.Response, method: str, 
                       url: str, elapsed_time: float, 
                       metrics: RequestMetrics) -> HTTPResponse:
        """构建HTTP响应对象
        
        Returns:
            HTTPResponse: HTTP响应对象
        """
        # 解析JSON响应
        json_data = None
        try:
            if response.content and 'application/json' in response.headers.get('content-type', ''):
                json_data = response.json()
        except (json.JSONDecodeError, ValueError):
            pass
        
        return HTTPResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.text,
            json_data=json_data,
            url=url,
            method=method,
            elapsed_time=elapsed_time,
            metrics=metrics,
            success=response.ok
        )
    
    def _calculate_request_size(self, request_kwargs: Dict[str, Any]) -> int:
        """计算请求大小
        
        Returns:
            int: 请求大小（字节）
        """
        size = 0
        
        # 计算JSON数据大小
        if "json" in request_kwargs:
            size += len(json.dumps(request_kwargs["json"]).encode('utf-8'))
        
        # 计算普通数据大小
        if "data" in request_kwargs:
            data = request_kwargs["data"]
            if isinstance(data, str):
                size += len(data.encode('utf-8'))
            elif isinstance(data, bytes):
                size += len(data)
        
        return size
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        return self.performance_monitor.get_stats()
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self.performance_monitor.reset()
    
    def close(self):
        """关闭HTTP客户端"""
        if self.session:
            self.session.close()
            self.logger.debug("HTTP客户端已关闭")
