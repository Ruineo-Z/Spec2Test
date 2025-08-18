"""
智能重试机制

提供任务重试的策略和实现。
"""

import asyncio
import random
from typing import Type, List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

from .models import TaskModel, TaskStatus, TaskType
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class RetryStrategy(str, Enum):
    """重试策略枚举"""
    FIXED_DELAY = "fixed_delay"          # 固定延迟
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    LINEAR_BACKOFF = "linear_backoff"    # 线性退避
    CUSTOM = "custom"                    # 自定义策略


class RetryCondition(str, Enum):
    """重试条件枚举"""
    ALWAYS = "always"                    # 总是重试
    ON_FAILURE = "on_failure"           # 仅失败时重试
    ON_TIMEOUT = "on_timeout"           # 仅超时时重试
    ON_SPECIFIC_ERROR = "on_specific_error"  # 特定错误时重试
    NEVER = "never"                     # 从不重试


class RetryConfig:
    """重试配置"""
    
    def __init__(self,
                 max_retries: int = 3,
                 strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
                 base_delay: float = 1.0,
                 max_delay: float = 300.0,
                 jitter: bool = True,
                 condition: RetryCondition = RetryCondition.ON_FAILURE,
                 retryable_exceptions: Optional[List[Type[Exception]]] = None,
                 custom_strategy: Optional[Callable[[int], float]] = None):
        """初始化重试配置
        
        Args:
            max_retries: 最大重试次数
            strategy: 重试策略
            base_delay: 基础延迟时间(秒)
            max_delay: 最大延迟时间(秒)
            jitter: 是否添加随机抖动
            condition: 重试条件
            retryable_exceptions: 可重试的异常类型列表
            custom_strategy: 自定义策略函数
        """
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.condition = condition
        self.retryable_exceptions = retryable_exceptions or self._default_retryable_exceptions()
        self.custom_strategy = custom_strategy
    
    def _default_retryable_exceptions(self) -> List[Type[Exception]]:
        """默认可重试的异常类型"""
        return [
            ConnectionError,
            TimeoutError,
            OSError,
            # 可以添加更多可重试的异常类型
        ]


class RetryManager:
    """重试管理器"""
    
    def __init__(self):
        """初始化重试管理器"""
        # 任务类型特定的重试配置
        self.task_configs: Dict[TaskType, RetryConfig] = {}
        
        # 默认重试配置
        self.default_config = RetryConfig()
        
        # 重试历史记录
        self.retry_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("🔄 重试管理器初始化完成")
    
    def set_task_config(self, task_type: TaskType, config: RetryConfig):
        """设置任务类型的重试配置
        
        Args:
            task_type: 任务类型
            config: 重试配置
        """
        self.task_configs[task_type] = config
        logger.info(f"📝 设置重试配置: {task_type} (最大重试: {config.max_retries})")
    
    def get_task_config(self, task_type: TaskType) -> RetryConfig:
        """获取任务类型的重试配置
        
        Args:
            task_type: 任务类型
            
        Returns:
            RetryConfig: 重试配置
        """
        return self.task_configs.get(task_type, self.default_config)
    
    def should_retry(self, task: TaskModel, exception: Optional[Exception] = None) -> bool:
        """判断任务是否应该重试
        
        Args:
            task: 任务模型
            exception: 异常对象
            
        Returns:
            bool: 是否应该重试
        """
        config = self.get_task_config(task.task_type)
        
        # 检查重试次数
        if task.retry_count >= config.max_retries:
            logger.info(f"🚫 重试次数已达上限: {task.task_id} ({task.retry_count}/{config.max_retries})")
            return False
        
        # 检查重试条件
        if config.condition == RetryCondition.NEVER:
            return False
        
        if config.condition == RetryCondition.ALWAYS:
            return True
        
        if config.condition == RetryCondition.ON_FAILURE and task.status == TaskStatus.FAILED:
            return self._check_exception_retryable(exception, config)
        
        if config.condition == RetryCondition.ON_TIMEOUT and task.status == TaskStatus.TIMEOUT:
            return True
        
        if config.condition == RetryCondition.ON_SPECIFIC_ERROR:
            return self._check_exception_retryable(exception, config)
        
        return False
    
    def _check_exception_retryable(self, exception: Optional[Exception], config: RetryConfig) -> bool:
        """检查异常是否可重试
        
        Args:
            exception: 异常对象
            config: 重试配置
            
        Returns:
            bool: 是否可重试
        """
        if not exception:
            return True  # 没有异常信息时默认可重试
        
        return any(isinstance(exception, exc_type) for exc_type in config.retryable_exceptions)
    
    def calculate_delay(self, task: TaskModel, retry_count: Optional[int] = None) -> float:
        """计算重试延迟时间
        
        Args:
            task: 任务模型
            retry_count: 重试次数，None时使用任务的重试次数
            
        Returns:
            float: 延迟时间(秒)
        """
        config = self.get_task_config(task.task_type)
        count = retry_count if retry_count is not None else task.retry_count
        
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (2 ** count)
        
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (count + 1)
        
        elif config.strategy == RetryStrategy.CUSTOM and config.custom_strategy:
            delay = config.custom_strategy(count)
        
        else:
            # 默认使用指数退避
            delay = config.base_delay * (2 ** count)
        
        # 限制最大延迟
        delay = min(delay, config.max_delay)
        
        # 添加随机抖动
        if config.jitter:
            jitter_amount = random.uniform(0.1, 0.3) * delay
            delay += jitter_amount
        
        return delay
    
    async def wait_for_retry(self, task: TaskModel, retry_count: Optional[int] = None):
        """等待重试
        
        Args:
            task: 任务模型
            retry_count: 重试次数
        """
        delay = self.calculate_delay(task, retry_count)
        
        logger.info(f"⏳ 等待重试: {task.task_id} (延迟 {delay:.2f} 秒)")
        
        # 记录重试历史
        self._record_retry_attempt(task.task_id, retry_count or task.retry_count, delay)
        
        await asyncio.sleep(delay)
    
    def _record_retry_attempt(self, task_id: str, retry_count: int, delay: float):
        """记录重试尝试
        
        Args:
            task_id: 任务ID
            retry_count: 重试次数
            delay: 延迟时间
        """
        if task_id not in self.retry_history:
            self.retry_history[task_id] = []
        
        self.retry_history[task_id].append({
            "retry_count": retry_count,
            "delay": delay,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 限制历史记录数量
        if len(self.retry_history[task_id]) > 10:
            self.retry_history[task_id] = self.retry_history[task_id][-10:]
    
    def get_retry_history(self, task_id: str) -> List[Dict[str, Any]]:
        """获取任务的重试历史
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[Dict[str, Any]]: 重试历史记录
        """
        return self.retry_history.get(task_id, [])
    
    def clear_retry_history(self, task_id: str):
        """清理任务的重试历史
        
        Args:
            task_id: 任务ID
        """
        if task_id in self.retry_history:
            del self.retry_history[task_id]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取重试统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_tasks_with_retries = len(self.retry_history)
        total_retry_attempts = sum(len(history) for history in self.retry_history.values())
        
        # 按任务类型统计重试配置
        config_stats = {}
        for task_type, config in self.task_configs.items():
            config_stats[task_type.value] = {
                "max_retries": config.max_retries,
                "strategy": config.strategy.value,
                "base_delay": config.base_delay,
                "max_delay": config.max_delay
            }
        
        return {
            "total_tasks_with_retries": total_tasks_with_retries,
            "total_retry_attempts": total_retry_attempts,
            "avg_retries_per_task": total_retry_attempts / total_tasks_with_retries if total_tasks_with_retries > 0 else 0,
            "task_type_configs": config_stats,
            "default_config": {
                "max_retries": self.default_config.max_retries,
                "strategy": self.default_config.strategy.value,
                "base_delay": self.default_config.base_delay,
                "max_delay": self.default_config.max_delay
            }
        }


# 预定义的重试配置
class PredefinedRetryConfigs:
    """预定义的重试配置"""
    
    # 快速重试（适用于轻量级任务）
    FAST_RETRY = RetryConfig(
        max_retries=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=0.5,
        max_delay=30.0,
        jitter=True
    )
    
    # 标准重试（适用于一般任务）
    STANDARD_RETRY = RetryConfig(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=1.0,
        max_delay=60.0,
        jitter=True
    )
    
    # 慢重试（适用于重量级任务）
    SLOW_RETRY = RetryConfig(
        max_retries=2,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=5.0,
        max_delay=300.0,
        jitter=True
    )
    
    # 网络重试（适用于网络相关任务）
    NETWORK_RETRY = RetryConfig(
        max_retries=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=2.0,
        max_delay=120.0,
        jitter=True,
        condition=RetryCondition.ON_SPECIFIC_ERROR,
        retryable_exceptions=[ConnectionError, TimeoutError, OSError]
    )
    
    # 无重试
    NO_RETRY = RetryConfig(
        max_retries=0,
        condition=RetryCondition.NEVER
    )


# 全局重试管理器实例
retry_manager = RetryManager()

# 设置默认任务类型配置
retry_manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, PredefinedRetryConfigs.STANDARD_RETRY)
retry_manager.set_task_config(TaskType.TEST_GENERATION, PredefinedRetryConfigs.STANDARD_RETRY)
retry_manager.set_task_config(TaskType.TEST_EXECUTION, PredefinedRetryConfigs.NETWORK_RETRY)
retry_manager.set_task_config(TaskType.REPORT_GENERATION, PredefinedRetryConfigs.SLOW_RETRY)


logger.info("✅ 智能重试机制模块初始化完成")
