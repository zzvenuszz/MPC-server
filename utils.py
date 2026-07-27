"""
MCP Programming Support Server - Tiện ích Chung
Cung cấp các hàm tiện ích: logging, validation, Vietnamese language support
"""

import os
import sys
import re
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

import structlog
from structlog.stdlib import LoggerFactory
from structlog.processors import JSONRenderer, TimeStamper, StackInfoRenderer
from logging.handlers import RotatingFileHandler

from config import get_settings

# =============================================================================
# LOGGING SYSTEM - Hệ thống Logging
# =============================================================================

# Định nghĩa các mức log
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def setup_logging() -> structlog.BoundLogger:
    """
    Thiết lập hệ thống logging với structlog

    Returns:
        Logger instance đã được cấu hình
    """
    settings = get_settings()

    # Tạo thư mục log nếu chưa tồn tại
    settings.ensure_log_dir_exists()

    # Kiểm tra nếu logging đã được cấu hình (tránh cấu hình lại do circular import)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # Đã có handlers, trả về logger hiện tại
        return structlog.get_logger("mcp-server")

    # Cấu hình structlog
    structlog.configure(
        processors=[
            # Thêm timestamp
            TimeStamper(fmt="iso", utc=True),
            # Thêm stack info cho warnings/errors
            StackInfoRenderer(),
            # Thêm log level
            structlog.stdlib.add_log_level,
            # Thêm logger name
            structlog.stdlib.add_logger_name,
            # Format exception
            structlog.processors.format_exc_info,
            # Render ra console (human-readable)
            structlog.dev.ConsoleRenderer(colors=True)
            if settings.is_development
            else JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True
    )

    # Cấu hình standard library logging
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVELS.get(settings.log_level.upper(), logging.INFO))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVELS.get(settings.log_level.upper(), logging.INFO))
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler với rotation
    log_file = settings.get_log_file_path("mcp-server")
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(LOG_LEVELS.get(settings.log_level.upper(), logging.INFO))
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Tạo logger cho MCP server
    logger = structlog.get_logger("mcp-server")

    logger.info(
        "Hệ thống logging đã được khởi tạo",
        log_level=settings.log_level,
        log_file=str(log_file),
        is_development=settings.is_development
    )

    return logger


# Logger toàn cục
logger: Optional[structlog.BoundLogger] = None


def get_logger() -> structlog.BoundLogger:
    """
    Lấy logger instance (Singleton)

    Returns:
        Logger instance
    """
    global logger
    if logger is None:
        logger = setup_logging()
    return logger


# =============================================================================
# VALIDATION UTILITIES - Tiện ích Validation
# =============================================================================

def validate_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate đường dẫn file/thư mục

    Args:
        path: Đường dẫn cần validate
        must_exist: Bắt buộc phải tồn tại

    Returns:
        Path object đã được resolve

    Raises:
        ValueError: Nếu đường dẫn không hợp lệ
    """
    settings = get_settings()
    path_obj = Path(path).resolve()

    # Kiểm tra path traversal
    try:
        path_obj.relative_to(settings.workspace.resolve())
    except ValueError:
        raise ValueError(
            f"Đường dẫn không nằm trong workspace: {path} -> {path_obj}"
        )

    if must_exist and not path_obj.exists():
        raise ValueError(f"Đường dẫn không tồn tại: {path}")

    return path_obj


def validate_file_size(file_path: Path) -> int:
    """
    Validate kích thước file

    Args:
        file_path: Đường dẫn file

    Returns:
        Kích thước file (bytes)

    Raises:
        ValueError: Nếu file quá lớn
    """
    settings = get_settings()
    size = file_path.stat().st_size

    if size > settings.max_file_size:
        raise ValueError(
            f"File quá lớn: {size} bytes (tối đa {settings.max_file_size} bytes)"
        )

    return size


def sanitize_filename(filename: str) -> str:
    """
    Làm sạch tên file, loại bỏ ký tự nguy hiểm

    Args:
        filename: Tên file gốc

    Returns:
        Tên file đã được làm sạch
    """
    # Loại bỏ ký tự đặc biệt
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Loại bỏ khoảng trắng thừa
    filename = re.sub(r'\s+', ' ', filename).strip()
    # Giới hạn độ dài
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename


def is_safe_command(command: str, allowed_commands: List[str]) -> bool:
    """
    Kiểm tra command có được phép chạy không

    Args:
        command: Command cần kiểm tra
        allowed_commands: Danh sách commands được phép

    Returns:
        True nếu được phép, False nếu không
    """
    # Lấy tên command (không có args)
    cmd_name = command.strip().split()[0] if command.strip() else ""

    return cmd_name in allowed_commands


# =============================================================================
# FILE UTILITIES - Tiện ích File
# =============================================================================

def read_file_safe(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    Đọc file an toàn với error handling

    Args:
        file_path: Đường dẫn file
        encoding: Encoding của file

    Returns:
        Nội dung file

    Raises:
        ValueError: Nếu có lỗi đọc file
    """
    settings = get_settings()
    path = validate_path(file_path, must_exist=True)
    validate_file_size(path)

    try:
        content = path.read_text(encoding=encoding)
        get_logger().debug(
            "Đọc file thành công",
            file_path=str(path),
            size=len(content)
        )
        return content
    except UnicodeDecodeError:
        # Thử encoding khác
        try:
            content = path.read_text(encoding="latin-1")
            get_logger().warning(
                "Đọc file với encoding latin-1",
                file_path=str(path)
            )
            return content
        except Exception as e:
            raise ValueError(f"Không thể đọc file: {e}")
    except Exception as e:
        raise ValueError(f"Lỗi đọc file: {e}")


def write_file_safe(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> Path:
    """
    Ghi file an toàn với error handling

    Args:
        file_path: Đường dẫn file
        content: Nội dung cần ghi
        encoding: Encoding của file
        create_dirs: Tạo thư mục nếu chưa tồn tại

    Returns:
        Path đến file đã ghi

    Raises:
        ValueError: Nếu có lỗi ghi file
    """
    settings = get_settings()

    if not settings.allow_write:
        raise ValueError("Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)")

    path = validate_path(file_path, must_exist=False)

    # Validate kích thước nội dung
    content_size = len(content.encode(encoding))
    if content_size > settings.max_file_size:
        raise ValueError(
            f"Nội dung quá lớn: {content_size} bytes "
            f"(tối đa {settings.max_file_size} bytes)"
        )

    # Tạo thư mục nếu cần
    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)

    try:
        path.write_text(content, encoding=encoding)
        get_logger().info(
            "Ghi file thành công",
            file_path=str(path),
            size=content_size
        )
        return path
    except Exception as e:
        raise ValueError(f"Lỗi ghi file: {e}")


# =============================================================================
# STRING UTILITIES - Tiện ích Chuỗi
# =============================================================================

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Cắt ngắn chuỗi nếu quá dài

    Args:
        text: Chuỗi gốc
        max_length: Độ dài tối đa
        suffix: Hậu tố thêm vào khi cắt

    Returns:
        Chuỗi đã cắt ngắn
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_code_blocks(text: str, language: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Trích xuất các code blocks từ markdown

    Args:
        text: Văn bản markdown
        language: Ngôn ngữ lọc (ví dụ: "python", "java")

    Returns:
        List các dict với keys: language, code
    """
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    blocks = []
    for lang, code in matches:
        if language is None or lang.lower() == language.lower():
            blocks.append({
                "language": lang or "text",
                "code": code.strip()
            })

    return blocks


def format_code_for_display(code: str, language: str = "text") -> str:
    """
    Format code để hiển thị trong markdown

    Args:
        code: Mã nguồn
        language: Ngôn ngữ lập trình

    Returns:
        Chuỗi markdown đã format
    """
    return f"```{language}\n{code}\n```"


# =============================================================================
# TIME UTILITIES - Tiện ích Thời gian
# =============================================================================

def get_timestamp() -> str:
    """Lấy timestamp hiện tại dạng ISO"""
    return datetime.utcnow().isoformat() + "Z"


def format_duration(seconds: float) -> str:
    """
    Format thời gian từ giây sang chuỗi dễ đọc

    Args:
        seconds: Số giây

    Returns:
        Chuỗi thời gian đã format
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


# =============================================================================
# HASH UTILITIES - Tiện ích Hash
# =============================================================================

def compute_file_hash(file_path: Path, algorithm: str = "md5") -> str:
    """
    Tính hash của file

    Args:
        file_path: Đường dẫn file
        algorithm: Thuật toán hash (md5, sha1, sha256)

    Returns:
        Hash string
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def compute_string_hash(text: str, algorithm: str = "md5") -> str:
    """
    Tính hash của chuỗi

    Args:
        text: Chuỗi cần hash
        algorithm: Thuật toán hash

    Returns:
        Hash string
    """
    hash_func = hashlib.new(algorithm)
    hash_func.update(text.encode("utf-8"))
    return hash_func.hexdigest()


# =============================================================================
# ERROR HANDLING - Xử lý Lỗi
# =============================================================================

class MCPError(Exception):
    """Lỗi MCP tùy chỉnh"""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: Optional[Dict] = None):
        """
        Khởi tạo lỗi MCP

        Args:
            message: Thông báo lỗi
            code: Mã lỗi
            details: Chi tiết bổ sung
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển thành dict"""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


def handle_exception(func):
    """
    Decorator để xử lý exception và log

    Args:
        func: Function cần wrap

    Returns:
        Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MCPError:
            # Lỗi MCP đã được xử lý, chỉ log
            get_logger().error("Lỗi MCP", exc_info=True)
            raise
        except Exception as e:
            # Lỗi không mong đợi
            get_logger().error(
                "Lỗi không mong đợi",
                function=func.__name__,
                error=str(e),
                exc_info=True
            )
            raise MCPError(
                message=f"Lỗi hệ thống: {str(e)}",
                code="SYSTEM_ERROR"
            )

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MCPError:
            get_logger().error("Lỗi MCP", exc_info=True)
            raise
        except Exception as e:
            get_logger().error(
                "Lỗi không mong đợi",
                function=func.__name__,
                error=str(e),
                exc_info=True
            )
            raise MCPError(
                message=f"Lỗi hệ thống: {str(e)}",
                code="SYSTEM_ERROR"
            )

    # Trả về wrapper phù hợp
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


# =============================================================================
# PERFORMANCE UTILITIES - Tiện ích Hiệu suất
# =============================================================================

@contextmanager
def timer(operation_name: str):
    """
    Context manager để đo thời gian thực thi

    Args:
        operation_name: Tên thao tác

    Yields:
        None
    """
    start_time = time.time()
    get_logger().debug(f"Bắt đầu: {operation_name}")

    try:
        yield
    finally:
        elapsed = time.time() - start_time
        get_logger().info(
            f"Hoàn thành: {operation_name}",
            duration=format_duration(elapsed),
            seconds=elapsed
        )


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator retry với exponential backoff

    Args:
        max_attempts: Số lần thử tối đa
        delay: Delay ban đầu (giây)
        backoff: Hệ số tăng delay

    Returns:
        Decorator
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        get_logger().warning(
                            "Thử lại lần nữa",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=current_delay,
                            error=str(e)
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise MCPError(
                message=f"Thất bại sau {max_attempts} lần thử: {str(last_exception)}",
                code="RETRY_EXHAUSTED"
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        get_logger().warning(
                            "Thử lại lần nữa",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                            delay=current_delay,
                            error=str(e)
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise MCPError(
                message=f"Thất bại sau {max_attempts} lần thử: {str(last_exception)}",
                code="RETRY_EXHAUSTED"
            )

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# DATA UTILITIES - Tiện ích Dữ liệu
# =============================================================================

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge hai dict sâu (deep merge)

    Args:
        base: Dict gốc
        override: Dict ghi đè

    Returns:
        Dict đã merge
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Làm phẳng dict lồng nhau

    Args:
        d: Dict cần làm phẳng
        parent_key: Key cha
        sep: Separator

    Returns:
        Dict đã làm phẳng
    """
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# =============================================================================
# VIETNAMESE LANGUAGE UTILITIES - Tiện ích Tiếng Việt
# =============================================================================

def remove_vietnamese_accents(text: str) -> str:
    """
    Loại bỏ dấu tiếng Việt

    Args:
        text: Văn bản tiếng Việt

    Returns:
        Văn bản không dấu
    """
    # Mapping các ký tự có dấu sang không dấu
    accent_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd',
        'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
        'Ă': 'A', 'Ắ': 'A', 'Ằ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
        'Â': 'A', 'Ấ': 'A', 'Ầ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
        'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
        'Ê': 'E', 'Ế': 'E', 'Ề': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
        'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
        'Ô': 'O', 'Ố': 'O', 'Ồ': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
        'Ơ': 'O', 'Ớ': 'O', 'Ờ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
        'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
        'Ư': 'U', 'Ứ': 'U', 'Ừ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
        'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
        'Đ': 'D'
    }

    result = []
    for char in text:
        result.append(accent_map.get(char, char))
    return ''.join(result)


def slugify_vietnamese(text: str) -> str:
    """
    Tạo slug từ văn bản tiếng Việt

    Args:
        text: Văn bản tiếng Việt

    Returns:
        Slug (không dấu, lowercase, dùng - thay vì space)
    """
    # Loại bỏ dấu
    text = remove_vietnamese_accents(text)
    # Chuyển lowercase
    text = text.lower()
    # Thay thế ký tự không phải chữ/số bằng dấu gạch ngang
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Loại bỏ dấu gạch ngang thừa
    text = re.sub(r'-+', '-', text)
    # Cắt đầu cuối
    text = text.strip('-')
    return text


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "logger",
    # Validation
    "validate_path",
    "validate_file_size",
    "sanitize_filename",
    "is_safe_command",
    # File utilities
    "read_file_safe",
    "write_file_safe",
    # String utilities
    "truncate_string",
    "extract_code_blocks",
    "format_code_for_display",
    # Time utilities
    "get_timestamp",
    "format_duration",
    # Hash utilities
    "compute_file_hash",
    "compute_string_hash",
    # Error handling
    "MCPError",
    "handle_exception",
    # Performance
    "timer",
    "retry",
    # Data utilities
    "deep_merge",
    "flatten_dict",
    # Vietnamese
    "remove_vietnamese_accents",
    "slugify_vietnamese"
]