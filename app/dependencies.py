"""
FastAPI依赖注入模块

定义应用程序中使用的各种依赖项，包括数据库会话、配置对象、
认证验证、日志记录器等。提供统一的依赖注入接口。
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from loguru import logger

from app.config import get_settings, Settings
from app.core.shared.utils.logger import get_logger
# from app.core.shared.utils.exceptions import BaseSpec2TestException, ErrorCode


# 安全认证方案
security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话依赖

    创建数据库会话，在请求结束后自动关闭。

    Yields:
        数据库会话对象
    """
    from app.database import get_db as get_database_session
    yield from get_database_session()


def get_settings_dependency() -> Settings:
    """获取配置对象依赖

    Returns:
        应用程序配置对象
    """
    return get_settings()


def get_logger_dependency(request: Request) -> "logger":
    """获取日志记录器依赖

    Args:
        request: FastAPI请求对象

    Returns:
        配置好的日志记录器
    """
    # 使用请求路径作为日志记录器名称
    logger_name = f"api.{request.url.path.strip('/').replace('/', '.')}"
    return get_logger(logger_name)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings_dependency)
) -> Optional[dict]:
    """获取当前用户依赖

    验证JWT令牌并返回用户信息。

    Args:
        credentials: HTTP认证凭据
        settings: 应用程序配置

    Returns:
        用户信息字典，如果未认证则返回None

    Raises:
        HTTPException: 认证失败时抛出
    """
    if not credentials:
        return None

    # token = credentials.credentials

    # TODO: 在后续阶段实现JWT令牌验证
    # 当前返回模拟用户信息
    if settings.ENVIRONMENT == "development":
        return {
            "user_id": "dev_user",
            "username": "developer",
            "email": "dev@spec2test.com",
            "is_active": True
        }

    # 生产环境需要实际的JWT验证
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证令牌无效",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_authentication(
    current_user: Optional[dict] = Depends(get_current_user)
) -> dict:
    """要求认证的依赖

    确保用户已认证，否则抛出异常。

    Args:
        current_user: 当前用户信息

    Returns:
        用户信息字典

    Raises:
        HTTPException: 用户未认证时抛出
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证才能访问此资源",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_admin(
    current_user: dict = Depends(require_authentication)
) -> dict:
    """要求管理员权限的依赖

    确保用户具有管理员权限。

    Args:
        current_user: 当前用户信息

    Returns:
        用户信息字典

    Raises:
        HTTPException: 用户权限不足时抛出
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限才能访问此资源"
        )
    return current_user


def validate_request_size(
    request: Request,
    max_size: int = 10 * 1024 * 1024  # 10MB
) -> Request:
    """验证请求大小的依赖

    Args:
        request: FastAPI请求对象
        max_size: 最大请求大小（字节）

    Returns:
        请求对象

    Raises:
        HTTPException: 请求过大时抛出
    """
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"请求大小超过限制 ({max_size} 字节)"
        )
    return request


def handle_exceptions(
    request: Request,
    logger: "logger" = Depends(get_logger_dependency)
) -> dict:
    """异常处理依赖

    提供统一的异常处理上下文。

    Args:
        request: FastAPI请求对象
        logger: 日志记录器

    Returns:
        异常处理上下文字典
    """
    return {
        "request": request,
        "logger": logger,
        "request_id": getattr(request.state, "request_id", None)
    }


class RateLimiter:
    """简单的速率限制器

    基于内存的速率限制实现，用于API请求频率控制。
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """初始化速率限制器

        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {client_id: [timestamp, ...]}

    def is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求

        Args:
            client_id: 客户端标识

        Returns:
            是否允许请求
        """
        import time

        now = time.time()
        window_start = now - self.window_seconds

        # 清理过期记录
        if client_id in self.requests:
            self.requests[client_id] = [
                timestamp for timestamp in self.requests[client_id]
                if timestamp > window_start
            ]
        else:
            self.requests[client_id] = []

        # 检查是否超过限制
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        # 记录当前请求
        self.requests[client_id].append(now)
        return True


# 全局速率限制器实例
rate_limiter = RateLimiter()


def check_rate_limit(
    request: Request,
    limiter: RateLimiter = rate_limiter
) -> Request:
    """检查速率限制的依赖

    Args:
        request: FastAPI请求对象
        limiter: 速率限制器实例

    Returns:
        请求对象

    Raises:
        HTTPException: 超过速率限制时抛出
    """
    # 使用客户端IP作为标识
    client_id = request.client.host if request.client else "unknown"

    if not limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求频率过高，请稍后再试"
        )

    return request


def get_pagination_params(
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> dict:
    """获取分页参数依赖

    Args:
        page: 页码（从1开始）
        size: 每页大小
        max_size: 最大每页大小

    Returns:
        分页参数字典

    Raises:
        HTTPException: 参数无效时抛出
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="页码必须大于0"
        )

    if size < 1 or size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"每页大小必须在1-{max_size}之间"
        )

    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size,
        "limit": size
    }
