"""
任务存储层测试
"""

import pytest
from datetime import datetime, timedelta

from app.core.tasks.storage import (
    TaskNotFoundError,
    TaskAlreadyExistsError,
    StorageException
)
from app.core.tasks.models import (
    TaskModel,
    TaskStatus,
    TaskType,
    TaskPriority,
    TaskExecutionMode,
    TaskListRequest
)


class TestDatabaseTaskStorage:
    """测试数据库任务存储"""
    
    async def test_create_task(self, task_storage, sample_task_model):
        """测试创建任务"""
        # 创建任务
        created_task = await task_storage.create_task(sample_task_model)
        
        assert created_task.task_id == sample_task_model.task_id
        assert created_task.task_type == sample_task_model.task_type
        assert created_task.status == sample_task_model.status
        assert created_task.input_data == sample_task_model.input_data
    
    async def test_create_duplicate_task(self, task_storage, sample_task_model):
        """测试创建重复任务"""
        # 创建第一个任务
        await task_storage.create_task(sample_task_model)
        
        # 尝试创建重复任务
        with pytest.raises(TaskAlreadyExistsError):
            await task_storage.create_task(sample_task_model)
    
    async def test_get_task(self, task_storage, sample_task_model):
        """测试获取任务"""
        # 创建任务
        await task_storage.create_task(sample_task_model)
        
        # 获取任务
        retrieved_task = await task_storage.get_task(sample_task_model.task_id)
        
        assert retrieved_task is not None
        assert retrieved_task.task_id == sample_task_model.task_id
        assert retrieved_task.task_type == sample_task_model.task_type
        assert retrieved_task.status == sample_task_model.status
    
    async def test_get_nonexistent_task(self, task_storage):
        """测试获取不存在的任务"""
        result = await task_storage.get_task("nonexistent-task")
        assert result is None
    
    async def test_update_task_status(self, task_storage, sample_task_model):
        """测试更新任务状态"""
        # 创建任务
        await task_storage.create_task(sample_task_model)
        
        # 更新状态
        now = datetime.utcnow()
        success = await task_storage.update_task_status(
            sample_task_model.task_id,
            TaskStatus.RUNNING,
            started_at=now
        )
        
        assert success is True
        
        # 验证更新
        updated_task = await task_storage.get_task(sample_task_model.task_id)
        assert updated_task.status == TaskStatus.RUNNING
        assert updated_task.started_at is not None
    
    async def test_update_nonexistent_task_status(self, task_storage):
        """测试更新不存在任务的状态"""
        success = await task_storage.update_task_status(
            "nonexistent-task",
            TaskStatus.RUNNING
        )
        assert success is False
    
    async def test_update_task_result(self, task_storage, sample_task_model):
        """测试更新任务结果"""
        # 创建任务
        await task_storage.create_task(sample_task_model)
        
        # 更新结果
        result_data = {"output": "test result", "count": 42}
        now = datetime.utcnow()
        
        success = await task_storage.update_task_result(
            sample_task_model.task_id,
            result_data,
            completed_at=now
        )
        
        assert success is True
        
        # 验证更新
        updated_task = await task_storage.get_task(sample_task_model.task_id)
        assert updated_task.result_data == result_data
        assert updated_task.completed_at is not None
    
    async def test_update_task_error(self, task_storage, sample_task_model):
        """测试更新任务错误"""
        # 创建任务
        await task_storage.create_task(sample_task_model)
        
        # 更新错误信息
        error_info = {"error": "Test error", "traceback": "..."}
        now = datetime.utcnow()
        
        success = await task_storage.update_task_error(
            sample_task_model.task_id,
            error_info,
            completed_at=now
        )
        
        assert success is True
        
        # 验证更新
        updated_task = await task_storage.get_task(sample_task_model.task_id)
        assert updated_task.error_info == error_info
        assert updated_task.completed_at is not None
    
    async def test_update_task_retry(self, task_storage, sample_task_model):
        """测试更新任务重试"""
        # 创建任务
        await task_storage.create_task(sample_task_model)
        
        # 更新重试信息
        retry_info = {"attempt": 2, "reason": "timeout"}
        
        success = await task_storage.update_task_retry(
            sample_task_model.task_id,
            2,
            retry_info
        )
        
        assert success is True
        
        # 验证更新
        updated_task = await task_storage.get_task(sample_task_model.task_id)
        assert updated_task.retry_count == 2
    
    async def test_list_tasks_basic(self, task_storage):
        """测试基本任务列表"""
        # 创建多个任务
        tasks = []
        for i in range(5):
            task = TaskModel(
                task_id=f"list-test-{i}",
                task_type=TaskType.DOCUMENT_ANALYSIS,
                status=TaskStatus.PENDING if i % 2 == 0 else TaskStatus.COMPLETED,
                priority=TaskPriority.NORMAL,
                execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
                created_at=datetime.utcnow(),
                input_data={"index": i}
            )
            await task_storage.create_task(task)
            tasks.append(task)
        
        # 获取任务列表
        request = TaskListRequest(limit=10)
        result = await task_storage.list_tasks(request)
        
        assert len(result.tasks) == 5
        assert result.total == 5
        assert result.limit == 10
        assert result.offset == 0
    
    async def test_list_tasks_with_filters(self, task_storage):
        """测试带过滤条件的任务列表"""
        # 创建不同类型的任务
        tasks_data = [
            (TaskType.DOCUMENT_ANALYSIS, TaskStatus.COMPLETED, TaskPriority.HIGH),
            (TaskType.TEST_GENERATION, TaskStatus.PENDING, TaskPriority.NORMAL),
            (TaskType.DOCUMENT_ANALYSIS, TaskStatus.FAILED, TaskPriority.HIGH),
            (TaskType.TEST_EXECUTION, TaskStatus.COMPLETED, TaskPriority.LOW),
        ]
        
        for i, (task_type, status, priority) in enumerate(tasks_data):
            task = TaskModel(
                task_id=f"filter-test-{i}",
                task_type=task_type,
                status=status,
                priority=priority,
                execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
                created_at=datetime.utcnow(),
                input_data={"index": i}
            )
            await task_storage.create_task(task)
        
        # 按任务类型过滤
        request = TaskListRequest(task_type=TaskType.DOCUMENT_ANALYSIS)
        result = await task_storage.list_tasks(request)
        assert len(result.tasks) == 2
        
        # 按状态过滤
        request = TaskListRequest(status=TaskStatus.COMPLETED)
        result = await task_storage.list_tasks(request)
        assert len(result.tasks) == 2
        
        # 按优先级过滤
        request = TaskListRequest(priority=TaskPriority.HIGH)
        result = await task_storage.list_tasks(request)
        assert len(result.tasks) == 2
    
    async def test_list_tasks_pagination(self, task_storage):
        """测试任务列表分页"""
        # 创建10个任务
        for i in range(10):
            task = TaskModel(
                task_id=f"page-test-{i:02d}",
                task_type=TaskType.DOCUMENT_ANALYSIS,
                status=TaskStatus.PENDING,
                priority=TaskPriority.NORMAL,
                execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
                created_at=datetime.utcnow(),
                input_data={"index": i}
            )
            await task_storage.create_task(task)
        
        # 第一页
        request = TaskListRequest(limit=3, offset=0)
        result = await task_storage.list_tasks(request)
        assert len(result.tasks) == 3
        assert result.total == 10
        
        # 第二页
        request = TaskListRequest(limit=3, offset=3)
        result = await task_storage.list_tasks(request)
        assert len(result.tasks) == 3
        
        # 最后一页
        request = TaskListRequest(limit=3, offset=9)
        result = await task_storage.list_tasks(request)
        assert len(result.tasks) == 1
    
    async def test_get_pending_tasks(self, task_storage):
        """测试获取待处理任务"""
        # 创建不同状态的任务
        statuses = [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.PENDING]
        
        for i, status in enumerate(statuses):
            task = TaskModel(
                task_id=f"pending-test-{i}",
                task_type=TaskType.DOCUMENT_ANALYSIS,
                status=status,
                priority=TaskPriority.NORMAL,
                execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
                created_at=datetime.utcnow(),
                input_data={"index": i}
            )
            await task_storage.create_task(task)
        
        # 获取待处理任务
        pending_tasks = await task_storage.get_pending_tasks(limit=10)
        
        assert len(pending_tasks) == 2
        for task in pending_tasks:
            assert task.status == TaskStatus.PENDING
    
    async def test_get_timeout_tasks(self, task_storage):
        """测试获取超时任务"""
        # 创建任务，其中一些已超时
        now = datetime.utcnow()
        old_time = now - timedelta(hours=2)
        
        # 正常任务
        normal_task = TaskModel(
            task_id="normal-task",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.RUNNING,
            priority=TaskPriority.NORMAL,
            execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
            created_at=now,
            started_at=now,
            input_data={}
        )
        await task_storage.create_task(normal_task)
        
        # 超时任务
        timeout_task = TaskModel(
            task_id="timeout-task",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.RUNNING,
            priority=TaskPriority.NORMAL,
            execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
            created_at=old_time,
            started_at=old_time,
            input_data={}
        )
        await task_storage.create_task(timeout_task)
        
        # 获取超时任务（1小时前开始的任务）
        timeout_threshold = now - timedelta(hours=1)
        timeout_tasks = await task_storage.get_timeout_tasks(timeout_threshold)
        
        assert len(timeout_tasks) == 1
        assert timeout_tasks[0].task_id == "timeout-task"
    
    async def test_delete_task(self, task_storage, sample_task_model):
        """测试删除任务"""
        # 创建任务
        await task_storage.create_task(sample_task_model)
        
        # 删除任务
        success = await task_storage.delete_task(sample_task_model.task_id)
        assert success is True
        
        # 验证删除
        deleted_task = await task_storage.get_task(sample_task_model.task_id)
        assert deleted_task is None
    
    async def test_delete_nonexistent_task(self, task_storage):
        """测试删除不存在的任务"""
        success = await task_storage.delete_task("nonexistent-task")
        assert success is False
    
    async def test_delete_old_tasks(self, task_storage):
        """测试删除旧任务"""
        now = datetime.utcnow()
        old_time = now - timedelta(days=8)
        
        # 创建新任务
        new_task = TaskModel(
            task_id="new-task",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.NORMAL,
            execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
            created_at=now,
            input_data={}
        )
        await task_storage.create_task(new_task)
        
        # 创建旧任务
        old_task = TaskModel(
            task_id="old-task",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.NORMAL,
            execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
            created_at=old_time,
            input_data={}
        )
        await task_storage.create_task(old_task)
        
        # 删除7天前的任务
        cutoff_time = now - timedelta(days=7)
        deleted_count = await task_storage.delete_old_tasks(
            cutoff_time,
            [TaskStatus.COMPLETED]
        )
        
        assert deleted_count == 1
        
        # 验证新任务仍存在
        remaining_task = await task_storage.get_task("new-task")
        assert remaining_task is not None
        
        # 验证旧任务已删除
        deleted_task = await task_storage.get_task("old-task")
        assert deleted_task is None
