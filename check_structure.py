#!/usr/bin/env python3
"""
Script kiểm tra cấu trúc dự án MCP Programming Support Server
Chạy script này để đảm bảo tất cả file đã được tạo đúng
"""

from pathlib import Path
from typing import List, Tuple

def check_project_structure() -> Tuple[bool, List[str]]:
    """
    Kiểm tra cấu trúc dự án có đầy đủ các file cần thiết không

    Returns:
        Tuple[bool, List[str]]: (is_complete, missing_files)
    """
    required_files = [
        # Root files
        "requirements.txt",
        ".env.example",
        ".dockerignore",
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
        "config.py",
        "server.py",
        "utils.py",
        
        # Tools package
        "tools/__init__.py",
        "tools/filesystem.py",
        "tools/github.py",
        "tools/search.py",
        "tools/review.py",
        "tools/shell.py",
        "tools/docker_tools.py",
        "tools/docs.py",
        
        # Minecraft tools
        "tools/minecraft/__init__.py",
        "tools/minecraft/paper_reference.py",
        "tools/minecraft/plugin_builder.py",
        "tools/minecraft/xianxia_generator.py",
        
        # Directories
        "logs/__init__.py",
        "workspace/__init__.py",
    ]

    missing_files = []
    project_root = Path(__file__).parent

    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    is_complete = len(missing_files) == 0
    return is_complete, missing_files


def main():
    """Main function"""
    print("🔍 Kiểm tra cấu trúc dự án MCP Programming Support Server...")
    print("=" * 70)

    is_complete, missing_files = check_project_structure()

    if is_complete:
        print("✅ Tất cả file đã được tạo đầy đủ!")
        print("\n📦 Cấu trúc dự án:")
        print("   - Root files: 9 files")
        print("   - Tools: 7 modules")
        print("   - Minecraft tools: 3 modules")
        print("   - Directories: 2 (logs/, workspace/)")
        print("\n🚀 Server đã sẵn sàng để build và chạy!")
        print("\nTiếp theo:")
        print("  1. docker-compose build")
        print("  2. docker-compose up -d")
        print("  3. docker-compose logs -f mcp-server")
        return 0
    else:
        print(f"❌ Thiếu {len(missing_files)} file:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n⚠️  Vui lòng tạo các file thiếu trước khi chạy server.")
        return 1


if __name__ == "__main__":
    exit(main())