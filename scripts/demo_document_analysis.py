#!/usr/bin/env python3
"""
文档分析演示脚本

演示文档分析器的完整功能，并生成分析报告。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.document_analyzer import DocumentAnalyzer, ChunkingStrategy

logger = get_logger(__name__)


def main():
    """主演示函数"""
    try:
        logger.info("🚀 开始文档分析演示...")
        
        # 创建输出目录
        output_dir = project_root / "examples" / "analysis_results"
        output_dir.mkdir(exist_ok=True)
        
        # 创建文档分析器
        analyzer = DocumentAnalyzer(config={
            "enable_validation": True,
            "enable_chunking": True,
            "max_tokens": 2000,
            "overlap_tokens": 100
        })
        
        # 分析示例API文档
        api_file = project_root / "examples" / "sample_api.json"
        
        if not api_file.exists():
            logger.error(f"示例API文件不存在: {api_file}")
            return False
        
        logger.info(f"📄 分析文档: {api_file}")
        
        # 执行分析
        result = analyzer.analyze_file(api_file)
        
        # 显示分析结果
        logger.info("📊 分析结果:")
        logger.info(f"   📋 文档标题: {result.title}")
        logger.info(f"   🔢 API版本: {result.version}")
        logger.info(f"   🌐 基础URL: {result.base_url}")
        logger.info(f"   🔗 端点数量: {result.total_endpoints}")
        
        if result.quality_metrics:
            logger.info(f"   ⭐ 质量评分: {result.quality_metrics.overall_score:.1f}/100")
            logger.info(f"   📈 质量等级: {result.quality_metrics.quality_level}")
            logger.info(f"   ✅ 完整性: {result.quality_metrics.completeness_score:.1f}/100")
            logger.info(f"   🔄 一致性: {result.quality_metrics.consistency_score:.1f}/100")
            logger.info(f"   💡 清晰度: {result.quality_metrics.clarity_score:.1f}/100")
            logger.info(f"   🎯 可用性: {result.quality_metrics.usability_score:.1f}/100")
        
        logger.info(f"   ⚠️  问题数量: {len(result.issues)}")
        logger.info(f"   📦 分块数量: {len(result.chunks)}")
        logger.info(f"   ⏱️  分析耗时: {result.analysis_duration:.3f}秒")
        
        # 显示端点信息
        logger.info("\n🔗 API端点列表:")
        for i, endpoint in enumerate(result.endpoints, 1):
            logger.info(f"   {i}. {endpoint.method} {endpoint.path}")
            if endpoint.summary:
                logger.info(f"      📝 {endpoint.summary}")
            if endpoint.tags:
                logger.info(f"      🏷️  标签: {', '.join(endpoint.tags)}")
        
        # 显示发现的问题
        if result.issues:
            logger.info("\n⚠️ 发现的问题:")
            for i, issue in enumerate(result.issues, 1):
                severity_icon = {
                    "critical": "🔴",
                    "high": "🟠", 
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "ℹ️"
                }.get(issue.severity, "❓")
                
                logger.info(f"   {i}. {severity_icon} [{issue.severity.upper()}] {issue.message}")
                if issue.location:
                    logger.info(f"      📍 位置: {issue.location}")
                if issue.suggestion:
                    logger.info(f"      💡 建议: {issue.suggestion}")
        
        # 显示改进建议
        if result.suggestions:
            logger.info("\n💡 改进建议:")
            for i, suggestion in enumerate(result.suggestions, 1):
                logger.info(f"   {i}. {suggestion}")
        
        # 显示分块信息
        if result.chunks:
            logger.info("\n📦 文档分块信息:")
            for i, chunk in enumerate(result.chunks, 1):
                logger.info(f"   分块{i}: {chunk.token_count} tokens, {len(chunk.endpoints)} endpoints")
                logger.info(f"      类型: {chunk.chunk_type}")
                if chunk.endpoints:
                    logger.info(f"      端点: {', '.join(chunk.endpoints)}")
        
        # 生成分析摘要
        summary = analyzer.get_analysis_summary(result)
        logger.info("\n📈 分析摘要:")
        logger.info(f"   文档类型: {summary['document_info']['type']}")
        logger.info(f"   HTTP方法分布: {summary['api_info']['methods']}")
        logger.info(f"   标签分布: {summary['api_info']['tags']}")
        logger.info(f"   已弃用端点: {summary['api_info']['deprecated_count']}")
        
        # 导出分析报告
        logger.info("\n📄 导出分析报告...")
        
        # JSON格式报告
        json_report = output_dir / "analysis_report.json"
        success = analyzer.export_analysis_report(result, json_report, "json")
        if success:
            logger.info(f"   ✅ JSON报告: {json_report}")
        else:
            logger.error(f"   ❌ JSON报告导出失败")
        
        # Markdown格式报告
        md_report = output_dir / "analysis_report.md"
        success = analyzer.export_analysis_report(result, md_report, "markdown")
        if success:
            logger.info(f"   ✅ Markdown报告: {md_report}")
        else:
            logger.error(f"   ❌ Markdown报告导出失败")
        
        logger.info("\n🎉 文档分析演示完成！")
        logger.info(f"📁 报告文件保存在: {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 文档分析演示失败: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
