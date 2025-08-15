"""
测试用例相关的Pydantic Schema

定义测试用例模型的输入输出Schema，用于API请求响应的数据验证。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.test_case import TestCaseType, TestCasePriority, HTTPMethod


class TestCaseBase(BaseModel):
    """测试用例基础Schema"""
    name: str = Field(..., description="测试用例名称", max_length=255)
    description: Optional[str] = Field(None, description="测试用例描述")
    test_type: TestCaseType = Field(TestCaseType.NORMAL, description="测试用例类型")
    priority: TestCasePriority = Field(TestCasePriority.MEDIUM, description="测试优先级")
    endpoint_path: str = Field(..., description="API端点路径", max_length=500)
    http_method: HTTPMethod = Field(..., description="HTTP请求方法")


class TestCaseCreate(TestCaseBase):
    """创建测试用例Schema"""
    document_id: int = Field(..., description="关联文档ID")
    
    # 请求参数
    request_headers: Optional[Dict[str, Any]] = Field(None, description="请求头参数")
    request_params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    request_body: Optional[Dict[str, Any]] = Field(None, description="请求体数据")
    path_variables: Optional[Dict[str, Any]] = Field(None, description="路径变量")
    
    # 认证信息
    auth_type: Optional[str] = Field(None, description="认证类型", max_length=50)
    auth_data: Optional[Dict[str, Any]] = Field(None, description="认证数据")
    
    # 期望结果
    expected_status_code: Optional[int] = Field(None, description="期望HTTP状态码")
    expected_response_headers: Optional[Dict[str, Any]] = Field(None, description="期望响应头")
    expected_response_body: Optional[Dict[str, Any]] = Field(None, description="期望响应体")
    expected_response_schema: Optional[Dict[str, Any]] = Field(None, description="期望响应Schema")
    
    # 验证规则
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="自定义验证规则")
    
    # 性能要求
    max_response_time: Optional[float] = Field(None, description="最大响应时间（秒）", gt=0)
    
    # 测试标签和分组
    tags: Optional[List[str]] = Field(None, description="测试标签")
    test_group: Optional[str] = Field(None, description="测试分组", max_length=100)
    
    # 依赖关系
    depends_on: Optional[List[int]] = Field(None, description="依赖的测试用例ID列表")
    
    # 执行配置
    retry_count: int = Field(0, description="重试次数", ge=0, le=10)
    timeout: Optional[float] = Field(30.0, description="超时时间（秒）", gt=0, le=300)
    is_enabled: bool = Field(True, description="是否启用此测试用例")


class TestCaseUpdate(BaseModel):
    """更新测试用例Schema"""
    name: Optional[str] = Field(None, description="测试用例名称", max_length=255)
    description: Optional[str] = Field(None, description="测试用例描述")
    test_type: Optional[TestCaseType] = Field(None, description="测试用例类型")
    priority: Optional[TestCasePriority] = Field(None, description="测试优先级")
    
    # 请求参数
    request_headers: Optional[Dict[str, Any]] = Field(None, description="请求头参数")
    request_params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    request_body: Optional[Dict[str, Any]] = Field(None, description="请求体数据")
    path_variables: Optional[Dict[str, Any]] = Field(None, description="路径变量")
    
    # 期望结果
    expected_status_code: Optional[int] = Field(None, description="期望HTTP状态码")
    expected_response_headers: Optional[Dict[str, Any]] = Field(None, description="期望响应头")
    expected_response_body: Optional[Dict[str, Any]] = Field(None, description="期望响应体")
    
    # 执行配置
    retry_count: Optional[int] = Field(None, description="重试次数", ge=0, le=10)
    timeout: Optional[float] = Field(None, description="超时时间（秒）", gt=0, le=300)
    is_enabled: Optional[bool] = Field(None, description="是否启用此测试用例")


class TestCaseResponse(TestCaseBase):
    """测试用例响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="测试用例ID")
    document_id: int = Field(..., description="关联文档ID")
    
    # 请求参数
    request_headers: Optional[Dict[str, Any]] = Field(None, description="请求头参数")
    request_params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    request_body: Optional[Dict[str, Any]] = Field(None, description="请求体数据")
    path_variables: Optional[Dict[str, Any]] = Field(None, description="路径变量")
    
    # 认证信息
    auth_type: Optional[str] = Field(None, description="认证类型")
    
    # 期望结果
    expected_status_code: Optional[int] = Field(None, description="期望HTTP状态码")
    expected_response_headers: Optional[Dict[str, Any]] = Field(None, description="期望响应头")
    expected_response_body: Optional[Dict[str, Any]] = Field(None, description="期望响应体")
    
    # 性能要求
    max_response_time: Optional[float] = Field(None, description="最大响应时间（秒）")
    
    # 测试标签和分组
    tags: Optional[List[str]] = Field(None, description="测试标签")
    test_group: Optional[str] = Field(None, description="测试分组")
    
    # 依赖关系
    depends_on: Optional[List[int]] = Field(None, description="依赖的测试用例ID列表")
    
    # 执行配置
    retry_count: int = Field(..., description="重试次数")
    timeout: Optional[float] = Field(None, description="超时时间（秒）")
    is_enabled: bool = Field(..., description="是否启用此测试用例")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class TestCaseDetail(TestCaseResponse):
    """测试用例详情Schema"""
    auth_data: Optional[Dict[str, Any]] = Field(None, description="认证数据")
    expected_response_schema: Optional[Dict[str, Any]] = Field(None, description="期望响应Schema")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="自定义验证规则")


class TestCaseList(BaseModel):
    """测试用例列表Schema"""
    items: List[TestCaseResponse] = Field(..., description="测试用例列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class TestCaseBatch(BaseModel):
    """批量测试用例Schema"""
    test_cases: List[TestCaseCreate] = Field(..., description="测试用例列表", min_items=1, max_items=100)
    document_id: int = Field(..., description="关联文档ID")


class TestCaseExecuteRequest(BaseModel):
    """测试用例执行请求Schema"""
    test_case_ids: List[int] = Field(..., description="要执行的测试用例ID列表", min_items=1)
    execution_config: Optional[Dict[str, Any]] = Field(None, description="执行配置")
    environment: Optional[str] = Field("default", description="执行环境", max_length=50)
    parallel: bool = Field(False, description="是否并行执行")
    max_workers: Optional[int] = Field(5, description="最大并行数", ge=1, le=20)


class TestCaseStats(BaseModel):
    """测试用例统计Schema"""
    total_test_cases: int = Field(..., description="测试用例总数")
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    by_priority: Dict[str, int] = Field(..., description="按优先级统计")
    by_method: Dict[str, int] = Field(..., description="按HTTP方法统计")
    enabled_count: int = Field(..., description="启用的测试用例数")
    disabled_count: int = Field(..., description="禁用的测试用例数")


class TestCaseValidation(BaseModel):
    """测试用例验证Schema"""
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(..., description="验证错误列表")
    warnings: List[str] = Field(..., description="验证警告列表")
    suggestions: List[str] = Field(..., description="改进建议列表")
