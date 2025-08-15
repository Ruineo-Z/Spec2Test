#!/usr/bin/env python3
"""
并发优化测试脚本

测试不同LLM提供商和并发数配置的性能表现。
"""

import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.shared.utils.logger import get_logger
from app.core.document_analyzer import DocumentAnalyzer
from app.core.test_generator import TestCaseGenerator, GenerationConfig
from app.core.test_generator.concurrent_generator import ConcurrentTestCaseGenerator


def test_ollama_concurrent_scaling():
    """测试Ollama的并发扩展性"""
    logger = get_logger("test_ollama_scaling")
    
    logger.info("🔄 测试Ollama并发扩展性...")
    
    # 分析文档
    analyzer = DocumentAnalyzer()
    api_file = project_root / "examples" / "sample_api.json"
    analysis_result = analyzer.analyze_file(str(api_file))
    
    # 测试不同并发数
    concurrent_workers = [1, 2, 3, 4, 5]
    results = []
    
    for workers in concurrent_workers:
        logger.info(f"\n📊 测试 {workers} 个并发线程...")
        
        try:
            # 配置
            config = GenerationConfig(
                include_positive=True,
                include_negative=False,
                max_cases_per_endpoint=2,
                max_concurrent_workers=workers
            )
            
            # 并发生成
            generator = ConcurrentTestCaseGenerator(max_workers=workers)
            start_time = time.time()
            result = generator.generate_test_cases_concurrent(analysis_result, config)
            duration = time.time() - start_time
            
            results.append({
                "workers": workers,
                "duration": duration,
                "cases": result.total_cases_generated,
                "success": result.success
            })
            
            logger.info(f"   ⏱️  耗时: {duration:.2f}秒")
            logger.info(f"   📊 用例数: {result.total_cases_generated}")
            logger.info(f"   ✅ 成功: {result.success}")
            
        except Exception as e:
            logger.error(f"   ❌ 失败: {e}")
            results.append({
                "workers": workers,
                "duration": float('inf'),
                "cases": 0,
                "success": False
            })
    
    # 分析结果
    logger.info(f"\n📈 Ollama并发扩展性分析:")
    logger.info(f"{'并发数':<8} {'耗时(秒)':<10} {'用例数':<8} {'效率':<10}")
    logger.info("-" * 40)
    
    baseline_duration = None
    for result in results:
        if result["success"]:
            if baseline_duration is None:
                baseline_duration = result["duration"]
                efficiency = "基准"
            else:
                speedup = baseline_duration / result["duration"]
                efficiency = f"{speedup:.2f}x"
            
            logger.info(f"{result['workers']:<8} {result['duration']:<10.2f} {result['cases']:<8} {efficiency:<10}")
        else:
            logger.info(f"{result['workers']:<8} {'失败':<10} {result['cases']:<8} {'N/A':<10}")
    
    return results


def test_gemini_concurrent_performance():
    """测试Gemini的并发性能（如果配置了API密钥）"""
    logger = get_logger("test_gemini_performance")
    
    # 检查是否配置了Gemini API密钥
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.info("⚠️  未配置GEMINI_API_KEY环境变量，跳过Gemini测试")
        return None
    
    logger.info("☁️  测试Gemini并发性能...")
    
    try:
        # 分析文档
        analyzer = DocumentAnalyzer()
        api_file = project_root / "examples" / "sample_api.json"
        analysis_result = analyzer.analyze_file(str(api_file))
        
        # Gemini配置
        gemini_config = {
            "provider": "gemini",
            "api_key": gemini_api_key,
            "model": "gemini-pro",
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        # 测试不同并发数
        concurrent_workers = [1, 3, 5, 8, 10]
        results = []
        
        for workers in concurrent_workers:
            logger.info(f"\n📊 测试Gemini {workers}个并发线程...")
            
            try:
                config = GenerationConfig(
                    include_positive=True,
                    include_negative=False,
                    max_cases_per_endpoint=2,
                    max_concurrent_workers=workers
                )
                
                generator = ConcurrentTestCaseGenerator(gemini_config, max_workers=workers)
                start_time = time.time()
                result = generator.generate_test_cases_concurrent(analysis_result, config)
                duration = time.time() - start_time
                
                results.append({
                    "workers": workers,
                    "duration": duration,
                    "cases": result.total_cases_generated,
                    "success": result.success
                })
                
                logger.info(f"   ⏱️  耗时: {duration:.2f}秒")
                logger.info(f"   📊 用例数: {result.total_cases_generated}")
                logger.info(f"   ✅ 成功: {result.success}")
                
            except Exception as e:
                logger.error(f"   ❌ 失败: {e}")
                results.append({
                    "workers": workers,
                    "duration": float('inf'),
                    "cases": 0,
                    "success": False
                })
        
        # 分析结果
        logger.info(f"\n📈 Gemini并发扩展性分析:")
        logger.info(f"{'并发数':<8} {'耗时(秒)':<10} {'用例数':<8} {'效率':<10}")
        logger.info("-" * 40)
        
        baseline_duration = None
        for result in results:
            if result["success"]:
                if baseline_duration is None:
                    baseline_duration = result["duration"]
                    efficiency = "基准"
                else:
                    speedup = baseline_duration / result["duration"]
                    efficiency = f"{speedup:.2f}x"
                
                logger.info(f"{result['workers']:<8} {result['duration']:<10.2f} {result['cases']:<8} {efficiency:<10}")
            else:
                logger.info(f"{result['workers']:<8} {'失败':<10} {result['cases']:<8} {'N/A':<10}")
        
        return results
        
    except Exception as e:
        logger.error(f"💥 Gemini测试失败: {e}")
        return None


def compare_providers_performance():
    """对比不同提供商的性能"""
    logger = get_logger("compare_providers")
    
    logger.info("🆚 对比不同LLM提供商性能...")
    
    # 分析文档
    analyzer = DocumentAnalyzer()
    api_file = project_root / "examples" / "sample_api.json"
    analysis_result = analyzer.analyze_file(str(api_file))
    
    providers_config = [
        {
            "name": "Ollama",
            "config": {
                "provider": "ollama",
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:3b",
                "temperature": 0.3
            },
            "optimal_workers": 2
        }
    ]
    
    # 如果有Gemini API密钥，添加Gemini测试
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        providers_config.append({
            "name": "Gemini",
            "config": {
                "provider": "gemini",
                "api_key": gemini_api_key,
                "model": "gemini-pro",
                "temperature": 0.3
            },
            "optimal_workers": 5
        })
    
    results = []
    
    for provider_info in providers_config:
        name = provider_info["name"]
        config = provider_info["config"]
        workers = provider_info["optimal_workers"]
        
        logger.info(f"\n🧪 测试 {name} (并发数: {workers})...")
        
        try:
            gen_config = GenerationConfig(
                include_positive=True,
                include_negative=False,
                max_cases_per_endpoint=2,
                max_concurrent_workers=workers
            )
            
            # 串行测试
            serial_generator = TestCaseGenerator(config)
            start_time = time.time()
            serial_result = serial_generator.generate_test_cases(analysis_result, gen_config)
            serial_duration = time.time() - start_time
            
            # 并发测试
            concurrent_generator = ConcurrentTestCaseGenerator(config, max_workers=workers)
            start_time = time.time()
            concurrent_result = concurrent_generator.generate_test_cases_concurrent(analysis_result, gen_config)
            concurrent_duration = time.time() - start_time
            
            # 计算提升
            improvement = (serial_duration - concurrent_duration) / serial_duration * 100 if serial_duration > 0 else 0
            
            result = {
                "provider": name,
                "workers": workers,
                "serial_duration": serial_duration,
                "concurrent_duration": concurrent_duration,
                "improvement": improvement,
                "serial_cases": serial_result.total_cases_generated,
                "concurrent_cases": concurrent_result.total_cases_generated,
                "success": serial_result.success and concurrent_result.success
            }
            
            results.append(result)
            
            logger.info(f"   串行: {serial_duration:.2f}秒, {serial_result.total_cases_generated}用例")
            logger.info(f"   并发: {concurrent_duration:.2f}秒, {concurrent_result.total_cases_generated}用例")
            logger.info(f"   提升: {improvement:.1f}%")
            
        except Exception as e:
            logger.error(f"   ❌ {name} 测试失败: {e}")
            results.append({
                "provider": name,
                "workers": workers,
                "serial_duration": float('inf'),
                "concurrent_duration": float('inf'),
                "improvement": 0,
                "success": False
            })
    
    # 总结对比
    logger.info(f"\n📊 提供商性能对比总结:")
    logger.info(f"{'提供商':<10} {'并发数':<8} {'串行(秒)':<10} {'并发(秒)':<10} {'提升':<10}")
    logger.info("-" * 55)
    
    for result in results:
        if result["success"]:
            logger.info(f"{result['provider']:<10} {result['workers']:<8} {result['serial_duration']:<10.2f} {result['concurrent_duration']:<10.2f} {result['improvement']:<10.1f}%")
        else:
            logger.info(f"{result['provider']:<10} {result['workers']:<8} {'失败':<10} {'失败':<10} {'N/A':<10}")
    
    return results


def main():
    """主函数"""
    logger = get_logger(__name__)
    
    logger.info("🚀 开始并发优化测试...")
    
    tests = [
        ("Ollama并发扩展性", test_ollama_concurrent_scaling),
        ("Gemini并发性能", test_gemini_concurrent_performance),
        ("提供商性能对比", compare_providers_performance),
    ]
    
    all_results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 执行: {test_name}")
        try:
            result = test_func()
            all_results[test_name] = result
            if result is not None:
                logger.info(f"✅ {test_name} 完成")
            else:
                logger.info(f"⚠️  {test_name} 跳过")
        except Exception as e:
            logger.error(f"💥 {test_name} 异常: {e}")
            all_results[test_name] = None
    
    # 最终建议
    logger.info(f"\n🎯 并发优化建议:")
    
    if all_results.get("Ollama并发扩展性"):
        ollama_results = all_results["Ollama并发扩展性"]
        best_ollama = min([r for r in ollama_results if r["success"]], key=lambda x: x["duration"], default=None)
        if best_ollama:
            logger.info(f"   🖥️  Ollama最优并发数: {best_ollama['workers']} (耗时: {best_ollama['duration']:.2f}秒)")
    
    if all_results.get("Gemini并发性能"):
        gemini_results = all_results["Gemini并发性能"]
        if gemini_results:
            best_gemini = min([r for r in gemini_results if r["success"]], key=lambda x: x["duration"], default=None)
            if best_gemini:
                logger.info(f"   ☁️  Gemini最优并发数: {best_gemini['workers']} (耗时: {best_gemini['duration']:.2f}秒)")
    
    if all_results.get("提供商性能对比"):
        comparison = all_results["提供商性能对比"]
        if comparison:
            best_provider = max([r for r in comparison if r["success"]], key=lambda x: x["improvement"], default=None)
            if best_provider:
                logger.info(f"   🏆 最佳提供商: {best_provider['provider']} (提升: {best_provider['improvement']:.1f}%)")
    
    logger.info(f"\n🎉 并发优化测试完成!")


if __name__ == "__main__":
    main()
