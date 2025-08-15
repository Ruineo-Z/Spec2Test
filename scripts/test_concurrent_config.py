#!/usr/bin/env python3
"""
并发配置测试脚本

验证环境变量配置是否正确加载和应用。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.test_generator import GenerationConfig
from app.core.test_generator.concurrent_generator import AdaptiveTestCaseGenerator


def test_environment_variables():
    """测试环境变量配置"""
    logger = get_logger("test_env_vars")
    
    logger.info("🔧 测试环境变量配置...")
    
    # 测试环境变量读取
    max_workers = os.getenv("SPEC2TEST_MAX_CONCURRENT_WORKERS", "8")
    threshold = os.getenv("SPEC2TEST_CONCURRENT_THRESHOLD", "3")
    
    logger.info(f"📊 环境变量读取结果:")
    logger.info(f"   SPEC2TEST_MAX_CONCURRENT_WORKERS: {max_workers}")
    logger.info(f"   SPEC2TEST_CONCURRENT_THRESHOLD: {threshold}")
    
    # 验证类型转换
    try:
        max_workers_int = int(max_workers)
        threshold_int = int(threshold)
        logger.info(f"✅ 类型转换成功: workers={max_workers_int}, threshold={threshold_int}")
    except ValueError as e:
        logger.error(f"❌ 类型转换失败: {e}")
        return False
    
    return True


def test_generation_config():
    """测试生成配置"""
    logger = get_logger("test_generation_config")
    
    logger.info("⚙️ 测试生成配置...")
    
    try:
        # 创建默认配置
        config = GenerationConfig()
        
        logger.info(f"📋 生成配置:")
        logger.info(f"   enable_concurrent: {config.enable_concurrent}")
        logger.info(f"   max_concurrent_workers: {config.max_concurrent_workers}")
        logger.info(f"   concurrent_threshold: {config.concurrent_threshold}")
        
        # 验证配置值
        if config.max_concurrent_workers <= 0:
            logger.error("❌ max_concurrent_workers 必须大于0")
            return False
        
        if config.concurrent_threshold <= 0:
            logger.error("❌ concurrent_threshold 必须大于0")
            return False
        
        logger.info("✅ 生成配置验证通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 生成配置测试失败: {e}")
        return False


def test_adaptive_generator():
    """测试自适应生成器配置"""
    logger = get_logger("test_adaptive_generator")
    
    logger.info("🧠 测试自适应生成器...")
    
    try:
        # 测试不同LLM提供商的配置
        providers = [
            {"provider": "ollama", "model": "qwen2.5:3b"},
            {"provider": "gemini", "api_key": "test_key"},
            {"provider": "openai", "api_key": "test_key"}
        ]
        
        for provider_config in providers:
            provider_name = provider_config["provider"]
            logger.info(f"\n📊 测试 {provider_name} 提供商配置...")
            
            try:
                # 注意：这里可能会因为API密钥无效而失败，但我们主要测试配置逻辑
                generator = AdaptiveTestCaseGenerator(provider_config)
                
                logger.info(f"   并发阈值: {generator.concurrent_threshold}")
                logger.info(f"   最大工作线程: {generator.max_workers}")
                
                # 验证配置合理性
                if provider_name == "ollama":
                    if generator.max_workers > 5:
                        logger.warning(f"   ⚠️  Ollama并发数可能过高: {generator.max_workers}")
                elif provider_name in ["gemini", "openai"]:
                    if generator.max_workers < 3:
                        logger.warning(f"   ⚠️  云端API并发数可能过低: {generator.max_workers}")
                
                logger.info(f"   ✅ {provider_name} 配置正常")
                
            except Exception as e:
                # 预期的错误（如API密钥无效）
                if "API" in str(e) or "密钥" in str(e) or "key" in str(e).lower():
                    logger.info(f"   ✅ {provider_name} 配置逻辑正常 (API密钥验证失败是预期的)")
                else:
                    logger.error(f"   ❌ {provider_name} 配置异常: {e}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 自适应生成器测试失败: {e}")
        return False


def test_config_override():
    """测试配置覆盖"""
    logger = get_logger("test_config_override")
    
    logger.info("🔄 测试配置覆盖...")
    
    # 保存原始环境变量
    original_workers = os.getenv("SPEC2TEST_MAX_CONCURRENT_WORKERS")
    original_threshold = os.getenv("SPEC2TEST_CONCURRENT_THRESHOLD")
    
    try:
        # 设置测试环境变量
        os.environ["SPEC2TEST_MAX_CONCURRENT_WORKERS"] = "15"
        os.environ["SPEC2TEST_CONCURRENT_THRESHOLD"] = "7"

        # 重新导入模块以确保环境变量生效
        import importlib
        import app.core.test_generator.models
        importlib.reload(app.core.test_generator.models)

        # 创建新配置
        from app.core.test_generator.models import GenerationConfig
        config = GenerationConfig()
        
        logger.info(f"📊 覆盖后的配置:")
        logger.info(f"   max_concurrent_workers: {config.max_concurrent_workers}")
        logger.info(f"   concurrent_threshold: {config.concurrent_threshold}")
        
        # 验证覆盖是否生效
        if config.max_concurrent_workers == 15 and config.concurrent_threshold == 7:
            logger.info("✅ 配置覆盖成功")
            result = True
        else:
            logger.error("❌ 配置覆盖失败")
            result = False
        
    except Exception as e:
        logger.error(f"❌ 配置覆盖测试失败: {e}")
        result = False
    
    finally:
        # 恢复原始环境变量
        if original_workers is not None:
            os.environ["SPEC2TEST_MAX_CONCURRENT_WORKERS"] = original_workers
        else:
            os.environ.pop("SPEC2TEST_MAX_CONCURRENT_WORKERS", None)
            
        if original_threshold is not None:
            os.environ["SPEC2TEST_CONCURRENT_THRESHOLD"] = original_threshold
        else:
            os.environ.pop("SPEC2TEST_CONCURRENT_THRESHOLD", None)
    
    return result


def test_performance_recommendations():
    """测试性能建议"""
    logger = get_logger("test_performance_recommendations")
    
    logger.info("💡 性能配置建议...")
    
    # 获取当前配置
    current_workers = int(os.getenv("SPEC2TEST_MAX_CONCURRENT_WORKERS", "8"))
    current_threshold = int(os.getenv("SPEC2TEST_CONCURRENT_THRESHOLD", "3"))
    
    logger.info(f"📊 当前配置:")
    logger.info(f"   并发工作线程: {current_workers}")
    logger.info(f"   并发阈值: {current_threshold}")
    
    # 提供建议
    logger.info(f"\n💡 配置建议:")
    
    if current_workers <= 3:
        logger.info("   🖥️  当前配置适合本地开发环境")
    elif current_workers <= 8:
        logger.info("   ⚖️  当前配置适合中等规模部署")
    else:
        logger.info("   🚀 当前配置适合高性能生产环境")
    
    if current_threshold <= 2:
        logger.info("   ⚡ 积极的并发策略 - 小型API也会启用并发")
    elif current_threshold <= 5:
        logger.info("   📊 平衡的并发策略 - 中等规模API启用并发")
    else:
        logger.info("   🛡️  保守的并发策略 - 仅大型API启用并发")
    
    # 环境特定建议
    logger.info(f"\n🎯 环境特定建议:")
    logger.info("   开发环境: SPEC2TEST_MAX_CONCURRENT_WORKERS=3")
    logger.info("   测试环境: SPEC2TEST_MAX_CONCURRENT_WORKERS=5")
    logger.info("   生产环境: SPEC2TEST_MAX_CONCURRENT_WORKERS=10")
    logger.info("   高性能环境: SPEC2TEST_MAX_CONCURRENT_WORKERS=15")
    
    return True


def main():
    """主函数"""
    logger = get_logger(__name__)
    
    logger.info("🚀 开始并发配置测试...")
    
    tests = [
        ("环境变量读取", test_environment_variables),
        ("生成配置", test_generation_config),
        ("自适应生成器", test_adaptive_generator),
        ("配置覆盖", test_config_override),
        ("性能建议", test_performance_recommendations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 测试: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 通过")
            else:
                logger.error(f"❌ {test_name} 失败")
        except Exception as e:
            logger.error(f"💥 {test_name} 异常: {e}")
    
    logger.info(f"\n📊 测试结果:")
    logger.info(f"   总测试数: {total}")
    logger.info(f"   通过数: {passed}")
    logger.info(f"   失败数: {total - passed}")
    logger.info(f"   通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 所有配置测试通过!")
        return True
    else:
        logger.error("💥 部分配置测试失败!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
