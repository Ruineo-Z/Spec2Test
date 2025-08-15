"""
HTTP性能监控器

提供HTTP请求的性能监控和统计功能。
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from app.core.shared.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RequestMetrics:
    """请求性能指标"""
    method: str
    url: str
    status_code: int
    response_time: float
    request_size: int
    response_size: int
    timestamp: float = field(default_factory=time.time)
    dns_lookup_time: Optional[float] = None
    tcp_connect_time: Optional[float] = None
    ssl_handshake_time: Optional[float] = None
    first_byte_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "method": self.method,
            "url": self.url,
            "status_code": self.status_code,
            "response_time": self.response_time,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "timestamp": self.timestamp,
            "dns_lookup_time": self.dns_lookup_time,
            "tcp_connect_time": self.tcp_connect_time,
            "ssl_handshake_time": self.ssl_handshake_time,
            "first_byte_time": self.first_byte_time
        }


class PerformanceMonitor:
    """HTTP性能监控器
    
    监控和统计HTTP请求的性能指标。
    """
    
    def __init__(self, max_records: int = 1000):
        """初始化性能监控器
        
        Args:
            max_records: 最大记录数量
        """
        self.max_records = max_records
        self.metrics: deque[RequestMetrics] = deque(maxlen=max_records)
        self.stats_cache: Dict[str, Any] = {}
        self.cache_timestamp = 0
        self.cache_ttl = 60  # 缓存TTL（秒）
        
        self.logger = get_logger(f"{self.__class__.__name__}")
    
    def create_metrics(self, method: str, url: str, status_code: int,
                      response_time: float, request_size: int, 
                      response_size: int, **kwargs) -> RequestMetrics:
        """创建请求指标
        
        Args:
            method: HTTP方法
            url: 请求URL
            status_code: 响应状态码
            response_time: 响应时间
            request_size: 请求大小
            response_size: 响应大小
            **kwargs: 其他指标
            
        Returns:
            RequestMetrics: 请求指标对象
        """
        return RequestMetrics(
            method=method,
            url=url,
            status_code=status_code,
            response_time=response_time,
            request_size=request_size,
            response_size=response_size,
            dns_lookup_time=kwargs.get("dns_lookup_time"),
            tcp_connect_time=kwargs.get("tcp_connect_time"),
            ssl_handshake_time=kwargs.get("ssl_handshake_time"),
            first_byte_time=kwargs.get("first_byte_time")
        )
    
    def record_request(self, metrics: RequestMetrics):
        """记录请求指标
        
        Args:
            metrics: 请求指标
        """
        self.metrics.append(metrics)
        
        # 清空缓存
        self.stats_cache.clear()
        self.cache_timestamp = 0
        
        self.logger.debug(f"记录请求指标: {metrics.method} {metrics.url} - {metrics.response_time:.3f}s")
    
    def get_stats(self, force_refresh: bool = False) -> Dict[str, Any]:
        """获取性能统计
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        current_time = time.time()
        
        # 检查缓存
        if (not force_refresh and 
            self.stats_cache and 
            current_time - self.cache_timestamp < self.cache_ttl):
            return self.stats_cache
        
        # 计算统计数据
        stats = self._calculate_stats()
        
        # 更新缓存
        self.stats_cache = stats
        self.cache_timestamp = current_time
        
        return stats
    
    def _calculate_stats(self) -> Dict[str, Any]:
        """计算统计数据
        
        Returns:
            Dict[str, Any]: 统计数据
        """
        if not self.metrics:
            return {
                "total_requests": 0,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "success_rate": 0,
                "error_rate": 0,
                "total_data_transferred": 0,
                "requests_per_second": 0,
                "status_code_distribution": {},
                "method_distribution": {},
                "response_time_percentiles": {}
            }
        
        metrics_list = list(self.metrics)
        total_requests = len(metrics_list)
        
        # 响应时间统计
        response_times = [m.response_time for m in metrics_list]
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        # 成功率统计
        successful_requests = sum(1 for m in metrics_list if 200 <= m.status_code < 400)
        success_rate = (successful_requests / total_requests) * 100
        error_rate = 100 - success_rate
        
        # 数据传输统计
        total_request_size = sum(m.request_size for m in metrics_list)
        total_response_size = sum(m.response_size for m in metrics_list)
        total_data_transferred = total_request_size + total_response_size
        
        # 请求频率统计
        if total_requests > 1:
            time_span = metrics_list[-1].timestamp - metrics_list[0].timestamp
            requests_per_second = total_requests / max(time_span, 1)
        else:
            requests_per_second = 0
        
        # 状态码分布
        status_code_distribution = defaultdict(int)
        for m in metrics_list:
            status_code_distribution[str(m.status_code)] += 1
        
        # HTTP方法分布
        method_distribution = defaultdict(int)
        for m in metrics_list:
            method_distribution[m.method] += 1
        
        # 响应时间百分位数
        response_time_percentiles = {}
        if response_times:
            percentiles = [50, 75, 90, 95, 99]
            for p in percentiles:
                try:
                    value = statistics.quantiles(response_times, n=100)[p-1]
                    response_time_percentiles[f"p{p}"] = value
                except (statistics.StatisticsError, IndexError):
                    response_time_percentiles[f"p{p}"] = 0
        
        return {
            "total_requests": total_requests,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "total_data_transferred": total_data_transferred,
            "total_request_size": total_request_size,
            "total_response_size": total_response_size,
            "requests_per_second": requests_per_second,
            "status_code_distribution": dict(status_code_distribution),
            "method_distribution": dict(method_distribution),
            "response_time_percentiles": response_time_percentiles
        }
    
    def get_recent_metrics(self, count: int = 10) -> List[RequestMetrics]:
        """获取最近的请求指标
        
        Args:
            count: 获取数量
            
        Returns:
            List[RequestMetrics]: 最近的请求指标列表
        """
        return list(self.metrics)[-count:]
    
    def get_slow_requests(self, threshold: float = 1.0) -> List[RequestMetrics]:
        """获取慢请求
        
        Args:
            threshold: 响应时间阈值（秒）
            
        Returns:
            List[RequestMetrics]: 慢请求列表
        """
        return [m for m in self.metrics if m.response_time > threshold]
    
    def get_error_requests(self) -> List[RequestMetrics]:
        """获取错误请求
        
        Returns:
            List[RequestMetrics]: 错误请求列表
        """
        return [m for m in self.metrics if m.status_code >= 400]
    
    def get_stats_by_method(self) -> Dict[str, Dict[str, Any]]:
        """按HTTP方法获取统计
        
        Returns:
            Dict[str, Dict[str, Any]]: 按方法分组的统计数据
        """
        method_stats = defaultdict(list)
        
        for m in self.metrics:
            method_stats[m.method].append(m)
        
        result = {}
        for method, metrics_list in method_stats.items():
            if metrics_list:
                response_times = [m.response_time for m in metrics_list]
                successful = sum(1 for m in metrics_list if 200 <= m.status_code < 400)
                
                result[method] = {
                    "count": len(metrics_list),
                    "avg_response_time": statistics.mean(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "success_rate": (successful / len(metrics_list)) * 100
                }
        
        return result
    
    def get_stats_by_status_code(self) -> Dict[str, Dict[str, Any]]:
        """按状态码获取统计
        
        Returns:
            Dict[str, Dict[str, Any]]: 按状态码分组的统计数据
        """
        status_stats = defaultdict(list)
        
        for m in self.metrics:
            status_stats[str(m.status_code)].append(m)
        
        result = {}
        for status_code, metrics_list in status_stats.items():
            if metrics_list:
                response_times = [m.response_time for m in metrics_list]
                
                result[status_code] = {
                    "count": len(metrics_list),
                    "avg_response_time": statistics.mean(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times)
                }
        
        return result
    
    def reset(self):
        """重置性能监控数据"""
        self.metrics.clear()
        self.stats_cache.clear()
        self.cache_timestamp = 0
        self.logger.info("性能监控数据已重置")
    
    def export_metrics(self, format: str = "json") -> str:
        """导出性能指标
        
        Args:
            format: 导出格式 (json, csv)
            
        Returns:
            str: 导出的数据
        """
        if format.lower() == "json":
            import json
            data = [m.to_dict() for m in self.metrics]
            return json.dumps(data, indent=2, ensure_ascii=False)
        
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if self.metrics:
                fieldnames = self.metrics[0].to_dict().keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for m in self.metrics:
                    writer.writerow(m.to_dict())
            
            return output.getvalue()
        
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def get_summary(self) -> str:
        """获取性能摘要
        
        Returns:
            str: 性能摘要文本
        """
        stats = self.get_stats()
        
        summary = f"""
HTTP性能监控摘要:
==================
总请求数: {stats['total_requests']}
平均响应时间: {stats['avg_response_time']:.3f}s
最小响应时间: {stats['min_response_time']:.3f}s
最大响应时间: {stats['max_response_time']:.3f}s
成功率: {stats['success_rate']:.1f}%
错误率: {stats['error_rate']:.1f}%
数据传输总量: {stats['total_data_transferred']} bytes
请求频率: {stats['requests_per_second']:.2f} req/s

响应时间百分位数:
P50: {stats['response_time_percentiles'].get('p50', 0):.3f}s
P75: {stats['response_time_percentiles'].get('p75', 0):.3f}s
P90: {stats['response_time_percentiles'].get('p90', 0):.3f}s
P95: {stats['response_time_percentiles'].get('p95', 0):.3f}s
P99: {stats['response_time_percentiles'].get('p99', 0):.3f}s
"""
        return summary.strip()
