# MCP Server - Deployment Summary

## Các vấn đề đã sửa

### 1. Import Error ✅
**File**: `tools/minecraft/paper_reference.py`
- **Vấn đề**: Import sai module
- **Giải pháp**: Sửa `from tools.filesystem import search_text`

### 2. Dashboard Stats không hiển thị ✅
**Files**: `dashboard.py`, `dashboard_static/index.html`
- **Vấn đề**: Logs và tool calls không hiển thị ngay khi mở tab
- **Giải pháp**: 
  - Thêm `renderAllLogs()` và `renderAllToolCalls()` khi navigate đến tabs
  - Load data ngay khi khởi động dashboard

### 3. Test Tool Validation Error ✅
**File**: `dashboard_static/index.html`
- **Vấn đề**: Test tool trả về lỗi validation (missing required fields)
- **Giải pháp**: 
  - Tự động điền giá trị mặc định cho các parameters
  - Validate required fields trước khi gửi request
  - Tạo test file tự động cho file operations

### 4. Terminal thực sự với PTY ✅
**Files**: `terminal.py`, `dashboard.py`, `dashboard_static/index.html`
- **Vấn đề**: Console cũ là input/output tách biệt, không phải terminal thật
- **Giải pháp**:
  - Tạo `terminal.py` với PTY-based terminal (os.fork + pty.openpty)
  - Tích hợp REST API endpoints: `/api/terminal/*`
  - Frontend sử dụng xterm.js cho terminal emulation
  - Real bash shell với đầy đủ tính năng (Ctrl+C, persistent session)

### 5. Workspace Path cho Hugging Face ✅
**File**: `config.py`
- **Vấn đề**: Permission denied khi tạo `/data` trên HF Spaces
- **Giải pháp**: Đổi workspace mặc định từ `/data` sang `/tmp/mcp-workspace`

## Files đã thay đổi

1. `tools/minecraft/paper_reference.py` - Sửa import error
2. `config.py` - Đổi workspace path
3. `dashboard.py` - Thêm terminal API routes với authentication
4. `terminal.py` - Mới: PTY-based terminal module
5. `dashboard_static/index.html` - Terminal UI với xterm.js

## Cách Deploy lên Hugging Face Spaces

### Bước 1: Commit và Push code

```bash
git add .
git commit -m "fix: terminal, dashboard stats, test tool, workspace path"
git push origin main
```

### Bước 2: Environment Variables (trên HF Spaces)

Đảm bảo các biến môi trường sau được set:

```bash
# Required
PASSWORD=your_password_here

# Optional (nếu cần)
GITHUB_TOKEN=ghp_xxx
LOG_LEVEL=INFO
```

### Bước 3: Restart Space

Sau khi push code, restart Hugging Face Space để áp dụng thay đổi.

## Cách sử dụng

### Dashboard
1. Mở URL của HF Space
2. Đăng nhập với password (nếu có set PASSWORD env)
3. Các tabs:
   - **Dashboard**: Overview stats
   - **Logs**: Real-time logs với filter
   - **Tool Usage**: Tool call history
   - **Tools**: Manage và test tools
   - **Console**: Terminal thực sự với bash shell
   - **Configuration**: Server config
   - **API Keys**: Manage API keys

### Terminal
- Terminal sử dụng PTY (pseudo-terminal) thực sự
- Real bash shell với đầy đủ tính năng
- Persistent session (giữ nguyên khi chuyển tab)
- Support Ctrl+C, Ctrl+Z, etc.
- Working directory: `/tmp/mcp-workspace`

### Test Tool
1. Vào tab "Tools"
2. Click "🧪 Test" trên tool muốn test
3. Form tự động điền giá trị mặc định
4. Click "▶️ Run Test"
5. Kết quả hiển thị chi tiết

## Lưu ý quan trọng

1. **Terminal API yêu cầu authentication**: Phải đăng nhập trước khi dùng terminal
2. **Workspace**: Tất cả file operations dùng `/tmp/mcp-workspace`
3. **Shell commands**: Chỉ chạy được commands trong `allowed_shell_commands`
4. **No persistent storage**: Trên HF Spaces, mọi thứ trong `/tmp` sẽ mất khi restart

## Troubleshooting

### Dashboard không load (404)
- Kiểm tra server log có lỗi gì không
- Đảm bảo `dashboard_static/index.html` tồn tại
- Restart Space

### Terminal không kết nối được
- Kiểm tra authentication (đã đăng nhập chưa)
- Kiểm tra `allow_shell` = true trong config
- Xem console log trong browser DevTools

### Test tool lỗi validation
- Kiểm tra required fields đã được điền chưa
- Xem log để debug arguments được gửi

## Technical Details

### Terminal Architecture
```
Frontend (xterm.js)
    ↓ REST API (polling 50ms)
Backend (Starlette routes)
    ↓ PTY (os.fork + pty.openpty)
Bash Shell (real bash process)
```

### Dashboard Architecture
```
Frontend (vanilla JS)
    ↓ REST API (aiohttp/starlette)
Backend (dashboard.py)
    ↓ WebSocket (logs/tools streaming)
MCP Server (FastMCP)
```

## Security Notes

1. Terminal có authentication (cookie-based)
2. Shell commands bị giới hạn bởi `allowed_shell_commands`
3. File operations bị giới hạn bởi workspace path
4. API keys được mask (hiển thị chỉ 4 ký tự cuối)