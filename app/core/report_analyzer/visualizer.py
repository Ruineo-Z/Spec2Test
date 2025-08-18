"""
可视化组件

生成测试结果的图表和可视化内容。
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from app.core.shared.utils.logger import get_logger
from .models import AnalysisReport, AnalysisConfig, PerformanceMetrics, EndpointAnalysis


class ReportVisualizer:
    """报告可视化器
    
    生成各种图表和可视化内容。
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """初始化可视化器
        
        Args:
            config: 分析配置
        """
        self.config = config or AnalysisConfig()
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        self.logger.info("报告可视化器初始化完成")
    
    def generate_success_rate_chart(self, report: AnalysisReport) -> str:
        """生成成功率饼图
        
        Args:
            report: 分析报告
            
        Returns:
            str: Chart.js配置的JSON字符串
        """
        metrics = report.overall_metrics
        
        chart_config = {
            "type": "pie",
            "data": {
                "labels": ["成功", "失败", "错误", "跳过"],
                "datasets": [{
                    "data": [
                        metrics.passed_tests,
                        metrics.failed_tests,
                        metrics.error_tests,
                        metrics.skipped_tests
                    ],
                    "backgroundColor": [
                        "#28a745",  # 绿色 - 成功
                        "#dc3545",  # 红色 - 失败
                        "#fd7e14",  # 橙色 - 错误
                        "#6c757d"   # 灰色 - 跳过
                    ],
                    "borderWidth": 2,
                    "borderColor": "#ffffff"
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "测试结果分布",
                        "font": {"size": 16}
                    },
                    "legend": {
                        "position": "bottom"
                    }
                }
            }
        }
        
        return json.dumps(chart_config, ensure_ascii=False)
    
    def generate_response_time_chart(self, report: AnalysisReport) -> str:
        """生成响应时间柱状图
        
        Args:
            report: 分析报告
            
        Returns:
            str: Chart.js配置的JSON字符串
        """
        if not report.endpoint_analyses:
            return "{}"
        
        # 按响应时间排序，取前10个
        sorted_endpoints = sorted(report.endpoint_analyses, 
                                key=lambda x: x.avg_response_time, reverse=True)[:10]
        
        labels = [f"{ep.http_method} {ep.endpoint_path}" for ep in sorted_endpoints]
        data = [ep.avg_response_time for ep in sorted_endpoints]
        
        # 根据响应时间设置颜色
        colors = []
        for time in data:
            if time <= 1.0:
                colors.append("#28a745")  # 绿色 - 快
            elif time <= 3.0:
                colors.append("#ffc107")  # 黄色 - 中等
            else:
                colors.append("#dc3545")  # 红色 - 慢
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "平均响应时间 (秒)",
                    "data": data,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "端点响应时间分析",
                        "font": {"size": 16}
                    },
                    "legend": {
                        "display": False
                    }
                },
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {
                            "display": True,
                            "text": "响应时间 (秒)"
                        }
                    },
                    "x": {
                        "ticks": {
                            "maxRotation": 45
                        }
                    }
                }
            }
        }
        
        return json.dumps(chart_config, ensure_ascii=False)
    
    def generate_endpoint_success_rate_chart(self, report: AnalysisReport) -> str:
        """生成端点成功率图表
        
        Args:
            report: 分析报告
            
        Returns:
            str: Chart.js配置的JSON字符串
        """
        if not report.endpoint_analyses:
            return "{}"
        
        # 按成功率排序
        sorted_endpoints = sorted(report.endpoint_analyses, 
                                key=lambda x: x.success_rate)
        
        labels = [f"{ep.http_method} {ep.endpoint_path}" for ep in sorted_endpoints]
        data = [ep.success_rate * 100 for ep in sorted_endpoints]  # 转换为百分比
        
        # 根据成功率设置颜色
        colors = []
        for rate in data:
            if rate >= 80:
                colors.append("#28a745")  # 绿色 - 高成功率
            elif rate >= 50:
                colors.append("#ffc107")  # 黄色 - 中等成功率
            else:
                colors.append("#dc3545")  # 红色 - 低成功率
        
        chart_config = {
            "type": "horizontalBar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "成功率 (%)",
                    "data": data,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "端点成功率分析",
                        "font": {"size": 16}
                    },
                    "legend": {
                        "display": False
                    }
                },
                "scales": {
                    "x": {
                        "beginAtZero": True,
                        "max": 100,
                        "title": {
                            "display": True,
                            "text": "成功率 (%)"
                        }
                    }
                }
            }
        }
        
        return json.dumps(chart_config, ensure_ascii=False)
    
    def generate_failure_category_chart(self, report: AnalysisReport) -> str:
        """生成失败类别分布图
        
        Args:
            report: 分析报告
            
        Returns:
            str: Chart.js配置的JSON字符串
        """
        if not report.top_failure_categories:
            return "{}"
        
        labels = [category["category"] for category in report.top_failure_categories]
        data = [category["count"] for category in report.top_failure_categories]
        
        # 为不同失败类别设置颜色
        color_map = {
            "network_error": "#dc3545",      # 红色
            "timeout_error": "#fd7e14",      # 橙色
            "http_error": "#ffc107",         # 黄色
            "assertion_error": "#17a2b8",    # 青色
            "auth_error": "#6f42c1",         # 紫色
            "validation_error": "#e83e8c",   # 粉色
            "server_error": "#dc3545",       # 红色
            "client_error": "#ffc107",       # 黄色
            "unknown_error": "#6c757d"       # 灰色
        }
        
        colors = [color_map.get(label, "#6c757d") for label in labels]
        
        chart_config = {
            "type": "doughnut",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": colors,
                    "borderWidth": 2,
                    "borderColor": "#ffffff"
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "失败类别分布",
                        "font": {"size": 16}
                    },
                    "legend": {
                        "position": "bottom"
                    }
                }
            }
        }
        
        return json.dumps(chart_config, ensure_ascii=False)
    
    def generate_performance_radar_chart(self, report: AnalysisReport) -> str:
        """生成性能雷达图
        
        Args:
            report: 分析报告
            
        Returns:
            str: Chart.js配置的JSON字符串
        """
        metrics = report.overall_metrics
        
        # 将各项指标标准化到0-100的范围
        success_rate_score = metrics.success_rate * 100
        
        # 响应时间评分 (越低越好，转换为评分)
        response_time_score = max(0, 100 - (metrics.avg_response_time * 20))
        
        # 稳定性评分 (基于失败率)
        stability_score = (1 - metrics.failure_rate) * 100
        
        # 效率评分 (基于测试执行时间)
        efficiency_score = max(0, 100 - (metrics.total_execution_time / metrics.total_tests * 10))
        
        # 覆盖率评分 (基于测试数量，假设更多测试意味着更好的覆盖)
        coverage_score = min(100, metrics.total_tests * 5)
        
        chart_config = {
            "type": "radar",
            "data": {
                "labels": ["成功率", "响应速度", "稳定性", "执行效率", "测试覆盖"],
                "datasets": [{
                    "label": "性能指标",
                    "data": [
                        success_rate_score,
                        response_time_score,
                        stability_score,
                        efficiency_score,
                        coverage_score
                    ],
                    "backgroundColor": "rgba(40, 167, 69, 0.2)",
                    "borderColor": "#28a745",
                    "borderWidth": 2,
                    "pointBackgroundColor": "#28a745",
                    "pointBorderColor": "#ffffff",
                    "pointBorderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "综合性能评估",
                        "font": {"size": 16}
                    }
                },
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "max": 100,
                        "ticks": {
                            "stepSize": 20
                        }
                    }
                }
            }
        }
        
        return json.dumps(chart_config, ensure_ascii=False)
    
    def generate_trend_chart(self, trend_data: List[Dict[str, Any]]) -> str:
        """生成趋势图表
        
        Args:
            trend_data: 趋势数据列表
            
        Returns:
            str: Chart.js配置的JSON字符串
        """
        if not trend_data:
            return "{}"
        
        # 提取时间标签和数据
        labels = [data["timestamp"] for data in trend_data]
        success_rates = [data["success_rate"] * 100 for data in trend_data]
        response_times = [data["avg_response_time"] for data in trend_data]
        
        chart_config = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "成功率 (%)",
                        "data": success_rates,
                        "borderColor": "#28a745",
                        "backgroundColor": "rgba(40, 167, 69, 0.1)",
                        "borderWidth": 2,
                        "fill": True,
                        "yAxisID": "y"
                    },
                    {
                        "label": "平均响应时间 (秒)",
                        "data": response_times,
                        "borderColor": "#007bff",
                        "backgroundColor": "rgba(0, 123, 255, 0.1)",
                        "borderWidth": 2,
                        "fill": True,
                        "yAxisID": "y1"
                    }
                ]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": "性能趋势分析",
                        "font": {"size": 16}
                    }
                },
                "scales": {
                    "x": {
                        "title": {
                            "display": True,
                            "text": "时间"
                        }
                    },
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "title": {
                            "display": True,
                            "text": "成功率 (%)"
                        },
                        "min": 0,
                        "max": 100
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {
                            "display": True,
                            "text": "响应时间 (秒)"
                        },
                        "grid": {
                            "drawOnChartArea": False
                        }
                    }
                }
            }
        }
        
        return json.dumps(chart_config, ensure_ascii=False)
    
    def generate_html_with_charts(self, report: AnalysisReport) -> str:
        """生成包含图表的HTML报告
        
        Args:
            report: 分析报告
            
        Returns:
            str: 包含图表的HTML内容
        """
        if not self.config.enable_charts:
            return ""
        
        # 生成各种图表配置
        success_rate_chart = self.generate_success_rate_chart(report)
        response_time_chart = self.generate_response_time_chart(report)
        endpoint_success_chart = self.generate_endpoint_success_rate_chart(report)
        failure_category_chart = self.generate_failure_category_chart(report)
        performance_radar_chart = self.generate_performance_radar_chart(report)
        
        html_template = f"""
        <div class="charts-section">
            <h2>📊 可视化分析</h2>
            
            <div class="chart-grid">
                <div class="chart-container">
                    <canvas id="successRateChart" width="{self.config.chart_width}" height="{self.config.chart_height}"></canvas>
                </div>
                
                <div class="chart-container">
                    <canvas id="responseTimeChart" width="{self.config.chart_width}" height="{self.config.chart_height}"></canvas>
                </div>
                
                <div class="chart-container">
                    <canvas id="endpointSuccessChart" width="{self.config.chart_width}" height="{self.config.chart_height}"></canvas>
                </div>
                
                <div class="chart-container">
                    <canvas id="failureCategoryChart" width="{self.config.chart_width}" height="{self.config.chart_height}"></canvas>
                </div>
                
                <div class="chart-container">
                    <canvas id="performanceRadarChart" width="{self.config.chart_width}" height="{self.config.chart_height}"></canvas>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // 成功率饼图
            const successRateCtx = document.getElementById('successRateChart').getContext('2d');
            new Chart(successRateCtx, {success_rate_chart});
            
            // 响应时间柱状图
            const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
            new Chart(responseTimeCtx, {response_time_chart});
            
            // 端点成功率图
            const endpointSuccessCtx = document.getElementById('endpointSuccessChart').getContext('2d');
            new Chart(endpointSuccessCtx, {endpoint_success_chart});
            
            // 失败类别分布图
            const failureCategoryCtx = document.getElementById('failureCategoryChart').getContext('2d');
            new Chart(failureCategoryCtx, {failure_category_chart});
            
            // 性能雷达图
            const performanceRadarCtx = document.getElementById('performanceRadarChart').getContext('2d');
            new Chart(performanceRadarCtx, {performance_radar_chart});
        </script>
        
        <style>
            .charts-section {{ margin: 30px 0; }}
            .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; }}
            .chart-container {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        </style>
        """
        
        return html_template
    
    def export_chart_data(self, report: AnalysisReport) -> Dict[str, Any]:
        """导出图表数据
        
        Args:
            report: 分析报告
            
        Returns:
            Dict[str, Any]: 图表数据字典
        """
        return {
            "success_rate_chart": json.loads(self.generate_success_rate_chart(report)),
            "response_time_chart": json.loads(self.generate_response_time_chart(report)),
            "endpoint_success_chart": json.loads(self.generate_endpoint_success_rate_chart(report)),
            "failure_category_chart": json.loads(self.generate_failure_category_chart(report)),
            "performance_radar_chart": json.loads(self.generate_performance_radar_chart(report)),
        }
