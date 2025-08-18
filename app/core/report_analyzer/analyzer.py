"""
结果分析器

分析测试执行结果，识别失败模式，生成性能指标和改进建议。
"""

import re
import statistics
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import uuid

from app.core.shared.utils.logger import get_logger
from app.core.test_executor.models import TestExecutionResult, TestSuiteExecutionResult
from .models import (
    FailureCategory, SeverityLevel, FailurePattern, FailureAnalysis,
    PerformanceMetrics, EndpointAnalysis, TrendData, AnalysisReport,
    AnalysisConfig
)


class ResultAnalyzer:
    """结果分析器
    
    分析测试执行结果，提供失败原因分析、性能指标计算、模式识别等功能。
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """初始化结果分析器
        
        Args:
            config: 分析配置
        """
        self.config = config or AnalysisConfig()
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 预定义失败模式
        self.failure_patterns = self._initialize_failure_patterns()
        
        self.logger.info("结果分析器初始化完成")
    
    def analyze_suite_result(self, suite_result: TestSuiteExecutionResult) -> AnalysisReport:
        """分析测试套件结果
        
        Args:
            suite_result: 测试套件执行结果
            
        Returns:
            AnalysisReport: 分析报告
        """
        self.logger.info(f"开始分析测试套件: {suite_result.suite_name}")
        
        # 创建报告
        report = AnalysisReport(
            report_id=str(uuid.uuid4()),
            report_name=f"{suite_result.suite_name}_分析报告",
            suite_id=suite_result.suite_id,
            suite_name=suite_result.suite_name,
            execution_time=suite_result.started_at,
            overall_metrics=self._calculate_overall_metrics(suite_result),
            summary="",
            risk_level=SeverityLevel.INFO
        )
        
        # 分析各个端点
        if self.config.enable_failure_analysis:
            report.endpoint_analyses = self._analyze_endpoints(suite_result.test_results)
            report.failure_patterns = self._analyze_failure_patterns(suite_result.test_results)
            report.top_failure_categories = self._get_top_failure_categories(suite_result.test_results)
        
        # 生成总结和建议
        report.summary = self._generate_summary(report)
        report.key_findings = self._extract_key_findings(report)
        report.recommendations = self._generate_recommendations(report)
        report.risk_level = self._assess_risk_level(report)
        report.critical_issues = self._identify_critical_issues(report)
        
        self.logger.info(f"分析完成: 成功率={report.overall_metrics.success_rate:.1%}")
        return report
    
    def _initialize_failure_patterns(self) -> List[FailurePattern]:
        """初始化预定义的失败模式"""
        patterns = [
            FailurePattern(
                pattern_id="timeout_pattern",
                category=FailureCategory.TIMEOUT_ERROR,
                pattern_name="请求超时",
                description="请求响应时间超过预设阈值",
                response_time_threshold=self.config.slow_response_threshold,
                error_keywords=["timeout", "超时", "time out"]
            ),
            FailurePattern(
                pattern_id="auth_failure_pattern",
                category=FailureCategory.AUTHENTICATION_ERROR,
                pattern_name="认证失败",
                description="身份认证或授权失败",
                status_codes=[401, 403],
                error_keywords=["unauthorized", "forbidden", "认证失败", "权限不足"]
            ),
            FailurePattern(
                pattern_id="not_found_pattern",
                category=FailureCategory.CLIENT_ERROR,
                pattern_name="资源未找到",
                description="请求的资源不存在",
                status_codes=[404],
                error_keywords=["not found", "未找到", "不存在"]
            ),
            FailurePattern(
                pattern_id="server_error_pattern",
                category=FailureCategory.SERVER_ERROR,
                pattern_name="服务器内部错误",
                description="服务器处理请求时发生内部错误",
                status_codes=[500, 502, 503, 504],
                error_keywords=["internal server error", "服务器错误", "系统异常"]
            ),
            FailurePattern(
                pattern_id="validation_error_pattern",
                category=FailureCategory.VALIDATION_ERROR,
                pattern_name="数据验证错误",
                description="请求数据格式或内容不符合要求",
                status_codes=[400, 422],
                error_keywords=["validation error", "invalid", "格式错误", "参数错误"]
            ),
            FailurePattern(
                pattern_id="network_error_pattern",
                category=FailureCategory.NETWORK_ERROR,
                pattern_name="网络连接错误",
                description="网络连接失败或中断",
                error_keywords=["connection", "network", "网络", "连接失败", "dns"]
            )
        ]
        return patterns
    
    def _calculate_overall_metrics(self, suite_result: TestSuiteExecutionResult) -> PerformanceMetrics:
        """计算整体性能指标"""
        response_times = []
        test_durations = []
        
        for test_result in suite_result.test_results:
            if test_result.response_time is not None:
                response_times.append(test_result.response_time)
            if test_result.duration is not None:
                test_durations.append(test_result.duration)
        
        # 计算响应时间统计
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = self._calculate_percentile(response_times, 95)
            p99_response_time = self._calculate_percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p95_response_time = p99_response_time = 0.0
        
        # 计算测试时长统计
        avg_test_duration = statistics.mean(test_durations) if test_durations else 0.0
        
        return PerformanceMetrics(
            total_tests=suite_result.total_tests,
            passed_tests=suite_result.passed_tests,
            failed_tests=suite_result.failed_tests,
            error_tests=suite_result.error_tests,
            skipped_tests=suite_result.skipped_tests,
            success_rate=suite_result.success_rate,
            failure_rate=1.0 - suite_result.success_rate,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            total_execution_time=suite_result.total_duration or 0.0,
            avg_test_duration=avg_test_duration
        )
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = (percentile / 100.0) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _analyze_endpoints(self, test_results: List[TestExecutionResult]) -> List[EndpointAnalysis]:
        """分析各个端点的执行情况"""
        endpoint_groups = defaultdict(list)
        
        # 按端点分组
        for result in test_results:
            key = f"{result.request_method}:{result.request_url}"
            endpoint_groups[key].append(result)
        
        endpoint_analyses = []
        
        for endpoint_key, results in endpoint_groups.items():
            method, url = endpoint_key.split(":", 1)
            
            # 计算端点统计
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.is_successful)
            failed_tests = total_tests - passed_tests
            success_rate = passed_tests / total_tests if total_tests > 0 else 0.0
            
            # 计算响应时间统计
            response_times = [r.response_time for r in results if r.response_time is not None]
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
            else:
                avg_response_time = min_response_time = max_response_time = 0.0
            
            # 分析失败情况
            failed_results = [r for r in results if not r.is_successful]
            failure_analyses = []
            common_failures = []
            
            if failed_results:
                failure_analyses = [self._analyze_single_failure(r) for r in failed_results]
                failure_reasons = [fa.failure_reason for fa in failure_analyses]
                common_failures = [reason for reason, count in Counter(failure_reasons).most_common(3)]
            
            # 生成建议
            recommendations = self._generate_endpoint_recommendations(
                success_rate, avg_response_time, failure_analyses
            )
            
            endpoint_analysis = EndpointAnalysis(
                endpoint_path=url,
                http_method=method,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                success_rate=success_rate,
                avg_response_time=avg_response_time,
                min_response_time=min_response_time,
                max_response_time=max_response_time,
                failure_analyses=failure_analyses,
                common_failures=common_failures,
                recommendations=recommendations
            )
            
            endpoint_analyses.append(endpoint_analysis)
        
        return endpoint_analyses
    
    def _analyze_single_failure(self, test_result: TestExecutionResult) -> FailureAnalysis:
        """分析单个失败的测试"""
        # 确定失败类别和严重程度
        failure_category = self._categorize_failure(test_result)
        severity_level = self._assess_failure_severity(test_result, failure_category)
        
        # 生成失败原因描述
        failure_reason = self._generate_failure_reason(test_result, failure_category)
        
        # 匹配失败模式
        matched_patterns = self._match_failure_patterns(test_result)
        
        # 生成修复建议
        fix_suggestions = self._generate_fix_suggestions(test_result, failure_category)
        
        return FailureAnalysis(
            test_id=test_result.test_id,
            endpoint_path=test_result.request_url,
            http_method=test_result.request_method,
            failure_category=failure_category,
            severity_level=severity_level,
            failure_reason=failure_reason,
            error_message=test_result.error_message or "",
            matched_patterns=matched_patterns,
            fix_suggestions=fix_suggestions,
            response_status_code=test_result.response_status_code,
            response_time=test_result.response_time
        )
    
    def _categorize_failure(self, test_result: TestExecutionResult) -> FailureCategory:
        """对失败进行分类"""
        error_msg = (test_result.error_message or "").lower()
        status_code = test_result.response_status_code
        
        # 基于状态码分类
        if status_code:
            if status_code == 401:
                return FailureCategory.AUTHENTICATION_ERROR
            elif status_code == 403:
                return FailureCategory.AUTHENTICATION_ERROR
            elif status_code == 404:
                return FailureCategory.CLIENT_ERROR
            elif 400 <= status_code < 500:
                return FailureCategory.CLIENT_ERROR
            elif 500 <= status_code < 600:
                return FailureCategory.SERVER_ERROR
        
        # 基于错误消息分类
        if any(keyword in error_msg for keyword in ["timeout", "超时"]):
            return FailureCategory.TIMEOUT_ERROR
        elif any(keyword in error_msg for keyword in ["connection", "network", "dns"]):
            return FailureCategory.NETWORK_ERROR
        elif any(keyword in error_msg for keyword in ["auth", "unauthorized", "forbidden"]):
            return FailureCategory.AUTHENTICATION_ERROR
        elif any(keyword in error_msg for keyword in ["validation", "invalid", "format"]):
            return FailureCategory.VALIDATION_ERROR
        
        return FailureCategory.UNKNOWN_ERROR
    
    def _assess_failure_severity(self, test_result: TestExecutionResult, category: FailureCategory) -> SeverityLevel:
        """评估失败的严重程度"""
        # 基于失败类别评估严重程度
        if category in [FailureCategory.SERVER_ERROR, FailureCategory.NETWORK_ERROR]:
            return SeverityLevel.HIGH
        elif category in [FailureCategory.AUTHENTICATION_ERROR, FailureCategory.TIMEOUT_ERROR]:
            return SeverityLevel.MEDIUM
        elif category in [FailureCategory.CLIENT_ERROR, FailureCategory.VALIDATION_ERROR]:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.MEDIUM
    
    def _generate_failure_reason(self, test_result: TestExecutionResult, category: FailureCategory) -> str:
        """生成失败原因描述"""
        status_code = test_result.response_status_code
        error_msg = test_result.error_message
        
        if category == FailureCategory.TIMEOUT_ERROR:
            return f"请求超时 (响应时间: {test_result.response_time:.2f}s)"
        elif category == FailureCategory.AUTHENTICATION_ERROR:
            return f"认证失败 (状态码: {status_code})"
        elif category == FailureCategory.CLIENT_ERROR:
            return f"客户端错误 (状态码: {status_code})"
        elif category == FailureCategory.SERVER_ERROR:
            return f"服务器错误 (状态码: {status_code})"
        elif category == FailureCategory.NETWORK_ERROR:
            return f"网络连接错误: {error_msg}"
        elif category == FailureCategory.VALIDATION_ERROR:
            return f"数据验证错误 (状态码: {status_code})"
        else:
            return f"未知错误: {error_msg}"
    
    def _match_failure_patterns(self, test_result: TestExecutionResult) -> List[str]:
        """匹配失败模式"""
        matched_patterns = []
        
        for pattern in self.failure_patterns:
            if self._test_matches_pattern(test_result, pattern):
                matched_patterns.append(pattern.pattern_id)
                pattern.occurrence_count += 1
                if test_result.request_url not in pattern.affected_endpoints:
                    pattern.affected_endpoints.append(test_result.request_url)
        
        return matched_patterns
    
    def _test_matches_pattern(self, test_result: TestExecutionResult, pattern: FailurePattern) -> bool:
        """检查测试结果是否匹配失败模式"""
        # 检查状态码
        if pattern.status_codes and test_result.response_status_code:
            if test_result.response_status_code in pattern.status_codes:
                return True
        
        # 检查响应时间阈值
        if pattern.response_time_threshold and test_result.response_time:
            if test_result.response_time > pattern.response_time_threshold:
                return True
        
        # 检查错误关键词
        if pattern.error_keywords and test_result.error_message:
            error_msg = test_result.error_message.lower()
            if any(keyword.lower() in error_msg for keyword in pattern.error_keywords):
                return True
        
        return False
    
    def _generate_fix_suggestions(self, test_result: TestExecutionResult, category: FailureCategory) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        if category == FailureCategory.TIMEOUT_ERROR:
            suggestions.extend([
                "增加请求超时时间配置",
                "检查服务器性能和负载情况",
                "优化API响应速度",
                "考虑实现请求重试机制"
            ])
        elif category == FailureCategory.AUTHENTICATION_ERROR:
            suggestions.extend([
                "检查API密钥或认证令牌是否有效",
                "确认用户权限配置是否正确",
                "检查认证头格式是否符合要求",
                "验证认证服务是否正常运行"
            ])
        elif category == FailureCategory.CLIENT_ERROR:
            suggestions.extend([
                "检查请求参数格式和内容",
                "确认API端点路径是否正确",
                "验证请求头信息是否完整",
                "检查API文档是否与实际实现一致"
            ])
        elif category == FailureCategory.SERVER_ERROR:
            suggestions.extend([
                "联系API提供方检查服务器状态",
                "检查服务器日志获取详细错误信息",
                "确认API服务是否正常部署",
                "考虑实现降级处理机制"
            ])
        elif category == FailureCategory.NETWORK_ERROR:
            suggestions.extend([
                "检查网络连接是否稳定",
                "确认DNS解析是否正常",
                "检查防火墙和代理设置",
                "验证目标服务器是否可达"
            ])
        
        return suggestions
    
    def _analyze_failure_patterns(self, test_results: List[TestExecutionResult]) -> List[FailurePattern]:
        """分析失败模式"""
        # 重置模式统计
        for pattern in self.failure_patterns:
            pattern.occurrence_count = 0
            pattern.affected_endpoints = []
        
        # 统计模式匹配
        for result in test_results:
            if not result.is_successful:
                self._match_failure_patterns(result)
        
        # 返回有匹配的模式
        return [p for p in self.failure_patterns if p.occurrence_count > 0]
    
    def _get_top_failure_categories(self, test_results: List[TestExecutionResult]) -> List[Dict[str, Any]]:
        """获取主要失败类别统计"""
        failed_results = [r for r in test_results if not r.is_successful]
        
        if not failed_results:
            return []
        
        category_counts = Counter()
        for result in failed_results:
            category = self._categorize_failure(result)
            category_counts[category.value] += 1
        
        total_failures = len(failed_results)
        top_categories = []
        
        for category, count in category_counts.most_common(5):
            percentage = (count / total_failures) * 100
            top_categories.append({
                "category": category,
                "count": count,
                "percentage": percentage
            })
        
        return top_categories
    
    def _generate_endpoint_recommendations(self, success_rate: float, avg_response_time: float, 
                                         failure_analyses: List[FailureAnalysis]) -> List[str]:
        """生成端点级别的建议"""
        recommendations = []
        
        if success_rate < self.config.low_success_rate_threshold:
            recommendations.append(f"成功率较低 ({success_rate:.1%})，需要重点关注和优化")
        
        if avg_response_time > self.config.slow_response_threshold:
            recommendations.append(f"响应时间较慢 ({avg_response_time:.2f}s)，建议优化性能")
        
        if failure_analyses:
            common_categories = Counter(fa.failure_category for fa in failure_analyses)
            most_common = common_categories.most_common(1)[0]
            category_name = most_common[0].value if hasattr(most_common[0], 'value') else str(most_common[0])
            recommendations.append(f"主要失败原因: {category_name} ({most_common[1]}次)")
        
        return recommendations
    
    def _generate_summary(self, report: AnalysisReport) -> str:
        """生成分析总结"""
        metrics = report.overall_metrics
        
        summary_parts = [
            f"测试套件 '{report.suite_name}' 执行分析:",
            f"总计 {metrics.total_tests} 个测试，成功率 {metrics.success_rate:.1%}",
            f"平均响应时间 {metrics.avg_response_time:.2f}秒"
        ]
        
        if metrics.failed_tests > 0:
            summary_parts.append(f"发现 {metrics.failed_tests} 个失败测试")
        
        if report.failure_patterns:
            summary_parts.append(f"识别出 {len(report.failure_patterns)} 种失败模式")
        
        return "。".join(summary_parts) + "。"
    
    def _extract_key_findings(self, report: AnalysisReport) -> List[str]:
        """提取关键发现"""
        findings = []
        metrics = report.overall_metrics
        
        # 成功率分析
        if metrics.success_rate >= 0.95:
            findings.append("✅ 测试成功率优秀 (≥95%)")
        elif metrics.success_rate >= 0.8:
            findings.append("⚠️ 测试成功率良好 (80-95%)")
        else:
            findings.append("❌ 测试成功率需要改进 (<80%)")
        
        # 性能分析
        if metrics.avg_response_time <= 1.0:
            findings.append("✅ API响应速度优秀 (≤1s)")
        elif metrics.avg_response_time <= 3.0:
            findings.append("⚠️ API响应速度一般 (1-3s)")
        else:
            findings.append("❌ API响应速度较慢 (>3s)")
        
        # 失败模式分析
        if report.failure_patterns:
            top_pattern = max(report.failure_patterns, key=lambda p: p.occurrence_count)
            findings.append(f"🔍 主要失败模式: {top_pattern.pattern_name} ({top_pattern.occurrence_count}次)")
        
        return findings
    
    def _generate_recommendations(self, report: AnalysisReport) -> List[str]:
        """生成改进建议"""
        recommendations = []
        metrics = report.overall_metrics
        
        # 基于成功率的建议
        if metrics.success_rate < 0.8:
            recommendations.append("优先解决失败率高的问题，提升整体稳定性")
        
        # 基于性能的建议
        if metrics.avg_response_time > self.config.slow_response_threshold:
            recommendations.append("优化API响应性能，减少响应时间")
        
        # 基于失败模式的建议
        if report.failure_patterns:
            for pattern in sorted(report.failure_patterns, key=lambda p: p.occurrence_count, reverse=True)[:3]:
                recommendations.append(f"重点关注 {pattern.pattern_name} 问题")
        
        # 基于端点分析的建议
        problematic_endpoints = [ep for ep in report.endpoint_analyses if ep.success_rate < 0.8]
        if problematic_endpoints:
            recommendations.append(f"重点优化 {len(problematic_endpoints)} 个问题端点")
        
        return recommendations
    
    def _assess_risk_level(self, report: AnalysisReport) -> SeverityLevel:
        """评估风险等级"""
        metrics = report.overall_metrics
        
        # 基于成功率和失败严重程度评估
        if metrics.success_rate < 0.5:
            return SeverityLevel.CRITICAL
        elif metrics.success_rate < 0.8:
            return SeverityLevel.HIGH
        elif metrics.avg_response_time > self.config.slow_response_threshold * 2:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
    
    def _identify_critical_issues(self, report: AnalysisReport) -> List[str]:
        """识别关键问题"""
        issues = []
        metrics = report.overall_metrics
        
        if metrics.success_rate < 0.5:
            issues.append("测试成功率极低，系统可能存在严重问题")
        
        if metrics.avg_response_time > 10.0:
            issues.append("API响应时间过长，用户体验严重受影响")
        
        # 检查是否有大量服务器错误
        server_error_patterns = [p for p in report.failure_patterns 
                               if p.category == FailureCategory.SERVER_ERROR and p.occurrence_count > 5]
        if server_error_patterns:
            issues.append("存在大量服务器错误，需要紧急处理")
        
        return issues
