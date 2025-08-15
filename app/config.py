"""
Spec2Test 后端配置管理模块

本模块为 Spec2Test 后端应用程序提供集中化的配置管理。
使用 Pydantic Settings 进行类型安全的环境变量配置加载。
"""

import os
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """数据库配置设置"""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = Field(default="localhost", description="数据库主机地址")
    port: int = Field(default=5432, description="数据库端口")
    name: str = Field(default="spec2test", description="数据库名称")
    user: str = Field(default="spec2test_user", description="数据库用户名")
    password: str = Field(default="", description="数据库密码")
    echo: bool = Field(default=False, description="启用SQLAlchemy查询日志")

    @property
    def url(self) -> str:
        """从配置组件构建数据库URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        """从配置组件构建异步数据库URL"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    """Redis配置设置"""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost", description="Redis主机地址")
    port: int = Field(default=6379, description="Redis端口")
    db: int = Field(default=0, description="Redis数据库编号")
    password: Optional[str] = Field(default=None, description="Redis密码")

    @property
    def url(self) -> str:
        """从配置组件构建Redis URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class GeminiConfig(BaseSettings):
    """Google Gemini LLM配置设置"""

    model_config = SettingsConfigDict(env_prefix="GEMINI_")

    api_key: str = Field(default="", description="Gemini API密钥")
    model: str = Field(default="gemini-1.5-pro", description="Gemini模型名称")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=8192, gt=0, description="最大生成token数")

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """验证温度值在有效范围内"""
        if not 0.0 <= v <= 2.0:
            raise ValueError("温度值必须在0.0到2.0之间")
        return v


class OllamaConfig(BaseSettings):
    """Ollama本地LLM配置设置"""

    model_config = SettingsConfigDict(env_prefix="OLLAMA_")

    base_url: str = Field(default="http://localhost:11434", description="Ollama基础URL")
    model: str = Field(default="llama3.1:8b", description="Ollama模型名称")
    timeout: int = Field(default=300, gt=0, description="请求超时时间（秒）")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """确保基础URL不以斜杠结尾"""
        return v.rstrip("/")


class LLMConfig(BaseSettings):
    """LLM配置设置"""

    model_config = SettingsConfigDict(env_prefix="")

    default_provider: str = Field(default="gemini", description="默认LLM提供商")
    gemini: GeminiConfig = Field(default_factory=lambda: GeminiConfig())
    ollama: OllamaConfig = Field(default_factory=lambda: OllamaConfig())

    @field_validator("default_provider")
    @classmethod
    def validate_default_provider(cls, v: str) -> str:
        """验证默认提供商是否受支持"""
        if v not in ["gemini", "ollama"]:
            raise ValueError("默认提供商必须是 'gemini' 或 'ollama'")
        return v


class FileStorageConfig(BaseSettings):
    """文件存储配置设置"""

    model_config = SettingsConfigDict(env_prefix="")

    upload_dir: str = Field(default="./uploads", description="上传目录路径")
    max_file_size: int = Field(default=10485760, gt=0, description="最大文件大小（字节，10MB）")
    allowed_file_types: List[str] = Field(
        default=["json", "yaml", "yml", "md"], description="允许的文件扩展名"
    )

    @field_validator("upload_dir")
    @classmethod
    def validate_upload_dir(cls, v: str) -> str:
        """确保上传目录存在"""
        os.makedirs(v, exist_ok=True)
        return v

    @field_validator("allowed_file_types")
    @classmethod
    def validate_file_types(cls, v: List[str]) -> List[str]:
        """规范化文件扩展名"""
        return [ext.lower().lstrip(".") for ext in v]


class LoggingConfig(BaseSettings):
    """日志配置设置"""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        description="日志格式字符串",
    )
    rotation: str = Field(default="1 week", description="日志轮转间隔")
    retention: str = Field(default="1 month", description="日志保留期")
    compression: str = Field(default="zip", description="日志压缩格式")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = [
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"日志级别必须是以下之一: {', '.join(valid_levels)}")
        return v_upper


class SecurityConfig(BaseSettings):
    """安全配置设置"""

    model_config = SettingsConfigDict(env_prefix="")

    secret_key: str = Field(default="", description="JWT令牌密钥")
    algorithm: str = Field(default="HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(
        default=30, gt=0, description="访问令牌过期时间（分钟）"
    )

    # CORS设置
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="允许的CORS源",
    )
    cors_allow_credentials: bool = Field(default=True, description="允许CORS凭据")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], description="允许的CORS方法"
    )
    cors_allow_headers: List[str] = Field(default=["*"], description="允许的CORS头部")


class PerformanceConfig(BaseSettings):
    """性能配置设置"""

    model_config = SettingsConfigDict(env_prefix="")

    # HTTP客户端设置
    http_timeout: int = Field(default=30, gt=0, description="HTTP请求超时时间")
    http_max_retries: int = Field(default=3, ge=0, description="HTTP最大重试次数")
    http_retry_delay: int = Field(default=1, gt=0, description="HTTP重试延迟（秒）")

    # 文档处理
    max_document_size: int = Field(default=5242880, gt=0, description="最大文档大小（5MB）")
    chunk_size: int = Field(default=4096, gt=0, description="文档块大小")
    max_chunks_per_document: int = Field(default=1000, gt=0, description="每个文档最大块数")

    # 并发处理
    max_concurrent_tests: int = Field(default=10, gt=0, description="最大并发测试执行数")
    max_concurrent_analysis: int = Field(default=5, gt=0, description="最大并发分析任务数")

    # 测试生成并发配置
    max_concurrent_workers: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_MAX_CONCURRENT_WORKERS", "8")),
        description="测试生成最大并发工作线程数"
    )
    concurrent_threshold: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_CONCURRENT_THRESHOLD", "3")),
        description="启用并发的端点数量阈值"
    )


class Settings(BaseSettings):
    """主应用程序设置"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # 应用程序设置
    app_name: str = Field(default="Spec2Test Backend", description="应用程序名称")
    app_version: str = Field(default="0.1.0", description="应用程序版本")
    app_description: str = Field(default="AI驱动的API文档测试工具后端", description="应用程序描述")
    debug: bool = Field(default=False, description="调试模式")
    environment: str = Field(default="development", description="环境名称")

    # 服务器设置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8000, gt=0, le=65535, description="服务器端口")
    reload: bool = Field(default=True, description="代码更改时自动重载")

    # 配置部分
    database: DatabaseConfig = Field(default_factory=lambda: DatabaseConfig())
    redis: RedisConfig = Field(default_factory=lambda: RedisConfig())
    llm: LLMConfig = Field(default_factory=lambda: LLMConfig())
    file_storage: FileStorageConfig = Field(default_factory=lambda: FileStorageConfig())
    logging: LoggingConfig = Field(default_factory=lambda: LoggingConfig())
    security: SecurityConfig = Field(default_factory=lambda: SecurityConfig())
    performance: PerformanceConfig = Field(default_factory=lambda: PerformanceConfig())

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证环境名称"""
        valid_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"环境必须是以下之一: {', '.join(valid_envs)}")
        return v.lower()


@lru_cache()
def get_settings() -> Settings:
    """
    获取缓存的应用程序设置

    此函数使用LRU缓存确保设置只加载一次，
    并在整个应用程序生命周期中重复使用。

    Returns:
        Settings: 应用程序设置实例
    """
    return Settings()


# 获取特定配置部分的便捷函数
def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return get_settings().database


def get_redis_config() -> RedisConfig:
    """获取Redis配置"""
    return get_settings().redis


def get_llm_config() -> LLMConfig:
    """获取LLM配置"""
    return get_settings().llm


def get_file_storage_config() -> FileStorageConfig:
    """获取文件存储配置"""
    return get_settings().file_storage


def get_logging_config() -> LoggingConfig:
    """获取日志配置"""
    return get_settings().logging


def get_security_config() -> SecurityConfig:
    """获取安全配置"""
    return get_settings().security


def get_performance_config() -> PerformanceConfig:
    """获取性能配置"""
    return get_settings().performance
