#!/usr/bin/env python3
"""
测试生成器演示脚本

演示如何使用测试生成器根据API文档分析结果生成测试用例。
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
from app.core.test_generator import TestCaseGenerator, GenerationConfig


def main():
    """主函数"""
    logger = get_logger(__name__)
    
    logger.info("🚀 开始测试生成器演示...")
    
    try:
        # 1. 初始化文档分析器
        logger.info("📄 初始化文档分析器...")
        analyzer = DocumentAnalyzer()
        
        # 2. 分析示例API文档
        api_file = project_root / "examples" / "sample_api.json"
        if not api_file.exists():
            logger.error(f"示例API文件不存在: {api_file}")
            return
        
        logger.info(f"📄 分析文档: {api_file}")
        analysis_result = analyzer.analyze_file(str(api_file))
        
        if not analysis_result.endpoints:
            logger.error("文档分析结果中没有找到API端点")
            return
        
        logger.info(f"📊 文档分析完成:")
        logger.info(f"   📋 文档标题: {analysis_result.title}")
        logger.info(f"   🔢 API版本: {analysis_result.version}")
        logger.info(f"   🌐 基础URL: {analysis_result.base_url}")
        logger.info(f"   🔗 端点数量: {len(analysis_result.endpoints)}")
        
        # 3. 初始化测试生成器
        logger.info("🧪 初始化测试生成器...")
        generator = TestCaseGenerator()
        
        # 4. 配置生成参数
        config = GenerationConfig(
            strategy="comprehensive",
            include_positive=True,
            include_negative=True,
            include_boundary=True,
            include_security=False,  # 暂时关闭安全测试
            include_performance=False,  # 暂时关闭性能测试
            max_cases_per_endpoint=5,
            include_invalid_data=True,
            include_null_data=True,
            include_special_chars=True,
            llm_temperature=0.3,
            llm_max_tokens=4000
        )
        
        logger.info("⚙️ 生成配置:")
        logger.info(f"   📋 生成策略: {config.strategy}")
        logger.info(f"   ✅ 正向用例: {config.include_positive}")
        logger.info(f"   ❌ 负向用例: {config.include_negative}")
        logger.info(f"   🔄 边界用例: {config.include_boundary}")
        logger.info(f"   🔢 每端点最大用例数: {config.max_cases_per_endpoint}")
        
        # 5. 生成测试用例
        logger.info("🎯 开始生成测试用例...")
        generation_result = generator.generate_test_cases(analysis_result, config)
        
        # 6. 显示生成结果
        if generation_result.success:
            logger.info("✅ 测试用例生成成功!")
            
            test_suite = generation_result.test_suite
            logger.info(f"📊 生成结果统计:")
            logger.info(f"   📦 测试套件: {test_suite.name}")
            logger.info(f"   🔢 用例总数: {generation_result.total_cases_generated}")
            logger.info(f"   ⏱️  生成耗时: {generation_result.generation_duration:.2f}秒")
            logger.info(f"   🤖 LLM调用次数: {generation_result.llm_calls_count}")
            
            # 按类型统计
            logger.info(f"   📋 按类型统计:")
            for case_type, count in generation_result.cases_by_type.items():
                logger.info(f"      {case_type}: {count}个")
            
            # 按优先级统计
            logger.info(f"   🎯 按优先级统计:")
            for priority, count in generation_result.cases_by_priority.items():
                logger.info(f"      {priority}: {count}个")
            
            # 显示部分测试用例详情
            logger.info(f"\n🔍 测试用例详情:")
            for i, test_case in enumerate(test_suite.test_cases[:3], 1):  # 只显示前3个
                logger.info(f"   {i}. 📝 {test_case.title}")
                logger.info(f"      🎯 类型: {test_case.case_type.value}")
                logger.info(f"      ⭐ 优先级: {test_case.priority.value}")
                logger.info(f"      🌐 端点: {test_case.http_method.upper()} {test_case.endpoint_path}")
                logger.info(f"      📊 状态码: {test_case.expected_status_code}")
                logger.info(f"      🔍 断言数: {len(test_case.assertions)}")
                if test_case.tags:
                    logger.info(f"      🏷️  标签: {', '.join(test_case.tags)}")
                logger.info("")
            
            if len(test_suite.test_cases) > 3:
                logger.info(f"   ... 还有 {len(test_suite.test_cases) - 3} 个测试用例")
            
            # 显示警告信息
            if generation_result.has_warnings:
                logger.info(f"\n⚠️ 警告信息:")
                for warning in generation_result.warnings:
                    logger.info(f"   - {warning}")
            
            # 7. 导出测试用例
            logger.info("\n📄 导出测试用例...")
            
            # 确保输出目录存在
            output_dir = project_root / "examples" / "test_generation_results"
            output_dir.mkdir(exist_ok=True)
            
            # 导出JSON格式
            json_file = output_dir / "generated_test_cases.json"
            test_suite_dict = test_suite.model_dump()
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(test_suite_dict, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"   ✅ JSON文件: {json_file}")
            
            # 导出生成结果
            result_file = output_dir / "generation_result.json"
            result_dict = generation_result.model_dump()
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"   ✅ 结果文件: {result_file}")
            
            # 导出Markdown格式的测试用例
            md_file = output_dir / "test_cases.md"
            _export_markdown_test_cases(test_suite, md_file)
            logger.info(f"   ✅ Markdown文件: {md_file}")
            
        else:
            logger.error("❌ 测试用例生成失败!")
            logger.error(f"   错误信息:")
            for error in generation_result.errors:
                logger.error(f"   - {error}")
        
        logger.info("\n🎉 测试生成器演示完成!")
        if 'output_dir' in locals():
            logger.info(f"📁 输出文件保存在: {output_dir}")
        else:
            logger.info("📁 由于生成失败，未创建输出文件")
        
    except Exception as e:
        logger.error(f"💥 测试生成器演示失败: {e}")
        import traceback
        logger.error(traceback.format_exc())


def _export_markdown_test_cases(test_suite, output_file):
    """导出Markdown格式的测试用例"""
    
    content = []
    content.append(f"# {test_suite.name}")
    content.append("")
    content.append(f"**描述**: {test_suite.description}")
    content.append(f"**基础URL**: {test_suite.base_url or 'N/A'}")
    content.append(f"**用例总数**: {test_suite.total_cases}")
    content.append(f"**创建时间**: {test_suite.created_at}")
    content.append("")
    
    # 按端点分组
    endpoints = {}
    for case in test_suite.test_cases:
        endpoint_key = f"{case.http_method.upper()} {case.endpoint_path}"
        if endpoint_key not in endpoints:
            endpoints[endpoint_key] = []
        endpoints[endpoint_key].append(case)
    
    for endpoint, cases in endpoints.items():
        content.append(f"## {endpoint}")
        content.append("")
        
        for i, case in enumerate(cases, 1):
            content.append(f"### {i}. {case.title}")
            content.append("")
            content.append(f"**描述**: {case.description}")
            content.append(f"**类型**: {case.case_type.value}")
            content.append(f"**优先级**: {case.priority.value}")
            content.append(f"**预期状态码**: {case.expected_status_code}")
            
            if case.tags:
                content.append(f"**标签**: {', '.join(case.tags)}")
            
            # 请求信息
            if case.request_headers:
                content.append("")
                content.append("**请求头**:")
                content.append("```json")
                content.append(json.dumps(case.request_headers, indent=2, ensure_ascii=False))
                content.append("```")
            
            if case.request_params:
                content.append("")
                content.append("**请求参数**:")
                content.append("```json")
                content.append(json.dumps(case.request_params, indent=2, ensure_ascii=False))
                content.append("```")
            
            if case.request_body:
                content.append("")
                content.append("**请求体**:")
                content.append("```json")
                content.append(json.dumps(case.request_body, indent=2, ensure_ascii=False))
                content.append("```")
            
            # 断言信息
            if case.assertions:
                content.append("")
                content.append("**断言验证**:")
                for assertion in case.assertions:
                    content.append(f"- {assertion.description}")
            
            content.append("")
            content.append("---")
            content.append("")
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))


if __name__ == "__main__":
    main()
