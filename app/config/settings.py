"""应用配置管理

使用Pydantic Settings进行配置管理，支持环境变量和.env文件。
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """LLM相关配置"""

    # 服务提供商选择
    provider: str = Field(default="gemini", env="LLM_PROVIDER")  # openai 或 gemini

    # OpenAI配置
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_base_url: Optional[str] = Field(default=None, env="OPENAI_BASE_URL")

    # Gemini配置
    gemini_api_key: Optional[str] = Field(
        default="AIzaSyBnllTxBgQY6CIunsWLthUrOK0KTrVcFfU", env="GEMINI_API_KEY"
    )
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")

    # 生成参数
    max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    timeout: int = Field(default=60, env="LLM_TIMEOUT")

    # 重试配置
    max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="LLM_RETRY_DELAY")

    model_config = {"env_prefix": "LLM_", "case_sensitive": False}


class TestSettings(BaseSettings):
    """测试相关配置"""

    # 执行配置
    timeout: int = Field(default=30, env="TEST_TIMEOUT")
    max_retries: int = Field(default=2, env="TEST_MAX_RETRIES")
    parallel_workers: int = Field(default=4, env="TEST_PARALLEL_WORKERS")

    # 输出配置
    output_dir: Path = Field(default=Path("./test_output"), env="TEST_OUTPUT_DIR")
    keep_generated_code: bool = Field(default=True, env="TEST_KEEP_CODE")

    # 测试用例生成配置
    max_test_cases_per_endpoint: int = Field(
        default=10, env="TEST_MAX_CASES_PER_ENDPOINT"
    )
    include_edge_cases: bool = Field(default=True, env="TEST_INCLUDE_EDGE_CASES")
    include_security_tests: bool = Field(default=True, env="TEST_INCLUDE_SECURITY")

    # 报告配置
    report_formats: List[str] = Field(
        default=["html", "json"], env="TEST_REPORT_FORMATS"
    )
    include_ai_analysis: bool = Field(default=True, env="TEST_INCLUDE_AI_ANALYSIS")

    model_config = {"env_prefix": "TEST_", "case_sensitive": False}


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    driver: str = Field("sqlite", description="数据库驱动")
    host: str = Field("localhost", description="数据库主机")
    port: int = Field(5432, description="数据库端口")
    name: str = Field("spec2test.db", description="数据库名称")
    user: Optional[str] = Field(None, description="数据库用户")
    password: Optional[str] = Field(None, description="数据库密码")

    # 连接池配置
    pool_size: int = Field(10, description="连接池大小")
    max_overflow: int = Field(20, description="最大溢出连接数")
    pool_timeout: int = Field(30, description="连接池超时时间")
    pool_recycle: int = Field(3600, description="连接回收时间")

    # 其他配置
    echo: bool = Field(False, description="是否打印SQL语句")
    echo_pool: bool = Field(False, description="是否打印连接池信息")

    model_config = {"env_prefix": "DB_", "case_sensitive": False}


class LogSettings(BaseSettings):
    """日志配置 - 使用loguru"""

    # 日志级别
    level: str = Field(default="INFO", env="LOG_LEVEL")

    # 日志格式
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        env="LOG_FORMAT",
    )

    # 文件日志配置
    file_enabled: bool = Field(default=True, env="LOG_FILE_ENABLED")
    file_path: Path = Field(default=Path("./logs/app.log"), env="LOG_FILE_PATH")
    file_rotation: str = Field(default="10 MB", env="LOG_FILE_ROTATION")
    file_retention: str = Field(default="30 days", env="LOG_FILE_RETENTION")

    # 控制台日志配置
    console_enabled: bool = Field(default=True, env="LOG_CONSOLE_ENABLED")
    console_colorize: bool = Field(default=True, env="LOG_CONSOLE_COLORIZE")

    # 结构化日志
    json_format: bool = Field(default=False, env="LOG_JSON_FORMAT")

    # 敏感信息过滤
    mask_sensitive: bool = Field(default=True, env="LOG_MASK_SENSITIVE")
    sensitive_fields: List[str] = Field(
        default=["password", "token", "api_key", "secret"], env="LOG_SENSITIVE_FIELDS"
    )

    model_config = {"env_prefix": "LOG_", "case_sensitive": False}


class AppSettings(BaseSettings):
    """应用主配置"""

    # 应用基础信息
    app_name: str = Field(default="Spec2Test", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # API配置
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")

    # CORS配置
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")

    # 安全配置
    secret_key: str = Field(
        default="dev-secret-key-change-in-production", env="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # 文件上传配置
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=[".yaml", ".yml", ".json"], env="ALLOWED_FILE_TYPES"
    )

    # 工作目录配置
    work_dir: Path = Field(default=Path("./workspace"), env="WORK_DIR")
    temp_dir: Path = Field(default=Path("./temp"), env="TEMP_DIR")

    # 子配置
    llm: LLMSettings = LLMSettings()
    test: TestSettings = TestSettings()
    database: DatabaseSettings = DatabaseSettings()
    log: LogSettings = LogSettings()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.test.output_dir.mkdir(parents=True, exist_ok=True)
        self.log.file_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库配置
        if not self.database:
            self.database = DatabaseSettings()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_nested_delimiter": "__",
    }


# 全局配置实例
settings = AppSettings()


# 配置验证函数
def validate_settings() -> bool:
    """验证配置是否正确"""
    try:
        # 验证必需的配置项
        if settings.llm.openai_api_key:
            assert settings.llm.openai_api_key.strip(), "OpenAI API Key cannot be empty"
        assert settings.secret_key, "Secret key is required"

        # 验证目录权限
        assert (
            settings.work_dir.exists()
        ), f"Work directory {settings.work_dir} does not exist"
        assert (
            settings.temp_dir.exists()
        ), f"Temp directory {settings.temp_dir} does not exist"

        return True
    except Exception as e:
        from loguru import logger

        logger.error(f"Configuration validation failed: {e}")
        return False


# 导出配置
__all__ = [
    "AppSettings",
    "LLMSettings",
    "TestSettings",
    "DatabaseSettings",
    "LogSettings",
    "settings",
    "validate_settings",
]
