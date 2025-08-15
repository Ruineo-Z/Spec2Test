"""
测试用例生成器

基于LLM的智能测试用例生成器，根据API文档分析结果生成高质量的测试用例。
"""

import json
import time
from typing import Dict, Any, List, Optional, Union
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


class TestCaseGenerator:
    """测试用例生成器
    
    使用LLM根据API文档分析结果生成智能化的测试用例。
    """
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """初始化测试用例生成器
        
        Args:
            llm_config: LLM配置，如果为None则使用默认配置
        """
        self.logger = get_logger(f"{self.__class__.__name__}")
        
        # 初始化LLM客户端
        try:
            # 从配置中获取提供商，默认使用ollama
            provider = (llm_config or {}).get("provider", "ollama")
            
            # 如果没有提供配置，使用可用的模型
            if not llm_config:
                llm_config = {
                    "base_url": "http://localhost:11434",
                    "model": "qwen2.5:3b",  # 使用可用的模型
                    "timeout": 300,
                    "temperature": 0.3
                }
            
            self.llm_client = LLMFactory.create_client(provider, llm_config)
            self.logger.info(f"LLM客户端初始化成功: {provider} ({llm_config.get('model', 'default')})")
        except Exception as e:
            self.logger.error(f"LLM客户端初始化失败: {e}")
            raise Exception(f"LLM客户端初始化失败，无法进行测试用例生成: {str(e)}")
        
        # 初始化提示词构建器
        self.prompt_builder = PromptBuilder()
        
        self.logger.info("测试用例生成器初始化完成")
    
    def generate_test_cases(self, 
                          analysis_result: DocumentAnalysisResult,
                          config: Optional[GenerationConfig] = None) -> GenerationResult:
        """生成测试用例
        
        Args:
            analysis_result: 文档分析结果
            config: 生成配置
            
        Returns:
            GenerationResult: 生成结果
        """
        start_time = time.time()
        
        try:
            self.logger.info("开始生成测试用例")
            
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
                description=f"基于文档分析结果自动生成的测试套件",
                base_url=analysis_result.base_url
            )
            
            # 为每个端点生成测试用例
            llm_calls = 0
            for endpoint in analysis_result.endpoints:
                try:
                    endpoint_cases = self._generate_endpoint_test_cases(
                        analysis_result, endpoint, config
                    )
                    
                    for case in endpoint_cases:
                        test_suite.add_test_case(case)
                    
                    llm_calls += 1
                    self.logger.info(f"为端点 {endpoint.method} {endpoint.path} 生成了 {len(endpoint_cases)} 个测试用例")
                    
                except Exception as e:
                    error_msg = f"为端点 {endpoint.method} {endpoint.path} 生成测试用例失败: {str(e)}"
                    self.logger.error(error_msg)
                    result.add_warning(error_msg)
                    continue
            
            # 设置结果
            result.test_suite = test_suite
            result.total_cases_generated = len(test_suite.test_cases)
            result.llm_calls_count = llm_calls
            result.generation_duration = time.time() - start_time
            
            # 统计信息
            result.cases_by_type = self._count_cases_by_type(test_suite.test_cases)
            result.cases_by_priority = self._count_cases_by_priority(test_suite.test_cases)
            
            self.logger.info(f"测试用例生成完成: 共生成 {result.total_cases_generated} 个用例，耗时 {result.generation_duration:.2f}秒")
            
            return result
            
        except Exception as e:
            error_msg = f"测试用例生成失败: {str(e)}"
            self.logger.error(error_msg)
            
            result = GenerationResult(
                success=False,
                generation_duration=time.time() - start_time,
                config_used=config
            )
            result.add_error(error_msg)
            return result
    
    def _generate_endpoint_test_cases(self, 
                                    analysis_result: DocumentAnalysisResult,
                                    endpoint: APIEndpoint,
                                    config: GenerationConfig) -> List[TestCase]:
        """为单个端点生成测试用例
        
        Args:
            analysis_result: 文档分析结果
            endpoint: API端点
            config: 生成配置
            
        Returns:
            List[TestCase]: 生成的测试用例列表
        """
        try:
            # 构建提示词
            prompt = self.prompt_builder.build_test_generation_prompt(
                analysis_result, endpoint, config
            )
            
            # 调用LLM生成测试用例
            llm_response = self.llm_client.generate_text(
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
            # 返回空列表而不是抛出异常，让调用者处理
            return []
    
    def _parse_llm_response(self, llm_response) -> LLMGenerationResponse:
        """解析LLM响应
        
        Args:
            llm_response: LLM响应对象
            
        Returns:
            LLMGenerationResponse: 解析后的响应
        """
        try:
            # 从LLM响应中提取内容
            if hasattr(llm_response, 'content'):
                content = llm_response.content
            elif hasattr(llm_response, 'text'):
                content = llm_response.text
            elif isinstance(llm_response, dict):
                content = llm_response.get("content", "")
            else:
                content = str(llm_response)
            
            # 尝试解析JSON
            if isinstance(content, str):
                # 提取JSON部分（如果有代码块包装）
                if "```json" in content:
                    start = content.find("```json") + 7
                    end = content.find("```", start)
                    if end != -1:
                        content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    if end != -1:
                        content = content[start:end].strip()
                
                response_data = json.loads(content)
            else:
                response_data = content
            
            # 验证和转换数据
            return LLMGenerationResponse(**response_data)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"LLM响应JSON解析失败: {e}")
            # 返回默认响应
            return LLMGenerationResponse(
                test_cases=[],
                summary="LLM响应解析失败",
                recommendations=["建议检查LLM输出格式"]
            )
        except Exception as e:
            self.logger.error(f"解析LLM响应失败: {e}")
            return LLMGenerationResponse(
                test_cases=[],
                summary="响应解析失败",
                recommendations=["建议重新生成"]
            )
    
    def _convert_llm_cases_to_test_cases(self, 
                                       llm_cases: List[LLMTestCase],
                                       endpoint: APIEndpoint,
                                       config: GenerationConfig) -> List[TestCase]:
        """将LLM生成的用例转换为标准测试用例格式
        
        Args:
            llm_cases: LLM生成的测试用例
            endpoint: API端点
            config: 生成配置
            
        Returns:
            List[TestCase]: 标准格式的测试用例列表
        """
        test_cases = []
        
        for i, llm_case in enumerate(llm_cases):
            try:
                # 生成用例ID
                case_id = f"{endpoint.method.lower()}_{endpoint.path.replace('/', '_').replace('{', '').replace('}', '')}_{i+1}"
                
                # 转换用例类型
                case_type = self._convert_case_type(llm_case.case_type)
                
                # 转换优先级
                priority = self._convert_priority(llm_case.priority)
                
                # 提取请求数据
                request_data = llm_case.request_data or {}
                headers = request_data.get("headers")
                params = request_data.get("params")
                body = request_data.get("body")
                
                # 转换断言
                assertions = self._convert_assertions(llm_case.assertions)
                
                # 创建测试用例
                test_case = TestCase(
                    case_id=case_id,
                    title=llm_case.title,
                    description=llm_case.description,
                    case_type=case_type,
                    priority=priority,
                    tags=llm_case.tags,
                    endpoint_path=endpoint.path,
                    http_method=endpoint.method,
                    request_headers=headers,
                    request_params=params,
                    request_body=body,
                    expected_status_code=llm_case.expected_status_code,
                    expected_response=llm_case.expected_response,
                    assertions=assertions,
                    estimated_duration=30.0  # 默认30秒
                )
                
                test_cases.append(test_case)
                
            except Exception as e:
                self.logger.error(f"转换测试用例失败: {e}")
                continue
        
        return test_cases
    
    def _convert_case_type(self, case_type_str: str) -> TestCaseType:
        """转换用例类型"""
        type_mapping = {
            "positive": TestCaseType.POSITIVE,
            "negative": TestCaseType.NEGATIVE,
            "boundary": TestCaseType.BOUNDARY,
            "security": TestCaseType.SECURITY,
            "performance": TestCaseType.PERFORMANCE,
            "integration": TestCaseType.INTEGRATION
        }
        return type_mapping.get(case_type_str.lower(), TestCaseType.POSITIVE)
    
    def _convert_priority(self, priority_str: str) -> TestCasePriority:
        """转换优先级"""
        priority_mapping = {
            "critical": TestCasePriority.CRITICAL,
            "high": TestCasePriority.HIGH,
            "medium": TestCasePriority.MEDIUM,
            "low": TestCasePriority.LOW
        }
        return priority_mapping.get(priority_str.lower(), TestCasePriority.MEDIUM)
    
    def _convert_assertions(self, llm_assertions: List[Dict[str, Any]]) -> List[TestAssertion]:
        """转换断言"""
        assertions = []
        
        for assertion_data in llm_assertions:
            try:
                assertion = TestAssertion(
                    assertion_type=assertion_data.get("type", "status_code"),
                    field_path=assertion_data.get("field"),
                    expected_value=assertion_data.get("expected"),
                    operator=assertion_data.get("operator", "equals"),
                    description=assertion_data.get("description", "")
                )
                assertions.append(assertion)
            except Exception as e:
                self.logger.error(f"转换断言失败: {e}")
                continue
        
        return assertions
    
    def _count_cases_by_type(self, test_cases: List[TestCase]) -> Dict[str, int]:
        """按类型统计测试用例"""
        counts = {}
        for case in test_cases:
            # 安全地获取类型值
            if hasattr(case.case_type, 'value'):
                case_type = case.case_type.value
            else:
                case_type = str(case.case_type)
            counts[case_type] = counts.get(case_type, 0) + 1
        return counts

    def _count_cases_by_priority(self, test_cases: List[TestCase]) -> Dict[str, int]:
        """按优先级统计测试用例"""
        counts = {}
        for case in test_cases:
            # 安全地获取优先级值
            if hasattr(case.priority, 'value'):
                priority = case.priority.value
            else:
                priority = str(case.priority)
            counts[priority] = counts.get(priority, 0) + 1
        return counts
