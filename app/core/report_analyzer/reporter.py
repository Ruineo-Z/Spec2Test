"""
报告生成器

生成各种格式的测试分析报告，包括HTML、Markdown、JSON等格式。
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import uuid

from app.core.shared.utils.logger import get_logger
from .models import AnalysisReport, AnalysisConfig, ComparisonReport, FailureCategory, SeverityLevel


class ReportGenerator:
    """报告生成器
    
    生成多种格式的测试分析报告。
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """初始化报告生成器
        
        Args:
            config: 分析配置
        """
        self.config = config or AnalysisConfig()
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        self.logger.info("报告生成器初始化完成")
    
    def generate_html_report(self, report: AnalysisReport, output_path: Optional[str] = None) -> str:
        """生成HTML格式报告
        
        Args:
            report: 分析报告
            output_path: 输出路径，如果不指定则返回HTML内容
            
        Returns:
            str: HTML内容或文件路径
        """
        self.logger.info(f"生成HTML报告: {report.report_name}")
        
        html_content = self._generate_html_content(report)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"HTML报告已保存: {output_path}")
            return output_path
        
        return html_content
    
    def generate_markdown_report(self, report: AnalysisReport, output_path: Optional[str] = None) -> str:
        """生成Markdown格式报告
        
        Args:
            report: 分析报告
            output_path: 输出路径，如果不指定则返回Markdown内容
            
        Returns:
            str: Markdown内容或文件路径
        """
        self.logger.info(f"生成Markdown报告: {report.report_name}")
        
        markdown_content = self._generate_markdown_content(report)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            self.logger.info(f"Markdown报告已保存: {output_path}")
            return output_path
        
        return markdown_content
    
    def generate_json_report(self, report: AnalysisReport, output_path: Optional[str] = None) -> str:
        """生成JSON格式报告
        
        Args:
            report: 分析报告
            output_path: 输出路径，如果不指定则返回JSON内容
            
        Returns:
            str: JSON内容或文件路径
        """
        self.logger.info(f"生成JSON报告: {report.report_name}")
        
        # 转换为可序列化的字典
        report_dict = self._convert_report_to_dict(report)
        json_content = json.dumps(report_dict, ensure_ascii=False, indent=2, default=str)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
            self.logger.info(f"JSON报告已保存: {output_path}")
            return output_path
        
        return json_content
    
    def generate_summary_report(self, report: AnalysisReport) -> str:
        """生成简要报告
        
        Args:
            report: 分析报告
            
        Returns:
            str: 简要报告内容
        """
        metrics = report.overall_metrics
        
        summary_lines = [
            f"📊 测试分析报告 - {report.suite_name}",
            f"🕐 执行时间: {report.execution_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"📈 生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📋 整体概况",
            f"- 总测试数: {metrics.total_tests}",
            f"- 成功数: {metrics.passed_tests} ✅",
            f"- 失败数: {metrics.failed_tests} ❌",
            f"- 错误数: {metrics.error_tests} 💥",
            f"- 成功率: {metrics.success_rate:.1%}",
            "",
            "## ⚡ 性能指标",
            f"- 平均响应时间: {metrics.avg_response_time:.2f}s",
            f"- 最快响应: {metrics.min_response_time:.2f}s",
            f"- 最慢响应: {metrics.max_response_time:.2f}s",
            f"- 95%分位: {metrics.p95_response_time:.2f}s",
            f"- 总执行时间: {metrics.total_execution_time:.2f}s",
            "",
            "## 🎯 关键发现",
        ]
        
        for finding in report.key_findings:
            summary_lines.append(f"- {finding}")
        
        if report.recommendations:
            summary_lines.extend([
                "",
                "## 💡 改进建议",
            ])
            for recommendation in report.recommendations:
                summary_lines.append(f"- {recommendation}")
        
        if report.critical_issues:
            summary_lines.extend([
                "",
                "## 🚨 关键问题",
            ])
            for issue in report.critical_issues:
                summary_lines.append(f"- ⚠️ {issue}")
        
        return "\n".join(summary_lines)
    
    def _generate_html_content(self, report: AnalysisReport) -> str:
        """生成HTML内容"""
        metrics = report.overall_metrics
        
        # HTML模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.report_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }}
        .title {{ color: #333; margin-bottom: 10px; }}
        .subtitle {{ color: #666; font-size: 16px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .section {{ margin: 30px 0; }}
        .section-title {{ color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 10px; }}
        .endpoint-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .endpoint-table th, .endpoint-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        .endpoint-table th {{ background-color: #f8f9fa; font-weight: 600; }}
        .success-rate {{ padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
        .success-high {{ background-color: #28a745; }}
        .success-medium {{ background-color: #ffc107; color: #333; }}
        .success-low {{ background-color: #dc3545; }}
        .failure-pattern {{ background: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; border-radius: 4px; }}
        .recommendations {{ background: #d1ecf1; padding: 15px; border-left: 4px solid #17a2b8; border-radius: 4px; }}
        .critical-issue {{ background: #f8d7da; padding: 15px; margin: 10px 0; border-left: 4px solid #dc3545; border-radius: 4px; }}
        .risk-level {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-weight: bold; text-transform: uppercase; }}
        .risk-critical {{ background-color: #dc3545; color: white; }}
        .risk-high {{ background-color: #fd7e14; color: white; }}
        .risk-medium {{ background-color: #ffc107; color: #333; }}
        .risk-low {{ background-color: #28a745; color: white; }}
        .risk-info {{ background-color: #17a2b8; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">{report.report_name}</h1>
            <p class="subtitle">生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p class="subtitle">执行时间: {report.execution_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <span class="risk-level risk-{report.risk_level if isinstance(report.risk_level, str) else report.risk_level.value}">{report.risk_level if isinstance(report.risk_level, str) else report.risk_level.value}</span>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{metrics.total_tests}</div>
                <div class="metric-label">总测试数</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #28a745;">{metrics.passed_tests}</div>
                <div class="metric-label">成功测试</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #dc3545;">{metrics.failed_tests}</div>
                <div class="metric-label">失败测试</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.success_rate:.1%}</div>
                <div class="metric-label">成功率</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.avg_response_time:.2f}s</div>
                <div class="metric-label">平均响应时间</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics.total_execution_time:.2f}s</div>
                <div class="metric-label">总执行时间</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📋 分析总结</h2>
            <p>{report.summary}</p>
        </div>
        
        {self._generate_html_key_findings(report)}
        {self._generate_html_endpoint_analysis(report)}
        {self._generate_html_failure_patterns(report)}
        {self._generate_html_recommendations(report)}
        {self._generate_html_critical_issues(report)}
    </div>
</body>
</html>
        """
        
        return html_template.strip()
    
    def _generate_html_key_findings(self, report: AnalysisReport) -> str:
        """生成HTML关键发现部分"""
        if not report.key_findings:
            return ""
        
        findings_html = '<div class="section"><h2 class="section-title">🎯 关键发现</h2><ul>'
        for finding in report.key_findings:
            findings_html += f'<li>{finding}</li>'
        findings_html += '</ul></div>'
        
        return findings_html
    
    def _generate_html_endpoint_analysis(self, report: AnalysisReport) -> str:
        """生成HTML端点分析部分"""
        if not report.endpoint_analyses:
            return ""
        
        html = '<div class="section"><h2 class="section-title">🔍 端点分析</h2>'
        html += '<table class="endpoint-table">'
        html += '<thead><tr><th>端点</th><th>方法</th><th>测试数</th><th>成功率</th><th>平均响应时间</th><th>状态</th></tr></thead><tbody>'
        
        for endpoint in report.endpoint_analyses:
            success_rate_class = self._get_success_rate_class(endpoint.success_rate)
            html += f'''
            <tr>
                <td>{endpoint.endpoint_path}</td>
                <td>{endpoint.http_method}</td>
                <td>{endpoint.total_tests}</td>
                <td><span class="success-rate {success_rate_class}">{endpoint.success_rate:.1%}</span></td>
                <td>{endpoint.avg_response_time:.2f}s</td>
                <td>{'✅' if endpoint.success_rate >= 0.8 else '⚠️' if endpoint.success_rate >= 0.5 else '❌'}</td>
            </tr>
            '''
        
        html += '</tbody></table></div>'
        return html
    
    def _generate_html_failure_patterns(self, report: AnalysisReport) -> str:
        """生成HTML失败模式部分"""
        if not report.failure_patterns:
            return ""
        
        html = '<div class="section"><h2 class="section-title">🔍 失败模式分析</h2>'
        
        for pattern in sorted(report.failure_patterns, key=lambda p: p.occurrence_count, reverse=True):
            html += f'''
            <div class="failure-pattern">
                <h4>{pattern.pattern_name} ({pattern.occurrence_count}次)</h4>
                <p>{pattern.description}</p>
                <p><strong>影响端点:</strong> {len(pattern.affected_endpoints)}个</p>
            </div>
            '''
        
        html += '</div>'
        return html
    
    def _generate_html_recommendations(self, report: AnalysisReport) -> str:
        """生成HTML建议部分"""
        if not report.recommendations:
            return ""
        
        html = '<div class="section"><h2 class="section-title">💡 改进建议</h2><div class="recommendations"><ul>'
        for recommendation in report.recommendations:
            html += f'<li>{recommendation}</li>'
        html += '</ul></div></div>'
        
        return html
    
    def _generate_html_critical_issues(self, report: AnalysisReport) -> str:
        """生成HTML关键问题部分"""
        if not report.critical_issues:
            return ""
        
        html = '<div class="section"><h2 class="section-title">🚨 关键问题</h2>'
        for issue in report.critical_issues:
            html += f'<div class="critical-issue"><strong>⚠️ {issue}</strong></div>'
        html += '</div>'
        
        return html
    
    def _get_success_rate_class(self, success_rate: float) -> str:
        """获取成功率样式类"""
        if success_rate >= 0.8:
            return "success-high"
        elif success_rate >= 0.5:
            return "success-medium"
        else:
            return "success-low"
    
    def _generate_markdown_content(self, report: AnalysisReport) -> str:
        """生成Markdown内容"""
        metrics = report.overall_metrics
        
        markdown_lines = [
            f"# {report.report_name}",
            "",
            f"**生成时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**执行时间**: {report.execution_time.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**风险等级**: {(report.risk_level if isinstance(report.risk_level, str) else report.risk_level.value).upper()}  ",
            "",
            "## 📊 整体概况",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总测试数 | {metrics.total_tests} |",
            f"| 成功测试 | {metrics.passed_tests} ✅ |",
            f"| 失败测试 | {metrics.failed_tests} ❌ |",
            f"| 错误测试 | {metrics.error_tests} 💥 |",
            f"| 成功率 | {metrics.success_rate:.1%} |",
            f"| 平均响应时间 | {metrics.avg_response_time:.2f}s |",
            f"| 总执行时间 | {metrics.total_execution_time:.2f}s |",
            "",
            "## 📋 分析总结",
            "",
            report.summary,
            "",
        ]
        
        # 关键发现
        if report.key_findings:
            markdown_lines.extend([
                "## 🎯 关键发现",
                "",
            ])
            for finding in report.key_findings:
                markdown_lines.append(f"- {finding}")
            markdown_lines.append("")
        
        # 端点分析
        if report.endpoint_analyses:
            markdown_lines.extend([
                "## 🔍 端点分析",
                "",
                "| 端点 | 方法 | 测试数 | 成功率 | 平均响应时间 | 状态 |",
                "|------|------|--------|--------|--------------|------|",
            ])
            
            for endpoint in report.endpoint_analyses:
                status = "✅" if endpoint.success_rate >= 0.8 else "⚠️" if endpoint.success_rate >= 0.5 else "❌"
                markdown_lines.append(
                    f"| {endpoint.endpoint_path} | {endpoint.http_method} | {endpoint.total_tests} | "
                    f"{endpoint.success_rate:.1%} | {endpoint.avg_response_time:.2f}s | {status} |"
                )
            markdown_lines.append("")
        
        # 失败模式
        if report.failure_patterns:
            markdown_lines.extend([
                "## 🔍 失败模式分析",
                "",
            ])
            
            for pattern in sorted(report.failure_patterns, key=lambda p: p.occurrence_count, reverse=True):
                markdown_lines.extend([
                    f"### {pattern.pattern_name} ({pattern.occurrence_count}次)",
                    "",
                    pattern.description,
                    "",
                    f"**影响端点**: {len(pattern.affected_endpoints)}个",
                    "",
                ])
        
        # 改进建议
        if report.recommendations:
            markdown_lines.extend([
                "## 💡 改进建议",
                "",
            ])
            for recommendation in report.recommendations:
                markdown_lines.append(f"- {recommendation}")
            markdown_lines.append("")
        
        # 关键问题
        if report.critical_issues:
            markdown_lines.extend([
                "## 🚨 关键问题",
                "",
            ])
            for issue in report.critical_issues:
                markdown_lines.append(f"- ⚠️ {issue}")
            markdown_lines.append("")
        
        return "\n".join(markdown_lines)
    
    def _convert_report_to_dict(self, report: AnalysisReport) -> Dict[str, Any]:
        """将报告转换为可序列化的字典"""
        return {
            "report_id": report.report_id,
            "report_name": report.report_name,
            "generated_at": report.generated_at.isoformat(),
            "suite_id": report.suite_id,
            "suite_name": report.suite_name,
            "execution_time": report.execution_time.isoformat(),
            "overall_metrics": {
                "total_tests": report.overall_metrics.total_tests,
                "passed_tests": report.overall_metrics.passed_tests,
                "failed_tests": report.overall_metrics.failed_tests,
                "error_tests": report.overall_metrics.error_tests,
                "skipped_tests": report.overall_metrics.skipped_tests,
                "success_rate": report.overall_metrics.success_rate,
                "failure_rate": report.overall_metrics.failure_rate,
                "avg_response_time": report.overall_metrics.avg_response_time,
                "min_response_time": report.overall_metrics.min_response_time,
                "max_response_time": report.overall_metrics.max_response_time,
                "p95_response_time": report.overall_metrics.p95_response_time,
                "p99_response_time": report.overall_metrics.p99_response_time,
                "total_execution_time": report.overall_metrics.total_execution_time,
                "avg_test_duration": report.overall_metrics.avg_test_duration,
            },
            "endpoint_analyses": [
                {
                    "endpoint_path": ep.endpoint_path,
                    "http_method": ep.http_method,
                    "total_tests": ep.total_tests,
                    "passed_tests": ep.passed_tests,
                    "failed_tests": ep.failed_tests,
                    "success_rate": ep.success_rate,
                    "avg_response_time": ep.avg_response_time,
                    "min_response_time": ep.min_response_time,
                    "max_response_time": ep.max_response_time,
                    "common_failures": ep.common_failures,
                    "recommendations": ep.recommendations,
                }
                for ep in report.endpoint_analyses
            ],
            "failure_patterns": [
                {
                    "pattern_id": fp.pattern_id,
                    "category": fp.category if isinstance(fp.category, str) else fp.category.value,
                    "pattern_name": fp.pattern_name,
                    "description": fp.description,
                    "occurrence_count": fp.occurrence_count,
                    "affected_endpoints": fp.affected_endpoints,
                }
                for fp in report.failure_patterns
            ],
            "top_failure_categories": report.top_failure_categories,
            "summary": report.summary,
            "key_findings": report.key_findings,
            "recommendations": report.recommendations,
            "risk_level": report.risk_level if isinstance(report.risk_level, str) else report.risk_level.value,
            "critical_issues": report.critical_issues,
        }
    
    def generate_comparison_report(self, baseline_report: AnalysisReport, 
                                 current_report: AnalysisReport) -> ComparisonReport:
        """生成对比报告
        
        Args:
            baseline_report: 基线报告
            current_report: 当前报告
            
        Returns:
            ComparisonReport: 对比报告
        """
        self.logger.info(f"生成对比报告: {baseline_report.suite_name} vs {current_report.suite_name}")
        
        # 计算性能变化
        performance_changes = {
            "success_rate_change": current_report.overall_metrics.success_rate - baseline_report.overall_metrics.success_rate,
            "avg_response_time_change": current_report.overall_metrics.avg_response_time - baseline_report.overall_metrics.avg_response_time,
            "total_tests_change": current_report.overall_metrics.total_tests - baseline_report.overall_metrics.total_tests,
            "failed_tests_change": current_report.overall_metrics.failed_tests - baseline_report.overall_metrics.failed_tests,
        }
        
        # 分析失败变化
        baseline_failures = set(fp.pattern_id for fp in baseline_report.failure_patterns)
        current_failures = set(fp.pattern_id for fp in current_report.failure_patterns)
        
        new_failures = list(current_failures - baseline_failures)
        resolved_failures = list(baseline_failures - current_failures)
        
        # 评估总体变化
        overall_change = self._assess_overall_change(performance_changes)
        change_summary = self._generate_change_summary(performance_changes, new_failures, resolved_failures)
        
        return ComparisonReport(
            comparison_id=str(uuid.uuid4()),
            comparison_name=f"{current_report.suite_name}_对比分析",
            baseline_report=baseline_report,
            current_report=current_report,
            performance_changes=performance_changes,
            new_failures=new_failures,
            resolved_failures=resolved_failures,
            regression_issues=[],  # 可以进一步实现回归问题检测
            overall_change=overall_change,
            change_summary=change_summary
        )
    
    def _assess_overall_change(self, performance_changes: Dict[str, float]) -> str:
        """评估总体变化"""
        success_rate_change = performance_changes.get("success_rate_change", 0)
        response_time_change = performance_changes.get("avg_response_time_change", 0)
        
        if success_rate_change > 0.05 and response_time_change < 0.5:
            return "improved"
        elif success_rate_change < -0.05 or response_time_change > 1.0:
            return "degraded"
        else:
            return "stable"
    
    def _generate_change_summary(self, performance_changes: Dict[str, float], 
                                new_failures: List[str], resolved_failures: List[str]) -> str:
        """生成变化总结"""
        summary_parts = []
        
        success_rate_change = performance_changes.get("success_rate_change", 0)
        if abs(success_rate_change) > 0.01:
            direction = "提升" if success_rate_change > 0 else "下降"
            summary_parts.append(f"成功率{direction}{abs(success_rate_change):.1%}")
        
        response_time_change = performance_changes.get("avg_response_time_change", 0)
        if abs(response_time_change) > 0.1:
            direction = "增加" if response_time_change > 0 else "减少"
            summary_parts.append(f"响应时间{direction}{abs(response_time_change):.2f}秒")
        
        if new_failures:
            summary_parts.append(f"新增{len(new_failures)}种失败模式")
        
        if resolved_failures:
            summary_parts.append(f"解决{len(resolved_failures)}种失败模式")
        
        if not summary_parts:
            return "整体表现保持稳定"
        
        return "，".join(summary_parts)
