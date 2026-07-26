"""
MCP Programming Support Server - Server chính
MCP Server hỗ trợ lập trình với đầy đủ công cụ phát triển
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Thêm thư mục gốc vào path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from config import get_settings, reload_settings
from utils import get_logger, setup_logging, MCPError

# Thiết lập logging
logger = setup_logging()

# Lấy settings
settings = get_settings()

# Tạo FastMCP server
mcp = FastMCP(
    name="programming-support-server",
    version="1.0.0",
    description="MCP Server hỗ trợ lập trình, phát triển Minecraft Paper plugin và thiết kế game tu tiên"
)

# Log khởi động
logger.info(
    "Khởi động MCP Programming Support Server",
    version="1.0.0",
    workspace=str(settings.workspace),
    log_level=settings.log_level
)


# =============================================================================
# FILESYSTEM TOOLS
# =============================================================================

@mcp.tool()
def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Đọc nội dung file từ workspace

    Args:
        file_path: Đường dẫn file (tương đối hoặc tuyệt đối trong workspace)
        encoding: Encoding của file (mặc định: utf-8)

    Returns:
        Dict chứa nội dung file và metadata
    """
    from tools.filesystem import read_file as fs_read_file
    return fs_read_file(file_path, encoding)


@mcp.tool()
def write_file(file_path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Ghi nội dung vào file

    Args:
        file_path: Đường dẫn file (tương đối hoặc tuyệt đối trong workspace)
        content: Nội dung cần ghi
        encoding: Encoding của file (mặc định: utf-8)

    Returns:
        Dict chứa thông tin file đã ghi
    """
    from tools.filesystem import write_file as fs_write_file
    return fs_write_file(file_path, content, encoding)


@mcp.tool()
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
    """
    from tools.filesystem import replace_text as fs_replace_text
    return fs_replace_text(file_path, old_text, new_text, encoding, replace_all)


@mcp.tool()
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
    """
    from tools.filesystem import list_directory as fs_list_directory
    return fs_list_directory(directory_path, recursive, show_hidden, file_pattern)


@mcp.tool()
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
    """
    from tools.filesystem import search_files as fs_search_files
    return fs_search_files(directory_path, pattern, recursive, case_sensitive)


@mcp.tool()
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
    """
    from tools.filesystem import search_text as fs_search_text
    return fs_search_text(directory_path, search_text, file_pattern, case_sensitive, regex, max_results)


# =============================================================================
# GITHUB TOOLS
# =============================================================================

@mcp.tool()
def github_search(
    query: str,
    search_type: str = "repositories",
    max_results: int = 10,
    language: Optional[str] = None,
    sort: str = "stars",
    order: str = "desc"
) -> Dict[str, Any]:
    """
    Tìm kiếm trên GitHub

    Args:
        query: Từ khóa tìm kiếm
        search_type: Loại tìm kiếm: repositories, code, issues, users
        max_results: Số kết quả tối đa (1-100)
        language: Lọc theo ngôn ngữ lập trình (ví dụ: "python", "java")
        sort: Sắp xếp theo: stars, forks, updated
        order: Thứ tự: desc, asc

    Returns:
        Dict chứa kết quả tìm kiếm
    """
    from tools.github import github_search
    return github_search(query, search_type, max_results, language, sort, order)


@mcp.tool()
def get_repository_info(owner: str, repo: str) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết về một repository

    Args:
        owner: Chủ sở hữu repository (username hoặc organization)
        repo: Tên repository

    Returns:
        Dict chứa thông tin repository
    """
    from tools.github import get_repository_info
    return get_repository_info(owner, repo)


@mcp.tool()
def get_file_from_github(owner: str, repo: str, file_path: str, branch: str = "main") -> Dict[str, Any]:
    """
    Lấy nội dung file từ GitHub repository

    Args:
        owner: Chủ sở hữu repository
        repo: Tên repository
        file_path: Đường dẫn file trong repository
        branch: Tên branch (mặc định: main)

    Returns:
        Dict chứa nội dung file
    """
    from tools.github import get_file_from_github
    return get_file_from_github(owner, repo, file_path, branch)


@mcp.tool()
def search_code_in_repo(
    owner: str,
    repo: str,
    query: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    Tìm kiếm code trong một repository cụ thể

    Args:
        owner: Chủ sở hữu repository
        repo: Tên repository
        query: Từ khóa tìm kiếm
        max_results: Số kết quả tối đa

    Returns:
        Dict chứa kết quả tìm kiếm
    """
    from tools.github import search_code_in_repo
    return search_code_in_repo(owner, repo, query, max_results)


# =============================================================================
# SEARCH TOOLS
# =============================================================================

@mcp.tool()
def fetch_url(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fetch nội dung từ URL

    Args:
        url: URL cần fetch
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Custom headers
        data: Request body data (cho POST/PUT)
        timeout: Timeout tùy chỉnh (giây)

    Returns:
        Dict chứa nội dung response
    """
    from tools.search import fetch_url
    return fetch_url(url, method, headers, data, timeout)


@mcp.tool()
def web_search(query: str, max_results: int = 10, safe_search: bool = True) -> Dict[str, Any]:
    """
    Tìm kiếm web sử dụng DuckDuckGo (không cần API key)

    Args:
        query: Từ khóa tìm kiếm
        max_results: Số kết quả tối đa
        safe_search: Bật safe search

    Returns:
        Dict chứa kết quả tìm kiếm
    """
    from tools.search import web_search
    return web_search(query, max_results, safe_search)


@mcp.tool()
def search_documentation(query: str, source: str = "auto", max_results: int = 5) -> Dict[str, Any]:
    """
    Tìm kiếm trong documentation của các framework/ngôn ngữ phổ biến

    Args:
        query: Từ khóa tìm kiếm
        source: Nguồn documentation: auto, python, java, javascript, minecraft, paper
        max_results: Số kết quả tối đa

    Returns:
        Dict chứa kết quả tìm kiếm
    """
    from tools.search import search_documentation
    return search_documentation(query, source, max_results)


@mcp.tool()
def extract_content_from_url(url: str, extract_type: str = "text") -> Dict[str, Any]:
    """
    Trích xuất nội dung có cấu trúc từ URL

    Args:
        url: URL cần trích xuất
        extract_type: Loại nội dung: text, links, images, tables, all

    Returns:
        Dict chứa nội dung đã trích xuất
    """
    from tools.search import extract_content_from_url
    return extract_content_from_url(url, extract_type)


# =============================================================================
# REVIEW TOOLS
# =============================================================================

@mcp.tool()
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
    """
    from tools.review import review_code
    return review_code(file_path, language, check_style, check_security, check_performance, check_best_practices)


@mcp.tool()
def error_control(file_path: str, language: str = "auto") -> Dict[str, Any]:
    """
    Phân tích và kiểm soát lỗi trong code

    Args:
        file_path: Đường dẫn file
        language: Ngôn ngữ lập trình

    Returns:
        Dict chứa phân tích lỗi và đề xuất fix
    """
    from tools.review import error_control
    return error_control(file_path, language)


@mcp.tool()
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
    """
    from tools.review import fix_code_safely
    return fix_code_safely(file_path, fix_type, auto_approve, create_backup)


@mcp.tool()
def add_debug_logs(
    file_path: str,
    language: str = "auto",
    log_level: str = "DEBUG",
    log_points: Optional[List[str]] = None
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
    """
    from tools.review import add_debug_logs
    return add_debug_logs(file_path, language, log_level, log_points)


@mcp.tool()
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
    """
    from tools.review import cleanup_code
    return cleanup_code(file_path, language, remove_trailing_whitespace, fix_indentation, remove_unused_imports, sort_imports)


# =============================================================================
# SHELL TOOLS
# =============================================================================

@mcp.tool()
def shell_execute(
    command: str,
    working_directory: Optional[str] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    shell: bool = False
) -> Dict[str, Any]:
    """
    Thực thi shell command an toàn

    Args:
        command: Command cần thực thi
        working_directory: Thư mục làm việc (mặc định: workspace)
        timeout: Timeout (giây)
        capture_output: Capture stdout/stderr
        shell: Sử dụng shell=True (False an toàn hơn)

    Returns:
        Dict chứa kết quả thực thi
    """
    from tools.shell import shell_execute
    return shell_execute(command, working_directory, timeout, capture_output, shell)


@mcp.tool()
def run_command_safe(
    command: str,
    args: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Chạy command an toàn với list of args (không dùng shell)

    Args:
        command: Command name
        args: List các arguments
        cwd: Working directory
        env: Environment variables

    Returns:
        Dict chứa kết quả
    """
    from tools.shell import run_command_safe
    return run_command_safe(command, args, cwd, env)


@mcp.tool()
def list_allowed_commands() -> Dict[str, Any]:
    """
    Liệt kê các shell commands được phép chạy

    Returns:
        Dict chứa danh sách commands được phép
    """
    from tools.shell import list_allowed_commands
    return list_allowed_commands()


# =============================================================================
# DOCKER TOOLS
# =============================================================================

@mcp.tool()
def generate_dockerfile(
    project_type: str,
    project_name: str,
    base_image: Optional[str] = None,
    port: int = 8080,
    working_dir: str = "/app",
    include_healthcheck: bool = True,
    include_non_root: bool = True,
    optimize_layers: bool = True,
    extra_packages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Tạo Dockerfile tối ưu cho dự án

    Args:
        project_type: Loại dự án: python, node, java, go, rust, generic
        project_name: Tên dự án
        base_image: Base image tùy chỉnh (nếu None sẽ dùng mặc định theo project_type)
        port: Port ứng dụng chạy
        working_dir: Thư mục làm việc trong container
        include_healthcheck: Thêm HEALTHCHECK
        include_non_root: Chạy với non-root user
        optimize_layers: Tối ưu layer caching
        extra_packages: List các packages cần cài thêm

    Returns:
        Dict chứa nội dung Dockerfile
    """
    from tools.docker_tools import generate_dockerfile
    return generate_dockerfile(project_type, project_name, base_image, port, working_dir, include_healthcheck, include_non_root, optimize_layers, extra_packages)


@mcp.tool()
def generate_docker_compose(
    project_name: str,
    services: List[Dict[str, Any]],
    volumes: Optional[List[Dict[str, str]]] = None,
    networks: Optional[List[str]] = None,
    restart_policy: str = "unless-stopped"
) -> Dict[str, Any]:
    """
    Tạo file docker-compose.yml

    Args:
        project_name: Tên dự án
        services: List các services
        volumes: List các volumes
        networks: List các networks
        restart_policy: Restart policy

    Returns:
        Dict chứa nội dung docker-compose.yml
    """
    from tools.docker_tools import generate_docker_compose
    return generate_docker_compose(project_name, services, volumes, networks, restart_policy)


@mcp.tool()
def analyze_dockerfile(file_path: str) -> Dict[str, Any]:
    """
    Phân tích Dockerfile và đưa ra đề xuất cải thiện

    Args:
        file_path: Đường dẫn Dockerfile

    Returns:
        Dict chứa phân tích và đề xuất
    """
    from tools.docker_tools import analyze_dockerfile
    return analyze_dockerfile(file_path)


@mcp.tool()
def generate_dockerignore(project_type: str = "generic") -> Dict[str, Any]:
    """
    Tạo file .dockerignore tối ưu

    Args:
        project_type: Loại dự án

    Returns:
        Dict chứa nội dung .dockerignore
    """
    from tools.docker_tools import generate_dockerignore
    return generate_dockerignore(project_type)


# =============================================================================
# DOCUMENTATION TOOLS
# =============================================================================

@mcp.tool()
def read_guide(guide_name: str, guide_dir: str = "guides") -> Dict[str, Any]:
    """
    Đọc file hướng dẫn

    Args:
        guide_name: Tên file hướng dẫn (ví dụ: "minecraft-plugin-guide.md")
        guide_dir: Thư mục chứa hướng dẫn

    Returns:
        Dict chứa nội dung hướng dẫn
    """
    from tools.docs import read_guide
    return read_guide(guide_name, guide_dir)


@mcp.tool()
def update_guide(
    guide_name: str,
    updates: Dict[str, Any],
    guide_dir: str = "guides",
    create_if_not_exists: bool = True,
    append_section: bool = False
) -> Dict[str, Any]:
    """
    Cập nhật file hướng dẫn với nội dung mới

    Args:
        guide_name: Tên file hướng dẫn
        updates: Dict chứa các cập nhật
        guide_dir: Thư mục chứa hướng dẫn
        create_if_not_exists: Tạo file mới nếu chưa tồn tại
        append_section: Thêm section mới vào cuối

    Returns:
        Dict chứa kết quả cập nhật
    """
    from tools.docs import update_guide
    return update_guide(guide_name, updates, guide_dir, create_if_not_exists, append_section)


@mcp.tool()
def create_guide(
    guide_name: str,
    title: str,
    content: str,
    guide_dir: str = "guides",
    category: str = "general",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Tạo file hướng dẫn mới

    Args:
        guide_name: Tên file (ví dụ: "minecraft-setup.md")
        title: Tiêu đề hướng dẫn
        content: Nội dung hướng dẫn
        guide_dir: Thư mục lưu
        category: Danh mục (general, minecraft, xianxia, etc.)
        tags: List tags

    Returns:
        Dict chứa thông tin guide đã tạo
    """
    from tools.docs import create_guide
    return create_guide(guide_name, title, content, guide_dir, category, tags)


@mcp.tool()
def list_guides(guide_dir: str = "guides", category: Optional[str] = None) -> Dict[str, Any]:
    """
    Liệt kê tất cả hướng dẫn

    Args:
        guide_dir: Thư mục chứa hướng dẫn
        category: Lọc theo danh mục

    Returns:
        Dict chứa danh sách hướng dẫn
    """
    from tools.docs import list_guides
    return list_guides(guide_dir, category)


@mcp.tool()
def extract_lessons(guide_name: str, guide_dir: str = "guides") -> Dict[str, Any]:
    """
    Trích xuất bài học kinh nghiệm từ hướng dẫn

    Args:
        guide_name: Tên file hướng dẫn
        guide_dir: Thư mục chứa hướng dẫn

    Returns:
        Dict chứa các bài học kinh nghiệm
    """
    from tools.docs import extract_lessons
    return extract_lessons(guide_name, guide_dir)


@mcp.tool()
def create_guide_template(
    template_type: str,
    title: str,
    guide_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo template hướng dẫn theo loại

    Args:
        template_type: Loại template: minecraft-plugin, xianxia-system, general
        title: Tiêu đề
        guide_name: Tên file (nếu None sẽ tự generate)

    Returns:
        Dict chứa template
    """
    from tools.docs import create_guide_template
    return create_guide_template(template_type, title, guide_name)


# =============================================================================
# MINECRAFT TOOLS
# =============================================================================

@mcp.tool()
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
    """
    from tools.minecraft.paper_reference import reference_paper_source
    return reference_paper_source(query, paper_path, search_type, max_results)


@mcp.tool()
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
    """
    from tools.minecraft.paper_reference import find_paper_api_usage
    return find_paper_api_usage(api_class, paper_path, max_examples)


@mcp.tool()
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
    """
    from tools.minecraft.paper_reference import extract_paper_patterns
    return extract_paper_patterns(pattern_type, paper_path, max_patterns)


@mcp.tool()
def create_plugin_structure(
    plugin_name: str,
    package_name: str,
    author: str,
    version: str = "1.0.0",
    main_class: Optional[str] = None,
    description: str = "",
    website: str = "",
    depends: Optional[List[str]] = None,
    soft_depends: Optional[List[str]] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo cấu trúc dự án plugin Minecraft

    Args:
        plugin_name: Tên plugin (ví dụ: "CultivationPlugin")
        package_name: Package name (ví dụ: "com.example.cultivation")
        author: Tác giả
        version: Phiên bản
        main_class: Class chính (nếu None sẽ tự generate)
        description: Mô tả plugin
        website: Website
        depends: List plugins phụ thuộc (hard dependencies)
        soft_depends: List plugins phụ thuộc (soft dependencies)
        output_dir: Thư mục output (nếu None dùng workspace)

    Returns:
        Dict chứa thông tin cấu trúc đã tạo
    """
    from tools.minecraft.plugin_builder import create_plugin_structure
    return create_plugin_structure(plugin_name, package_name, author, version, main_class, description, website, depends, soft_depends, output_dir)


@mcp.tool()
def generate_plugin_yml(
    plugin_name: str,
    main_class: str,
    version: str = "1.0.0",
    author: str = "",
    description: str = "",
    api_version: str = "1.20",
    depends: Optional[List[str]] = None,
    soft_depends: Optional[List[str]] = None,
    commands: Optional[List[Dict[str, Any]]] = None,
    permissions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Tạo file plugin.yml

    Args:
        plugin_name: Tên plugin
        main_class: Class chính
        version: Phiên bản
        author: Tác giả
        description: Mô tả
        api_version: Phiên bản API
        depends: List hard dependencies
        soft_depends: List soft dependencies
        commands: List commands
        permissions: List permissions

    Returns:
        Dict chứa nội dung plugin.yml
    """
    from tools.minecraft.plugin_builder import generate_plugin_yml
    return generate_plugin_yml(plugin_name, main_class, version, author, description, api_version, depends, soft_depends, commands, permissions)


@mcp.tool()
def implement_listener(
    listener_name: str,
    package_name: str,
    events: List[str],
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo event listener class

    Args:
        listener_name: Tên listener (ví dụ: "PlayerListener")
        package_name: Package name
        events: List events cần handle
        output_dir: Thư mục output

    Returns:
        Dict chứa nội dung listener class
    """
    from tools.minecraft.plugin_builder import implement_listener
    return implement_listener(listener_name, package_name, events, output_dir)


@mcp.tool()
def implement_command(
    command_name: str,
    package_name: str,
    description: str = "",
    usage: str = "",
    permission: str = "",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo command class

    Args:
        command_name: Tên command (ví dụ: "cultivation")
        package_name: Package name
        description: Mô tả command
        usage: Cách sử dụng
        permission: Permission required
        output_dir: Thư mục output

    Returns:
        Dict chứa nội dung command class
    """
    from tools.minecraft.plugin_builder import implement_command
    return implement_command(command_name, package_name, description, usage, permission, output_dir)


@mcp.tool()
def generate_config_yml(
    config_name: str,
    sections: List[Dict[str, Any]],
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo file config.yml cho plugin

    Args:
        config_name: Tên config (ví dụ: "config")
        sections: List các sections
        output_dir: Thư mục output

    Returns:
        Dict chứa nội dung config.yml
    """
    from tools.minecraft.plugin_builder import generate_config_yml
    return generate_config_yml(config_name, sections, output_dir)


# =============================================================================
# XIANXIA CULTIVATION TOOLS
# =============================================================================

@mcp.tool()
def search_cultivation_story(
    query: str,
    max_results: int = 5,
    include_summary: bool = True
) -> Dict[str, Any]:
    """
    Tìm kiếm cốt truyện và cơ chế tu tiên từ các tiểu thuyết

    Args:
        query: Từ khóa tìm kiếm (ví dụ: "luyện khí", "đan dược", "pháp bảo")
        max_results: Số kết quả tối đa
        include_summary: Bao gồm tóm tắt

    Returns:
        Dict chứa kết quả tìm kiếm
    """
    from tools.minecraft.xianxia_generator import search_cultivation_story
    return search_cultivation_story(query, max_results, include_summary)


@mcp.tool()
def generate_cultivation_system(
    system_name: str,
    realm_count: int = 9,
    difficulty: str = "medium",
    include_sub_realms: bool = True,
    include_breakthrough_mechanic: bool = True
) -> Dict[str, Any]:
    """
    Tạo hệ thống cảnh giới tu luyện

    Args:
        system_name: Tên hệ thống (ví dụ: "Hệ thống Cảnh Giới Cơ Bản")
        realm_count: Số cảnh giới chính (3-12)
        difficulty: Độ khó: easy, medium, hard, extreme
        include_sub_realms: Bao gồm cảnh giới phụ
        include_breakthrough_mechanic: Bao gồm cơ chế đột phá

    Returns:
        Dict chứa hệ thống cảnh giới
    """
    from tools.minecraft.xianxia_generator import generate_cultivation_system
    return generate_cultivation_system(system_name, realm_count, difficulty, include_sub_realms, include_breakthrough_mechanic)


@mcp.tool()
def generate_item_system(
    system_name: str,
    item_categories: List[str],
    rarity_levels: int = 5,
    include_crafting: bool = True,
    include_upgrade: bool = True
) -> Dict[str, Any]:
    """
    Tạo hệ thống vật phẩm tu tiên

    Args:
        system_name: Tên hệ thống
        item_categories: List categories (ví dụ: ["pháp bảo", "đan dược", "tài liệu"])
        rarity_levels: Số cấp độ hiếm (1-7)
        include_crafting: Bao gồm hệ thống chế tạo
        include_upgrade: Bao gồm hệ thống nâng cấp

    Returns:
        Dict chứa hệ thống vật phẩm
    """
    from tools.minecraft.xianxia_generator import generate_item_system
    return generate_item_system(system_name, item_categories, rarity_levels, include_crafting, include_upgrade)


@mcp.tool()
def generate_skill_system(
    system_name: str,
    skill_types: List[str],
    max_skill_level: int = 10,
    include_skill_tree: bool = True,
    include_cooldowns: bool = True
) -> Dict[str, Any]:
    """
    Tạo hệ thống kỹ năng tu tiên

    Args:
        system_name: Tên hệ thống
        skill_types: List loại kỹ năng (ví dụ: ["công kích", "phòng thủ", "hồi phục", "phụ trợ"])
        max_skill_level: Cấp độ tối đa của kỹ năng
        include_skill_tree: Bao gồm skill tree
        include_cooldowns: Bao gồm cooldown system

    Returns:
        Dict chứa hệ thống kỹ năng
    """
    from tools.minecraft.xianxia_generator import generate_skill_system
    return generate_skill_system(system_name, skill_types, max_skill_level, include_skill_tree, include_cooldowns)


@mcp.tool()
def generate_faction_system(
    system_name: str,
    faction_count: int = 5,
    include_relations: bool = True,
    include_quests: bool = True
) -> Dict[str, Any]:
    """
    Tạo hệ thống môn phái và thế lực

    Args:
        system_name: Tên hệ thống
        faction_count: Số môn phái
        include_relations: Bao gồm hệ thống quan hệ
        include_quests: Bao gồm nhiệm vụ môn phái

    Returns:
        Dict chứa hệ thống môn phái
    """
    from tools.minecraft.xianxia_generator import generate_faction_system
    return generate_faction_system(system_name, faction_count, include_relations, include_quests)


@mcp.tool()
def generate_world_system(
    system_name: str,
    include_spiritual_veins: bool = True,
    include_secret_realms: bool = True,
    include_ancient_ruins: bool = True
) -> Dict[str, Any]:
    """
    Tạo hệ thống thế giới tu tiên

    Args:
        system_name: Tên hệ thống
        include_spiritual_veins: Bao gồm linh mạch
        include_secret_realms: Bao gồm bí cảnh
        include_ancient_ruins: Bao gồm cổ tích

    Returns:
        Dict chứa hệ thống thế giới
    """
    from tools.minecraft.xianxia_generator import generate_world_system
    return generate_world_system(system_name, include_spiritual_veins, include_secret_realms, include_ancient_ruins)


@mcp.tool()
def balance_cultivation(
    realms: List[Dict[str, Any]],
    target_playtime_hours: int = 100,
    progression_curve: str = "exponential"
) -> Dict[str, Any]:
    """
    Cân bằng hệ thống tu luyện

    Args:
        realms: List các cảnh giới
        target_playtime_hours: Thời gian chơi mục tiêu (giờ)
        progression_curve: Đường cong progression: linear, exponential, logarithmic

    Returns:
        Dict chứa đề xuất cân bằng
    """
    from tools.minecraft.xianxia_generator import balance_cultivation
    return balance_cultivation(realms, target_playtime_hours, progression_curve)


@mcp.tool()
def generate_quest_chain(
    chain_name: str,
    quest_count: int = 5,
    difficulty: str = "medium",
    rewards_type: str = "balanced"
) -> Dict[str, Any]:
    """
    Tạo chuỗi nhiệm vụ tu tiên

    Args:
        chain_name: Tên chuỗi nhiệm vụ
        quest_count: Số nhiệm vụ
        difficulty: Độ khó: easy, medium, hard
        rewards_type: Loại phần thưởng: balanced, cultivation, items, story

    Returns:
        Dict chứa chuỗi nhiệm vụ
    """
    from tools.minecraft.xianxia_generator import generate_quest_chain
    return generate_quest_chain(chain_name, quest_count, difficulty, rewards_type)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    try:
        logger.info("Bắt đầu chạy MCP Server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Nhận tín hiệu dừng...")
    except Exception as e:
        logger.error("Lỗi khởi chạy server", error=str(e), exc_info=True)
        sys.exit(1)