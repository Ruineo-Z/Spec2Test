"""日志配置模块

使用loguru进行日志管理，提供结构化日志、敏感信息过滤等功能。
"""

import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from app.config.settings import settings


def mask_sensitive_data(record: Dict[str, Any]) -> Dict[str, Any]:
    """过滤敏感信息

    Args:
        record: 日志记录

    Returns:
        过滤后的日志记录
    """
    if not settings.log.mask_sensitive:
        return record

    message = record.get("message", "")

    # 过滤敏感字段
    for field in settings.log.sensitive_fields:
        # 匹配 field="value" 或 field: value 格式
        patterns = [
            rf'{field}["\']?\s*[:=]\s*["\']?([^"\',\s}}]+)["\']?',
            rf'"?{field}"?\s*:\s*"?([^"\',\s}}]+)"?',
        ]

        for pattern in patterns:
            message = re.sub(pattern, f'{field}="***"', message, flags=re.IGNORECASE)

    # 过滤常见的token格式
    token_patterns = [
        r"Bearer\s+([A-Za-z0-9\-_\.]+)",
        r"sk-[A-Za-z0-9]{32,}",
        r"[A-Za-z0-9]{32,}",  # 通用长字符串
    ]

    for pattern in token_patterns:
        message = re.sub(pattern, "***", message)

    record["message"] = message
    return record


def json_formatter(record: Dict[str, Any]) -> str:
    """JSON格式化器

    Args:
        record: 日志记录

    Returns:
        JSON格式的日志字符串
    """
    import json

    # 过滤敏感信息
    record = mask_sensitive_data(record)

    # 构建JSON日志
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }

    # 添加额外字段
    if "extra" in record:
        log_entry.update(record["extra"])

    # 添加异常信息
    if record.get("exception"):
        log_entry["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }

    return json.dumps(log_entry, ensure_ascii=False)


def text_formatter(record: Dict[str, Any]) -> str:
    """文本格式化器

    Args:
        record: 日志记录

    Returns:
        格式化的日志字符串
    """
    # 过滤敏感信息
    record = mask_sensitive_data(record)

    # 使用配置的格式
    return settings.log.format + "\n"


def setup_logger() -> None:
    """设置日志配置"""
    # 移除默认处理器
    logger.remove()

    # 控制台日志
    if settings.log.console_enabled:
        console_format = json_formatter if settings.log.json_format else text_formatter

        logger.add(
            sys.stderr,
            format=console_format,
            level=settings.log.level,
            colorize=settings.log.console_colorize and not settings.log.json_format,
            backtrace=settings.debug,
            diagnose=settings.debug,
        )

    # 文件日志
    if settings.log.file_enabled:
        file_format = json_formatter if settings.log.json_format else text_formatter

        logger.add(
            settings.log.file_path,
            format=file_format,
            level=settings.log.level,
            rotation=settings.log.file_rotation,
            retention=settings.log.file_retention,
            compression="gz",
            backtrace=settings.debug,
            diagnose=settings.debug,
            enqueue=True,  # 异步写入
        )

    # 添加全局异常处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception

    logger.info(f"Logger initialized with level: {settings.log.level}")


def get_logger(name: Optional[str] = None) -> "logger":
    """获取日志器实例

    Args:
        name: 日志器名称，默认为调用模块名

    Returns:
        日志器实例
    """
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")

    return logger.bind(name=name)


# 日志装饰器
def log_execution_time(func_name: Optional[str] = None):
    """记录函数执行时间的装饰器

    Args:
        func_name: 自定义函数名称
    """

    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()

            try:
                logger.debug(f"Starting execution: {name}")
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Completed execution: {name} in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Failed execution: {name} in {execution_time:.3f}s - {str(e)}"
                )
                raise

        return wrapper

    return decorator


def log_api_request(func):
    """记录API请求的装饰器"""
    import functools

    @functools.wraps(func)
    async def wrapper(request, *args, **kwargs):
        start_time = time.time()

        # 记录请求信息
        logger.info(
            "API Request",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        try:
            response = await func(request, *args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                "API Response",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": getattr(response, "status_code", 200),
                    "execution_time": f"{execution_time:.3f}s",
                },
            )

            return response
        except Exception as e:
            execution_time = time.time() - start_time

            logger.error(
                "API Error",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "execution_time": f"{execution_time:.3f}s",
                },
            )
            raise

    return wrapper


# 导出
__all__ = [
    "setup_logger",
    "get_logger",
    "log_execution_time",
    "log_api_request",
    "mask_sensitive_data",
]
