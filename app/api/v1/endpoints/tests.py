"""
测试相关API端点

提供测试用例生成、管理和执行功能。
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.core.shared.utils.logger import get_logger
from app.core.test_generator import TestCaseGenerator, GenerationConfig
from app.core.test_executor import TestRunner, ExecutionConfig
from app.api.v1.endpoints.documents import documents_store, analysis_results_store


# 创建路由器
router = APIRouter(prefix="/tests", tags=["测试"])
logger = get_logger(__name__)


# 请求/响应模型
class TestGenerationRequest(BaseModel):
    """测试生成请求"""
    document_id: str = Field(description="文档ID")
    config: Optional[Dict[str, Any]] = Field(default=None, description="生成配置")
    test_scenarios: Optional[List[str]] = Field(default=None, description="测试场景")


class TestGenerationResponse(BaseModel):
    """测试生成响应"""
    test_suite_id: str = Field(description="测试套件ID")
    document_id: str = Field(description="文档ID")
    status: str = Field(description="生成状态")
    started_at: datetime = Field(description="开始时间")
    message: str = Field(description="状态消息")


class TestSuiteInfo(BaseModel):
    """测试套件信息"""
    test_suite_id: str = Field(description="测试套件ID")
    document_id: str = Field(description="文档ID")
    suite_name: str = Field(description="套件名称")
    total_tests: int = Field(description="总测试数")
    created_at: datetime = Field(description="创建时间")
    status: str = Field(description="状态")
    test_cases: Optional[List[Dict[str, Any]]] = Field(default=None, description="测试用例")


class TestExecutionRequest(BaseModel):
    """测试执行请求"""
    base_url: str = Field(description="测试目标URL")
    config: Optional[Dict[str, Any]] = Field(default=None, description="执行配置")
    selected_tests: Optional[List[str]] = Field(default=None, description="选择的测试用例ID")


class TestExecutionResponse(BaseModel):
    """测试执行响应"""
    execution_id: str = Field(description="执行ID")
    test_suite_id: str = Field(description="测试套件ID")
    status: str = Field(description="执行状态")
    started_at: datetime = Field(description="开始时间")
    message: str = Field(description="状态消息")


# 简单的内存存储
test_suites_store: Dict[str, Dict[str, Any]] = {}
test_executions_store: Dict[str, Dict[str, Any]] = {}


@router.post("/generate", response_model=TestGenerationResponse, summary="生成测试用例")
async def generate_test_cases(
    request: TestGenerationRequest,
    background_tasks: BackgroundTasks
) -> TestGenerationResponse:
    """
    基于API文档生成测试用例
    
    生成过程包括:
    1. 解析文档分析结果
    2. 生成基础测试用例
    3. 生成边界条件测试
    4. 生成错误场景测试
    5. 优化和去重
    """
    logger.info(f"🧪 开始生成测试用例: {request.document_id}")
    
    # 检查文档是否存在且已分析
    if request.document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = documents_store[request.document_id]
    if doc_info["status"] != "analyzed":
        raise HTTPException(status_code=400, detail="文档尚未分析完成")
    
    if request.document_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="文档分析结果不存在")
    
    # 生成测试套件ID
    test_suite_id = str(uuid.uuid4())
    
    # 创建测试套件记录
    test_suite_info = {
        "test_suite_id": test_suite_id,
        "document_id": request.document_id,
        "suite_name": f"{doc_info['filename']}_测试套件",
        "status": "generating",
        "created_at": datetime.now(),
        "config": request.config or {},
        "test_scenarios": request.test_scenarios or [],
        "test_cases": None,
        "total_tests": 0
    }
    
    test_suites_store[test_suite_id] = test_suite_info
    
    # 添加后台生成任务
    background_tasks.add_task(
        _perform_test_generation,
        test_suite_id,
        request.document_id,
        request.config or {},
        request.test_scenarios or []
    )
    
    logger.info(f"🚀 测试生成任务已启动: {test_suite_id}")
    
    return TestGenerationResponse(
        test_suite_id=test_suite_id,
        document_id=request.document_id,
        status="generating",
        started_at=datetime.now(),
        message="测试用例生成已开始，请稍后查询结果"
    )


@router.get("/{test_suite_id}", response_model=TestSuiteInfo, summary="获取测试套件信息")
async def get_test_suite(test_suite_id: str) -> TestSuiteInfo:
    """
    获取测试套件的详细信息
    
    包括测试用例列表和生成状态
    """
    logger.info(f"📋 获取测试套件信息: {test_suite_id}")
    
    # 检查测试套件是否存在
    if test_suite_id not in test_suites_store:
        raise HTTPException(status_code=404, detail="测试套件不存在")
    
    suite_info = test_suites_store[test_suite_id]
    
    response = TestSuiteInfo(
        test_suite_id=suite_info["test_suite_id"],
        document_id=suite_info["document_id"],
        suite_name=suite_info["suite_name"],
        total_tests=suite_info["total_tests"],
        created_at=suite_info["created_at"],
        status=suite_info["status"],
        test_cases=suite_info.get("test_cases")
    )
    
    logger.info(f"✅ 测试套件信息获取成功: {test_suite_id}")
    return response


@router.post("/{test_suite_id}/execute", response_model=TestExecutionResponse, summary="执行测试套件")
async def execute_test_suite(
    test_suite_id: str,
    request: TestExecutionRequest,
    background_tasks: BackgroundTasks
) -> TestExecutionResponse:
    """
    执行测试套件
    
    执行过程包括:
    1. 验证测试目标可达性
    2. 准备测试环境
    3. 并发执行测试用例
    4. 收集执行结果
    5. 生成执行报告
    """
    logger.info(f"⚡ 开始执行测试套件: {test_suite_id}")
    
    # 检查测试套件是否存在
    if test_suite_id not in test_suites_store:
        raise HTTPException(status_code=404, detail="测试套件不存在")
    
    suite_info = test_suites_store[test_suite_id]
    if suite_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="测试套件尚未生成完成")
    
    # 生成执行ID
    execution_id = str(uuid.uuid4())
    
    # 创建执行记录
    execution_info = {
        "execution_id": execution_id,
        "test_suite_id": test_suite_id,
        "base_url": request.base_url,
        "status": "running",
        "started_at": datetime.now(),
        "config": request.config or {},
        "selected_tests": request.selected_tests,
        "result": None
    }
    
    test_executions_store[execution_id] = execution_info
    
    # 添加后台执行任务
    background_tasks.add_task(
        _perform_test_execution,
        execution_id,
        test_suite_id,
        request.base_url,
        request.config or {},
        request.selected_tests
    )
    
    logger.info(f"🚀 测试执行任务已启动: {execution_id}")
    
    return TestExecutionResponse(
        execution_id=execution_id,
        test_suite_id=test_suite_id,
        status="running",
        started_at=datetime.now(),
        message="测试执行已开始，请稍后查询结果"
    )


@router.get("/{test_suite_id}/executions/{execution_id}", summary="获取测试执行结果")
async def get_test_execution_result(test_suite_id: str, execution_id: str) -> Dict[str, Any]:
    """
    获取测试执行结果
    
    返回详细的执行结果，包括每个测试用例的执行状态和结果
    """
    logger.info(f"📊 获取测试执行结果: {execution_id}")
    
    # 检查执行记录是否存在
    if execution_id not in test_executions_store:
        raise HTTPException(status_code=404, detail="测试执行记录不存在")
    
    execution_info = test_executions_store[execution_id]
    
    # 验证测试套件ID
    if execution_info["test_suite_id"] != test_suite_id:
        raise HTTPException(status_code=400, detail="测试套件ID不匹配")
    
    logger.info(f"✅ 执行结果获取成功: {execution_id}")
    
    return {
        "execution_id": execution_id,
        "test_suite_id": test_suite_id,
        "status": execution_info["status"],
        "started_at": execution_info["started_at"],
        "completed_at": execution_info.get("completed_at"),
        "base_url": execution_info["base_url"],
        "result": execution_info.get("result"),
        "error": execution_info.get("error")
    }


@router.get("/", summary="获取测试套件列表")
async def list_test_suites(
    limit: int = 10,
    offset: int = 0,
    document_id: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取测试套件列表
    
    支持按文档ID和状态过滤
    """
    logger.info(f"📋 获取测试套件列表: limit={limit}, offset={offset}")
    
    # 获取所有测试套件
    all_suites = list(test_suites_store.values())
    
    # 过滤
    if document_id:
        all_suites = [suite for suite in all_suites if suite["document_id"] == document_id]
    
    if status:
        all_suites = [suite for suite in all_suites if suite["status"] == status]
    
    # 排序（按创建时间倒序）
    all_suites.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 分页
    total = len(all_suites)
    suites = all_suites[offset:offset + limit]
    
    # 构建响应
    test_suites = []
    for suite in suites:
        test_suites.append({
            "test_suite_id": suite["test_suite_id"],
            "document_id": suite["document_id"],
            "suite_name": suite["suite_name"],
            "total_tests": suite["total_tests"],
            "created_at": suite["created_at"],
            "status": suite["status"]
        })
    
    logger.info(f"✅ 测试套件列表获取成功: {len(test_suites)}/{total}")
    
    return {
        "test_suites": test_suites,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total
    }


async def _perform_test_generation(
    test_suite_id: str,
    document_id: str,
    config: Dict[str, Any],
    test_scenarios: List[str]
):
    """执行测试生成（后台任务）"""
    logger.info(f"🧪 开始执行测试生成: {test_suite_id}")
    
    try:
        # 获取文档分析结果
        analysis_result = analysis_results_store[document_id]
        
        # 创建生成配置
        generation_config = GenerationConfig()
        for key, value in config.items():
            if hasattr(generation_config, key):
                setattr(generation_config, key, value)
        
        # 创建测试生成器
        generator = TestCaseGenerator(generation_config)
        
        # 生成测试用例
        test_suite = generator.generate_test_cases(analysis_result, generation_config)
        
        # 转换为API响应格式
        test_cases = []
        for test_case in test_suite.test_cases:
            test_cases.append({
                "test_id": test_case.test_id,
                "name": test_case.name,
                "description": test_case.description,
                "endpoint_path": test_case.endpoint_path,
                "http_method": test_case.http_method,
                "parameters": test_case.parameters,
                "expected_status": test_case.expected_status,
                "test_type": test_case.test_type,
                "priority": test_case.priority
            })
        
        # 更新测试套件信息
        test_suites_store[test_suite_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "total_tests": len(test_cases),
            "test_cases": test_cases,
            "suite_object": test_suite  # 保存原始对象用于执行
        })
        
        logger.info(f"✅ 测试生成完成: {test_suite_id} ({len(test_cases)} 个测试用例)")
        
    except Exception as e:
        logger.error(f"❌ 测试生成失败: {test_suite_id} - {str(e)}")
        
        # 更新失败状态
        test_suites_store[test_suite_id].update({
            "status": "failed",
            "completed_at": datetime.now(),
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        })


async def _perform_test_execution(
    execution_id: str,
    test_suite_id: str,
    base_url: str,
    config: Dict[str, Any],
    selected_tests: Optional[List[str]]
):
    """执行测试执行（后台任务）"""
    logger.info(f"⚡ 开始执行测试: {execution_id}")
    
    try:
        # 获取测试套件
        suite_info = test_suites_store[test_suite_id]
        test_suite = suite_info["suite_object"]
        
        # 创建执行配置
        execution_config = ExecutionConfig()
        for key, value in config.items():
            if hasattr(execution_config, key):
                setattr(execution_config, key, value)
        
        # 创建测试执行器
        runner = TestRunner(execution_config)
        
        # 执行测试
        execution_result = runner.execute_test_suite(test_suite, base_url)
        
        # 转换为API响应格式
        result_data = {
            "suite_id": execution_result.suite_id,
            "suite_name": execution_result.suite_name,
            "total_tests": execution_result.total_tests,
            "passed_tests": execution_result.passed_tests,
            "failed_tests": execution_result.failed_tests,
            "error_tests": execution_result.error_tests,
            "skipped_tests": execution_result.skipped_tests,
            "success_rate": execution_result.success_rate,
            "total_duration": execution_result.total_duration,
            "started_at": execution_result.started_at,
            "completed_at": execution_result.completed_at,
            "test_results": [
                {
                    "test_id": result.test_id,
                    "status": result.status,
                    "request_url": result.request_url,
                    "request_method": result.request_method,
                    "response_status_code": result.response_status_code,
                    "response_time": result.response_time,
                    "duration": result.duration,
                    "error_message": result.error_message,
                    "is_successful": result.is_successful
                }
                for result in execution_result.test_results
            ]
        }
        
        # 更新执行记录
        test_executions_store[execution_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "result": result_data,
            "execution_result": execution_result  # 保存原始对象用于分析
        })
        
        logger.info(f"✅ 测试执行完成: {execution_id} (成功率: {execution_result.success_rate:.1%})")
        
    except Exception as e:
        logger.error(f"❌ 测试执行失败: {execution_id} - {str(e)}")
        
        # 更新失败状态
        test_executions_store[execution_id].update({
            "status": "failed",
            "completed_at": datetime.now(),
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        })
