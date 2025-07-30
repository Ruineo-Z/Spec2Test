"""pytest配置文件 - 全局测试配置和fixtures"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, Generator

try:
    import pytest
    import pytest_asyncio

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    # Create mock objects for when pytest is not available
    class MockPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        @staticmethod
        def skip(reason):
            def decorator(func):
                return func

            return decorator

    pytest = MockPytest()

try:
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    # 尝试导入app模块，如果失败则使用模拟
    try:
        from app.core.config import get_settings
        from app.core.database import Base, get_db
        from app.main import app

        APP_AVAILABLE = True
    except ImportError:
        # 如果app模块不可用，创建模拟对象
        APP_AVAILABLE = False

        class MockBase:
            metadata = type("MockMetadata", (), {"create_all": lambda **kwargs: None})()

        Base = MockBase()

        def get_settings():
            return type(
                "MockSettings",
                (),
                {"ENVIRONMENT": "testing", "LOG_LEVEL": "DEBUG", "TESTING": True},
            )()

        def get_db():
            yield None

        app = None

except ImportError:
    # 如果连基础依赖都没有，跳过所有数据库相关的fixture
    APP_AVAILABLE = False
    Base = None
    get_settings = lambda: None
    get_db = lambda: None
    app = None


# 测试配置
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="session")
def test_db_url(temp_dir: Path) -> str:
    """创建测试数据库URL"""
    db_path = temp_dir / "test.db"
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def test_engine(test_db_url: str):
    """创建测试数据库引擎"""
    if not APP_AVAILABLE or "create_engine" not in globals():
        pytest.skip("SQLAlchemy not available")

    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    if Base and hasattr(Base, "metadata"):
        Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_async_engine(test_db_url: str):
    """创建异步测试数据库引擎"""
    if not APP_AVAILABLE or "create_async_engine" not in globals():
        pytest.skip("SQLAlchemy async not available")

    # 将sqlite URL转换为异步版本
    async_url = test_db_url.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(
        async_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    # 注意：异步引擎的清理需要在异步上下文中进行


@pytest.fixture
def db_session(test_engine):
    """创建数据库会话"""
    if not APP_AVAILABLE or "sessionmaker" not in globals():
        pytest.skip("SQLAlchemy not available")

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def async_db_session(test_async_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建异步数据库会话"""
    if not APP_AVAILABLE or "AsyncSession" not in globals():
        pytest.skip("SQLAlchemy async not available")

    async with test_async_engine.begin() as conn:
        if Base and hasattr(Base, "metadata"):
            await conn.run_sync(Base.metadata.create_all)

    AsyncTestingSessionLocal = sessionmaker(
        test_async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest.fixture
def override_get_db(db_session):
    """覆盖数据库依赖"""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    return _override_get_db


@pytest.fixture
def client(override_get_db):
    """创建测试客户端"""
    if not APP_AVAILABLE or not app or "TestClient" not in globals():
        pytest.skip("FastAPI not available")

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """测试环境配置"""
    settings = get_settings()
    # 覆盖测试特定的设置
    settings.ENVIRONMENT = "testing"
    settings.LOG_LEVEL = "DEBUG"
    settings.TESTING = True
    return settings


# 测试数据fixtures
@pytest.fixture
def sample_openapi_spec() -> dict:
    """示例OpenAPI规范"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "A test API for unit testing",
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserCreate"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        }
                    },
                },
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                    "required": ["id", "name", "email"],
                },
                "UserCreate": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                    },
                    "required": ["name", "email"],
                },
            }
        },
    }


@pytest.fixture
def sample_invalid_openapi_spec() -> dict:
    """无效的OpenAPI规范用于测试错误处理"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Invalid API"
            # 缺少required字段 version
        },
        "paths": {
            "/invalid": {
                "get": {
                    # 缺少responses字段
                }
            }
        },
    }


@pytest.fixture
def test_yaml_content() -> str:
    """读取test.yaml文件内容用于测试"""
    test_yaml_path = Path("/Users/augenstern/development/personal/Spec2Test/test.yaml")

    if not test_yaml_path.exists():
        pytest.skip("test.yaml文件不存在")

    with open(test_yaml_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def test_yaml_file() -> Path:
    """返回test.yaml文件路径用于测试"""
    test_yaml_path = Path("/Users/augenstern/development/personal/Spec2Test/test.yaml")

    if not test_yaml_path.exists():
        pytest.skip("test.yaml文件不存在")

    return test_yaml_path


@pytest.fixture
def test_yaml_spec() -> Dict[str, Any]:
    """加载test.yaml规范文件"""
    import yaml

    test_yaml_path = Path("/Users/augenstern/development/personal/Spec2Test/test.yaml")

    if not test_yaml_path.exists():
        pytest.skip("test.yaml文件不存在")

    with open(test_yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 测试辅助函数
def assert_error_response(response, expected_status: int = None):
    """验证错误响应的结构"""
    if expected_status:
        assert response.status_code == expected_status

    assert response.status_code >= 400

    # 验证响应是JSON格式
    try:
        error_data = response.json()
    except ValueError:
        pytest.fail("错误响应不是有效的JSON格式")

    # 验证错误响应包含必要字段
    assert "detail" in error_data or "message" in error_data, "错误响应缺少错误信息字段"

    return error_data


def assert_valid_document_id(document_id):
    """验证文档ID的有效性"""
    assert document_id is not None, "文档ID不能为None"
    assert isinstance(document_id, (str, int)), "文档ID必须是字符串或整数"
    if isinstance(document_id, str):
        assert len(document_id.strip()) > 0, "文档ID不能为空字符串"
    return True


def assert_valid_response_structure(response, expected_fields: list = None):
    """验证响应结构的有效性"""
    assert response.status_code < 400, f"响应状态码错误: {response.status_code}"

    # 验证响应是JSON格式
    try:
        response_data = response.json()
    except ValueError:
        pytest.fail("响应不是有效的JSON格式")

    # 验证必需字段
    if expected_fields:
        for field in expected_fields:
            assert field in response_data, f"响应缺少必需字段: {field}"

    return response_data


# 测试标记
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """pytest配置钩子"""
    # 添加自定义标记
    config.addinivalue_line("markers", "unit: 标记单元测试")
    config.addinivalue_line("markers", "integration: 标记集成测试")
    config.addinivalue_line("markers", "e2e: 标记端到端测试")
    config.addinivalue_line("markers", "slow: 标记慢速测试")
    config.addinivalue_line("markers", "parser: 标记解析器相关测试")
    config.addinivalue_line("markers", "generator: 标记生成器相关测试")
    config.addinivalue_line("markers", "executor: 标记执行器相关测试")
    config.addinivalue_line("markers", "reporter: 标记报告器相关测试")
    config.addinivalue_line("markers", "api: 标记API相关测试")
    config.addinivalue_line("markers", "database: 标记数据库相关测试")
    config.addinivalue_line("markers", "llm: 标记LLM相关测试")


def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    # 为没有标记的测试添加默认标记
    for item in items:
        # 根据文件路径自动添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # 根据测试名称添加功能标记
        if "parser" in item.name.lower():
            item.add_marker(pytest.mark.parser)
        elif "generator" in item.name.lower():
            item.add_marker(pytest.mark.generator)
        elif "executor" in item.name.lower():
            item.add_marker(pytest.mark.executor)
        elif "reporter" in item.name.lower():
            item.add_marker(pytest.mark.reporter)
        elif "api" in item.name.lower():
            item.add_marker(pytest.mark.api)
        elif "database" in item.name.lower() or "db" in item.name.lower():
            item.add_marker(pytest.mark.database)
        elif "llm" in item.name.lower() or "ai" in item.name.lower():
            item.add_marker(pytest.mark.llm)
