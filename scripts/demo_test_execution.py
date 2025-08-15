#!/usr/bin/env python3
"""
测试执行演示脚本

演示测试执行器的功能，包括单个测试、批量测试和任务调度。
"""

import sys
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.test_generator.models import TestCase, TestSuite, TestAssertion
from app.core.test_executor import (
    TestRunner, TestTaskScheduler, ExecutionConfig, TaskScheduleConfig, TaskPriority
)


def create_sample_test_case() -> TestCase:
    """创建示例测试用例"""
    return TestCase(
        case_id="demo_test_001",
        title="获取用户信息测试",
        description="测试获取用户信息API",
        case_type="positive",
        priority="medium",
        endpoint_path="/users/1",
        http_method="GET",
        expected_status_code=200,
        request_headers={"Accept": "application/json"},
        request_params=None,
        request_body=None,
        assertions=[
            TestAssertion(
                assertion_type="status_code",
                expected_value=200,
                description="状态码应为200"
            )
        ],
        tags=["api", "users", "get"]
    )


def create_sample_test_suite() -> TestSuite:
    """创建示例测试套件"""
    test_cases = []
    
    # 创建多个测试用例 (使用正确的JSONPlaceholder端点)
    endpoints = [
        ("/users", "GET", "获取用户列表"),
        ("/users/1", "GET", "获取单个用户"),
        ("/posts", "GET", "获取文章列表"),
        ("/posts/1", "GET", "获取单个文章"),
        ("/comments", "GET", "获取评论列表")
    ]
    
    for i, (path, method, title) in enumerate(endpoints, 1):
        test_case = TestCase(
            case_id=f"demo_suite_test_{i:03d}",
            title=title,
            description=f"测试{title}API",
            case_type="positive",
            priority="medium",
            endpoint_path=path,
            http_method=method,
            expected_status_code=200,
            request_headers={"Accept": "application/json"},
            assertions=[
                TestAssertion(
                    assertion_type="status_code",
                    expected_value=200,
                    description="状态码应为200"
                )
            ],
            tags=["api", "demo"]
        )
        test_cases.append(test_case)
    
    return TestSuite(
        suite_id="demo_test_suite",
        name="演示测试套件",
        description="用于演示测试执行器功能的测试套件",
        test_cases=test_cases,
        tags=["demo", "api"]
    )


def demo_single_test_execution():
    """演示单个测试执行"""
    logger = get_logger("demo_single_test")
    
    logger.info("🧪 演示单个测试执行...")
    
    # 创建执行配置
    config = ExecutionConfig(
        max_concurrent_tests=1,
        request_timeout=10.0,
        verbose=True
    )
    
    # 创建测试运行器
    runner = TestRunner(config)
    
    # 创建测试用例
    test_case = create_sample_test_case()
    
    # 执行测试（使用JSONPlaceholder作为测试API）
    base_url = "https://jsonplaceholder.typicode.com"
    
    logger.info(f"执行测试用例: {test_case.title}")
    result = runner.execute_test_case(test_case, base_url)
    
    # 显示结果
    logger.info(f"测试结果:")
    logger.info(f"  测试ID: {result.test_id}")
    logger.info(f"  状态: {result.status}")
    logger.info(f"  请求URL: {result.request_url}")
    logger.info(f"  响应状态码: {result.response_status_code}")
    logger.info(f"  响应时间: {result.response_time:.3f}秒")
    logger.info(f"  是否成功: {result.is_successful}")
    
    if result.assertion_results:
        logger.info(f"  断言结果:")
        for assertion in result.assertion_results:
            status = "✅" if assertion.passed else "❌"
            logger.info(f"    {status} {assertion.assertion_type}: {assertion.message}")
    
    return result


def demo_test_suite_execution():
    """演示测试套件执行"""
    logger = get_logger("demo_test_suite")
    
    logger.info("📦 演示测试套件执行...")
    
    # 创建执行配置（启用并发）
    config = ExecutionConfig(
        max_concurrent_tests=3,
        request_timeout=10.0,
        verbose=True
    )
    
    # 创建测试运行器
    runner = TestRunner(config)
    
    # 创建测试套件
    test_suite = create_sample_test_suite()
    
    # 执行测试套件
    base_url = "https://jsonplaceholder.typicode.com"
    
    logger.info(f"执行测试套件: {test_suite.name} ({len(test_suite.test_cases)}个测试)")
    start_time = time.time()
    result = runner.execute_test_suite(test_suite, base_url)
    execution_time = time.time() - start_time
    
    # 显示结果
    logger.info(f"测试套件执行完成:")
    logger.info(f"  套件名称: {result.suite_name}")
    logger.info(f"  总测试数: {result.total_tests}")
    logger.info(f"  通过: {result.passed_tests}")
    logger.info(f"  失败: {result.failed_tests}")
    logger.info(f"  错误: {result.error_tests}")
    logger.info(f"  成功率: {result.success_rate:.1%}")
    logger.info(f"  总耗时: {result.total_duration:.2f}秒")
    logger.info(f"  实际耗时: {execution_time:.2f}秒")
    
    # 显示详细结果
    logger.info(f"详细测试结果:")
    for test_result in result.test_results:
        status_icon = "✅" if test_result.is_successful else "❌"
        logger.info(f"  {status_icon} {test_result.test_id}: {test_result.status} ({test_result.response_time:.3f}s)")
    
    return result


def demo_task_scheduler():
    """演示任务调度器"""
    logger = get_logger("demo_scheduler")
    
    logger.info("⏰ 演示任务调度器...")
    
    # 创建调度配置
    schedule_config = TaskScheduleConfig(
        enable_priority=True,
        worker_threads=2,
        max_queue_size=50
    )
    
    execution_config = ExecutionConfig(
        max_concurrent_tests=2,
        request_timeout=10.0,
        verbose=False  # 减少日志输出
    )
    
    # 创建任务调度器
    scheduler = TestTaskScheduler(schedule_config, execution_config)
    
    # 添加回调函数
    def on_task_complete(task):
        logger.info(f"任务完成回调: {task.task_id} - {task.status}")
    
    scheduler.add_callback("on_task_complete", on_task_complete)
    
    # 启动调度器
    scheduler.start()
    
    try:
        base_url = "https://jsonplaceholder.typicode.com"
        
        # 提交单个测试任务
        test_case = create_sample_test_case()
        task_id_1 = scheduler.submit_test_case(
            test_case, base_url, priority=TaskPriority.HIGH
        )
        logger.info(f"提交高优先级单个测试任务: {task_id_1}")
        
        # 提交测试套件任务
        test_suite = create_sample_test_suite()
        task_id_2 = scheduler.submit_test_suite(
            test_suite, base_url, priority=TaskPriority.NORMAL
        )
        logger.info(f"提交普通优先级测试套件任务: {task_id_2}")
        
        # 监控任务状态
        task_ids = [task_id_1, task_id_2]
        
        logger.info("监控任务执行状态...")
        while True:
            all_completed = True
            
            for task_id in task_ids:
                status = scheduler.get_task_status(task_id)
                if status and not status["is_completed"]:
                    all_completed = False
                    logger.info(f"任务 {task_id[:8]}... 状态: {status['status']}")
            
            if all_completed:
                break
            
            time.sleep(2)
        
        # 获取任务结果
        logger.info("获取任务执行结果:")
        for task_id in task_ids:
            status = scheduler.get_task_status(task_id)
            result = scheduler.get_task_result(task_id)
            
            if status and result:
                logger.info(f"任务 {task_id[:8]}...:")
                logger.info(f"  状态: {status['status']}")
                logger.info(f"  类型: {result['type']}")
                
                if result['type'] == 'single_test':
                    logger.info(f"  测试状态: {result['status']}")
                    logger.info(f"  耗时: {result['duration']:.3f}秒")
                elif result['type'] == 'test_suite':
                    logger.info(f"  总测试数: {result['total_tests']}")
                    logger.info(f"  通过数: {result['passed_tests']}")
                    logger.info(f"  成功率: {result['success_rate']:.1%}")
                    logger.info(f"  总耗时: {result['total_duration']:.2f}秒")
        
        # 显示队列状态
        queue_status = scheduler.get_queue_status()
        logger.info(f"队列状态: {queue_status}")
        
    finally:
        # 停止调度器
        scheduler.stop()
        logger.info("任务调度器已停止")


def demo_concurrent_performance():
    """演示并发性能对比"""
    logger = get_logger("demo_performance")
    
    logger.info("🚀 演示并发性能对比...")
    
    # 创建测试套件
    test_suite = create_sample_test_suite()
    base_url = "https://jsonplaceholder.typicode.com"
    
    # 串行执行
    logger.info("串行执行测试...")
    serial_config = ExecutionConfig(max_concurrent_tests=1, verbose=False)
    serial_runner = TestRunner(serial_config)
    
    start_time = time.time()
    serial_result = serial_runner.execute_test_suite(test_suite, base_url)
    serial_time = time.time() - start_time
    
    logger.info(f"串行执行结果: {serial_result.success_rate:.1%} 成功率, {serial_time:.2f}秒")
    
    # 并发执行
    logger.info("并发执行测试...")
    concurrent_config = ExecutionConfig(max_concurrent_tests=3, verbose=False)
    concurrent_runner = TestRunner(concurrent_config)
    
    start_time = time.time()
    concurrent_result = concurrent_runner.execute_test_suite(test_suite, base_url)
    concurrent_time = time.time() - start_time
    
    logger.info(f"并发执行结果: {concurrent_result.success_rate:.1%} 成功率, {concurrent_time:.2f}秒")
    
    # 性能对比
    if serial_time > 0:
        speedup = serial_time / concurrent_time
        improvement = (serial_time - concurrent_time) / serial_time * 100
        
        logger.info(f"性能对比:")
        logger.info(f"  串行耗时: {serial_time:.2f}秒")
        logger.info(f"  并发耗时: {concurrent_time:.2f}秒")
        logger.info(f"  性能提升: {speedup:.2f}x ({improvement:.1f}%)")


def main():
    """主函数"""
    logger = get_logger(__name__)
    
    logger.info("🎯 开始测试执行器演示...")
    
    demos = [
        ("单个测试执行", demo_single_test_execution),
        ("测试套件执行", demo_test_suite_execution),
        ("任务调度器", demo_task_scheduler),
        ("并发性能对比", demo_concurrent_performance),
    ]
    
    for demo_name, demo_func in demos:
        logger.info(f"\n{'='*50}")
        logger.info(f"📋 演示: {demo_name}")
        logger.info(f"{'='*50}")
        
        try:
            demo_func()
            logger.info(f"✅ {demo_name} 演示完成")
        except Exception as e:
            logger.error(f"❌ {demo_name} 演示失败: {e}")
        
        logger.info(f"等待3秒后继续...")
        time.sleep(3)
    
    logger.info(f"\n🎉 所有演示完成!")


if __name__ == "__main__":
    main()
