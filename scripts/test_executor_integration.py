#!/usr/bin/env python3
"""
测试执行器集成测试脚本

测试测试执行器HTTP客户端的功能和集成。
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.test_executor import (
    TestHTTPClient, TestRequest, TestResult, TestAssertion,
    TestStatus, AssertionType
)

logger = get_logger(__name__)


def test_executor_imports():
    """测试测试执行器模块导入"""
    logger.info("测试测试执行器模块导入...")
    
    try:
        from app.core.test_executor import (
            TestHTTPClient, TestRequest, TestResult, TestAssertion,
            TestStatus, AssertionType
        )
        logger.info("✅ 测试执行器模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ 测试执行器模块导入失败: {e}")
        return False


def test_data_structures():
    """测试数据结构"""
    logger.info("测试数据结构...")
    
    try:
        # 测试TestRequest
        test_request = TestRequest(
            method="POST",
            url="/api/users",
            headers={"Content-Type": "application/json"},
            json_data={"name": "test", "email": "test@example.com"}
        )
        assert test_request.method == "POST"
        assert test_request.url == "/api/users"
        logger.info("✅ TestRequest创建成功")
        
        # 测试TestAssertion
        assertion = TestAssertion(
            type=AssertionType.STATUS_CODE,
            expected=201
        )
        assert assertion.type == AssertionType.STATUS_CODE
        assert assertion.expected == 201
        logger.info("✅ TestAssertion创建成功")
        
        # 测试TestResult
        result = TestResult(
            test_id="test_001",
            status=TestStatus.PENDING,
            request=test_request
        )
        assert result.test_id == "test_001"
        assert result.status == TestStatus.PENDING
        logger.info("✅ TestResult创建成功")
        
        # 测试序列化
        request_dict = test_request.to_dict()
        assert "method" in request_dict
        assert "url" in request_dict
        logger.info("✅ 数据结构序列化成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据结构测试失败: {e}")
        return False


def test_http_client_creation():
    """测试HTTP客户端创建"""
    logger.info("测试HTTP客户端创建...")
    
    try:
        # 创建测试HTTP客户端
        client = TestHTTPClient(
            base_url="https://httpbin.org",
            config={
                "default_timeout": 10.0,
                "max_retries": 2,
                "verify_ssl": True
            }
        )
        
        assert client.base_url == "https://httpbin.org"
        assert client.default_timeout == 10.0
        assert client.max_retries == 2
        logger.info("✅ 测试HTTP客户端创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试HTTP客户端创建失败: {e}")
        return False


def test_simple_request_execution():
    """测试简单请求执行"""
    logger.info("测试简单请求执行...")
    
    try:
        # 创建客户端
        client = TestHTTPClient(base_url="https://httpbin.org")
        
        # 创建测试请求
        test_request = TestRequest(
            method="GET",
            url="/get",
            params={"test": "value"}
        )
        
        # 创建断言
        assertions = [
            TestAssertion(type=AssertionType.STATUS_CODE, expected=200),
            TestAssertion(type=AssertionType.RESPONSE_TIME, expected=5.0)
        ]
        
        # 执行测试用例
        result = client.execute_test_case(test_request, assertions, "test_get")
        
        # 验证结果
        assert result.test_id == "test_get"
        assert result.response is not None
        assert result.execution_time is not None
        
        logger.info(f"✅ 简单请求执行成功: 状态 {result.status.value}")
        logger.info(f"   响应状态码: {result.response.status_code if result.response else 'None'}")
        logger.info(f"   执行时间: {result.execution_time:.3f}s")
        logger.info(f"   断言结果: {len([a for a in result.assertions if a.passed])}/{len(result.assertions)} 通过")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 简单请求执行失败: {e}")
        return False


def test_post_request_with_json():
    """测试POST请求和JSON数据"""
    logger.info("测试POST请求和JSON数据...")
    
    try:
        client = TestHTTPClient(base_url="https://httpbin.org")
        
        # 创建POST请求
        test_request = TestRequest(
            method="POST",
            url="/post",
            headers={"Content-Type": "application/json"},
            json_data={"name": "测试用户", "age": 25}
        )
        
        # 创建断言
        assertions = [
            TestAssertion(type=AssertionType.STATUS_CODE, expected=200),
            TestAssertion(type=AssertionType.BODY_CONTAINS, expected="测试用户"),
            TestAssertion(type=AssertionType.HEADER_EXISTS, expected="Content-Type")
        ]
        
        # 执行测试
        result = client.execute_test_case(test_request, assertions, "test_post_json")
        
        logger.info(f"✅ POST请求执行成功: 状态 {result.status.value}")
        
        # 显示断言结果
        for assertion in result.assertions:
            status = "✅" if assertion.passed else "❌"
            logger.info(f"   {status} {assertion.message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ POST请求测试失败: {e}")
        return False


def test_assertion_types():
    """测试不同类型的断言"""
    logger.info("测试不同类型的断言...")
    
    try:
        client = TestHTTPClient(base_url="https://httpbin.org")
        
        # 创建请求
        test_request = TestRequest(method="GET", url="/json")
        
        # 创建多种类型的断言
        assertions = [
            TestAssertion(type=AssertionType.STATUS_CODE, expected=200),
            TestAssertion(type=AssertionType.RESPONSE_TIME, expected=10.0),
            TestAssertion(type=AssertionType.HEADER_EXISTS, expected="Content-Type"),
            TestAssertion(type=AssertionType.BODY_CONTAINS, expected="slideshow"),
            TestAssertion(type=AssertionType.REGEX_MATCH, expected=r'"title":\s*"[^"]*"')
        ]
        
        # 执行测试
        result = client.execute_test_case(test_request, assertions, "test_assertions")
        
        logger.info(f"✅ 断言测试执行完成: 状态 {result.status.value}")
        
        # 统计断言结果
        passed_count = sum(1 for a in result.assertions if a.passed)
        total_count = len(result.assertions)
        
        logger.info(f"   断言统计: {passed_count}/{total_count} 通过")
        
        for assertion in result.assertions:
            status = "✅" if assertion.passed else "❌"
            logger.info(f"   {status} {assertion.type.value}: {assertion.message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 断言测试失败: {e}")
        return False


def test_test_suite_execution():
    """测试测试套件执行"""
    logger.info("测试测试套件执行...")
    
    try:
        client = TestHTTPClient(base_url="https://httpbin.org")
        
        # 创建测试套件
        test_suite = [
            {
                "id": "test_get_status",
                "request": {
                    "method": "GET",
                    "url": "/status/200"
                },
                "assertions": [
                    {"type": "status_code", "expected": 200}
                ]
            },
            {
                "id": "test_get_json",
                "request": {
                    "method": "GET",
                    "url": "/json"
                },
                "assertions": [
                    {"type": "status_code", "expected": 200},
                    {"type": "body_contains", "expected": "slideshow"}
                ]
            },
            {
                "id": "test_post_data",
                "request": {
                    "method": "POST",
                    "url": "/post",
                    "json": {"test": "data"}
                },
                "assertions": [
                    {"type": "status_code", "expected": 200},
                    {"type": "body_contains", "expected": "test"}
                ]
            }
        ]
        
        # 执行测试套件
        results = client.execute_test_suite(test_suite)
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if r.failed)
        
        logger.info(f"✅ 测试套件执行完成:")
        logger.info(f"   总计: {total} 个测试")
        logger.info(f"   通过: {passed} 个")
        logger.info(f"   失败: {failed} 个")
        
        # 显示每个测试的结果
        for result in results:
            status_icon = "✅" if result.passed else "❌"
            logger.info(f"   {status_icon} {result.test_id}: {result.status.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试套件执行失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    logger.info("测试错误处理...")
    
    try:
        client = TestHTTPClient(base_url="https://httpbin.org")
        
        # 测试无效URL
        test_request = TestRequest(method="GET", url="/status/404")
        assertions = [TestAssertion(type=AssertionType.STATUS_CODE, expected=200)]  # 故意错误的断言
        
        result = client.execute_test_case(test_request, assertions, "test_404")
        
        # 验证错误处理
        assert result.status == TestStatus.FAILED  # 应该失败
        assert not result.passed
        
        logger.info("✅ 错误处理测试成功")
        logger.info(f"   测试状态: {result.status.value}")
        logger.info(f"   断言失败: {result.assertions[0].message}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 错误处理测试失败: {e}")
        return False


def test_performance_stats():
    """测试性能统计"""
    logger.info("测试性能统计...")
    
    try:
        client = TestHTTPClient(base_url="https://httpbin.org")
        
        # 执行几个请求
        for i in range(3):
            test_request = TestRequest(method="GET", url=f"/delay/{i+1}")
            assertions = [TestAssertion(type=AssertionType.STATUS_CODE, expected=200)]
            client.execute_test_case(test_request, assertions, f"perf_test_{i+1}")
        
        # 获取性能统计
        stats = client.get_performance_stats()
        
        logger.info("✅ 性能统计获取成功")
        logger.info(f"   统计信息: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 性能统计测试失败: {e}")
        return False


def main():
    """主函数"""
    try:
        logger.info("🚀 开始测试执行器集成测试...")
        
        tests = [
            ("测试执行器模块导入", test_executor_imports),
            ("数据结构", test_data_structures),
            ("HTTP客户端创建", test_http_client_creation),
            ("简单请求执行", test_simple_request_execution),
            ("POST请求和JSON", test_post_request_with_json),
            ("断言类型", test_assertion_types),
            ("测试套件执行", test_test_suite_execution),
            ("错误处理", test_error_handling),
            ("性能统计", test_performance_stats),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- 测试: {test_name} ---")
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name} 通过")
                else:
                    logger.error(f"❌ {test_name} 失败")
            except Exception as e:
                logger.error(f"💥 {test_name} 异常: {e}")
        
        logger.info(f"\n🎯 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            logger.info("🎉 所有测试执行器测试通过！")
        else:
            logger.warning(f"⚠️ {total - passed} 个测试失败")
            
        return passed == total
        
    except Exception as e:
        logger.error(f"💥 测试执行器测试失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
