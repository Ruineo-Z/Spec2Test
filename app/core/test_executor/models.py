"""
测试执行器数据模型

定义测试执行过程中使用的数据结构。
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    """测试状态枚举"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    PASSED = "passed"        # 通过
    FAILED = "failed"        # 失败
    ERROR = "error"          # 错误
    SKIPPED = "skipped"      # 跳过
    TIMEOUT = "timeout"      # 超时


class AssertionResult(BaseModel):
    """断言结果"""
    assertion_type: str = Field(description="断言类型")
    expected: Any = Field(description="期望值")
    actual: Any = Field(description="实际值")
    passed: bool = Field(description="是否通过")
    message: str = Field(description="断言消息")
    
    class Config:
        arbitrary_types_allowed = True


class TestExecutionResult(BaseModel):
    """测试执行结果"""
    test_id: str = Field(description="测试ID")
    status: TestStatus = Field(description="执行状态")
    
    # 请求信息
    request_url: str = Field(description="请求URL")
    request_method: str = Field(description="请求方法")
    request_headers: Optional[Dict[str, str]] = Field(default=None, description="请求头")
    request_body: Optional[str] = Field(default=None, description="请求体")
    
    # 响应信息
    response_status_code: Optional[int] = Field(default=None, description="响应状态码")
    response_headers: Optional[Dict[str, str]] = Field(default=None, description="响应头")
    response_body: Optional[str] = Field(default=None, description="响应体")
    response_time: Optional[float] = Field(default=None, description="响应时间(秒)")
    
    # 断言结果
    assertion_results: List[AssertionResult] = Field(default_factory=list, description="断言结果列表")
    
    # 错误信息
    error_message: Optional[str] = Field(default=None, description="错误消息")
    error_traceback: Optional[str] = Field(default=None, description="错误堆栈")
    
    # 执行信息
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    duration: Optional[float] = Field(default=None, description="执行时长(秒)")
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
    
    @property
    def is_successful(self) -> bool:
        """是否执行成功"""
        return self.status == TestStatus.PASSED
    
    @property
    def passed_assertions(self) -> int:
        """通过的断言数量"""
        return sum(1 for assertion in self.assertion_results if assertion.passed)
    
    @property
    def failed_assertions(self) -> int:
        """失败的断言数量"""
        return sum(1 for assertion in self.assertion_results if not assertion.passed)


class TestSuiteExecutionResult(BaseModel):
    """测试套件执行结果"""
    suite_id: str = Field(description="套件ID")
    suite_name: str = Field(description="套件名称")
    
    # 执行结果
    test_results: List[TestExecutionResult] = Field(default_factory=list, description="测试结果列表")
    
    # 统计信息
    total_tests: int = Field(default=0, description="总测试数")
    passed_tests: int = Field(default=0, description="通过测试数")
    failed_tests: int = Field(default=0, description="失败测试数")
    error_tests: int = Field(default=0, description="错误测试数")
    skipped_tests: int = Field(default=0, description="跳过测试数")
    
    # 执行信息
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    total_duration: Optional[float] = Field(default=None, description="总执行时长(秒)")
    
    class Config:
        arbitrary_types_allowed = True
    
    def add_test_result(self, result: TestExecutionResult):
        """添加测试结果"""
        self.test_results.append(result)
        self.total_tests = len(self.test_results)
        
        # 更新统计
        self._update_statistics()
    
    def _update_statistics(self):
        """更新统计信息"""
        self.passed_tests = sum(1 for r in self.test_results if r.status == TestStatus.PASSED)
        self.failed_tests = sum(1 for r in self.test_results if r.status == TestStatus.FAILED)
        self.error_tests = sum(1 for r in self.test_results if r.status == TestStatus.ERROR)
        self.skipped_tests = sum(1 for r in self.test_results if r.status == TestStatus.SKIPPED)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests
    
    @property
    def is_all_passed(self) -> bool:
        """是否全部通过"""
        return self.total_tests > 0 and self.passed_tests == self.total_tests


class ExecutionConfig(BaseModel):
    """执行配置"""
    # 并发配置
    max_concurrent_tests: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_MAX_CONCURRENT_TESTS", "5")),
        description="最大并发测试数"
    )
    
    # 超时配置
    request_timeout: float = Field(
        default_factory=lambda: float(os.getenv("SPEC2TEST_REQUEST_TIMEOUT", "30.0")),
        description="请求超时时间(秒)"
    )
    test_timeout: float = Field(
        default_factory=lambda: float(os.getenv("SPEC2TEST_TEST_TIMEOUT", "60.0")),
        description="单个测试超时时间(秒)"
    )
    
    # 重试配置
    max_retries: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_MAX_RETRIES", "3")),
        description="最大重试次数"
    )
    retry_delay: float = Field(
        default_factory=lambda: float(os.getenv("SPEC2TEST_RETRY_DELAY", "1.0")),
        description="重试延迟(秒)"
    )
    
    # 输出配置
    verbose: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_VERBOSE", "true").lower() == "true",
        description="详细输出"
    )
    save_responses: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_SAVE_RESPONSES", "true").lower() == "true",
        description="保存响应内容"
    )
    
    # 验证配置
    verify_ssl: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_VERIFY_SSL", "true").lower() == "true",
        description="验证SSL证书"
    )
    follow_redirects: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_FOLLOW_REDIRECTS", "true").lower() == "true",
        description="跟随重定向"
    )
    
    class Config:
        arbitrary_types_allowed = True


class TaskScheduleConfig(BaseModel):
    """任务调度配置"""
    # 调度策略
    schedule_strategy: str = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_SCHEDULE_STRATEGY", "immediate"),
        description="调度策略: immediate, delayed, cron"
    )
    
    # 优先级配置
    enable_priority: bool = Field(
        default_factory=lambda: os.getenv("SPEC2TEST_ENABLE_PRIORITY", "false").lower() == "true",
        description="启用优先级调度"
    )
    
    # 队列配置
    max_queue_size: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_MAX_QUEUE_SIZE", "100")),
        description="最大队列大小"
    )
    
    # 工作线程配置
    worker_threads: int = Field(
        default_factory=lambda: int(os.getenv("SPEC2TEST_WORKER_THREADS", "3")),
        description="工作线程数"
    )
    
    class Config:
        arbitrary_types_allowed = True


class TestTask(BaseModel):
    """测试任务"""
    task_id: str = Field(description="任务ID")
    task_type: str = Field(description="任务类型: single_test, test_suite")
    
    # 任务数据
    test_data: Dict[str, Any] = Field(description="测试数据")
    base_url: Optional[str] = Field(default=None, description="基础URL")
    
    # 调度信息
    priority: int = Field(default=0, description="优先级，数字越大优先级越高")
    scheduled_at: Optional[datetime] = Field(default=None, description="计划执行时间")
    
    # 状态信息
    status: str = Field(default="pending", description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    
    # 结果信息
    result: Optional[Dict[str, Any]] = Field(default=None, description="执行结果")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    
    class Config:
        arbitrary_types_allowed = True
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status in ["completed", "failed", "error"]
    
    @property
    def is_successful(self) -> bool:
        """是否成功"""
        return self.status == "completed" and self.result is not None
