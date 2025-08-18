"""
任务执行器

提供CPU密集型和I/O密集型任务的优化执行器。
"""

import asyncio
import multiprocessing
import threading
import psutil
from typing import Any, Callable, Dict, Optional, List, Union
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, as_completed
from datetime import datetime
from dataclasses import dataclass

from .models import TaskExecutionMode, TaskType
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutorConfig:
    """执行器配置"""
    max_workers: int
    thread_name_prefix: Optional[str] = None
    initializer: Optional[Callable] = None
    initargs: tuple = ()
    
    # 进程池特有配置
    mp_context: Optional[multiprocessing.context.BaseContext] = None
    max_tasks_per_child: Optional[int] = None
    
    # 线程池特有配置
    thread_name_prefix: Optional[str] = None


class OptimizedProcessPoolExecutor:
    """优化的进程池执行器"""
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 mp_context: Optional[multiprocessing.context.BaseContext] = None,
                 initializer: Optional[Callable] = None,
                 initargs: tuple = (),
                 max_tasks_per_child: Optional[int] = None):
        """初始化进程池执行器
        
        Args:
            max_workers: 最大工作进程数
            mp_context: 多进程上下文
            initializer: 初始化函数
            initargs: 初始化参数
            max_tasks_per_child: 每个子进程最大任务数
        """
        # 自动确定最佳工作进程数
        if max_workers is None:
            max_workers = min(32, (multiprocessing.cpu_count() or 1) + 4)
        
        self.max_workers = max_workers
        self.mp_context = mp_context
        self.initializer = initializer
        self.initargs = initargs
        self.max_tasks_per_child = max_tasks_per_child or 100  # 防止内存泄漏
        
        # 创建进程池
        self._executor = ProcessPoolExecutor(
            max_workers=self.max_workers,
            mp_context=self.mp_context,
            initializer=self.initializer,
            initargs=self.initargs,
            max_tasks_per_child=self.max_tasks_per_child
        )
        
        # 统计信息
        self.submitted_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = datetime.utcnow()
        
        logger.info(f"🔧 优化进程池执行器初始化: {self.max_workers} 个工作进程")
    
    async def submit(self, fn: Callable, *args, **kwargs) -> Any:
        """提交任务到进程池
        
        Args:
            fn: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 执行结果
        """
        self.submitted_tasks += 1
        
        try:
            # 在事件循环中运行进程池任务
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, fn, *args, **kwargs)
            
            self.completed_tasks += 1
            return result
            
        except Exception as e:
            self.failed_tasks += 1
            logger.error(f"❌ 进程池任务执行失败: {e}")
            raise
    
    def submit_batch(self, fn: Callable, args_list: List[tuple]) -> List[Future]:
        """批量提交任务
        
        Args:
            fn: 要执行的函数
            args_list: 参数列表
            
        Returns:
            List[Future]: Future对象列表
        """
        futures = []
        for args in args_list:
            future = self._executor.submit(fn, *args)
            futures.append(future)
            self.submitted_tasks += 1
        
        logger.info(f"📤 批量提交进程池任务: {len(futures)} 个")
        return futures
    
    async def submit_batch_async(self, fn: Callable, args_list: List[tuple]) -> List[Any]:
        """异步批量提交任务
        
        Args:
            fn: 要执行的函数
            args_list: 参数列表
            
        Returns:
            List[Any]: 执行结果列表
        """
        futures = self.submit_batch(fn, args_list)
        results = []
        
        for future in as_completed(futures):
            try:
                result = await asyncio.wrap_future(future)
                results.append(result)
                self.completed_tasks += 1
            except Exception as e:
                self.failed_tasks += 1
                logger.error(f"❌ 批量任务执行失败: {e}")
                results.append(None)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "executor_type": "ProcessPool",
            "max_workers": self.max_workers,
            "submitted_tasks": self.submitted_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (self.completed_tasks / self.submitted_tasks * 100) if self.submitted_tasks > 0 else 0,
            "tasks_per_second": self.completed_tasks / uptime if uptime > 0 else 0,
            "uptime_seconds": uptime,
            "max_tasks_per_child": self.max_tasks_per_child
        }
    
    def shutdown(self, wait: bool = True):
        """关闭执行器
        
        Args:
            wait: 是否等待任务完成
        """
        logger.info("🛑 关闭进程池执行器")
        self._executor.shutdown(wait=wait)


class OptimizedThreadPoolExecutor:
    """优化的线程池执行器"""
    
    def __init__(self, 
                 max_workers: Optional[int] = None,
                 thread_name_prefix: str = "TaskThread",
                 initializer: Optional[Callable] = None,
                 initargs: tuple = ()):
        """初始化线程池执行器
        
        Args:
            max_workers: 最大工作线程数
            thread_name_prefix: 线程名称前缀
            initializer: 初始化函数
            initargs: 初始化参数
        """
        # 自动确定最佳工作线程数
        if max_workers is None:
            max_workers = min(32, (multiprocessing.cpu_count() or 1) * 4)
        
        self.max_workers = max_workers
        self.thread_name_prefix = thread_name_prefix
        self.initializer = initializer
        self.initargs = initargs
        
        # 创建线程池
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix=self.thread_name_prefix,
            initializer=self.initializer,
            initargs=self.initargs
        )
        
        # 统计信息
        self.submitted_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = datetime.utcnow()
        
        logger.info(f"🧵 优化线程池执行器初始化: {self.max_workers} 个工作线程")
    
    async def submit(self, fn: Callable, *args, **kwargs) -> Any:
        """提交任务到线程池
        
        Args:
            fn: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 执行结果
        """
        self.submitted_tasks += 1
        
        try:
            # 在事件循环中运行线程池任务
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, fn, *args, **kwargs)
            
            self.completed_tasks += 1
            return result
            
        except Exception as e:
            self.failed_tasks += 1
            logger.error(f"❌ 线程池任务执行失败: {e}")
            raise
    
    def submit_batch(self, fn: Callable, args_list: List[tuple]) -> List[Future]:
        """批量提交任务
        
        Args:
            fn: 要执行的函数
            args_list: 参数列表
            
        Returns:
            List[Future]: Future对象列表
        """
        futures = []
        for args in args_list:
            future = self._executor.submit(fn, *args)
            futures.append(future)
            self.submitted_tasks += 1
        
        logger.info(f"📤 批量提交线程池任务: {len(futures)} 个")
        return futures
    
    async def submit_batch_async(self, fn: Callable, args_list: List[tuple]) -> List[Any]:
        """异步批量提交任务
        
        Args:
            fn: 要执行的函数
            args_list: 参数列表
            
        Returns:
            List[Any]: 执行结果列表
        """
        futures = self.submit_batch(fn, args_list)
        results = []
        
        for future in as_completed(futures):
            try:
                result = await asyncio.wrap_future(future)
                results.append(result)
                self.completed_tasks += 1
            except Exception as e:
                self.failed_tasks += 1
                logger.error(f"❌ 批量任务执行失败: {e}")
                results.append(None)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "executor_type": "ThreadPool",
            "max_workers": self.max_workers,
            "submitted_tasks": self.submitted_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": (self.completed_tasks / self.submitted_tasks * 100) if self.submitted_tasks > 0 else 0,
            "tasks_per_second": self.completed_tasks / uptime if uptime > 0 else 0,
            "uptime_seconds": uptime,
            "active_threads": threading.active_count()
        }
    
    def shutdown(self, wait: bool = True):
        """关闭执行器
        
        Args:
            wait: 是否等待任务完成
        """
        logger.info("🛑 关闭线程池执行器")
        self._executor.shutdown(wait=wait)


class ExecutorManager:
    """执行器管理器"""
    
    def __init__(self, 
                 cpu_workers: Optional[int] = None,
                 io_workers: Optional[int] = None):
        """初始化执行器管理器
        
        Args:
            cpu_workers: CPU密集型任务工作进程数
            io_workers: I/O密集型任务工作线程数
        """
        # 自动配置工作进程/线程数
        cpu_count = multiprocessing.cpu_count() or 1
        
        if cpu_workers is None:
            cpu_workers = cpu_count
        
        if io_workers is None:
            io_workers = cpu_count * 4
        
        # 创建执行器
        self.cpu_executor = OptimizedProcessPoolExecutor(max_workers=cpu_workers)
        self.io_executor = OptimizedThreadPoolExecutor(max_workers=io_workers)
        
        # 任务类型到执行器的映射
        self.task_executor_mapping = {
            TaskExecutionMode.CPU_INTENSIVE: self.cpu_executor,
            TaskExecutionMode.IO_INTENSIVE: self.io_executor,
            TaskExecutionMode.ASYNC_COROUTINE: None  # 直接异步执行
        }
        
        logger.info(f"⚙️ 执行器管理器初始化: CPU工作进程={cpu_workers}, I/O工作线程={io_workers}")
    
    async def execute_task(self, 
                          execution_mode: TaskExecutionMode,
                          fn: Callable,
                          *args,
                          **kwargs) -> Any:
        """执行任务
        
        Args:
            execution_mode: 执行模式
            fn: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 执行结果
        """
        executor = self.task_executor_mapping.get(execution_mode)
        
        if executor is None:
            # 异步协程直接执行
            if asyncio.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            else:
                # 同步函数包装为协程
                return await asyncio.to_thread(fn, *args, **kwargs)
        else:
            # 使用对应的执行器
            return await executor.submit(fn, *args, **kwargs)
    
    def get_optimal_execution_mode(self, task_type: TaskType) -> TaskExecutionMode:
        """获取任务类型的最优执行模式
        
        Args:
            task_type: 任务类型
            
        Returns:
            TaskExecutionMode: 执行模式
        """
        # 根据任务类型特性选择执行模式
        if task_type == TaskType.DOCUMENT_ANALYSIS:
            return TaskExecutionMode.CPU_INTENSIVE  # 文档解析是CPU密集型
        elif task_type == TaskType.TEST_GENERATION:
            return TaskExecutionMode.CPU_INTENSIVE  # 测试生成是CPU密集型
        elif task_type == TaskType.TEST_EXECUTION:
            return TaskExecutionMode.IO_INTENSIVE   # 测试执行是I/O密集型
        elif task_type == TaskType.REPORT_GENERATION:
            return TaskExecutionMode.CPU_INTENSIVE  # 报告生成是CPU密集型
        else:
            return TaskExecutionMode.ASYNC_COROUTINE  # 默认异步执行
    
    def get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源信息
        
        Returns:
            Dict[str, Any]: 系统资源信息
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                "cpu_count": multiprocessing.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "memory_percent": memory.percent,
                "active_threads": threading.active_count()
            }
        except Exception as e:
            logger.error(f"❌ 获取系统资源信息失败: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "cpu_executor": self.cpu_executor.get_statistics(),
            "io_executor": self.io_executor.get_statistics(),
            "system_resources": self.get_system_resources()
        }
    
    def shutdown(self, wait: bool = True):
        """关闭所有执行器
        
        Args:
            wait: 是否等待任务完成
        """
        logger.info("🛑 关闭执行器管理器")
        self.cpu_executor.shutdown(wait=wait)
        self.io_executor.shutdown(wait=wait)


# 全局执行器管理器实例
executor_manager = ExecutorManager()


logger.info("✅ 任务执行器模块初始化完成")
