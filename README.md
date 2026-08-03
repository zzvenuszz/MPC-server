---
title: MPC Server!
emoji: 💥
colorFrom: indigo
colorTo: gray
sdk: docker
sdk_version: "latest"
python_version: "3.12"
app_file: server.py
pinned: false
app_port: 8080
---

# MCP Programming Support Server

> MCP Server hỗ trợ lập trình, phát triển Minecraft Paper plugin và thiết kế game tu tiên (Xianxia)

## 📋 Giới thiệu

MCP Programming Support Server là một MCP (Model Context Protocol) Server production-ready, được thiết kế theo nguyên tắc **Docker First**. Server này cung cấp bộ công cụ toàn diện cho lập trình viên, đặc biệt chuyên sâu về phát triển Minecraft Paper plugin và thiết kế hệ thống game tu tiên.

### Tính năng chính

- **📁 Filesystem Tools**: Đọc, ghi, tìm kiếm file an toàn
- **🐙 GitHub Integration**: Tìm kiếm repository, code, issues
- **🔍 Web Search**: Tìm kiếm web, fetch URL, trích xuất nội dung
- **🔍 Code Review**: Review code, kiểm soát lỗi, dọn dẹp code, thêm debug logs
- **💻 Shell Execution**: Thực thi shell commands an toàn với whitelist
- **🐳 Docker Tools**: Tạo Dockerfile, docker-compose, phân tích Dockerfile
- **📚 Documentation**: Quản lý hướng dẫn, tạo template, trích xuất bài học kinh nghiệm
- **⛏️ Minecraft Paper**: Tham khảo mã nguồn Paper, tạo plugin structure
- **🏔️ Xianxia Cultivation**: Tạo hệ thống tu tiên, cảnh giới, vật phẩm, kỹ năng

## 🏗️ Kiến trúc

```
mcp-programming-server/
├── Dockerfile                 # Multi-stage build, non-root user
├── docker-compose.yml         # Production configuration
├── .dockerignore              # Docker ignore rules
├── .env.example               # Environment variables template
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation (this file)
├── config.py                   # Pydantic settings management
├── server.py                   # FastMCP server với 30+ tools
├── utils.py                    # Logging, validation, utilities
├── tools/
│   ├── __init__.py
│   ├── filesystem.py          # File operations
│   ├── github.py              # GitHub API integration
│   ├── search.py              # Web search & URL fetching
│   ├── review.py              # Code review & quality
│   ├── shell.py               # Safe shell execution
│   ├── docker_tools.py        # Dockerfile generation
│   ├── docs.py                # Documentation management
│   └── minecraft/
│       ├── __init__.py
│       ├── paper_reference.py # Paper source reference
│       ├── plugin_builder.py  # Plugin scaffolding
│       └── xianxia_generator.py # Cultivation systems
└── logs/                       # Log files directory
```

### Nguyên tắc thiết kế

1. **Docker First**: Mọi thứ chạy trong Docker, không giả định cài đặt trên host
2. **Security First**: Non-root user, command whitelist, path validation
3. **Production-Ready**: Logging, healthcheck, error handling, type hints đầy đủ
4. **Vietnamese Language**: Toàn bộ tool descriptions và responses bằng tiếng Việt
5. **Extensible**: Dễ dàng thêm tools và features mới

## 🚀 Cách Build Docker

### Build image

```bash
# Build từ Dockerfile
docker build -t mcp-programming-server:latest .

# Hoặc sử dụng docker-compose
docker-compose build
```

### Verify build

```bash
# Kiểm tra image đã build
docker images | grep mcp-programming-server

# Test run
docker run --rm -it mcp-programming-server:latest python -c "import sys; print('OK')"
```

## 🐳 Docker Compose

### Khởi chạy

```bash
# Start service
docker-compose up -d

# Xem logs
docker-compose logs -f mcp-server

# Stop service
docker-compose down
```

### Volume mounts

- `/data:/data` - Workspace chính cho file operations (mount sẵn của host)
- `./logs:/app/logs` - Log files
- `paper-server:/data/paper-server` - Paper server source code

### Environment variables

Tất cả cấu hình qua environment variables. Xem `.env.example` để biết đầy đủ.

## 💻 Chạy Local (không dùng Docker)

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Clone repository
git clone <repository-url>
cd mcp-programming-server

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Cấu hình environment
cp .env.example .env
# Edit .env với các giá trị thực tế

# Chạy server
python server.py
```

## ☁️ Chạy Hugging Face Spaces

### Setup

1. Tạo Hugging Face Space với SDK: Docker
2. Upload toàn bộ project (trừ `logs/`, `workspace/`)
3. Hugging Face sẽ tự động build và deploy

### Configuration

```bash
# Trong Space Settings -> Variables and secrets
# Thêm các environment variables:
WORKSPACE=/workspace
LOG_LEVEL=INFO
ALLOW_SHELL=true
ALLOW_WRITE=true
```

## ⚙️ Cấu hình Cline

### Cấu hình cho Hugging Face Spaces (Remote SSE)

Nếu server chạy trên Hugging Face Spaces (remote), sử dụng cấu hình SSE:

```json
{
  "mcpServers": {
    "programming-support": {
      "url": "https://huyhoan76-cline.hf.space/sse",
      "transport": "sse"
    }
  }
}
```

### Cấu hình cho Docker Local

Thêm vào Cline MCP settings (`cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "programming-support": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-programming-server",
        "python",
        "server.py"
      ],
      "env": {
        "WORKSPACE": "/workspace",
        "LOG_LEVEL": "INFO",
        "ALLOW_SHELL": "true",
        "ALLOW_WRITE": "true"
      }
    }
  }
}
```

### Cấu hình cho Local (không Docker)

```json
{
  "mcpServers": {
    "programming-support": {
      "command": "python",
      "args": ["/path/to/mcp-programming-server/server.py"],
      "env": {
        "WORKSPACE": "/path/to/workspace",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## ⚙️ Cấu hình Claude Desktop

Thêm vào Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "programming-support": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp-programming-server",
        "python",
        "server.py"
      ],
      "env": {
        "WORKSPACE": "/workspace",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Lưu ý**: Claude Desktop hiện tại chủ yếu hỗ trợ stdio transport. Để sử dụng SSE transport, cần cấu hình khác.

## 📚 Ví dụ Tool Call

### Filesystem Tools

```python
# Đọc file
read_file(file_path="src/main.py", encoding="utf-8")

# Ghi file
write_file(file_path="src/utils.py", content="...")

# Tìm kiếm text
search_text(
    directory_path="src",
    search_text="TODO",
    file_pattern="*.py"
)

# Liệt kê thư mục
list_directory(directory_path="src", recursive=True)
```

### GitHub Tools

```python
# Tìm kiếm repository
github_search(
    query="minecraft plugin",
    search_type="repositories",
    language="java",
    max_results=10
)

# Lấy thông tin repository
get_repository_info(owner="PaperMC", repo="Paper")

# Tìm code trong repo
search_code_in_repo(
    owner="PaperMC",
    repo="Paper",
    query="PlayerJoinEvent",
    max_results=5
)
```

### Code Review Tools

```python
# Review code
review_code(
    file_path="src/main.py",
    language="python",
    check_security=True,
    check_performance=True
)

# Kiểm soát lỗi
error_control(file_path="src/main.py")

# Fix code an toàn
fix_code_safely(
    file_path="src/main.py",
    fix_type="remove_unused_imports",
    auto_approve=False
)

# Thêm debug logs
add_debug_logs(
    file_path="src/main.py",
    language="python",
    log_level="DEBUG"
)

# Dọn dẹp code
cleanup_code(file_path="src/main.py")
```

### Minecraft Tools

```python
# Tham khảo Paper source
reference_paper_source(
    query="PlayerJoinEvent",
    search_type="event",
    max_results=5
)

# Tạo plugin structure
create_plugin_structure(
    plugin_name="CultivationPlugin",
    package_name="com.example.cultivation",
    author="Your Name",
    version="1.0.0"
)

# Tạo listener
implement_listener(
    listener_name="PlayerListener",
    package_name="com.example.cultivation",
    events=["PlayerJoinEvent", "PlayerQuitEvent"]
)
```

### Xianxia Cultivation Tools

```python
# Tìm kiếm cốt truyện tu tiên
search_cultivation_story(
    query="luyện khí",
    max_results=5
)

# Tạo hệ thống cảnh giới
generate_cultivation_system(
    system_name="Hệ thống Cảnh Giới Cơ Bản",
    realm_count=9,
    difficulty="medium"
)

# Tạo hệ thống vật phẩm
generate_item_system(
    system_name="Vật phẩm tu tiên",
    item_categories=["pháp bảo", "đan dược", "tài liệu"],
    rarity_levels=5
)

# Tạo hệ thống kỹ năng
generate_skill_system(
    system_name="Kỹ năng tu luyện",
    skill_types=["công kích", "phòng thủ", "hồi phục"],
    max_skill_level=10
)

# Cân bằng game
balance_cultivation(
    realms=[...],
    target_playtime_hours=100,
    progression_curve="exponential"
)
```

## 🔧 Troubleshooting

### Docker issues

**Problem**: Container không start

```bash
# Check logs
docker-compose logs mcp-server

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

**Problem**: Permission denied

```bash
# Fix workspace permissions
sudo chown -R 1000:1000 ./workspace
sudo chown -R 1000:1000 ./logs
```

### Python issues

**Problem**: Import errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Problem**: Module not found

```bash
# Ensure PYTHONPATH
export PYTHONPATH=/path/to/mcp-programming-server:$PYTHONPATH
```

### MCP Connection issues

**Problem**: Server không connect

```bash
# Test server manually
python server.py

# Check logs
tail -f logs/mcp-server.log

# Verify SSE endpoint is accessible
curl -N https://huyhoan76-cline.hf.space/sse
```

**Problem**: SSE connection fails với lỗi 400

```bash
# Đảm bảo server đang chạy với SSE transport
# Check logs để xem endpoint đúng
# FastMCP SSE endpoint mặc định là /sse
```

**Problem**: Parse error khi kết nối

```bash
# Lỗi này xảy ra khi client gửi request đến endpoint sai
# Đảm bảo endpoint là /sse (không phải /mcp)
# SSE transport sử dụng JSON-RPC 2.0 protocol
```

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Port cho MCP Server (HF Spaces: 8080) |
| `WORKSPACE` | `/workspace` | Thư mục làm việc chính |
| `LOG_LEVEL` | `INFO` | Mức log: DEBUG, INFO, WARNING, ERROR |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout (giây) |
| `MAX_FILE_SIZE` | `10485760` | Kích thước file tối đa (bytes) |
| `ALLOW_SHELL` | `true` | Cho phép shell execution |
| `ALLOW_WRITE` | `true` | Cho phép ghi file |
| `GITHUB_TOKEN` | - | GitHub Personal Access Token |
| `PAPER_SERVER_PATH` | - | Đường dẫn Paper source code |
| `PAPER_API_VERSION` | `1.20` | Paper API version |
| `CULTIVATION_LANGUAGE` | `vi` | Ngôn ngữ nội dung tu tiên |

## 🛡️ Security

### Shell Command Whitelist

Commands được phép:
- `git`, `ls`, `find`, `grep`, `rg`
- `python`, `node`, `npm`, `pip`
- `cargo`, `go`, `java`, `gradle`, `mvn`

Commands bị chặn:
- `rm`, `shutdown`, `reboot`, `mkfs`, `dd`
- `sudo`, `passwd`, `iptables`, `systemctl`
- `kill`, `killall`, `chmod 777`

### Path Validation

Tất cả file operations được giới hạn trong `WORKSPACE` directory. Path traversal attacks bị chặn.

## 📊 Monitoring

### Logs

```bash
# Docker logs
docker-compose logs -f mcp-server

# Log files
tail -f ./logs/mcp-server.log
```

### Health Check

```bash
# Check container health
docker-compose ps

# Manual health check
docker exec mcp-programming-server python -c "import sys; sys.exit(0)"
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License

## 👥 Author

MCP Programming Support Server Team

---

**Lưu ý**: Server này được thiết kế để chạy trong Docker. Không chạy trực tiếp trên host mà không có Docker container.
