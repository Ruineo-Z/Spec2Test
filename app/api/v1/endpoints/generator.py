"""测试生成API端点

提供AI驱动的测试用例生成和代码生成功能。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.core.ai_generator import AITestCaseGenerator, TestCaseGenerationRequest
from app.core.models import APIEndpoint
from app.core.models import TestCaseType as CoreTestCaseType
from app.core.parser.openapi_parser import OpenAPIParser
from app.utils.exceptions import LLMError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# 枚举类型
class TestCaseType(str, Enum):
    """测试用例类型"""

    NORMAL = "normal"
    ERROR = "error"
    EDGE = "edge"
    SECURITY = "security"


class CodeFramework(str, Enum):
    """代码框架类型"""

    PYTEST = "pytest"
    UNITTEST = "unittest"
    REQUESTS = "requests"


# 请求模型
class GenerateTestCasesRequest(BaseModel):
    """生成测试用例请求模型"""

    document_id: str = Field(..., description="文档ID")
    endpoint_paths: Optional[List[str]] = Field(None, description="指定端点路径，为空则生成所有端点")
    test_types: List[TestCaseType] = Field(
        default=[TestCaseType.NORMAL, TestCaseType.ERROR], description="测试用例类型"
    )
    max_cases_per_endpoint: int = Field(default=5, ge=1, le=20, description="每个端点最大用例数")
    include_edge_cases: bool = Field(default=True, description="是否包含边界测试")
    include_security_tests: bool = Field(default=False, description="是否包含安全测试")
    custom_requirements: Optional[str] = Field(None, description="自定义测试需求")


class GenerateCodeRequest(BaseModel):
    """生成测试代码请求模型"""

    test_suite_id: str = Field(..., description="测试套件ID")
    framework: CodeFramework = Field(default=CodeFramework.PYTEST, description="测试框架")
    include_setup: bool = Field(default=True, description="是否包含测试环境设置")
    include_teardown: bool = Field(default=True, description="是否包含测试清理")
    base_url: Optional[str] = Field(None, description="API基础URL")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="认证配置")


# 响应模型
class TestCaseResponse(BaseModel):
    """测试用例响应模型"""

    id: str
    name: str
    description: str
    endpoint_path: str
    method: str
    test_type: TestCaseType
    request_data: Dict[str, Any]
    expected_response: Dict[str, Any]
    assertions: List[str]
    priority: int


class GenerateTestCasesResponse(BaseModel):
    """生成测试用例响应模型"""

    success: bool
    message: str
    test_suite_id: str
    test_cases: List[TestCaseResponse]
    generation_stats: Dict[str, Any]
    ai_analysis: Optional[str]


class GenerateCodeResponse(BaseModel):
    """生成测试代码响应模型"""

    success: bool
    message: str
    code_project_id: str
    generated_files: List[Dict[str, str]]
    project_structure: Dict[str, Any]
    execution_instructions: List[str]


@router.post("/test-cases", response_model=GenerateTestCasesResponse)
async def generate_test_cases(
    request: GenerateTestCasesRequest, background_tasks: BackgroundTasks
) -> GenerateTestCasesResponse:
    """生成AI测试用例

    Args:
        request: 测试用例生成请求
        background_tasks: 后台任务

    Returns:
        生成的测试用例

    Raises:
        HTTPException: 文档不存在或生成失败
    """
    logger.info(f"Generating test cases for document: {request.document_id}")

    try:
        # 初始化AI生成器
        ai_generator = AITestCaseGenerator()

        if not ai_generator.is_available():
            raise HTTPException(status_code=503, detail="AI测试用例生成服务不可用，请检查LLM配置")

        # 解析OpenAPI文档获取端点信息
        parser = OpenAPIParser()
        # TODO: 从数据库或缓存中获取文档内容
        # 这里暂时使用模拟端点数据
        if request.document_id != "doc_123456":
            raise HTTPException(status_code=404, detail="文档不存在")

        # 模拟端点数据（实际应从解析的文档中获取）
        mock_endpoints = [
            APIEndpoint(
                path="/api/users",
                method="GET",
                description="获取用户列表",
                parameters={
                    "query": {
                        "page": {"type": "integer", "minimum": 1},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    }
                },
                responses={
                    "200": {
                        "description": "成功返回用户列表",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/User"},
                                }
                            }
                        },
                    },
                    "400": {"description": "请求参数错误"},
                },
            )
        ]

        # 过滤指定的端点
        target_endpoints = mock_endpoints
        if request.endpoint_paths:
            target_endpoints = [
                ep for ep in mock_endpoints if ep.path in request.endpoint_paths
            ]

        if not target_endpoints:
            raise HTTPException(status_code=400, detail="未找到指定的端点")

        # 转换测试类型
        core_test_types = []
        for test_type in request.test_types:
            if test_type == TestCaseType.NORMAL:
                core_test_types.append(CoreTestCaseType.NORMAL)
            elif test_type == TestCaseType.ERROR:
                core_test_types.append(CoreTestCaseType.ERROR)
            elif test_type == TestCaseType.EDGE:
                core_test_types.append(CoreTestCaseType.EDGE)
            elif test_type == TestCaseType.SECURITY:
                core_test_types.append(CoreTestCaseType.SECURITY)

        all_generated_cases = []
        generation_stats_list = []

        # 为每个端点生成测试用例
        for endpoint in target_endpoints:
            generation_request = TestCaseGenerationRequest(
                endpoint=endpoint,
                test_types=core_test_types,
                max_cases_per_type=request.max_cases_per_endpoint,
                include_edge_cases=request.include_edge_cases,
                include_security_tests=request.include_security_tests,
                custom_requirements=request.custom_requirements,
            )

            # 调用AI生成器
            result = await ai_generator.generate_test_cases(generation_request)
            all_generated_cases.extend(result.test_cases)
            generation_stats_list.append(result.generation_stats)

        # 转换为响应格式
        response_test_cases = []
        for test_case in all_generated_cases:
            # 转换测试类型
            api_test_type = TestCaseType.NORMAL
            if test_case.type == CoreTestCaseType.ERROR:
                api_test_type = TestCaseType.ERROR
            elif test_case.type == CoreTestCaseType.EDGE:
                api_test_type = TestCaseType.EDGE
            elif test_case.type == CoreTestCaseType.SECURITY:
                api_test_type = TestCaseType.SECURITY

            response_test_cases.append(
                TestCaseResponse(
                    id=test_case.id,
                    name=test_case.name,
                    description=test_case.description,
                    endpoint_path=test_case.endpoint.path,
                    method=test_case.endpoint.method.value,
                    test_type=api_test_type,
                    request_data=test_case.test_data,
                    expected_response=test_case.expected_response,
                    assertions=getattr(test_case, "assertions", []),
                    priority=test_case.priority,
                )
            )

        # 汇总统计信息
        total_stats = {
            "total_cases": len(response_test_cases),
            "normal_cases": len(
                [c for c in response_test_cases if c.test_type == TestCaseType.NORMAL]
            ),
            "error_cases": len(
                [c for c in response_test_cases if c.test_type == TestCaseType.ERROR]
            ),
            "edge_cases": len(
                [c for c in response_test_cases if c.test_type == TestCaseType.EDGE]
            ),
            "security_cases": len(
                [c for c in response_test_cases if c.test_type == TestCaseType.SECURITY]
            ),
            "generation_time": f"{sum(s.get('generation_time', 0) for s in generation_stats_list):.2f}s",
            "ai_model": "gpt-4",
            "endpoints_processed": len(target_endpoints),
        }

        # 生成AI分析摘要
        ai_analysis = "基于AI分析生成的测试用例，覆盖了主要功能场景和错误处理。"
        if generation_stats_list:
            first_result = next(
                (r for r in generation_stats_list if "ai_analysis" in r), None
            )
            if first_result:
                ai_analysis = first_result.get("ai_analysis", ai_analysis)

        response = GenerateTestCasesResponse(
            success=True,
            message="AI测试用例生成成功",
            test_suite_id=f"ts_{request.document_id}_{int(datetime.now().timestamp())}",
            test_cases=response_test_cases,
            generation_stats=total_stats,
            ai_analysis=ai_analysis,
        )

        # 添加后台任务记录生成历史
        background_tasks.add_task(
            log_generation_history,
            request.document_id,
            "test_cases",
            len(response_test_cases),
        )

        logger.info(
            f"AI test cases generated successfully: {len(response_test_cases)} cases"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate test cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试用例生成失败: {str(e)}")


@router.post("/code", response_model=GenerateCodeResponse)
async def generate_test_code(
    request: GenerateCodeRequest, background_tasks: BackgroundTasks
) -> GenerateCodeResponse:
    """生成测试代码

    Args:
        request: 代码生成请求
        background_tasks: 后台任务

    Returns:
        生成的测试代码项目

    Raises:
        HTTPException: 测试套件不存在或生成失败
    """
    logger.info(f"Generating test code for suite: {request.test_suite_id}")

    try:
        # TODO: 实现测试代码生成逻辑
        # 这里暂时返回模拟数据

        if request.test_suite_id != "ts_123456":
            raise HTTPException(status_code=404, detail="测试套件不存在")

        # 模拟生成的文件
        mock_files = [
            {
                "path": "test_api_users.py",
                "content": "# Generated test file for /api/users\nimport pytest\nimport requests\n\ndef test_get_users_normal():\n    pass",
                "size": 1024,
            },
            {
                "path": "conftest.py",
                "content": "# Test configuration\nimport pytest\n\n@pytest.fixture\ndef api_client():\n    pass",
                "size": 512,
            },
            {
                "path": "requirements.txt",
                "content": "pytest>=7.4.0\nrequests>=2.31.0\npytest-html>=4.1.0",
                "size": 64,
            },
        ]

        mock_response = GenerateCodeResponse(
            success=True,
            message="测试代码生成成功",
            code_project_id="cp_123456",
            generated_files=mock_files,
            project_structure={
                "root": "test_project_123456",
                "files": [f["path"] for f in mock_files],
                "framework": request.framework.value,
                "total_size": sum(f["size"] for f in mock_files),
            },
            execution_instructions=[
                "1. 安装依赖: pip install -r requirements.txt",
                "2. 运行测试: pytest -v",
                "3. 生成报告: pytest --html=report.html",
            ],
        )

        # 添加后台任务记录生成历史
        background_tasks.add_task(
            log_generation_history, request.test_suite_id, "test_code", len(mock_files)
        )

        logger.info(f"Test code generated successfully: {len(mock_files)} files")
        return mock_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate test code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试代码生成失败: {str(e)}")


@router.get("/test-suites")
async def list_test_suites() -> Dict[str, Any]:
    """获取测试套件列表

    Returns:
        测试套件列表
    """
    logger.info("Listing test suites")

    # TODO: 实现测试套件列表查询逻辑

    return {
        "test_suites": [
            {
                "id": "ts_123456",
                "document_id": "doc_123456",
                "name": "API Users Test Suite",
                "created_time": "2025-01-01T10:30:00Z",
                "test_cases_count": 2,
                "status": "generated",
            }
        ],
        "total": 1,
    }


@router.get("/code-projects")
async def list_code_projects() -> Dict[str, Any]:
    """获取代码项目列表

    Returns:
        代码项目列表
    """
    logger.info("Listing code projects")

    # TODO: 实现代码项目列表查询逻辑

    return {
        "code_projects": [
            {
                "id": "cp_123456",
                "test_suite_id": "ts_123456",
                "name": "API Users Test Project",
                "framework": "pytest",
                "created_time": "2025-01-01T11:00:00Z",
                "files_count": 3,
                "status": "generated",
            }
        ],
        "total": 1,
    }


# 后台任务函数
async def log_generation_history(
    source_id: str, generation_type: str, items_count: int
):
    """记录生成历史

    Args:
        source_id: 源ID
        generation_type: 生成类型
        items_count: 生成项目数量
    """
    logger.info(
        f"Generation history logged",
        extra={"source_id": source_id, "type": generation_type, "count": items_count},
    )
    # TODO: 实现历史记录存储逻辑
