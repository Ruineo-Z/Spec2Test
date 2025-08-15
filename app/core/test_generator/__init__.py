"""
测试生成器模块

基于LLM的智能测试用例生成器，能够根据API文档分析结果生成高质量的测试用例。

主要组件:
- TestCaseGenerator: 核心测试用例生成器
- PromptBuilder: 提示词构建器
- 数据模型: 测试生成相关的数据结构

使用示例:
    from app.core.test_generator import TestCaseGenerator, GenerationConfig
    from app.core.document_analyzer import DocumentAnalyzer
    
    # 分析文档
    analyzer = DocumentAnalyzer()
    analysis_result = analyzer.analyze_file("api_spec.json")
    
    # 生成测试用例
    generator = TestCaseGenerator()
    config = GenerationConfig(
        include_positive=True,
        include_negative=True,
        max_cases_per_endpoint=5
    )
    
    result = generator.generate_test_cases(analysis_result, config)
    
    if result.success:
        print(f"生成了 {result.total_cases_generated} 个测试用例")
        test_suite = result.test_suite
    else:
        print(f"生成失败: {result.errors}")
"""

from .case_generator import TestCaseGenerator
from .prompt_builder import PromptBuilder
from .models import (
    # 枚举类型
    TestCaseType,
    TestCasePriority,
    TestDataType,
    GenerationStrategy,
    
    # 数据模型
    TestStep,
    TestAssertion,
    TestCase,
    TestSuite,
    GenerationConfig,
    GenerationResult,
    
    # LLM响应模型
    LLMTestCase,
    LLMGenerationResponse
)

__all__ = [
    # 主要类
    "TestCaseGenerator",
    "PromptBuilder",
    
    # 枚举类型
    "TestCaseType",
    "TestCasePriority", 
    "TestDataType",
    "GenerationStrategy",
    
    # 数据模型
    "TestStep",
    "TestAssertion",
    "TestCase",
    "TestSuite",
    "GenerationConfig",
    "GenerationResult",
    
    # LLM响应模型
    "LLMTestCase",
    "LLMGenerationResponse"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Spec2Test Team"
__description__ = "基于LLM的智能API测试用例生成器"
