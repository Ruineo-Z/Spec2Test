#!/usr/bin/env python3
"""
简化的测试生成器验证脚本

快速验证测试生成器的核心功能。
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.document_analyzer import DocumentAnalyzer
from app.core.test_generator import TestCaseGenerator, GenerationConfig


def main():
    """主函数"""
    logger = get_logger(__name__)
    
    logger.info("🚀 开始简化测试生成器验证...")
    
    try:
        # 1. 分析示例API文档
        analyzer = DocumentAnalyzer()
        api_file = project_root / "examples" / "sample_api.json"
        
        logger.info(f"📄 分析文档: {api_file}")
        analysis_result = analyzer.analyze_file(str(api_file))
        
        logger.info(f"📊 分析结果: {len(analysis_result.endpoints)}个端点")
        
        # 2. 初始化测试生成器
        generator = TestCaseGenerator()
        
        # 3. 配置生成参数（简化配置）
        config = GenerationConfig(
            include_positive=True,
            include_negative=True,
            include_boundary=False,  # 简化：关闭边界测试
            include_security=False,
            include_performance=False,
            max_cases_per_endpoint=3,  # 减少用例数量
            llm_temperature=0.3
        )
        
        logger.info("⚙️ 开始生成测试用例（简化模式）...")
        
        # 4. 生成测试用例
        result = generator.generate_test_cases(analysis_result, config)
        
        # 5. 显示结果
        if result.success:
            logger.info("✅ 测试用例生成成功!")
            logger.info(f"📊 统计信息:")
            logger.info(f"   🔢 用例总数: {result.total_cases_generated}")
            logger.info(f"   ⏱️  生成耗时: {result.generation_duration:.2f}秒")
            logger.info(f"   🤖 LLM调用次数: {result.llm_calls_count}")
            
            # 按类型统计
            if result.cases_by_type:
                logger.info(f"   📋 按类型统计: {result.cases_by_type}")
            
            # 按优先级统计
            if result.cases_by_priority:
                logger.info(f"   🎯 按优先级统计: {result.cases_by_priority}")
            
            # 显示部分测试用例
            test_suite = result.test_suite
            logger.info(f"\n🔍 生成的测试用例示例:")
            for i, case in enumerate(test_suite.test_cases[:2], 1):  # 只显示前2个
                logger.info(f"   {i}. {case.title}")
                logger.info(f"      端点: {case.http_method.upper()} {case.endpoint_path}")
                logger.info(f"      类型: {case.case_type}")
                logger.info(f"      优先级: {case.priority}")
                logger.info(f"      状态码: {case.expected_status_code}")
            
            # 保存结果
            output_dir = project_root / "examples" / "test_generation_results"
            output_dir.mkdir(exist_ok=True)
            
            result_file = output_dir / "simple_test_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result.model_dump(), f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"\n📄 结果已保存到: {result_file}")
            
        else:
            logger.error("❌ 测试用例生成失败!")
            for error in result.errors:
                logger.error(f"   - {error}")
        
        logger.info("\n🎉 简化测试生成器验证完成!")
        
    except Exception as e:
        logger.error(f"💥 验证失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
