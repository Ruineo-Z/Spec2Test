"""
配置管理模块的测试
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import (
    DatabaseConfig,
    FileStorageConfig,
    GeminiConfig,
    LoggingConfig,
    OllamaConfig,
    RedisConfig,
    Settings,
    get_settings,
)


class TestDatabaseConfig:
    """测试数据库配置"""

    def test_default_values(self):
        """测试默认数据库配置值"""
        config = DatabaseConfig(password="test_password")
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "spec2test"
        assert config.user == "spec2test_user"
        assert config.password == "test_password"
        assert config.echo is False
    
    def test_database_url_construction(self):
        """Test database URL construction."""
        config = DatabaseConfig(
            host="db.example.com",
            port=5433,
            name="testdb",
            user="testuser",
            password="testpass"
        )
        
        expected_url = "postgresql://testuser:testpass@db.example.com:5433/testdb"
        assert config.url == expected_url
    
    def test_async_database_url_construction(self):
        """Test async database URL construction."""
        config = DatabaseConfig(
            host="db.example.com",
            port=5433,
            name="testdb",
            user="testuser",
            password="testpass"
        )
        
        expected_url = "postgresql+asyncpg://testuser:testpass@db.example.com:5433/testdb"
        assert config.async_url == expected_url


class TestRedisConfig:
    """Test Redis configuration."""
    
    def test_default_values(self):
        """Test default Redis configuration values."""
        config = RedisConfig()
        
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
    
    def test_redis_url_without_password(self):
        """Test Redis URL construction without password."""
        config = RedisConfig(host="redis.example.com", port=6380, db=1)
        
        expected_url = "redis://redis.example.com:6380/1"
        assert config.url == expected_url
    
    def test_redis_url_with_password(self):
        """Test Redis URL construction with password."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret"
        )
        
        expected_url = "redis://:secret@redis.example.com:6380/1"
        assert config.url == expected_url


class TestGeminiConfig:
    """Test Gemini LLM configuration."""
    
    def test_default_values(self):
        """Test default Gemini configuration values."""
        config = GeminiConfig(api_key="test_key")
        
        assert config.api_key == "test_key"
        assert config.model == "gemini-1.5-pro"
        assert config.temperature == 0.1
        assert config.max_tokens == 8192
    
    def test_temperature_validation(self):
        """Test temperature validation."""
        # Valid temperature
        config = GeminiConfig(api_key="test_key", temperature=0.5)
        assert config.temperature == 0.5
        
        # Invalid temperature - too low
        with pytest.raises(ValidationError):
            GeminiConfig(api_key="test_key", temperature=-0.1)
        
        # Invalid temperature - too high
        with pytest.raises(ValidationError):
            GeminiConfig(api_key="test_key", temperature=2.1)


class TestOllamaConfig:
    """Test Ollama LLM configuration."""
    
    def test_default_values(self):
        """Test default Ollama configuration values."""
        config = OllamaConfig()
        
        assert config.base_url == "http://localhost:11434"
        assert config.model == "llama3.1:8b"
        assert config.timeout == 300
    
    def test_base_url_normalization(self):
        """Test base URL normalization (removes trailing slash)."""
        config = OllamaConfig(base_url="http://localhost:11434/")
        assert config.base_url == "http://localhost:11434"


class TestFileStorageConfig:
    """Test file storage configuration."""
    
    def test_default_values(self):
        """Test default file storage configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = FileStorageConfig(upload_dir=temp_dir)
            
            assert config.upload_dir == temp_dir
            assert config.max_file_size == 10485760  # 10MB
            assert config.allowed_file_types == ["json", "yaml", "yml", "md"]
    
    def test_upload_directory_creation(self):
        """Test upload directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path = os.path.join(temp_dir, "uploads", "test")
            config = FileStorageConfig(upload_dir=upload_path)
            
            assert os.path.exists(upload_path)
            assert config.upload_dir == upload_path
    
    def test_file_types_normalization(self):
        """Test file types are normalized (lowercase, no dots)."""
        config = FileStorageConfig(
            upload_dir="./test",
            allowed_file_types=[".JSON", "YAML", ".yml", "md"]
        )
        
        assert config.allowed_file_types == ["json", "yaml", "yml", "md"]


class TestLoggingConfig:
    """Test logging configuration."""
    
    def test_default_values(self):
        """Test default logging configuration values."""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.rotation == "1 week"
        assert config.retention == "1 month"
        assert config.compression == "zip"
    
    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log level
        config = LoggingConfig(level="DEBUG")
        assert config.level == "DEBUG"
        
        # Valid log level (case insensitive)
        config = LoggingConfig(level="error")
        assert config.level == "ERROR"
        
        # Invalid log level
        with pytest.raises(ValidationError):
            LoggingConfig(level="INVALID")


class TestSettings:
    """Test main settings class."""
    
    def test_default_values(self):
        """Test default settings values."""
        with patch.dict(os.environ, {"SECRET_KEY": "test_secret", "GEMINI_API_KEY": "test_key", "DB_PASSWORD": "test_db_pass"}):
            settings = Settings()

            assert settings.app_name == "Spec2Test Backend"
            assert settings.app_version == "0.1.0"
            assert settings.debug is False
            assert settings.environment == "development"
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000
    
    def test_environment_validation(self):
        """Test environment validation."""
        # Valid environment
        with patch.dict(os.environ, {"SECRET_KEY": "test_secret", "GEMINI_API_KEY": "test_key", "DB_PASSWORD": "test_db_pass"}):
            settings = Settings(environment="production")
            assert settings.environment == "production"

        # Invalid environment
        with patch.dict(os.environ, {"SECRET_KEY": "test_secret", "GEMINI_API_KEY": "test_key", "DB_PASSWORD": "test_db_pass"}):
            with pytest.raises(ValidationError):
                Settings(environment="invalid_env")
    
    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        with patch.dict(os.environ, {"SECRET_KEY": "test_secret", "GEMINI_API_KEY": "test_key", "DB_PASSWORD": "test_db_pass"}):
            settings1 = get_settings()
            settings2 = get_settings()

            # Should be the same instance due to caching
            assert settings1 is settings2
