"""
共享工具模块包

提供应用程序中使用的各种工具函数和类。
"""

from .logger import get_logger, log_function_call, log_exception, log_performance
from .exceptions import (
    BaseSpec2TestException,
    ValidationException,
    DocumentException,
    TestException,
    LLMException,
    StorageException,
    NetworkException,
    ErrorCode
)
from .helpers import (
    generate_uuid,
    generate_short_id,
    calculate_md5,
    calculate_sha256,
    get_current_timestamp,
    format_datetime,
    parse_datetime,
    safe_json_loads,
    safe_json_dumps,
    clean_string,
    truncate_string,
    is_valid_email,
    is_valid_url,
    normalize_url,
    get_file_extension,
    get_mime_type,
    ensure_directory,
    read_file_content,
    write_file_content,
    flatten_dict,
    chunk_list,
    retry_on_exception
)

__all__ = [
    # 日志工具
    "get_logger",
    "log_function_call",
    "log_exception",
    "log_performance",

    # 异常类
    "BaseSpec2TestException",
    "ValidationException",
    "DocumentException",
    "TestException",
    "LLMException",
    "StorageException",
    "NetworkException",
    "ErrorCode",

    # 工具函数
    "generate_uuid",
    "generate_short_id",
    "calculate_md5",
    "calculate_sha256",
    "get_current_timestamp",
    "format_datetime",
    "parse_datetime",
    "safe_json_loads",
    "safe_json_dumps",
    "clean_string",
    "truncate_string",
    "is_valid_email",
    "is_valid_url",
    "normalize_url",
    "get_file_extension",
    "get_mime_type",
    "ensure_directory",
    "read_file_content",
    "write_file_content",
    "flatten_dict",
    "chunk_list",
    "retry_on_exception"
]
