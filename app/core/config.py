#!/usr/bin/env python3
"""
应用配置模块
"""

import os
from typing import List, Optional

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # =============================================================================
    # 应用基础配置
    # =============================================================================
    APP_NAME: str = "Spec2Test"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # API服务配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # 处理JSON格式的字符串
                import json

                return json.loads(v)
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    @validator("CORS_METHODS", pre=True)
    def assemble_cors_methods(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    @validator("CORS_HEADERS", pre=True)
    def assemble_cors_headers(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 工作目录配置
    WORK_DIR: str = "./workspace"
    TEMP_DIR: str = "./temp"

    # =============================================================================
    # LLM配置
    # =============================================================================
    LLM_PROVIDER: str = "gemini"

    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_BASE_URL: Optional[str] = None

    # Gemini配置
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # 生成参数
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT: int = 60

    # 重试配置
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: float = 1.0

    # =============================================================================
    # 测试配置
    # =============================================================================
    # 执行配置
    TEST_TIMEOUT: int = 30
    TEST_MAX_RETRIES: int = 2
    TEST_PARALLEL_WORKERS: int = 4

    # 输出配置
    TEST_OUTPUT_DIR: str = "./test_output"
    TEST_KEEP_CODE: bool = True

    # 测试用例生成配置
    TEST_MAX_CASES_PER_ENDPOINT: int = 10
    TEST_INCLUDE_EDGE_CASES: bool = True
    TEST_INCLUDE_SECURITY: bool = True

    # 报告配置
    TEST_REPORT_FORMATS: List[str] = ["html", "json"]
    TEST_INCLUDE_AI_ANALYSIS: bool = True

    @validator("TEST_REPORT_FORMATS", pre=True)
    def assemble_test_report_formats(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # =============================================================================
    # 数据库配置
    # =============================================================================
    DB_DRIVER: str = "sqlite"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "spec2test.db"
    DB_USER: str = "your-db-user"
    DB_PASSWORD: str = "your-db-password"

    # 连接池配置
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # 其他数据库配置
    DB_ECHO: bool = False
    DB_ECHO_POOL: bool = False

    # =============================================================================
    # 日志配置
    # =============================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"

    # 文件日志配置
    LOG_FILE_ENABLED: bool = True
    LOG_FILE_PATH: str = "./logs/app.log"
    LOG_FILE_ROTATION: str = "10 MB"
    LOG_FILE_RETENTION: str = "30 days"

    # 控制台日志配置
    LOG_CONSOLE_ENABLED: bool = True
    LOG_CONSOLE_COLORIZE: bool = True

    # 结构化日志
    LOG_JSON_FORMAT: bool = False

    # 敏感信息过滤
    LOG_MASK_SENSITIVE: bool = True
    LOG_SENSITIVE_FIELDS: List[str] = ["password", "token", "api_key", "secret"]

    @validator("LOG_SENSITIVE_FIELDS", pre=True)
    def assemble_log_sensitive_fields(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # =============================================================================
    # 兼容性字段（保持向后兼容）
    # =============================================================================
    PROJECT_NAME: str = "Spec2Test"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "基于AI的API测试用例生成器"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".json", ".yaml", ".yml"]
    MAX_TEST_CASES_PER_ENDPOINT: int = 10
    DEFAULT_TEST_TYPES: List[str] = ["normal", "error", "boundary"]
    DATABASE_URL: Optional[str] = None

    @validator("ALLOWED_FILE_TYPES", pre=True)
    def assemble_allowed_file_types(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                return json.loads(v)
            else:
                return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 允许额外的字段


# 创建全局配置实例
settings = Settings()
