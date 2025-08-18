#!/usr/bin/env python3
"""
健康检查脚本

用于检查Spec2Test应用和依赖服务的健康状态
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiohttp
import asyncpg
import redis.asyncio as redis

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化健康检查器
        
        Args:
            config: 配置字典，包含服务连接信息
        """
        self.config = config or {
            "app_url": "http://localhost:8000",
            "database_url": "postgresql://spec2test:spec2test123@localhost:5432/spec2test",
            "redis_url": "redis://localhost:6379/0",
            "timeout": 10
        }
        
        self.results = {}
    
    async def check_app_health(self) -> Tuple[bool, str]:
        """检查应用健康状态"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.config['app_url']}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return True, f"应用健康 - {data.get('status', 'OK')}"
                    else:
                        return False, f"应用响应异常 - HTTP {response.status}"
        
        except aiohttp.ClientError as e:
            return False, f"应用连接失败 - {str(e)}"
        except Exception as e:
            return False, f"应用检查异常 - {str(e)}"
    
    async def check_database_health(self) -> Tuple[bool, str]:
        """检查数据库健康状态"""
        try:
            conn = await asyncpg.connect(
                self.config["database_url"],
                command_timeout=self.config["timeout"]
            )
            
            # 执行简单查询
            result = await conn.fetchval("SELECT 1")
            
            # 检查表是否存在
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            await conn.close()
            
            if result == 1:
                return True, f"数据库健康 - 找到 {len(tables)} 个表"
            else:
                return False, "数据库查询异常"
        
        except asyncpg.PostgresError as e:
            return False, f"数据库连接失败 - {str(e)}"
        except Exception as e:
            return False, f"数据库检查异常 - {str(e)}"
    
    async def check_redis_health(self) -> Tuple[bool, str]:
        """检查Redis健康状态"""
        try:
            redis_client = redis.from_url(
                self.config["redis_url"],
                socket_timeout=self.config["timeout"]
            )
            
            # 执行ping命令
            pong = await redis_client.ping()
            
            # 获取Redis信息
            info = await redis_client.info()
            
            await redis_client.close()
            
            if pong:
                version = info.get('redis_version', 'unknown')
                return True, f"Redis健康 - 版本 {version}"
            else:
                return False, "Redis ping失败"
        
        except redis.RedisError as e:
            return False, f"Redis连接失败 - {str(e)}"
        except Exception as e:
            return False, f"Redis检查异常 - {str(e)}"
    
    async def check_disk_space(self, threshold: float = 0.8) -> Tuple[bool, str]:
        """检查磁盘空间"""
        try:
            import shutil
            
            # 检查根目录磁盘空间
            total, used, free = shutil.disk_usage("/")
            
            usage_percent = used / total
            
            if usage_percent < threshold:
                return True, f"磁盘空间充足 - 使用率 {usage_percent:.1%}"
            else:
                return False, f"磁盘空间不足 - 使用率 {usage_percent:.1%}"
        
        except Exception as e:
            return False, f"磁盘空间检查异常 - {str(e)}"
    
    async def check_memory_usage(self, threshold: float = 0.9) -> Tuple[bool, str]:
        """检查内存使用情况"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            usage_percent = memory.percent / 100
            
            if usage_percent < threshold:
                return True, f"内存使用正常 - 使用率 {usage_percent:.1%}"
            else:
                return False, f"内存使用过高 - 使用率 {usage_percent:.1%}"
        
        except ImportError:
            return True, "psutil未安装，跳过内存检查"
        except Exception as e:
            return False, f"内存检查异常 - {str(e)}"
    
    async def run_all_checks(self) -> Dict[str, Dict]:
        """运行所有健康检查"""
        checks = [
            ("app", self.check_app_health()),
            ("database", self.check_database_health()),
            ("redis", self.check_redis_health()),
            ("disk", self.check_disk_space()),
            ("memory", self.check_memory_usage())
        ]
        
        results = {}
        
        for name, check_coro in checks:
            try:
                start_time = time.time()
                healthy, message = await check_coro
                duration = time.time() - start_time
                
                results[name] = {
                    "healthy": healthy,
                    "message": message,
                    "duration": round(duration, 3),
                    "timestamp": time.time()
                }
                
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "message": f"检查失败 - {str(e)}",
                    "duration": 0,
                    "timestamp": time.time()
                }
        
        return results
    
    def print_results(self, results: Dict[str, Dict]) -> None:
        """打印检查结果"""
        print("🏥 Spec2Test 健康检查报告")
        print("=" * 50)
        
        all_healthy = True
        
        for service, result in results.items():
            status_icon = "✅" if result["healthy"] else "❌"
            duration = result["duration"]
            message = result["message"]
            
            print(f"{status_icon} {service.upper()}: {message} ({duration}s)")
            
            if not result["healthy"]:
                all_healthy = False
        
        print("=" * 50)
        
        if all_healthy:
            print("🎉 所有服务都健康运行！")
        else:
            print("⚠️ 发现健康问题，请检查上述失败的服务")
        
        return all_healthy
    
    def export_results(self, results: Dict[str, Dict], format: str = "json") -> str:
        """导出检查结果"""
        if format == "json":
            return json.dumps(results, indent=2)
        elif format == "prometheus":
            # 导出Prometheus格式的指标
            metrics = []
            for service, result in results.items():
                healthy = 1 if result["healthy"] else 0
                duration = result["duration"]
                
                metrics.append(f'health_check_status{{service="{service}"}} {healthy}')
                metrics.append(f'health_check_duration_seconds{{service="{service}"}} {duration}')
            
            return "\n".join(metrics)
        else:
            raise ValueError(f"不支持的导出格式: {format}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Spec2Test健康检查")
    parser.add_argument(
        "--app-url",
        default="http://localhost:8000",
        help="应用URL"
    )
    parser.add_argument(
        "--database-url",
        help="数据库连接URL"
    )
    parser.add_argument(
        "--redis-url",
        help="Redis连接URL"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="检查超时时间（秒）"
    )
    parser.add_argument(
        "--format",
        choices=["json", "prometheus", "text"],
        default="text",
        help="输出格式"
    )
    parser.add_argument(
        "--output",
        help="输出文件路径"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="持续监控模式"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="持续监控间隔（秒）"
    )
    
    args = parser.parse_args()
    
    # 构建配置
    config = {
        "app_url": args.app_url,
        "timeout": args.timeout
    }
    
    if args.database_url:
        config["database_url"] = args.database_url
    
    if args.redis_url:
        config["redis_url"] = args.redis_url
    
    checker = HealthChecker(config)
    
    try:
        if args.continuous:
            print(f"🔄 开始持续健康监控，间隔 {args.interval} 秒...")
            
            while True:
                results = await checker.run_all_checks()
                
                if args.format == "text":
                    print(f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}")
                    all_healthy = checker.print_results(results)
                else:
                    output = checker.export_results(results, args.format)
                    print(output)
                
                await asyncio.sleep(args.interval)
        
        else:
            results = await checker.run_all_checks()
            
            if args.format == "text":
                all_healthy = checker.print_results(results)
                sys.exit(0 if all_healthy else 1)
            else:
                output = checker.export_results(results, args.format)
                
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(output)
                    print(f"结果已保存到: {args.output}")
                else:
                    print(output)
    
    except KeyboardInterrupt:
        print("\n⏹️ 健康检查被用户中断")
        sys.exit(0)
    
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
