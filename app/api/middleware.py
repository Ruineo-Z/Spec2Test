"""
API中间件

提供CORS处理、请求日志、异常处理等中间件功能。
"""

import time
import uuid
from typing import Callable, Dict, Any
import json

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.shared.utils.logger import get_logger
from app.core.shared.utils.exceptions import (
    BusinessException, SystemException, ValidationException
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求日志"""
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 记录请求信息
        self.logger.info(
            f"📥 请求开始 [{request_id}] "
            f"{request.method} {request.url.path} "
            f"from {client_ip}"
        )
        
        # 记录请求详情（仅在调试模式）
        try:
            # 检查是否为DEBUG级别
            import logging
            if self.logger.isEnabledFor(logging.DEBUG):
                headers = dict(request.headers)
                # 隐藏敏感信息
                if "authorization" in headers:
                    headers["authorization"] = "***"

                self.logger.debug(
                    f"📋 请求详情 [{request_id}] "
                    f"Headers: {headers}, "
                    f"Query: {dict(request.query_params)}"
                )
        except Exception:
            # 忽略日志记录错误
            pass
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            self.logger.info(
                f"📤 请求完成 [{request_id}] "
                f"{response.status_code} "
                f"in {process_time:.3f}s"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常
            self.logger.error(
                f"💥 请求异常 [{request_id}] "
                f"{type(e).__name__}: {str(e)} "
                f"in {process_time:.3f}s"
            )
            
            # 重新抛出异常，让异常处理中间件处理
            raise


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """异常处理中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理异常"""
        try:
            response = await call_next(request)
            return response
            
        except BusinessException as e:
            # 业务异常
            self.logger.warning(f"业务异常: {e.error_code.value} - {e.message}")
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": e.error_code.value,
                        "message": e.message,
                        "type": "business_error",
                        "details": e.details,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "request_id": getattr(request.state, "request_id", None)
                    }
                }
            )
            
        except ValidationException as e:
            # 验证异常
            self.logger.warning(f"验证异常: {e.error_code.value} - {e.message}")
            
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": e.error_code.value,
                        "message": e.message,
                        "type": "validation_error",
                        "details": e.details,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "request_id": getattr(request.state, "request_id", None)
                    }
                }
            )
            
        except SystemException as e:
            # 系统异常
            self.logger.error(f"系统异常: {e.error_code.value} - {e.message}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": e.error_code.value,
                        "message": e.message,
                        "type": "system_error",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "request_id": getattr(request.state, "request_id", None)
                    }
                }
            )
            
        except HTTPException as e:
            # HTTP异常，直接传递
            raise
            
        except Exception as e:
            # 未知异常
            self.logger.error(f"未知异常: {type(e).__name__}: {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "UNKNOWN_ERROR",
                        "message": "服务器内部错误",
                        "type": "unknown_error",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "request_id": getattr(request.state, "request_id", None)
                    }
                }
            )


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """请求验证中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """验证请求"""
        # 检查请求大小限制
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            max_size = 50 * 1024 * 1024  # 50MB
            
            if content_length > max_size:
                self.logger.warning(f"请求体过大: {content_length} bytes")
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": {
                            "code": "REQUEST_TOO_LARGE",
                            "message": f"请求体大小超过限制 ({max_size} bytes)",
                            "type": "validation_error",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "request_id": getattr(request.state, "request_id", None)
                        }
                    }
                )
        
        # 检查Content-Type（对于POST/PUT请求）
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            
            # 如果有请求体但没有Content-Type
            if content_length and int(content_length) > 0 and not content_type:
                self.logger.warning("缺少Content-Type头")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "MISSING_CONTENT_TYPE",
                            "message": "请求缺少Content-Type头",
                            "type": "validation_error",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "request_id": getattr(request.state, "request_id", None)
                        }
                    }
                )
        
        # 检查API版本（如果需要）
        api_version = request.headers.get("api-version")
        if request.url.path.startswith("/api/v") and not api_version:
            # 从URL中提取版本
            path_parts = request.url.path.split("/")
            if len(path_parts) >= 3 and path_parts[2].startswith("v"):
                api_version = path_parts[2]
                request.state.api_version = api_version
        
        # 添加请求上下文信息
        request.state.start_time = time.time()
        request.state.client_ip = request.client.host if request.client else "unknown"
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            # 记录验证相关的异常
            if "validation" in str(e).lower():
                self.logger.warning(f"请求验证失败: {str(e)}")
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件（简单实现）"""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # 简单的内存存储，生产环境应使用Redis
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """速率限制检查"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_requests(current_time)
        
        # 检查当前IP的请求次数
        if client_ip in self.requests:
            request_times = self.requests[client_ip]
            recent_requests = [t for t in request_times if current_time - t < 60]  # 1分钟内
            
            if len(recent_requests) >= self.requests_per_minute:
                self.logger.warning(f"速率限制触发: {client_ip} ({len(recent_requests)} requests/min)")
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"请求频率超过限制 ({self.requests_per_minute} requests/min)",
                            "type": "rate_limit_error",
                            "retry_after": 60,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "request_id": getattr(request.state, "request_id", None)
                        }
                    },
                    headers={"Retry-After": "60"}
                )
            
            # 更新请求记录
            self.requests[client_ip] = recent_requests + [current_time]
        else:
            # 新IP，记录第一次请求
            self.requests[client_ip] = [current_time]
        
        response = await call_next(request)
        
        # 添加速率限制相关的响应头
        remaining = max(0, self.requests_per_minute - len(self.requests.get(client_ip, [])))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response
    
    def _cleanup_expired_requests(self, current_time: float):
        """清理过期的请求记录"""
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if current_time - t < 60]
            if not self.requests[ip]:
                del self.requests[ip]
