"""
任务存储接口定义

提供任务数据持久化的抽象接口，支持PostgreSQL和SQLite。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from .models import TaskModel, TaskStatus, TaskType, TaskPriority, TaskStatistics, TaskListRequest
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStorageInterface(ABC):
    """任务存储抽象接口
    
    定义任务数据持久化的标准接口，支持多种数据库后端。
    """
    
    @abstractmethod
    async def create_task(self, task: TaskModel) -> str:
        """创建任务
        
        Args:
            task: 任务模型
            
        Returns:
            str: 任务ID
            
        Raises:
            StorageException: 存储操作失败
        """
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[TaskModel]:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskModel]: 任务模型，不存在时返回None
        """
        pass
    
    @abstractmethod
    async def update_task_status(self, 
                               task_id: str, 
                               status: TaskStatus,
                               result_data: Optional[Dict[str, Any]] = None,
                               error_info: Optional[Dict[str, Any]] = None,
                               started_at: Optional[datetime] = None,
                               completed_at: Optional[datetime] = None) -> bool:
        """更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            result_data: 结果数据
            error_info: 错误信息
            started_at: 开始时间
            completed_at: 完成时间
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def update_task_retry(self, task_id: str, retry_count: int, error_info: Dict[str, Any]) -> bool:
        """更新任务重试信息
        
        Args:
            task_id: 任务ID
            retry_count: 重试次数
            error_info: 错误信息
            
        Returns:
            bool: 更新是否成功
        """
        pass
    
    @abstractmethod
    async def list_tasks(self, request: TaskListRequest) -> Tuple[List[TaskModel], int]:
        """获取任务列表
        
        Args:
            request: 查询请求参数
            
        Returns:
            Tuple[List[TaskModel], int]: (任务列表, 总数量)
        """
        pass
    
    @abstractmethod
    async def get_pending_tasks(self, limit: int = 100) -> List[TaskModel]:
        """获取待执行任务列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[TaskModel]: 待执行任务列表，按优先级和创建时间排序
        """
        pass
    
    @abstractmethod
    async def get_running_tasks(self) -> List[TaskModel]:
        """获取正在运行的任务列表
        
        Returns:
            List[TaskModel]: 运行中任务列表
        """
        pass
    
    @abstractmethod
    async def get_timeout_tasks(self, timeout_threshold: datetime) -> List[TaskModel]:
        """获取超时任务列表
        
        Args:
            timeout_threshold: 超时阈值时间
            
        Returns:
            List[TaskModel]: 超时任务列表
        """
        pass
    
    @abstractmethod
    async def get_task_statistics(self, 
                                time_range: Optional[timedelta] = None) -> TaskStatistics:
        """获取任务统计信息
        
        Args:
            time_range: 统计时间范围，None表示全部时间
            
        Returns:
            TaskStatistics: 统计信息
        """
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def delete_old_tasks(self, 
                             older_than: datetime,
                             status_filter: Optional[List[TaskStatus]] = None) -> int:
        """删除旧任务
        
        Args:
            older_than: 删除早于此时间的任务
            status_filter: 状态过滤，None表示所有状态
            
        Returns:
            int: 删除的任务数量
        """
        pass
    
    @abstractmethod
    async def bulk_update_status(self, 
                               task_ids: List[str], 
                               status: TaskStatus,
                               error_info: Optional[Dict[str, Any]] = None) -> int:
        """批量更新任务状态
        
        Args:
            task_ids: 任务ID列表
            status: 新状态
            error_info: 错误信息
            
        Returns:
            int: 更新的任务数量
        """
        pass
    
    @abstractmethod
    async def get_tasks_by_type_and_status(self, 
                                         task_type: TaskType,
                                         status: TaskStatus,
                                         limit: int = 100) -> List[TaskModel]:
        """根据类型和状态获取任务
        
        Args:
            task_type: 任务类型
            status: 任务状态
            limit: 返回数量限制
            
        Returns:
            List[TaskModel]: 任务列表
        """
        pass
    
    @abstractmethod
    async def count_tasks_by_status(self, 
                                  status: TaskStatus,
                                  time_range: Optional[timedelta] = None) -> int:
        """按状态统计任务数量
        
        Args:
            status: 任务状态
            time_range: 时间范围
            
        Returns:
            int: 任务数量
        """
        pass
    
    @abstractmethod
    async def get_task_execution_times(self, 
                                     task_type: Optional[TaskType] = None,
                                     limit: int = 1000) -> List[float]:
        """获取任务执行时间列表
        
        Args:
            task_type: 任务类型过滤
            limit: 返回数量限制
            
        Returns:
            List[float]: 执行时间列表(秒)
        """
        pass
    
    # 事务支持
    @abstractmethod
    async def begin_transaction(self):
        """开始事务"""
        pass
    
    @abstractmethod
    async def commit_transaction(self):
        """提交事务"""
        pass
    
    @abstractmethod
    async def rollback_transaction(self):
        """回滚事务"""
        pass
    
    # 连接管理
    @abstractmethod
    async def connect(self):
        """建立数据库连接"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查
        
        Returns:
            bool: 数据库连接是否正常
        """
        pass


class StorageException(Exception):
    """存储操作异常"""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause
        self.timestamp = datetime.utcnow()
    
    def __str__(self):
        if self.cause:
            return f"{super().__str__()} (caused by: {self.cause})"
        return super().__str__()


class TaskNotFoundError(StorageException):
    """任务不存在异常"""
    
    def __init__(self, task_id: str):
        super().__init__(f"Task not found: {task_id}")
        self.task_id = task_id


class TaskAlreadyExistsError(StorageException):
    """任务已存在异常"""
    
    def __init__(self, task_id: str):
        super().__init__(f"Task already exists: {task_id}")
        self.task_id = task_id


class DatabaseConnectionError(StorageException):
    """数据库连接异常"""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(f"Database connection error: {message}", cause)


class TransactionError(StorageException):
    """事务操作异常"""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(f"Transaction error: {message}", cause)


# 存储工厂接口
class TaskStorageFactory(ABC):
    """任务存储工厂接口"""
    
    @abstractmethod
    def create_storage(self, database_url: str, **kwargs) -> TaskStorageInterface:
        """创建存储实例
        
        Args:
            database_url: 数据库连接URL
            **kwargs: 其他配置参数
            
        Returns:
            TaskStorageInterface: 存储实例
        """
        pass


logger.info("✅ 任务存储接口定义完成")
