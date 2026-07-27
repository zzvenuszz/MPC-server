"""
MCP Programming Support Server - Web Dashboard
Cung cấp giao diện web quản lý MCP server: logs, tools, config, API keys, permissions
"""

import os
import io
import json
import time
import asyncio
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from collections import deque

# Web server
try:
    from aiohttp import web
except ImportError:
    web = None

# Đường dẫn đến thư mục dashboard static files
DASHBOARD_DIR = Path(__file__).parent / "dashboard_static"

# =============================================================================
# Log Capture Handler - Bắt log để stream lên dashboard
# =============================================================================

class LogCaptureHandler(logging.Handler):
    """Handler bắt log và lưu vào buffer để stream qua WebSocket"""

    def __init__(self, max_logs: int = 1000):
        super().__init__()
        self.logs = deque(maxlen=max_logs)
        self._listeners: Set[asyncio.Queue] = set()

    def emit(self, record: logging.LogRecord):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        self.logs.append(log_entry)
        # Gửi đến tất cả WebSocket listeners
        for q in self._listeners.copy():
            try:
                q.put_nowait(log_entry)
            except asyncio.QueueFull:
                self._listeners.discard(q)

    async def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self._listeners.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._listeners.discard(q)


# Singleton instance
_log_handler = LogCaptureHandler()


# =============================================================================
# Tool Usage Tracker - Theo dõi tool nào được gọi
# =============================================================================

class ToolUsageTracker:
    """Theo dõi lịch sử gọi tool"""

    def __init__(self, max_records: int = 500):
        self.records = deque(maxlen=max_records)
        self._listeners: Set[asyncio.Queue] = set()

    def log_call(self, tool_name: str, arguments: Dict[str, Any], result: Any = None,
                 status: str = "success", duration_ms: float = 0, error: str = None):
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tool": tool_name,
            "arguments": arguments,
            "status": status,
            "duration_ms": round(duration_ms, 2),
            "error": error
        }
        self.records.append(record)
        for q in self._listeners.copy():
            try:
                q.put_nowait(record)
            except asyncio.QueueFull:
                self._listeners.discard(q)

    async def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self._listeners.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._listeners.discard(q)

    def get_tool_stats(self) -> Dict[str, Any]:
        """Thống kê số lần gọi mỗi tool"""
        stats = {}
        for r in self.records:
            tool = r["tool"]
            if tool not in stats:
                stats[tool] = {"calls": 0, "success": 0, "error": 0, "total_duration_ms": 0}
            stats[tool]["calls"] += 1
            if r["status"] == "success":
                stats[tool]["success"] += 1
            else:
                stats[tool]["error"] += 1
            stats[tool]["total_duration_ms"] += r["duration_ms"]
        return stats


_tool_tracker = ToolUsageTracker()


# =============================================================================
# Tool Registry - Quản lý bật/tắt tool
# =============================================================================

class ToolRegistry:
    """Quản lý danh sách tools, bật/tắt, quyền"""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._disabled_tools: Set[str] = set()
        self._tool_permissions: Dict[str, List[str]] = {}  # tool -> allowed roles

    def register(self, name: str, description: str = "", category: str = "general",
                 parameters: List[Dict[str, Any]] = None):
        self._tools[name] = {
            "name": name,
            "description": description,
            "category": category,
            "parameters": parameters or [],
            "enabled": name not in self._disabled_tools,
            "permissions": self._tool_permissions.get(name, ["admin", "user"])
        }

    def is_enabled(self, name: str) -> bool:
        return name not in self._disabled_tools

    def toggle(self, name: str, enabled: bool = None):
        if enabled is None:
            # Toggle
            if name in self._disabled_tools:
                self._disabled_tools.discard(name)
            else:
                self._disabled_tools.add(name)
        elif enabled:
            self._disabled_tools.discard(name)
        else:
            self._disabled_tools.add(name)
        if name in self._tools:
            self._tools[name]["enabled"] = name not in self._disabled_tools

    def get_all_tools(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())

    def set_permission(self, tool_name: str, roles: List[str]):
        self._tool_permissions[tool_name] = roles
        if tool_name in self._tools:
            self._tools[tool_name]["permissions"] = roles


_tool_registry = ToolRegistry()


# =============================================================================
# Dashboard Web Server
# =============================================================================

# Cache for mcp instance to avoid circular import
_mcp_instance = None


def _get_tools_list():
    """Lấy danh sách tools từ FastMCP server"""
    global _mcp_instance
    try:
        # Lazy import to avoid circular dependency
        if _mcp_instance is None:
            from server import mcp
            _mcp_instance = mcp
        
        tools = []
        for tool in _mcp_instance._tool_manager.list_tools():
            tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.input_schema if hasattr(tool, 'input_schema') else {},
            })
        return tools
    except Exception as e:
        return [{"name": f"error: {e}", "description": "", "input_schema": {}}]


def create_dashboard_app():
    """Tạo aiohttp app cho dashboard"""
    if web is None:
        return None

    app = web.Application()

    # =========================================================================
    # MCP HTTP Bridge - Cho phép Cline kết nối qua HTTP
    # =========================================================================
    async def mcp_http_handler(request):
        """HTTP endpoint cho MCP server - cho phép Cline kết nối từ xa"""
        try:
            # Đọc request body
            data = await request.json()
            
            # Import MCP server
            from server import mcp as mcp_server
            
            # Xử lý MCP message
            method = data.get('method', '')
            params = data.get('params', {})
            request_id = data.get('id')
            
            result = None
            error = None
            
            try:
                # Xử lý các MCP methods
                if method == 'initialize':
                    result = {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {
                            'tools': {}
                        },
                        'serverInfo': {
                            'name': 'programming-support-server',
                            'version': '1.0.0'
                        }
                    }
                elif method == 'tools/list':
                    tools_list = []
                    for tool in mcp_server._tool_manager.list_tools():
                        tools_list.append({
                            'name': tool.name,
                            'description': tool.description or '',
                            'inputSchema': tool.input_schema if hasattr(tool, 'input_schema') else {}
                        })
                    result = {'tools': tools_list}
                elif method == 'tools/call':
                    tool_name = params.get('name')
                    arguments = params.get('arguments', {})
                    
                    # Gọi tool
                    import asyncio
                    loop = asyncio.get_event_loop()
                    tool_result = await loop.run_in_executor(
                        None,
                        lambda: mcp_server._tool_manager.call_tool(tool_name, arguments)
                    )
                    
                    result = {
                        'content': [{'type': 'text', 'text': str(tool_result)}]
                    }
                else:
                    error = {'code': -32601, 'message': f'Method not found: {method}'}
            except Exception as e:
                error = {'code': -32603, 'message': f'Internal error: {str(e)}'}
            
            # Trả về response
            response_data = {}
            if error:
                response_data['error'] = error
            if result is not None:
                response_data['result'] = result
            if request_id is not None:
                response_data['id'] = request_id
            
            return web.json_response(response_data)
            
        except Exception as e:
            return web.json_response({
                'error': {'code': -32700, 'message': f'Parse error: {str(e)}'}
            }, status=400)

    app.router.add_post('/mcp', mcp_http_handler)
    app.router.add_get('/mcp', mcp_http_handler)  # Also accept GET for SSE

    # =========================================================================
    # API Routes
    # =========================================================================

    async def api_auth_login(request):
        """POST /api/auth/login - Đăng nhập"""
        try:
            data = await request.json()
            password = data.get('password', '')
            
            # Lấy password từ environment variable
            expected_password = os.environ.get('PASSWORD', '')
            
            if not expected_password:
                # Nếu không có PASSWORD env, cho phép truy cập (development mode)
                return web.json_response({'status': 'ok'})
            
            if password == expected_password:
                # Tạo response với cookie
                response = web.json_response({'status': 'ok'})
                response.set_cookie('dashboard_auth', 'authenticated', max_age=86400, httponly=True)
                return response
            else:
                return web.json_response({'error': 'Invalid password'}, status=401)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)

    async def api_logs(request):
        """GET /api/logs - Lấy logs"""
        level = request.query.get("level", "").upper()
        limit = int(request.query.get("limit", 200))
        logs = list(_log_handler.logs)
        if level:
            logs = [l for l in logs if l["level"] == level]
        return web.json_response(logs[-limit:])

    async def api_log_stream(request):
        """GET /api/logs/stream - WebSocket stream logs"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        q = await _log_handler.subscribe()
        try:
            # Gửi logs hiện tại
            current_logs = list(_log_handler.logs)[-50:]
            await ws.send_json({"type": "init", "data": current_logs})
            # Stream logs mới
            while True:
                try:
                    log_entry = await asyncio.wait_for(q.get(), timeout=30)
                    await ws.send_json({"type": "log", "data": log_entry})
                except asyncio.TimeoutError:
                    await ws.send_json({"type": "ping"})
        except asyncio.CancelledError:
            pass
        finally:
            _log_handler.unsubscribe(q)
        return ws

    async def api_tools(request):
        """GET /api/tools - Lấy danh sách tools"""
        tools_info = _get_tools_list()
        for t in tools_info:
            t["enabled"] = _tool_registry.is_enabled(t["name"])
        return web.json_response(tools_info)

    async def api_tools_toggle(request):
        """POST /api/tools/{name}/toggle - Bật/tắt tool"""
        name = request.match_info.get("name")
        data = await request.json()
        enabled = data.get("enabled")
        _tool_registry.toggle(name, enabled)
        return web.json_response({"name": name, "enabled": _tool_registry.is_enabled(name)})

    async def api_tool_usage(request):
        """GET /api/tools/usage - Lấy thống kê sử dụng tool"""
        stats = _tool_tracker.get_tool_stats()
        return web.json_response({
            "stats": stats,
            "recent_calls": list(_tool_tracker.records)[-50:]
        })

    async def api_tool_stream(request):
        """GET /api/tools/stream - WebSocket stream tool calls"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        q = await _tool_tracker.subscribe()
        try:
            recent = list(_tool_tracker.records)[-20:]
            await ws.send_json({"type": "init", "data": recent})
            while True:
                try:
                    record = await asyncio.wait_for(q.get(), timeout=30)
                    await ws.send_json({"type": "tool_call", "data": record})
                except asyncio.TimeoutError:
                    await ws.send_json({"type": "ping"})
        except asyncio.CancelledError:
            pass
        finally:
            _tool_tracker.unsubscribe(q)
        return ws

    async def api_config(request):
        """GET /api/config - Lấy cấu hình hiện tại"""
        from config import get_settings
        settings = get_settings()
        config = {
            "workspace": str(settings.workspace),
            "log_level": settings.log_level,
            "request_timeout": settings.request_timeout,
            "max_file_size": settings.max_file_size,
            "allow_shell": settings.allow_shell,
            "allow_write": settings.allow_write,
            "allowed_shell_commands": settings.allowed_shell_commands,
            "github_token": "***" if settings.github_token else None,
            "cultivation_language": settings.cultivation_language,
            "cultivation_detail_level": settings.cultivation_detail_level,
            "rate_limit_per_minute": settings.rate_limit_per_minute,
            "max_concurrent_requests": settings.max_concurrent_requests,
            "verify_ssl": settings.verify_ssl,
        }
        return web.json_response(config)

    async def api_config_update(request):
        """POST /api/config - Cập nhật cấu hình"""
        from config import reload_settings, get_settings
        data = await request.json()
        # Chỉ cập nhật các biến môi trường
        for key, value in data.items():
            env_key = key.upper()
            if value is not None:
                os.environ[env_key] = str(value)
        # Reload settings
        new_settings = reload_settings()
        return web.json_response({"status": "updated", "log_level": new_settings.log_level})

    async def api_keys(request):
        """GET /api/keys - Lấy danh sách API keys"""
        from config import get_settings
        settings = get_settings()
        keys = {}
        if settings.github_token:
            keys["github_token"] = "***" + settings.github_token[-4:]
        return web.json_response(keys)

    async def api_keys_update(request):
        """POST /api/keys - Cập nhật API key"""
        from config import reload_settings
        data = await request.json()
        for key, value in data.items():
            env_key = key.upper()
            os.environ[env_key] = value
        reload_settings()
        return web.json_response({"status": "updated"})

    async def api_test_tool(request):
        """POST /api/tools/{name}/test - Test một tool"""
        name = request.match_info.get("name")
        data = await request.json()
        args = data.get("arguments", {})
        try:
            from server import mcp
            start = time.time()
            result = await mcp.call_tool(name, args)
            duration = (time.time() - start) * 1000
            _tool_tracker.log_call(name, args, result, "success", duration)
            return web.json_response({
                "status": "success",
                "result": str(result),
                "duration_ms": round(duration, 2)
            })
        except Exception as e:
            _tool_tracker.log_call(name, args, None, "error", 0, str(e))
            return web.json_response({"status": "error", "error": str(e)}, status=400)

    async def api_server_status(request):
        """GET /api/status - Lấy trạng thái server"""
        import psutil
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            uptime = time.time() - psutil.boot_time()
        except ImportError:
            cpu_percent = 0
            memory = type('obj', (object,), {'percent': 0, 'used': 0, 'total': 0})()
            uptime = 0

        from config import get_settings
        settings = get_settings()
        tools_info = _get_tools_list()

        return web.json_response({
            "server": {
                "name": "MCP Programming Support Server",
                "version": "1.0.0",
                "status": "running",
                "uptime_seconds": uptime,
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "memory_total": memory.total,
            },
            "tools": {
                "total": len(tools_info),
                "enabled": sum(1 for t in tools_info if _tool_registry.is_enabled(t["name"])),
            },
            "config": {
                "log_level": settings.log_level,
                "workspace": str(settings.workspace),
            }
        })

    # =========================================================================
    # Register routes
    # =========================================================================
    app.router.add_post("/api/auth/login", api_auth_login)
    app.router.add_get("/api/logs", api_logs)
    app.router.add_get("/api/logs/stream", api_log_stream)
    app.router.add_get("/api/tools", api_tools)
    app.router.add_post("/api/tools/{name}/toggle", api_tools_toggle)
    app.router.add_post("/api/tools/{name}/test", api_test_tool)
    app.router.add_get("/api/tools/usage", api_tool_usage)
    app.router.add_get("/api/tools/stream", api_tool_stream)
    app.router.add_get("/api/config", api_config)
    app.router.add_post("/api/config", api_config_update)
    app.router.add_get("/api/keys", api_keys)
    app.router.add_post("/api/keys", api_keys_update)
    app.router.add_get("/api/status", api_server_status)

    # =========================================================================
    # Serve dashboard frontend
    # =========================================================================
    static_dir = Path(__file__).parent / "dashboard_static"
    index_html = static_dir / "index.html"
    if index_html.exists():
        # Serve static files (CSS/JS) từ /static/ prefix
        app.router.add_static("/static", str(static_dir))
        async def index_handler(request):
            return web.FileResponse(index_html)
        app.router.add_get("/", index_handler)
    else:
        async def index(request):
            return web.Response(text="Dashboard static files not found", status=404)
        app.router.add_get("/", index)

    return app


def _start_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """Khởi động dashboard web server trong thread riêng"""
    app = create_dashboard_app()
    if app is None:
        logging.getLogger("mcp-server").error(
            "Không thể khởi động dashboard: thiếu aiohttp. Cài: pip install aiohttp"
        )
        return

    logger = logging.getLogger("mcp-server")
    logger.info(f"Dashboard đang khởi động trên http://{host}:{port}")

    # Tạo event loop mới cho thread này (không dùng web.run_app vì nó dùng signal handlers)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    runner = web.AppRunner(app, handle_signals=False)
    loop.run_until_complete(runner.setup())

    site = web.TCPSite(runner, host, port)
    loop.run_until_complete(site.start())

    logger.info(f"Dashboard đã khởi động trên http://{host}:{port}")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(runner.cleanup())
        loop.close()


def start_dashboard_thread(host: str = None, port: int = None):
    """Khởi động dashboard trong background thread"""
    # Đọc cấu hình từ config nếu không được truyền vào
    if host is None or port is None:
        try:
            from config import get_settings
            settings = get_settings()
            host = host or settings.host
            port = port or settings.port
        except Exception:
            # Fallback to defaults nếu không đọc được config
            host = host or "0.0.0.0"
            port = port or 8080

    thread = threading.Thread(
        target=_start_dashboard,
        args=(host, port),
        daemon=True,
        name="dashboard-server"
    )
    thread.start()
    return thread


# =============================================================================
# Utility: Gắn log handler
# =============================================================================

def setup_dashboard_logging():
    """Gắn log capture handler vào root logger"""
    root_logger = logging.getLogger()
    _log_handler.setLevel(logging.DEBUG)
    _log_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    # Chỉ thêm nếu chưa có
    if _log_handler not in root_logger.handlers:
        root_logger.addHandler(_log_handler)

    # Gắn vào structlog
    try:
        import structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    except ImportError:
        pass


def log_tool_call(tool_name: str, arguments: Dict[str, Any], result: Any = None,
                  status: str = "success", duration_ms: float = 0, error: str = None):
    """Ghi lại một lần gọi tool"""
    _tool_tracker.log_call(tool_name, arguments, result, status, duration_ms, error)


# =============================================================================
# Export
# =============================================================================
__all__ = [
    "setup_dashboard_logging",
    "start_dashboard_thread",
    "create_dashboard_app",
    "log_tool_call",
    "_log_handler",
    "_tool_tracker",
    "_tool_registry",
]