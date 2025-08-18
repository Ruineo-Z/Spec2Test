"""
结果分析模块

提供测试结果分析、报告生成和可视化功能。
"""

from .models import (
    FailureCategory, SeverityLevel, FailurePattern, FailureAnalysis,
    PerformanceMetrics, EndpointAnalysis, TrendData, AnalysisReport,
    AnalysisConfig, ComparisonReport
)
from .analyzer import ResultAnalyzer
from .reporter import ReportGenerator
from .visualizer import ReportVisualizer

__all__ = [
    # 枚举类
    "FailureCategory",
    "SeverityLevel",
    
    # 数据模型
    "FailurePattern",
    "FailureAnalysis",
    "PerformanceMetrics",
    "EndpointAnalysis",
    "TrendData",
    "AnalysisReport",
    "AnalysisConfig",
    "ComparisonReport",
    
    # 核心类
    "ResultAnalyzer",
    "ReportGenerator",
    "ReportVisualizer"
]
