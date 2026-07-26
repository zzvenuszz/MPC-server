"""
MCP Programming Support Server - Công cụ GitHub
Tích hợp với GitHub API để tìm kiếm repository, code, issues
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from config import get_settings
from utils import get_logger, MCPError, handle_exception

logger = get_logger()


# =============================================================================
# TOOL: TÌM KIẾM GITHUB
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.github_token:
        raise MCPError(
            message="GitHub token chưa được cấu hình. Vui lòng thêm GITHUB_TOKEN vào .env",
            code="GITHUB_TOKEN_MISSING"
        )

    logger.info(
        "Tìm kiếm GitHub",
        query=query,
        search_type=search_type,
        max_results=max_results,
        language=language
    )

    try:
        import httpx

        # Xây dựng query
        search_query = query
        if language:
            search_query += f" language:{language}"

        # Gọi GitHub Search API
        url = f"https://api.github.com/search/{search_type}"
        params = {
            "q": search_query,
            "per_page": min(max_results, 100),
            "sort": sort if search_type == "repositories" else None,
            "order": order if search_type == "repositories" else None
        }
        # Loại bỏ None values
        params = {k: v for k, v in params.items() if v is not None}

        headers = {
            "Authorization": f"token {settings.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Programming-Support-Server"
        }

        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        # Xử lý kết quả
        items = data.get("items", [])
        total_count = data.get("total_count", 0)

        results = []
        for item in items[:max_results]:
            if search_type == "repositories":
                results.append({
                    "name": item.get("full_name"),
                    "url": item.get("html_url"),
                    "description": item.get("description"),
                    "language": item.get("language"),
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "updated_at": item.get("updated_at"),
                    "created_at": item.get("created_at"),
                    "topics": item.get("topics", []),
                    "license": item.get("license", {}).get("name") if item.get("license") else None
                })
            elif search_type == "code":
                results.append({
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "repository": item.get("repository", {}).get("full_name"),
                    "url": item.get("html_url"),
                    "language": item.get("language"),
                    "score": item.get("score")
                })
            elif search_type == "issues":
                results.append({
                    "title": item.get("title"),
                    "number": item.get("number"),
                    "state": item.get("state"),
                    "url": item.get("html_url"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "user": item.get("user", {}).get("login"),
                    "labels": [label.get("name") for label in item.get("labels", [])]
                })
            elif search_type == "users":
                results.append({
                    "login": item.get("login"),
                    "url": item.get("html_url"),
                    "type": item.get("type"),
                    "score": item.get("score"),
                    "followers": item.get("followers"),
                    "public_repos": item.get("public_repos"),
                    "created_at": item.get("created_at")
                })

        result = {
            "success": True,
            "query": query,
            "search_type": search_type,
            "total_count": total_count,
            "returned_count": len(results),
            "results": results
        }

        logger.info(
            "Tìm kiếm GitHub thành công",
            query=query,
            search_type=search_type,
            total_count=total_count,
            returned_count=len(results)
        )

        return result

    except Exception as e:
        logger.error("Lỗi tìm kiếm GitHub", query=query, error=str(e))
        raise MCPError(
            message=f"Không thể tìm kiếm trên GitHub: {str(e)}",
            code="GITHUB_SEARCH_ERROR",
            details={"query": query, "search_type": search_type}
        )


# =============================================================================
# TOOL: LẤY THÔNG TIN REPOSITORY
# =============================================================================

@handle_exception
def get_repository_info(owner: str, repo: str) -> Dict[str, Any]:
    """
    Lấy thông tin chi tiết về một repository

    Args:
        owner: Chủ sở hữu repository (username hoặc organization)
        repo: Tên repository

    Returns:
        Dict chứa thông tin repository

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.github_token:
        raise MCPError(
            message="GitHub token chưa được cấu hình. Vui lòng thêm GITHUB_TOKEN vào .env",
            code="GITHUB_TOKEN_MISSING"
        )

    logger.info(
        "Lấy thông tin repository",
        owner=owner,
        repo=repo
    )

    try:
        import httpx

        url = f"https://api.github.com/repos/{owner}/{repo}"

        headers = {
            "Authorization": f"token {settings.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Programming-Support-Server"
        }

        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        result = {
            "success": True,
            "name": data.get("full_name"),
            "url": data.get("html_url"),
            "description": data.get("description"),
            "language": data.get("language"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "watchers": data.get("watchers_count"),
            "open_issues": data.get("open_issues_count"),
            "size_kb": data.get("size"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "pushed_at": data.get("pushed_at"),
            "default_branch": data.get("default_branch"),
            "topics": data.get("topics", []),
            "license": data.get("license", {}).get("name") if data.get("license") else None,
            "is_private": data.get("private"),
            "is_fork": data.get("fork"),
            "archived": data.get("archived")
        }

        logger.info(
            "Lấy thông tin repository thành công",
            owner=owner,
            repo=repo,
            stars=data.get("stargazers_count")
        )

        return result

    except Exception as e:
        logger.error("Lỗi lấy thông tin repository", owner=owner, repo=repo, error=str(e))
        raise MCPError(
            message=f"Không thể lấy thông tin repository: {str(e)}",
            code="GITHUB_REPO_ERROR",
            details={"owner": owner, "repo": repo}
        )


# =============================================================================
# TOOL: LẤY NỘI DUNG FILE TỪ GITHUB
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.github_token:
        raise MCPError(
            message="GitHub token chưa được cấu hình. Vui lòng thêm GITHUB_TOKEN vào .env",
            code="GITHUB_TOKEN_MISSING"
        )

    logger.info(
        "Lấy file từ GitHub",
        owner=owner,
        repo=repo,
        file_path=file_path,
        branch=branch
    )

    try:
        import httpx
        import base64

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        params = {"ref": branch}

        headers = {
            "Authorization": f"token {settings.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Programming-Support-Server"
        }

        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        # Decode nội dung (base64)
        content_b64 = data.get("content", "")
        content = base64.b64decode(content_b64).decode("utf-8")

        result = {
            "success": True,
            "file_path": file_path,
            "repository": f"{owner}/{repo}",
            "branch": branch,
            "size_bytes": data.get("size"),
            "content": content,
            "sha": data.get("sha"),
            "url": data.get("html_url")
        }

        logger.info(
            "Lấy file từ GitHub thành công",
            owner=owner,
            repo=repo,
            file_path=file_path,
            size_bytes=data.get("size")
        )

        return result

    except Exception as e:
        logger.error(
            "Lỗi lấy file từ GitHub",
            owner=owner,
            repo=repo,
            file_path=file_path,
            error=str(e)
        )
        raise MCPError(
            message=f"Không thể lấy file từ GitHub: {str(e)}",
            code="GITHUB_FILE_ERROR",
            details={"owner": owner, "repo": repo, "file_path": file_path}
        )


# =============================================================================
# TOOL: TÌM KIẾM CODE TRONG REPOSITORY
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.github_token:
        raise MCPError(
            message="GitHub token chưa được cấu hình. Vui lòng thêm GITHUB_TOKEN vào .env",
            code="GITHUB_TOKEN_MISSING"
        )

    logger.info(
        "Tìm kiếm code trong repository",
        owner=owner,
        repo=repo,
        query=query,
        max_results=max_results
    )

    try:
        import httpx

        # Sử dụng GitHub Search API với qualifier
        search_query = f"{query} repo:{owner}/{repo}"

        url = "https://api.github.com/search/code"
        params = {
            "q": search_query,
            "per_page": min(max_results, 100)
        }

        headers = {
            "Authorization": f"token {settings.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Programming-Support-Server"
        }

        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

        items = data.get("items", [])
        total_count = data.get("total_count", 0)

        results = []
        for item in items[:max_results]:
            results.append({
                "name": item.get("name"),
                "path": item.get("path"),
                "url": item.get("html_url"),
                "repository": item.get("repository", {}).get("full_name"),
                "language": item.get("language"),
                "score": item.get("score")
            })

        result = {
            "success": True,
            "owner": owner,
            "repo": repo,
            "query": query,
            "total_count": total_count,
            "returned_count": len(results),
            "results": results
        }

        logger.info(
            "Tìm kiếm code trong repository thành công",
            owner=owner,
            repo=repo,
            total_count=total_count,
            returned_count=len(results)
        )

        return result

    except Exception as e:
        logger.error(
            "Lỗi tìm kiếm code trong repository",
            owner=owner,
            repo=repo,
            query=query,
            error=str(e)
        )
        raise MCPError(
            message=f"Không thể tìm kiếm code: {str(e)}",
            code="GITHUB_CODE_SEARCH_ERROR",
            details={"owner": owner, "repo": repo, "query": query}
        )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "github_search",
    "get_repository_info",
    "get_file_from_github",
    "search_code_in_repo"
]