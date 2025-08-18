"""
增强任务管理器

基于FastAPI BackgroundTasks的增强任务管理系统。
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Awaitable, Union, List
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import asynccontextmanager

from .models import (
    TaskModel, TaskStatus, TaskType, TaskPriority, TaskExecutionMode,
    TaskCreateRequest, TaskExecutionContext, TaskHandler
)
from .storage import TaskStorageInterface
from .lifecycle import TaskLifecycleManager, task_lifecycle_manager
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class EnhancedTaskManager:
    """增强任务管理器
    
    基于FastAPI BackgroundTasks构建的企业级任务管理系统。
    """
    
    def __init__(self, 
                 storage: TaskStorageInterface,
                 max_cpu_workers: int = 4,
                 max_io_workers: int = 16,
                 lifecycle_manager: Optional[TaskLifecycleManager] = None):
        """初始化任务管理器
        
        Args:
            storage: 任务存储接口
            max_cpu_workers: CPU密集型任务最大工作进程数
            max_io_workers: I/O密集型任务最大工作线程数
            lifecycle_manager: 生命周期管理器
        """
        self.storage = storage
        self.lifecycle_manager = lifecycle_manager or task_lifecycle_manager
        
        # 执行器池
        self.cpu_executor = ProcessPoolExecutor(max_workers=max_cpu_workers)
        self.io_executor = ThreadPoolExecutor(max_workers=max_io_workers)
        
        # 任务处理器注册表
        self.task_handlers: Dict[TaskType, TaskHandler] = {}
        
        # 运行状态跟踪
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_contexts: Dict[str, TaskExecutionContext] = {}
        
        # 配置参数
        self.max_cpu_workers = max_cpu_workers
        self.max_io_workers = max_io_workers
        self.cleanup_interval = 300  # 5分钟清理一次
        self.timeout_check_interval = 60  # 1分钟检查一次超时
        
        # 启动后台任务
        self._cleanup_task = None
        self._timeout_check_task = None
        
        logger.info(f"🚀 增强任务管理器初始化完成: CPU工作进程={max_cpu_workers}, I/O工作线程={max_io_workers}")
    
    async def start(self):
        """启动任务管理器"""
        # 连接存储
        await self.storage.connect()
        
        # 启动后台清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._timeout_check_task = asyncio.create_task(self._timeout_check_loop())
        
        logger.info("✅ 任务管理器启动完成")
    
    async def stop(self):
        """停止任务管理器"""
        logger.info("🛑 正在停止任务管理器...")
        
        # 停止后台任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._timeout_check_task:
            self._timeout_check_task.cancel()
        
        # 取消所有运行中的任务
        for task_id, task in self.running_tasks.items():
            logger.info(f"🛑 取消运行中任务: {task_id}")
            task.cancel()
        
        # 等待任务完成
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        # 关闭执行器
        self.cpu_executor.shutdown(wait=True)
        self.io_executor.shutdown(wait=True)
        
        # 断开存储连接
        await self.storage.disconnect()
        
        logger.info("✅ 任务管理器已停止")
    
    def register_handler(self, task_type: TaskType, handler: TaskHandler):
        """注册任务处理器
        
        Args:
            task_type: 任务类型
            handler: 任务处理函数
        """
        self.task_handlers[task_type] = handler
        logger.info(f"📝 注册任务处理器: {task_type}")
    
    def unregister_handler(self, task_type: TaskType):
        """注销任务处理器
        
        Args:
            task_type: 任务类型
        """
        if task_type in self.task_handlers:
            del self.task_handlers[task_type]
            logger.info(f"📝 注销任务处理器: {task_type}")
    
    async def submit_task(self, request: TaskCreateRequest) -> str:
        """提交任务
        
        Args:
            request: 任务创建请求
            
        Returns:
            str: 任务ID
            
        Raises:
            ValueError: 任务类型未注册处理器
            StorageException: 存储操作失败
        """
        # 检查处理器是否存在
        if request.task_type not in self.task_handlers:
            raise ValueError(f"No handler registered for task type: {request.task_type}")
        
        # 创建任务模型
        task = TaskModel(
            task_id=str(uuid.uuid4()),
            task_type=request.task_type,
            status=TaskStatus.PENDING,
            priority=request.priority,
            execution_mode=request.execution_mode,
            created_at=datetime.utcnow(),
            input_data=request.input_data,
            timeout_seconds=request.timeout_seconds,
            max_retries=request.max_retries,
            metadata=request.metadata
        )
        
        # 保存到存储
        await self.storage.create_task(task)
        
        # 异步执行任务
        asyncio.create_task(self._execute_task(task.task_id))
        
        logger.info(f"📤 任务提交成功: {task.task_id} ({request.task_type})")
        return task.task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskModel]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskModel]: 任务模型
        """
        return await self.storage.get_task(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        # 取消运行中的任务
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]
        
        # 更新数据库状态
        success = await self.storage.update_task_status(
            task_id, TaskStatus.CANCELLED,
            completed_at=datetime.utcnow()
        )
        
        if success:
            logger.info(f"🛑 任务取消成功: {task_id}")
        
        return success
    
    async def retry_task(self, task_id: str) -> bool:
        """重试任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功启动重试
        """
        task = await self.storage.get_task(task_id)
        if not task:
            return False
        
        # 检查是否可以重试
        if not self.lifecycle_manager.should_retry(task):
            logger.warning(f"⚠️ 任务不能重试: {task_id} (重试次数: {task.retry_count}/{task.max_retries})")
            return False
        
        # 更新重试信息
        task.retry_count += 1
        task.status = TaskStatus.PENDING
        task.error_info = None
        task.started_at = None
        task.completed_at = None
        
        # 保存更新
        await self.storage.update_task_retry(task_id, task.retry_count, {})
        await self.storage.update_task_status(task_id, TaskStatus.PENDING)
        
        # 重新执行
        asyncio.create_task(self._execute_task(task_id))
        
        logger.info(f"🔄 任务重试启动: {task_id} (第{task.retry_count}次重试)")
        return True
    
    async def _execute_task(self, task_id: str):
        """执行任务
        
        Args:
            task_id: 任务ID
        """
        try:
            # 获取任务
            task = await self.storage.get_task(task_id)
            if not task:
                logger.error(f"❌ 任务不存在: {task_id}")
                return
            
            # 检查任务状态
            if task.status != TaskStatus.PENDING:
                logger.warning(f"⚠️ 任务状态不是PENDING: {task_id} ({task.status})")
                return
            
            # 获取处理器
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                await self._mark_task_failed(task_id, "No handler registered")
                return
            
            # 创建执行上下文
            context = TaskExecutionContext(
                task_id=task_id,
                task_type=task.task_type,
                execution_mode=task.execution_mode,
                timeout_seconds=task.timeout_seconds,
                retry_count=task.retry_count,
                max_retries=task.max_retries,
                input_data=task.input_data,
                metadata=task.metadata,
                started_at=datetime.utcnow()
            )
            
            self.task_contexts[task_id] = context
            
            # 更新状态为运行中
            await self.storage.update_task_status(
                task_id, TaskStatus.RUNNING,
                started_at=context.started_at
            )
            
            # 执行任务（带超时和重试）
            result = await self._execute_with_timeout_and_retry(task, handler, context)
            
            # 更新完成状态
            await self.storage.update_task_status(
                task_id, TaskStatus.COMPLETED,
                result_data=result,
                completed_at=datetime.utcnow()
            )
            
            logger.info(f"✅ 任务执行完成: {task_id}")
            
        except asyncio.CancelledError:
            logger.info(f"🛑 任务被取消: {task_id}")
            await self.storage.update_task_status(
                task_id, TaskStatus.CANCELLED,
                completed_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"❌ 任务执行异常: {task_id} - {e}")
            await self._mark_task_failed(task_id, str(e))
        finally:
            # 清理运行状态
            self.running_tasks.pop(task_id, None)
            self.task_contexts.pop(task_id, None)
    
    async def _execute_with_timeout_and_retry(self, 
                                            task: TaskModel, 
                                            handler: TaskHandler,
                                            context: TaskExecutionContext) -> Any:
        """带超时和重试的任务执行
        
        Args:
            task: 任务模型
            handler: 任务处理器
            context: 执行上下文
            
        Returns:
            Any: 任务执行结果
        """
        # 根据执行模式选择执行方式
        if task.execution_mode == TaskExecutionMode.CPU_INTENSIVE:
            # CPU密集型任务使用进程池
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(self.cpu_executor, handler, task.input_data),
                timeout=task.timeout_seconds
            )
        elif task.execution_mode == TaskExecutionMode.IO_INTENSIVE:
            # I/O密集型任务使用线程池
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(self.io_executor, handler, task.input_data),
                timeout=task.timeout_seconds
            )
        else:
            # 异步协程直接执行
            if asyncio.iscoroutinefunction(handler):
                result = await asyncio.wait_for(
                    handler(task.input_data),
                    timeout=task.timeout_seconds
                )
            else:
                # 同步函数包装为协程
                result = await asyncio.wait_for(
                    asyncio.to_thread(handler, task.input_data),
                    timeout=task.timeout_seconds
                )
        
        return result
    
    async def _mark_task_failed(self, task_id: str, error_msg: str):
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error_msg: 错误消息
        """
        error_info = {
            "error": error_msg,
            "failed_at": datetime.utcnow().isoformat(),
            "worker_info": {
                "cpu_workers": self.max_cpu_workers,
                "io_workers": self.max_io_workers
            }
        }
        
        await self.storage.update_task_status(
            task_id, TaskStatus.FAILED,
            error_info=error_info,
            completed_at=datetime.utcnow()
        )
    
    async def _cleanup_loop(self):
        """后台清理循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 清理任务异常: {e}")
    
    async def _timeout_check_loop(self):
        """超时检查循环"""
        while True:
            try:
                await asyncio.sleep(self.timeout_check_interval)
                await self._check_timeout_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 超时检查异常: {e}")
    
    async def _cleanup_old_tasks(self):
        """清理旧任务"""
        # 清理7天前的已完成任务
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        deleted_count = await self.storage.delete_old_tasks(
            cutoff_time, 
            [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        )
        
        if deleted_count > 0:
            logger.info(f"🧹 清理旧任务: {deleted_count} 个")
    
    async def _check_timeout_tasks(self):
        """检查超时任务"""
        timeout_threshold = datetime.utcnow() - timedelta(seconds=300)  # 5分钟前
        timeout_tasks = await self.storage.get_timeout_tasks(timeout_threshold)
        
        for task in timeout_tasks:
            # 取消运行中的任务
            if task.task_id in self.running_tasks:
                self.running_tasks[task.task_id].cancel()
            
            # 更新状态为超时
            await self.storage.update_task_status(
                task.task_id, TaskStatus.TIMEOUT,
                error_info={"timeout_at": datetime.utcnow().isoformat()},
                completed_at=datetime.utcnow()
            )
            
            logger.warning(f"⏰ 任务超时: {task.task_id}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取任务管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        storage_stats = await self.storage.get_task_statistics()
        
        return {
            **storage_stats.dict(),
            "running_tasks": len(self.running_tasks),
            "registered_handlers": len(self.task_handlers),
            "cpu_workers": self.max_cpu_workers,
            "io_workers": self.max_io_workers,
            "manager_uptime": "N/A"  # 可以添加启动时间跟踪
        }


logger.info("✅ 增强任务管理器模块初始化完成")
