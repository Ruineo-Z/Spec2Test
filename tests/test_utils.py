"""
工具模块单元测试

测试共享工具模块中的各种函数和类。
"""

import pytest
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.shared.utils import (
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
    BaseSpec2TestException,
    ValidationException,
    DocumentException,
    ErrorCode
)


class TestHelperFunctions:
    """测试工具函数"""
    
    def test_generate_uuid(self):
        """测试UUID生成"""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()
        
        assert len(uuid1) == 36
        assert len(uuid2) == 36
        assert uuid1 != uuid2
        assert '-' in uuid1
        
    def test_generate_short_id(self):
        """测试短ID生成"""
        short_id = generate_short_id(8)
        assert len(short_id) == 8
        assert '-' not in short_id
        
        short_id_custom = generate_short_id(12)
        assert len(short_id_custom) == 12
        
    def test_calculate_md5(self):
        """测试MD5计算"""
        text = "hello world"
        # 计算实际的MD5值
        actual_md5 = calculate_md5(text)

        # 验证MD5长度和格式
        assert len(actual_md5) == 32
        assert all(c in '0123456789abcdef' for c in actual_md5)

        # 验证字符串和字节的结果一致
        assert calculate_md5(text) == calculate_md5(text.encode())
        
    def test_calculate_sha256(self):
        """测试SHA256计算"""
        text = "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        
        assert calculate_sha256(text) == expected
        assert calculate_sha256(text.encode()) == expected
        
    def test_format_datetime(self):
        """测试日期时间格式化"""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        formatted = format_datetime(dt)
        assert formatted == "2024-01-15 10:30:45"
        
        custom_format = format_datetime(dt, "%Y/%m/%d")
        assert custom_format == "2024/01/15"
        
    def test_parse_datetime(self):
        """测试日期时间解析"""
        dt_str = "2024-01-15 10:30:45"
        parsed = parse_datetime(dt_str)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 10
        assert parsed.minute == 30
        assert parsed.second == 45
        
    def test_safe_json_loads(self):
        """测试安全JSON解析"""
        valid_json = '{"key": "value"}'
        result = safe_json_loads(valid_json)
        assert result == {"key": "value"}
        
        invalid_json = '{"key": invalid}'
        result = safe_json_loads(invalid_json, {"default": True})
        assert result == {"default": True}
        
    def test_safe_json_dumps(self):
        """测试安全JSON序列化"""
        data = {"key": "值"}
        result = safe_json_dumps(data)
        assert "值" in result
        
        # 测试不可序列化对象
        class CustomObject:
            pass
        
        result = safe_json_dumps(CustomObject(), {"error": "serialization_failed"})
        assert "error" in result
        
    def test_clean_string(self):
        """测试字符串清理"""
        text = "  hello   world  "
        cleaned = clean_string(text)
        assert cleaned == "hello world"
        
        text_with_newlines = "hello\n\n  world\t"
        cleaned = clean_string(text_with_newlines)
        assert cleaned == "hello world"
        
    def test_truncate_string(self):
        """测试字符串截断"""
        # 测试英文字符串截断
        text = "This is a very long string that needs to be truncated"
        truncated = truncate_string(text, 20)
        assert len(truncated) <= 20
        assert truncated.endswith("...")

        # 测试中文字符串截断
        chinese_text = "这是一个很长的字符串需要被截断"
        truncated_chinese = truncate_string(chinese_text, 10)
        assert len(truncated_chinese) <= 10
        assert truncated_chinese.endswith("...")

        # 测试短文本不截断
        short_text = "短文本"
        result = truncate_string(short_text, 10)
        assert result == short_text
        
    def test_is_valid_email(self):
        """测试邮箱验证"""
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user.name+tag@domain.co.uk") is True
        assert is_valid_email("invalid-email") is False
        assert is_valid_email("@domain.com") is False
        assert is_valid_email("user@") is False
        
    def test_is_valid_url(self):
        """测试URL验证"""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("http://localhost:8000") is True
        assert is_valid_url("ftp://files.example.com") is True
        assert is_valid_url("invalid-url") is False
        assert is_valid_url("://example.com") is False
        
    def test_normalize_url(self):
        """测试URL标准化"""
        base = "https://api.example.com"
        path = "/v1/users"
        result = normalize_url(base, path)
        assert result == "https://api.example.com/v1/users"
        
        # 测试带斜杠的情况
        base_with_slash = "https://api.example.com/"
        path_with_slash = "/v1/users"
        result = normalize_url(base_with_slash, path_with_slash)
        assert result == "https://api.example.com/v1/users"
        
    def test_get_file_extension(self):
        """测试文件扩展名获取"""
        assert get_file_extension("document.pdf") == "pdf"
        assert get_file_extension("image.jpg") == "jpg"
        assert get_file_extension("file") == ""
        assert get_file_extension("archive.tar.gz") == "gz"
        
    def test_flatten_dict(self):
        """测试字典扁平化"""
        nested = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3
                }
            }
        }
        
        flattened = flatten_dict(nested)
        expected = {
            "a": 1,
            "b.c": 2,
            "b.d.e": 3
        }
        assert flattened == expected
        
    def test_chunk_list(self):
        """测试列表分块"""
        data = list(range(10))
        chunks = chunk_list(data, 3)
        
        assert len(chunks) == 4
        assert chunks[0] == [0, 1, 2]
        assert chunks[1] == [3, 4, 5]
        assert chunks[2] == [6, 7, 8]
        assert chunks[3] == [9]
        
    def test_file_operations(self):
        """测试文件操作"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 测试目录创建
            new_dir = temp_path / "new" / "nested" / "dir"
            ensure_directory(new_dir)
            assert new_dir.exists()
            
            # 测试文件写入和读取
            file_path = new_dir / "test.txt"
            content = "测试内容"
            write_file_content(file_path, content)
            
            assert file_path.exists()
            read_content = read_file_content(file_path)
            assert read_content == content


class TestExceptions:
    """测试异常类"""
    
    def test_base_exception(self):
        """测试基础异常类"""
        exc = BaseSpec2TestException(
            "测试错误",
            error_code=ErrorCode.INVALID_PARAMETER,
            details={"field": "test"}
        )
        
        assert str(exc) == "[1001] 测试错误"
        assert exc.error_code == ErrorCode.INVALID_PARAMETER
        assert exc.details["field"] == "test"
        
        exc_dict = exc.to_dict()
        assert exc_dict["error_code"] == "1001"
        assert exc_dict["message"] == "测试错误"
        assert exc_dict["details"]["field"] == "test"
        
    def test_validation_exception(self):
        """测试验证异常"""
        exc = ValidationException(
            "参数验证失败",
            field="email",
            value="invalid-email"
        )
        
        assert exc.details["field"] == "email"
        assert exc.details["value"] == "invalid-email"
        assert exc.error_code == ErrorCode.INVALID_PARAMETER
        
    def test_document_exception(self):
        """测试文档异常"""
        exc = DocumentException(
            "文档解析失败",
            document_type="openapi",
            document_path="/path/to/doc.yaml"
        )
        
        assert exc.details["document_type"] == "openapi"
        assert exc.details["document_path"] == "/path/to/doc.yaml"
        assert exc.error_code == ErrorCode.DOCUMENT_PARSE_ERROR
