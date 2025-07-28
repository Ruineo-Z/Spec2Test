"""工具函数模块

提供各种通用的工具函数，包括文件操作、数据格式化、敏感数据处理等。
"""

import os
import json
import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set
from datetime import datetime, timezone
import re
import uuid
from urllib.parse import urlparse

from loguru import logger


# 文件操作相关
def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小
    """
    return Path(file_path).stat().st_size


def get_file_extension(file_path: Union[str, Path]) -> str:
    """获取文件扩展名
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件扩展名（小写，不包含点）
    """
    return Path(file_path).suffix.lower().lstrip('.')


def get_mime_type(file_path: Union[str, Path]) -> Optional[str]:
    """获取文件MIME类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        MIME类型字符串
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type


def is_valid_file_type(file_path: Union[str, Path], allowed_extensions: Set[str]) -> bool:
    """检查文件类型是否允许
    
    Args:
        file_path: 文件路径
        allowed_extensions: 允许的扩展名集合
        
    Returns:
        是否为允许的文件类型
    """
    extension = get_file_extension(file_path)
    return extension in {ext.lower().lstrip('.') for ext in allowed_extensions}


def generate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """生成文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法（md5, sha1, sha256等）
        
    Returns:
        文件哈希值
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def safe_filename(filename: str) -> str:
    """生成安全的文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    # 移除或替换不安全的字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    safe_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_name)
    # 限制长度
    if len(safe_name) > 255:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:255-len(ext)] + ext
    
    return safe_name


# 数据格式化相关
def format_bytes(bytes_value: int) -> str:
    """格式化字节数为人类可读格式
    
    Args:
        bytes_value: 字节数
        
    Returns:
        格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """格式化时间间隔为人类可读格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的字符串
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}m {remaining_seconds:.0f}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {remaining_minutes:.0f}m"


def format_timestamp(timestamp: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间戳
    
    Args:
        timestamp: 时间戳，默认为当前时间
        format_str: 格式字符串
        
    Returns:
        格式化后的时间字符串
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return timestamp.strftime(format_str)


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# 敏感数据处理
def mask_sensitive_data(data: Any, sensitive_keys: Optional[Set[str]] = None) -> Any:
    """掩码敏感数据
    
    Args:
        data: 要处理的数据
        sensitive_keys: 敏感字段名集合
        
    Returns:
        掩码后的数据
    """
    if sensitive_keys is None:
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'api_key', 'access_token',
            'refresh_token', 'authorization', 'auth', 'credential', 'private_key'
        }
    
    def _mask_value(value: str) -> str:
        """掩码单个值"""
        if len(value) <= 4:
            return '*' * len(value)
        return value[:2] + '*' * (len(value) - 4) + value[-2:]
    
    def _process_item(item: Any) -> Any:
        """递归处理数据项"""
        if isinstance(item, dict):
            return {
                key: _mask_value(str(value)) if key.lower() in sensitive_keys and isinstance(value, (str, int, float))
                else _process_item(value)
                for key, value in item.items()
            }
        elif isinstance(item, list):
            return [_process_item(sub_item) for sub_item in item]
        elif isinstance(item, tuple):
            return tuple(_process_item(sub_item) for sub_item in item)
        else:
            return item
    
    return _process_item(data)


def mask_url_credentials(url: str) -> str:
    """掩码URL中的凭据信息
    
    Args:
        url: 原始URL
        
    Returns:
        掩码后的URL
    """
    try:
        parsed = urlparse(url)
        if parsed.username or parsed.password:
            # 构建掩码后的netloc
            netloc = parsed.hostname or ''
            if parsed.port:
                netloc += f':{parsed.port}'
            if parsed.username:
                masked_user = parsed.username[:2] + '*' * max(0, len(parsed.username) - 2)
                netloc = f'{masked_user}@{netloc}'
            
            # 重构URL
            return f"{parsed.scheme}://{netloc}{parsed.path}"
        return url
    except Exception:
        return url


# JSON处理
def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"JSON解析失败: {e}")
        return default


def safe_json_dumps(data: Any, default: str = "{}", **kwargs) -> str:
    """安全的JSON序列化
    
    Args:
        data: 要序列化的数据
        default: 序列化失败时的默认值
        **kwargs: json.dumps的其他参数
        
    Returns:
        JSON字符串或默认值
    """
    try:
        return json.dumps(data, ensure_ascii=False, **kwargs)
    except (TypeError, ValueError) as e:
        logger.warning(f"JSON序列化失败: {e}")
        return default


# ID生成
def generate_uuid() -> str:
    """生成UUID字符串
    
    Returns:
        UUID字符串
    """
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """生成短ID
    
    Args:
        length: ID长度
        
    Returns:
        短ID字符串
    """
    return str(uuid.uuid4()).replace('-', '')[:length]


def generate_timestamp_id() -> str:
    """生成基于时间戳的ID
    
    Returns:
        时间戳ID
    """
    timestamp = int(datetime.now().timestamp() * 1000000)
    return f"{timestamp}_{generate_short_id(4)}"


# 数据验证
def is_valid_email(email: str) -> bool:
    """验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否为有效邮箱
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """验证URL格式
    
    Args:
        url: URL地址
        
    Returns:
        是否为有效URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_json(json_str: str) -> bool:
    """验证JSON格式
    
    Args:
        json_str: JSON字符串
        
    Returns:
        是否为有效JSON
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


# 字符串处理
def snake_to_camel(snake_str: str) -> str:
    """蛇形命名转驼峰命名
    
    Args:
        snake_str: 蛇形命名字符串
        
    Returns:
        驼峰命名字符串
    """
    components = snake_str.split('_')
    return components[0] + ''.join(word.capitalize() for word in components[1:])


def camel_to_snake(camel_str: str) -> str:
    """驼峰命名转蛇形命名
    
    Args:
        camel_str: 驼峰命名字符串
        
    Returns:
        蛇形命名字符串
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def clean_text(text: str) -> str:
    """清理文本，移除多余空白字符
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    # 移除首尾空白
    return text.strip()


# 列表和字典处理
def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """扁平化嵌套字典
    
    Args:
        d: 嵌套字典
        parent_key: 父键名
        sep: 分隔符
        
    Returns:
        扁平化后的字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 块大小
        
    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


# 环境变量处理
def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔类型环境变量
    
    Args:
        key: 环境变量名
        default: 默认值
        
    Returns:
        布尔值
    """
    value = os.getenv(key, '').lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int = 0) -> int:
    """获取整数类型环境变量
    
    Args:
        key: 环境变量名
        default: 默认值
        
    Returns:
        整数值
    """
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_list(key: str, separator: str = ',', default: Optional[List[str]] = None) -> List[str]:
    """获取列表类型环境变量
    
    Args:
        key: 环境变量名
        separator: 分隔符
        default: 默认值
        
    Returns:
        字符串列表
    """
    value = os.getenv(key, '')
    if not value:
        return default or []
    return [item.strip() for item in value.split(separator) if item.strip()]


# 导出所有函数
__all__ = [
    # 文件操作
    'ensure_dir', 'get_file_size', 'get_file_extension', 'get_mime_type',
    'is_valid_file_type', 'generate_file_hash', 'safe_filename',
    
    # 数据格式化
    'format_bytes', 'format_duration', 'format_timestamp', 'truncate_string',
    
    # 敏感数据处理
    'mask_sensitive_data', 'mask_url_credentials',
    
    # JSON处理
    'safe_json_loads', 'safe_json_dumps',
    
    # ID生成
    'generate_uuid', 'generate_short_id', 'generate_timestamp_id',
    
    # 数据验证
    'is_valid_email', 'is_valid_url', 'is_valid_json',
    
    # 字符串处理
    'snake_to_camel', 'camel_to_snake', 'clean_text',
    
    # 列表和字典处理
    'flatten_dict', 'deep_merge_dicts', 'chunk_list',
    
    # 环境变量处理
    'get_env_bool', 'get_env_int', 'get_env_list',
]