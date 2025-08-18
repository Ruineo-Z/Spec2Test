"""
异步任务系统模块

基于FastAPI BackgroundTasks的增强异步任务系统。
"""

from .models import (
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
    TaskEventType,
    TaskHandler
)

from .storage import (
    TaskStorageInterface,
    StorageException,
    TaskNotFoundError,
    TaskAlreadyExistsError,
    DatabaseConnectionError,
    TransactionError,
    TaskStorageFactory
)

from .database import DatabaseTaskStorage

from .lifecycle import (
    TaskLifecycleManager,
    InvalidTransitionError,
    task_lifecycle_manager
)

from .manager import EnhancedTaskManager

from .retry import (
    RetryManager,
    RetryConfig,
    RetryStrategy,
    RetryCondition,
    PredefinedRetryConfigs,
    retry_manager
)

from .timeout import (
    TimeoutManager,
    TimeoutConfig,
    PredefinedTimeoutConfigs,
    timeout_manager
)

from .context import (
    TaskContext,
    TaskContextManager,
    task_context_manager,
    get_current_task_context,
    get_current_task_id,
    update_task_progress,
    log_task_info,
    log_task_warning,
    log_task_error,
    set_task_step
)

from .executors import (
    OptimizedProcessPoolExecutor,
    OptimizedThreadPoolExecutor,
    ExecutorManager,
    executor_manager
)

from .optimization import (
    PerformanceProfiler,
    MemoryOptimizer,
    CPUOptimizer,
    IOOptimizer,
    PerformanceOptimizer,
    performance_optimizer,
    performance_monitor
)

from .monitor import (
    TaskMonitor,
    TaskMetrics,
    SystemMetrics,
    task_monitor
)

__all__ = [
    # 数据模型
    "TaskStatus",
    "TaskType",
    "TaskPriority",
    "TaskExecutionMode",
    "TaskModel",
    "TaskRecord",
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskListRequest",
    "TaskStatistics",
    "TaskExecutionContext",
    "TaskEvent",
    "TaskEventType",
    "TaskHandler",

    # 存储接口
    "TaskStorageInterface",
    "StorageException",
    "TaskNotFoundError",
    "TaskAlreadyExistsError",
    "DatabaseConnectionError",
    "TransactionError",
    "TaskStorageFactory",

    # 数据库实现
    "DatabaseTaskStorage",

    # 生命周期管理
    "TaskLifecycleManager",
    "InvalidTransitionError",
    "task_lifecycle_manager",

    # 任务管理器
    "EnhancedTaskManager",

    # 重试机制
    "RetryManager",
    "RetryConfig",
    "RetryStrategy",
    "RetryCondition",
    "PredefinedRetryConfigs",
    "retry_manager",

    # 超时处理
    "TimeoutManager",
    "TimeoutConfig",
    "PredefinedTimeoutConfigs",
    "timeout_manager",

    # 上下文管理
    "TaskContext",
    "TaskContextManager",
    "task_context_manager",
    "get_current_task_context",
    "get_current_task_id",
    "update_task_progress",
    "log_task_info",
    "log_task_warning",
    "log_task_error",
    "set_task_step",

    # 执行器
    "OptimizedProcessPoolExecutor",
    "OptimizedThreadPoolExecutor",
    "ExecutorManager",
    "executor_manager",

    # 性能优化
    "PerformanceProfiler",
    "MemoryOptimizer",
    "CPUOptimizer",
    "IOOptimizer",
    "PerformanceOptimizer",
    "performance_optimizer",
    "performance_monitor",

    # 监控统计
    "TaskMonitor",
    "TaskMetrics",
    "SystemMetrics",
    "task_monitor"
]
