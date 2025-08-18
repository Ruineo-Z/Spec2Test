"""
任务数据模型测试
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.core.tasks.models import (
    TaskStatus,
    TaskType,
    TaskPriority,
    TaskExecutionMode,
    TaskModel,
    TaskRecord,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskListRequest,
    TaskStatistics,
    TaskExecutionContext,
    TaskEvent,
    TaskEventType
)


class TestTaskEnums:
    """测试任务枚举类型"""
    
    def test_task_status_values(self):
        """测试任务状态枚举值"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.RETRYING == "retrying"
        assert TaskStatus.CANCELLED == "cancelled"
        assert TaskStatus.TIMEOUT == "timeout"
    
    def test_task_type_values(self):
        """测试任务类型枚举值"""
        assert TaskType.DOCUMENT_ANALYSIS == "document_analysis"
        assert TaskType.TEST_GENERATION == "test_generation"
        assert TaskType.TEST_EXECUTION == "test_execution"
        assert TaskType.REPORT_GENERATION == "report_generation"
    
    def test_task_priority_values(self):
        """测试任务优先级枚举值"""
        assert TaskPriority.LOW == 1
        assert TaskPriority.NORMAL == 5
        assert TaskPriority.HIGH == 10
        assert TaskPriority.URGENT == 20
    
    def test_execution_mode_values(self):
        """测试执行模式枚举值"""
        assert TaskExecutionMode.CPU_INTENSIVE == "cpu_intensive"
        assert TaskExecutionMode.IO_INTENSIVE == "io_intensive"
        assert TaskExecutionMode.ASYNC_COROUTINE == "async_coroutine"


class TestTaskModel:
    """测试任务模型"""
    
    def test_task_model_creation(self):
        """测试任务模型创建"""
        now = datetime.utcnow()
        
        task = TaskModel(
            task_id="test-123",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            execution_mode=TaskExecutionMode.ASYNC_COROUTINE,
            created_at=now,
            input_data={"test": "data"},
            timeout_seconds=300,
            max_retries=3,
            metadata={"key": "value"}
        )
        
        assert task.task_id == "test-123"
        assert task.task_type == TaskType.DOCUMENT_ANALYSIS
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.execution_mode == TaskExecutionMode.ASYNC_COROUTINE
        assert task.created_at == now
        assert task.input_data == {"test": "data"}
        assert task.timeout_seconds == 300
        assert task.max_retries == 3
        assert task.metadata == {"key": "value"}
    
    def test_task_model_defaults(self):
        """测试任务模型默认值"""
        task = TaskModel(
            task_id="test-456",
            task_type=TaskType.TEST_GENERATION,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL
        assert task.execution_mode == TaskExecutionMode.ASYNC_COROUTINE
        assert task.started_at is None
        assert task.completed_at is None
        assert task.result_data is None
        assert task.error_info is None
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.timeout_seconds == 300
        assert task.metadata == {}
    
    def test_task_model_to_record_conversion(self):
        """测试任务模型转换为数据库记录"""
        now = datetime.utcnow()
        
        task = TaskModel(
            task_id="test-789",
            task_type=TaskType.REPORT_GENERATION,
            status=TaskStatus.RUNNING,
            priority=TaskPriority.LOW,
            execution_mode=TaskExecutionMode.CPU_INTENSIVE,
            created_at=now,
            started_at=now,
            input_data={"report_type": "summary"},
            timeout_seconds=600,
            max_retries=5,
            metadata={"version": "1.0"}
        )
        
        record = task.to_record()
        
        assert isinstance(record, TaskRecord)
        assert record.id == "test-789"
        assert record.task_type == "report_generation"
        assert record.status == "running"
        assert record.priority == 1
        assert record.execution_mode == "cpu_intensive"
        assert record.created_at == now
        assert record.started_at == now
        assert record.input_data == {"report_type": "summary"}
        assert record.timeout_seconds == 600
        assert record.max_retries == 5
        assert record.metadata_info == {"version": "1.0"}
    
    def test_task_model_from_record_conversion(self):
        """测试从数据库记录创建任务模型"""
        now = datetime.utcnow()
        
        record = TaskRecord(
            id="test-abc",
            task_type="test_execution",
            status="completed",
            priority=10,
            execution_mode="io_intensive",
            created_at=now,
            completed_at=now,
            input_data={"url": "http://example.com"},
            result_data={"status": "success"},
            timeout_seconds=120,
            max_retries=2,
            metadata_info={"env": "test"}
        )
        
        task = TaskModel.from_record(record)
        
        assert task.task_id == "test-abc"
        assert task.task_type == TaskType.TEST_EXECUTION
        assert task.status == TaskStatus.COMPLETED
        assert task.priority == TaskPriority.HIGH
        assert task.execution_mode == TaskExecutionMode.IO_INTENSIVE
        assert task.created_at == now
        assert task.completed_at == now
        assert task.input_data == {"url": "http://example.com"}
        assert task.result_data == {"status": "success"}
        assert task.timeout_seconds == 120
        assert task.max_retries == 2
        assert task.metadata == {"env": "test"}


class TestTaskCreateRequest:
    """测试任务创建请求"""
    
    def test_create_request_validation(self):
        """测试创建请求验证"""
        request = TaskCreateRequest(
            task_type=TaskType.DOCUMENT_ANALYSIS,
            input_data={"document": "test.json"},
            priority=TaskPriority.URGENT,
            execution_mode=TaskExecutionMode.CPU_INTENSIVE,
            timeout_seconds=180,
            max_retries=1,
            metadata={"source": "api"}
        )
        
        assert request.task_type == TaskType.DOCUMENT_ANALYSIS
        assert request.input_data == {"document": "test.json"}
        assert request.priority == TaskPriority.URGENT
        assert request.execution_mode == TaskExecutionMode.CPU_INTENSIVE
        assert request.timeout_seconds == 180
        assert request.max_retries == 1
        assert request.metadata == {"source": "api"}
    
    def test_create_request_defaults(self):
        """测试创建请求默认值"""
        request = TaskCreateRequest(
            task_type=TaskType.TEST_GENERATION,
            input_data={"spec": "openapi.yaml"}
        )
        
        assert request.priority == TaskPriority.NORMAL
        assert request.execution_mode == TaskExecutionMode.ASYNC_COROUTINE
        assert request.timeout_seconds == 300
        assert request.max_retries == 3
        assert request.metadata == {}


class TestTaskListRequest:
    """测试任务列表请求"""
    
    def test_list_request_defaults(self):
        """测试列表请求默认值"""
        request = TaskListRequest()
        
        assert request.task_type is None
        assert request.status is None
        assert request.priority is None
        assert request.limit == 100
        assert request.offset == 0
        assert request.order_by == "created_at"
        assert request.order_desc is True
    
    def test_list_request_validation(self):
        """测试列表请求验证"""
        request = TaskListRequest(
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.HIGH,
            limit=50,
            offset=10,
            order_by="priority",
            order_desc=False
        )
        
        assert request.task_type == TaskType.DOCUMENT_ANALYSIS
        assert request.status == TaskStatus.COMPLETED
        assert request.priority == TaskPriority.HIGH
        assert request.limit == 50
        assert request.offset == 10
        assert request.order_by == "priority"
        assert request.order_desc is False
    
    def test_list_request_limit_validation(self):
        """测试列表请求限制验证"""
        # 有效限制
        request = TaskListRequest(limit=500)
        assert request.limit == 500
        
        # 超出最大限制
        with pytest.raises(ValidationError):
            TaskListRequest(limit=2000)
        
        # 小于最小限制
        with pytest.raises(ValidationError):
            TaskListRequest(limit=0)


class TestTaskExecutionContext:
    """测试任务执行上下文"""
    
    def test_execution_context_creation(self):
        """测试执行上下文创建"""
        context = TaskExecutionContext(
            task_id="ctx-test-123",
            task_type=TaskType.TEST_EXECUTION,
            execution_mode=TaskExecutionMode.IO_INTENSIVE,
            timeout_seconds=240,
            retry_count=1,
            max_retries=3,
            input_data={"test": "context"},
            metadata={"context": True}
        )
        
        assert context.task_id == "ctx-test-123"
        assert context.task_type == TaskType.TEST_EXECUTION
        assert context.execution_mode == TaskExecutionMode.IO_INTENSIVE
        assert context.timeout_seconds == 240
        assert context.retry_count == 1
        assert context.max_retries == 3
        assert context.input_data == {"test": "context"}
        assert context.metadata == {"context": True}


class TestTaskEvent:
    """测试任务事件"""
    
    def test_task_event_creation(self):
        """测试任务事件创建"""
        now = datetime.utcnow()
        
        event = TaskEvent(
            event_type=TaskEventType.TASK_STARTED,
            task_id="event-test-123",
            timestamp=now,
            data={"status": "started", "worker": "worker-1"}
        )
        
        assert event.event_type == TaskEventType.TASK_STARTED
        assert event.task_id == "event-test-123"
        assert event.timestamp == now
        assert event.data == {"status": "started", "worker": "worker-1"}
    
    def test_task_event_defaults(self):
        """测试任务事件默认值"""
        event = TaskEvent(
            event_type=TaskEventType.TASK_COMPLETED,
            task_id="event-test-456"
        )
        
        assert event.event_type == TaskEventType.TASK_COMPLETED
        assert event.task_id == "event-test-456"
        assert isinstance(event.timestamp, datetime)
        assert event.data == {}


class TestTaskStatistics:
    """测试任务统计"""
    
    def test_task_statistics_creation(self):
        """测试任务统计创建"""
        stats = TaskStatistics(
            total_tasks=100,
            by_status={"completed": 80, "failed": 15, "running": 5},
            by_type={"document_analysis": 60, "test_execution": 40},
            by_priority={"normal": 70, "high": 30},
            avg_execution_time=2.5,
            success_rate=80.0,
            last_hour_tasks=10,
            last_day_tasks=100,
            last_week_tasks=500
        )
        
        assert stats.total_tasks == 100
        assert stats.by_status == {"completed": 80, "failed": 15, "running": 5}
        assert stats.by_type == {"document_analysis": 60, "test_execution": 40}
        assert stats.by_priority == {"normal": 70, "high": 30}
        assert stats.avg_execution_time == 2.5
        assert stats.success_rate == 80.0
        assert stats.last_hour_tasks == 10
        assert stats.last_day_tasks == 100
        assert stats.last_week_tasks == 500
