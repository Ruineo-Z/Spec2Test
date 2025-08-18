"""
结果分析器单元测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.core.report_analyzer.analyzer import ReportAnalyzer
from app.core.report_analyzer.models import (
    TestReport, ReportSummary, TestCoverage, PerformanceMetrics,
    IssueAnalysis, RecommendationLevel, ReportConfig
)
from app.core.test_executor.models import (
    TestExecution, TestResult, ExecutionStatus, AssertionResult
)
from app.core.test_generator.models import TestType, AssertionType


class TestReportAnalyzer:
    """测试结果分析器"""
    
    def setup_method(self):
        """测试前设置"""
        self.analyzer = ReportAnalyzer()
    
    @pytest.fixture
    def sample_test_results(self):
        """示例测试结果"""
        return [
            TestResult(
                test_case_name="test_get_user_success",
                status=ExecutionStatus.PASSED,
                response_time=150,
                actual_response={
                    "status_code": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"id": "123", "name": "John"}'
                },
                assertion_results=[
                    AssertionResult(
                        assertion_type=AssertionType.STATUS_CODE,
                        passed=True,
                        expected_value=200,
                        actual_value=200
                    )
                ]
            ),
            TestResult(
                test_case_name="test_get_user_not_found",
                status=ExecutionStatus.FAILED,
                response_time=200,
                actual_response={
                    "status_code": 200,  # 期望404但得到200
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"id": "123", "name": "John"}'
                },
                assertion_results=[
                    AssertionResult(
                        assertion_type=AssertionType.STATUS_CODE,
                        passed=False,
                        expected_value=404,
                        actual_value=200,
                        error_message="Expected 404 but got 200"
                    )
                ]
            ),
            TestResult(
                test_case_name="test_create_user_performance",
                status=ExecutionStatus.PASSED,
                response_time=2500,  # 较慢的响应
                actual_response={
                    "status_code": 201,
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"id": "456", "name": "Jane"}'
                },
                assertion_results=[
                    AssertionResult(
                        assertion_type=AssertionType.STATUS_CODE,
                        passed=True,
                        expected_value=201,
                        actual_value=201
                    ),
                    AssertionResult(
                        assertion_type=AssertionType.RESPONSE_TIME,
                        passed=False,
                        expected_value=1000,
                        actual_value=2500,
                        error_message="Response time exceeded 1000ms"
                    )
                ]
            )
        ]
    
    @pytest.fixture
    def sample_test_execution(self, sample_test_results):
        """示例测试执行"""
        return TestExecution(
            execution_id="exec_123",
            test_suite_name="User API Tests",
            status=ExecutionStatus.COMPLETED,
            start_time=datetime.utcnow() - timedelta(minutes=5),
            end_time=datetime.utcnow(),
            test_results=sample_test_results,
            total_tests=3,
            passed_tests=2,
            failed_tests=1,
            error_tests=0
        )
    
    @pytest.fixture
    def report_config(self):
        """报告配置"""
        return ReportConfig(
            include_performance_analysis=True,
            include_coverage_analysis=True,
            include_issue_analysis=True,
            include_recommendations=True,
            performance_threshold_ms=1000,
            coverage_threshold_percent=80
        )
    
    def test_analyze_test_execution(self, sample_test_execution, report_config):
        """测试分析测试执行结果"""
        report = self.analyzer.analyze_test_execution(sample_test_execution, report_config)
        
        assert isinstance(report, TestReport)
        assert report.execution_id == "exec_123"
        assert report.test_suite_name == "User API Tests"
        
        # 检查摘要
        assert isinstance(report.summary, ReportSummary)
        assert report.summary.total_tests == 3
        assert report.summary.passed_tests == 2
        assert report.summary.failed_tests == 1
        assert report.summary.success_rate == 66.67
        
        # 检查性能指标
        assert isinstance(report.performance_metrics, PerformanceMetrics)
        assert report.performance_metrics.avg_response_time > 0
        assert report.performance_metrics.max_response_time == 2500
        assert report.performance_metrics.min_response_time == 150
        
        # 检查问题分析
        assert isinstance(report.issue_analysis, IssueAnalysis)
        assert len(report.issue_analysis.failed_tests) == 1
        assert len(report.issue_analysis.performance_issues) > 0
    
    def test_generate_summary(self, sample_test_results):
        """测试生成测试摘要"""
        summary = self.analyzer._generate_summary(sample_test_results)
        
        assert isinstance(summary, ReportSummary)
        assert summary.total_tests == 3
        assert summary.passed_tests == 2
        assert summary.failed_tests == 1
        assert summary.error_tests == 0
        assert summary.success_rate == 66.67
        
        # 检查按测试类型统计（如果有的话）
        assert isinstance(summary.tests_by_type, dict)
    
    def test_analyze_performance(self, sample_test_results, report_config):
        """测试性能分析"""
        metrics = self.analyzer._analyze_performance(sample_test_results, report_config)
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_requests == 3
        assert metrics.avg_response_time == (150 + 200 + 2500) / 3
        assert metrics.max_response_time == 2500
        assert metrics.min_response_time == 150
        assert metrics.p95_response_time > 0
        assert metrics.p99_response_time > 0
        
        # 检查慢请求
        assert len(metrics.slow_requests) == 1
        assert metrics.slow_requests[0]["test_name"] == "test_create_user_performance"
        assert metrics.slow_requests[0]["response_time"] == 2500
    
    def test_analyze_coverage(self, sample_test_results):
        """测试覆盖率分析"""
        # 模拟端点信息
        endpoints = [
            {"path": "/users", "method": "GET"},
            {"path": "/users", "method": "POST"},
            {"path": "/users/{id}", "method": "GET"},
            {"path": "/users/{id}", "method": "PUT"},  # 未测试
            {"path": "/posts", "method": "GET"}  # 未测试
        ]
        
        coverage = self.analyzer._analyze_coverage(sample_test_results, endpoints)
        
        assert isinstance(coverage, TestCoverage)
        assert coverage.total_endpoints == 5
        assert coverage.tested_endpoints == 3  # 基于测试结果推断
        assert coverage.coverage_percentage == 60.0
        
        # 检查未测试的端点
        assert len(coverage.untested_endpoints) == 2
    
    def test_analyze_issues(self, sample_test_results, report_config):
        """测试问题分析"""
        issues = self.analyzer._analyze_issues(sample_test_results, report_config)
        
        assert isinstance(issues, IssueAnalysis)
        
        # 检查失败测试
        assert len(issues.failed_tests) == 1
        failed_test = issues.failed_tests[0]
        assert failed_test["test_name"] == "test_get_user_not_found"
        assert "Expected 404 but got 200" in failed_test["error_message"]
        
        # 检查性能问题
        assert len(issues.performance_issues) == 1
        perf_issue = issues.performance_issues[0]
        assert perf_issue["test_name"] == "test_create_user_performance"
        assert perf_issue["response_time"] == 2500
        
        # 检查断言失败
        assert len(issues.assertion_failures) == 2  # 状态码失败 + 响应时间失败
    
    def test_generate_recommendations_performance(self, sample_test_results, report_config):
        """测试生成性能相关建议"""
        recommendations = self.analyzer._generate_recommendations(sample_test_results, report_config)
        
        # 应该包含性能优化建议
        perf_recommendations = [
            rec for rec in recommendations 
            if "performance" in rec["description"].lower() or "response time" in rec["description"].lower()
        ]
        assert len(perf_recommendations) > 0
        
        # 检查建议级别
        high_priority_recs = [rec for rec in recommendations if rec["level"] == RecommendationLevel.HIGH]
        assert len(high_priority_recs) > 0
    
    def test_generate_recommendations_test_coverage(self, sample_test_results, report_config):
        """测试生成测试覆盖率相关建议"""
        # 模拟低覆盖率场景
        endpoints = [{"path": f"/endpoint{i}", "method": "GET"} for i in range(10)]
        
        with patch.object(self.analyzer, '_get_api_endpoints', return_value=endpoints):
            recommendations = self.analyzer._generate_recommendations(sample_test_results, report_config)
            
            # 应该包含覆盖率改进建议
            coverage_recommendations = [
                rec for rec in recommendations 
                if "coverage" in rec["description"].lower()
            ]
            assert len(coverage_recommendations) > 0
    
    def test_calculate_percentiles(self):
        """测试计算百分位数"""
        response_times = [100, 150, 200, 250, 300, 400, 500, 1000, 2000, 2500]
        
        p95 = self.analyzer._calculate_percentile(response_times, 95)
        p99 = self.analyzer._calculate_percentile(response_times, 99)
        
        assert p95 > 0
        assert p99 > p95
        assert p99 <= max(response_times)
    
    def test_categorize_test_results(self, sample_test_results):
        """测试测试结果分类"""
        categorized = self.analyzer._categorize_test_results(sample_test_results)
        
        assert "passed" in categorized
        assert "failed" in categorized
        assert "error" in categorized
        
        assert len(categorized["passed"]) == 2
        assert len(categorized["failed"]) == 1
        assert len(categorized["error"]) == 0
    
    def test_extract_error_patterns(self, sample_test_results):
        """测试提取错误模式"""
        patterns = self.analyzer._extract_error_patterns(sample_test_results)
        
        assert isinstance(patterns, list)
        # 应该识别出状态码不匹配的模式
        status_code_patterns = [
            p for p in patterns 
            if "status code" in p["pattern"].lower()
        ]
        assert len(status_code_patterns) > 0
    
    def test_calculate_test_stability(self):
        """测试计算测试稳定性"""
        # 模拟多次执行结果
        historical_results = [
            {"test_name": "test_stable", "passed": True},
            {"test_name": "test_stable", "passed": True},
            {"test_name": "test_stable", "passed": True},
            {"test_name": "test_flaky", "passed": True},
            {"test_name": "test_flaky", "passed": False},
            {"test_name": "test_flaky", "passed": True},
        ]
        
        stability = self.analyzer._calculate_test_stability(historical_results)
        
        assert "test_stable" in stability
        assert "test_flaky" in stability
        assert stability["test_stable"] == 100.0  # 100% 稳定
        assert stability["test_flaky"] == 66.67  # 66.67% 稳定
    
    def test_generate_trend_analysis(self):
        """测试生成趋势分析"""
        # 模拟历史执行数据
        historical_executions = [
            {
                "date": datetime.utcnow() - timedelta(days=7),
                "success_rate": 80.0,
                "avg_response_time": 300
            },
            {
                "date": datetime.utcnow() - timedelta(days=3),
                "success_rate": 85.0,
                "avg_response_time": 280
            },
            {
                "date": datetime.utcnow(),
                "success_rate": 90.0,
                "avg_response_time": 250
            }
        ]
        
        trends = self.analyzer._generate_trend_analysis(historical_executions)
        
        assert "success_rate_trend" in trends
        assert "performance_trend" in trends
        
        # 成功率应该是上升趋势
        assert trends["success_rate_trend"] == "improving"
        # 响应时间应该是下降趋势（改善）
        assert trends["performance_trend"] == "improving"
    
    def test_export_report_json(self, sample_test_execution, report_config):
        """测试导出JSON格式报告"""
        report = self.analyzer.analyze_test_execution(sample_test_execution, report_config)
        
        json_report = self.analyzer.export_report(report, format="json")
        
        assert isinstance(json_report, str)
        # 验证是有效的JSON
        import json
        parsed = json.loads(json_report)
        assert "execution_id" in parsed
        assert "summary" in parsed
        assert "performance_metrics" in parsed
    
    def test_export_report_html(self, sample_test_execution, report_config):
        """测试导出HTML格式报告"""
        report = self.analyzer.analyze_test_execution(sample_test_execution, report_config)
        
        html_report = self.analyzer.export_report(report, format="html")
        
        assert isinstance(html_report, str)
        assert "<html>" in html_report
        assert "<body>" in html_report
        assert report.test_suite_name in html_report
