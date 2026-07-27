"""
MCP Programming Support Server - Cấu hình Trung tâm
Quản lý tất cả cấu hình thông qua biến môi trường với Pydantic Settings
"""

from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Cấu hình trung tâm cho MCP Server.
    Tất cả giá trị được đọc từ biến môi trường hoặc file .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # =============================================================================
    # CẤU HÌNH CHUNG
    # =============================================================================

    # Thư mục làm việc chính
    workspace: Path = Field(
        default=Path("/data"),
        description="Thư mục làm việc chính cho các thao tác file"
    )

    # Mức độ log
    log_level: str = Field(
        default="INFO",
        description="Mức độ log: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    # Timeout cho HTTP requests (giây)
    request_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout cho các request HTTP"
    )

    # Kích thước file tối đa (bytes) - mặc định 10MB
    max_file_size: int = Field(
        default=10_485_760,
        ge=1024,
        le=104_857_600,
        description="Kích thước file tối đa được phép đọc/ghi (bytes)"
    )

    # =============================================================================
    # BẢO MẬT & QUYỀN HẠN
    # =============================================================================

    # Cho phép thực thi shell commands
    allow_shell: bool = Field(
        default=True,
        description="Cho phép thực thi shell commands"
    )

    # Cho phép ghi file
    allow_write: bool = Field(
        default=True,
        description="Cho phép ghi file vào workspace"
    )

    # Danh sách shell commands được phép
    allowed_shell_commands: List[str] = Field(
        default_factory=lambda: [
            "git", "ls", "find", "grep", "rg", "python", "node",
            "npm", "pip", "cargo", "go", "java", "gradle", "mvn"
        ],
        description="Danh sách shell commands được phép thực thi"
    )

    @validator("allowed_shell_commands", pre=True)
    def parse_shell_commands(cls, v) -> List[str]:
        """Parse danh sách commands từ string hoặc list"""
        if isinstance(v, str):
            return [cmd.strip() for cmd in v.split(",") if cmd.strip()]
        return v

    # =============================================================================
    # GITHUB INTEGRATION
    # =============================================================================

    # GitHub Personal Access Token
    github_token: Optional[str] = Field(
        default=None,
        description="GitHub Personal Access Token để tìm kiếm repository"
    )

    # =============================================================================
    # MINECRAFT PAPER SERVER
    # =============================================================================

    # Đường dẫn đến mã nguồn Paper server
    paper_server_path: Optional[Path] = Field(
        default=None,
        description="Đường dẫn đến thư mục mã nguồn Paper server đã clone"
    )

    # Phiên bản Paper API
    paper_api_version: str = Field(
        default="1.20",
        description="Phiên bản Paper API (ví dụ: 1.20, 1.20.1)"
    )

    # =============================================================================
    # LOGGING & MONITORING
    # =============================================================================

    # Đường dẫn thư mục log
    log_dir: Path = Field(
        default=Path("/app/logs"),
        description="Đường dẫn thư mục lưu log files"
    )

    # Kích thước file log tối đa trước khi rotate (bytes) - 10MB
    log_max_size: int = Field(
        default=10_485_760,
        ge=1_048_576,
        le=104_857_600,
        description="Kích thước file log tối đa trước khi rotate"
    )

    # Số file log backup giữ lại
    log_backup_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Số file log backup giữ lại"
    )

    # =============================================================================
    # DOCKER
    # =============================================================================

    # Docker socket path
    docker_socket: Optional[str] = Field(
        default="/var/run/docker.sock",
        description="Đường dẫn đến Docker socket"
    )

    # =============================================================================
    # CULTIVATION GAME DESIGN (XIANXIA)
    # =============================================================================

    # Ngôn ngữ cho nội dung tu tiên
    cultivation_language: str = Field(
        default="vi",
        description="Ngôn ngữ cho nội dung tu tiên: vi, en, zh"
    )

    # Mức độ chi tiết của nội dung tu tiên
    cultivation_detail_level: str = Field(
        default="high",
        description="Mức độ chi tiết: low, medium, high"
    )

    # =============================================================================
    # PERFORMANCE & RATE LIMITING
    # =============================================================================

    # Số request tối đa mỗi phút
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Số request tối đa mỗi phút"
    )

    # Số concurrent requests tối đa
    max_concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Số concurrent requests tối đa"
    )

    # =============================================================================
    # NETWORK & PROXY
    # =============================================================================

    # HTTP Proxy
    http_proxy: Optional[str] = Field(
        default=None,
        description="HTTP Proxy URL (nếu cần)"
    )

    # HTTPS Proxy
    https_proxy: Optional[str] = Field(
        default=None,
        description="HTTPS Proxy URL (nếu cần)"
    )

    # Không verify SSL certificates
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates (chỉ tắt cho development)"
    )

    # =============================================================================
    # SERVER CONFIGURATION
    # =============================================================================

    # Server host
    host: str = Field(
        default="0.0.0.0",
        description="Server host (HF Spaces cần 0.0.0.0)"
    )

    # Server port
    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description="Server port (HF Spaces dùng 8080)"
    )

    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================

    @property
    def is_production(self) -> bool:
        """Kiểm tra có đang chạy trong môi trường production không"""
        return self.log_level.upper() in ["INFO", "WARNING", "ERROR", "CRITICAL"]

    @property
    def is_development(self) -> bool:
        """Kiểm tra có đang chạy trong môi trường development không"""
        return self.log_level.upper() == "DEBUG"

    @property
    def max_file_size_mb(self) -> float:
        """Kích thước file tối đa tính bằng MB"""
        return self.max_file_size / (1024 * 1024)

    def get_workspace_path(self, *subpaths: str) -> Path:
        """
        Lấy đường dẫn đầy đủ trong workspace

        Args:
            *subpaths: Các thư mục con cần nối

        Returns:
            Path đầy đủ
        """
        return self.workspace.joinpath(*subpaths)

    def ensure_workspace_exists(self) -> None:
        """Tạo thư mục workspace nếu chưa tồn tại"""
        self.workspace.mkdir(parents=True, exist_ok=True)

    def ensure_log_dir_exists(self) -> None:
        """Tạo thư mục log nếu chưa tồn tại"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_log_file_path(self, name: str = "mcp-server") -> Path:
        """
        Lấy đường dẫn file log

        Args:
            name: Tên file log (không cần extension)

        Returns:
            Path đến file log
        """
        return self.log_dir / f"{name}.log"


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Lấy instance Settings (Singleton pattern)

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        # Đảm bảo các thư mục tồn tại
        _settings.ensure_workspace_exists()
        _settings.ensure_log_dir_exists()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings từ environment variables

    Returns:
        Settings instance mới
    """
    global _settings
    _settings = Settings()
    _settings.ensure_workspace_exists()
    _settings.ensure_log_dir_exists()
    return _settings


# Export tiện ích
__all__ = [
    "Settings",
    "get_settings",
    "reload_settings"
]