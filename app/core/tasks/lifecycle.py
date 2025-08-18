"""
任务状态生命周期管理

管理任务状态的转换规则和生命周期事件。
"""

from typing import Dict, Set, List, Optional, Callable, Any
from datetime import datetime
from enum import Enum

from .models import TaskStatus, TaskType, TaskEvent, TaskEventType, TaskModel
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class TaskLifecycleManager:
    """任务生命周期管理器"""
    
    def __init__(self):
        """初始化生命周期管理器"""
        self.state_transitions = self._build_state_transitions()
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        logger.info("🔄 任务生命周期管理器初始化完成")
    
    def _build_state_transitions(self) -> Dict[TaskStatus, Set[TaskStatus]]:
        """构建状态转换规则"""
        return {
            TaskStatus.PENDING: {
                TaskStatus.RUNNING,
                TaskStatus.CANCELLED
            },
            TaskStatus.RUNNING: {
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.TIMEOUT,
                TaskStatus.CANCELLED,
                TaskStatus.RETRYING
            },
            TaskStatus.RETRYING: {
                TaskStatus.RUNNING,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED
            },
            TaskStatus.COMPLETED: set(),  # 终态，不能转换
            TaskStatus.FAILED: {
                TaskStatus.RETRYING  # 可以重试
            },
            TaskStatus.TIMEOUT: {
                TaskStatus.RETRYING,  # 可以重试
                TaskStatus.FAILED     # 或标记为失败
            },
            TaskStatus.CANCELLED: set()  # 终态，不能转换
        }
    
    def can_transition(self, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """检查状态转换是否合法
        
        Args:
            from_status: 当前状态
            to_status: 目标状态
            
        Returns:
            bool: 是否可以转换
        """
        allowed_transitions = self.state_transitions.get(from_status, set())
        return to_status in allowed_transitions
    
    def validate_transition(self, from_status: TaskStatus, to_status: TaskStatus) -> None:
        """验证状态转换
        
        Args:
            from_status: 当前状态
            to_status: 目标状态
            
        Raises:
            InvalidTransitionError: 状态转换不合法
        """
        if not self.can_transition(from_status, to_status):
            raise InvalidTransitionError(
                f"Invalid state transition: {from_status} -> {to_status}"
            )
    
    def get_allowed_transitions(self, current_status: TaskStatus) -> Set[TaskStatus]:
        """获取当前状态允许的转换目标
        
        Args:
            current_status: 当前状态
            
        Returns:
            Set[TaskStatus]: 允许的转换目标状态集合
        """
        return self.state_transitions.get(current_status, set()).copy()
    
    def is_terminal_state(self, status: TaskStatus) -> bool:
        """检查是否为终态
        
        Args:
            status: 任务状态
            
        Returns:
            bool: 是否为终态
        """
        return len(self.state_transitions.get(status, set())) == 0
    
    def is_active_state(self, status: TaskStatus) -> bool:
        """检查是否为活跃状态（正在处理中）
        
        Args:
            status: 任务状态
            
        Returns:
            bool: 是否为活跃状态
        """
        return status in {TaskStatus.RUNNING, TaskStatus.RETRYING}
    
    def is_success_state(self, status: TaskStatus) -> bool:
        """检查是否为成功状态
        
        Args:
            status: 任务状态
            
        Returns:
            bool: 是否为成功状态
        """
        return status == TaskStatus.COMPLETED
    
    def is_failure_state(self, status: TaskStatus) -> bool:
        """检查是否为失败状态
        
        Args:
            status: 任务状态
            
        Returns:
            bool: 是否为失败状态
        """
        return status in {TaskStatus.FAILED, TaskStatus.TIMEOUT}
    
    def register_event_handler(self, event_type: str, handler: Callable[[TaskEvent], None]):
        """注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"📝 注册事件处理器: {event_type}")
    
    def unregister_event_handler(self, event_type: str, handler: Callable[[TaskEvent], None]):
        """注销事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                logger.info(f"📝 注销事件处理器: {event_type}")
            except ValueError:
                logger.warning(f"⚠️ 事件处理器不存在: {event_type}")
    
    async def emit_event(self, event: TaskEvent):
        """发送事件
        
        Args:
            event: 任务事件
        """
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"❌ 事件处理器执行失败: {event.event_type} - {e}")
    
    async def transition_task_status(self, 
                                   task: TaskModel,
                                   new_status: TaskStatus,
                                   result_data: Optional[Dict[str, Any]] = None,
                                   error_info: Optional[Dict[str, Any]] = None) -> TaskModel:
        """执行任务状态转换
        
        Args:
            task: 任务模型
            new_status: 新状态
            result_data: 结果数据
            error_info: 错误信息
            
        Returns:
            TaskModel: 更新后的任务模型
            
        Raises:
            InvalidTransitionError: 状态转换不合法
        """
        # 验证状态转换
        self.validate_transition(task.status, new_status)
        
        # 记录旧状态
        old_status = task.status
        
        # 更新任务状态
        task.status = new_status
        
        # 更新时间戳
        now = datetime.utcnow()
        if new_status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = now
        elif new_status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED}:
            if not task.completed_at:
                task.completed_at = now
        
        # 更新数据
        if result_data is not None:
            task.result_data = result_data
        
        if error_info is not None:
            task.error_info = error_info
        
        # 发送状态转换事件
        event_type = self._get_event_type_for_status(new_status)
        if event_type:
            event = TaskEvent(
                event_type=event_type,
                task_id=task.task_id,
                timestamp=now,
                data={
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "task_type": task.task_type.value,
                    "result_data": result_data,
                    "error_info": error_info
                }
            )
            await self.emit_event(event)
        
        logger.info(f"🔄 任务状态转换: {task.task_id} {old_status} -> {new_status}")
        return task
    
    def _get_event_type_for_status(self, status: TaskStatus) -> Optional[str]:
        """根据状态获取对应的事件类型"""
        status_to_event = {
            TaskStatus.RUNNING: TaskEventType.TASK_STARTED,
            TaskStatus.COMPLETED: TaskEventType.TASK_COMPLETED,
            TaskStatus.FAILED: TaskEventType.TASK_FAILED,
            TaskStatus.RETRYING: TaskEventType.TASK_RETRYING,
            TaskStatus.CANCELLED: TaskEventType.TASK_CANCELLED,
            TaskStatus.TIMEOUT: TaskEventType.TASK_TIMEOUT
        }
        return status_to_event.get(status)
    
    def get_task_duration(self, task: TaskModel) -> Optional[float]:
        """获取任务执行时长
        
        Args:
            task: 任务模型
            
        Returns:
            Optional[float]: 执行时长(秒)，未完成返回None
        """
        if not task.started_at:
            return None
        
        end_time = task.completed_at or datetime.utcnow()
        duration = (end_time - task.started_at).total_seconds()
        return duration
    
    def should_retry(self, task: TaskModel) -> bool:
        """判断任务是否应该重试
        
        Args:
            task: 任务模型
            
        Returns:
            bool: 是否应该重试
        """
        # 检查重试次数
        if task.retry_count >= task.max_retries:
            return False
        
        # 检查当前状态是否允许重试
        if task.status not in {TaskStatus.FAILED, TaskStatus.TIMEOUT}:
            return False
        
        return True
    
    def calculate_retry_delay(self, retry_count: int, base_delay: float = 1.0) -> float:
        """计算重试延迟时间（指数退避）
        
        Args:
            retry_count: 重试次数
            base_delay: 基础延迟时间(秒)
            
        Returns:
            float: 延迟时间(秒)
        """
        import random
        
        # 指数退避
        delay = base_delay * (2 ** retry_count)
        
        # 添加随机抖动（避免雷群效应）
        jitter = random.uniform(0.1, 0.3) * delay
        
        # 限制最大延迟时间
        max_delay = 300  # 5分钟
        total_delay = min(delay + jitter, max_delay)
        
        return total_delay


class InvalidTransitionError(Exception):
    """无效状态转换异常"""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.timestamp = datetime.utcnow()


# 全局生命周期管理器实例
task_lifecycle_manager = TaskLifecycleManager()


# 导入asyncio用于事件处理
import asyncio


logger.info("✅ 任务生命周期管理模块初始化完成")
