"""
应用程序配置设置

使用Pydantic进行配置管理，支持环境变量覆盖。
"""

import os
from typing import List, Optional
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """应用程序设置"""
    
    # 基础配置
    PROJECT_NAME: str = Field(
        default="Spec2Test",
        description="项目名称"
    )
    
    VERSION: str = Field(
        default="1.0.0",
        description="版本号"
    )
    
    ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development"),
        description="运行环境"
    )
    
    DEBUG: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true",
        description="调试模式"
    )
    
    # API服务配置
    HOST: str = Field(
        default_factory=lambda: os.getenv("HOST", "0.0.0.0"),
        description="API服务主机地址"
    )
    
    PORT: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "8000")),
        description="API服务端口"
    )
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            origin.strip() 
            for origin in os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000").split(",")
            if origin.strip()
        ],
        description="允许的CORS源"
    )
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./spec2test.db"),
        description="数据库连接URL"
    )
    
    # Redis配置
    REDIS_URL: str = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        description="Redis连接URL"
    )
    
    # 日志配置
    LOG_LEVEL: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="日志级别"
    )
    
    LOG_FILE: Optional[str] = Field(
        default_factory=lambda: os.getenv("LOG_FILE"),
        description="日志文件路径"
    )
    
    # 安全配置
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "your-secret-key-here"),
        description="应用密钥"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        description="访问令牌过期时间(分钟)"
    )
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024))),  # 10MB
        description="最大上传文件大小(字节)"
    )
    
    UPLOAD_DIR: str = Field(
        default_factory=lambda: os.getenv("UPLOAD_DIR", "./uploads"),
        description="文件上传目录"
    )
    
    # 任务配置
    CELERY_BROKER_URL: str = Field(
        default_factory=lambda: os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        description="Celery消息代理URL"
    )
    
    CELERY_RESULT_BACKEND: str = Field(
        default_factory=lambda: os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        description="Celery结果后端URL"
    )
    
    # 外部服务配置
    OPENAI_API_KEY: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        description="OpenAI API密钥"
    )
    
    GEMINI_API_KEY: Optional[str] = Field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY"),
        description="Gemini API密钥"
    )
    
    # 测试配置
    TEST_DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv("TEST_DATABASE_URL", "sqlite:///./test_spec2test.db"),
        description="测试数据库URL"
    )
    
    # 性能配置
    MAX_WORKERS: int = Field(
        default_factory=lambda: int(os.getenv("MAX_WORKERS", "4")),
        description="最大工作进程数"
    )
    
    REQUEST_TIMEOUT: int = Field(
        default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30")),
        description="请求超时时间(秒)"
    )
    
    # 缓存配置
    CACHE_TTL: int = Field(
        default_factory=lambda: int(os.getenv("CACHE_TTL", "3600")),  # 1小时
        description="缓存过期时间(秒)"
    )
    
    # 监控配置
    ENABLE_METRICS: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_METRICS", "false").lower() == "true",
        description="启用指标收集"
    )
    
    METRICS_PORT: int = Field(
        default_factory=lambda: int(os.getenv("METRICS_PORT", "9090")),
        description="指标服务端口"
    )
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取应用程序设置（单例模式）"""
    return Settings()
