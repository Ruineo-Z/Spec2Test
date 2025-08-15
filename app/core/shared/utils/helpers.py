"""
通用工具函数模块

提供应用程序中常用的工具函数，包括字符串处理、文件操作、
时间处理、数据验证等功能。
"""

import re
import json
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union, Callable
from urllib.parse import urlparse, urljoin
import mimetypes


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


def calculate_md5(content: Union[str, bytes]) -> str:
    """计算MD5哈希值

    Args:
        content: 要计算哈希的内容

    Returns:
        MD5哈希值字符串
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.md5(content).hexdigest()


def calculate_sha256(content: Union[str, bytes]) -> str:
    """计算SHA256哈希值

    Args:
        content: 要计算哈希的内容

    Returns:
        SHA256哈希值字符串
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()


def get_current_timestamp() -> datetime:
    """获取当前UTC时间戳

    Returns:
        当前UTC时间
    """
    return datetime.now(timezone.utc)


def format_datetime(
        dt: datetime,
        format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间

    Args:
        dt: 日期时间对象
        format_str: 格式字符串

    Returns:
        格式化后的日期时间字符串
    """
    return dt.strftime(format_str)


def parse_datetime(
        dt_str: str,
        format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析日期时间字符串

    Args:
        dt_str: 日期时间字符串
        format_str: 格式字符串

    Returns:
        日期时间对象
    """
    return datetime.strptime(dt_str, format_str)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析

    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值

    Returns:
        解析后的对象或默认值
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: Any = None, **kwargs) -> str:
    """安全的JSON序列化

    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
        **kwargs: json.dumps的其他参数

    Returns:
        JSON字符串
    """
    try:
        return json.dumps(obj, ensure_ascii=False, **kwargs)
    except (TypeError, ValueError):
        return json.dumps(default) if default is not None else "{}"


def clean_string(text: str, remove_extra_spaces: bool = True) -> str:
    """清理字符串

    Args:
        text: 要清理的字符串
        remove_extra_spaces: 是否移除多余空格

    Returns:
        清理后的字符串
    """
    if not text:
        return ""

    # 移除首尾空白
    text = text.strip()

    # 移除多余空格
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text)

    return text


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """截断字符串

    Args:
        text: 要截断的字符串
        max_length: 最大长度
        suffix: 截断后的后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_email(email: str) -> bool:
    """验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        是否为有效邮箱格式
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """验证URL格式

    Args:
        url: URL地址

    Returns:
        是否为有效URL格式
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(base_url: str, path: str) -> str:
    """标准化URL

    Args:
        base_url: 基础URL
        path: 路径

    Returns:
        完整的URL
    """
    return urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))


def get_file_extension(filename: str) -> str:
    """获取文件扩展名

    Args:
        filename: 文件名

    Returns:
        文件扩展名（不包含点号）
    """
    return Path(filename).suffix.lstrip('.')


def get_mime_type(filename: str) -> str:
    """获取文件MIME类型

    Args:
        filename: 文件名

    Returns:
        MIME类型
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file_content(
        file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """读取文件内容

    Args:
        file_path: 文件路径
        encoding: 编码格式

    Returns:
        文件内容
    """
    return Path(file_path).read_text(encoding=encoding)


def write_file_content(
    file_path: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> None:
    """写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码格式
        create_dirs: 是否创建目录
    """
    file_path = Path(file_path)
    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)


def flatten_dict(d: Dict[str, Any], parent_key: str = '',
                 sep: str = '.') -> Dict[str, Any]:
    """扁平化字典

    Args:
        d: 要扁平化的字典
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


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分块

    Args:
        lst: 要分块的列表
        chunk_size: 块大小

    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_exception(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """异常重试装饰器

    Args:
        func: 要重试的函数
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        exceptions: 要捕获的异常类型

    Returns:
        函数执行结果
    """
    import time

    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            if attempt == max_retries:
                raise e
            time.sleep(delay * (2 ** attempt))  # 指数退避

    return None
