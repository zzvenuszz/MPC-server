"""
MCP Programming Support Server - Công cụ Tìm kiếm Web
Fetch URL, tìm kiếm web, trích xuất nội dung
"""

from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import re

from config import get_settings
from utils import get_logger, MCPError, handle_exception

logger = get_logger()


# =============================================================================
# TOOL: FETCH URL
# =============================================================================

@handle_exception
def fetch_url(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None,
              data: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()
    request_timeout = timeout or settings.request_timeout

    logger.info(
        "Fetch URL",
        url=url,
        method=method,
        timeout=request_timeout
    )

    try:
        import httpx

        # Validate URL
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise MCPError(
                message=f"URL không hợp lệ: {url}",
                code="INVALID_URL"
            )

        # Chỉ cho phép HTTP/HTTPS
        if parsed.scheme not in ["http", "https"]:
            raise MCPError(
                message=f"Chỉ hỗ trợ HTTP/HTTPS, không hỗ trợ: {parsed.scheme}",
                code="UNSUPPORTED_PROTOCOL"
            )

        # Chuẩn bị request
        request_headers = {
            "User-Agent": "MCP-Programming-Support-Server/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        if headers:
            request_headers.update(headers)

        request_kwargs = {
            "headers": request_headers,
            "timeout": request_timeout,
            "follow_redirects": True
        }

        if data and method in ["POST", "PUT", "PATCH"]:
            request_kwargs["json"] = data

        # Thực hiện request
        with httpx.Client() as client:
            response = client.request(method, url, **request_kwargs)
            response.raise_for_status()

        # Xác định content type
        content_type = response.headers.get("content-type", "").lower()

        # Parse nội dung
        if "application/json" in content_type:
            try:
                content = response.json()
                content_text = str(content)
                is_json = True
            except Exception:
                content = response.text
                content_text = content[:500]
                is_json = False
        else:
            content = response.text
            content_text = content[:500]
            is_json = False

        result = {
            "success": True,
            "url": str(response.url),
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_type": content_type,
            "is_json": is_json,
            "content": content,
            "content_preview": content_text,
            "content_length": len(response.content),
            "encoding": response.encoding
        }

        logger.info(
            "Fetch URL thành công",
            url=url,
            status_code=response.status_code,
            content_length=len(response.content)
        )

        return result

    except Exception as e:
        logger.error("Lỗi fetch URL", url=url, error=str(e))
        raise MCPError(
            message=f"Không thể fetch URL: {str(e)}",
            code="FETCH_URL_ERROR",
            details={"url": url, "method": method}
        )


# =============================================================================
# TOOL: TÌM KIẾM WEB (DuckDuckGo)
# =============================================================================

@handle_exception
def web_search(query: str, max_results: int = 10, safe_search: bool = True) -> Dict[str, Any]:
    """
    Tìm kiếm web sử dụng DuckDuckGo (không cần API key)

    Args:
        query: Từ khóa tìm kiếm
        max_results: Số kết quả tối đa
        safe_search: Bật safe search

    Returns:
        Dict chứa kết quả tìm kiếm

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Tìm kiếm web",
        query=query,
        max_results=max_results,
        safe_search=safe_search
    )

    try:
        import httpx
        from bs4 import BeautifulSoup

        # DuckDuckGo HTML endpoint
        url = "https://html.duckduckgo.com/html/"

        params = {
            "q": query,
            "kl": "vn-vn" if settings.cultivation_language == "vi" else "us-en"
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        with httpx.Client(timeout=settings.request_timeout) as client:
            response = client.post(url, data=params, headers=headers)
            response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        results = []
        # DuckDuckGo sử dụng class "result" cho mỗi kết quả
        result_elements = soup.find_all("div", class_="result", limit=max_results)

        for element in result_elements:
            try:
                # Lấy title và URL
                title_element = element.find("a", class_="result__a")
                if not title_element:
                    continue

                title = title_element.get_text(strip=True)
                link = title_element.get("href", "")

                # Lấy snippet
                snippet_element = element.find("a", class_="result__snippet")
                snippet = snippet_element.get_text(strip=True) if snippet_element else ""

                # Lấy domain
                domain_element = element.find("span", class_="result__url")
                domain = domain_element.get_text(strip=True) if domain_element else ""

                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet,
                    "domain": domain
                })
            except Exception as e:
                logger.warning("Lỗi parse kết quả tìm kiếm", error=str(e))
                continue

        result = {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results
        }

        logger.info(
            "Tìm kiếm web thành công",
            query=query,
            results_count=len(results)
        )

        return result

    except Exception as e:
        logger.error("Lỗi tìm kiếm web", query=query, error=str(e))
        raise MCPError(
            message=f"Không thể tìm kiếm web: {str(e)}",
            code="WEB_SEARCH_ERROR",
            details={"query": query}
        )


# =============================================================================
# TOOL: TÌM KIẾM DOCUMENTATION
# =============================================================================

@handle_exception
def search_documentation(query: str, source: str = "auto", max_results: int = 5) -> Dict[str, Any]:
    """
    Tìm kiếm trong documentation của các framework/ngôn ngữ phổ biến

    Args:
        query: Từ khóa tìm kiếm
        source: Nguồn documentation: auto, python, java, javascript, minecraft, paper
        max_results: Số kết quả tối đa

    Returns:
        Dict chứa kết quả tìm kiếm

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Tìm kiếm documentation",
        query=query,
        source=source,
        max_results=max_results
    )

    # Map source -> URL
    doc_sources = {
        "python": "https://docs.python.org/3/search.html",
        "java": "https://docs.oracle.com/en/java/javase/17/docs/api/",
        "javascript": "https://developer.mozilla.org/en-US/search",
        "minecraft": "https://minecraft.fandom.com/wiki/Special:Search",
        "paper": "https://docs.papermc.org/",
        "spring": "https://docs.spring.io/spring-framework/docs/current/reference/html/",
        "react": "https://react.dev/search"
    }

    # Auto-detect source
    if source == "auto":
        query_lower = query.lower()
        if any(word in query_lower for word in ["python", "pip", "django", "flask", "fastapi"]):
            source = "python"
        elif any(word in query_lower for word in ["java", "spring", "maven", "gradle"]):
            source = "java"
        elif any(word in query_lower for word in ["javascript", "js", "node", "npm", "react"]):
            source = "javascript"
        elif any(word in query_lower for word in ["minecraft", "paper", "plugin", "spigot"]):
            source = "paper"
        else:
            source = "python"  # Default

    if source not in doc_sources:
        raise MCPError(
            message=f"Không hỗ trợ nguồn documentation: {source}",
            code="UNSUPPORTED_DOC_SOURCE",
            details={"supported_sources": list(doc_sources.keys())}
        )

    try:
        # Fetch documentation search page
        doc_url = doc_sources[source]

        # Tạo URL tìm kiếm
        if source == "python":
            search_url = f"https://docs.python.org/3/search.html?q={query.replace(' ', '+')}"
        elif source == "java":
            search_url = f"https://docs.oracle.com/en/java/javase/17/docs/api/search.html?q={query.replace(' ', '+')}"
        elif source == "javascript":
            search_url = f"https://developer.mozilla.org/en-US/search?q={query.replace(' ', '+')}"
        elif source == "paper":
            search_url = f"https://docs.papermc.org/paper/1.20/search?q={query.replace(' ', '+')}"
        else:
            search_url = doc_url

        # Fetch search results
        result = fetch_url(search_url, timeout=settings.request_timeout)

        # Parse HTML để trích xuất kết quả
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result["content"], "lxml")

        search_results = []

        if source == "python":
            # Python docs search results
            result_links = soup.find_all("a", class_="reference", limit=max_results)
            for link in result_links:
                search_results.append({
                    "title": link.get_text(strip=True),
                    "url": link.get("href", ""),
                    "source": "Python Documentation"
                })

        elif source == "paper":
            # Paper docs
            result_links = soup.find_all("a", href=True, limit=max_results * 2)
            for link in result_links:
                href = link.get("href", "")
                if "paper" in href.lower() or any(keyword in href.lower() for keyword in ["api", "plugin", "event"]):
                    search_results.append({
                        "title": link.get_text(strip=True),
                        "url": href if href.startswith("http") else f"https://docs.papermc.org{href}",
                        "source": "Paper Documentation"
                    })
                    if len(search_results) >= max_results:
                        break

        else:
            # Generic: lấy tất cả links
            all_links = soup.find_all("a", href=True, limit=max_results * 2)
            for link in all_links:
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if title and len(title) > 5 and href.startswith("http"):
                    search_results.append({
                        "title": title,
                        "url": href,
                        "source": doc_sources[source]
                    })
                    if len(search_results) >= max_results:
                        break

        final_result = {
            "success": True,
            "query": query,
            "source": source,
            "search_url": search_url,
            "results_count": len(search_results),
            "results": search_results[:max_results]
        }

        logger.info(
            "Tìm kiếm documentation thành công",
            query=query,
            source=source,
            results_count=len(search_results)
        )

        return final_result

    except Exception as e:
        logger.error("Lỗi tìm kiếm documentation", query=query, source=source, error=str(e))
        raise MCPError(
            message=f"Không thể tìm kiếm documentation: {str(e)}",
            code="DOC_SEARCH_ERROR",
            details={"query": query, "source": source}
        )


# =============================================================================
# TOOL: TRÍCH XUẤT NỘI DUNG TỪ URL
# =============================================================================

@handle_exception
def extract_content_from_url(url: str, extract_type: str = "text") -> Dict[str, Any]:
    """
    Trích xuất nội dung có cấu trúc từ URL

    Args:
        url: URL cần trích xuất
        extract_type: Loại nội dung: text, links, images, tables, all

    Returns:
        Dict chứa nội dung đã trích xuất

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Trích xuất nội dung từ URL",
        url=url,
        extract_type=extract_type
    )

    try:
        from bs4 import BeautifulSoup

        # Fetch URL
        fetch_result = fetch_url(url)
        html = fetch_result["content"]

        # Parse HTML
        soup = BeautifulSoup(html, "lxml")

        # Loại bỏ script và style
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        result = {
            "success": True,
            "url": url,
            "title": soup.title.string.strip() if soup.title else ""
        }

        # Trích xuất theo type
        if extract_type in ["text", "all"]:
            # Lấy text chính
            main_content = soup.find("main") or soup.find("article") or soup.find("body")
            text = main_content.get_text(separator="\n", strip=True) if main_content else soup.get_text(separator="\n", strip=True)
            # Làm sạch text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            result["text"] = text
            result["text_length"] = len(text)

        if extract_type in ["links", "all"]:
            # Lấy tất cả links
            links = []
            for link in soup.find_all("a", href=True):
                links.append({
                    "text": link.get_text(strip=True),
                    "url": link.get("href", "")
                })
            result["links"] = links[:100]  # Giới hạn
            result["links_count"] = len(links)

        if extract_type in ["images", "all"]:
            # Lấy tất cả images
            images = []
            for img in soup.find_all("img", src=True):
                images.append({
                    "alt": img.get("alt", ""),
                    "src": img.get("src", ""),
                    "width": img.get("width"),
                    "height": img.get("height")
                })
            result["images"] = images[:50]  # Giới hạn
            result["images_count"] = len(images)

        if extract_type in ["tables", "all"]:
            # Lấy tất cả tables
            tables = []
            for table in soup.find_all("table"):
                table_data = []
                for row in table.find_all("tr"):
                    row_data = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
                    if row_data:
                        table_data.append(row_data)
                if table_data:
                    tables.append(table_data)
            result["tables"] = tables[:10]  # Giới hạn
            result["tables_count"] = len(tables)

        logger.info(
            "Trích xuất nội dung thành công",
            url=url,
            extract_type=extract_type
        )

        return result

    except Exception as e:
        logger.error("Lỗi trích xuất nội dung", url=url, error=str(e))
        raise MCPError(
            message=f"Không thể trích xuất nội dung: {str(e)}",
            code="CONTENT_EXTRACTION_ERROR",
            details={"url": url, "extract_type": extract_type}
        )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "fetch_url",
    "web_search",
    "search_documentation",
    "extract_content_from_url"
]