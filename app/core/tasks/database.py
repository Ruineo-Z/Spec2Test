"""
数据库任务存储实现

基于SQLAlchemy的任务存储实现，支持PostgreSQL和SQLite。
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload

from .storage import TaskStorageInterface, StorageException, TaskNotFoundError, TaskAlreadyExistsError, DatabaseConnectionError, TransactionError
from .models import TaskModel, TaskRecord, TaskStatus, TaskType, TaskPriority, TaskStatistics, TaskListRequest, Base
from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseTaskStorage(TaskStorageInterface):
    """数据库任务存储实现"""
    
    def __init__(self, database_url: str, **kwargs):
        """初始化数据库存储
        
        Args:
            database_url: 数据库连接URL
            **kwargs: 其他配置参数
        """
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self._current_session = None
        
        # 配置参数
        self.pool_size = kwargs.get('pool_size', 20)
        self.max_overflow = kwargs.get('max_overflow', 30)
        self.pool_pre_ping = kwargs.get('pool_pre_ping', True)
        self.echo = kwargs.get('echo', False)
        
        logger.info(f"🗄️ 初始化数据库任务存储: {self._mask_url(database_url)}")
    
    def _mask_url(self, url: str) -> str:
        """屏蔽URL中的敏感信息"""
        if '://' in url and '@' in url:
            protocol, rest = url.split('://', 1)
            if '@' in rest:
                credentials, host_part = rest.split('@', 1)
                return f"{protocol}://***:***@{host_part}"
        return url
    
    async def connect(self):
        """建立数据库连接"""
        try:
            if self.database_url.startswith("postgresql"):
                # PostgreSQL配置
                self.engine = create_async_engine(
                    self.database_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_pre_ping=self.pool_pre_ping,
                    echo=self.echo
                )
            elif self.database_url.startswith("sqlite"):
                # SQLite配置
                self.engine = create_async_engine(
                    self.database_url,
                    echo=self.echo,
                    connect_args={"check_same_thread": False}
                )
            else:
                raise ValueError(f"Unsupported database URL: {self.database_url}")
            
            # 创建会话工厂
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 创建表结构
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ 数据库连接建立成功")
            
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise DatabaseConnectionError("Failed to connect to database", e)
    
    async def disconnect(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ 数据库连接已关闭")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with self.session_factory() as session:
                result = await session.execute(select(1))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"❌ 数据库健康检查失败: {e}")
            return False
    
    @asynccontextmanager
    async def _get_session(self):
        """获取数据库会话"""
        if self._current_session:
            # 使用当前事务会话
            yield self._current_session
        else:
            # 创建新会话
            async with self.session_factory() as session:
                yield session
    
    async def create_task(self, task: TaskModel) -> str:
        """创建任务"""
        try:
            async with self._get_session() as session:
                # 检查任务是否已存在
                existing = await session.get(TaskRecord, task.task_id)
                if existing:
                    raise TaskAlreadyExistsError(task.task_id)
                
                # 创建新任务记录
                record = task.to_record()
                session.add(record)
                
                if not self._current_session:
                    await session.commit()
                
                logger.info(f"✅ 任务创建成功: {task.task_id} ({task.task_type})")
                return task.task_id
                
        except TaskAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"❌ 任务创建失败: {task.task_id} - {e}")
            raise StorageException(f"Failed to create task: {task.task_id}", e)
    
    async def get_task(self, task_id: str) -> Optional[TaskModel]:
        """获取任务"""
        try:
            async with self._get_session() as session:
                record = await session.get(TaskRecord, task_id)
                if record:
                    return TaskModel.from_record(record)
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取任务失败: {task_id} - {e}")
            raise StorageException(f"Failed to get task: {task_id}", e)
    
    async def update_task_status(self, 
                               task_id: str, 
                               status: TaskStatus,
                               result_data: Optional[Dict[str, Any]] = None,
                               error_info: Optional[Dict[str, Any]] = None,
                               started_at: Optional[datetime] = None,
                               completed_at: Optional[datetime] = None) -> bool:
        """更新任务状态"""
        try:
            async with self._get_session() as session:
                # 构建更新数据
                update_data = {"status": status.value}
                
                if result_data is not None:
                    update_data["result_data"] = result_data
                
                if error_info is not None:
                    update_data["error_info"] = error_info
                
                if started_at is not None:
                    update_data["started_at"] = started_at
                
                if completed_at is not None:
                    update_data["completed_at"] = completed_at
                
                # 执行更新
                stmt = update(TaskRecord).where(TaskRecord.id == task_id).values(**update_data)
                result = await session.execute(stmt)
                
                if not self._current_session:
                    await session.commit()
                
                success = result.rowcount > 0
                if success:
                    logger.info(f"✅ 任务状态更新成功: {task_id} -> {status}")
                else:
                    logger.warning(f"⚠️ 任务不存在: {task_id}")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ 任务状态更新失败: {task_id} - {e}")
            raise StorageException(f"Failed to update task status: {task_id}", e)
    
    async def update_task_retry(self, task_id: str, retry_count: int, error_info: Dict[str, Any]) -> bool:
        """更新任务重试信息"""
        try:
            async with self._get_session() as session:
                stmt = update(TaskRecord).where(TaskRecord.id == task_id).values(
                    retry_count=retry_count,
                    error_info=error_info,
                    status=TaskStatus.RETRYING.value
                )
                result = await session.execute(stmt)
                
                if not self._current_session:
                    await session.commit()
                
                success = result.rowcount > 0
                if success:
                    logger.info(f"✅ 任务重试信息更新成功: {task_id} (重试次数: {retry_count})")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ 任务重试信息更新失败: {task_id} - {e}")
            raise StorageException(f"Failed to update task retry: {task_id}", e)
    
    async def list_tasks(self, request: TaskListRequest) -> Tuple[List[TaskModel], int]:
        """获取任务列表"""
        try:
            async with self._get_session() as session:
                # 构建查询条件
                conditions = []
                
                if request.task_type:
                    conditions.append(TaskRecord.task_type == request.task_type.value)
                
                if request.status:
                    conditions.append(TaskRecord.status == request.status.value)
                
                if request.priority:
                    conditions.append(TaskRecord.priority == request.priority.value)
                
                # 构建基础查询
                base_query = select(TaskRecord)
                if conditions:
                    base_query = base_query.where(and_(*conditions))
                
                # 获取总数
                count_query = select(func.count()).select_from(base_query.subquery())
                total_result = await session.execute(count_query)
                total = total_result.scalar()
                
                # 构建分页查询
                query = base_query
                
                # 排序
                if request.order_by == "created_at":
                    order_col = TaskRecord.created_at
                elif request.order_by == "priority":
                    order_col = TaskRecord.priority
                elif request.order_by == "status":
                    order_col = TaskRecord.status
                else:
                    order_col = TaskRecord.created_at
                
                if request.order_desc:
                    query = query.order_by(desc(order_col))
                else:
                    query = query.order_by(asc(order_col))
                
                # 分页
                query = query.offset(request.offset).limit(request.limit)
                
                # 执行查询
                result = await session.execute(query)
                records = result.scalars().all()
                
                # 转换为业务模型
                tasks = [TaskModel.from_record(record) for record in records]
                
                logger.info(f"✅ 任务列表查询成功: {len(tasks)}/{total}")
                return tasks, total
                
        except Exception as e:
            logger.error(f"❌ 任务列表查询失败: {e}")
            raise StorageException("Failed to list tasks", e)
    
    async def get_pending_tasks(self, limit: int = 100) -> List[TaskModel]:
        """获取待执行任务列表"""
        try:
            async with self._get_session() as session:
                query = select(TaskRecord).where(
                    TaskRecord.status == TaskStatus.PENDING.value
                ).order_by(
                    desc(TaskRecord.priority),  # 优先级高的在前
                    asc(TaskRecord.created_at)  # 创建时间早的在前
                ).limit(limit)
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                tasks = [TaskModel.from_record(record) for record in records]
                logger.info(f"✅ 获取待执行任务: {len(tasks)} 个")
                return tasks
                
        except Exception as e:
            logger.error(f"❌ 获取待执行任务失败: {e}")
            raise StorageException("Failed to get pending tasks", e)
    
    async def get_running_tasks(self) -> List[TaskModel]:
        """获取正在运行的任务列表"""
        try:
            async with self._get_session() as session:
                query = select(TaskRecord).where(
                    TaskRecord.status == TaskStatus.RUNNING.value
                )
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                tasks = [TaskModel.from_record(record) for record in records]
                logger.info(f"✅ 获取运行中任务: {len(tasks)} 个")
                return tasks
                
        except Exception as e:
            logger.error(f"❌ 获取运行中任务失败: {e}")
            raise StorageException("Failed to get running tasks", e)
    
    async def get_timeout_tasks(self, timeout_threshold: datetime) -> List[TaskModel]:
        """获取超时任务列表"""
        try:
            async with self._get_session() as session:
                query = select(TaskRecord).where(
                    and_(
                        TaskRecord.status == TaskStatus.RUNNING.value,
                        TaskRecord.started_at < timeout_threshold
                    )
                )
                
                result = await session.execute(query)
                records = result.scalars().all()
                
                tasks = [TaskModel.from_record(record) for record in records]
                logger.info(f"✅ 获取超时任务: {len(tasks)} 个")
                return tasks
                
        except Exception as e:
            logger.error(f"❌ 获取超时任务失败: {e}")
            raise StorageException("Failed to get timeout tasks", e)

    async def get_task_statistics(self, time_range: Optional[timedelta] = None) -> TaskStatistics:
        """获取任务统计信息"""
        try:
            async with self._get_session() as session:
                # 基础查询条件
                base_conditions = []
                if time_range:
                    cutoff_time = datetime.utcnow() - time_range
                    base_conditions.append(TaskRecord.created_at >= cutoff_time)

                # 总任务数
                total_query = select(func.count(TaskRecord.id))
                if base_conditions:
                    total_query = total_query.where(and_(*base_conditions))

                total_result = await session.execute(total_query)
                total_tasks = total_result.scalar() or 0

                # 按状态统计
                status_query = select(
                    TaskRecord.status,
                    func.count(TaskRecord.id)
                ).group_by(TaskRecord.status)
                if base_conditions:
                    status_query = status_query.where(and_(*base_conditions))

                status_result = await session.execute(status_query)
                by_status = {status: count for status, count in status_result.fetchall()}

                # 按类型统计
                type_query = select(
                    TaskRecord.task_type,
                    func.count(TaskRecord.id)
                ).group_by(TaskRecord.task_type)
                if base_conditions:
                    type_query = type_query.where(and_(*base_conditions))

                type_result = await session.execute(type_query)
                by_type = {task_type: count for task_type, count in type_result.fetchall()}

                # 按优先级统计
                priority_query = select(
                    TaskRecord.priority,
                    func.count(TaskRecord.id)
                ).group_by(TaskRecord.priority)
                if base_conditions:
                    priority_query = priority_query.where(and_(*base_conditions))

                priority_result = await session.execute(priority_query)
                by_priority = {str(priority): count for priority, count in priority_result.fetchall()}

                # 平均执行时间
                avg_time_query = select(
                    func.avg(
                        func.extract('epoch', TaskRecord.completed_at) -
                        func.extract('epoch', TaskRecord.started_at)
                    )
                ).where(
                    and_(
                        TaskRecord.status == TaskStatus.COMPLETED.value,
                        TaskRecord.started_at.isnot(None),
                        TaskRecord.completed_at.isnot(None),
                        *base_conditions
                    )
                )

                avg_time_result = await session.execute(avg_time_query)
                avg_execution_time = avg_time_result.scalar()

                # 成功率
                completed_count = by_status.get(TaskStatus.COMPLETED.value, 0)
                failed_count = by_status.get(TaskStatus.FAILED.value, 0)
                finished_count = completed_count + failed_count
                success_rate = (completed_count / finished_count * 100) if finished_count > 0 else None

                # 时间范围统计
                now = datetime.utcnow()

                # 最近1小时
                hour_ago = now - timedelta(hours=1)
                hour_query = select(func.count(TaskRecord.id)).where(TaskRecord.created_at >= hour_ago)
                hour_result = await session.execute(hour_query)
                last_hour_tasks = hour_result.scalar() or 0

                # 最近24小时
                day_ago = now - timedelta(days=1)
                day_query = select(func.count(TaskRecord.id)).where(TaskRecord.created_at >= day_ago)
                day_result = await session.execute(day_query)
                last_day_tasks = day_result.scalar() or 0

                # 最近7天
                week_ago = now - timedelta(days=7)
                week_query = select(func.count(TaskRecord.id)).where(TaskRecord.created_at >= week_ago)
                week_result = await session.execute(week_query)
                last_week_tasks = week_result.scalar() or 0

                statistics = TaskStatistics(
                    total_tasks=total_tasks,
                    by_status=by_status,
                    by_type=by_type,
                    by_priority=by_priority,
                    avg_execution_time=avg_execution_time,
                    success_rate=success_rate,
                    last_hour_tasks=last_hour_tasks,
                    last_day_tasks=last_day_tasks,
                    last_week_tasks=last_week_tasks
                )

                logger.info(f"✅ 任务统计查询成功: 总数 {total_tasks}")
                return statistics

        except Exception as e:
            logger.error(f"❌ 任务统计查询失败: {e}")
            raise StorageException("Failed to get task statistics", e)

    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            async with self._get_session() as session:
                stmt = delete(TaskRecord).where(TaskRecord.id == task_id)
                result = await session.execute(stmt)

                if not self._current_session:
                    await session.commit()

                success = result.rowcount > 0
                if success:
                    logger.info(f"✅ 任务删除成功: {task_id}")
                else:
                    logger.warning(f"⚠️ 任务不存在: {task_id}")

                return success

        except Exception as e:
            logger.error(f"❌ 任务删除失败: {task_id} - {e}")
            raise StorageException(f"Failed to delete task: {task_id}", e)

    async def delete_old_tasks(self,
                             older_than: datetime,
                             status_filter: Optional[List[TaskStatus]] = None) -> int:
        """删除旧任务"""
        try:
            async with self._get_session() as session:
                conditions = [TaskRecord.created_at < older_than]

                if status_filter:
                    status_values = [status.value for status in status_filter]
                    conditions.append(TaskRecord.status.in_(status_values))

                stmt = delete(TaskRecord).where(and_(*conditions))
                result = await session.execute(stmt)

                if not self._current_session:
                    await session.commit()

                deleted_count = result.rowcount
                logger.info(f"✅ 删除旧任务: {deleted_count} 个")
                return deleted_count

        except Exception as e:
            logger.error(f"❌ 删除旧任务失败: {e}")
            raise StorageException("Failed to delete old tasks", e)

    async def bulk_update_status(self,
                               task_ids: List[str],
                               status: TaskStatus,
                               error_info: Optional[Dict[str, Any]] = None) -> int:
        """批量更新任务状态"""
        try:
            async with self._get_session() as session:
                update_data = {"status": status.value}
                if error_info:
                    update_data["error_info"] = error_info

                stmt = update(TaskRecord).where(TaskRecord.id.in_(task_ids)).values(**update_data)
                result = await session.execute(stmt)

                if not self._current_session:
                    await session.commit()

                updated_count = result.rowcount
                logger.info(f"✅ 批量更新任务状态: {updated_count} 个 -> {status}")
                return updated_count

        except Exception as e:
            logger.error(f"❌ 批量更新任务状态失败: {e}")
            raise StorageException("Failed to bulk update task status", e)

    async def get_tasks_by_type_and_status(self,
                                         task_type: TaskType,
                                         status: TaskStatus,
                                         limit: int = 100) -> List[TaskModel]:
        """根据类型和状态获取任务"""
        try:
            async with self._get_session() as session:
                query = select(TaskRecord).where(
                    and_(
                        TaskRecord.task_type == task_type.value,
                        TaskRecord.status == status.value
                    )
                ).limit(limit)

                result = await session.execute(query)
                records = result.scalars().all()

                tasks = [TaskModel.from_record(record) for record in records]
                logger.info(f"✅ 按类型状态查询任务: {len(tasks)} 个 ({task_type}, {status})")
                return tasks

        except Exception as e:
            logger.error(f"❌ 按类型状态查询任务失败: {e}")
            raise StorageException("Failed to get tasks by type and status", e)

    async def count_tasks_by_status(self,
                                  status: TaskStatus,
                                  time_range: Optional[timedelta] = None) -> int:
        """按状态统计任务数量"""
        try:
            async with self._get_session() as session:
                conditions = [TaskRecord.status == status.value]

                if time_range:
                    cutoff_time = datetime.utcnow() - time_range
                    conditions.append(TaskRecord.created_at >= cutoff_time)

                query = select(func.count(TaskRecord.id)).where(and_(*conditions))
                result = await session.execute(query)
                count = result.scalar() or 0

                logger.info(f"✅ 按状态统计任务: {count} 个 ({status})")
                return count

        except Exception as e:
            logger.error(f"❌ 按状态统计任务失败: {e}")
            raise StorageException("Failed to count tasks by status", e)

    async def get_task_execution_times(self,
                                     task_type: Optional[TaskType] = None,
                                     limit: int = 1000) -> List[float]:
        """获取任务执行时间列表"""
        try:
            async with self._get_session() as session:
                conditions = [
                    TaskRecord.status == TaskStatus.COMPLETED.value,
                    TaskRecord.started_at.isnot(None),
                    TaskRecord.completed_at.isnot(None)
                ]

                if task_type:
                    conditions.append(TaskRecord.task_type == task_type.value)

                query = select(
                    func.extract('epoch', TaskRecord.completed_at) -
                    func.extract('epoch', TaskRecord.started_at)
                ).where(and_(*conditions)).limit(limit)

                result = await session.execute(query)
                execution_times = [float(time) for time in result.scalars().all() if time is not None]

                logger.info(f"✅ 获取任务执行时间: {len(execution_times)} 个")
                return execution_times

        except Exception as e:
            logger.error(f"❌ 获取任务执行时间失败: {e}")
            raise StorageException("Failed to get task execution times", e)

    # 事务支持
    async def begin_transaction(self):
        """开始事务"""
        if self._current_session:
            raise TransactionError("Transaction already active")

        self._current_session = self.session_factory()
        await self._current_session.begin()
        logger.debug("🔄 事务开始")

    async def commit_transaction(self):
        """提交事务"""
        if not self._current_session:
            raise TransactionError("No active transaction")

        try:
            await self._current_session.commit()
            logger.debug("✅ 事务提交成功")
        finally:
            await self._current_session.close()
            self._current_session = None

    async def rollback_transaction(self):
        """回滚事务"""
        if not self._current_session:
            raise TransactionError("No active transaction")

        try:
            await self._current_session.rollback()
            logger.debug("🔄 事务回滚")
        finally:
            await self._current_session.close()
            self._current_session = None


logger.info("✅ 数据库任务存储实现完成")
