"""
异步任务系统数据模型

定义任务相关的数据结构和枚举类型。
"""

import uuid
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)

# SQLAlchemy基类
Base = declarative_base()


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    RETRYING = "retrying"    # 重试中
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"      # 执行超时


class TaskType(str, Enum):
    """任务类型枚举"""
    DOCUMENT_ANALYSIS = "document_analysis"
    TEST_GENERATION = "test_generation"
    TEST_EXECUTION = "test_execution"
    REPORT_GENERATION = "report_generation"


class TaskPriority(int, Enum):
    """任务优先级枚举"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    URGENT = 20


class TaskExecutionMode(str, Enum):
    """任务执行模式"""
    CPU_INTENSIVE = "cpu_intensive"    # CPU密集型，使用进程池
    IO_INTENSIVE = "io_intensive"      # I/O密集型，使用线程池
    ASYNC_COROUTINE = "async_coroutine"  # 异步协程


# SQLAlchemy数据库模型
class TaskRecord(Base):
    """任务数据库记录"""
    __tablename__ = "tasks"
    
    # 基础字段
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default=TaskStatus.PENDING, index=True)
    priority = Column(Integer, nullable=False, default=TaskPriority.NORMAL)
    execution_mode = Column(String, nullable=False, default=TaskExecutionMode.ASYNC_COROUTINE)
    
    # 时间字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # 数据字段 (JSON格式，PostgreSQL原生支持，SQLite存储为TEXT)
    input_data = Column(JSON, nullable=False)
    result_data = Column(JSON, nullable=True)
    error_info = Column(JSON, nullable=True)
    
    # 执行信息
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    timeout_seconds = Column(Integer, nullable=False, default=300)
    
    # 元数据
    metadata_info = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<TaskRecord(id={self.id}, type={self.task_type}, status={self.status})>"


# Pydantic模型用于API和业务逻辑
class TaskModel(BaseModel):
    """任务业务模型"""
    task_id: str = Field(description="任务唯一标识")
    task_type: TaskType = Field(description="任务类型")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="任务优先级")
    execution_mode: TaskExecutionMode = Field(default=TaskExecutionMode.ASYNC_COROUTINE, description="执行模式")
    
    # 时间信息
    created_at: datetime = Field(description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    
    # 任务数据
    input_data: Dict[str, Any] = Field(description="输入数据")
    result_data: Optional[Dict[str, Any]] = Field(default=None, description="结果数据")
    error_info: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")
    
    # 执行信息
    retry_count: int = Field(default=0, description="重试次数")
    max_retries: int = Field(default=3, description="最大重试次数")
    timeout_seconds: int = Field(default=300, description="超时时间(秒)")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_record(cls, record: TaskRecord) -> "TaskModel":
        """从数据库记录创建业务模型"""
        return cls(
            task_id=record.id,
            task_type=TaskType(record.task_type),
            status=TaskStatus(record.status),
            priority=TaskPriority(record.priority),
            execution_mode=TaskExecutionMode(record.execution_mode),
            created_at=record.created_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            input_data=record.input_data or {},
            result_data=record.result_data,
            error_info=record.error_info,
            retry_count=record.retry_count or 0,
            max_retries=record.max_retries or 3,
            timeout_seconds=record.timeout_seconds or 300,
            metadata=record.metadata_info or {}
        )
    
    def to_record(self) -> TaskRecord:
        """转换为数据库记录"""
        return TaskRecord(
            id=self.task_id,
            task_type=self.task_type.value if hasattr(self.task_type, 'value') else self.task_type,
            status=self.status.value if hasattr(self.status, 'value') else self.status,
            priority=self.priority.value if hasattr(self.priority, 'value') else self.priority,
            execution_mode=self.execution_mode.value if hasattr(self.execution_mode, 'value') else self.execution_mode,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            input_data=self.input_data,
            result_data=self.result_data,
            error_info=self.error_info,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            metadata_info=self.metadata
        )


class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""
    task_type: TaskType = Field(description="任务类型")
    input_data: Dict[str, Any] = Field(description="输入数据")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="任务优先级")
    execution_mode: TaskExecutionMode = Field(default=TaskExecutionMode.ASYNC_COROUTINE, description="执行模式")
    timeout_seconds: int = Field(default=300, description="超时时间(秒)")
    max_retries: int = Field(default=3, description="最大重试次数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class TaskUpdateRequest(BaseModel):
    """更新任务请求模型"""
    status: Optional[TaskStatus] = Field(default=None, description="任务状态")
    result_data: Optional[Dict[str, Any]] = Field(default=None, description="结果数据")
    error_info: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class TaskListRequest(BaseModel):
    """任务列表查询请求"""
    task_type: Optional[TaskType] = Field(default=None, description="任务类型过滤")
    status: Optional[TaskStatus] = Field(default=None, description="状态过滤")
    priority: Optional[TaskPriority] = Field(default=None, description="优先级过滤")
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")
    order_by: str = Field(default="created_at", description="排序字段")
    order_desc: bool = Field(default=True, description="是否降序")


class TaskStatistics(BaseModel):
    """任务统计信息"""
    total_tasks: int = Field(description="总任务数")
    by_status: Dict[str, int] = Field(description="按状态统计")
    by_type: Dict[str, int] = Field(description="按类型统计")
    by_priority: Dict[str, int] = Field(description="按优先级统计")
    avg_execution_time: Optional[float] = Field(description="平均执行时间(秒)")
    success_rate: Optional[float] = Field(description="成功率(%)")
    
    # 时间范围统计
    last_hour_tasks: int = Field(description="最近1小时任务数")
    last_day_tasks: int = Field(description="最近24小时任务数")
    last_week_tasks: int = Field(description="最近7天任务数")


class TaskExecutionContext(BaseModel):
    """任务执行上下文"""
    task_id: str = Field(description="任务ID")
    task_type: TaskType = Field(description="任务类型")
    execution_mode: TaskExecutionMode = Field(description="执行模式")
    timeout_seconds: int = Field(description="超时时间")
    retry_count: int = Field(description="当前重试次数")
    max_retries: int = Field(description="最大重试次数")
    input_data: Dict[str, Any] = Field(description="输入数据")
    metadata: Dict[str, Any] = Field(description="元数据")
    
    # 执行环境信息
    worker_id: Optional[str] = Field(default=None, description="工作进程ID")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    
    class Config:
        use_enum_values = True


# 任务处理器类型定义
from typing import Callable, Awaitable, Union

TaskHandler = Union[
    Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],  # 异步处理器
    Callable[[Dict[str, Any]], Dict[str, Any]]              # 同步处理器
]


# 任务事件类型
class TaskEvent(BaseModel):
    """任务事件"""
    event_type: str = Field(description="事件类型")
    task_id: str = Field(description="任务ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="事件时间")
    data: Dict[str, Any] = Field(default_factory=dict, description="事件数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 常用的任务事件类型
class TaskEventType:
    """任务事件类型常量"""
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_CANCELLED = "task_cancelled"
    TASK_TIMEOUT = "task_timeout"


logger.info("✅ 任务数据模型初始化完成")
