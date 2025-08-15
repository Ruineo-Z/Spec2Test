"""
自定义异常类模块

定义应用程序中使用的各种自定义异常类，提供统一的错误处理机制。
包含业务异常、系统异常、验证异常等不同类型的异常。
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(Enum):
    """错误代码枚举

    定义应用程序中使用的标准错误代码，便于错误分类和处理。
    """
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = "1000"
    INVALID_PARAMETER = "1001"
    MISSING_PARAMETER = "1002"
    INVALID_OPERATION = "1003"

    # 文档相关错误 (2000-2999)
    DOCUMENT_NOT_FOUND = "2000"
    DOCUMENT_PARSE_ERROR = "2001"
    DOCUMENT_VALIDATION_ERROR = "2002"
    UNSUPPORTED_DOCUMENT_TYPE = "2003"
    DOCUMENT_TOO_LARGE = "2004"

    # 测试相关错误 (3000-3999)
    TEST_GENERATION_ERROR = "3000"
    TEST_EXECUTION_ERROR = "3001"
    TEST_CASE_NOT_FOUND = "3002"
    TEST_RESULT_PARSE_ERROR = "3003"

    # LLM相关错误 (4000-4999)
    LLM_API_ERROR = "4000"
    LLM_RESPONSE_ERROR = "4001"
    LLM_QUOTA_EXCEEDED = "4002"
    LLM_TIMEOUT_ERROR = "4003"

    # 存储相关错误 (5000-5999)
    STORAGE_ERROR = "5000"
    FILE_NOT_FOUND = "5001"
    FILE_WRITE_ERROR = "5002"
    DATABASE_ERROR = "5003"

    # 网络相关错误 (6000-6999)
    HTTP_REQUEST_ERROR = "6000"
    NETWORK_TIMEOUT = "6001"
    CONNECTION_ERROR = "6002"

    # 认证授权错误 (7000-7999)
    AUTHENTICATION_ERROR = "7000"
    AUTHORIZATION_ERROR = "7001"
    TOKEN_EXPIRED = "7002"


class BaseSpec2TestException(Exception):
    """Spec2Test基础异常类

    所有自定义异常的基类，提供统一的异常处理接口。
    包含错误代码、错误消息、详细信息等属性。
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """初始化异常

        Args:
            message: 错误消息
            error_code: 错误代码
            details: 详细信息字典
            cause: 原始异常（如果有）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """将异常转换为字典格式

        Returns:
            包含异常信息的字典
        """
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }

    def __str__(self) -> str:
        """返回异常的字符串表示"""
        return f"[{self.error_code.value}] {self.message}"


class ValidationException(BaseSpec2TestException):
    """验证异常类

    用于参数验证、数据格式验证等场景的异常。
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        """初始化验证异常

        Args:
            message: 错误消息
            field: 验证失败的字段名
            value: 验证失败的值
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.INVALID_PARAMETER),
            details=details,
            cause=kwargs.get("cause")
        )


class DocumentException(BaseSpec2TestException):
    """文档处理异常类

    用于文档解析、验证、处理等场景的异常。
    """

    def __init__(
        self,
        message: str,
        document_type: Optional[str] = None,
        document_path: Optional[str] = None,
        **kwargs
    ):
        """初始化文档异常

        Args:
            message: 错误消息
            document_type: 文档类型
            document_path: 文档路径
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if document_type:
            details["document_type"] = document_type
        if document_path:
            details["document_path"] = document_path

        super().__init__(
            message,
            error_code=kwargs.get(
                "error_code",
                ErrorCode.DOCUMENT_PARSE_ERROR),
            details=details,
            cause=kwargs.get("cause"))


class TestException(BaseSpec2TestException):
    """测试相关异常类

    用于测试生成、执行、结果处理等场景的异常。
    """

    def __init__(
        self,
        message: str,
        test_case_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        """初始化测试异常

        Args:
            message: 错误消息
            test_case_id: 测试用例ID
            endpoint: API端点
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if test_case_id:
            details["test_case_id"] = test_case_id
        if endpoint:
            details["endpoint"] = endpoint

        super().__init__(
            message,
            error_code=kwargs.get(
                "error_code",
                ErrorCode.TEST_GENERATION_ERROR),
            details=details,
            cause=kwargs.get("cause"))


class LLMException(BaseSpec2TestException):
    """LLM相关异常类

    用于LLM API调用、响应处理等场景的异常。
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        """初始化LLM异常

        Args:
            message: 错误消息
            provider: LLM提供商
            model: 模型名称
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model

        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.LLM_API_ERROR),
            details=details,
            cause=kwargs.get("cause")
        )


class StorageException(BaseSpec2TestException):
    """存储相关异常类

    用于文件存储、数据库操作等场景的异常。
    """

    def __init__(
        self,
        message: str,
        storage_type: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs
    ):
        """初始化存储异常

        Args:
            message: 错误消息
            storage_type: 存储类型
            path: 文件路径
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if storage_type:
            details["storage_type"] = storage_type
        if path:
            details["path"] = path

        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.STORAGE_ERROR),
            details=details,
            cause=kwargs.get("cause")
        )


class NetworkException(BaseSpec2TestException):
    """网络相关异常类

    用于HTTP请求、网络连接等场景的异常。
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        """初始化网络异常

        Args:
            message: 错误消息
            url: 请求URL
            status_code: HTTP状态码
            **kwargs: 其他参数
        """
        details = kwargs.get("details", {})
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code

        super().__init__(
            message,
            error_code=kwargs.get("error_code", ErrorCode.HTTP_REQUEST_ERROR),
            details=details,
            cause=kwargs.get("cause")
        )
