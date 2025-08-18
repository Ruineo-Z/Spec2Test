"""
任务超时处理

提供任务执行超时的检测和处理机制。
"""

import asyncio
import signal
import threading
from typing import Any, Awaitable, Optional, Dict, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from .models import TaskModel, TaskType, TaskStatus
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class TimeoutConfig:
    """超时配置"""
    
    def __init__(self,
                 default_timeout: int = 300,
                 task_timeouts: Optional[Dict[TaskType, int]] = None,
                 enable_soft_timeout: bool = True,
                 soft_timeout_ratio: float = 0.8,
                 enable_graceful_shutdown: bool = True,
                 shutdown_grace_period: int = 30):
        """初始化超时配置
        
        Args:
            default_timeout: 默认超时时间(秒)
            task_timeouts: 任务类型特定超时时间
            enable_soft_timeout: 是否启用软超时
            soft_timeout_ratio: 软超时比例(0-1)
            enable_graceful_shutdown: 是否启用优雅关闭
            shutdown_grace_period: 关闭宽限期(秒)
        """
        self.default_timeout = default_timeout
        self.task_timeouts = task_timeouts or {}
        self.enable_soft_timeout = enable_soft_timeout
        self.soft_timeout_ratio = soft_timeout_ratio
        self.enable_graceful_shutdown = enable_graceful_shutdown
        self.shutdown_grace_period = shutdown_grace_period


class TimeoutManager:
    """超时管理器"""
    
    def __init__(self, config: Optional[TimeoutConfig] = None):
        """初始化超时管理器
        
        Args:
            config: 超时配置
        """
        self.config = config or TimeoutConfig()
        
        # 运行中的任务跟踪
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        
        # 超时回调
        self.timeout_callbacks: Dict[str, Callable] = {}
        
        # 软超时回调
        self.soft_timeout_callbacks: Dict[str, Callable] = {}
        
        logger.info("⏰ 超时管理器初始化完成")
    
    def get_timeout_for_task(self, task: TaskModel) -> int:
        """获取任务的超时时间
        
        Args:
            task: 任务模型
            
        Returns:
            int: 超时时间(秒)
        """
        # 优先使用任务自身的超时设置
        if task.timeout_seconds > 0:
            return task.timeout_seconds
        
        # 使用任务类型特定的超时设置
        if task.task_type in self.config.task_timeouts:
            return self.config.task_timeouts[task.task_type]
        
        # 使用默认超时设置
        return self.config.default_timeout
    
    async def execute_with_timeout(self, 
                                 coro: Awaitable[Any], 
                                 timeout_seconds: int,
                                 task_id: Optional[str] = None) -> Any:
        """带超时的协程执行
        
        Args:
            coro: 要执行的协程
            timeout_seconds: 超时时间(秒)
            task_id: 任务ID（用于跟踪）
            
        Returns:
            Any: 协程执行结果
            
        Raises:
            asyncio.TimeoutError: 执行超时
        """
        start_time = datetime.utcnow()
        
        # 记录任务开始
        if task_id:
            self.running_tasks[task_id] = {
                "start_time": start_time,
                "timeout_seconds": timeout_seconds,
                "soft_timeout_triggered": False
            }
        
        try:
            # 设置软超时警告
            soft_timeout_task = None
            if self.config.enable_soft_timeout and task_id:
                soft_timeout_seconds = timeout_seconds * self.config.soft_timeout_ratio
                soft_timeout_task = asyncio.create_task(
                    self._soft_timeout_warning(task_id, soft_timeout_seconds)
                )
            
            # 执行协程
            result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            
            # 取消软超时任务
            if soft_timeout_task:
                soft_timeout_task.cancel()
            
            # 记录成功完成
            if task_id:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"✅ 任务在超时前完成: {task_id} (执行时间: {execution_time:.2f}s)")
            
            return result
            
        except asyncio.TimeoutError:
            # 记录超时
            if task_id:
                logger.warning(f"⏰ 任务执行超时: {task_id} (超时时间: {timeout_seconds}s)")
                
                # 触发超时回调
                if task_id in self.timeout_callbacks:
                    try:
                        await self.timeout_callbacks[task_id]()
                    except Exception as e:
                        logger.error(f"❌ 超时回调执行失败: {task_id} - {e}")
            
            raise asyncio.TimeoutError(f"Task timed out after {timeout_seconds} seconds")
            
        finally:
            # 清理任务记录
            if task_id:
                self.running_tasks.pop(task_id, None)
                self.timeout_callbacks.pop(task_id, None)
                self.soft_timeout_callbacks.pop(task_id, None)
    
    async def _soft_timeout_warning(self, task_id: str, soft_timeout_seconds: float):
        """软超时警告
        
        Args:
            task_id: 任务ID
            soft_timeout_seconds: 软超时时间
        """
        try:
            await asyncio.sleep(soft_timeout_seconds)
            
            # 标记软超时已触发
            if task_id in self.running_tasks:
                self.running_tasks[task_id]["soft_timeout_triggered"] = True
                
                logger.warning(f"⚠️ 任务软超时警告: {task_id} (已执行 {soft_timeout_seconds:.1f}s)")
                
                # 触发软超时回调
                if task_id in self.soft_timeout_callbacks:
                    try:
                        await self.soft_timeout_callbacks[task_id]()
                    except Exception as e:
                        logger.error(f"❌ 软超时回调执行失败: {task_id} - {e}")
                        
        except asyncio.CancelledError:
            # 任务在软超时前完成，正常取消
            pass
    
    def register_timeout_callback(self, task_id: str, callback: Callable):
        """注册超时回调
        
        Args:
            task_id: 任务ID
            callback: 超时回调函数
        """
        self.timeout_callbacks[task_id] = callback
    
    def register_soft_timeout_callback(self, task_id: str, callback: Callable):
        """注册软超时回调
        
        Args:
            task_id: 任务ID
            callback: 软超时回调函数
        """
        self.soft_timeout_callbacks[task_id] = callback
    
    def get_running_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取运行中任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务信息
        """
        if task_id not in self.running_tasks:
            return None
        
        task_info = self.running_tasks[task_id].copy()
        
        # 计算已执行时间
        elapsed_time = (datetime.utcnow() - task_info["start_time"]).total_seconds()
        task_info["elapsed_seconds"] = elapsed_time
        
        # 计算剩余时间
        remaining_time = task_info["timeout_seconds"] - elapsed_time
        task_info["remaining_seconds"] = max(0, remaining_time)
        
        # 计算进度百分比（基于时间）
        progress = min(100, (elapsed_time / task_info["timeout_seconds"]) * 100)
        task_info["time_progress_percent"] = progress
        
        return task_info
    
    def get_all_running_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有运行中任务信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 所有任务信息
        """
        result = {}
        for task_id in self.running_tasks:
            result[task_id] = self.get_running_task_info(task_id)
        return result
    
    def is_task_near_timeout(self, task_id: str, threshold_ratio: float = 0.9) -> bool:
        """检查任务是否接近超时
        
        Args:
            task_id: 任务ID
            threshold_ratio: 阈值比例(0-1)
            
        Returns:
            bool: 是否接近超时
        """
        task_info = self.get_running_task_info(task_id)
        if not task_info:
            return False
        
        progress = task_info["time_progress_percent"] / 100
        return progress >= threshold_ratio
    
    async def graceful_shutdown_task(self, task_id: str) -> bool:
        """优雅关闭任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功关闭
        """
        if not self.config.enable_graceful_shutdown:
            return False
        
        if task_id not in self.running_tasks:
            return False
        
        logger.info(f"🛑 开始优雅关闭任务: {task_id}")
        
        try:
            # 发送关闭信号（如果支持）
            # 这里可以扩展为发送特定信号给任务
            
            # 等待宽限期
            await asyncio.sleep(self.config.shutdown_grace_period)
            
            # 检查任务是否已完成
            if task_id not in self.running_tasks:
                logger.info(f"✅ 任务优雅关闭成功: {task_id}")
                return True
            else:
                logger.warning(f"⚠️ 任务未在宽限期内完成: {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 优雅关闭任务失败: {task_id} - {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取超时管理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        running_count = len(self.running_tasks)
        soft_timeout_count = sum(
            1 for info in self.running_tasks.values() 
            if info.get("soft_timeout_triggered", False)
        )
        
        # 计算平均执行时间
        if running_count > 0:
            total_elapsed = sum(
                (datetime.utcnow() - info["start_time"]).total_seconds()
                for info in self.running_tasks.values()
            )
            avg_elapsed = total_elapsed / running_count
        else:
            avg_elapsed = 0
        
        return {
            "running_tasks": running_count,
            "soft_timeout_triggered": soft_timeout_count,
            "avg_elapsed_seconds": avg_elapsed,
            "config": {
                "default_timeout": self.config.default_timeout,
                "enable_soft_timeout": self.config.enable_soft_timeout,
                "soft_timeout_ratio": self.config.soft_timeout_ratio,
                "enable_graceful_shutdown": self.config.enable_graceful_shutdown,
                "shutdown_grace_period": self.config.shutdown_grace_period
            }
        }


# 预定义的超时配置
class PredefinedTimeoutConfigs:
    """预定义的超时配置"""
    
    # 快速任务超时配置
    FAST_TASKS = TimeoutConfig(
        default_timeout=60,  # 1分钟
        task_timeouts={
            TaskType.DOCUMENT_ANALYSIS: 120,  # 2分钟
        },
        enable_soft_timeout=True,
        soft_timeout_ratio=0.8
    )
    
    # 标准任务超时配置
    STANDARD_TASKS = TimeoutConfig(
        default_timeout=300,  # 5分钟
        task_timeouts={
            TaskType.DOCUMENT_ANALYSIS: 180,   # 3分钟
            TaskType.TEST_GENERATION: 300,    # 5分钟
            TaskType.TEST_EXECUTION: 600,     # 10分钟
            TaskType.REPORT_GENERATION: 240   # 4分钟
        },
        enable_soft_timeout=True,
        soft_timeout_ratio=0.8
    )
    
    # 长时间任务超时配置
    LONG_TASKS = TimeoutConfig(
        default_timeout=1800,  # 30分钟
        task_timeouts={
            TaskType.TEST_EXECUTION: 3600,    # 1小时
            TaskType.REPORT_GENERATION: 1200  # 20分钟
        },
        enable_soft_timeout=True,
        soft_timeout_ratio=0.9,
        enable_graceful_shutdown=True,
        shutdown_grace_period=60
    )


# 全局超时管理器实例
timeout_manager = TimeoutManager(PredefinedTimeoutConfigs.STANDARD_TASKS)


logger.info("✅ 任务超时处理模块初始化完成")
