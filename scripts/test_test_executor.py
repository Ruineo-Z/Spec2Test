#!/usr/bin/env python3
"""
测试执行器单元测试

测试测试执行器的各个组件功能。
"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.test_generator.models import TestCase, TestSuite, TestAssertion
from app.core.test_executor import (
    TestRunner, TestTaskScheduler, ExecutionConfig, TaskScheduleConfig,
    TestExecutionResult, TestSuiteExecutionResult, TaskPriority
)


class TestExecutionConfigTest(unittest.TestCase):
    """测试执行配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = ExecutionConfig()
        
        self.assertIsInstance(config.max_concurrent_tests, int)
        self.assertGreater(config.max_concurrent_tests, 0)
        self.assertIsInstance(config.request_timeout, float)
        self.assertGreater(config.request_timeout, 0)
        self.assertIsInstance(config.verbose, bool)
    
    def test_environment_variable_config(self):
        """测试环境变量配置"""
        with patch.dict('os.environ', {
            'SPEC2TEST_MAX_CONCURRENT_TESTS': '10',
            'SPEC2TEST_REQUEST_TIMEOUT': '45.0',
            'SPEC2TEST_VERBOSE': 'false'
        }):
            config = ExecutionConfig()
            
            self.assertEqual(config.max_concurrent_tests, 10)
            self.assertEqual(config.request_timeout, 45.0)
            self.assertFalse(config.verbose)


class TestRunnerTest(unittest.TestCase):
    """测试运行器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = ExecutionConfig(
            max_concurrent_tests=2,
            request_timeout=5.0,
            verbose=False
        )
        self.runner = TestRunner(self.config)
        
        # 创建测试用例
        self.test_case = TestCase(
            case_id="test_001",
            title="测试用例",
            description="单元测试用例",
            case_type="positive",
            priority="medium",
            endpoint_path="/test",
            http_method="GET",
            expected_status_code=200,
            assertions=[
                TestAssertion(
                    assertion_type="status_code",
                    expected_value=200,
                    description="状态码检查"
                )
            ],
            tags=["test"]
        )
    
    def test_runner_initialization(self):
        """测试运行器初始化"""
        self.assertIsNotNone(self.runner.config)
        self.assertIsNotNone(self.runner.http_client)
        self.assertEqual(self.runner.config.max_concurrent_tests, 2)
    
    @patch('app.core.test_executor.http_client.TestHTTPClient.execute_test_case')
    def test_execute_test_case(self, mock_execute):
        """测试单个测试用例执行"""
        # 模拟HTTP客户端返回
        mock_result = Mock()
        mock_result.status = "passed"
        mock_result.request.url = "http://example.com/test"
        mock_result.request.method = "GET"
        mock_result.request.headers = {}
        mock_result.request.json_data = None
        mock_result.response.status_code = 200
        mock_result.response.headers = {}
        mock_result.response.text = "OK"
        mock_result.response_time = 0.1
        mock_result.assertions = []
        mock_result.error_message = None
        mock_result.end_time = time.time()
        mock_result.duration = 0.1
        
        mock_execute.return_value = mock_result
        
        # 执行测试
        result = self.runner.execute_test_case(self.test_case, "http://example.com")
        
        # 验证结果
        self.assertIsInstance(result, TestExecutionResult)
        self.assertEqual(result.test_id, "test_001")
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.request_url, "http://example.com/test")
        self.assertEqual(result.response_status_code, 200)
    
    def test_execute_test_suite(self):
        """测试测试套件执行"""
        # 创建测试套件
        test_cases = [self.test_case]
        test_suite = TestSuite(
            suite_id="suite_001",
            name="测试套件",
            description="单元测试套件",
            test_cases=test_cases,
            tags=["test"]
        )
        
        # 模拟执行
        with patch.object(self.runner, 'execute_test_case') as mock_execute:
            mock_result = TestExecutionResult(
                test_id="test_001",
                status="passed",
                request_url="http://example.com/test",
                request_method="GET"
            )
            mock_execute.return_value = mock_result
            
            # 执行测试套件
            result = self.runner.execute_test_suite(test_suite, "http://example.com")
            
            # 验证结果
            self.assertIsInstance(result, TestSuiteExecutionResult)
            self.assertEqual(result.suite_id, "suite_001")
            self.assertEqual(result.total_tests, 1)
            self.assertEqual(result.passed_tests, 1)
            self.assertEqual(result.success_rate, 1.0)


class TestTaskSchedulerTest(unittest.TestCase):
    """任务调度器测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.schedule_config = TaskScheduleConfig(
            enable_priority=True,
            worker_threads=1,
            max_queue_size=10
        )
        self.execution_config = ExecutionConfig(
            max_concurrent_tests=1,
            request_timeout=5.0,
            verbose=False
        )
        self.scheduler = TestTaskScheduler(self.schedule_config, self.execution_config)
        
        # 创建测试用例
        self.test_case = TestCase(
            case_id="scheduler_test_001",
            title="调度器测试用例",
            description="调度器单元测试用例",
            case_type="positive",
            priority="medium",
            endpoint_path="/scheduler-test",
            http_method="GET",
            expected_status_code=200,
            assertions=[
                TestAssertion(
                    assertion_type="status_code",
                    expected_value=200,
                    description="状态码检查"
                )
            ],
            tags=["scheduler", "test"]
        )
    
    def tearDown(self):
        """清理测试环境"""
        if self.scheduler.is_running:
            self.scheduler.stop()
    
    def test_scheduler_initialization(self):
        """测试调度器初始化"""
        self.assertIsNotNone(self.scheduler.schedule_config)
        self.assertIsNotNone(self.scheduler.execution_config)
        self.assertIsNotNone(self.scheduler.test_runner)
        self.assertFalse(self.scheduler.is_running)
    
    def test_submit_test_case(self):
        """测试提交测试用例"""
        task_id = self.scheduler.submit_test_case(
            self.test_case, 
            "http://example.com",
            priority=TaskPriority.HIGH
        )
        
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.scheduler.tasks)
        
        # 检查任务状态
        status = self.scheduler.get_task_status(task_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["task_type"], "single_test")
        self.assertEqual(status["priority"], TaskPriority.HIGH)
    
    def test_submit_test_suite(self):
        """测试提交测试套件"""
        test_suite = TestSuite(
            suite_id="scheduler_suite_001",
            name="调度器测试套件",
            description="调度器单元测试套件",
            test_cases=[self.test_case],
            tags=["scheduler", "test"]
        )
        
        task_id = self.scheduler.submit_test_suite(
            test_suite,
            "http://example.com",
            priority=TaskPriority.NORMAL
        )
        
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.scheduler.tasks)
        
        # 检查任务状态
        status = self.scheduler.get_task_status(task_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["task_type"], "test_suite")
        self.assertEqual(status["priority"], TaskPriority.NORMAL)
    
    def test_queue_status(self):
        """测试队列状态"""
        status = self.scheduler.get_queue_status()
        
        self.assertIn("queue_size", status)
        self.assertIn("max_queue_size", status)
        self.assertIn("total_tasks", status)
        self.assertIn("worker_threads", status)
        self.assertIn("is_running", status)
        
        self.assertEqual(status["max_queue_size"], 10)
        self.assertEqual(status["worker_threads"], 1)
        self.assertFalse(status["is_running"])
    
    def test_cancel_task(self):
        """测试取消任务"""
        task_id = self.scheduler.submit_test_case(
            self.test_case,
            "http://example.com"
        )
        
        # 取消任务
        success = self.scheduler.cancel_task(task_id)
        self.assertTrue(success)
        
        # 检查任务状态
        status = self.scheduler.get_task_status(task_id)
        self.assertEqual(status["status"], "cancelled")
    
    def test_callback_system(self):
        """测试回调系统"""
        callback_called = []
        
        def test_callback(task):
            callback_called.append(task.task_id)
        
        # 添加回调
        self.scheduler.add_callback("on_task_start", test_callback)
        
        # 验证回调已添加
        self.assertIn(test_callback, self.scheduler.task_callbacks["on_task_start"])


class TestModelsTest(unittest.TestCase):
    """数据模型测试"""
    
    def test_test_execution_result(self):
        """测试执行结果模型测试"""
        result = TestExecutionResult(
            test_id="model_test_001",
            status="passed",
            request_url="http://example.com/test",
            request_method="GET",
            response_status_code=200,
            response_time=0.1
        )
        
        self.assertEqual(result.test_id, "model_test_001")
        self.assertEqual(result.status, "passed")
        self.assertTrue(result.is_successful)
        self.assertEqual(result.passed_assertions, 0)  # 没有断言
        self.assertEqual(result.failed_assertions, 0)
    
    def test_test_suite_execution_result(self):
        """测试套件执行结果模型测试"""
        suite_result = TestSuiteExecutionResult(
            suite_id="model_suite_001",
            suite_name="模型测试套件"
        )
        
        # 添加测试结果
        test_result = TestExecutionResult(
            test_id="model_test_001",
            status="passed",
            request_url="http://example.com/test",
            request_method="GET"
        )
        
        suite_result.add_test_result(test_result)
        
        self.assertEqual(suite_result.total_tests, 1)
        self.assertEqual(suite_result.passed_tests, 1)
        self.assertEqual(suite_result.success_rate, 1.0)
        self.assertTrue(suite_result.is_all_passed)


def run_tests():
    """运行所有测试"""
    logger = get_logger(__name__)
    
    logger.info("🧪 开始测试执行器单元测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestExecutionConfigTest,
        TestRunnerTest,
        TestTaskSchedulerTest,
        TestModelsTest
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 显示结果
    logger.info(f"测试结果:")
    logger.info(f"  运行测试数: {result.testsRun}")
    logger.info(f"  失败数: {len(result.failures)}")
    logger.info(f"  错误数: {len(result.errors)}")
    logger.info(f"  跳过数: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        logger.error("失败的测试:")
        for test, traceback in result.failures:
            logger.error(f"  {test}: {traceback}")
    
    if result.errors:
        logger.error("错误的测试:")
        for test, traceback in result.errors:
            logger.error(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        logger.info("🎉 所有测试通过!")
    else:
        logger.error("💥 部分测试失败!")
    
    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
