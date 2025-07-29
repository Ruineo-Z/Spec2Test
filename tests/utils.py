"""测试工具模块 - 提供测试辅助函数和工具类"""

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from unittest.mock import Mock, patch

if TYPE_CHECKING:
    import pytest
    from fastapi.testclient import TestClient


class TestDataBuilder:
    """测试数据构建器"""

    @staticmethod
    def create_openapi_spec(
        title: str = "Test API",
        version: str = "1.0.0",
        paths: Optional[Dict] = None,
        components: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """创建OpenAPI规范"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": title, "version": version},
            "paths": paths or {},
        }

        if components:
            spec["components"] = components

        return spec

    @staticmethod
    def create_api_path(
        method: str = "get",
        summary: str = "Test endpoint",
        parameters: Optional[List] = None,
        request_body: Optional[Dict] = None,
        responses: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """创建API路径定义"""
        path_item = {
            method.lower(): {
                "summary": summary,
                "responses": responses
                or {
                    "200": {
                        "description": "Success",
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    }
                },
            }
        }

        if parameters:
            path_item[method.lower()]["parameters"] = parameters

        if request_body:
            path_item[method.lower()]["requestBody"] = request_body

        return path_item

    @staticmethod
    def create_schema(
        schema_type: str = "object",
        properties: Optional[Dict] = None,
        required: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """创建JSON Schema"""
        schema = {"type": schema_type}

        if properties:
            schema["properties"] = properties

        if required:
            schema["required"] = required

        return schema


class MockLLMClient:
    """模拟LLM客户端"""

    def __init__(self, responses: Optional[List[str]] = None):
        self.responses = responses or ["Mock LLM response"]
        self.call_count = 0

    async def generate(self, prompt: str, **kwargs) -> str:
        """模拟生成响应"""
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response

    def reset(self):
        """重置调用计数"""
        self.call_count = 0


class FileTestHelper:
    """文件测试辅助类"""

    @staticmethod
    def create_temp_file(
        content: Union[str, Dict], suffix: str = ".json", encoding: str = "utf-8"
    ) -> Path:
        """创建临时文件"""
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding=encoding
        )

        if isinstance(content, dict):
            json.dump(content, temp_file, indent=2)
        else:
            temp_file.write(content)

        temp_file.close()
        return Path(temp_file.name)

    @staticmethod
    def create_temp_dir() -> Path:
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        return Path(temp_dir)

    @staticmethod
    def read_file(file_path: Path, encoding: str = "utf-8") -> str:
        """读取文件内容"""
        return file_path.read_text(encoding=encoding)

    @staticmethod
    def read_json_file(file_path: Path, encoding: str = "utf-8") -> Dict:
        """读取JSON文件"""
        content = file_path.read_text(encoding=encoding)
        return json.loads(content)


class APITestHelper:
    """API测试辅助类"""

    @staticmethod
    def assert_response_success(
        response,
        expected_status: int = 200,
        expected_content_type: str = "application/json",
    ):
        """断言响应成功"""
        assert response.status_code == expected_status
        assert expected_content_type in response.headers.get("content-type", "")

    @staticmethod
    def assert_response_error(
        response, expected_status: int = 400, expected_error_code: Optional[str] = None
    ):
        """断言响应错误"""
        assert response.status_code == expected_status

        if expected_error_code:
            error_data = response.json()
            assert "error" in error_data
            assert error_data["error"]["code"] == expected_error_code

    @staticmethod
    def assert_json_schema(data: Dict, expected_keys: List[str]):
        """断言JSON数据包含期望的键"""
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

    @staticmethod
    def create_multipart_file(content: str, filename: str = "test.json"):
        """创建multipart文件上传数据"""
        return ("files", (filename, content, "application/json"))


class DatabaseTestHelper:
    """数据库测试辅助类"""

    @staticmethod
    def create_test_record(session, model_class, **kwargs):
        """创建测试记录"""
        record = model_class(**kwargs)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    @staticmethod
    def count_records(session, model_class) -> int:
        """统计记录数量"""
        return session.query(model_class).count()

    @staticmethod
    def clear_table(session, model_class):
        """清空表数据"""
        session.query(model_class).delete()
        session.commit()


class AsyncTestHelper:
    """异步测试辅助类"""

    @staticmethod
    async def run_with_timeout(coro, timeout: float = 5.0):
        """运行协程并设置超时"""
        import asyncio

        return await asyncio.wait_for(coro, timeout=timeout)

    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """创建异步Mock"""
        mock = Mock()

        async def async_return(*args, **kwargs):
            if side_effect:
                if callable(side_effect):
                    return side_effect(*args, **kwargs)
                else:
                    raise side_effect
            return return_value

        mock.return_value = async_return()
        return mock


class TestCaseGenerator:
    """测试用例生成器"""

    @staticmethod
    def generate_boundary_values(data_type: str) -> List[Any]:
        """生成边界值测试数据"""
        if data_type == "string":
            return ["", "a", "a" * 255, "a" * 256]
        elif data_type == "integer":
            return [0, 1, -1, 2147483647, -2147483648]
        elif data_type == "number":
            return [0.0, 0.1, -0.1, 1.7976931348623157e308]
        elif data_type == "array":
            return [[], [1], list(range(1000))]
        elif data_type == "object":
            return [{}, {"key": "value"}, {f"key{i}": f"value{i}" for i in range(100)}]
        else:
            return [None]

    @staticmethod
    def generate_invalid_values(data_type: str) -> List[Any]:
        """生成无效值测试数据"""
        if data_type == "string":
            return [123, [], {}, None]
        elif data_type == "integer":
            return ["string", 1.5, [], {}, None]
        elif data_type == "number":
            return ["string", [], {}, None]
        elif data_type == "boolean":
            return ["true", 1, 0, [], {}, None]
        elif data_type == "array":
            return ["string", 123, {}, None]
        elif data_type == "object":
            return ["string", 123, [], None]
        else:
            return []


# 装饰器
def skip_if_no_llm(func):
    """如果没有LLM配置则跳过测试"""
    import os

    try:
        import pytest

        return pytest.mark.skipif(
            not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"),
            reason="No LLM API key configured",
        )(func)
    except ImportError:
        return func


def slow_test(func):
    """标记为慢速测试"""
    try:
        import pytest

        return pytest.mark.slow(func)
    except ImportError:
        return func


def integration_test(func):
    """标记为集成测试"""
    try:
        import pytest

        return pytest.mark.integration(func)
    except ImportError:
        return func


def e2e_test(func):
    """标记为端到端测试"""
    try:
        import pytest

        return pytest.mark.e2e(func)
    except ImportError:
        return func


# 上下文管理器
class MockEnvironment:
    """模拟环境变量上下文管理器"""

    def __init__(self, **env_vars):
        self.env_vars = env_vars
        self.original_values = {}

    def __enter__(self):
        import os

        for key, value in self.env_vars.items():
            self.original_values[key] = os.environ.get(key)
            os.environ[key] = str(value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import os

        for key, original_value in self.original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


class CaptureLogs:
    """捕获日志上下文管理器"""

    def __init__(self, logger_name: str = None, level: str = "INFO"):
        self.logger_name = logger_name
        self.level = level
        self.records = []

    def __enter__(self):
        import logging
        from unittest.mock import patch

        def capture_log(record):
            self.records.append(record)

        logger = logging.getLogger(self.logger_name)
        self.original_level = logger.level
        logger.setLevel(getattr(logging, self.level))

        # 这里需要实际的日志捕获实现
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import logging

        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.original_level)
