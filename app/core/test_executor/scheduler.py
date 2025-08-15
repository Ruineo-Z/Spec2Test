"""
测试任务调度器

管理测试任务的调度、队列和执行。
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable
from queue import PriorityQueue, Queue, Empty
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

from app.core.shared.utils.logger import get_logger
from app.core.test_generator.models import TestCase, TestSuite
from .models import TestTask, TaskScheduleConfig, TestExecutionResult, TestSuiteExecutionResult
from .runner import TestRunner, ExecutionConfig


class TaskPriority:
    """任务优先级定义"""
    HIGH = 10
    NORMAL = 5
    LOW = 1


class TestTaskScheduler:
    """测试任务调度器
    
    负责管理测试任务的调度、队列和执行。
    """
    
    def __init__(self, schedule_config: Optional[TaskScheduleConfig] = None, 
                 execution_config: Optional[ExecutionConfig] = None):
        """初始化任务调度器
        
        Args:
            schedule_config: 调度配置
            execution_config: 执行配置
        """
        self.schedule_config = schedule_config or TaskScheduleConfig()
        self.execution_config = execution_config or ExecutionConfig()
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 任务队列
        if self.schedule_config.enable_priority:
            self.task_queue = PriorityQueue(maxsize=self.schedule_config.max_queue_size)
        else:
            self.task_queue = Queue(maxsize=self.schedule_config.max_queue_size)
        
        # 任务存储
        self.tasks: Dict[str, TestTask] = {}
        self.task_futures: Dict[str, Future] = {}
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.schedule_config.worker_threads)
        
        # 测试运行器
        self.test_runner = TestRunner(self.execution_config)
        
        # 调度器状态
        self.is_running = False
        self.scheduler_thread = None
        
        # 回调函数
        self.task_callbacks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_task_error": []
        }
        
        self.logger.info(f"任务调度器初始化完成: 工作线程={self.schedule_config.worker_threads}")
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            self.logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        self.logger.info("任务调度器已停止")
    
    def submit_test_case(self, test_case: TestCase, base_url: Optional[str] = None, 
                        priority: int = TaskPriority.NORMAL, 
                        scheduled_at: Optional[datetime] = None) -> str:
        """提交单个测试用例
        
        Args:
            test_case: 测试用例
            base_url: 基础URL
            priority: 优先级
            scheduled_at: 计划执行时间
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        task = TestTask(
            task_id=task_id,
            task_type="single_test",
            test_data=test_case.dict(),
            base_url=base_url,
            priority=priority,
            scheduled_at=scheduled_at
        )
        
        self.tasks[task_id] = task
        self._enqueue_task(task)
        
        self.logger.info(f"提交单个测试任务: {task_id} - {test_case.title}")
        return task_id
    
    def submit_test_suite(self, test_suite: TestSuite, base_url: Optional[str] = None,
                         priority: int = TaskPriority.NORMAL,
                         scheduled_at: Optional[datetime] = None) -> str:
        """提交测试套件
        
        Args:
            test_suite: 测试套件
            base_url: 基础URL
            priority: 优先级
            scheduled_at: 计划执行时间
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        
        task = TestTask(
            task_id=task_id,
            task_type="test_suite",
            test_data=test_suite.dict(),
            base_url=base_url,
            priority=priority,
            scheduled_at=scheduled_at
        )
        
        self.tasks[task_id] = task
        self._enqueue_task(task)
        
        self.logger.info(f"提交测试套件任务: {task_id} - {test_suite.name}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务状态信息
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        status_info = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "scheduled_at": task.scheduled_at,
            "is_completed": task.is_completed,
            "is_successful": task.is_successful
        }
        
        if task.error_message:
            status_info["error_message"] = task.error_message
        
        return status_info
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Dict[str, Any]]: 任务结果
        """
        task = self.tasks.get(task_id)
        if not task or not task.is_completed:
            return None
        
        return task.result
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.is_completed:
            self.logger.warning(f"任务已完成，无法取消: {task_id}")
            return False
        
        # 取消Future
        future = self.task_futures.get(task_id)
        if future:
            future.cancel()
        
        # 更新任务状态
        task.status = "cancelled"
        task.completed_at = datetime.now()
        
        self.logger.info(f"任务已取消: {task_id}")
        return True
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态
        
        Returns:
            Dict[str, Any]: 队列状态信息
        """
        return {
            "queue_size": self.task_queue.qsize(),
            "max_queue_size": self.schedule_config.max_queue_size,
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.task_futures),
            "worker_threads": self.schedule_config.worker_threads,
            "is_running": self.is_running
        }
    
    def add_callback(self, event: str, callback: Callable):
        """添加回调函数
        
        Args:
            event: 事件类型 (on_task_start, on_task_complete, on_task_error)
            callback: 回调函数
        """
        if event in self.task_callbacks:
            self.task_callbacks[event].append(callback)
    
    def _enqueue_task(self, task: TestTask):
        """将任务加入队列"""
        try:
            if self.schedule_config.enable_priority:
                # 优先级队列，数字越小优先级越高，所以取负值
                priority_item = (-task.priority, task.created_at, task)
                self.task_queue.put(priority_item, block=False)
            else:
                self.task_queue.put(task, block=False)
                
        except Exception as e:
            self.logger.error(f"任务入队失败: {task.task_id} - {e}")
            task.status = "failed"
            task.error_message = f"任务入队失败: {e}"
    
    def _scheduler_loop(self):
        """调度器主循环"""
        self.logger.info("调度器主循环已启动")
        
        while self.is_running:
            try:
                # 从队列获取任务
                if self.schedule_config.enable_priority:
                    try:
                        priority_item = self.task_queue.get(timeout=1.0)
                        task = priority_item[2]  # 获取任务对象
                    except Empty:
                        continue
                else:
                    try:
                        task = self.task_queue.get(timeout=1.0)
                    except Empty:
                        continue
                
                # 检查是否需要延迟执行
                if task.scheduled_at and task.scheduled_at > datetime.now():
                    # 重新放回队列
                    self._enqueue_task(task)
                    time.sleep(0.1)
                    continue
                
                # 提交任务执行
                future = self.executor.submit(self._execute_task, task)
                self.task_futures[task.task_id] = future
                
                # 清理已完成的Future
                self._cleanup_completed_futures()
                
            except Exception as e:
                self.logger.error(f"调度器循环异常: {e}")
                time.sleep(1.0)
        
        self.logger.info("调度器主循环已退出")
    
    def _execute_task(self, task: TestTask):
        """执行任务"""
        try:
            # 更新任务状态
            task.status = "running"
            task.started_at = datetime.now()
            
            # 触发开始回调
            self._trigger_callbacks("on_task_start", task)
            
            self.logger.info(f"开始执行任务: {task.task_id}")
            
            # 根据任务类型执行
            if task.task_type == "single_test":
                result = self._execute_single_test(task)
            elif task.task_type == "test_suite":
                result = self._execute_test_suite(task)
            else:
                raise ValueError(f"未知的任务类型: {task.task_type}")
            
            # 更新任务结果
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now()
            
            # 触发完成回调
            self._trigger_callbacks("on_task_complete", task)
            
            self.logger.info(f"任务执行完成: {task.task_id}")
            
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            self.logger.error(f"{error_msg} - {task.task_id}")
            
            # 更新任务状态
            task.status = "error"
            task.error_message = error_msg
            task.completed_at = datetime.now()
            
            # 触发错误回调
            self._trigger_callbacks("on_task_error", task)
        
        finally:
            # 清理Future引用
            self.task_futures.pop(task.task_id, None)
    
    def _execute_single_test(self, task: TestTask) -> Dict[str, Any]:
        """执行单个测试"""
        test_case_data = task.test_data
        test_case = TestCase(**test_case_data)
        
        result = self.test_runner.execute_test_case(test_case, task.base_url)
        
        return {
            "type": "single_test",
            "test_id": result.test_id,
            "status": result.status,
            "duration": result.duration,
            "result": result.dict() if hasattr(result, 'dict') else result.__dict__
        }
    
    def _execute_test_suite(self, task: TestTask) -> Dict[str, Any]:
        """执行测试套件"""
        test_suite_data = task.test_data
        test_suite = TestSuite(**test_suite_data)
        
        result = self.test_runner.execute_test_suite(test_suite, task.base_url)
        
        return {
            "type": "test_suite",
            "suite_id": result.suite_id,
            "total_tests": result.total_tests,
            "passed_tests": result.passed_tests,
            "failed_tests": result.failed_tests,
            "success_rate": result.success_rate,
            "total_duration": result.total_duration,
            "result": result.dict() if hasattr(result, 'dict') else result.__dict__
        }
    
    def _cleanup_completed_futures(self):
        """清理已完成的Future"""
        completed_task_ids = []
        
        for task_id, future in self.task_futures.items():
            if future.done():
                completed_task_ids.append(task_id)
        
        for task_id in completed_task_ids:
            self.task_futures.pop(task_id, None)
    
    def _trigger_callbacks(self, event: str, task: TestTask):
        """触发回调函数"""
        callbacks = self.task_callbacks.get(event, [])
        for callback in callbacks:
            try:
                callback(task)
            except Exception as e:
                self.logger.error(f"回调函数执行失败: {event} - {e}")
    
    def __del__(self):
        """析构函数"""
        try:
            if hasattr(self, 'is_running'):
                self.stop()
        except Exception:
            pass  # 忽略析构函数中的异常
