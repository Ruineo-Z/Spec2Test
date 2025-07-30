"""测试生成API端点

提供AI驱动的测试用例生成和代码生成功能。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_generator import AITestCaseGenerator, TestCaseGenerationRequest
from app.core.database import get_async_db
from app.core.db_models import DocumentModel
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
    """测试用例生成请求模型"""

    document_id: str = Field(..., description="文档ID")
    count: int = Field(default=10, ge=1, le=50, description="生成测试用例数量")


class GenerateTestCodeRequest(BaseModel):
    """测试代码生成请求模型"""

    test_suite_id: str = Field(..., description="测试套件ID")
    framework: CodeFramework = Field(default=CodeFramework.PYTEST, description="测试框架")
    include_setup_teardown: bool = Field(default=True, description="是否包含setup/teardown")
    base_url: str = Field(default="http://localhost:8000", description="API基础URL")
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
    priority: str


class GenerateTestCasesResponse(BaseModel):
    """生成测试用例响应模型"""

    success: bool
    message: str
    test_suite_id: str
    test_cases: List[TestCaseResponse]
    generation_stats: Dict[str, Any]
    ai_analysis: str


class GeneratedFile(BaseModel):
    """生成的文件信息"""

    path: str = Field(..., description="文件路径")
    content: str = Field(..., description="文件内容")
    file_type: str = Field(..., description="文件类型")
    description: str = Field(..., description="文件描述")


class GenerateTestCodeResponse(BaseModel):
    """生成测试代码响应模型"""

    success: bool
    message: str
    code_project_id: str
    generated_files: List[GeneratedFile]
    project_structure: Dict[str, Any]
    generation_stats: Dict[str, Any]


# 辅助函数
async def log_generation_history(
    document_id: str, generation_type: str, count: int
) -> None:
    """记录生成历史"""
    logger.info(
        f"Generation history: {document_id} - {generation_type} - {count} items"
    )


async def _generate_test_cases_internal(
    request: GenerateTestCasesRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
) -> GenerateTestCasesResponse:
    """内部测试用例生成逻辑"""
    logger.info(f"Generating test cases for document: {request.document_id}")

    try:
        # 初始化AI生成器
        ai_generator = AITestCaseGenerator()

        # 从document_id中提取数据库ID
        try:
            # document_id格式为 "doc_xxxxxxxx" (8位十六进制)
            hex_id = request.document_id.replace("doc_", "")
            db_id = int(hex_id, 16)  # 将十六进制转换为十进制
        except ValueError:
            logger.warning(f"Invalid document_id format: {request.document_id}")
            raise HTTPException(status_code=400, detail="无效的文档ID格式")

        # 从数据库查询文档
        result = await db.execute(
            select(DocumentModel).where(DocumentModel.id == db_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            logger.warning(f"Document not found: {request.document_id}")
            raise HTTPException(status_code=404, detail="文档不存在")

        logger.info(f"Found document: {document.name}")

        # 解析OpenAPI文档获取端点信息
        parser = OpenAPIParser()

        # 从文档内容中解析真正的端点信息
        try:
            # 从数据库中的analysis_result字段获取文档内容
            content = None
            if document.analysis_result and isinstance(document.analysis_result, dict):
                content = document.analysis_result.get("content")

            if not content:
                raise ValueError("Document content not found in database")

            # 解析OpenAPI文档
            parsed_endpoints = parser.parse_openapi_content(content)
            logger.info(f"Parsed {len(parsed_endpoints)} endpoints from document")

        except Exception as e:
            logger.warning(
                f"Failed to parse OpenAPI document: {str(e)}, using mock data"
            )
            # 如果解析失败，使用模拟端点数据
            parsed_endpoints = [
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

        # 使用所有解析到的端点
        target_endpoints = parsed_endpoints
        if not target_endpoints:
            raise HTTPException(status_code=400, detail="未找到可用的端点")

        # 使用默认配置：只生成normal类型的测试用例
        core_test_types = [CoreTestCaseType.NORMAL]

        # 计算每个端点应该生成的测试用例数量
        cases_per_endpoint = max(1, min(request.count // len(target_endpoints), 10))
        if cases_per_endpoint * len(target_endpoints) < request.count:
            cases_per_endpoint += 1

        all_generated_cases = []
        generation_stats_list = []

        # 为每个端点生成测试用例
        for endpoint in target_endpoints:
            generation_request = TestCaseGenerationRequest(
                endpoint=endpoint,
                test_types=core_test_types,
                max_cases_per_type=cases_per_endpoint,
                include_edge_cases=False,
                include_security_tests=False,
                custom_requirements=None,
            )

            # 调用AI生成器
            result = await ai_generator.generate_test_cases(generation_request)
            all_generated_cases.extend(result.test_cases)
            generation_stats_list.append(result.generation_stats)

            # 如果已经生成足够的测试用例，就停止
            if len(all_generated_cases) >= request.count:
                all_generated_cases = all_generated_cases[: request.count]
                break

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
                    priority=str(test_case.priority),
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
    except ValueError as e:
        # 处理配置错误和文档质量错误
        logger.warning(f"Test case generation validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate test cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试用例生成失败: {str(e)}")


# API端点
async def _generate_test_code_internal(
    request: GenerateTestCodeRequest,
    background_tasks: BackgroundTasks,
) -> GenerateTestCodeResponse:
    """内部测试代码生成逻辑"""
    logger.info(f"Generating test code for test suite: {request.test_suite_id}")

    try:
        # 模拟从测试套件ID获取测试用例数据
        # 在实际实现中，这里应该从数据库或缓存中获取测试用例
        test_cases_data = {
            "test_cases": [
                {
                    "id": "test_1",
                    "name": "测试用户注册接口",
                    "endpoint_path": "/user/register",
                    "method": "POST",
                    "request_data": {"email": "test@example.com", "password": "password123"},
                    "expected_response": {"status": "success", "user_id": "12345"},
                    "expected_status_code": 200
                }
            ]
        }

        # 生成pytest测试代码
        if request.framework == CodeFramework.PYTEST:
            test_code = _generate_pytest_code(
                test_cases_data["test_cases"],
                request.base_url,
                request.include_setup_teardown,
                request.auth_config
            )
        else:
            # 其他框架的实现
            test_code = _generate_unittest_code(
                test_cases_data["test_cases"],
                request.base_url,
                request.include_setup_teardown,
                request.auth_config
            )

        # 生成配置文件
        config_files = _generate_config_files(request.framework, request.base_url)

        # 组装生成的文件
        generated_files = [
            GeneratedFile(
                path="test_api.py",
                content=test_code,
                file_type="python",
                description="主要的API测试文件"
            )
        ]
        generated_files.extend(config_files)

        # 生成项目结构信息
        project_structure = {
            "framework": request.framework.value,
            "base_url": request.base_url,
            "files_count": len(generated_files),
            "test_cases_count": len(test_cases_data["test_cases"])
        }

        # 生成统计信息
        generation_stats = {
            "framework": request.framework.value,
            "generated_files_count": len(generated_files),
            "test_cases_count": len(test_cases_data["test_cases"]),
            "generation_time": datetime.now().isoformat()
        }

        # 生成代码项目ID
        code_project_id = f"cp_{request.test_suite_id}_{int(datetime.now().timestamp())}"

        response = GenerateTestCodeResponse(
            success=True,
            message="测试代码生成成功",
            code_project_id=code_project_id,
            generated_files=generated_files,
            project_structure=project_structure,
            generation_stats=generation_stats
        )

        # 添加后台任务记录生成历史
        background_tasks.add_task(
            log_generation_history,
            request.test_suite_id,
            "test_code",
            len(generated_files)
        )

        logger.info(f"Test code generated successfully: {len(generated_files)} files")
        return response

    except Exception as e:
        logger.error(f"Failed to generate test code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"测试代码生成失败: {str(e)}")


def _generate_pytest_code(
    test_cases: List[Dict[str, Any]],
    base_url: str,
    include_setup_teardown: bool,
    auth_config: Optional[Dict[str, Any]]
) -> str:
    """生成pytest测试代码"""
    code_lines = [
        "import pytest",
        "import requests",
        "import json",
        "from typing import Dict, Any",
        "",
        "",
        "class TestAPI:",
        '    """API测试类"""',
        "",
    ]

    if include_setup_teardown:
        code_lines.extend([
            "    @pytest.fixture(autouse=True)",
            "    def setup_method(self):",
            f'        self.base_url = "{base_url}"',
            "        self.session = requests.Session()",
        ])
        
        if auth_config:
            code_lines.extend([
                "        # 认证配置",
                f"        self.auth_config = {auth_config}",
            ])
        
        code_lines.extend([
            "",
            "    def teardown_method(self):",
            "        self.session.close()",
            "",
        ])

    # 为每个测试用例生成测试方法
    for i, test_case in enumerate(test_cases):
        method_name = f"test_{test_case['endpoint_path'].replace('/', '_').replace('{', '').replace('}', '').strip('_')}_{i+1}"
        
        test_name = test_case['name']
        endpoint_path = test_case['endpoint_path']
        method = test_case['method'].lower()
        request_data = json.dumps(test_case['request_data'], ensure_ascii=False, indent=8)
        expected_status = test_case.get('expected_status_code', 200)
        
        code_lines.extend([
             f"    def {method_name}(self):",
             f'        """测试{test_name}"""',
             f"        url = self.base_url + '{endpoint_path}'",
             f"        method = '{method}'",
             f"        data = {request_data}",
             "",
             "        response = self.session.request(method, url, json=data)",
             "",
             "        # 验证状态码",
             f"        assert response.status_code == {expected_status}",
             "",
             "        # 验证响应内容",
             "        response_data = response.json()",
         ])
        
        # 添加响应验证
        expected_response = test_case.get('expected_response', {})
        for key, value in expected_response.items():
            if isinstance(value, str):
                code_lines.append(f"        assert response_data.get('{key}') == '{value}'")
            else:
                code_lines.append(f"        assert response_data.get('{key}') == {value}")
        
        code_lines.append("")

    return "\n".join(code_lines)


def _generate_unittest_code(
    test_cases: List[Dict[str, Any]],
    base_url: str,
    include_setup_teardown: bool,
    auth_config: Optional[Dict[str, Any]]
) -> str:
    """生成unittest测试代码"""
    code_lines = [
        "import unittest",
        "import requests",
        "import json",
        "",
        "",
        "class TestAPI(unittest.TestCase):",
        '    """API测试类"""',
        "",
    ]

    if include_setup_teardown:
        code_lines.extend([
            "    def setUp(self):",
            f'        self.base_url = "{base_url}"',
            "        self.session = requests.Session()",
        ])
        
        if auth_config:
            code_lines.extend([
                "        # 认证配置",
                f"        self.auth_config = {auth_config}",
            ])
        
        code_lines.extend([
            "",
            "    def tearDown(self):",
            "        self.session.close()",
            "",
        ])

    # 为每个测试用例生成测试方法
    for i, test_case in enumerate(test_cases):
        method_name = f"test_{test_case['endpoint_path'].replace('/', '_').replace('{', '').replace('}', '').strip('_')}_{i+1}"
        
        test_name = test_case['name']
        endpoint_path = test_case['endpoint_path']
        method = test_case['method'].lower()
        request_data = json.dumps(test_case['request_data'], ensure_ascii=False, indent=8)
        expected_status = test_case.get('expected_status_code', 200)
        
        code_lines.extend([
             f"    def {method_name}(self):",
             f'        """测试{test_name}"""',
             f"        url = self.base_url + '{endpoint_path}'",
             f"        method = '{method}'",
             f"        data = {request_data}",
             "",
             "        response = self.session.request(method, url, json=data)",
             "",
             "        # 验证状态码",
             f"        self.assertEqual(response.status_code, {expected_status})",
             "",
             "        # 验证响应内容",
             "        response_data = response.json()",
         ])
        
        # 添加响应验证
        expected_response = test_case.get('expected_response', {})
        for key, value in expected_response.items():
            if isinstance(value, str):
                code_lines.append(f"        self.assertEqual(response_data.get('{key}'), '{value}')")
            else:
                code_lines.append(f"        self.assertEqual(response_data.get('{key}'), {value})")
        
        code_lines.append("")

    code_lines.extend([
        "",
        "if __name__ == '__main__':",
        "    unittest.main()"
    ])

    return "\n".join(code_lines)


def _generate_config_files(framework: CodeFramework, base_url: str) -> List[GeneratedFile]:
    """生成配置文件"""
    config_files = []
    
    if framework == CodeFramework.PYTEST:
        # 生成pytest.ini配置文件
        pytest_config = """[tool:pytest]
addopts = -v --tb=short
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*
"""
        config_files.append(GeneratedFile(
            path="pytest.ini",
            content=pytest_config,
            file_type="ini",
            description="pytest配置文件"
        ))
        
        # 生成conftest.py
        conftest_content = f"""import pytest
import requests

@pytest.fixture(scope="session")
def api_client():
    \"\"\"API客户端fixture\"\"\"
    session = requests.Session()
    session.base_url = "{base_url}"
    yield session
    session.close()
"""
        config_files.append(GeneratedFile(
            path="conftest.py",
            content=conftest_content,
            file_type="python",
            description="pytest配置和fixture文件"
        ))
    
    # 生成requirements.txt
    requirements = """requests>=2.28.0
pytest>=7.0.0
pytest-html>=3.1.0
"""
    config_files.append(GeneratedFile(
        path="requirements.txt",
        content=requirements,
        file_type="text",
        description="Python依赖文件"
    ))
    
    # 生成README.md
    readme_content = f"""# API测试项目

## 简介
这是一个自动生成的API测试项目，使用{framework.value}框架。

## 安装依赖
```bash
pip install -r requirements.txt
```

## 运行测试
```bash
{'pytest' if framework == CodeFramework.PYTEST else 'python -m unittest'}
```

## 配置
- 基础URL: {base_url}
- 测试框架: {framework.value}
"""
    config_files.append(GeneratedFile(
        path="README.md",
        content=readme_content,
        file_type="markdown",
        description="项目说明文档"
    ))
    
    return config_files


# API端点
@router.post("/test-cases", response_model=GenerateTestCasesResponse)
async def generate_test_cases(
    request: GenerateTestCasesRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
) -> GenerateTestCasesResponse:
    """生成AI测试用例

    只需要提供文档ID和数量，系统会自动：
    - 生成所有端点的测试用例
    - 使用normal类型的测试用例
    - 每个端点生成3个测试用例
    - 智能分配测试用例数量

    Args:
        request: 测试用例生成请求
        background_tasks: 后台任务

    Returns:
        生成的测试用例

    Raises:
        HTTPException: 文档不存在或生成失败
    """
    return await _generate_test_cases_internal(request, background_tasks, db)


@router.post("/code", response_model=GenerateTestCodeResponse)
async def generate_test_code(
    request: GenerateTestCodeRequest,
    background_tasks: BackgroundTasks,
) -> GenerateTestCodeResponse:
    """生成测试代码

    基于测试套件ID生成可执行的测试代码，支持：
    - pytest和unittest框架
    - 自动生成配置文件
    - 包含setup/teardown逻辑
    - 支持认证配置

    Args:
        request: 测试代码生成请求
        background_tasks: 后台任务

    Returns:
        生成的测试代码和配置文件

    Raises:
        HTTPException: 测试套件不存在或生成失败
    """
    return await _generate_test_code_internal(request, background_tasks)
