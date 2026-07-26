"""
MCP Programming Support Server - Công cụ Filesystem
Cung cấp các công cụ đọc, ghi, tìm kiếm file an toàn
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import os

from config import get_settings
from utils import (
    get_logger,
    validate_path,
    validate_file_size,
    read_file_safe,
    write_file_safe,
    sanitize_filename,
    MCPError,
    handle_exception
)

logger = get_logger()


# =============================================================================
# TOOL: ĐỌC FILE
# =============================================================================

@handle_exception
def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Đọc nội dung file từ workspace

    Args:
        file_path: Đường dẫn file (tương đối hoặc tuyệt đối trong workspace)
        encoding: Encoding của file (mặc định: utf-8)

    Returns:
        Dict chứa nội dung file và metadata

    Raises:
        MCPError: Nếu có lỗi đọc file
    """
    settings = get_settings()

    logger.info(
        "Đọc file",
        file_path=file_path,
        encoding=encoding
    )

    try:
        # Đọc file an toàn
        content = read_file_safe(file_path, encoding=encoding)

        # Lấy thông tin file
        path = validate_path(file_path, must_exist=True)
        stat = path.stat()

        result = {
            "success": True,
            "file_path": str(path.relative_to(settings.workspace)),
            "content": content,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "encoding": encoding,
            "line_count": content.count('\n') + (1 if content and not content.endswith('\n') else 0),
            "char_count": len(content)
        }

        logger.info(
            "Đọc file thành công",
            file_path=str(path.relative_to(settings.workspace)),
            size_bytes=stat.st_size
        )

        return result

    except Exception as e:
        logger.error("Lỗi đọc file", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể đọc file: {str(e)}",
            code="FILE_READ_ERROR",
            details={"file_path": file_path}
        )


# =============================================================================
# TOOL: GHI FILE
# =============================================================================

@handle_exception
def write_file(file_path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Ghi nội dung vào file

    Args:
        file_path: Đường dẫn file (tương đối hoặc tuyệt đối trong workspace)
        content: Nội dung cần ghi
        encoding: Encoding của file (mặc định: utf-8)

    Returns:
        Dict chứa thông tin file đã ghi

    Raises:
        MCPError: Nếu có lỗi ghi file
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info(
        "Ghi file",
        file_path=file_path,
        content_length=len(content),
        encoding=encoding
    )

    try:
        # Ghi file an toàn
        path = write_file_safe(file_path, content, encoding=encoding)

        result = {
            "success": True,
            "file_path": str(path.relative_to(settings.workspace)),
            "size_bytes": len(content.encode(encoding)),
            "size_mb": round(len(content.encode(encoding)) / (1024 * 1024), 2),
            "encoding": encoding,
            "line_count": content.count('\n') + (1 if content and not content.endswith('\n') else 0)
        }

        logger.info(
            "Ghi file thành công",
            file_path=str(path.relative_to(settings.workspace)),
            size_bytes=len(content.encode(encoding))
        )

        return result

    except Exception as e:
        logger.error("Lỗi ghi file", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể ghi file: {str(e)}",
            code="FILE_WRITE_ERROR",
            details={"file_path": file_path}
        )


# =============================================================================
# TOOL: THAY THẾ VĂN BẢN
# =============================================================================

@handle_exception
def replace_text(
    file_path: str,
    old_text: str,
    new_text: str,
    encoding: str = "utf-8",
    replace_all: bool = False
) -> Dict[str, Any]:
    """
    Thay thế văn bản trong file

    Args:
        file_path: Đường dẫn file
        old_text: Văn bản cần thay thế
        new_text: Văn bản thay thế
        encoding: Encoding của file
        replace_all: Thay thế tất cả occurrences (True) hay chỉ đầu tiên (False)

    Returns:
        Dict chứa thông tin thay thế

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info(
        "Thay thế văn bản",
        file_path=file_path,
        old_text_length=len(old_text),
        new_text_length=len(new_text),
        replace_all=replace_all
    )

    try:
        # Đọc file
        content = read_file_safe(file_path, encoding=encoding)

        # Đếm số lần xuất hiện
        occurrences = content.count(old_text)

        if occurrences == 0:
            raise MCPError(
                message=f"Không tìm thấy văn bản cần thay thế trong file",
                code="TEXT_NOT_FOUND",
                details={"file_path": file_path, "old_text": old_text[:100]}
            )

        # Thay thế
        if replace_all:
            new_content = content.replace(old_text, new_text)
            actual_replacements = occurrences
        else:
            new_content = content.replace(old_text, new_text, 1)
            actual_replacements = 1

        # Ghi file
        path = write_file_safe(file_path, new_content, encoding=encoding)

        result = {
            "success": True,
            "file_path": str(path.relative_to(settings.workspace)),
            "occurrences_found": occurrences,
            "replacements_made": actual_replacements,
            "old_text_length": len(old_text),
            "new_text_length": len(new_text)
        }

        logger.info(
            "Thay thế văn bản thành công",
            file_path=str(path.relative_to(settings.workspace)),
            replacements=actual_replacements
        )

        return result

    except MCPError:
        raise
    except Exception as e:
        logger.error("Lỗi thay thế văn bản", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể thay thế văn bản: {str(e)}",
            code="TEXT_REPLACE_ERROR",
            details={"file_path": file_path}
        )


# =============================================================================
# TOOL: LIỆT KÊ THƯ MỤC
# =============================================================================

@handle_exception
def list_directory(
    directory_path: str,
    recursive: bool = False,
    show_hidden: bool = False,
    file_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Liệt kê nội dung thư mục

    Args:
        directory_path: Đường dẫn thư mục
        recursive: Liệt kê đệ quy (True) hay chỉ thư mục hiện tại (False)
        show_hidden: Hiển thị file/thư mục ẩn (bắt đầu bằng .)
        file_pattern: Filter theo pattern (ví dụ: "*.py", "*.java")

    Returns:
        Dict chứa danh sách file/thư mục

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Liệt kê thư mục",
        directory_path=directory_path,
        recursive=recursive,
        show_hidden=show_hidden,
        file_pattern=file_pattern
    )

    try:
        # Validate path
        path = validate_path(directory_path, must_exist=True)

        if not path.is_dir():
            raise MCPError(
                message=f"Đường dẫn không phải thư mục: {directory_path}",
                code="NOT_A_DIRECTORY"
            )

        # Thu thập files
        files = []
        directories = []

        if recursive:
            # Duyệt đệ quy
            for root, dirs, filenames in os.walk(path):
                # Filter hidden
                if not show_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    filenames = [f for f in filenames if not f.startswith('.')]

                root_path = Path(root)

                # Thêm directories
                for dirname in dirs:
                    dir_path = root_path / dirname
                    try:
                        dir_path.relative_to(settings.workspace)
                        dir_stat = dir_path.stat()
                        directories.append({
                            "name": dirname,
                            "path": str(dir_path.relative_to(settings.workspace)),
                            "size_bytes": dir_stat.st_size,
                            "modified_at": datetime.fromtimestamp(dir_stat.st_mtime).isoformat()
                        })
                    except ValueError:
                        pass

                # Thêm files
                for filename in filenames:
                    # Filter by pattern
                    if file_pattern:
                        import fnmatch
                        if not fnmatch.fnmatch(filename, file_pattern):
                            continue

                    file_path = root_path / filename
                    try:
                        file_path.relative_to(settings.workspace)
                        file_stat = file_path.stat()
                        files.append({
                            "name": filename,
                            "path": str(file_path.relative_to(settings.workspace)),
                            "size_bytes": file_stat.st_size,
                            "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                            "extension": file_path.suffix,
                            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                        })
                    except ValueError:
                        pass
        else:
            # Chỉ thư mục hiện tại
            for item in path.iterdir():
                # Filter hidden
                if not show_hidden and item.name.startswith('.'):
                    continue

                # Filter by pattern
                if file_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(item.name, file_pattern):
                        continue

                try:
                    item.relative_to(settings.workspace)
                    stat = item.stat()

                    if item.is_dir():
                        directories.append({
                            "name": item.name,
                            "path": str(item.relative_to(settings.workspace)),
                            "size_bytes": stat.st_size,
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                    else:
                        files.append({
                            "name": item.name,
                            "path": str(item.relative_to(settings.workspace)),
                            "size_bytes": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "extension": item.suffix,
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                except ValueError:
                    pass

        result = {
            "success": True,
            "directory": str(path.relative_to(settings.workspace)),
            "directories": sorted(directories, key=lambda x: x["name"]),
            "files": sorted(files, key=lambda x: x["name"]),
            "total_directories": len(directories),
            "total_files": len(files)
        }

        logger.info(
            "Liệt kê thư mục thành công",
            directory=str(path.relative_to(settings.workspace)),
            total_directories=len(directories),
            total_files=len(files)
        )

        return result

    except MCPError:
        raise
    except Exception as e:
        logger.error("Lỗi liệt kê thư mục", directory_path=directory_path, error=str(e))
        raise MCPError(
            message=f"Không thể liệt kê thư mục: {str(e)}",
            code="DIRECTORY_LIST_ERROR",
            details={"directory_path": directory_path}
        )


# =============================================================================
# TOOL: TÌM KIẾM FILES
# =============================================================================

@handle_exception
def search_files(
    directory_path: str,
    pattern: str,
    recursive: bool = True,
    case_sensitive: bool = False
) -> Dict[str, Any]:
    """
    Tìm kiếm file theo pattern (glob)

    Args:
        directory_path: Đường dẫn thư mục
        pattern: Pattern tìm kiếm (ví dụ: "*.py", "**/*.java")
        recursive: Tìm kiếm đệ quy
        case_sensitive: Phân biệt chữ hoa/thường

    Returns:
        Dict chứa danh sách file tìm thấy

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Tìm kiếm files",
        directory_path=directory_path,
        pattern=pattern,
        recursive=recursive
    )

    try:
        # Validate path
        path = validate_path(directory_path, must_exist=True)

        if not path.is_dir():
            raise MCPError(
                message=f"Đường dẫn không phải thư mục: {directory_path}",
                code="NOT_A_DIRECTORY"
            )

        # Tìm files
        found_files = []

        if recursive:
            # Tìm đệ quy
            for file_path in path.rglob(pattern):
                try:
                    file_path.relative_to(settings.workspace)
                    if file_path.is_file():
                        stat = file_path.stat()
                        found_files.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(settings.workspace)),
                            "size_bytes": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "extension": file_path.suffix,
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                except ValueError:
                    pass
        else:
            # Chỉ thư mục hiện tại
            for file_path in path.glob(pattern):
                try:
                    file_path.relative_to(settings.workspace)
                    if file_path.is_file():
                        stat = file_path.stat()
                        found_files.append({
                            "name": file_path.name,
                            "path": str(file_path.relative_to(settings.workspace)),
                            "size_bytes": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "extension": file_path.suffix,
                            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                except ValueError:
                    pass

        result = {
            "success": True,
            "directory": str(path.relative_to(settings.workspace)),
            "pattern": pattern,
            "recursive": recursive,
            "files": sorted(found_files, key=lambda x: x["path"]),
            "total_found": len(found_files)
        }

        logger.info(
            "Tìm kiếm files thành công",
            directory=str(path.relative_to(settings.workspace)),
            pattern=pattern,
            total_found=len(found_files)
        )

        return result

    except MCPError:
        raise
    except Exception as e:
        logger.error("Lỗi tìm kiếm files", directory_path=directory_path, error=str(e))
        raise MCPError(
            message=f"Không thể tìm kiếm files: {str(e)}",
            code="FILE_SEARCH_ERROR",
            details={"directory_path": directory_path, "pattern": pattern}
        )


# =============================================================================
# TOOL: TÌM KIẾM VĂN BẢN
# =============================================================================

@handle_exception
def search_text(
    directory_path: str,
    search_text: str,
    file_pattern: str = "*",
    case_sensitive: bool = False,
    regex: bool = False,
    max_results: int = 100
) -> Dict[str, Any]:
    """
    Tìm kiếm văn bản trong các file

    Args:
        directory_path: Đường dẫn thư mục
        search_text: Văn bản cần tìm (hoặc regex pattern)
        file_pattern: Pattern file cần tìm (ví dụ: "*.py", "*.java")
        case_sensitive: Phân biệt chữ hoa/thường
        regex: Sử dụng regex pattern
        max_results: Số kết quả tối đa

    Returns:
        Dict chứa kết quả tìm kiếm

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Tìm kiếm văn bản",
        directory_path=directory_path,
        search_text=search_text[:50],
        file_pattern=file_pattern,
        case_sensitive=case_sensitive,
        regex=regex
    )

    try:
        # Validate path
        path = validate_path(directory_path, must_exist=True)

        if not path.is_dir():
            raise MCPError(
                message=f"Đường dẫn không phải thư mục: {directory_path}",
                code="NOT_A_DIRECTORY"
            )

        # Chuẩn bị search
        if not case_sensitive:
            search_text_lower = search_text.lower()

        # Compile regex nếu cần
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(search_text, flags)
        else:
            pattern = None

        # Tìm kiếm
        results = []
        files_checked = 0

        for file_path in path.rglob(file_pattern):
            try:
                file_path.relative_to(settings.workspace)
                if not file_path.is_file():
                    continue

                # Đọc file
                try:
                    content = read_file_safe(file_path, encoding="utf-8")
                except Exception:
                    # Bỏ qua file không đọc được
                    continue

                files_checked += 1

                # Tìm kiếm
                matches = []
                lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    if regex:
                        if pattern.search(line):
                            matches.append({
                                "line_number": line_num,
                                "line_content": line.strip(),
                                "match": pattern.search(line).group(0)
                            })
                    else:
                        if case_sensitive:
                            if search_text in line:
                                matches.append({
                                    "line_number": line_num,
                                    "line_content": line.strip(),
                                    "match": search_text
                                })
                        else:
                            if search_text_lower in line.lower():
                                matches.append({
                                    "line_number": line_num,
                                    "line_content": line.strip(),
                                    "match": search_text
                                })

                if matches:
                    results.append({
                        "file_path": str(file_path.relative_to(settings.workspace)),
                        "file_name": file_path.name,
                        "matches": matches[:max_results],  # Giới hạn matches per file
                        "total_matches": len(matches)
                    })

                # Giới hạn tổng số results
                if len(results) >= max_results:
                    break

            except ValueError:
                pass

        result = {
            "success": True,
            "directory": str(path.relative_to(settings.workspace)),
            "search_text": search_text,
            "file_pattern": file_pattern,
            "case_sensitive": case_sensitive,
            "regex": regex,
            "files_checked": files_checked,
            "files_with_matches": len(results),
            "results": results[:max_results],
            "total_results": len(results)
        }

        logger.info(
            "Tìm kiếm văn bản thành công",
            directory=str(path.relative_to(settings.workspace)),
            files_checked=files_checked,
            files_with_matches=len(results)
        )

        return result

    except MCPError:
        raise
    except Exception as e:
        logger.error("Lỗi tìm kiếm văn bản", directory_path=directory_path, error=str(e))
        raise MCPError(
            message=f"Không thể tìm kiếm văn bản: {str(e)}",
            code="TEXT_SEARCH_ERROR",
            details={"directory_path": directory_path, "search_text": search_text}
        )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "read_file",
    "write_file",
    "replace_text",
    "list_directory",
    "search_files",
    "search_text"
]