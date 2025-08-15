"""
日志工具模块

基于loguru的统一日志管理工具，提供结构化日志记录功能。
支持多种日志级别、按天轮转、格式化输出等功能。

日志轮转策略：
- 普通日志：spec2test_YYYY-MM-DD.log，每天午夜轮转
- 错误日志：spec2test_error_YYYY-MM-DD.log，只记录ERROR级别
- 保留策略：只保留最近5天的日志文件，自动清理过期文件
- 压缩策略：支持zip压缩以节省存储空间
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from app.config import get_settings


class LoggerManager:
    """日志管理器类

    负责配置和管理应用程序的日志系统，提供统一的日志接口。
    支持控制台输出、文件输出、日志轮转等功能。
    """

    def __init__(self):
        """初始化日志管理器"""
        self._configured = False
        self.settings = get_settings()

    def configure(self) -> None:
        """配置日志系统

        根据配置文件设置日志级别、输出格式、文件路径等参数。
        只能配置一次，重复调用会被忽略。
        """
        if self._configured:
            return

        # 移除默认处理器
        logger.remove()

        # 配置控制台输出
        self._configure_console()

        # 配置文件输出（默认启用文件日志）
        self._configure_file()

        self._configured = True
        logger.info("日志系统配置完成")

    def _configure_console(self) -> None:
        """配置控制台日志输出"""
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>")

        logger.add(
            sys.stdout,
            format=console_format,
            level=self.settings.logging.level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )

    def _configure_file(self) -> None:
        """配置文件日志输出

        日志文件按天轮转，文件名格式：spec2test_YYYY-MM-DD.log
        每天午夜(00:00)自动轮转，只保留最近5天的日志文件
        错误日志单独存储在spec2test_error_YYYY-MM-DD.log中
        """
        # 确保日志目录存在
        log_dir = Path("./logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # 文件格式（不包含颜色代码）
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )

        # 配置普通日志文件 - 按天轮转，保留5天
        logger.add(
            log_dir / "spec2test_{time:YYYY-MM-DD}.log",
            format=file_format,
            level=self.settings.logging.level,
            rotation="00:00",  # 每天午夜轮转
            retention="5 days",  # 只保留最近5天
            compression=self.settings.logging.compression,
            backtrace=True,
            diagnose=True
        )

        # 配置错误日志文件 - 按天轮转，保留5天
        logger.add(
            log_dir / "spec2test_error_{time:YYYY-MM-DD}.log",
            format=file_format,
            level="ERROR",
            rotation="00:00",  # 每天午夜轮转
            retention="5 days",  # 只保留最近5天
            compression=self.settings.logging.compression,
            backtrace=True,
            diagnose=True
        )

    def get_logger(self, name: Optional[str] = None) -> "logger":
        """获取日志记录器实例

        Args:
            name: 日志记录器名称，通常使用模块名

        Returns:
            配置好的日志记录器实例
        """
        if not self._configured:
            self.configure()

        if name:
            return logger.bind(name=name)
        return logger


# 全局日志管理器实例
_logger_manager = LoggerManager()


def get_logger(name: Optional[str] = None) -> "logger":
    """获取日志记录器的便捷函数

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器实例

    Example:
        >>> from app.core.shared.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
    """
    return _logger_manager.get_logger(name)


def log_function_call(func_name: str, args: tuple = (),
                      kwargs: Dict[str, Any] = None) -> None:
    """记录函数调用日志

    Args:
        func_name: 函数名称
        args: 位置参数
        kwargs: 关键字参数
    """
    kwargs = kwargs or {}
    logger.debug(f"调用函数: {func_name}, 参数: args={args}, kwargs={kwargs}")


def log_exception(exc: Exception, context: str = "") -> None:
    """记录异常日志

    Args:
        exc: 异常对象
        context: 异常上下文信息
    """
    context_msg = f" - 上下文: {context}" if context else ""
    logger.exception(f"发生异常: {type(exc).__name__}: {str(exc)}{context_msg}")


def log_performance(operation: str, duration: float,
                    details: Dict[str, Any] = None) -> None:
    """记录性能日志

    Args:
        operation: 操作名称
        duration: 执行时间（秒）
        details: 详细信息
    """
    details = details or {}
    logger.info(f"性能统计 - 操作: {operation}, 耗时: {duration:.3f}s, 详情: {details}")


# 初始化日志系统
_logger_manager.configure()
