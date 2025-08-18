"""
重试机制测试
"""

import pytest
import asyncio
from datetime import datetime

from app.core.tasks.retry import (
    RetryManager,
    RetryConfig,
    RetryStrategy,
    RetryCondition,
    PredefinedRetryConfigs
)
from app.core.tasks.models import TaskModel, TaskType, TaskStatus


class TestRetryConfig:
    """测试重试配置"""
    
    def test_retry_config_defaults(self):
        """测试重试配置默认值"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.base_delay == 1.0
        assert config.max_delay == 300.0
        assert config.jitter is True
        assert config.condition == RetryCondition.ON_FAILURE
        assert len(config.retryable_exceptions) > 0
        assert config.custom_strategy is None
    
    def test_retry_config_custom(self):
        """测试自定义重试配置"""
        def custom_strategy(retry_count):
            return retry_count * 2.0
        
        config = RetryConfig(
            max_retries=5,
            strategy=RetryStrategy.CUSTOM,
            base_delay=2.0,
            max_delay=600.0,
            jitter=False,
            condition=RetryCondition.ALWAYS,
            custom_strategy=custom_strategy
        )
        
        assert config.max_retries == 5
        assert config.strategy == RetryStrategy.CUSTOM
        assert config.base_delay == 2.0
        assert config.max_delay == 600.0
        assert config.jitter is False
        assert config.condition == RetryCondition.ALWAYS
        assert config.custom_strategy == custom_strategy


class TestRetryManager:
    """测试重试管理器"""
    
    def test_retry_manager_initialization(self):
        """测试重试管理器初始化"""
        manager = RetryManager()
        
        assert len(manager.task_configs) == 0
        assert manager.default_config is not None
        assert len(manager.retry_history) == 0
    
    def test_set_and_get_task_config(self):
        """测试设置和获取任务配置"""
        manager = RetryManager()
        config = RetryConfig(max_retries=5, base_delay=2.0)
        
        # 设置配置
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        # 获取配置
        retrieved_config = manager.get_task_config(TaskType.DOCUMENT_ANALYSIS)
        assert retrieved_config == config
        
        # 获取不存在的配置（应返回默认配置）
        default_config = manager.get_task_config(TaskType.TEST_GENERATION)
        assert default_config == manager.default_config
    
    def test_should_retry_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        manager = RetryManager()
        config = RetryConfig(max_retries=2)
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-retry-1",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=3,  # 超过最大重试次数
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        should_retry = manager.should_retry(task)
        assert should_retry is False
    
    def test_should_retry_never_condition(self):
        """测试从不重试条件"""
        manager = RetryManager()
        config = RetryConfig(condition=RetryCondition.NEVER)
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-retry-2",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=0,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        should_retry = manager.should_retry(task)
        assert should_retry is False
    
    def test_should_retry_always_condition(self):
        """测试总是重试条件"""
        manager = RetryManager()
        config = RetryConfig(condition=RetryCondition.ALWAYS, max_retries=3)
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-retry-3",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=1,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        should_retry = manager.should_retry(task)
        assert should_retry is True
    
    def test_should_retry_on_failure_condition(self):
        """测试失败时重试条件"""
        manager = RetryManager()
        config = RetryConfig(condition=RetryCondition.ON_FAILURE)
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        # 失败任务应该重试
        failed_task = TaskModel(
            task_id="test-retry-4",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=0,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        should_retry = manager.should_retry(failed_task)
        assert should_retry is True
        
        # 完成任务不应该重试
        completed_task = TaskModel(
            task_id="test-retry-5",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.COMPLETED,
            retry_count=0,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        should_retry = manager.should_retry(completed_task)
        assert should_retry is False
    
    def test_should_retry_on_timeout_condition(self):
        """测试超时时重试条件"""
        manager = RetryManager()
        config = RetryConfig(condition=RetryCondition.ON_TIMEOUT)
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        # 超时任务应该重试
        timeout_task = TaskModel(
            task_id="test-retry-6",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.TIMEOUT,
            retry_count=0,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        should_retry = manager.should_retry(timeout_task)
        assert should_retry is True
        
        # 失败任务不应该重试
        failed_task = TaskModel(
            task_id="test-retry-7",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=0,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        should_retry = manager.should_retry(failed_task)
        assert should_retry is False
    
    def test_calculate_delay_fixed(self):
        """测试固定延迟计算"""
        manager = RetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=5.0,
            jitter=False
        )
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-delay-1",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=2,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        delay = manager.calculate_delay(task)
        assert delay == 5.0
    
    def test_calculate_delay_exponential_backoff(self):
        """测试指数退避延迟计算"""
        manager = RetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=2.0,
            jitter=False
        )
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-delay-2",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=3,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        delay = manager.calculate_delay(task)
        expected_delay = 2.0 * (2 ** 3)  # 2.0 * 8 = 16.0
        assert delay == expected_delay
    
    def test_calculate_delay_linear_backoff(self):
        """测试线性退避延迟计算"""
        manager = RetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=3.0,
            jitter=False
        )
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-delay-3",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=2,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        delay = manager.calculate_delay(task)
        expected_delay = 3.0 * (2 + 1)  # 3.0 * 3 = 9.0
        assert delay == expected_delay
    
    def test_calculate_delay_custom_strategy(self):
        """测试自定义策略延迟计算"""
        manager = RetryManager()
        
        def custom_strategy(retry_count):
            return retry_count * 10.0
        
        config = RetryConfig(
            strategy=RetryStrategy.CUSTOM,
            custom_strategy=custom_strategy,
            jitter=False
        )
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-delay-4",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=4,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        delay = manager.calculate_delay(task)
        assert delay == 40.0
    
    def test_calculate_delay_max_delay_limit(self):
        """测试最大延迟限制"""
        manager = RetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=10.0,
            max_delay=50.0,
            jitter=False
        )
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-delay-5",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=10,  # 会产生很大的延迟
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        delay = manager.calculate_delay(task)
        assert delay == 50.0  # 应该被限制在最大延迟
    
    def test_calculate_delay_with_jitter(self):
        """测试带抖动的延迟计算"""
        manager = RetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=10.0,
            jitter=True
        )
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-delay-6",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=1,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        # 多次计算延迟，应该有变化（由于抖动）
        delays = [manager.calculate_delay(task) for _ in range(10)]
        
        # 所有延迟都应该大于基础延迟
        assert all(delay >= 10.0 for delay in delays)
        
        # 应该有变化（不是所有延迟都相同）
        assert len(set(delays)) > 1
    
    async def test_wait_for_retry(self):
        """测试等待重试"""
        manager = RetryManager()
        config = RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=0.1,  # 很短的延迟用于测试
            jitter=False
        )
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, config)
        
        task = TaskModel(
            task_id="test-wait-1",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=TaskStatus.FAILED,
            retry_count=1,
            created_at=datetime.utcnow(),
            input_data={}
        )
        
        start_time = asyncio.get_event_loop().time()
        await manager.wait_for_retry(task)
        end_time = asyncio.get_event_loop().time()
        
        elapsed_time = end_time - start_time
        assert elapsed_time >= 0.1  # 至少等待了指定的时间
        
        # 检查重试历史记录
        history = manager.get_retry_history(task.task_id)
        assert len(history) == 1
        assert history[0]["retry_count"] == 1
        assert history[0]["delay"] == 0.1
    
    def test_retry_history_management(self):
        """测试重试历史管理"""
        manager = RetryManager()
        task_id = "test-history-1"
        
        # 记录多次重试
        for i in range(5):
            manager._record_retry_attempt(task_id, i, i * 1.0)
        
        # 获取历史记录
        history = manager.get_retry_history(task_id)
        assert len(history) == 5
        
        for i, record in enumerate(history):
            assert record["retry_count"] == i
            assert record["delay"] == i * 1.0
            assert "timestamp" in record
        
        # 清理历史记录
        manager.clear_retry_history(task_id)
        history = manager.get_retry_history(task_id)
        assert len(history) == 0
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        manager = RetryManager()
        
        # 设置一些任务配置
        manager.set_task_config(TaskType.DOCUMENT_ANALYSIS, RetryConfig(max_retries=5))
        manager.set_task_config(TaskType.TEST_GENERATION, RetryConfig(max_retries=3))
        
        # 记录一些重试历史
        manager._record_retry_attempt("task1", 1, 2.0)
        manager._record_retry_attempt("task1", 2, 4.0)
        manager._record_retry_attempt("task2", 1, 1.0)
        
        # 获取统计信息
        stats = manager.get_statistics()
        
        assert stats["total_tasks_with_retries"] == 2
        assert stats["total_retry_attempts"] == 3
        assert stats["avg_retries_per_task"] == 1.5
        
        assert "task_type_configs" in stats
        assert "document_analysis" in stats["task_type_configs"]
        assert "test_generation" in stats["task_type_configs"]
        
        assert "default_config" in stats


class TestPredefinedRetryConfigs:
    """测试预定义重试配置"""
    
    def test_fast_retry_config(self):
        """测试快速重试配置"""
        config = PredefinedRetryConfigs.FAST_RETRY
        
        assert config.max_retries == 5
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.jitter is True
    
    def test_standard_retry_config(self):
        """测试标准重试配置"""
        config = PredefinedRetryConfigs.STANDARD_RETRY
        
        assert config.max_retries == 3
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter is True
    
    def test_slow_retry_config(self):
        """测试慢重试配置"""
        config = PredefinedRetryConfigs.SLOW_RETRY
        
        assert config.max_retries == 2
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.base_delay == 5.0
        assert config.max_delay == 300.0
        assert config.jitter is True
    
    def test_network_retry_config(self):
        """测试网络重试配置"""
        config = PredefinedRetryConfigs.NETWORK_RETRY
        
        assert config.max_retries == 5
        assert config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.jitter is True
        assert config.condition == RetryCondition.ON_SPECIFIC_ERROR
        assert ConnectionError in config.retryable_exceptions
        assert TimeoutError in config.retryable_exceptions
    
    def test_no_retry_config(self):
        """测试无重试配置"""
        config = PredefinedRetryConfigs.NO_RETRY
        
        assert config.max_retries == 0
        assert config.condition == RetryCondition.NEVER
