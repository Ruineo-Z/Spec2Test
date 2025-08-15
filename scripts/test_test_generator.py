#!/usr/bin/env python3
"""
测试生成器集成测试

测试测试生成器的各个组件功能。
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.document_analyzer import DocumentAnalyzer
from app.core.test_generator import (
    TestCaseGenerator, PromptBuilder, GenerationConfig,
    TestCaseType, TestCasePriority, TestCase, TestSuite
)


def test_prompt_builder():
    """测试提示词构建器"""
    logger = get_logger("test_prompt_builder")
    logger.info("🧪 测试提示词构建器...")
    
    try:
        # 创建模拟的分析结果和端点
        from app.core.document_analyzer.models import DocumentAnalysisResult, APIEndpoint
        
        analysis_result = DocumentAnalysisResult(
            document_type="openapi_json",
            document_format="json",
            title="测试API",
            version="1.0.0",
            base_url="https://api.test.com"
        )
        
        endpoint = APIEndpoint(
            path="/users",
            method="GET",
            summary="获取用户列表",
            description="获取系统中的用户列表",
            tags=["用户管理"],
            parameters=[
                {
                    "name": "page",
                    "in": "query",
                    "type": "integer",
                    "required": False,
                    "description": "页码"
                }
            ]
        )
        
        config = GenerationConfig()
        
        # 测试提示词构建
        builder = PromptBuilder()
        prompt = builder.build_test_generation_prompt(analysis_result, endpoint, config)
        
        assert len(prompt) > 100, "提示词长度应该大于100字符"
        assert "GET /users" in prompt, "提示词应该包含端点信息"
        assert "测试API" in prompt, "提示词应该包含API名称"
        
        logger.info("✅ 提示词构建器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 提示词构建器测试失败: {e}")
        return False


def test_generation_config():
    """测试生成配置"""
    logger = get_logger("test_generation_config")
    logger.info("🧪 测试生成配置...")
    
    try:
        # 测试默认配置
        config = GenerationConfig()
        assert config.strategy == "comprehensive"
        assert config.include_positive == True
        assert config.max_cases_per_endpoint == 10
        
        # 测试自定义配置
        custom_config = GenerationConfig(
            strategy="focused",
            include_positive=True,
            include_negative=False,
            max_cases_per_endpoint=3
        )
        assert custom_config.strategy == "focused"
        assert custom_config.include_negative == False
        assert custom_config.max_cases_per_endpoint == 3
        
        logger.info("✅ 生成配置测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 生成配置测试失败: {e}")
        return False


def test_test_case_models():
    """测试测试用例数据模型"""
    logger = get_logger("test_test_case_models")
    logger.info("🧪 测试测试用例数据模型...")
    
    try:
        # 测试TestCase模型
        test_case = TestCase(
            case_id="test_001",
            title="测试用例1",
            description="这是一个测试用例",
            case_type=TestCaseType.POSITIVE,
            priority=TestCasePriority.HIGH,
            endpoint_path="/users",
            http_method="GET",
            expected_status_code=200
        )
        
        assert test_case.case_id == "test_001"
        assert test_case.case_type == TestCaseType.POSITIVE
        assert test_case.priority == TestCasePriority.HIGH
        assert test_case.case_identifier == "GET:/users:test_001"
        
        # 测试TestSuite模型
        test_suite = TestSuite(
            suite_id="suite_001",
            name="测试套件1",
            description="这是一个测试套件"
        )
        
        test_suite.add_test_case(test_case)
        assert test_suite.total_cases == 1
        assert len(test_suite.test_cases) == 1
        
        # 测试按类型获取用例
        positive_cases = test_suite.get_cases_by_type(TestCaseType.POSITIVE)
        assert len(positive_cases) == 1
        
        # 测试按端点获取用例
        endpoint_cases = test_suite.get_cases_by_endpoint("/users", "GET")
        assert len(endpoint_cases) == 1
        
        logger.info("✅ 测试用例数据模型测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试用例数据模型测试失败: {e}")
        return False


def test_llm_response_parsing():
    """测试LLM响应解析"""
    logger = get_logger("test_llm_response_parsing")
    logger.info("🧪 测试LLM响应解析...")
    
    try:
        # 模拟LLM响应
        mock_llm_response = {
            "test_cases": [
                {
                    "title": "获取用户列表-正常情况",
                    "description": "验证正常获取用户列表的功能",
                    "case_type": "positive",
                    "priority": "high",
                    "request_data": {
                        "params": {"page": 1, "limit": 10}
                    },
                    "expected_status_code": 200,
                    "assertions": [
                        {
                            "type": "status_code",
                            "expected": 200,
                            "description": "验证状态码为200"
                        }
                    ],
                    "tags": ["smoke"]
                }
            ],
            "summary": "生成了1个测试用例",
            "recommendations": ["建议添加更多边界测试"]
        }
        
        # 创建生成器并测试解析
        generator = TestCaseGenerator()
        
        # 模拟响应对象
        class MockResponse:
            def __init__(self, content):
                self.content = json.dumps(content)
        
        mock_response = MockResponse(mock_llm_response)
        parsed_response = generator._parse_llm_response(mock_response)
        
        assert len(parsed_response.test_cases) == 1
        assert parsed_response.test_cases[0].title == "获取用户列表-正常情况"
        assert parsed_response.test_cases[0].case_type == "positive"
        assert parsed_response.summary == "生成了1个测试用例"
        
        logger.info("✅ LLM响应解析测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM响应解析测试失败: {e}")
        return False


def test_case_conversion():
    """测试用例转换"""
    logger = get_logger("test_case_conversion")
    logger.info("🧪 测试用例转换...")
    
    try:
        from app.core.test_generator.models import LLMTestCase
        from app.core.document_analyzer.models import APIEndpoint
        
        # 创建LLM测试用例
        llm_case = LLMTestCase(
            title="测试用例",
            description="测试描述",
            case_type="positive",
            priority="high",
            request_data={
                "headers": {"Content-Type": "application/json"},
                "params": {"id": 1}
            },
            expected_status_code=200,
            assertions=[
                {
                    "type": "status_code",
                    "expected": 200,
                    "description": "验证状态码"
                }
            ]
        )
        
        # 创建端点
        endpoint = APIEndpoint(
            path="/users/{id}",
            method="GET",
            summary="获取用户详情"
        )
        
        # 创建生成器并转换
        generator = TestCaseGenerator()
        config = GenerationConfig()
        
        test_cases = generator._convert_llm_cases_to_test_cases([llm_case], endpoint, config)
        
        assert len(test_cases) == 1
        test_case = test_cases[0]
        assert test_case.title == "测试用例"
        assert test_case.case_type == TestCaseType.POSITIVE
        assert test_case.priority == TestCasePriority.HIGH
        assert test_case.endpoint_path == "/users/{id}"
        assert test_case.http_method == "GET"
        assert len(test_case.assertions) == 1
        
        logger.info("✅ 用例转换测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 用例转换测试失败: {e}")
        return False


def main():
    """主测试函数"""
    logger = get_logger(__name__)
    
    logger.info("🚀 开始测试生成器集成测试...")
    
    tests = [
        ("生成配置", test_generation_config),
        ("测试用例数据模型", test_test_case_models),
        ("提示词构建器", test_prompt_builder),
        ("LLM响应解析", test_llm_response_parsing),
        ("用例转换", test_case_conversion),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 测试: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        except Exception as e:
            logger.error(f"💥 {test_name} 测试异常: {e}")
    
    logger.info(f"\n📊 测试结果统计:")
    logger.info(f"   总测试数: {total}")
    logger.info(f"   通过数: {passed}")
    logger.info(f"   失败数: {total - passed}")
    logger.info(f"   通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 所有测试通过!")
        return True
    else:
        logger.error("💥 部分测试失败!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
