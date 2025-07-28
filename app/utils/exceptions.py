"""自定义异常类

定义应用中使用的各种自定义异常。
"""

from typing import Optional, Dict, Any, List


class Spec2TestException(Exception):
    """Spec2Test基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "SPEC2TEST_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


class DocumentParseError(Spec2TestException):
    """文档解析异常"""
    
    def __init__(
        self,
        message: str,
        file_name: Optional[str] = None,
        line_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if file_name:
            error_details["file_name"] = file_name
        if line_number:
            error_details["line_number"] = line_number
        
        super().__init__(
            message=message,
            error_code="DOCUMENT_PARSE_ERROR",
            status_code=400,
            details=error_details
        )


class DocumentValidationError(Spec2TestException):
    """文档验证异常"""
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if validation_errors:
            error_details["validation_errors"] = validation_errors
        
        super().__init__(
            message=message,
            error_code="DOCUMENT_VALIDATION_ERROR",
            status_code=400,
            details=error_details
        )


class TestGenerationError(Spec2TestException):
    """测试生成异常"""
    
    def __init__(
        self,
        message: str,
        generation_stage: Optional[str] = None,
        endpoint_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if generation_stage:
            error_details["generation_stage"] = generation_stage
        if endpoint_path:
            error_details["endpoint_path"] = endpoint_path
        
        super().__init__(
            message=message,
            error_code="TEST_GENERATION_ERROR",
            status_code=500,
            details=error_details
        )


class LLMError(Spec2TestException):
    """LLM调用异常"""
    
    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        api_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if model_name:
            error_details["model_name"] = model_name
        if api_error:
            error_details["api_error"] = api_error
        
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            status_code=502,
            details=error_details
        )


class TestExecutionError(Spec2TestException):
    """测试执行异常"""
    
    def __init__(
        self,
        message: str,
        test_case_id: Optional[str] = None,
        execution_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if test_case_id:
            error_details["test_case_id"] = test_case_id
        if execution_stage:
            error_details["execution_stage"] = execution_stage
        
        super().__init__(
            message=message,
            error_code="TEST_EXECUTION_ERROR",
            status_code=500,
            details=error_details
        )


class CodeGenerationError(Spec2TestException):
    """代码生成异常"""
    
    def __init__(
        self,
        message: str,
        template_name: Optional[str] = None,
        generation_step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if template_name:
            error_details["template_name"] = template_name
        if generation_step:
            error_details["generation_step"] = generation_step
        
        super().__init__(
            message=message,
            error_code="CODE_GENERATION_ERROR",
            status_code=500,
            details=error_details
        )


class ReportGenerationError(Spec2TestException):
    """报告生成异常"""
    
    def __init__(
        self,
        message: str,
        report_format: Optional[str] = None,
        generation_step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if report_format:
            error_details["report_format"] = report_format
        if generation_step:
            error_details["generation_step"] = generation_step
        
        super().__init__(
            message=message,
            error_code="REPORT_GENERATION_ERROR",
            status_code=500,
            details=error_details
        )


class ConfigurationError(Spec2TestException):
    """配置错误异常"""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=error_details
        )


class ResourceNotFoundError(Spec2TestException):
    """资源不存在异常"""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id:
            error_details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=error_details
        )


class ValidationError(Spec2TestException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field_name:
            error_details["field_name"] = field_name
        if field_value is not None:
            error_details["field_value"] = str(field_value)
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=error_details
        )


class RateLimitError(Spec2TestException):
    """速率限制异常"""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if retry_after:
            error_details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details=error_details
        )


class AuthenticationError(Spec2TestException):
    """认证异常"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(Spec2TestException):
    """授权异常"""
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=error_details
        )


# 异常处理工具函数
def handle_exception(exc: Exception) -> Spec2TestException:
    """将通用异常转换为Spec2Test异常
    
    Args:
        exc: 原始异常
        
    Returns:
        Spec2Test异常实例
    """
    if isinstance(exc, Spec2TestException):
        return exc
    
    # 根据异常类型进行转换
    if isinstance(exc, FileNotFoundError):
        return ResourceNotFoundError(
            message=f"File not found: {str(exc)}",
            resource_type="file",
            details={"original_error": str(exc)}
        )
    
    if isinstance(exc, PermissionError):
        return AuthorizationError(
            message=f"Permission denied: {str(exc)}",
            details={"original_error": str(exc)}
        )
    
    if isinstance(exc, ValueError):
        return ValidationError(
            message=f"Invalid value: {str(exc)}",
            details={"original_error": str(exc)}
        )
    
    if isinstance(exc, ConnectionError):
        return Spec2TestException(
            message=f"Connection error: {str(exc)}",
            error_code="CONNECTION_ERROR",
            status_code=502,
            details={"original_error": str(exc)}
        )
    
    if isinstance(exc, TimeoutError):
        return Spec2TestException(
            message=f"Operation timeout: {str(exc)}",
            error_code="TIMEOUT_ERROR",
            status_code=504,
            details={"original_error": str(exc)}
        )
    
    # 默认转换为通用异常
    return Spec2TestException(
        message=f"Unexpected error: {str(exc)}",
        error_code="INTERNAL_ERROR",
        status_code=500,
        details={
            "original_error": str(exc),
            "exception_type": type(exc).__name__
        }
    )


# 导出所有异常类
__all__ = [
    "Spec2TestException",
    "DocumentParseError",
    "DocumentValidationError",
    "TestGenerationError",
    "LLMError",
    "TestExecutionError",
    "CodeGenerationError",
    "ReportGenerationError",
    "ConfigurationError",
    "ResourceNotFoundError",
    "ValidationError",
    "RateLimitError",
    "AuthenticationError",
    "AuthorizationError",
    "handle_exception",
]