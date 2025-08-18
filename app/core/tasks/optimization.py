"""
任务性能优化

提供各种任务性能优化策略和工具。
"""

import asyncio
import gc
import resource
import threading
import time
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass

from .models import TaskType, TaskExecutionMode
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float
    memory_usage_mb: float
    cpu_time: float
    peak_memory_mb: Optional[float] = None
    gc_collections: int = 0
    thread_switches: int = 0


class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        """初始化性能分析器"""
        self.profiles: Dict[str, List[PerformanceMetrics]] = {}
        self.active_profiles: Dict[str, Dict[str, Any]] = {}
        
        logger.info("📊 性能分析器初始化完成")
    
    @contextmanager
    def profile_task(self, task_id: str):
        """任务性能分析上下文管理器
        
        Args:
            task_id: 任务ID
        """
        # 开始分析
        start_time = time.time()
        start_cpu_time = time.process_time()
        
        # 获取初始内存使用
        try:
            import psutil
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            peak_memory = start_memory
        except ImportError:
            start_memory = 0
            peak_memory = None
        
        # 获取初始GC统计
        gc_stats_start = gc.get_stats()
        gc_collections_start = sum(stat['collections'] for stat in gc_stats_start)
        
        # 记录开始状态
        self.active_profiles[task_id] = {
            "start_time": start_time,
            "start_cpu_time": start_cpu_time,
            "start_memory": start_memory,
            "peak_memory": peak_memory,
            "gc_collections_start": gc_collections_start
        }
        
        try:
            yield
        finally:
            # 结束分析
            end_time = time.time()
            end_cpu_time = time.process_time()
            
            # 计算执行时间
            execution_time = end_time - start_time
            cpu_time = end_cpu_time - start_cpu_time
            
            # 获取结束内存使用
            try:
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = end_memory - start_memory
                
                # 更新峰值内存
                current_memory = process.memory_info().rss / 1024 / 1024
                if peak_memory is None or current_memory > peak_memory:
                    peak_memory = current_memory
            except:
                memory_usage = 0
                peak_memory = None
            
            # 获取GC统计
            gc_stats_end = gc.get_stats()
            gc_collections_end = sum(stat['collections'] for stat in gc_stats_end)
            gc_collections = gc_collections_end - gc_collections_start
            
            # 创建性能指标
            metrics = PerformanceMetrics(
                execution_time=execution_time,
                memory_usage_mb=memory_usage,
                cpu_time=cpu_time,
                peak_memory_mb=peak_memory,
                gc_collections=gc_collections,
                thread_switches=0  # 需要更复杂的监控
            )
            
            # 保存指标
            if task_id not in self.profiles:
                self.profiles[task_id] = []
            self.profiles[task_id].append(metrics)
            
            # 清理活跃分析
            self.active_profiles.pop(task_id, None)
            
            logger.info(f"📊 任务性能分析完成: {task_id} (执行时间: {execution_time:.3f}s, 内存: {memory_usage:.1f}MB)")
    
    def get_task_metrics(self, task_id: str) -> List[PerformanceMetrics]:
        """获取任务性能指标
        
        Args:
            task_id: 任务ID
            
        Returns:
            List[PerformanceMetrics]: 性能指标列表
        """
        return self.profiles.get(task_id, [])
    
    def get_average_metrics(self, task_type: Optional[TaskType] = None) -> Optional[PerformanceMetrics]:
        """获取平均性能指标
        
        Args:
            task_type: 任务类型过滤
            
        Returns:
            Optional[PerformanceMetrics]: 平均性能指标
        """
        all_metrics = []
        for metrics_list in self.profiles.values():
            all_metrics.extend(metrics_list)
        
        if not all_metrics:
            return None
        
        # 计算平均值
        avg_execution_time = sum(m.execution_time for m in all_metrics) / len(all_metrics)
        avg_memory_usage = sum(m.memory_usage_mb for m in all_metrics) / len(all_metrics)
        avg_cpu_time = sum(m.cpu_time for m in all_metrics) / len(all_metrics)
        avg_gc_collections = sum(m.gc_collections for m in all_metrics) / len(all_metrics)
        
        # 计算峰值内存平均值
        peak_memories = [m.peak_memory_mb for m in all_metrics if m.peak_memory_mb is not None]
        avg_peak_memory = sum(peak_memories) / len(peak_memories) if peak_memories else None
        
        return PerformanceMetrics(
            execution_time=avg_execution_time,
            memory_usage_mb=avg_memory_usage,
            cpu_time=avg_cpu_time,
            peak_memory_mb=avg_peak_memory,
            gc_collections=int(avg_gc_collections)
        )
    
    def clear_profiles(self, task_id: Optional[str] = None):
        """清理性能分析数据
        
        Args:
            task_id: 任务ID，None表示清理所有
        """
        if task_id:
            self.profiles.pop(task_id, None)
        else:
            self.profiles.clear()
        
        logger.info(f"🧹 清理性能分析数据: {task_id or '全部'}")


class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self):
        """初始化内存优化器"""
        self.gc_threshold = (700, 10, 10)  # 更激进的GC阈值
        self.memory_limit_mb = 1024  # 1GB内存限制
        
        # 设置GC阈值
        gc.set_threshold(*self.gc_threshold)
        
        logger.info("🧠 内存优化器初始化完成")
    
    def optimize_memory(self):
        """执行内存优化"""
        # 强制垃圾回收
        collected = gc.collect()
        
        # 获取内存使用情况
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            logger.info(f"🧠 内存优化完成: 回收对象={collected}, 当前内存={memory_mb:.1f}MB")
            
            # 如果内存使用过高，发出警告
            if memory_mb > self.memory_limit_mb:
                logger.warning(f"⚠️ 内存使用过高: {memory_mb:.1f}MB > {self.memory_limit_mb}MB")
                
        except ImportError:
            logger.info(f"🧠 内存优化完成: 回收对象={collected}")
    
    @contextmanager
    def memory_limit_context(self, limit_mb: int):
        """内存限制上下文管理器
        
        Args:
            limit_mb: 内存限制(MB)
        """
        old_limit = self.memory_limit_mb
        self.memory_limit_mb = limit_mb
        
        try:
            yield
        finally:
            self.memory_limit_mb = old_limit
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用情况
        
        Returns:
            Dict[str, Any]: 内存使用信息
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
                "gc_stats": gc.get_stats(),
                "gc_counts": gc.get_count()
            }
        except ImportError:
            return {
                "gc_stats": gc.get_stats(),
                "gc_counts": gc.get_count()
            }


class CPUOptimizer:
    """CPU优化器"""
    
    def __init__(self):
        """初始化CPU优化器"""
        self.cpu_intensive_tasks = {
            TaskType.DOCUMENT_ANALYSIS,
            TaskType.TEST_GENERATION,
            TaskType.REPORT_GENERATION
        }
        
        logger.info("⚡ CPU优化器初始化完成")
    
    def optimize_for_cpu_task(self, task_type: TaskType) -> Dict[str, Any]:
        """为CPU密集型任务优化
        
        Args:
            task_type: 任务类型
            
        Returns:
            Dict[str, Any]: 优化配置
        """
        if task_type not in self.cpu_intensive_tasks:
            return {}
        
        # CPU密集型任务优化配置
        config = {
            "use_process_pool": True,
            "chunk_size": self._calculate_optimal_chunk_size(),
            "enable_parallel": True,
            "gc_frequency": "low"  # 降低GC频率
        }
        
        logger.info(f"⚡ CPU任务优化配置: {task_type} -> {config}")
        return config
    
    def _calculate_optimal_chunk_size(self) -> int:
        """计算最优分块大小
        
        Returns:
            int: 分块大小
        """
        try:
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            # 基于CPU核心数计算分块大小
            return max(1, 1000 // cpu_count)
        except:
            return 100


class IOOptimizer:
    """I/O优化器"""
    
    def __init__(self):
        """初始化I/O优化器"""
        self.io_intensive_tasks = {
            TaskType.TEST_EXECUTION
        }
        
        # 连接池配置
        self.connection_pool_config = {
            "max_connections": 100,
            "max_keepalive_connections": 20,
            "keepalive_expiry": 5.0
        }
        
        logger.info("🔌 I/O优化器初始化完成")
    
    def optimize_for_io_task(self, task_type: TaskType) -> Dict[str, Any]:
        """为I/O密集型任务优化
        
        Args:
            task_type: 任务类型
            
        Returns:
            Dict[str, Any]: 优化配置
        """
        if task_type not in self.io_intensive_tasks:
            return {}
        
        # I/O密集型任务优化配置
        config = {
            "use_thread_pool": True,
            "connection_pool": self.connection_pool_config,
            "enable_async": True,
            "batch_size": 50,
            "timeout": 30
        }
        
        logger.info(f"🔌 I/O任务优化配置: {task_type} -> {config}")
        return config
    
    async def optimize_http_requests(self, urls: List[str]) -> List[Any]:
        """优化HTTP请求
        
        Args:
            urls: URL列表
            
        Returns:
            List[Any]: 响应列表
        """
        import aiohttp
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=self.connection_pool_config["max_connections"],
                limit_per_host=self.connection_pool_config["max_keepalive_connections"],
                keepalive_timeout=self.connection_pool_config["keepalive_expiry"]
            )
        ) as session:
            tasks = [self._fetch_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        return results
    
    async def _fetch_url(self, session: 'aiohttp.ClientSession', url: str) -> Any:
        """获取URL内容
        
        Args:
            session: HTTP会话
            url: URL
            
        Returns:
            Any: 响应内容
        """
        try:
            async with session.get(url) as response:
                return await response.text()
        except Exception as e:
            logger.error(f"❌ HTTP请求失败: {url} - {e}")
            return None


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        """初始化性能优化器"""
        self.profiler = PerformanceProfiler()
        self.memory_optimizer = MemoryOptimizer()
        self.cpu_optimizer = CPUOptimizer()
        self.io_optimizer = IOOptimizer()
        
        logger.info("🚀 性能优化器初始化完成")
    
    def get_optimization_config(self, task_type: TaskType, execution_mode: TaskExecutionMode) -> Dict[str, Any]:
        """获取优化配置
        
        Args:
            task_type: 任务类型
            execution_mode: 执行模式
            
        Returns:
            Dict[str, Any]: 优化配置
        """
        config = {}
        
        if execution_mode == TaskExecutionMode.CPU_INTENSIVE:
            config.update(self.cpu_optimizer.optimize_for_cpu_task(task_type))
        elif execution_mode == TaskExecutionMode.IO_INTENSIVE:
            config.update(self.io_optimizer.optimize_for_io_task(task_type))
        
        return config
    
    def optimize_task_execution(self, task_type: TaskType):
        """优化任务执行环境
        
        Args:
            task_type: 任务类型
        """
        # 执行内存优化
        self.memory_optimizer.optimize_memory()
        
        # 根据任务类型进行特定优化
        if task_type in self.cpu_optimizer.cpu_intensive_tasks:
            logger.info(f"⚡ 为CPU密集型任务优化: {task_type}")
        elif task_type in self.io_optimizer.io_intensive_tasks:
            logger.info(f"🔌 为I/O密集型任务优化: {task_type}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告
        
        Returns:
            Dict[str, Any]: 性能报告
        """
        avg_metrics = self.profiler.get_average_metrics()
        memory_info = self.memory_optimizer.check_memory_usage()
        
        return {
            "average_metrics": avg_metrics.__dict__ if avg_metrics else None,
            "memory_info": memory_info,
            "total_profiles": len(self.profiler.profiles),
            "optimization_config": {
                "gc_threshold": self.memory_optimizer.gc_threshold,
                "memory_limit_mb": self.memory_optimizer.memory_limit_mb
            }
        }


# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()


def performance_monitor(func: Callable) -> Callable:
    """性能监控装饰器
    
    Args:
        func: 要监控的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        task_id = kwargs.get('task_id', f"func_{func.__name__}_{int(time.time())}")
        
        with performance_optimizer.profiler.profile_task(task_id):
            return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        task_id = kwargs.get('task_id', f"func_{func.__name__}_{int(time.time())}")
        
        with performance_optimizer.profiler.profile_task(task_id):
            return func(*args, **kwargs)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


logger.info("✅ 任务性能优化模块初始化完成")
