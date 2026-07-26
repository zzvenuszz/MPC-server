"""
MCP Programming Support Server - Công cụ Docker
Tạo và quản lý Dockerfiles, docker-compose
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from config import get_settings
from utils import get_logger, MCPError, handle_exception, write_file_safe

logger = get_logger()


# =============================================================================
# TOOL: TẠO DOCKERFILE
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Tạo Dockerfile",
        project_type=project_type,
        project_name=project_name,
        port=port
    )

    try:
        # Chọn base image theo project type
        if not base_image:
            base_images = {
                "python": "python:3.12-slim",
                "node": "node:20-alpine",
                "java": "eclipse-temurin:17-jre-slim",
                "go": "golang:1.22-alpine",
                "rust": "rust:1.75-slim",
                "generic": "alpine:latest"
            }
            base_image = base_images.get(project_type, "alpine:latest")

        # Tạo Dockerfile content
        dockerfile_lines = []

        # Stage 1: Build (nếu cần)
        if project_type in ["python", "node", "java", "go", "rust"]:
            dockerfile_lines.append(f"# Stage 1: Build dependencies")
            dockerfile_lines.append(f"FROM {base_image} AS builder")

            if project_type == "python":
                dockerfile_lines.extend([
                    f"WORKDIR /build",
                    f"COPY requirements.txt .",
                    f"RUN pip install --no-cache-dir --prefix=/install -r requirements.txt"
                ])
            elif project_type == "node":
                dockerfile_lines.extend([
                    f"WORKDIR /build",
                    f"COPY package*.json .",
                    f"RUN npm ci --only=production"
                ])
            elif project_type == "java":
                dockerfile_lines.extend([
                    f"WORKDIR /build",
                    f"COPY . .",
                    f"RUN javac *.java" if project_type == "java" else ""
                ])
            elif project_type == "go":
                dockerfile_lines.extend([
                    f"WORKDIR /build",
                    f"COPY go.mod go.sum .",
                    f"RUN go mod download",
                    f"COPY . .",
                    f"RUN CGO_ENABLED=0 GOOS=linux go build -o /app/main ."
                ])

            dockerfile_lines.append("")

        # Stage 2: Production
        dockerfile_lines.append(f"# Stage 2: Production image")
        dockerfile_lines.append(f"FROM {base_image.split('-slim')[0].split('-alpine')[0]}-slim AS production")

        # Working directory
        dockerfile_lines.append(f"")
        dockerfile_lines.append(f"# Cấu hình thư mục làm việc")
        dockerfile_lines.append(f"WORKDIR {working_dir}")

        # Copy dependencies từ builder stage (nếu có)
        if project_type in ["python", "node", "go"]:
            dockerfile_lines.append(f"")
            dockerfile_lines.append(f"# Copy dependencies từ builder")
            if project_type == "python":
                dockerfile_lines.append(f"COPY --from=builder /install /usr/local")
            elif project_type == "node":
                dockerfile_lines.append(f"COPY --from=builder /build/node_modules ./node_modules")
            elif project_type == "go":
                dockerfile_lines.append(f"COPY --from=builder /app/main .")

        # Copy source code
        dockerfile_lines.append(f"")
        dockerfile_lines.append(f"# Copy source code")
        if optimize_layers:
            # Tối ưu: copy dependency files trước, source sau
            if project_type == "python":
                dockerfile_lines.append(f"COPY requirements.txt .")
                dockerfile_lines.append(f"RUN pip install --no-cache-dir -r requirements.txt")
                dockerfile_lines.append(f"COPY . .")
            elif project_type == "node":
                dockerfile_lines.append(f"COPY package*.json .")
                dockerfile_lines.append(f"RUN npm ci --only=production")
                dockerfile_lines.append(f"COPY . .")
            else:
                dockerfile_lines.append(f"COPY . .")
        else:
            dockerfile_lines.append(f"COPY . .")

        # Install extra packages
        if extra_packages:
            dockerfile_lines.append(f"")
            dockerfile_lines.append(f"# Cài đặt packages bổ sung")
            if project_type in ["python", "generic"]:
                dockerfile_lines.append(f"RUN apt-get update && apt-get install -y --no-install-recommends \\")
                dockerfile_lines.append(f"    {' '.join(extra_packages)} \\")
                dockerfile_lines.append(f"    && rm -rf /var/lib/apt/lists/*")
            elif project_type == "node":
                dockerfile_lines.append(f"RUN apk add --no-cache {' '.join(extra_packages)}")

        # Expose port
        dockerfile_lines.append(f"")
        dockerfile_lines.append(f"# Expose port")
        dockerfile_lines.append(f"EXPOSE {port}")

        # Healthcheck
        if include_healthcheck:
            dockerfile_lines.append(f"")
            dockerfile_lines.append(f"# Healthcheck")
            if project_type == "python":
                dockerfile_lines.append(f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\")
                dockerfile_lines.append(f"    CMD python -c \"import sys; sys.exit(0)\" || exit 1")
            elif project_type == "node":
                dockerfile_lines.append(f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\")
                dockerfile_lines.append(f"    CMD node -e \"require('http').get('http://localhost:{port}', (r) => {{ process.exit(r.statusCode === 200 ? 0 : 1) }})\" || exit 1")
            else:
                dockerfile_lines.append(f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\")
                dockerfile_lines.append(f"    CMD curl -f http://localhost:{port}/health || exit 1")

        # Non-root user
        if include_non_root:
            dockerfile_lines.append(f"")
            dockerfile_lines.append(f"# Tạo non-root user")
            dockerfile_lines.append(f"RUN useradd -m -u 1000 appuser && \\")
            dockerfile_lines.append(f"    chown -R appuser:appuser {working_dir}")
            dockerfile_lines.append(f"USER appuser")

        # Default command
        dockerfile_lines.append(f"")
        dockerfile_lines.append(f"# Command mặc định")
        if project_type == "python":
            dockerfile_lines.append(f'CMD ["python", "main.py"]')
        elif project_type == "node":
            dockerfile_lines.append(f'CMD ["node", "index.js"]')
        elif project_type == "java":
            dockerfile_lines.append(f'CMD ["java", "-jar", "app.jar"]')
        elif project_type == "go":
            dockerfile_lines.append(f'CMD ["./main"]')
        else:
            dockerfile_lines.append(f'CMD ["echo", "Hello from {project_name}"]')

        dockerfile_content = "\n".join(dockerfile_lines)

        result = {
            "success": True,
            "project_type": project_type,
            "project_name": project_name,
            "base_image": base_image,
            "port": port,
            "dockerfile": dockerfile_content,
            "line_count": len(dockerfile_lines),
            "features": {
                "multi_stage": project_type in ["python", "node", "java", "go", "rust"],
                "healthcheck": include_healthcheck,
                "non_root": include_non_root,
                "layer_optimization": optimize_layers
            }
        }

        logger.info(
            "Tạo Dockerfile thành công",
            project_type=project_type,
            line_count=len(dockerfile_lines)
        )

        return result

    except Exception as e:
        logger.error("Lỗi tạo Dockerfile", project_type=project_type, error=str(e))
        raise MCPError(
            message=f"Không thể tạo Dockerfile: {str(e)}",
            code="DOCKERFILE_GENERATION_ERROR",
            details={"project_type": project_type, "project_name": project_name}
        )


# =============================================================================
# TOOL: TẠO DOCKER-COMPOSE.YML
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info(
        "Tạo docker-compose.yml",
        project_name=project_name,
        services_count=len(services)
    )

    try:
        import yaml

        # Build docker-compose structure
        compose = {
            "version": "3.8",
            "services": {},
            "volumes": {},
            "networks": {}
        }

        # Add services
        for service in services:
            service_name = service.get("name", "app")
            service_config = {
                "image": service.get("image", f"{project_name}-{service_name}:latest"),
                "build": service.get("build", "."),
                "restart": restart_policy,
                "ports": [f"{service.get('port', 8080)}:{service.get('port', 8080)}"],
                "environment": service.get("environment", {}),
                "volumes": service.get("volumes", []),
                "networks": service.get("networks", ["default"]),
                "healthcheck": service.get("healthcheck", {
                    "test": ["CMD", "curl", "-f", f"http://localhost:{service.get('port', 8080)}/health"],
                    "interval": "30s",
                    "timeout": "3s",
                    "retries": 3
                }) if service.get("include_healthcheck", True) else None
            }

            # Remove None values
            service_config = {k: v for k, v in service_config.items() if v is not None}

            compose["services"][service_name] = service_config

        # Add volumes
        if volumes:
            for vol in volumes:
                vol_name = vol.get("name", f"{project_name}-data")
                compose["volumes"][vol_name] = {"driver": "local"}

        # Add networks
        if networks:
            compose["networks"] = {net: {"driver": "bridge"} for net in networks}

        # Convert to YAML
        docker_compose_content = yaml.dump(
            compose,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
        )

        result = {
            "success": True,
            "project_name": project_name,
            "services": list(compose["services"].keys()),
            "volumes": list(compose["volumes"].keys()),
            "networks": list(compose["networks"].keys()),
            "docker_compose": docker_compose_content,
            "line_count": len(docker_compose_content.split('\n'))
        }

        logger.info(
            "Tạo docker-compose.yml thành công",
            project_name=project_name,
            services=len(compose["services"])
        )

        return result

    except Exception as e:
        logger.error("Lỗi tạo docker-compose.yml", project_name=project_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo docker-compose.yml: {str(e)}",
            code="DOCKER_COMPOSE_ERROR",
            details={"project_name": project_name}
        )


# =============================================================================
# TOOL: PHÂN TÍCH DOCKERFILE
# =============================================================================

@handle_exception
def analyze_dockerfile(file_path: str) -> Dict[str, Any]:
    """
    Phân tích Dockerfile và đưa ra đề xuất cải thiện

    Args:
        file_path: Đường dẫn Dockerfile

    Returns:
        Dict chứa phân tích và đề xuất

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Phân tích Dockerfile", file_path=file_path)

    try:
        content = read_file_safe(file_path)
        lines = content.split('\n')

        issues = []
        suggestions = []
        best_practices = []

        # Check for multi-stage build
        has_multi_stage = "FROM" in content and content.count("FROM") > 1
        if not has_multi_stage:
            suggestions.append({
                "priority": "high",
                "message": "Sử dụng multi-stage build để giảm kích thước image",
                "suggestion": "Tách build stage và production stage"
            })

        # Check for non-root user
        has_non_root = "USER" in content and "root" not in content
        if not has_non_root:
            issues.append({
                "severity": "high",
                "message": "Đang chạy với root user",
                "suggestion": "Tạo non-root user với USER directive"
            })

        # Check for HEALTHCHECK
        has_healthcheck = "HEALTHCHECK" in content
        if not has_healthcheck:
            suggestions.append({
                "priority": "medium",
                "message": "Thiếu HEALTHCHECK",
                "suggestion": "Thêm HEALTHCHECK để monitor container health"
            })

        # Check for layer optimization
        has_layer_optimization = (
            "COPY requirements.txt" in content or
            "COPY package*.json" in content or
            "COPY go.mod" in content
        )
        if not has_layer_optimization:
            suggestions.append({
                "priority": "medium",
                "message": "Chưa tối ưu layer caching",
                "suggestion": "Copy dependency files trước, source code sau"
            })

        # Check for cache cleanup
        has_cache_cleanup = (
            "rm -rf /var/lib/apt/lists/*" in content or
            "npm cache clean" in content or
            "pip cache" in content
        )
        if not has_cache_cleanup:
            suggestions.append({
                "priority": "low",
                "message": "Chưa cleanup package cache",
                "suggestion": "Xóa package cache để giảm kích thước image"
            })

        # Check for specific base images
        uses_slim = "slim" in content or "alpine" in content
        if not uses_slim:
            suggestions.append({
                "priority": "high",
                "message": "Sử dụng base image lớn",
                "suggestion": "Sử dụng slim hoặc alpine variants"
            })

        # Best practices
        best_practices.append("Sử dụng .dockerignore để bỏ qua file không cần thiết")
        best_practices.append("Pin version của base image (ví dụ: python:3.12.1-slim)")
        best_practices.append("Sử dụng COPY thay vì ADD trừ khi cần extract tar")
        best_practices.append("Combine RUN commands để giảm số layers")
        best_practices.append("Sử dụng ENV cho configuration")

        result = {
            "success": True,
            "file_path": file_path,
            "total_lines": len(lines),
            "has_multi_stage": has_multi_stage,
            "has_non_root": has_non_root,
            "has_healthcheck": has_healthcheck,
            "has_layer_optimization": has_layer_optimization,
            "issues": issues,
            "suggestions": suggestions,
            "best_practices": best_practices,
            "score": _calculate_dockerfile_score(has_multi_stage, has_non_root, has_healthcheck, has_layer_optimization)
        }

        logger.info(
            "Phân tích Dockerfile thành công",
            file_path=file_path,
            issues=len(issues),
            suggestions=len(suggestions),
            score=result["score"]
        )

        return result

    except Exception as e:
        logger.error("Lỗi phân tích Dockerfile", file_path=file_path, error=str(e))
        raise MCPError(
            message=f"Không thể phân tích Dockerfile: {str(e)}",
            code="DOCKERFILE_ANALYSIS_ERROR",
            details={"file_path": file_path}
        )


def _calculate_dockerfile_score(has_multi_stage: bool, has_non_root: bool,
                                has_healthcheck: bool, has_layer_optimization: bool) -> int:
    """Tính điểm Dockerfile (0-100)"""
    score = 0
    if has_multi_stage:
        score += 30
    if has_non_root:
        score += 30
    if has_healthcheck:
        score += 20
    if has_layer_optimization:
        score += 20

    return score


# =============================================================================
# TOOL: TẠO .DOCKERIGNORE
# =============================================================================

@handle_exception
def generate_dockerignore(project_type: str = "generic") -> Dict[str, Any]:
    """
    Tạo file .dockerignore tối ưu

    Args:
        project_type: Loại dự án

    Returns:
        Dict chứa nội dung .dockerignore

    Raises:
        MCPError: Nếu có lỗi
    """
    logger.info("Tạo .dockerignore", project_type=project_type)

    try:
        # Common ignores
        dockerignore_lines = [
            "# Git",
            ".git",
            ".github",
            ".gitignore",
            "",
            "# IDE",
            ".vscode",
            ".idea",
            "*.swp",
            "*.swo",
            "*~",
            "",
            "# OS",
            ".DS_Store",
            "Thumbs.db",
            "",
            "# Docker",
            "Dockerfile",
            "docker-compose*.yml",
            ".dockerignore",
            "",
            "# Documentation",
            "*.md",
            "LICENSE",
            "docs/",
            "",
            "# Tests (nếu không cần chạy trong production)",
            "tests/",
            "test/",
            "*.test.js",
            "*.test.py",
            "*.spec.js",
            "*.spec.py",
            "",
            "# Development files",
            "*.log",
            "*.tmp",
            ".env.local",
            ".env.development",
            "",
            "# Node modules",
            "node_modules/",
            "npm-debug.log",
            "",
            "# Python",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            ".venv/",
            "venv/",
            "env/",
            "",
            "# Java",
            "target/",
            "*.class",
            "*.jar",
            "*.war",
            "",
            "# Go",
            "vendor/",
            "",
            "# Build outputs",
            "dist/",
            "build/",
            "out/",
            "bin/",
            "target/",
            "",
            "# IDE specific",
            "*.iml",
            ".project",
            ".classpath",
            ".settings/"
        ]

        # Add project-specific ignores
        if project_type == "python":
            dockerignore_lines.extend([
                "",
                "# Python specific",
                ".python-version",
                "pip-log.txt",
                "pip-delete-this-directory.txt",
                ".tox/",
                ".eggs/"
            ])
        elif project_type == "node":
            dockerignore_lines.extend([
                "",
                "# Node specific",
                "package-lock.json",
                "yarn.lock",
                ".npm",
                ".node-gyp"
            ])
        elif project_type == "java":
            dockerignore_lines.extend([
                "",
                "# Java specific",
                "*.iml",
                ".gradle/",
                "build/"
            ])

        dockerignore_content = "\n".join(dockerignore_lines)

        result = {
            "success": True,
            "project_type": project_type,
            "dockerignore": dockerignore_content,
            "line_count": len(dockerignore_lines)
        }

        logger.info("Tạo .dockerignore thành công", line_count=len(dockerignore_lines))

        return result

    except Exception as e:
        logger.error("Lỗi tạo .dockerignore", error=str(e))
        raise MCPError(
            message=f"Không thể tạo .dockerignore: {str(e)}",
            code="DOCKERIGNORE_ERROR"
        )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "generate_dockerfile",
    "generate_docker_compose",
    "analyze_dockerfile",
    "generate_dockerignore"
]