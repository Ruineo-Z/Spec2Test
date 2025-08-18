"""
任务管理器测试
"""

import asyncio
import pytest
from datetime import datetime

from app.core.tasks.models import (
    TaskCreateRequest,
    TaskType,
    TaskStatus,
    TaskPriority,
    TaskExecutionMode
)


class TestEnhancedTaskManager:
    """测试增强任务管理器"""
    
    async def test_manager_initialization(self, task_manager):
        """测试管理器初始化"""
        assert task_manager.storage is not None
        assert task_manager.max_cpu_workers == 2
        assert task_manager.max_io_workers == 4
        assert len(task_manager.task_handlers) == 3  # 从conftest.py注册的处理器
    
    async def test_submit_task_success(self, task_manager, cleanup_monitors):
        """测试成功提交任务"""
        request = TaskCreateRequest(
            task_type=TaskType.DOCUMENT_ANALYSIS,
            input_data={"test_id": "submit_test", "content": "test document"},
            priority=TaskPriority.HIGH,
            timeout_seconds=60
        )
        
        # 提交任务
        task_id = await task_manager.submit_task(request)
        
        assert task_id is not None
        assert isinstance(task_id, str)
        
        # 等待任务完成
        await asyncio.sleep(0.5)
        
        # 检查任务状态
        task = await task_manager.get_task_status(task_id)
        assert task is not None
        assert task.status in [TaskStatus.COMPLETED, TaskStatus.RUNNING]
    
    async def test_submit_task_no_handler(self, task_manager):
        """测试提交没有处理器的任务"""
        request = TaskCreateRequest(
            task_type=TaskType.REPORT_GENERATION,  # 没有注册处理器
            input_data={"report_type": "summary"}
        )
        
        # 应该抛出异常
        with pytest.raises(ValueError, match="No handler registered"):
            await task_manager.submit_task(request)
    
    async def test_get_task_status(self, task_manager, cleanup_monitors):
        """测试获取任务状态"""
        request = TaskCreateRequest(
            task_type=TaskType.DOCUMENT_ANALYSIS,
            input_data={"test_id": "status_test"}
        )
        
        # 提交任务
        task_id = await task_manager.submit_task(request)
        
        # 获取状态
        task = await task_manager.get_task_status(task_id)
        
        assert task is not None
        assert task.task_id == task_id
        assert task.task_type == TaskType.DOCUMENT_ANALYSIS
        assert task.input_data == {"test_id": "status_test"}
    
    async def test_get_nonexistent_task_status(self, task_manager):
        """测试获取不存在任务的状态"""
        task = await task_manager.get_task_status("nonexistent-task")
        assert task is None
    
    async def test_cancel_task(self, task_manager, cleanup_monitors):
        """测试取消任务"""
        request = TaskCreateRequest(
            task_type=TaskType.TEST_GENERATION,  # 慢速处理器
            input_data={"test_count": 100}
        )
        
        # 提交任务
        task_id = await task_manager.submit_task(request)
        
        # 等待任务开始
        await asyncio.sleep(0.1)
        
        # 取消任务
        success = await task_manager.cancel_task(task_id)
        assert success is True
        
        # 等待取消完成
        await asyncio.sleep(0.1)
        
        # 检查任务状态
        task = await task_manager.get_task_status(task_id)
        assert task.status == TaskStatus.CANCELLED
    
    async def test_cancel_nonexistent_task(self, task_manager):
        """测试取消不存在的任务"""
        success = await task_manager.cancel_task("nonexistent-task")
        assert success is False
    
    async def test_retry_task_success(self, task_manager, cleanup_monitors):
        """测试成功重试任务"""
        request = TaskCreateRequest(
            task_type=TaskType.TEST_EXECUTION,  # 失败处理器
            input_data={"should_fail": True},
            max_retries=2
        )
        
        # 提交任务（会失败）
        task_id = await task_manager.submit_task(request)
        
        # 等待任务失败
        await asyncio.sleep(0.5)
        
        # 检查任务失败
        task = await task_manager.get_task_status(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.retry_count == 0
        
        # 重试任务
        success = await task_manager.retry_task(task_id)
        assert success is True
        
        # 等待重试完成
        await asyncio.sleep(0.5)
        
        # 检查重试状态
        task = await task_manager.get_task_status(task_id)
        assert task.retry_count == 1
    
    async def test_retry_task_max_retries_exceeded(self, task_manager, cleanup_monitors):
        """测试超过最大重试次数"""
        request = TaskCreateRequest(
            task_type=TaskType.TEST_EXECUTION,  # 失败处理器
            input_data={"should_fail": True},
            max_retries=1
        )
        
        # 提交任务
        task_id = await task_manager.submit_task(request)
        
        # 等待任务失败
        await asyncio.sleep(0.5)
        
        # 第一次重试
        success = await task_manager.retry_task(task_id)
        assert success is True
        
        # 等待重试失败
        await asyncio.sleep(0.5)
        
        # 第二次重试（应该失败）
        success = await task_manager.retry_task(task_id)
        assert success is False
    
    async def test_retry_nonexistent_task(self, task_manager):
        """测试重试不存在的任务"""
        success = await task_manager.retry_task("nonexistent-task")
        assert success is False
    
    async def test_register_handler(self, task_manager, mock_handler):
        """测试注册处理器"""
        # 注册新处理器
        task_manager.register_handler(TaskType.REPORT_GENERATION, mock_handler)
        
        # 验证处理器已注册
        assert TaskType.REPORT_GENERATION in task_manager.task_handlers
        assert task_manager.task_handlers[TaskType.REPORT_GENERATION] == mock_handler
    
    async def test_unregister_handler(self, task_manager):
        """测试注销处理器"""
        # 注销现有处理器
        task_manager.unregister_handler(TaskType.DOCUMENT_ANALYSIS)
        
        # 验证处理器已注销
        assert TaskType.DOCUMENT_ANALYSIS not in task_manager.task_handlers
    
    async def test_get_statistics(self, task_manager, cleanup_monitors):
        """测试获取统计信息"""
        # 提交几个任务
        for i in range(3):
            request = TaskCreateRequest(
                task_type=TaskType.DOCUMENT_ANALYSIS,
                input_data={"test_id": f"stats_test_{i}"}
            )
            await task_manager.submit_task(request)
        
        # 等待任务处理
        await asyncio.sleep(0.5)
        
        # 获取统计信息
        stats = await task_manager.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "running_tasks" in stats
        assert "registered_handlers" in stats
        assert "cpu_workers" in stats
        assert "io_workers" in stats
        
        assert stats["registered_handlers"] == 3
        assert stats["cpu_workers"] == 2
        assert stats["io_workers"] == 4
    
    async def test_concurrent_task_execution(self, task_manager, cleanup_monitors):
        """测试并发任务执行"""
        # 提交多个任务
        task_ids = []
        for i in range(5):
            request = TaskCreateRequest(
                task_type=TaskType.DOCUMENT_ANALYSIS,
                input_data={"test_id": f"concurrent_test_{i}"}
            )
            task_id = await task_manager.submit_task(request)
            task_ids.append(task_id)
        
        # 等待所有任务完成
        await asyncio.sleep(1.0)
        
        # 检查所有任务状态
        completed_count = 0
        for task_id in task_ids:
            task = await task_manager.get_task_status(task_id)
            if task.status == TaskStatus.COMPLETED:
                completed_count += 1
        
        assert completed_count == 5
    
    async def test_task_timeout_handling(self, task_manager, cleanup_monitors):
        """测试任务超时处理"""
        request = TaskCreateRequest(
            task_type=TaskType.TEST_GENERATION,  # 慢速处理器（2秒）
            input_data={"test_count": 100},
            timeout_seconds=1  # 1秒超时
        )
        
        # 提交任务
        task_id = await task_manager.submit_task(request)
        
        # 等待超时
        await asyncio.sleep(2.0)
        
        # 检查任务状态（应该超时或失败）
        task = await task_manager.get_task_status(task_id)
        assert task.status in [TaskStatus.TIMEOUT, TaskStatus.FAILED]
    
    async def test_task_execution_with_different_modes(self, task_manager, mock_handler, cleanup_monitors):
        """测试不同执行模式的任务"""
        # 注册处理器
        task_manager.register_handler(TaskType.REPORT_GENERATION, mock_handler)
        
        # 测试不同执行模式
        execution_modes = [
            TaskExecutionMode.ASYNC_COROUTINE,
            TaskExecutionMode.CPU_INTENSIVE,
            TaskExecutionMode.IO_INTENSIVE
        ]
        
        task_ids = []
        for mode in execution_modes:
            request = TaskCreateRequest(
                task_type=TaskType.REPORT_GENERATION,
                input_data={"mode": mode.value},
                execution_mode=mode
            )
            task_id = await task_manager.submit_task(request)
            task_ids.append(task_id)
        
        # 等待任务完成
        await asyncio.sleep(1.0)
        
        # 检查所有任务完成
        for task_id in task_ids:
            task = await task_manager.get_task_status(task_id)
            assert task.status == TaskStatus.COMPLETED
        
        # 验证处理器被调用
        assert mock_handler.call_count == 3
