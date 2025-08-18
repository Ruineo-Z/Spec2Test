"""
任务执行上下文管理

提供任务执行过程中的上下文信息管理和传递。
"""

import asyncio
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from contextvars import ContextVar
from dataclasses import dataclass, field

from .models import TaskModel, TaskType, TaskStatus, TaskExecutionContext
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


# 上下文变量定义
current_task_context: ContextVar[Optional['TaskContext']] = ContextVar('current_task_context', default=None)
current_task_id: ContextVar[Optional[str]] = ContextVar('current_task_id', default=None)


@dataclass
class TaskContext:
    """任务执行上下文"""
    
    # 基础信息
    task_id: str
    task_type: TaskType
    execution_mode: str
    
    # 时间信息
    created_at: datetime
    started_at: Optional[datetime] = None
    
    # 执行信息
    worker_id: Optional[str] = None
    process_id: Optional[int] = None
    thread_id: Optional[int] = None
    
    # 任务数据
    input_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 执行状态
    current_step: Optional[str] = None
    progress_percent: float = 0.0
    status_message: str = ""
    
    # 资源使用
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    # 日志和调试
    log_entries: List[Dict[str, Any]] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    # 回调函数
    progress_callbacks: List[Callable] = field(default_factory=list)
    status_callbacks: List[Callable] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.started_at:
            self.started_at = datetime.utcnow()
        
        if not self.worker_id:
            self.worker_id = f"worker-{threading.get_ident()}"
        
        if not self.process_id:
            import os
            self.process_id = os.getpid()
        
        if not self.thread_id:
            self.thread_id = threading.get_ident()
    
    def update_progress(self, percent: float, message: str = ""):
        """更新进度
        
        Args:
            percent: 进度百分比(0-100)
            message: 状态消息
        """
        self.progress_percent = max(0, min(100, percent))
        if message:
            self.status_message = message
        
        # 触发进度回调
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(self.task_id, percent, message))
                else:
                    callback(self.task_id, percent, message)
            except Exception as e:
                logger.error(f"❌ 进度回调执行失败: {e}")
    
    def set_current_step(self, step: str):
        """设置当前执行步骤
        
        Args:
            step: 步骤名称
        """
        self.current_step = step
        self.log_info(f"开始执行步骤: {step}")
    
    def log_info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """记录信息日志
        
        Args:
            message: 日志消息
            extra_data: 额外数据
        """
        self._add_log_entry("INFO", message, extra_data)
    
    def log_warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """记录警告日志
        
        Args:
            message: 日志消息
            extra_data: 额外数据
        """
        self._add_log_entry("WARNING", message, extra_data)
    
    def log_error(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """记录错误日志
        
        Args:
            message: 日志消息
            extra_data: 额外数据
        """
        self._add_log_entry("ERROR", message, extra_data)
    
    def _add_log_entry(self, level: str, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """添加日志条目
        
        Args:
            level: 日志级别
            message: 日志消息
            extra_data: 额外数据
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "step": self.current_step,
            "progress": self.progress_percent
        }
        
        if extra_data:
            entry["extra"] = extra_data
        
        self.log_entries.append(entry)
        
        # 限制日志条目数量
        if len(self.log_entries) > 100:
            self.log_entries = self.log_entries[-100:]
        
        # 同时记录到系统日志
        log_message = f"[{self.task_id}] {message}"
        if level == "INFO":
            logger.info(log_message)
        elif level == "WARNING":
            logger.warning(log_message)
        elif level == "ERROR":
            logger.error(log_message)
    
    def add_debug_info(self, key: str, value: Any):
        """添加调试信息
        
        Args:
            key: 键名
            value: 值
        """
        self.debug_info[key] = value
    
    def get_execution_duration(self) -> Optional[float]:
        """获取执行时长
        
        Returns:
            Optional[float]: 执行时长(秒)
        """
        if not self.started_at:
            return None
        
        return (datetime.utcnow() - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 上下文字典
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else self.task_type,
            "execution_mode": self.execution_mode,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "worker_id": self.worker_id,
            "process_id": self.process_id,
            "thread_id": self.thread_id,
            "current_step": self.current_step,
            "progress_percent": self.progress_percent,
            "status_message": self.status_message,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "execution_duration": self.get_execution_duration(),
            "log_entries_count": len(self.log_entries),
            "debug_info": self.debug_info,
            "metadata": self.metadata
        }


class TaskContextManager:
    """任务上下文管理器"""
    
    def __init__(self):
        """初始化上下文管理器"""
        self.contexts: Dict[str, TaskContext] = {}
        self.global_callbacks: List[Callable] = []
        
        logger.info("📋 任务上下文管理器初始化完成")
    
    def create_context(self, task: TaskModel) -> TaskContext:
        """创建任务上下文
        
        Args:
            task: 任务模型
            
        Returns:
            TaskContext: 任务上下文
        """
        context = TaskContext(
            task_id=task.task_id,
            task_type=task.task_type,
            execution_mode=task.execution_mode.value,
            created_at=task.created_at,
            input_data=task.input_data,
            metadata=task.metadata
        )
        
        self.contexts[task.task_id] = context
        logger.info(f"📋 创建任务上下文: {task.task_id}")
        
        return context
    
    def get_context(self, task_id: str) -> Optional[TaskContext]:
        """获取任务上下文
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskContext]: 任务上下文
        """
        return self.contexts.get(task_id)
    
    def remove_context(self, task_id: str):
        """移除任务上下文
        
        Args:
            task_id: 任务ID
        """
        if task_id in self.contexts:
            del self.contexts[task_id]
            logger.info(f"📋 移除任务上下文: {task_id}")
    
    def set_current_context(self, context: TaskContext):
        """设置当前上下文
        
        Args:
            context: 任务上下文
        """
        current_task_context.set(context)
        current_task_id.set(context.task_id)
    
    def clear_current_context(self):
        """清除当前上下文"""
        current_task_context.set(None)
        current_task_id.set(None)
    
    def get_current_context(self) -> Optional[TaskContext]:
        """获取当前上下文
        
        Returns:
            Optional[TaskContext]: 当前任务上下文
        """
        return current_task_context.get()
    
    def get_current_task_id(self) -> Optional[str]:
        """获取当前任务ID
        
        Returns:
            Optional[str]: 当前任务ID
        """
        return current_task_id.get()
    
    def add_global_callback(self, callback: Callable):
        """添加全局回调
        
        Args:
            callback: 回调函数
        """
        self.global_callbacks.append(callback)
    
    def remove_global_callback(self, callback: Callable):
        """移除全局回调
        
        Args:
            callback: 回调函数
        """
        if callback in self.global_callbacks:
            self.global_callbacks.remove(callback)
    
    def get_all_contexts(self) -> Dict[str, TaskContext]:
        """获取所有上下文
        
        Returns:
            Dict[str, TaskContext]: 所有任务上下文
        """
        return self.contexts.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_contexts = len(self.contexts)
        
        # 按任务类型统计
        by_type = {}
        for context in self.contexts.values():
            task_type = context.task_type.value if isinstance(context.task_type, TaskType) else context.task_type
            by_type[task_type] = by_type.get(task_type, 0) + 1
        
        # 计算平均进度
        if total_contexts > 0:
            total_progress = sum(context.progress_percent for context in self.contexts.values())
            avg_progress = total_progress / total_contexts
        else:
            avg_progress = 0
        
        # 计算平均执行时间
        durations = [
            context.get_execution_duration() 
            for context in self.contexts.values() 
            if context.get_execution_duration() is not None
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_contexts": total_contexts,
            "by_task_type": by_type,
            "avg_progress_percent": avg_progress,
            "avg_execution_duration": avg_duration,
            "global_callbacks": len(self.global_callbacks)
        }


# 全局上下文管理器实例
task_context_manager = TaskContextManager()


# 便捷函数
def get_current_task_context() -> Optional[TaskContext]:
    """获取当前任务上下文"""
    return task_context_manager.get_current_context()


def get_current_task_id() -> Optional[str]:
    """获取当前任务ID"""
    return task_context_manager.get_current_task_id()


def update_task_progress(percent: float, message: str = ""):
    """更新当前任务进度"""
    context = get_current_task_context()
    if context:
        context.update_progress(percent, message)


def log_task_info(message: str, extra_data: Optional[Dict[str, Any]] = None):
    """记录当前任务信息日志"""
    context = get_current_task_context()
    if context:
        context.log_info(message, extra_data)


def log_task_warning(message: str, extra_data: Optional[Dict[str, Any]] = None):
    """记录当前任务警告日志"""
    context = get_current_task_context()
    if context:
        context.log_warning(message, extra_data)


def log_task_error(message: str, extra_data: Optional[Dict[str, Any]] = None):
    """记录当前任务错误日志"""
    context = get_current_task_context()
    if context:
        context.log_error(message, extra_data)


def set_task_step(step: str):
    """设置当前任务执行步骤"""
    context = get_current_task_context()
    if context:
        context.set_current_step(step)


logger.info("✅ 任务执行上下文管理模块初始化完成")
