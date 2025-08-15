"""
并发测试用例生成器

实现基于asyncio的并发测试用例生成，显著提升大量端点的生成效率。
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.core.shared.llm.factory import LLMFactory
from app.core.shared.llm.base import BaseLLMClient
from app.core.shared.utils.logger import get_logger
from app.core.document_analyzer.models import DocumentAnalysisResult, APIEndpoint

from .models import (
    GenerationConfig, GenerationResult, TestSuite, TestCase, 
    TestCaseType, TestCasePriority, TestStep, TestAssertion,
    LLMGenerationResponse, LLMTestCase
)
from .prompt_builder import PromptBuilder
from .case_generator import TestCaseGenerator


class ConcurrentTestCaseGenerator(TestCaseGenerator):
    """并发测试用例生成器
    
    继承自基础生成器，添加并发处理能力。
    """
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None, max_workers: int = 3):
        """初始化并发测试用例生成器
        
        Args:
            llm_config: LLM配置
            max_workers: 最大并发工作线程数
        """
        super().__init__(llm_config)
        self.max_workers = max_workers
        self.logger.info(f"并发测试用例生成器初始化完成，最大并发数: {max_workers}")
    
    def generate_test_cases_concurrent(self, 
                                     analysis_result: DocumentAnalysisResult,
                                     config: Optional[GenerationConfig] = None) -> GenerationResult:
        """并发生成测试用例
        
        Args:
            analysis_result: 文档分析结果
            config: 生成配置
            
        Returns:
            GenerationResult: 生成结果
        """
        start_time = time.time()
        
        try:
            self.logger.info("开始并发生成测试用例")
            
            # 使用默认配置
            if config is None:
                config = GenerationConfig()
            
            # 创建生成结果
            result = GenerationResult(
                success=True,
                config_used=config,
                generated_at=datetime.now()
            )
            
            # 检查是否有端点
            if not analysis_result.endpoints:
                result.add_error("文档分析结果中没有找到API端点")
                return result
            
            # 创建测试套件
            test_suite = TestSuite(
                suite_id=f"suite_{int(time.time())}",
                name=f"{analysis_result.title or 'API'} 测试套件",
                description=f"基于文档分析结果并发生成的测试套件",
                base_url=analysis_result.base_url
            )
            
            # 并发生成测试用例
            endpoint_results = self._generate_concurrent(analysis_result, config)
            
            # 汇总结果
            llm_calls = 0
            for endpoint, cases, success in endpoint_results:
                if success:
                    for case in cases:
                        test_suite.add_test_case(case)
                    llm_calls += 1
                    self.logger.info(f"端点 {endpoint.method} {endpoint.path} 生成了 {len(cases)} 个测试用例")
                else:
                    error_msg = f"端点 {endpoint.method} {endpoint.path} 生成失败"
                    self.logger.error(error_msg)
                    result.add_warning(error_msg)
            
            # 设置结果
            result.test_suite = test_suite
            result.total_cases_generated = len(test_suite.test_cases)
            result.llm_calls_count = llm_calls
            result.generation_duration = time.time() - start_time
            
            # 统计信息
            result.cases_by_type = self._count_cases_by_type(test_suite.test_cases)
            result.cases_by_priority = self._count_cases_by_priority(test_suite.test_cases)
            
            self.logger.info(f"并发测试用例生成完成: 共生成 {result.total_cases_generated} 个用例，耗时 {result.generation_duration:.2f}秒")
            
            return result
            
        except Exception as e:
            error_msg = f"并发测试用例生成失败: {str(e)}"
            self.logger.error(error_msg)
            
            result = GenerationResult(
                success=False,
                generation_duration=time.time() - start_time,
                config_used=config
            )
            result.add_error(error_msg)
            return result
    
    def _generate_concurrent(self, 
                           analysis_result: DocumentAnalysisResult,
                           config: GenerationConfig) -> List[tuple]:
        """并发生成所有端点的测试用例
        
        Args:
            analysis_result: 文档分析结果
            config: 生成配置
            
        Returns:
            List[tuple]: (endpoint, cases, success) 的列表
        """
        results = []
        
        # 使用ThreadPoolExecutor进行并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_endpoint = {
                executor.submit(
                    self._generate_single_endpoint_safe,
                    analysis_result, endpoint, config
                ): endpoint
                for endpoint in analysis_result.endpoints
            }
            
            # 收集结果
            for future in as_completed(future_to_endpoint):
                endpoint = future_to_endpoint[future]
                try:
                    cases = future.result()
                    results.append((endpoint, cases, True))
                except Exception as e:
                    self.logger.error(f"端点 {endpoint.method} {endpoint.path} 并发生成失败: {e}")
                    results.append((endpoint, [], False))
        
        return results
    
    def _generate_single_endpoint_safe(self, 
                                     analysis_result: DocumentAnalysisResult,
                                     endpoint: APIEndpoint,
                                     config: GenerationConfig) -> List[TestCase]:
        """安全地为单个端点生成测试用例（用于并发调用）
        
        Args:
            analysis_result: 文档分析结果
            endpoint: API端点
            config: 生成配置
            
        Returns:
            List[TestCase]: 生成的测试用例列表
        """
        try:
            # 为每个线程创建独立的LLM客户端
            thread_llm_client = LLMFactory.create_client("ollama", {
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:3b",
                "timeout": 300,
                "temperature": 0.3
            })
            
            # 构建提示词
            prompt = self.prompt_builder.build_test_generation_prompt(
                analysis_result, endpoint, config
            )
            
            # 调用LLM生成测试用例
            llm_response = thread_llm_client.generate_text(
                prompt=prompt,
                schema=LLMGenerationResponse.model_json_schema()
            )
            
            # 解析LLM响应
            generation_response = self._parse_llm_response(llm_response)
            
            # 转换为标准测试用例格式
            test_cases = self._convert_llm_cases_to_test_cases(
                generation_response.test_cases, endpoint, config
            )
            
            return test_cases
            
        except Exception as e:
            self.logger.error(f"为端点 {endpoint.method} {endpoint.path} 生成测试用例失败: {e}")
            return []


class AdaptiveTestCaseGenerator(TestCaseGenerator):
    """自适应测试用例生成器

    根据端点数量和LLM服务类型自动选择最优策略。
    """

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """初始化自适应生成器"""
        super().__init__(llm_config)

        # 从配置获取基础并发设置
        try:
            from app.config import get_performance_config
            perf_config = get_performance_config()
            base_max_workers = perf_config.max_concurrent_workers
            base_threshold = perf_config.concurrent_threshold
        except ImportError:
            # 如果无法导入配置，使用环境变量
            import os
            base_max_workers = int(os.getenv("SPEC2TEST_MAX_CONCURRENT_WORKERS", "8"))
            base_threshold = int(os.getenv("SPEC2TEST_CONCURRENT_THRESHOLD", "3"))

        # 根据LLM类型调整策略
        provider = (llm_config or {}).get("provider", "ollama")
        if provider == "ollama":
            # Ollama本地服务：保守的并发策略
            self.concurrent_threshold = max(base_threshold, 5)  # 至少5个端点才并发
            self.max_workers = min(base_max_workers, 3)  # 最多3个并发
        elif provider in ["openai", "claude", "gemini"]:
            # 云端服务：使用配置的并发策略
            self.concurrent_threshold = base_threshold
            self.max_workers = base_max_workers
        else:
            # 未知服务：中等策略
            self.concurrent_threshold = base_threshold + 1
            self.max_workers = min(base_max_workers, 5)

        self.concurrent_generator = ConcurrentTestCaseGenerator(llm_config, self.max_workers)

        self.logger.info(f"自适应生成器配置: 阈值={self.concurrent_threshold}, 最大并发={self.max_workers} (基于{provider}提供商)")
        
    def generate_test_cases_adaptive(self, 
                                   analysis_result: DocumentAnalysisResult,
                                   config: Optional[GenerationConfig] = None) -> GenerationResult:
        """自适应生成测试用例
        
        Args:
            analysis_result: 文档分析结果
            config: 生成配置
            
        Returns:
            GenerationResult: 生成结果
        """
        endpoint_count = len(analysis_result.endpoints)
        
        if endpoint_count >= self.concurrent_threshold:
            self.logger.info(f"端点数量 {endpoint_count} >= {self.concurrent_threshold}，使用并发模式")
            return self.concurrent_generator.generate_test_cases_concurrent(analysis_result, config)
        else:
            self.logger.info(f"端点数量 {endpoint_count} < {self.concurrent_threshold}，使用串行模式")
            return self.generate_test_cases(analysis_result, config)


# 性能对比工具
class PerformanceComparator:
    """性能对比工具"""
    
    @staticmethod
    def compare_serial_vs_concurrent(analysis_result: DocumentAnalysisResult,
                                   config: Optional[GenerationConfig] = None):
        """对比串行和并发性能
        
        Args:
            analysis_result: 文档分析结果
            config: 生成配置
        """
        logger = get_logger("PerformanceComparator")
        
        # 串行测试
        logger.info("🔄 开始串行生成测试...")
        serial_generator = TestCaseGenerator()
        serial_start = time.time()
        serial_result = serial_generator.generate_test_cases(analysis_result, config)
        serial_duration = time.time() - serial_start
        
        # 并发测试
        logger.info("⚡ 开始并发生成测试...")
        concurrent_generator = ConcurrentTestCaseGenerator()
        concurrent_start = time.time()
        concurrent_result = concurrent_generator.generate_test_cases_concurrent(analysis_result, config)
        concurrent_duration = time.time() - concurrent_start
        
        # 性能对比
        improvement = (serial_duration - concurrent_duration) / serial_duration * 100
        
        logger.info("📊 性能对比结果:")
        logger.info(f"   串行模式: {serial_duration:.2f}秒, {serial_result.total_cases_generated}个用例")
        logger.info(f"   并发模式: {concurrent_duration:.2f}秒, {concurrent_result.total_cases_generated}个用例")
        logger.info(f"   性能提升: {improvement:.1f}%")
        
        return {
            "serial_duration": serial_duration,
            "concurrent_duration": concurrent_duration,
            "improvement_percent": improvement,
            "serial_cases": serial_result.total_cases_generated,
            "concurrent_cases": concurrent_result.total_cases_generated
        }
