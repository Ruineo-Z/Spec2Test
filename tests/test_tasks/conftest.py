"""
异步任务系统测试配置和fixtures
"""

import asyncio
import tempfile
import pytest
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

from app.core.tasks import (
    DatabaseTaskStorage,
    EnhancedTaskManager,
    TaskModel,
    TaskType,
    TaskStatus,
    TaskPriority,
    TaskExecutionMode,
    TaskCreateRequest,
    task_monitor,
    task_context_manager,
    retry_manager,
    timeout_manager
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_database_url():
    """测试数据库URL"""
    # 使用内存SQLite数据库进行测试（异步驱动）
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def task_storage(test_database_url):
    """任务存储fixture"""
    storage = DatabaseTaskStorage(test_database_url)
    await storage.connect()
    yield storage
    await storage.disconnect()


@pytest.fixture
async def task_manager(task_storage):
    """任务管理器fixture"""
    manager = EnhancedTaskManager(
        storage=task_storage,
        max_cpu_workers=2,
        max_io_workers=4
    )
    
    # 注册测试处理器
    async def test_handler(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试任务处理器"""
        await asyncio.sleep(0.1)  # 模拟处理时间
        return {"result": f"processed_{input_data.get('test_id', 'unknown')}"}
    
    async def slow_handler(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """慢速任务处理器"""
        await asyncio.sleep(2.0)  # 模拟长时间处理
        return {"result": "slow_processed"}
    
    async def failing_handler(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """失败任务处理器"""
        raise ValueError("Test error")
    
    manager.register_handler(TaskType.DOCUMENT_ANALYSIS, test_handler)
    manager.register_handler(TaskType.TEST_GENERATION, slow_handler)
    manager.register_handler(TaskType.TEST_EXECUTION, failing_handler)
    
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
def sample_task_model():
    """示例任务模型"""
    return TaskModel(
        task_id="test-task-123",
        task_type=TaskType.DOCUMENT_ANALYSIS,
        status=TaskStatus.PENDING,
        priority=TaskPriority.NORMAL,
        execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
        created_at=datetime.utcnow(),
        input_data={"test_id": "123", "content": "test content"},
        timeout_seconds=300,
        max_retries=3,
        metadata={"test": True}
    )


@pytest.fixture
def sample_task_request():
    """示例任务创建请求"""
    return TaskCreateRequest(
        task_type=TaskType.DOCUMENT_ANALYSIS,
        input_data={"test_id": "456", "content": "test request"},
        priority=TaskPriority.HIGH,
        execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
        timeout_seconds=60,
        max_retries=2,
        metadata={"test_request": True}
    )


@pytest.fixture
def cleanup_monitors():
    """清理监控器状态"""
    yield
    # 测试后清理
    task_monitor.reset_statistics()
    task_context_manager.contexts.clear()


@pytest.fixture
async def mock_task_data():
    """模拟任务数据"""
    return {
        "simple_task": {
            "task_type": TaskType.DOCUMENT_ANALYSIS,
            "input_data": {"doc_id": "doc123", "content": "Simple document"},
            "expected_result": {"result": "processed_doc123"}
        },
        "slow_task": {
            "task_type": TaskType.TEST_GENERATION,
            "input_data": {"test_count": 10},
            "expected_result": {"result": "slow_processed"}
        },
        "failing_task": {
            "task_type": TaskType.TEST_EXECUTION,
            "input_data": {"should_fail": True},
            "expected_error": "Test error"
        }
    }


class MockTaskHandler:
    """模拟任务处理器"""
    
    def __init__(self):
        self.call_count = 0
        self.last_input = None
        self.should_fail = False
        self.delay = 0.0
    
    async def __call__(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.call_count += 1
        self.last_input = input_data
        
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        if self.should_fail:
            raise RuntimeError("Mock handler failure")
        
        return {"result": f"mock_processed_{self.call_count}"}


@pytest.fixture
def mock_handler():
    """模拟处理器fixture"""
    return MockTaskHandler()


# 测试标记
pytestmark = pytest.mark.asyncio
