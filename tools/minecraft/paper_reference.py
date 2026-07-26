"""
MCP Programming Support Server - Paper Server Reference
Công cụ tham khảo và phân tích mã nguồn Paper server
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import re

from config import get_settings
from utils import get_logger, MCPError, handle_exception, read_file_safe, search_text

logger = get_logger()


# =============================================================================
# TOOL: THAM KHẢO MÃ NGUỒN PAPER
# =============================================================================

@handle_exception
def reference_paper_source(
    query: str,
    paper_path: Optional[str] = None,
    search_type: str = "auto",
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Tham khảo mã nguồn Paper server

    Args:
        query: Từ khóa tìm kiếm (ví dụ: "PlayerJoinEvent", "InventoryClickEvent")
        paper_path: Đường dẫn đến thư mục mã nguồn Paper (nếu None dùng config)
        search_type: Loại tìm kiếm: auto, class, method, event, annotation
        max_results: Số kết quả tối đa

    Returns:
        Dict chứa kết quả tham khảo

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    # Sử dụng paper_path từ config nếu không có
    if not paper_path:
        paper_path = str(settings.paper_server_path) if settings.paper_server_path else None

    if not paper_path:
        raise MCPError(
            message="Đường dẫn Paper server chưa được cấu hình. "
                    "Vui lòng thêm PAPER_SERVER_PATH vào .env hoặc cung cấp tham số paper_path",
            code="PAPER_PATH_MISSING"
        )

    paper_dir = Path(paper_path)

    if not paper_dir.exists():
        raise MCPError(
            message=f"Thư mục Paper server không tồn tại: {paper_path}",
            code="PAPER_PATH_NOT_FOUND",
            details={"paper_path": paper_path}
        )

    logger.info(
        "Tham khảo mã nguồn Paper",
        query=query,
        paper_path=paper_path,
        search_type=search_type
    )

    try:
        # Auto-detect search type
        if search_type == "auto":
            search_type = _detect_search_type(query)

        # Tìm kiếm theo loại
        if search_type == "event":
            results = _search_events(paper_dir, query, max_results)
        elif search_type == "class":
            results = _search_classes(paper_dir, query, max_results)
        elif search_type == "method":
            results = _search_methods(paper_dir, query, max_results)
        else:
            results = _search_general(paper_dir, query, max_results)

        result = {
            "success": True,
            "query": query,
            "search_type": search_type,
            "paper_path": paper_path,
            "results_count": len(results),
            "results": results
        }

        logger.info(
            "Tham khảo Paper thành công",
            query=query,
            results_count=len(results)
        )

        return result

    except Exception as e:
        logger.error("Lỗi tham khảo Paper", query=query, error=str(e))
        raise MCPError(
            message=f"Không thể tham khảo mã nguồn Paper: {str(e)}",
            code="PAPER_REFERENCE_ERROR",
            details={"query": query, "paper_path": paper_path}
        )


def _detect_search_type(query: str) -> str:
    """Tự động phát hiện loại tìm kiếm"""
    query_lower = query.lower()

    if "event" in query_lower or query.endswith("Event"):
        return "event"
    elif "class" in query_lower or query[0].isupper():
        return "class"
    elif "method" in query_lower or "(" in query:
        return "method"
    else:
        return "general"


def _search_events(paper_dir: Path, query: str, max_results: int) -> List[Dict[str, Any]]:
    """Tìm kiếm Paper events"""
    results = []

    # Paper events thường có tên kết thúc bằng "Event"
    event_patterns = [
        f"*{query}*.java",
        f"*{query}Event*.java"
    ]

    for pattern in event_patterns:
        for event_file in paper_dir.rglob(pattern):
            try:
                content = read_file_safe(str(event_file))
                relative_path = event_file.relative_to(paper_dir)

                # Extract event info
                event_info = _extract_event_info(content, relative_path)
                if event_info:
                    results.append(event_info)

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.warning("Lỗi đọc event file", file=str(event_file), error=str(e))
                continue

        if len(results) >= max_results:
            break

    return results[:max_results]


def _search_classes(paper_dir: Path, query: str, max_results: int) -> List[Dict[str, Any]]:
    """Tìm kiếm Paper classes"""
    results = []

    # Tìm file Java chứa class name
    for java_file in paper_dir.rglob("*.java"):
        try:
            content = read_file_safe(str(java_file))

            # Check if file contains class
            if f"class {query}" in content or f"interface {query}" in content:
                relative_path = java_file.relative_to(paper_dir)

                class_info = _extract_class_info(content, relative_path, query)
                if class_info:
                    results.append(class_info)

                if len(results) >= max_results:
                    break
        except Exception as e:
            logger.warning("Lỗi đọc class file", file=str(java_file), error=str(e))
            continue

    return results[:max_results]


def _search_methods(paper_dir: Path, query: str, max_results: int) -> List[Dict[str, Any]]:
    """Tìm kiếm methods trong Paper code"""
    results = []

    # Tìm method definitions
    for java_file in paper_dir.rglob("*.java"):
        try:
            content = read_file_safe(str(java_file))

            # Tìm method signature
            method_pattern = rf"(public|protected|private)\s+\w+\s+{re.escape(query)}\s*\("
            matches = re.findall(method_pattern, content)

            if matches:
                relative_path = java_file.relative_to(paper_dir)

                for match in matches[:5]:  # Giới hạn mỗi file
                    results.append({
                        "type": "method",
                        "name": query,
                        "signature": match,
                        "file": str(relative_path),
                        "file_name": java_file.name
                    })

                if len(results) >= max_results:
                    break
        except Exception as e:
            logger.warning("Lỗi đọc method file", file=str(java_file), error=str(e))
            continue

    return results[:max_results]


def _search_general(paper_dir: Path, query: str, max_results: int) -> List[Dict[str, Any]]:
    """Tìm kiếm tổng quát"""
    results = []

    # Sử dụng search_text utility
    search_result = search_text(
        directory_path=str(paper_dir),
        search_text=query,
        file_pattern="*.java",
        case_sensitive=False,
        max_results=max_results
    )

    for file_match in search_result.get("results", []):
        results.append({
            "type": "general",
            "file": file_match["file_path"],
            "file_name": file_match["file_name"],
            "matches": file_match["total_matches"],
            "sample_lines": [m["line_content"] for m in file_match["matches"][:3]]
        })

    return results[:max_results]


def _extract_event_info(content: str, file_path: Path) -> Optional[Dict[str, Any]]:
    """Trích xuất thông tin event từ Java file"""
    try:
        lines = content.split('\n')

        # Tìm class name
        class_match = re.search(r"class\s+(\w+Event)", content)
        if not class_match:
            return None

        class_name = class_match.group(1)

        # Tìm annotation @EventHandler
        has_handler = "@EventHandler" in content

        # Tìm package
        package_match = re.search(r"package\s+([\w.]+);", content)
        package = package_match.group(1) if package_match else ""

        # Tìm extends/implements
        extends_match = re.search(r"extends\s+(\w+)", content)
        extends = extends_match.group(1) if extends_match else ""

        return {
            "type": "event",
            "class_name": class_name,
            "package": package,
            "extends": extends,
            "has_handler": has_handler,
            "file": str(file_path),
            "file_name": file_path.name
        }
    except Exception as e:
        logger.warning("Lỗi extract event info", error=str(e))
        return None


def _extract_class_info(content: str, file_path: Path, class_name: str) -> Optional[Dict[str, Any]]:
    """Trích xuất thông tin class từ Java file"""
    try:
        lines = content.split('\n')

        # Tìm package
        package_match = re.search(r"package\s+([\w.]+);", content)
        package = package_match.group(1) if package_match else ""

        # Tìm extends/implements
        extends_match = re.search(r"extends\s+(\w+)", content)
        extends = extends_match.group(1) if extends_match else ""

        implements_match = re.search(r"implements\s+([\w,\s]+)", content)
        implements = implements_match.group(1).strip() if implements_match else ""

        # Tìm annotations
        annotations = re.findall(r"@(\w+)", content)

        # Đếm methods
        methods = re.findall(r"(public|protected|private)\s+\w+\s+\w+\s*\(", content)

        return {
            "type": "class",
            "class_name": class_name,
            "package": package,
            "extends": extends,
            "implements": implements,
            "annotations": list(set(annotations))[:10],
            "method_count": len(methods),
            "file": str(file_path),
            "file_name": file_path.name
        }
    except Exception as e:
        logger.warning("Lỗi extract class info", error=str(e))
        return None


# =============================================================================
# TOOL: TÌM PAPER API USAGE PATTERNS
# =============================================================================

@handle_exception
def find_paper_api_usage(
    api_class: str,
    paper_path: Optional[str] = None,
    max_examples: int = 5
) -> Dict[str, Any]:
    """
    Tìm ví dụ sử dụng Paper API

    Args:
        api_class: Tên class/API cần tìm (ví dụ: "Player", "Inventory", "ItemStack")
        paper_path: Đường dẫn Paper source
        max_examples: Số ví dụ tối đa

    Returns:
        Dict chứa ví dụ sử dụng

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not paper_path:
        paper_path = str(settings.paper_server_path) if settings.paper_server_path else None

    if not paper_path:
        raise MCPError(
            message="Đường dẫn Paper server chưa được cấu hình",
            code="PAPER_PATH_MISSING"
        )

    logger.info("Tìm Paper API usage", api_class=api_class, max_examples=max_examples)

    try:
        paper_dir = Path(paper_path)

        # Tìm các file sử dụng API class
        examples = []

        for java_file in paper_dir.rglob("*.java"):
            try:
                content = read_file_safe(str(java_file))

                # Check if file uses the API class
                if api_class in content:
                    # Extract usage examples
                    usage_examples = _extract_api_usage(content, api_class)

                    if usage_examples:
                        relative_path = java_file.relative_to(paper_dir)
                        examples.append({
                            "file": str(relative_path),
                            "file_name": java_file.name,
                            "usage_count": len(usage_examples),
                            "examples": usage_examples[:3]  # Top 3 examples
                        })

                    if len(examples) >= max_examples:
                        break
            except Exception as e:
                logger.warning("Lỗi đọc file", file=str(java_file), error=str(e))
                continue

        result = {
            "success": True,
            "api_class": api_class,
            "examples_found": len(examples),
            "examples": examples[:max_examples]
        }

        logger.info("Tìm API usage thành công", api_class=api_class, examples=len(examples))

        return result

    except Exception as e:
        logger.error("Lỗi tìm API usage", api_class=api_class, error=str(e))
        raise MCPError(
            message=f"Không thể tìm API usage: {str(e)}",
            code="API_USAGE_ERROR",
            details={"api_class": api_class}
        )


def _extract_api_usage(content: str, api_class: str) -> List[str]:
    """Trích xuất ví dụ sử dụng API"""
    examples = []
    lines = content.split('\n')

    for i, line in enumerate(lines):
        if api_class in line:
            # Lấy context (3 dòng trước và sau)
            start = max(0, i - 3)
            end = min(len(lines), i + 4)
            context = "\n".join(lines[start:end])

            examples.append(context.strip())

    return examples[:5]  # Giới hạn


# =============================================================================
# TOOL: TRÍCH XUẤT PAPER PATTERNS
# =============================================================================

@handle_exception
def extract_paper_patterns(
    pattern_type: str,
    paper_path: Optional[str] = None,
    max_patterns: int = 10
) -> Dict[str, Any]:
    """
    Trích xuất các patterns phổ biến từ Paper code

    Args:
        pattern_type: Loại pattern: listener, command, scheduler, config
        paper_path: Đường dẫn Paper source
        max_patterns: Số patterns tối đa

    Returns:
        Dict chứa các patterns

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not paper_path:
        paper_path = str(settings.paper_server_path) if settings.paper_server_path else None

    if not paper_path:
        raise MCPError(
            message="Đường dẫn Paper server chưa được cấu hình",
            code="PAPER_PATH_MISSING"
        )

    logger.info("Trích xuất Paper patterns", pattern_type=pattern_type)

    try:
        paper_dir = Path(paper_path)
        patterns = []

        if pattern_type == "listener":
            patterns = _extract_listener_patterns(paper_dir, max_patterns)
        elif pattern_type == "command":
            patterns = _extract_command_patterns(paper_dir, max_patterns)
        elif pattern_type == "scheduler":
            patterns = _extract_scheduler_patterns(paper_dir, max_patterns)
        elif pattern_type == "config":
            patterns = _extract_config_patterns(paper_dir, max_patterns)
        else:
            raise MCPError(
                message=f"Pattern type không hỗ trợ: {pattern_type}",
                code="UNSUPPORTED_PATTERN_TYPE"
            )

        result = {
            "success": True,
            "pattern_type": pattern_type,
            "patterns_found": len(patterns),
            "patterns": patterns
        }

        logger.info("Trích xuất patterns thành công", pattern_type=pattern_type, patterns=len(patterns))

        return result

    except Exception as e:
        logger.error("Lỗi trích xuất patterns", pattern_type=pattern_type, error=str(e))
        raise MCPError(
            message=f"Không thể trích xuất patterns: {str(e)}",
            code="PATTERN_EXTRACTION_ERROR",
            details={"pattern_type": pattern_type}
        )


def _extract_listener_patterns(paper_dir: Path, max_patterns: int) -> List[Dict[str, Any]]:
    """Trích xuất listener patterns"""
    patterns = []

    for java_file in paper_dir.rglob("*Listener.java"):
        if len(patterns) >= max_patterns:
            break

        try:
            content = read_file_safe(str(java_file))
            relative_path = java_file.relative_to(paper_dir)

            # Extract @EventHandler methods
            event_handlers = re.findall(
                r"@EventHandler\s+(?:public|protected|private)\s+\w+\s+(\w+)\s*\([^)]*\)",
                content
            )

            if event_handlers:
                patterns.append({
                    "file": str(relative_path),
                    "file_name": java_file.name,
                    "event_handlers": event_handlers[:5],
                    "handler_count": len(event_handlers)
                })
        except Exception as e:
            logger.warning("Lỗi đọc listener", file=str(java_file), error=str(e))
            continue

    return patterns


def _extract_command_patterns(paper_dir: Path, max_patterns: int) -> List[Dict[str, Any]]:
    """Trích xuất command patterns"""
    patterns = []

    for java_file in paper_dir.rglob("*Command.java"):
        if len(patterns) >= max_patterns:
            break

        try:
            content = read_file_safe(str(java_file))
            relative_path = java_file.relative_to(paper_dir)

            # Extract command info
            class_match = re.search(r"class\s+(\w+Command)", content)
            class_name = class_match.group(1) if class_match else java_file.stem

            # Tìm @Override onCommand
            has_on_command = "onCommand" in content

            patterns.append({
                "file": str(relative_path),
                "file_name": java_file.name,
                "class_name": class_name,
                "has_on_command": has_on_command
            })
        except Exception as e:
            logger.warning("Lỗi đọc command", file=str(java_file), error=str(e))
            continue

    return patterns


def _extract_scheduler_patterns(paper_dir: Path, max_patterns: int) -> List[Dict[str, Any]]:
    """Trích xuất scheduler patterns"""
    patterns = []

    for java_file in paper_dir.rglob("*.java"):
        if len(patterns) >= max_patterns:
            break

        try:
            content = read_file_safe(str(java_file))

            # Tìm scheduler usage
            if "Bukkit.getScheduler()" in content or "runTask" in content or "scheduleSyncRepeatingTask" in content:
                relative_path = java_file.relative_to(paper_dir)

                # Extract scheduler calls
                scheduler_calls = re.findall(
                    r"(runTask|scheduleSyncRepeatingTask|runTaskTimer|runTaskLater)\s*\(",
                    content
                )

                patterns.append({
                    "file": str(relative_path),
                    "file_name": java_file.name,
                    "scheduler_calls": list(set(scheduler_calls))
                })
        except Exception as e:
            logger.warning("Lỗi đọc scheduler", file=str(java_file), error=str(e))
            continue

    return patterns[:max_patterns]


def _extract_config_patterns(paper_dir: Path, max_patterns: int) -> List[Dict[str, Any]]:
    """Trích xuất config patterns"""
    patterns = []

    for java_file in paper_dir.rglob("*.java"):
        if len(patterns) >= max_patterns:
            break

        try:
            content = read_file_safe(str(java_file))

            # Tìm config usage
            if "getConfig()" in content or "saveConfig()" in content or "reloadConfig()" in content:
                relative_path = java_file.relative_to(paper_dir)

                config_methods = []
                if "getConfig()" in content:
                    config_methods.append("getConfig()")
                if "saveConfig()" in content:
                    config_methods.append("saveConfig()")
                if "reloadConfig()" in content:
                    config_methods.append("reloadConfig()")

                patterns.append({
                    "file": str(relative_path),
                    "file_name": java_file.name,
                    "config_methods": config_methods
                })
        except Exception as e:
            logger.warning("Lỗi đọc config", file=str(java_file), error=str(e))
            continue

    return patterns[:max_patterns]


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "reference_paper_source",
    "find_paper_api_usage",
    "extract_paper_patterns"
]