"""
任务监控和统计

提供任务执行的监控、指标收集和统计分析功能。
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field

from .models import TaskStatus, TaskType, TaskModel
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TaskMetrics:
    """任务指标"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    
    # 时间指标
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 性能指标
    execution_time: Optional[float] = None
    queue_time: Optional[float] = None
    retry_count: int = 0
    
    # 资源指标
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    def calculate_times(self):
        """计算时间指标"""
        if self.started_at:
            self.queue_time = (self.started_at - self.created_at).total_seconds()
        
        if self.started_at and self.completed_at:
            self.execution_time = (self.completed_at - self.started_at).total_seconds()


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    
    # 任务统计
    total_tasks: int = 0
    running_tasks: int = 0
    pending_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    # 性能统计
    avg_execution_time: float = 0.0
    avg_queue_time: float = 0.0
    success_rate: float = 0.0
    throughput_per_minute: float = 0.0
    
    # 系统资源
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    memory_usage_percent: float = 0.0
    
    # 执行器统计
    cpu_executor_stats: Dict[str, Any] = field(default_factory=dict)
    io_executor_stats: Dict[str, Any] = field(default_factory=dict)


class TaskMonitor:
    """任务监控器"""
    
    def __init__(self, max_history: int = 10000):
        """初始化任务监控器
        
        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        
        # 任务指标存储
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.completed_metrics: deque = deque(maxlen=max_history)
        
        # 系统指标历史
        self.system_metrics_history: deque = deque(maxlen=1000)
        
        # 统计计数器
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        
        # 监控回调
        self.callbacks: List[Callable] = []
        
        # 启动时间
        self.start_time = datetime.utcnow()
        
        logger.info("📊 任务监控器初始化完成")
    
    def record_task_created(self, task: TaskModel):
        """记录任务创建
        
        Args:
            task: 任务模型
        """
        metrics = TaskMetrics(
            task_id=task.task_id,
            task_type=task.task_type,
            status=task.status,
            created_at=task.created_at
        )
        
        self.task_metrics[task.task_id] = metrics
        self.counters[f"created_{task.task_type.value}"] += 1
        self.counters["total_created"] += 1
        
        logger.debug(f"📊 记录任务创建: {task.task_id}")
    
    def record_task_started(self, task_id: str):
        """记录任务开始
        
        Args:
            task_id: 任务ID
        """
        if task_id in self.task_metrics:
            metrics = self.task_metrics[task_id]
            metrics.started_at = datetime.utcnow()
            metrics.status = TaskStatus.RUNNING
            metrics.calculate_times()
            
            self.counters[f"started_{metrics.task_type.value}"] += 1
            self.counters["total_started"] += 1
            
            logger.debug(f"📊 记录任务开始: {task_id}")
    
    def record_task_completed(self, 
                            task_id: str, 
                            success: bool = True,
                            error: Optional[str] = None,
                            retry_count: int = 0):
        """记录任务完成
        
        Args:
            task_id: 任务ID
            success: 是否成功
            error: 错误信息
            retry_count: 重试次数
        """
        if task_id in self.task_metrics:
            metrics = self.task_metrics[task_id]
            metrics.completed_at = datetime.utcnow()
            metrics.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            metrics.retry_count = retry_count
            metrics.calculate_times()
            
            # 移动到完成指标
            self.completed_metrics.append(metrics)
            del self.task_metrics[task_id]
            
            # 更新计数器
            status_key = "completed" if success else "failed"
            self.counters[f"{status_key}_{metrics.task_type.value}"] += 1
            self.counters[f"total_{status_key}"] += 1
            
            # 记录执行时间
            if metrics.execution_time:
                self.timers[f"execution_time_{metrics.task_type.value}"].append(metrics.execution_time)
                self.timers["execution_time_all"].append(metrics.execution_time)
            
            # 记录队列时间
            if metrics.queue_time:
                self.timers[f"queue_time_{metrics.task_type.value}"].append(metrics.queue_time)
                self.timers["queue_time_all"].append(metrics.queue_time)
            
            logger.debug(f"📊 记录任务完成: {task_id} ({'成功' if success else '失败'})")
            
            # 触发回调
            self._trigger_callbacks("task_completed", {
                "task_id": task_id,
                "success": success,
                "metrics": metrics
            })
    
    def record_system_metrics(self, metrics: SystemMetrics):
        """记录系统指标
        
        Args:
            metrics: 系统指标
        """
        self.system_metrics_history.append(metrics)
        logger.debug("📊 记录系统指标")
    
    def get_task_statistics(self, 
                          task_type: Optional[TaskType] = None,
                          time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """获取任务统计
        
        Args:
            task_type: 任务类型过滤
            time_range: 时间范围过滤
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        # 过滤指标
        metrics_list = list(self.completed_metrics)
        
        if time_range:
            cutoff_time = datetime.utcnow() - time_range
            metrics_list = [m for m in metrics_list if m.completed_at and m.completed_at >= cutoff_time]
        
        if task_type:
            metrics_list = [m for m in metrics_list if m.task_type == task_type]
        
        # 计算统计
        total_tasks = len(metrics_list)
        if total_tasks == 0:
            return self._empty_statistics()
        
        # 按状态统计
        completed_tasks = len([m for m in metrics_list if m.status == TaskStatus.COMPLETED])
        failed_tasks = len([m for m in metrics_list if m.status == TaskStatus.FAILED])
        
        # 计算成功率
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 计算平均时间
        execution_times = [m.execution_time for m in metrics_list if m.execution_time]
        queue_times = [m.queue_time for m in metrics_list if m.queue_time]
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        avg_queue_time = sum(queue_times) / len(queue_times) if queue_times else 0
        
        # 计算吞吐量
        if time_range:
            throughput_per_minute = total_tasks / (time_range.total_seconds() / 60)
        else:
            uptime_minutes = (datetime.utcnow() - self.start_time).total_seconds() / 60
            throughput_per_minute = total_tasks / uptime_minutes if uptime_minutes > 0 else 0
        
        # 按任务类型统计
        by_type = defaultdict(int)
        for metrics in metrics_list:
            by_type[metrics.task_type.value] += 1
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": len(self.task_metrics),
            "success_rate": round(success_rate, 2),
            "avg_execution_time": round(avg_execution_time, 3),
            "avg_queue_time": round(avg_queue_time, 3),
            "throughput_per_minute": round(throughput_per_minute, 2),
            "by_task_type": dict(by_type),
            "time_range": str(time_range) if time_range else "all_time"
        }
    
    def _empty_statistics(self) -> Dict[str, Any]:
        """空统计信息"""
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "running_tasks": 0,
            "success_rate": 0,
            "avg_execution_time": 0,
            "avg_queue_time": 0,
            "throughput_per_minute": 0,
            "by_task_type": {},
            "time_range": "empty"
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能趋势
        
        Args:
            hours: 小时数
            
        Returns:
            Dict[str, Any]: 趋势数据
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 按小时分组统计
        hourly_stats = defaultdict(lambda: {"completed": 0, "failed": 0, "total_time": 0})
        
        for metrics in self.completed_metrics:
            if metrics.completed_at and metrics.completed_at >= cutoff_time:
                hour_key = metrics.completed_at.strftime("%Y-%m-%d %H:00")
                
                if metrics.status == TaskStatus.COMPLETED:
                    hourly_stats[hour_key]["completed"] += 1
                else:
                    hourly_stats[hour_key]["failed"] += 1
                
                if metrics.execution_time:
                    hourly_stats[hour_key]["total_time"] += metrics.execution_time
        
        # 转换为趋势数据
        trends = []
        for hour, stats in sorted(hourly_stats.items()):
            total = stats["completed"] + stats["failed"]
            avg_time = stats["total_time"] / stats["completed"] if stats["completed"] > 0 else 0
            success_rate = (stats["completed"] / total * 100) if total > 0 else 0
            
            trends.append({
                "hour": hour,
                "total_tasks": total,
                "completed_tasks": stats["completed"],
                "failed_tasks": stats["failed"],
                "success_rate": round(success_rate, 2),
                "avg_execution_time": round(avg_time, 3)
            })
        
        return {
            "time_range_hours": hours,
            "trends": trends,
            "summary": {
                "total_hours": len(trends),
                "peak_hour": max(trends, key=lambda x: x["total_tasks"])["hour"] if trends else None,
                "avg_success_rate": round(sum(t["success_rate"] for t in trends) / len(trends), 2) if trends else 0
            }
        }
    
    def add_callback(self, callback: Callable):
        """添加监控回调
        
        Args:
            callback: 回调函数
        """
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """移除监控回调
        
        Args:
            callback: 回调函数
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]):
        """触发回调
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event_type, data))
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"❌ 监控回调执行失败: {e}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """获取实时指标
        
        Returns:
            Dict[str, Any]: 实时指标
        """
        # 获取系统资源信息
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            system_resources = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_mb": memory.used / 1024 / 1024,
                "memory_usage_percent": memory.percent,
                "available_memory_mb": memory.available / 1024 / 1024
            }
        except ImportError:
            system_resources = {}
        
        # 当前运行任务统计
        running_by_type = defaultdict(int)
        for metrics in self.task_metrics.values():
            running_by_type[metrics.task_type.value] += 1
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "running_tasks": len(self.task_metrics),
            "running_by_type": dict(running_by_type),
            "completed_tasks_total": len(self.completed_metrics),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "system_resources": system_resources
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self.task_metrics.clear()
        self.completed_metrics.clear()
        self.system_metrics_history.clear()
        self.counters.clear()
        self.timers.clear()
        self.start_time = datetime.utcnow()
        
        logger.info("🔄 任务监控统计已重置")


# 全局任务监控器实例
task_monitor = TaskMonitor()


logger.info("✅ 任务监控和统计模块初始化完成")
