"""
MCP Programming Support Server - Công cụ Documentation
Quản lý hướng dẫn, đọc và cập nhật tài liệu
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import re

from config import get_settings
from utils import get_logger, MCPError, handle_exception, read_file_safe, write_file_safe

logger = get_logger()


# =============================================================================
# TOOL: ĐỌC HƯỚNG DẪN
# =============================================================================

@handle_exception
def read_guide(guide_name: str, guide_dir: str = "guides") -> Dict[str, Any]:
    """
    Đọc file hướng dẫn

    Args:
        guide_name: Tên file hướng dẫn (ví dụ: "minecraft-plugin-guide.md")
        guide_dir: Thư mục chứa hướng dẫn

    Returns:
        Dict chứa nội dung hướng dẫn

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Đọc hướng dẫn", guide_name=guide_name, guide_dir=guide_dir)

    try:
        # Tìm file hướng dẫn
        guide_path = settings.get_workspace_path(guide_dir, guide_name)

        if not guide_path.exists():
            # Thử tìm với .md extension
            if not guide_name.endswith(".md"):
                guide_path_md = settings.get_workspace_path(guide_dir, f"{guide_name}.md")
                if guide_path_md.exists():
                    guide_path = guide_path_md

        if not guide_path.exists():
            raise MCPError(
                message=f"Không tìm thấy hướng dẫn: {guide_name}",
                code="GUIDE_NOT_FOUND",
                details={"guide_name": guide_name, "guide_dir": guide_dir}
            )

        # Đọc file
        content = read_file_safe(str(guide_path))

        # Parse metadata (nếu có)
        metadata = _parse_guide_metadata(content)

        result = {
            "success": True,
            "guide_name": guide_name,
            "guide_path": str(guide_path.relative_to(settings.workspace)),
            "content": content,
            "metadata": metadata,
            "line_count": len(content.split('\n')),
            "char_count": len(content)
        }

        logger.info("Đọc hướng dẫn thành công", guide_name=guide_name)

        return result

    except Exception as e:
        logger.error("Lỗi đọc hướng dẫn", guide_name=guide_name, error=str(e))
        raise MCPError(
            message=f"Không thể đọc hướng dẫn: {str(e)}",
            code="GUIDE_READ_ERROR",
            details={"guide_name": guide_name}
        )


def _parse_guide_metadata(content: str) -> Dict[str, Any]:
    """Parse metadata từ YAML frontmatter"""
    metadata = {}

    # Check for YAML frontmatter
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            frontmatter = content[3:end_idx]
            # Simple parsing (không dùng yaml parser để tránh dependencies)
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

    return metadata


# =============================================================================
# TOOL: CẬP NHẬT HƯỚNG DẪN
# =============================================================================

@handle_exception
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
            - content: Nội dung mới (thay thế toàn bộ)
            - section: Section cần cập nhật
            - lessons_learned: Bài học kinh nghiệm mới
            - append: Nội dung thêm vào cuối
        guide_dir: Thư mục chứa hướng dẫn
        create_if_not_exists: Tạo file mới nếu chưa tồn tại
        append_section: Thêm section mới vào cuối

    Returns:
        Dict chứa kết quả cập nhật

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info("Cập nhật hướng dẫn", guide_name=guide_name, updates=list(updates.keys()))

    try:
        guide_path = settings.get_workspace_path(guide_dir, guide_name)

        # Đọc nội dung hiện tại hoặc tạo mới
        if guide_path.exists():
            content = read_file_safe(str(guide_path))
            logger.info("Đọc hướng dẫn hiện tại", guide_name=guide_name)
        else:
            if not create_if_not_exists:
                raise MCPError(
                    message=f"Hướng dẫn không tồn tại: {guide_name}",
                    code="GUIDE_NOT_FOUND"
                )

            # Tạo file mới
            content = f"# {guide_name}\n\n"
            content += f"*Tạo lúc: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            logger.info("Tạo hướng dẫn mới", guide_name=guide_name)

        # Áp dụng updates
        changes_made = []

        # Update toàn bộ content
        if "content" in updates:
            new_content = updates["content"]
            if new_content != content:
                content = new_content
                changes_made.append("Cập nhật toàn bộ nội dung")

        # Update section cụ thể
        if "section" in updates:
            section_data = updates["section"]
            section_name = section_data.get("name", "")
            section_content = section_data.get("content", "")

            if section_name and section_content:
                content = _update_section(content, section_name, section_content)
                changes_made.append(f"Cập nhật section: {section_name}")

        # Thêm lessons learned
        if "lessons_learned" in updates:
            lessons = updates["lessons_learned"]
            if isinstance(lessons, list):
                content = _append_lessons_learned(content, lessons)
                changes_made.append(f"Thêm {len(lessons)} bài học kinh nghiệm")
            elif isinstance(lessons, str):
                content = _append_lessons_learned(content, [lessons])
                changes_made.append("Thêm bài học kinh nghiệm")

        # Append content
        if "append" in updates:
            append_content = updates["append"]
            content = content.rstrip() + "\n\n" + append_content
            changes_made.append("Thêm nội dung vào cuối")

        # Cập nhật metadata
        if "metadata" in updates:
            content = _update_metadata(content, updates["metadata"])
            changes_made.append("Cập nhật metadata")

        # Ghi file
        write_file_safe(str(guide_path), content)

        result = {
            "success": True,
            "guide_name": guide_name,
            "guide_path": str(guide_path.relative_to(settings.workspace)),
            "changes_made": changes_made,
            "total_changes": len(changes_made),
            "new_line_count": len(content.split('\n')),
            "updated_at": datetime.now().isoformat()
        }

        logger.info(
            "Cập nhật hướng dẫn thành công",
            guide_name=guide_name,
            changes=len(changes_made)
        )

        return result

    except Exception as e:
        logger.error("Lỗi cập nhật hướng dẫn", guide_name=guide_name, error=str(e))
        raise MCPError(
            message=f"Không thể cập nhật hướng dẫn: {str(e)}",
            code="GUIDE_UPDATE_ERROR",
            details={"guide_name": guide_name}
        )


def _update_section(content: str, section_name: str, section_content: str) -> str:
    """Cập nhật section trong markdown"""
    # Tìm section hiện tại
    section_pattern = rf"(## {re.escape(section_name)}.*?)(?=## |\Z)"
    match = re.search(section_pattern, content, re.DOTALL | re.IGNORECASE)

    if match:
        # Replace section
        new_section = f"## {section_name}\n\n{section_content}\n"
        content = content[:match.start()] + new_section + content[match.end():]
    else:
        # Thêm section mới vào cuối
        content = content.rstrip() + f"\n\n## {section_name}\n\n{section_content}\n"

    return content


def _append_lessons_learned(content: str, lessons: List[str]) -> str:
    """Thêm section 'Bài học kinh nghiệm' vào cuối"""
    lessons_section = "\n\n## Bài học kinh nghiệm\n\n"

    # Kiểm tra xem đã có section chưa
    if "## Bài học kinh nghiệm" in content or "## Lessons Learned" in content:
        # Tìm và append vào section hiện tại
        pattern = r"(## (Bài học kinh nghiệm|Lessons Learned).*?)(?=## |\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            # Append lessons vào section hiện tại
            current_section = match.group(1)
            new_lessons = "\n".join([f"- {lesson}" for lesson in lessons])
            updated_section = current_section.rstrip() + "\n" + new_lessons
            content = content[:match.start()] + updated_section + content[match.end():]
        else:
            # Thêm section mới
            content = content.rstrip() + lessons_section + "\n".join([f"- {lesson}" for lesson in lessons])
    else:
        # Thêm section mới
        content = content.rstrip() + lessons_section + "\n".join([f"- {lesson}" for lesson in lessons])

    return content


def _update_metadata(content: str, metadata: Dict[str, str]) -> str:
    """Cập nhật metadata trong YAML frontmatter"""
    # Kiểm tra xem có frontmatter không
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            # Update existing frontmatter
            frontmatter = content[3:end_idx]
            rest = content[end_idx + 3:]

            for key, value in metadata.items():
                if f"{key}:" in frontmatter:
                    # Update existing
                    frontmatter = re.sub(rf"{key}:.*", f"{key}: {value}", frontmatter)
                else:
                    # Add new
                    frontmatter = frontmatter.rstrip() + f"\n{key}: {value}\n"

            return f"---{frontmatter}---{rest}"

    # Tạo frontmatter mới
    frontmatter = "---\n"
    for key, value in metadata.items():
        frontmatter += f"{key}: {value}\n"
    frontmatter += "---\n\n"

    return frontmatter + content


# =============================================================================
# TOOL: TẠO HƯỚNG DẪN MỚI
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info("Tạo hướng dẫn mới", guide_name=guide_name, title=title)

    try:
        # Đảm bảo guide_dir tồn tại
        guide_path_dir = settings.get_workspace_path(guide_dir)
        guide_path_dir.mkdir(parents=True, exist_ok=True)

        # Tạo file path
        if not guide_name.endswith(".md"):
            guide_name = f"{guide_name}.md"

        guide_path = guide_path_dir / guide_name

        # Tạo nội dung với metadata
        frontmatter = f"---\n"
        frontmatter += f"title: {title}\n"
        frontmatter += f"category: {category}\n"
        frontmatter += f"created_at: {datetime.now().isoformat()}\n"
        frontmatter += f"updated_at: {datetime.now().isoformat()}\n"
        if tags:
            frontmatter += f"tags: {', '.join(tags)}\n"
        frontmatter += f"---\n\n"

        full_content = frontmatter + content

        # Ghi file
        write_file_safe(str(guide_path), full_content)

        result = {
            "success": True,
            "guide_name": guide_name,
            "guide_path": str(guide_path.relative_to(settings.workspace)),
            "title": title,
            "category": category,
            "tags": tags or [],
            "line_count": len(full_content.split('\n')),
            "created_at": datetime.now().isoformat()
        }

        logger.info("Tạo hướng dẫn thành công", guide_name=guide_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo hướng dẫn", guide_name=guide_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo hướng dẫn: {str(e)}",
            code="GUIDE_CREATE_ERROR",
            details={"guide_name": guide_name}
        )


# =============================================================================
# TOOL: LIỆT KÊ HƯỚNG DẪN
# =============================================================================

@handle_exception
def list_guides(guide_dir: str = "guides", category: Optional[str] = None) -> Dict[str, Any]:
    """
    Liệt kê tất cả hướng dẫn

    Args:
        guide_dir: Thư mục chứa hướng dẫn
        category: Lọc theo danh mục

    Returns:
        Dict chứa danh sách hướng dẫn

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Liệt kê hướng dẫn", guide_dir=guide_dir, category=category)

    try:
        guide_path = settings.get_workspace_path(guide_dir)

        if not guide_path.exists():
            return {
                "success": True,
                "guides": [],
                "total": 0,
                "guide_dir": guide_dir
            }

        guides = []

        for guide_file in guide_path.glob("*.md"):
            try:
                content = read_file_safe(str(guide_file))
                metadata = _parse_guide_metadata(content)

                # Filter by category
                if category and metadata.get("category") != category:
                    continue

                guides.append({
                    "name": guide_file.name,
                    "path": str(guide_file.relative_to(settings.workspace)),
                    "title": metadata.get("title", guide_file.stem),
                    "category": metadata.get("category", "general"),
                    "tags": metadata.get("tags", "").split(", ") if metadata.get("tags") else [],
                    "created_at": metadata.get("created_at", ""),
                    "updated_at": metadata.get("updated_at", ""),
                    "line_count": len(content.split('\n'))
                })
            except Exception as e:
                logger.warning("Lỗi đọc guide", guide_file=guide_file.name, error=str(e))
                continue

        # Sort by updated_at
        guides.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        result = {
            "success": True,
            "guides": guides,
            "total": len(guides),
            "guide_dir": guide_dir,
            "category_filter": category
        }

        logger.info("Liệt kê hướng dẫn thành công", total=len(guides))

        return result

    except Exception as e:
        logger.error("Lỗi liệt kê hướng dẫn", guide_dir=guide_dir, error=str(e))
        raise MCPError(
            message=f"Không thể liệt kê hướng dẫn: {str(e)}",
            code="GUIDE_LIST_ERROR",
            details={"guide_dir": guide_dir}
        )


# =============================================================================
# TOOL: TRÍCH XUẤT BÀI HỌC KINH NGHIỆM
# =============================================================================

@handle_exception
def extract_lessons(guide_name: str, guide_dir: str = "guides") -> Dict[str, Any]:
    """
    Trích xuất bài học kinh nghiệm từ hướng dẫn

    Args:
        guide_name: Tên file hướng dẫn
        guide_dir: Thư mục chứa hướng dẫn

    Returns:
        Dict chứa các bài học kinh nghiệm

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Trích xuất bài học kinh nghiệm", guide_name=guide_name)

    try:
        # Đọc guide
        guide_result = read_guide(guide_name, guide_dir)
        content = guide_result["content"]

        # Tìm section "Bài học kinh nghiệm" hoặc "Lessons Learned"
        lessons = []

        # Pattern 1: ## Bài học kinh nghiệm
        pattern1 = r"## (Bài học kinh nghiệm|Lessons Learned)\s*\n(.*?)(?=## |\Z)"
        match1 = re.search(pattern1, content, re.DOTALL | re.IGNORECASE)

        if match1:
            lessons_text = match1.group(2)
            # Parse bullet points
            for line in lessons_text.split('\n'):
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    lessons.append(line[2:])

        # Pattern 2: Tìm trong toàn bộ content
        if not lessons:
            # Tìm các dòng có dạng "Bài học:" hoặc "Lesson:"
            lesson_pattern = r"[-*]\s*(Bài học|Lesson|Kinh nghiệm):\s*(.+)"
            matches = re.findall(lesson_pattern, content, re.IGNORECASE)
            for match in matches:
                lessons.append(match[1] if len(match) > 1 else match[0])

        result = {
            "success": True,
            "guide_name": guide_name,
            "lessons_count": len(lessons),
            "lessons": lessons,
            "has_lessons_section": len(lessons) > 0
        }

        logger.info("Trích xuất bài học thành công", guide_name=guide_name, lessons=len(lessons))

        return result

    except Exception as e:
        logger.error("Lỗi trích xuất bài học", guide_name=guide_name, error=str(e))
        raise MCPError(
            message=f"Không thể trích xuất bài học: {str(e)}",
            code="LESSONS_EXTRACT_ERROR",
            details={"guide_name": guide_name}
        )


# =============================================================================
# TOOL: TẠO TEMPLATE HƯỚNG DẪN
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    logger.info("Tạo template hướng dẫn", template_type=template_type, title=title)

    try:
        templates = {
            "minecraft-plugin": _get_minecraft_plugin_template,
            "xianxia-system": _get_xianxia_system_template,
            "general": _get_general_template
        }

        template_func = templates.get(template_type)
        if not template_func:
            raise MCPError(
                message=f"Template type không hỗ trợ: {template_type}",
                code="UNSUPPORTED_TEMPLATE",
                details={"supported": list(templates.keys())}
            )

        content = template_func(title)

        # Generate guide name nếu không có
        if not guide_name:
            from utils import slugify_vietnamese
            guide_name = f"{slugify_vietnamese(title)}.md"

        result = {
            "success": True,
            "template_type": template_type,
            "guide_name": guide_name,
            "title": title,
            "content": content,
            "line_count": len(content.split('\n'))
        }

        logger.info("Tạo template thành công", template_type=template_type)

        return result

    except Exception as e:
        logger.error("Lỗi tạo template", template_type=template_type, error=str(e))
        raise MCPError(
            message=f"Không thể tạo template: {str(e)}",
            code="TEMPLATE_CREATE_ERROR",
            details={"template_type": template_type}
        )


def _get_minecraft_plugin_template(title: str) -> str:
    """Template cho hướng dẫn Minecraft plugin"""
    return f"""---
title: {title}
category: minecraft
created_at: {datetime.now().isoformat()}
tags: minecraft, plugin, paper, spigot
---

# {title}

## Tổng quan

Mô tả ngắn gọn về plugin này.

## Chức năng chính

- Chức năng 1
- Chức năng 2
- Chức năng 3

## Cấu trúc dự án

```
src/
├── main/
│   ├── java/
│   │   └── com/example/plugin/
│   │       ├── Main.java
│   │       ├── commands/
│   │       ├── listeners/
│   │       └── managers/
│   └── resources/
│       └── plugin.yml
└── test/
```

## Cài đặt

1. Clone repository
2. Build với Maven/Gradle
3. Copy jar vào thư mục `plugins/` của Paper server

## Cách sử dụng

### Commands

- `/plugin command1` - Mô tả
- `/plugin command2` - Mô tả

### Configuration

Mô tả file config.yml

## API Reference

Tài liệu API nếu có

## Troubleshooting

### Lỗi thường gặp

**Lỗi 1**: Mô tả lỗi
- **Nguyên nhân**: Lý do
- **Giải pháp**: Cách fix

## Bài học kinh nghiệm

- Bài học 1
- Bài học 2
"""


def _get_xianxia_system_template(title: str) -> str:
    """Template cho hệ thống tu tiên"""
    return f"""---
title: {title}
category: xianxia
created_at: {datetime.now().isoformat()}
tags: tu-tien, cultivation, minecraft, rpg
---

# {title}

## Tổng quan

Mô tả hệ thống tu tiên này.

## Cảnh giới tu luyện

### Cảnh giới thường

1. **Luyện Khí** (Qi Refining)
   - Mô tả
   - Yêu cầu: ...
   - Sức mạnh: ...

2. **Trúc Cơ** (Foundation Building)
   - Mô tả
   - Yêu cầu: ...
   - Sức mạnh: ...

### Cảnh giới cao cấp

3. **Kim Đan** (Golden Core)
   - ...

## Hệ thống tu luyện

### Công pháp

- **Công pháp thường**: ...
- **Công pháp cao cấp**: ...
- **Công pháp thần thoại**: ...

### Tài nguyên tu luyện

- Linh thạch
- Đan dược
- Tài liệu luyện khí

## Hệ thống vật phẩm

### Pháp bảo

- **Kiếm pháp bảo**: ...
- **Trận bàn**: ...
- **Pháp y**: ...

### Đan dược

- **Đan dược phục dụng**: ...
- **Đan dược đột phá**: ...

## Hệ thống kỹ năng

### Kỹ năng tu luyện

- **Thiên phú**: ...
- **Công pháp**: ...

### Kỹ năng chiến đấu

- **Kiếm thuật**: ...
- **Pháp thuật**: ...

## Hệ thống môn phái

### Môn phái chính

- **Môn phái chính**: ...
- **Môn phái phụ**: ...

## Thế giới tu tiên

### Bí cảnh

- **Bí cảnh cấp thấp**: ...
- **Bí cảnh cấp cao**: ...

### Linh mạch

- **Linh mạch hạ đẳng**: ...
- **Linh mạch thượng đẳng**: ...

## Cân bằng game

### Tỷ lệ tu luyện

- Tốc độ tu luyện cơ bản
- Tỷ lệ đột phá
- Hệ số nhân

### Kinh nghiệm

- Kinh nghiệm chiến đấu
- Kinh nghiệm tu luyện

## Bài học kinh nghiệm

- Bài học 1
- Bài học 2
"""


def _get_general_template(title: str) -> str:
    """Template chung"""
    return f"""---
title: {title}
category: general
created_at: {datetime.now().isoformat()}
---

# {title}

## Mục đích

Mô tả mục đích của hướng dẫn này.

## Nội dung

### Phần 1

Nội dung phần 1

### Phần 2

Nội dung phần 2

## Ví dụ

Ví dụ code hoặc hình ảnh

## Best Practices

- Best practice 1
- Best practice 2

## Troubleshooting

### Lỗi thường gặp

**Lỗi 1**: Mô tả
- **Giải pháp**: Cách fix

## Bài học kinh nghiệm

- Bài học 1
- Bài học 2
"""


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "read_guide",
    "update_guide",
    "create_guide",
    "list_guides",
    "extract_lessons",
    "create_guide_template"
]