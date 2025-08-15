#!/usr/bin/env python3
"""
并发性能测试脚本

测试串行vs并发生成的性能差异。
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.document_analyzer import DocumentAnalyzer
from app.core.test_generator import TestCaseGenerator, GenerationConfig
from app.core.test_generator.concurrent_generator import (
    ConcurrentTestCaseGenerator, 
    AdaptiveTestCaseGenerator,
    PerformanceComparator
)


def test_concurrent_performance():
    """测试并发性能"""
    logger = get_logger(__name__)
    
    logger.info("🚀 开始并发性能测试...")
    
    try:
        # 1. 分析示例API文档
        analyzer = DocumentAnalyzer()
        api_file = project_root / "examples" / "sample_api.json"
        
        logger.info(f"📄 分析文档: {api_file}")
        analysis_result = analyzer.analyze_file(str(api_file))
        
        logger.info(f"📊 分析结果: {len(analysis_result.endpoints)}个端点")
        for i, endpoint in enumerate(analysis_result.endpoints, 1):
            logger.info(f"   {i}. {endpoint.method.upper()} {endpoint.path}")
        
        # 2. 配置生成参数
        config = GenerationConfig(
            include_positive=True,
            include_negative=True,
            include_boundary=False,
            max_cases_per_endpoint=3,
            enable_concurrent=True,
            max_concurrent_workers=3
        )
        
        # 3. 串行生成测试
        logger.info("\n🔄 测试串行生成...")
        serial_generator = TestCaseGenerator()
        
        serial_start = time.time()
        serial_result = serial_generator.generate_test_cases(analysis_result, config)
        serial_duration = time.time() - serial_start
        
        logger.info(f"串行生成结果:")
        logger.info(f"   ⏱️  耗时: {serial_duration:.2f}秒")
        logger.info(f"   📊 用例数: {serial_result.total_cases_generated}")
        logger.info(f"   🤖 LLM调用: {serial_result.llm_calls_count}次")
        logger.info(f"   ✅ 成功: {serial_result.success}")
        
        # 4. 并发生成测试
        logger.info("\n⚡ 测试并发生成...")
        concurrent_generator = ConcurrentTestCaseGenerator(max_workers=3)
        
        concurrent_start = time.time()
        concurrent_result = concurrent_generator.generate_test_cases_concurrent(analysis_result, config)
        concurrent_duration = time.time() - concurrent_start
        
        logger.info(f"并发生成结果:")
        logger.info(f"   ⏱️  耗时: {concurrent_duration:.2f}秒")
        logger.info(f"   📊 用例数: {concurrent_result.total_cases_generated}")
        logger.info(f"   🤖 LLM调用: {concurrent_result.llm_calls_count}次")
        logger.info(f"   ✅ 成功: {concurrent_result.success}")
        
        # 5. 性能对比
        if serial_duration > 0:
            improvement = (serial_duration - concurrent_duration) / serial_duration * 100
            speedup = serial_duration / concurrent_duration if concurrent_duration > 0 else float('inf')
            
            logger.info(f"\n📈 性能对比:")
            logger.info(f"   ⚡ 性能提升: {improvement:.1f}%")
            logger.info(f"   🚀 加速比: {speedup:.2f}x")
            logger.info(f"   ⏰ 时间节省: {serial_duration - concurrent_duration:.2f}秒")
            
            # 判断并发效果
            if improvement > 30:
                logger.info("   🎉 并发效果显著！")
            elif improvement > 10:
                logger.info("   👍 并发效果良好")
            elif improvement > 0:
                logger.info("   📊 并发有轻微提升")
            else:
                logger.info("   ⚠️  并发未带来性能提升")
        
        # 6. 测试自适应生成器
        logger.info("\n🧠 测试自适应生成器...")
        adaptive_generator = AdaptiveTestCaseGenerator()
        
        adaptive_start = time.time()
        adaptive_result = adaptive_generator.generate_test_cases_adaptive(analysis_result, config)
        adaptive_duration = time.time() - adaptive_start
        
        logger.info(f"自适应生成结果:")
        logger.info(f"   ⏱️  耗时: {adaptive_duration:.2f}秒")
        logger.info(f"   📊 用例数: {adaptive_result.total_cases_generated}")
        logger.info(f"   ✅ 成功: {adaptive_result.success}")
        
        # 7. 质量验证
        logger.info(f"\n🔍 质量验证:")
        
        # 检查用例数量一致性
        if (serial_result.total_cases_generated == concurrent_result.total_cases_generated == 
            adaptive_result.total_cases_generated):
            logger.info("   ✅ 用例数量一致")
        else:
            logger.info("   ⚠️  用例数量不一致")
            logger.info(f"      串行: {serial_result.total_cases_generated}")
            logger.info(f"      并发: {concurrent_result.total_cases_generated}")
            logger.info(f"      自适应: {adaptive_result.total_cases_generated}")
        
        # 检查成功率
        success_count = sum([serial_result.success, concurrent_result.success, adaptive_result.success])
        logger.info(f"   📊 成功率: {success_count}/3 ({success_count/3*100:.1f}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 并发性能测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_scalability():
    """测试可扩展性（模拟更多端点）"""
    logger = get_logger("test_scalability")
    
    logger.info("📈 开始可扩展性测试...")
    
    try:
        # 分析文档
        analyzer = DocumentAnalyzer()
        api_file = project_root / "examples" / "sample_api.json"
        analysis_result = analyzer.analyze_file(str(api_file))
        
        # 模拟更多端点（复制现有端点）
        original_endpoints = analysis_result.endpoints.copy()
        
        # 测试不同端点数量的性能
        endpoint_counts = [3, 6, 9]  # 3, 6, 9个端点
        
        for count in endpoint_counts:
            logger.info(f"\n🔢 测试 {count} 个端点...")
            
            # 复制端点到指定数量
            analysis_result.endpoints = original_endpoints * (count // len(original_endpoints))
            analysis_result.endpoints = analysis_result.endpoints[:count]
            
            config = GenerationConfig(
                include_positive=True,
                include_negative=False,  # 简化测试
                max_cases_per_endpoint=2,  # 减少每个端点的用例数
                max_concurrent_workers=3
            )
            
            # 串行测试
            serial_generator = TestCaseGenerator()
            serial_start = time.time()
            serial_result = serial_generator.generate_test_cases(analysis_result, config)
            serial_duration = time.time() - serial_start
            
            # 并发测试
            concurrent_generator = ConcurrentTestCaseGenerator(max_workers=3)
            concurrent_start = time.time()
            concurrent_result = concurrent_generator.generate_test_cases_concurrent(analysis_result, config)
            concurrent_duration = time.time() - concurrent_start
            
            # 计算性能提升
            improvement = (serial_duration - concurrent_duration) / serial_duration * 100 if serial_duration > 0 else 0
            
            logger.info(f"   端点数: {count}")
            logger.info(f"   串行: {serial_duration:.2f}秒")
            logger.info(f"   并发: {concurrent_duration:.2f}秒")
            logger.info(f"   提升: {improvement:.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 可扩展性测试失败: {e}")
        return False


def main():
    """主函数"""
    logger = get_logger(__name__)
    
    logger.info("🚀 开始并发性能测试套件...")
    
    tests = [
        ("并发性能测试", test_concurrent_performance),
        ("可扩展性测试", test_scalability),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 执行: {test_name}")
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
        logger.info("🎉 所有测试通过!")
        return True
    else:
        logger.error("💥 部分测试失败!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
