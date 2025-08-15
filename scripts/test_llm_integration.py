#!/usr/bin/env python3
"""
LLM集成测试脚本

测试新的LangChain + Instructor集成LLM功能，包括结构化输出。
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.shared.llm.models import APITestCase, TestSuite, DocumentAnalysis, ValidationResult

logger = get_logger(__name__)


def test_llm_imports():
    """测试LLM模块导入"""
    logger.info("测试LLM模块导入...")
    
    try:
        from app.core.shared.llm import (
            BaseLLMClient, LLMFactory, get_llm_client,
            OllamaLangChainClient, OpenAILangChainClient
        )
        logger.info("✅ LLM模块导入成功")
        return True
    except ImportError as e:
        logger.error(f"❌ LLM模块导入失败: {e}")
        return False


def test_structured_models():
    """测试结构化模型"""
    logger.info("测试结构化模型...")
    
    try:
        # 测试APITestCase模型
        test_case = APITestCase(
            name="测试用户登录",
            description="测试用户登录功能",
            test_type="normal",
            method="POST",
            endpoint="/api/auth/login",
            expected_status_code=200,
            request_body={"username": "test", "password": "123456"},
            assertions=["response.status_code == 200", "response.json().token is not None"]
        )
        logger.info(f"✅ APITestCase模型创建成功: {test_case.name}")
        
        # 测试TestSuite模型
        test_suite = TestSuite(
            name="用户认证测试套件",
            description="测试用户认证相关功能",
            test_cases=[test_case]
        )
        logger.info(f"✅ TestSuite模型创建成功: {test_suite.name}")
        
        # 测试DocumentAnalysis模型
        doc_analysis = DocumentAnalysis(
            document_type="openapi",
            title="用户API文档",
            api_version="1.0.0",
            total_endpoints=5,
            quality_score=8.5
        )
        logger.info(f"✅ DocumentAnalysis模型创建成功: {doc_analysis.title}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 结构化模型测试失败: {e}")
        return False


def test_llm_factory():
    """测试LLM工厂"""
    logger.info("测试LLM工厂...")
    
    try:
        from app.core.shared.llm import LLMFactory
        
        # 测试获取可用提供商
        providers = LLMFactory.get_available_providers()
        logger.info(f"✅ 可用LLM提供商: {providers}")
        
        # 测试缓存信息
        cache_info = LLMFactory.get_cache_info()
        logger.info(f"✅ 缓存信息: {cache_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM工厂测试失败: {e}")
        return False


def test_ollama_client_creation():
    """测试Ollama客户端创建"""
    logger.info("测试Ollama客户端创建...")
    
    try:
        from app.core.shared.llm import LLMFactory
        
        # 测试配置
        config = {
            "base_url": "http://localhost:11434",
            "model": "llama2",
            "use_langchain": True
        }
        
        # 创建客户端（不测试连接，因为可能没有Ollama服务）
        client = LLMFactory.create_client("ollama", config)
        logger.info(f"✅ Ollama客户端创建成功: {client.__class__.__name__}")
        
        # 测试客户端信息
        model_info = client.get_model_info()
        logger.info(f"✅ 模型信息: {model_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ollama客户端创建失败: {e}")
        return False


def test_structured_output_interface():
    """测试结构化输出接口"""
    logger.info("测试结构化输出接口...")
    
    try:
        from app.core.shared.llm import LLMFactory
        from app.core.shared.llm.models import APITestCase
        
        # 创建客户端
        config = {
            "base_url": "http://localhost:11434",
            "model": "llama2",
            "use_langchain": True
        }
        
        client = LLMFactory.create_client("ollama", config)
        
        # 检查是否有结构化输出方法
        if hasattr(client, 'generate_structured'):
            logger.info("✅ 客户端支持结构化输出接口")
            
            # 测试方法签名（不实际调用，因为可能没有服务）
            import inspect
            sig = inspect.signature(client.generate_structured)
            logger.info(f"✅ generate_structured方法签名: {sig}")
            
        else:
            logger.error("❌ 客户端不支持结构化输出接口")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 结构化输出接口测试失败: {e}")
        return False


def test_dependency_availability():
    """测试依赖可用性"""
    logger.info("测试依赖可用性...")
    
    dependencies = [
        ("langchain", "LangChain"),
        ("instructor", "Instructor"),
        ("openai", "OpenAI"),
        ("ollama", "Ollama"),
    ]
    
    available_deps = []
    missing_deps = []
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            available_deps.append(display_name)
            logger.info(f"✅ {display_name} 可用")
        except ImportError:
            missing_deps.append(display_name)
            logger.warning(f"⚠️ {display_name} 不可用")
    
    logger.info(f"可用依赖: {available_deps}")
    if missing_deps:
        logger.warning(f"缺失依赖: {missing_deps}")
        logger.info("请运行: pip install langchain langchain-community instructor openai ollama")
    
    return len(available_deps) > 0


def test_json_serialization():
    """测试JSON序列化"""
    logger.info("测试JSON序列化...")
    
    try:
        from app.core.shared.llm.models import APITestCase, TestSuite
        
        # 创建测试用例
        test_case = APITestCase(
            name="测试API",
            description="测试描述",
            test_type="normal",
            method="GET",
            endpoint="/api/test",
            expected_status_code=200
        )
        
        # 测试JSON序列化
        json_str = test_case.model_dump_json(indent=2)
        logger.info("✅ JSON序列化成功")
        
        # 测试JSON反序列化
        parsed_case = APITestCase.model_validate_json(json_str)
        logger.info("✅ JSON反序列化成功")
        
        # 验证数据一致性
        assert parsed_case.name == test_case.name
        assert parsed_case.method == test_case.method
        logger.info("✅ 数据一致性验证通过")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ JSON序列化测试失败: {e}")
        return False


def main():
    """主函数"""
    try:
        logger.info("🚀 开始LLM集成测试...")
        
        tests = [
            ("依赖可用性", test_dependency_availability),
            ("LLM模块导入", test_llm_imports),
            ("结构化模型", test_structured_models),
            ("LLM工厂", test_llm_factory),
            ("Ollama客户端创建", test_ollama_client_creation),
            ("结构化输出接口", test_structured_output_interface),
            ("JSON序列化", test_json_serialization),
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
            logger.info("🎉 所有LLM集成测试通过！")
        else:
            logger.warning(f"⚠️ {total - passed} 个测试失败")
            
        return passed == total
        
    except Exception as e:
        logger.error(f"💥 LLM集成测试失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
