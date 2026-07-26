"""
MCP Programming Support Server - Công cụ Review & Quality
Review code, kiểm soát lỗi, dọn dẹp code, thêm debug logs
"""

from typing import Optional, Dict, Any, List, Tuple
import ast
import re
from pathlib import Path

from config import get_settings
from utils import get_logger, MCPError, handle_exception, read_file_safe, write_file_safe

logger = get_logger()


# =============================================================================
# TOOL: REVIEW CODE
# =============================================================================

@handle_exception
def review_code(
    file_path: str,
    language: str = "auto",
    check_style: bool = True,
    check_security: bool = True,
    check_performance: bool = True,
    check_best_practices: bool = True
) -> Dict[str, Any]:
    """
    Review code với các tiêu chí khác nhau

    Args:
        file_path: Đường dẫn file cần review
        language: Ngôn ngữ lập trình (auto, python, java, javascript, etc.)
        check_style: Kiểm tra code style
        check_security: Kiểm tra bảo mật
        check_performance: Kiểm tra hiệu suất
        check_best_practices: Kiểm tra best practices

    Returns:
        Dict chứa kết quả review

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Review code",
        file_path=file_path,
        language=language,
        check_style=check_style,
        check_security=check_security
    )

    try:
        # Đọc file
        content = read_file_safe(file_path)
        path = Path(file_path)

        # Auto-detect language
        if language == "auto":
            language = _detect_language(path)

        issues = []
        suggestions = []

        # Review theo ngôn ngữ
        if language == "python":
            issues, suggestions = _review_python_code(content, check_style, check_security, check_performance, check_best_practices)
        elif language == "java":
            issues, suggestions = _review_java_code(content, check_style, check_security, check_performance, check_best_practices)
        elif language in ["javascript", "typescript"]:
            issues, suggestions = _review_javascript_code(content, check_style, check_security, check_performance, check_best_practices)
        else:
            # Generic review
            issues, suggestions = _review_generic_code(content, check_style, check_security)

        # Phân loại issues theo severity
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        warning_issues = [i for i in issues if i["severity"] == "warning"]
        info_issues = [i for i in issues if i["severity"] == "info"]

        result = {
            "success": True,
            "file_path": file_path,
            "language": language,
            "total_issues": len(issues),
            "critical_issues": len(critical_issues),
            "warnings": len(warning_issues),
            "info": len(info_issues),
            "issues": issues,
            "suggestions": suggestions,
            "score": _calculate_quality_score(issues, suggestions)
        }

        logger.info(
            "Review code thành công",
            file_path=file_path,
            total_issues=len(issues),
            score=result["score"]
        )

        return result

    except Exception as e:
        logger.error("Lỗi review code", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể review code: {str(e)}",
            code="CODE_REVIEW_ERROR",
            details={"file_path": file_path}
        )


def _detect_language(file_path: Path) -> str:
    """Tự động phát hiện ngôn ngữ từ file extension"""
    ext_map = {
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
        ".kt": "kotlin",
        ".scala": "scala"
    }
    return ext_map.get(file_path.suffix.lower(), "unknown")


def _review_python_code(content: str, check_style: bool, check_security: bool,
                        check_performance: bool, check_best_practices: bool) -> Tuple[List[Dict], List[Dict]]:
    """Review Python code"""
    issues = []
    suggestions = []

    lines = content.split('\n')

    # Check style
    if check_style:
        for i, line in enumerate(lines, 1):
            # Line too long
            if len(line) > 120:
                issues.append({
                    "line": i,
                    "severity": "warning",
                    "category": "style",
                    "message": "Dòng quá dài (>120 ký tự)",
                    "suggestion": "Chia nhỏ dòng hoặc sử dụng implicit line continuation"
                })

            # Trailing whitespace
            if line != line.rstrip():
                issues.append({
                    "line": i,
                    "severity": "info",
                    "category": "style",
                    "message": "Có khoảng trắng thừa ở cuối dòng",
                    "suggestion": "Xóa khoảng trắng thừa"
                })

            # Multiple imports on one line
            if line.strip().startswith("import ") and "," in line and "(" not in line:
                issues.append({
                    "line": i,
                    "severity": "warning",
                    "category": "style",
                    "message": "Multiple imports trên một dòng",
                    "suggestion": "Tách thành nhiều dòng import"
                })

    # Check security
    if check_security:
        for i, line in enumerate(lines, 1):
            # eval() usage
            if "eval(" in line:
                issues.append({
                    "line": i,
                    "severity": "critical",
                    "category": "security",
                    "message": "Sử dụng eval() - nguy hiểm cho bảo mật",
                    "suggestion": "Sử dụng ast.literal_eval() hoặc alternative an toàn"
                })

            # exec() usage
            if "exec(" in line:
                issues.append({
                    "line": i,
                    "severity": "critical",
                    "category": "security",
                    "message": "Sử dụng exec() - nguy hiểm cho bảo mật",
                    "suggestion": "Tránh sử dụng exec() nếu có thể"
                })

            # SQL injection risk
            if "execute(" in line and ("%s" in line or "+" in line or "format(" in line):
                issues.append({
                    "line": i,
                    "severity": "critical",
                    "category": "security",
                    "message": "Nguy cơ SQL injection",
                    "suggestion": "Sử dụng parameterized queries"
                })

            # Hardcoded password/secret
            if re.search(r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']', line, re.IGNORECASE):
                issues.append({
                    "line": i,
                    "severity": "critical",
                    "category": "security",
                    "message": "Hardcoded password/secret",
                    "suggestion": "Sử dụng environment variables hoặc config files"
                })

    # Check performance
    if check_performance:
        for i, line in enumerate(lines, 1):
            # List comprehension vs loop
            if re.search(r'for\s+\w+\s+in\s+range\(len\(', line):
                issues.append({
                    "line": i,
                    "severity": "info",
                    "category": "performance",
                    "message": "Sử dụng range(len()) thay vì enumerate()",
                    "suggestion": "Sử dụng: for i, item in enumerate(items)"
                })

            # String concatenation in loop
            if re.search(r'\+\=.*["\']', line) and i > 1:
                issues.append({
                    "line": i,
                    "severity": "warning",
                    "category": "performance",
                    "message": "String concatenation trong loop",
                    "suggestion": "Sử dụng list và join() thay vì += cho strings"
                })

    # Check best practices
    if check_best_practices:
        # Check for bare except
        for i, line in enumerate(lines, 1):
            if re.search(r'except\s*:', line):
                issues.append({
                    "line": i,
                    "severity": "warning",
                    "category": "best_practice",
                    "message": "Bare except clause",
                    "suggestion": "Specify exception type: except Exception:"
                })

        # Check for mutable default arguments
        for i, line in enumerate(lines, 1):
            if re.search(r'def\s+\w+\(.*=\s*[\[\{]', line):
                issues.append({
                    "line": i,
                    "severity": "critical",
                    "category": "best_practice",
                    "message": "Mutable default argument",
                    "suggestion": "Sử dụng None và khởi tạo trong function body"
                })

    return issues, suggestions


def _review_java_code(content: str, check_style: bool, check_security: bool,
                      check_performance: bool, check_best_practices: bool) -> Tuple[List[Dict], List[Dict]]:
    """Review Java code"""
    issues = []
    suggestions = []

    lines = content.split('\n')

    if check_security:
        for i, line in enumerate(lines, 1):
            if "System.out.println" in line and "password" in line.lower():
                issues.append({
                    "line": i,
                    "severity": "critical",
                    "category": "security",
                    "message": "Có thể log sensitive information",
                    "suggestion": "Tránh log passwords hoặc sensitive data"
                })

    if check_best_practices:
        for i, line in enumerate(lines, 1):
            if "catch (Exception e)" in line and "e.printStackTrace()" in content[content.find(line):content.find(line)+200]:
                issues.append({
                    "line": i,
                    "severity": "warning",
                    "category": "best_practice",
                    "message": "Empty catch block hoặc chỉ printStackTrace",
                    "suggestion": "Xử lý exception properly hoặc log nó"
                })

    return issues, suggestions


def _review_javascript_code(content: str, check_style: bool, check_security: bool,
                            check_performance: bool, check_best_practices: bool) -> Tuple[List[Dict], List[Dict]]:
    """Review JavaScript/TypeScript code"""
    issues = []
    suggestions = []

    lines = content.split('\n')

    if check_security:
        for i, line in enumerate(lines, 1):
            if "eval(" in line or "innerHTML" in line:
                issues.append({
                    "line": i,
                    "severity": "critical",
                    "category": "security",
                    "message": "Sử dụng eval() hoặc innerHTML - XSS risk",
                    "suggestion": "Sử dụng textContent hoặc sanitize input"
                })

    return issues, suggestions


def _review_generic_code(content: str, check_style: bool, check_security: bool) -> Tuple[List[Dict], List[Dict]]:
    """Generic code review"""
    issues = []
    suggestions = []

    lines = content.split('\n')

    if check_style:
        for i, line in enumerate(lines, 1):
            if len(line) > 150:
                issues.append({
                    "line": i,
                    "severity": "info",
                    "category": "style",
                    "message": "Dòng quá dài (>150 ký tự)",
                    "suggestion": "Chia nhỏ dòng để dễ đọc"
                })

    if check_security:
        for i, line in enumerate(lines, 1):
            if "password" in line.lower() and "=" in line:
                issues.append({
                    "line": i,
                    "severity": "warning",
                    "category": "security",
                    "message": "Có thể chứa hardcoded password",
                    "suggestion": "Sử dụng environment variables"
                })

    return issues, suggestions


def _calculate_quality_score(issues: List[Dict], suggestions: List[Dict]) -> int:
    """Tính điểm chất lượng code (0-100)"""
    base_score = 100

    # Trừ điểm theo severity
    for issue in issues:
        if issue["severity"] == "critical":
            base_score -= 10
        elif issue["severity"] == "warning":
            base_score -= 5
        elif issue["severity"] == "info":
            base_score -= 2

    # Giới hạn 0-100
    return max(0, min(100, base_score))


# =============================================================================
# TOOL: KIỂM SOÁT LỖI
# =============================================================================

@handle_exception
def error_control(file_path: str, language: str = "auto") -> Dict[str, Any]:
    """
    Phân tích và kiểm soát lỗi trong code

    Args:
        file_path: Đường dẫn file
        language: Ngôn ngữ lập trình

    Returns:
        Dict chứa phân tích lỗi và đề xuất fix

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Kiểm soát lỗi",
        file_path=file_path,
        language=language
    )

    try:
        content = read_file_safe(file_path)
        path = Path(file_path)

        if language == "auto":
            language = _detect_language(path)

        potential_errors = []
        fixes = []

        if language == "python":
            potential_errors, fixes = _analyze_python_errors(content)
        elif language == "java":
            potential_errors, fixes = _analyze_java_errors(content)
        else:
            potential_errors, fixes = _analyze_generic_errors(content)

        result = {
            "success": True,
            "file_path": file_path,
            "language": language,
            "total_potential_errors": len(potential_errors),
            "potential_errors": potential_errors,
            "suggested_fixes": fixes,
            "can_auto_fix": len([f for f in fixes if f.get("auto_fixable", False)])
        }

        logger.info(
            "Kiểm soát lỗi thành công",
            file_path=file_path,
            total_errors=len(potential_errors)
        )

        return result

    except Exception as e:
        logger.error("Lỗi kiểm soát lỗi", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể kiểm soát lỗi: {str(e)}",
            code="ERROR_CONTROL_ERROR",
            details={"file_path": file_path}
        )


def _analyze_python_errors(content: str) -> Tuple[List[Dict], List[Dict]]:
    """Phân tích lỗi tiềm ẩn trong Python code"""
    errors = []
    fixes = []

    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # Unused imports
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            errors.append({
                "line": i,
                "type": "unused_import",
                "severity": "warning",
                "message": "Import có thể không được sử dụng",
                "fix": f"Xóa dòng {i} nếu không sử dụng"
            })

        # Division by zero risk
        if "/" in line and "0" in line:
            errors.append({
                "line": i,
                "type": "division_by_zero",
                "severity": "warning",
                "message": "Nguy cơ chia cho zero",
                "fix": "Thêm kiểm tra divisor != 0"
            })

        # Possible None comparison
        if "== None" in line or "!= None" in line:
            errors.append({
                "line": i,
                "type": "none_comparison",
                "severity": "info",
                "message": "So sánh với None không dùng is",
                "fix": f"Sử dụng 'is None' hoặc 'is not None' thay vì '== None'"
            })

    return errors, fixes


def _analyze_java_errors(content: str) -> Tuple[List[Dict], List[Dict]]:
    """Phân tích lỗi tiềm ẩn trong Java code"""
    errors = []
    fixes = []

    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        if "== null" in line:
            errors.append({
                "line": i,
                "type": "null_comparison",
                "severity": "info",
                "message": "So sánh với null",
                "fix": "Sử dụng Objects.nonNull() hoặc Optional"
            })

    return errors, fixes


def _analyze_generic_errors(content: str) -> Tuple[List[Dict], List[Dict]]:
    """Phân tích lỗi tiềm ẩn generic"""
    errors = []
    fixes = []

    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        if "TODO" in line or "FIXME" in line:
            errors.append({
                "line": i,
                "type": "todo_found",
                "severity": "info",
                "message": f"Tìm thấy {line.strip()}",
                "fix": "Hoàn thành TODO/FIXME"
            })

    return errors, fixes


# =============================================================================
# TOOL: FIX CODE AN TOÀN
# =============================================================================

@handle_exception
def fix_code_safely(
    file_path: str,
    fix_type: str,
    auto_approve: bool = False,
    create_backup: bool = True
) -> Dict[str, Any]:
    """
    Fix code một cách an toàn, không làm hỏng code hiện tại

    Args:
        file_path: Đường dẫn file
        fix_type: Loại fix: remove_unused_imports, fix_indentation, add_error_handling, remove_todos
        auto_approve: Tự động approve các fix (False để chỉ suggest)
        create_backup: Tạo backup file trước khi fix

    Returns:
        Dict chứa kết quả fix

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
        "Fix code an toàn",
        file_path=file_path,
        fix_type=fix_type,
        auto_approve=auto_approve,
        create_backup=create_backup
    )

    try:
        content = read_file_safe(file_path)
        original_content = content

        # Tạo backup
        if create_backup:
            backup_path = f"{file_path}.backup"
            write_file_safe(backup_path, original_content)
            logger.info("Đã tạo backup", backup_path=backup_path)

        # Thực hiện fix theo type
        if fix_type == "remove_unused_imports":
            new_content, fixes_applied = _remove_unused_imports(content)
        elif fix_type == "fix_indentation":
            new_content, fixes_applied = _fix_indentation(content)
        elif fix_type == "add_error_handling":
            new_content, fixes_applied = _add_error_handling(content)
        elif fix_type == "remove_todos":
            new_content, fixes_applied = _remove_todos(content)
        else:
            raise MCPError(
                message=f"Loại fix không hỗ trợ: {fix_type}",
                code="UNSUPPORTED_FIX_TYPE"
            )

        # Kiểm tra xem có thay đổi không
        if new_content == original_content:
            return {
                "success": True,
                "file_path": file_path,
                "fix_type": fix_type,
                "fixes_applied": 0,
                "message": "Không cần fix",
                "changes": []
            }

        # Nếu không auto_approve, chỉ trả về suggestions
        if not auto_approve:
            return {
                "success": True,
                "file_path": file_path,
                "fix_type": fix_type,
                "fixes_applied": 0,
                "message": f"Có {fixes_applied} fixes có thể áp dụng. Set auto_approve=true để áp dụng.",
                "pending_fixes": fixes_applied,
                "preview": new_content[:500]
            }

        # Áp dụng fixes
        write_file_safe(file_path, new_content)

        result = {
            "success": True,
            "file_path": file_path,
            "fix_type": fix_type,
            "fixes_applied": fixes_applied,
            "message": f"Đã áp dụng {fixes_applied} fixes thành công",
            "backup_created": create_backup,
            "changes_summary": f"Fixed {fixes_applied} issues"
        }

        logger.info(
            "Fix code thành công",
            file_path=file_path,
            fix_type=fix_type,
            fixes_applied=fixes_applied
        )

        return result

    except Exception as e:
        logger.error("Lỗi fix code", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể fix code: {str(e)}",
            code="CODE_FIX_ERROR",
            details={"file_path": file_path, "fix_type": fix_type}
        )


def _remove_unused_imports(content: str) -> Tuple[str, int]:
    """Loại bỏ imports không sử dụng (Python)"""
    lines = content.split('\n')
    new_lines = []
    fixes = 0

    # Simple heuristic: tìm imports không được sử dụng
    imports = []
    for line in lines:
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            imports.append(line)

    # Loại bỏ imports có comment "# noqa" hoặc "# unused"
    for line in lines:
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            if "# noqa" in line or "# unused" in line.lower():
                new_lines.append(line)
                continue

            # Check if import is used (simple check)
            module_name = line.split()[1].split(".")[0] if len(line.split()) > 1 else ""
            rest_of_code = "\n".join(lines[lines.index(line) + 1:])

            if module_name and module_name not in rest_of_code:
                fixes += 1
                continue  # Skip this import

        new_lines.append(line)

    return "\n".join(new_lines), fixes


def _fix_indentation(content: str) -> Tuple[str, int]:
    """Fix indentation (basic)"""
    lines = content.split('\n')
    new_lines = []
    fixes = 0

    for line in lines:
        # Fix tabs to spaces
        if "\t" in line:
            line = line.replace("\t", "    ")
            fixes += 1
        new_lines.append(line)

    return "\n".join(new_lines), fixes


def _add_error_handling(content: str) -> Tuple[str, int]:
    """Thêm error handling cơ bản"""
    # Placeholder - complex implementation would require AST parsing
    return content, 0


def _remove_todos(content: str) -> Tuple[str, int]:
    """Loại bỏ TODO comments"""
    lines = content.split('\n')
    new_lines = []
    fixes = 0

    for line in lines:
        if "TODO" in line or "FIXME" in line:
            fixes += 1
            continue
        new_lines.append(line)

    return "\n".join(new_lines), fixes


# =============================================================================
# TOOL: THÊM DEBUG LOGS
# =============================================================================

@handle_exception
def add_debug_logs(
    file_path: str,
    language: str = "auto",
    log_level: str = "DEBUG",
    log_points: List[str] = None
) -> Dict[str, Any]:
    """
    Thêm debug logs chiến lược vào code

    Args:
        file_path: Đường dẫn file
        language: Ngôn ngữ lập trình
        log_level: Mức log: DEBUG, INFO, WARNING, ERROR
        log_points: List các điểm cần thêm log (function_start, function_end, loop, condition, error)

    Returns:
        Dict chứa code đã thêm debug logs

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
        "Thêm debug logs",
        file_path=file_path,
        language=language,
        log_level=log_level
    )

    try:
        content = read_file_safe(file_path)
        path = Path(file_path)

        if language == "auto":
            language = _detect_language(path)

        if log_points is None:
            log_points = ["function_start", "function_end", "condition", "error"]

        # Thêm logs theo ngôn ngữ
        if language == "python":
            new_content, logs_added = _add_python_debug_logs(content, log_level, log_points)
        elif language == "java":
            new_content, logs_added = _add_java_debug_logs(content, log_level, log_points)
        else:
            raise MCPError(
                message=f"Chưa hỗ trợ thêm debug logs cho ngôn ngữ: {language}",
                code="UNSUPPORTED_LANGUAGE"
            )

        # Ghi file
        write_file_safe(file_path, new_content)

        result = {
            "success": True,
            "file_path": file_path,
            "language": language,
            "log_level": log_level,
            "logs_added": logs_added,
            "message": f"Đã thêm {logs_added} debug logs"
        }

        logger.info(
            "Thêm debug logs thành công",
            file_path=file_path,
            logs_added=logs_added
        )

        return result

    except Exception as e:
        logger.error("Lỗi thêm debug logs", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể thêm debug logs: {str(e)}",
            code="DEBUG_LOG_ERROR",
            details={"file_path": file_path}
        )


def _add_python_debug_logs(content: str, log_level: str, log_points: List[str]) -> Tuple[str, int]:
    """Thêm debug logs vào Python code"""
    lines = content.split('\n')
    new_lines = []
    logs_added = 0

    # Check if logging is imported
    has_logging_import = any("import logging" in line for line in lines)

    if not has_logging_import and "function_start" in log_points:
        new_lines.append("import logging")
        new_lines.append("logger = logging.getLogger(__name__)")
        new_lines.append("")
        logs_added += 1

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Add log at function start
        if "function_start" in log_points and line.strip().startswith("def "):
            func_name = line.strip().split("(")[0].replace("def ", "")
            indent = len(line) - len(line.lstrip())
            log_stmt = f"{' ' * indent}    logger.{log_level.lower()}(\"Gọi hàm: {func_name}\")"
            new_lines.append(log_stmt)
            logs_added += 1

        # Add log at conditions
        if "condition" in log_points and "if " in line and ":" in line:
            indent = len(line) - len(line.lstrip())
            log_stmt = f"{' ' * indent}    logger.{log_level.lower()}(\"Điều kiện đúng: {{}}\")"
            new_lines.append(log_stmt)
            logs_added += 1

    return "\n".join(new_lines), logs_added


def _add_java_debug_logs(content: str, log_level: str, log_points: List[str]) -> Tuple[str, int]:
    """Thêm debug logs vào Java code"""
    # Placeholder
    return content, 0


# =============================================================================
# TOOL: DỌN DẸP CODE
# =============================================================================

@handle_exception
def cleanup_code(
    file_path: str,
    language: str = "auto",
    remove_trailing_whitespace: bool = True,
    fix_indentation: bool = True,
    remove_unused_imports: bool = True,
    sort_imports: bool = True
) -> Dict[str, Any]:
    """
    Dọn dẹp và refactor code

    Args:
        file_path: Đường dẫn file
        language: Ngôn ngữ lập trình
        remove_trailing_whitespace: Xóa khoảng trắng thừa
        fix_indentation: Fix indentation
        remove_unused_imports: Loại bỏ imports không dùng
        sort_imports: Sắp xếp imports

    Returns:
        Dict chứa kết quả cleanup

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
        "Dọn dẹp code",
        file_path=file_path,
        language=language
    )

    try:
        content = read_file_safe(file_path)
        original_content = content
        changes = []

        # Remove trailing whitespace
        if remove_trailing_whitespace:
            lines = content.split('\n')
            new_lines = [line.rstrip() for line in lines]
            content = '\n'.join(new_lines)
            if content != original_content:
                changes.append("Đã xóa trailing whitespace")

        # Fix indentation
        if fix_indentation:
            # Basic: convert tabs to spaces
            if "\t" in content:
                content = content.replace("\t", "    ")
                changes.append("Đã chuyển tabs thành spaces")

        # Remove unused imports
        if remove_unused_imports:
            content, removed = _remove_unused_imports(content)
            if removed > 0:
                changes.append(f"Đã loại bỏ {removed} unused imports")

        # Sort imports (Python only)
        if sort_imports:
            content, sorted_count = _sort_imports(content)
            if sorted_count > 0:
                changes.append(f"Đã sắp xếp {sorted_count} imports")

        # Ghi file nếu có thay đổi
        if content != original_content:
            write_file_safe(file_path, content)

        result = {
            "success": True,
            "file_path": file_path,
            "changes_applied": len(changes),
            "changes": changes,
            "message": f"Đã dọn dẹp code: {len(changes)} thay đổi"
        }

        logger.info(
            "Dọn dẹp code thành công",
            file_path=file_path,
            changes=len(changes)
        )

        return result

    except Exception as e:
        logger.error("Lỗi dọn dẹp code", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể dọn dẹp code: {str(e)}",
            code="CODE_CLEANUP_ERROR",
            details={"file_path": file_path}
        )


def _sort_imports(content: str) -> Tuple[str, int]:
    """Sắp xếp imports (Python)"""
    lines = content.split('\n')
    import_lines = []
    other_lines = []

    for line in lines:
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            import_lines.append(line)
        else:
            other_lines.append(line)

    if import_lines:
        # Sort imports
        import_lines.sort()
        # Group: stdlib first, then third-party, then local
        content = "\n".join(import_lines + [""] + other_lines)
        return content, len(import_lines)

    return content, 0


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "review_code",
    "error_control",
    "fix_code_safely",
    "add_debug_logs",
    "cleanup_code"
]