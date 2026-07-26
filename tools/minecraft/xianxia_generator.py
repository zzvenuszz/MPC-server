"""
MCP Programming Support Server - Xianxia Cultivation Generator
Công cụ tạo hệ thống tu tiên (cultivation) cho Minecraft
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import random

from config import get_settings
from utils import get_logger, MCPError, handle_exception

logger = get_logger()


# =============================================================================
# TOOL: TÌM KIẾM CỐT TRUYỆN TU TIÊN
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Tìm kiếm cốt truyện tu tiên", query=query, max_results=max_results)

    try:
        # Database của các cốt truyện và hệ thống tu tiên phổ biến
        cultivation_database = [
            {
                "title": "Tiên Nghịch (Reverend Insanity)",
                "author": "Cửu Nặc Ngã Tư",
                "realms": ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Đại Thừa", "Diệu Phong"],
                "key_features": [
                    "Hệ thống Ngũ Hành (Kim, Mộc, Thủy, Hỏa, Thổ)",
                    "Côn Lôn Ngũ Hành Ấn",
                    "Thiên Địa Hồn",
                    "Hồn Thú",
                    "Trùng Sinh"
                ],
                "cultivation_speed": "chậm",
                "difficulty": "cao",
                "tags": ["dark", "philosophical", "anti-hero"]
            },
            {
                "title": "Ngã Duyên Phật Môn (Buddha's Palm)",
                "author": "Tịch Yên",
                "realms": ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Đại Thừa", "Đại La Kim Tiên"],
                "key_features": [
                    "Phật Môn Công Pháp",
                    "Thiên Thủ Ấn",
                    "Phật Đà",
                    "Tâm Ấn",
                    "Thiện Nghiệp"
                ],
                "cultivation_speed": "trung bình",
                "difficulty": "trung bình",
                "tags": ["buddhist", "philosophical", "balanced"]
            },
            {
                "title": "Vũ Trụ Của Ta (My Cosmic Aspirations)",
                "author": "Vũ Trụ Của Ta",
                "realms": ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Đại Thừa", "Tiên Vương", "Tiên Đế"],
                "key_features": [
                    "Hệ thống Vũ Trụ",
                    "Tinh Vực",
                    "Thiên Đạo",
                    "Hồn Thú",
                    "Luyện Khí Sư"
                ],
                "cultivation_speed": "nhanh",
                "difficulty": "thấp",
                "tags": ["action", "adventure", "fast-paced"]
            },
            {
                "title": "Đấu Phá Thương Khung (Battle Through the Heavens)",
                "author": "Thiên Tân Tuyết",
                "realms": ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Đại Thừa", "Bất Tử", "Vấn Đỉnh"],
                "key_features": [
                    "Dị Năng (Hỏa Diễm)",
                    "Luyện Đan",
                    "Luyện Khí",
                    "Hồn Thú",
                    "Bí Cảnh"
                ],
                "cultivation_speed": "nhanh",
                "difficulty": "thấp",
                "tags": ["action", "comedy", "alchemy"]
            },
            {
                "title": "Bách Luyện Thành Tiên (I Shall Seal the Heavens)",
                "author": "Er Gen",
                "realms": ["Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần", "Luyện Hư", "Đại Thừa", "Tẩy Tủy", "Thoát Thai", "Anh Biến", "Ly Dị", "Hợp Thể", "Đại Thừa", "Chân Tiên", "Kim Tiên", "Đại La Kim Tiên", "Tiên Vương", "Tiên Đế", "Minh Vương", "Đạo Tổ"],
                "key_features": [
                    "Bách Luyện Trận",
                    "Thất Tinh Đảo",
                    "Hồn Thú",
                    "Đạo Cảnh",
                    "Thiên Địa"
                ],
                "cultivation_speed": "rất chậm",
                "difficulty": "rất cao",
                "tags": ["epic", "philosophical", "long-running"]
            }
        ]

        # Tìm kiếm
        query_lower = query.lower()
        results = []

        for story in cultivation_database:
            score = 0
            matched_features = []

            # Check title
            if query_lower in story["title"].lower():
                score += 10

            # Check author
            if query_lower in story["author"].lower():
                score += 5

            # Check realms
            for realm in story["realms"]:
                if query_lower in realm.lower():
                    score += 3
                    matched_features.append(realm)

            # Check key features
            for feature in story["key_features"]:
                if query_lower in feature.lower():
                    score += 2
                    matched_features.append(feature)

            # Check tags
            for tag in story["tags"]:
                if query_lower in tag.lower():
                    score += 1

            if score > 0:
                result = {
                    "title": story["title"],
                    "author": story["author"],
                    "realms": story["realms"],
                    "key_features": story["key_features"],
                    "cultivation_speed": story["cultivation_speed"],
                    "difficulty": story["difficulty"],
                    "tags": story["tags"],
                    "relevance_score": score,
                    "matched_features": matched_features
                }

                if include_summary:
                    result["summary"] = _generate_story_summary(story)

                results.append(result)

        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)

        final_result = {
            "success": True,
            "query": query,
            "total_found": len(results),
            "results": results[:max_results]
        }

        logger.info("Tìm kiếm cốt truyện thành công", query=query, results=len(results))

        return final_result

    except Exception as e:
        logger.error("Lỗi tìm kiếm cốt truyện", query=query, error=str(e))
        raise MCPError(
            message=f"Không thể tìm kiếm cốt truyện: {str(e)}",
            code="STORY_SEARCH_ERROR",
            details={"query": query}
        )


def _generate_story_summary(story: Dict[str, Any]) -> str:
    """Tạo tóm tắt cho cốt truyện"""
    summary = f"'{story['title']}' của {story['author']} là một bộ tiểu thuyết tu tiên "
    summary += f"với {len(story['realms'])} cảnh giới tu luyện. "
    summary += f"Tốc độ tu luyện {story['cultivation_speed']}, độ khó {story['difficulty']}. "
    summary += f"Các đặc điểm nổi bật: {', '.join(story['key_features'][:3])}."
    return summary


# =============================================================================
# TOOL: TẠO HỆ THỐNG CẢNH GIỚI
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Tạo hệ thống cảnh giới", system_name=system_name, realm_count=realm_count)

    try:
        # Giới hạn realm_count
        realm_count = max(3, min(12, realm_count))

        # Difficulty multipliers
        difficulty_config = {
            "easy": {"breakthrough_chance": 0.8, "resource_multiplier": 0.5, "time_multiplier": 0.5},
            "medium": {"breakthrough_chance": 0.6, "resource_multiplier": 1.0, "time_multiplier": 1.0},
            "hard": {"breakthrough_chance": 0.4, "resource_multiplier": 1.5, "time_multiplier": 1.5},
            "extreme": {"breakthrough_chance": 0.2, "resource_multiplier": 2.0, "time_multiplier": 2.0}
        }

        config = difficulty_config.get(difficulty, difficulty_config["medium"])

        # Generate realms
        realms = _generate_realms(realm_count, include_sub_realms, config)

        # Generate breakthrough mechanic
        breakthrough = None
        if include_breakthrough_mechanic:
            breakthrough = _generate_breakthrough_mechanic(difficulty, config)

        result = {
            "success": True,
            "system_name": system_name,
            "difficulty": difficulty,
            "total_main_realms": realm_count,
            "total_sub_realms": sum(len(r.get("sub_realms", [])) for r in realms),
            "realms": realms,
            "breakthrough_mechanic": breakthrough,
            "config": config
        }

        logger.info("Tạo hệ thống cảnh giới thành công", system_name=system_name, realms=realm_count)

        return result

    except Exception as e:
        logger.error("Lỗi tạo hệ thống cảnh giới", system_name=system_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo hệ thống cảnh giới: {str(e)}",
            code="CULTIVATION_SYSTEM_ERROR"
        )


def _generate_realms(count: int, include_sub_realms: bool, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Tạo danh sách cảnh giới"""
    realm_names = [
        "Luyện Khí", "Trúc Cơ", "Kim Đan", "Nguyên Anh", "Hóa Thần",
        "Luyện Hư", "Đại Thừa", "Bất Tử", "Vấn Đỉnh", "Chân Tiên",
        "Kim Tiên", "Đại La"
    ]

    realms = []
    for i in range(count):
        realm_name = realm_names[i] if i < len(realm_names) else f"Cảnh Giới {i+1}"

        realm = {
            "level": i + 1,
            "name": realm_name,
            "name_vn": realm_name,
            "power_multiplier": (i + 1) * 10,
            "required_cultivation": (i + 1) * 1000,
            "breakthrough_chance": config["breakthrough_chance"] - (i * 0.05),
            "description": f"Cảnh giới {realm_name} - Giai đoạn {i+1} của tu luyện"
        }

        # Add sub-realms
        if include_sub_realms:
            sub_realms = ["Sơ Kỳ", "Trung Kỳ", "Hậu Kỳ", "Đỉnh Phong"]
            realm["sub_realms"] = [
                {
                    "name": sub,
                    "power_multiplier": (i + 1) * 10 + j * 2.5,
                    "description": f"{realm_name} - {sub}"
                }
                for j, sub in enumerate(sub_realms[:min(4, 4 - i//3)])
            ]

        realms.append(realm)

    return realms


def _generate_breakthrough_mechanic(difficulty: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Tạo cơ chế đột phá cảnh giới"""
    return {
        "type": "resource_based",
        "base_chance": config["breakthrough_chance"],
        "required_resources": [
            {"name": "Linh thạch", "amount": 1000 * config["resource_multiplier"]},
            {"name": "Đan dược đột phá", "amount": 5 * config["resource_multiplier"]}
        ],
        "failure_penalty": "Mất 50% tài nguyên",
        "success_bonus": "Tăng 10% sức mạnh",
        "special_requirements": [
            "Hiểu rõ đạo pháp của cảnh giới hiện tại",
            "Có đủ linh khí trong cơ thể"
        ]
    }


# =============================================================================
# TOOL: TẠO HỆ THỐNG VẬT PHẨM
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Tạo hệ thống vật phẩm", system_name=system_name, categories=len(item_categories))

    try:
        # Giới hạn rarity_levels
        rarity_levels = max(1, min(7, rarity_levels))

        # Rarity names
        rarity_names = [
            "Phàm Phẩm", "Linh Phẩm", "Pháp Phẩm", "Chân Phẩm",
            "Tiên Phẩm", "Thần Phẩm", "Thiên Phẩm"
        ]

        # Generate rarity system
        rarities = []
        for i in range(rarity_levels):
            rarities.append({
                "level": i + 1,
                "name": rarity_names[i],
                "power_multiplier": (i + 1) * 2,
                "drop_chance": max(0.01, 1.0 - (i * 0.15)),
                "color_code": _get_rarity_color(i)
            })

        # Generate items by category
        categories_data = {}
        for category in item_categories:
            categories_data[category] = _generate_category_items(category, rarity_levels)

        # Crafting system
        crafting = None
        if include_crafting:
            crafting = _generate_crafting_system()

        # Upgrade system
        upgrade = None
        if include_upgrade:
            upgrade = _generate_upgrade_system(rarity_levels)

        result = {
            "success": True,
            "system_name": system_name,
            "rarity_levels": rarity_levels,
            "rarities": rarities,
            "categories": categories_data,
            "crafting_system": crafting,
            "upgrade_system": upgrade
        }

        logger.info("Tạo hệ thống vật phẩm thành công", system_name=system_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo hệ thống vật phẩm", system_name=system_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo hệ thống vật phẩm: {str(e)}",
            code="ITEM_SYSTEM_ERROR"
        )


def _get_rarity_color(rarity_level: int) -> str:
    """Lấy màu cho rarity level"""
    colors = ["§f", "§a", "§9", "§5", "§6", "§c", "§d"]
    return colors[rarity_level] if rarity_level < len(colors) else "§f"


def _generate_category_items(category: str, max_rarity: int) -> List[Dict[str, Any]]:
    """Tạo items cho một category"""
    items = []

    if category == "pháp bảo":
        items = [
            {"name": "Kiếm Phi Hành", "type": "weapon", "rarity": 3, "effects": ["tăng sức mạnh", "bay được"]},
            {"name": "Trận Bàn", "type": "tool", "rarity": 4, "effects": ["tạo trận pháp", "bảo vệ"]},
            {"name": "Pháp Y", "type": "armor", "rarity": 3, "effects": ["tăng phòng thủ", "chống pháp thuật"]},
            {"name": "Nhẫn Trữ Vật", "type": "accessory", "rarity": 2, "effects": ["lưu trữ item"]},
            {"name": "Bội Kiếm", "type": "weapon", "rarity": 5, "effects": ["tấn công từ xa", "nhanh nhẹn"]}
        ]
    elif category == "đan dược":
        items = [
            {"name": "Đan Dược Tu Luyện", "type": "consumable", "rarity": 2, "effects": ["tăng kinh nghiệm tu luyện"]},
            {"name": "Đan Dược Đột Phá", "type": "consumable", "rarity": 4, "effects": ["tăng tỷ lệ đột phá"]},
            {"name": "Đan Dược Hồi Máu", "type": "consumable", "rarity": 1, "effects": ["hồi phục HP"]},
            {"name": "Đan Dược Tăng Cường", "type": "consumable", "rarity": 3, "effects": ["tăng sức mạnh tạm thời"]}
        ]
    elif category == "tài liệu":
        items = [
            {"name": "Linh Thạch Hạ Đẳng", "type": "currency", "rarity": 1, "effects": ["tiền tệ cơ bản"]},
            {"name": "Linh Thạch Trung Đẳng", "type": "currency", "rarity": 2, "effects": ["tiền tệ trung cấp"]},
            {"name": "Linh Thạch Thượng Đẳng", "type": "currency", "rarity": 3, "effects": ["tiền tệ cao cấp"]},
            {"name": "Tinh Thạch", "type": "material", "rarity": 4, "effects": ["chế tạo pháp bảo"]}
        ]
    else:
        # Generic items
        items = [
            {"name": f"{category.capitalize()} Cơ Bản", "type": "basic", "rarity": 1, "effects": ["hiệu ứng cơ bản"]},
            {"name": f"{category.capitalize()} Trung Cấp", "type": "advanced", "rarity": 2, "effects": ["hiệu ứng trung cấp"]},
            {"name": f"{category.capitalize()} Cao Cấp", "type": "advanced", "rarity": 3, "effects": ["hiệu ứng cao cấp"]}
        ]

    # Filter by max rarity
    return [item for item in items if item["rarity"] <= max_rarity]


def _generate_crafting_system() -> Dict[str, Any]:
    """Tạo hệ thống chế tạo"""
    return {
        "type": "recipe_based",
        "crafting_stations": ["Lò Luyện", "Bàn Luyện Khí", "Thiên Địa Đỉnh"],
        "recipes": [
            {
                "name": "Đan Dược Tu Luyện",
                "materials": ["Linh thạch", "Thảo dược"],
                "result": "Đan Dược Tu Luyện",
                "success_rate": 0.7
            },
            {
                "name": "Kiếm Phi Hành",
                "materials": ["Tinh thạch", "Sắt thiên"],
                "result": "Kiếm Phi Hành",
                "success_rate": 0.5
            }
        ]
    }


def _generate_upgrade_system(max_rarity: int) -> Dict[str, Any]:
    """Tạo hệ thống nâng cấp"""
    return {
        "type": "enhancement",
        "max_level": 10,
        "success_rates": [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1],
        "failure_penalty": "Giảm 1 cấp nếu thất bại",
        "materials_per_level": ["Linh thạch", "Tinh thạch", "Đan dược"],
        "special_events": {
            "critical_success": "Tăng 2 cấp",
            "critical_failure": "Phá hủy vật phẩm"
        }
    }


# =============================================================================
# TOOL: TẠO HỆ THỐNG KỸ NĂNG
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Tạo hệ thống kỹ năng", system_name=system_name, skill_types=len(skill_types))

    try:
        # Giới hạn max_skill_level
        max_skill_level = max(1, min(20, max_skill_level))

        # Generate skills by type
        skills_by_type = {}
        for skill_type in skill_types:
            skills_by_type[skill_type] = _generate_skills_for_type(skill_type, max_skill_level)

        # Skill tree
        skill_tree = None
        if include_skill_tree:
            skill_tree = _generate_skill_tree(skill_types)

        # Cooldown system
        cooldown_system = None
        if include_cooldowns:
            cooldown_system = _generate_cooldown_system()

        result = {
            "success": True,
            "system_name": system_name,
            "max_skill_level": max_skill_level,
            "skill_types": skill_types,
            "skills": skills_by_type,
            "skill_tree": skill_tree,
            "cooldown_system": cooldown_system
        }

        logger.info("Tạo hệ thống kỹ năng thành công", system_name=system_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo hệ thống kỹ năng", system_name=system_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo hệ thống kỹ năng: {str(e)}",
            code="SKILL_SYSTEM_ERROR"
        )


def _generate_skills_for_type(skill_type: str, max_level: int) -> List[Dict[str, Any]]:
    """Tạo skills cho một type"""
    skill_templates = {
        "công kích": [
            {"name": "Kiếm Khí", "description": "Bắn kiếm khí tấn công địch"},
            {"name": "Lôi Điện", "description": "Gọi sấm sét tấn công"},
            {"name": "Hỏa Cầu", "description": "Ném hỏa cầu"}
        ],
        "phòng thủ": [
            {"name": "Linh Khí Hộ Thuẫn", "description": "Tạo khiên linh khí"},
            {"name": "Thân Pháp", "description": "Tăng tốc độ di chuyển"}
        ],
        "hồi phục": [
            {"name": "Chữa Trị", "description": "Hồi phục HP"},
            {"name": "Giải Độc", "description": "Giải các trạng thái độc"}
        ],
        "phụ trợ": [
            {"name": "Tăng Sức Mạnh", "description": "Tăng sức mạnh tạm thời"},
            {"name": "Thuật Tìm Kiếm", "description": "Tìm kho báu gần đó"}
        ]
    }

    templates = skill_templates.get(skill_type, [{"name": f"Kỹ Năng {skill_type}", "description": "Mô tả kỹ năng"}])

    skills = []
    for template in templates:
        for level in range(1, max_level + 1):
            skill = {
                "name": template["name"],
                "type": skill_type,
                "level": level,
                "description": template["description"],
                "power": level * 10,
                "mana_cost": level * 5,
                "cooldown": level * 0.5
            }
            skills.append(skill)

    return skills


def _generate_skill_tree(skill_types: List[str]) -> Dict[str, Any]:
    """Tạo skill tree"""
    return {
        "type": "tree",
        "nodes": [
            {"id": "root", "name": "Gốc Tu Luyện", "unlocks": skill_types},
            *[{"id": f"branch_{i}", "name": f"{skill_type} Chi", "unlocks": []} for i, skill_type in enumerate(skill_types)]
        ],
        "connections": [
            {"from": "root", "to": f"branch_{i}"} for i in range(len(skill_types))
        ]
    }


def _generate_cooldown_system() -> Dict[str, Any]:
    """Tạo hệ thống cooldown"""
    return {
        "type": "global_cooldown",
        "base_cooldown": 1.0,
        "cooldown_reduction_per_level": 0.05,
        "max_cooldown_reduction": 0.5,
        "shared_cooldown_categories": ["công kích", "phòng thủ"]
    }


# =============================================================================
# TOOL: TẠO HỆ THỐNG MÔN PHÁI
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Tạo hệ thống môn phái", system_name=system_name, faction_count=faction_count)

    try:
        # Giới hạn faction_count
        faction_count = max(2, min(10, faction_count))

        # Generate factions
        factions = _generate_factions(faction_count)

        # Relations
        relations = None
        if include_relations:
            relations = _generate_faction_relations(factions)

        # Quests
        quests = None
        if include_quests:
            quests = _generate_faction_quests(factions)

        result = {
            "success": True,
            "system_name": system_name,
            "faction_count": faction_count,
            "factions": factions,
            "relations": relations,
            "quests": quests
        }

        logger.info("Tạo hệ thống môn phái thành công", system_name=system_name, factions=faction_count)

        return result

    except Exception as e:
        logger.error("Lỗi tạo hệ thống môn phái", system_name=system_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo hệ thống môn phái: {str(e)}",
            code="FACTION_SYSTEM_ERROR"
        )


def _generate_factions(count: int) -> List[Dict[str, Any]]:
    """Tạo danh sách môn phái"""
    faction_templates = [
        {"name": "Tiên Nhạc Môn", "alignment": "good", "specialty": "Kiếm Thuật", "location": "Núi Tiên Nhạc"},
        {"name": "Ma Đạo", "alignment": "evil", "specialty": "Ma Thuật", "location": "Ma Vực"},
        {"name": "Thiên Đạo Môn", "alignment": "neutral", "specialty": "Cân Bằng", "location": "Thiên Đạo Sơn"},
        {"name": "Phật Môn", "alignment": "good", "specialty": "Pháp Thuật", "location": "Phật Sơn"},
        {"name": "Yêu Tộc", "alignment": "neutral", "specialty": "Biến Hình", "location": "Yêu Sâm"},
        {"name": "Thần Tiên Cung", "alignment": "good", "specialty": "Thần Thuật", "location": "Thiên Cung"},
        {"name": "Địa Ngục Giáo", "alignment": "evil", "specialty": "Hắc Ám", "location": "Địa Ngục"},
        {"name": "Linh Thú Sơn", "alignment": "neutral", "specialty": "Linh Thú", "location": "Linh Sơn"},
        {"name": "Vũ Trụ Môn", "alignment": "neutral", "specialty": "Vũ Trụ", "location": "Vũ Trụ Đảo"},
        {"name": "Nhân Gian Kiếm Phái", "alignment": "good", "specialty": "Nhân Gian Kiếm Thuật", "location": "Nhân Gian"}
    ]

    return faction_templates[:count]


def _generate_faction_relations(factions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tạo quan hệ giữa các môn phái"""
    relations = {}

    for i, faction1 in enumerate(factions):
        relations[faction1["name"]] = {}
        for j, faction2 in enumerate(factions):
            if i != j:
                # Determine relation based on alignment
                if faction1["alignment"] == faction2["alignment"]:
                    relation = "ally"
                elif faction1["alignment"] == "neutral" or faction2["alignment"] == "neutral":
                    relation = "neutral"
                else:
                    relation = "enemy"

                relations[faction1["name"]][faction2["name"]] = relation

    return relations


def _generate_faction_quests(factions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Tạo nhiệm vụ môn phái"""
    quests = []

    for faction in factions:
        quests.append({
            "faction": faction["name"],
            "quests": [
                {"name": "Nhiệm vụ gia nhập", "type": "join", "reward": "Thành viên môn phái"},
                {"name": "Nhiệm vụ hằng ngày", "type": "daily", "reward": "Kinh nghiệm, Linh thạch"},
                {"name": "Nhiệm vụ tu luyện", "type": "cultivation", "reward": "Công pháp, Tài nguyên"}
            ]
        })

    return quests


# =============================================================================
# TOOL: TẠO HỆ THỐNG THẾ GIỚI
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Tạo hệ thống thế giới", system_name=system_name)

    try:
        world_data = {
            "name": system_name,
            "description": "Thế giới tu tiên với đầy đủ các cảnh quan và bí cảnh"
        }

        # Spiritual veins
        if include_spiritual_veins:
            world_data["spiritual_veins"] = _generate_spiritual_veins()

        # Secret realms
        if include_secret_realms:
            world_data["secret_realms"] = _generate_secret_realms()

        # Ancient ruins
        if include_ancient_ruins:
            world_data["ancient_ruins"] = _generate_ancient_ruins()

        result = {
            "success": True,
            "system_name": system_name,
            "world": world_data
        }

        logger.info("Tạo hệ thống thế giới thành công", system_name=system_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo hệ thống thế giới", system_name=system_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo hệ thống thế giới: {str(e)}",
            code="WORLD_SYSTEM_ERROR"
        )


def _generate_spiritual_veins() -> List[Dict[str, Any]]:
    """Tạo linh mạch"""
    return [
        {"name": "Linh Mạch Hạ Đẳng", "quality": 1, "density": 100, "location": "Vùng biên giới"},
        {"name": "Linh Mạch Trung Đẳng", "quality": 2, "density": 500, "location": "Vùng trung tâm"},
        {"name": "Linh Mạch Thượng Đẳng", "quality": 3, "density": 2000, "location": "Vùng thiêng liêng"},
        {"name": "Linh Mạch Tuyệt Thế", "quality": 4, "density": 10000, "location": "Vùng cấm"}
    ]


def _generate_secret_realms() -> List[Dict[str, Any]]:
    """Tạo bí cảnh"""
    return [
        {"name": "Bí Cảnh Cấp Thấp", "min_level": 1, "max_level": 10, "rewards": ["Linh thạch", "Đan dược"]},
        {"name": "Bí Cảnh Cấp Trung", "min_level": 11, "max_level": 50, "rewards": ["Pháp bảo", "Công pháp"]},
        {"name": "Bí Cảnh Cấp Cao", "min_level": 51, "max_level": 100, "rewards": ["Tiên phẩm", "Thần thuật"]},
        {"name": "Bí Cảnh Tuyệt Thế", "min_level": 101, "max_level": 999, "rewards": ["Thiên phẩm", "Đạo pháp"]}
    ]


def _generate_ancient_ruins() -> List[Dict[str, Any]]:
    """Tạo cổ tích"""
    return [
        {"name": "Cổ Tiên Táng", "age": "100000 năm", "dangers": ["Cổ trận", "Cổ thú"], "rewards": ["Tiên phẩm", "Cổ công pháp"]},
        {"name": "Thần Chiến Trường", "age": "500000 năm", "dangers": ["Thần linh", "Thần binh"], "rewards": ["Thần khí", "Thần thuật"]},
        {"name": "Ma Đạo Cổ Thành", "age": "200000 năm", "dangers": ["Ma linh", "Ma bảo"], "rewards": ["Ma pháp", "Ma khí"]}
    ]


# =============================================================================
# TOOL: CÂN BẰNG CULTIVATION
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Cân bằng cultivation", realms=len(realms), target_hours=target_playtime_hours)

    try:
        # Calculate time per realm
        total_realms = len(realms)
        base_time_per_realm = (target_playtime_hours * 60) / total_realms  # minutes

        balanced_realms = []

        for i, realm in enumerate(realms):
            # Calculate time based on progression curve
            if progression_curve == "linear":
                time_required = base_time_per_realm
            elif progression_curve == "exponential":
                time_required = base_time_per_realm * (1.5 ** i)
            elif progression_curve == "logarithmic":
                time_required = base_time_per_realm * (1 + (i / total_realms))
            else:
                time_required = base_time_per_realm

            # Resources required
            resources = {
                "linh_thach": int(1000 * (i + 1) * 1.5),
                "dan_duoc": int(5 * (i + 1))
            }

            balanced_realm = {
                "level": realm["level"],
                "name": realm["name"],
                "time_required_minutes": round(time_required, 1),
                "time_required_hours": round(time_required / 60, 2),
                "resources_required": resources,
                "breakthrough_chance": max(0.1, 0.8 - (i * 0.08)),
                "difficulty_rating": min(10, i + 1)
            }

            balanced_realms.append(balanced_realm)

        # Summary
        total_time = sum(r["time_required_hours"] for r in balanced_realms)

        result = {
            "success": True,
            "target_playtime_hours": target_playtime_hours,
            "actual_playtime_hours": round(total_time, 2),
            "progression_curve": progression_curve,
            "realms": balanced_realms,
            "balance_notes": [
                "Tốc độ tu luyện tăng dần theo cảnh giới",
                "Tài nguyên yêu cầu tăng theo cấp độ",
                "Tỷ lệ đột phá giảm dần ở cảnh giới cao"
            ]
        }

        logger.info("Cân bằng cultivation thành công", total_time=round(total_time, 2))

        return result

    except Exception as e:
        logger.error("Lỗi cân bằng cultivation", error=str(e))
        raise MCPError(
            message=f"Không thể cân bằng cultivation: {str(e)}",
            code="BALANCE_ERROR"
        )


# =============================================================================
# TOOL: TẠO QUEST CHAIN
# =============================================================================

@handle_exception
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

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    logger.info("Tạo quest chain", chain_name=chain_name, quest_count=quest_count)

    try:
        # Giới hạn quest_count
        quest_count = max(1, min(10, quest_count))

        quests = []
        for i in range(quest_count):
            quest = {
                "order": i + 1,
                "name": f"Nhiệm vụ {i+1}: {_generate_quest_name(i)}",
                "type": _generate_quest_type(i),
                "description": _generate_quest_description(i, chain_name),
                "objectives": _generate_quest_objectives(i),
                "difficulty": difficulty,
                "rewards": _generate_quest_rewards(i, rewards_type)
            }
            quests.append(quest)

        result = {
            "success": True,
            "chain_name": chain_name,
            "quest_count": quest_count,
            "difficulty": difficulty,
            "rewards_type": rewards_type,
            "quests": quests
        }

        logger.info("Tạo quest chain thành công", chain_name=chain_name, quests=quest_count)

        return result

    except Exception as e:
        logger.error("Lỗi tạo quest chain", chain_name=chain_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo quest chain: {str(e)}",
            code="QUEST_CHAIN_ERROR"
        )


def _generate_quest_name(index: int) -> str:
    """Tạo tên nhiệm vụ"""
    quest_names = [
        "Bắt Đầu Tu Luyện",
        "Thu Thập Tài Nguyên",
        "Đột Phá Cảnh Giới",
        "Thử Thách Đầu Tiên",
        "Gặp Gỡ Đồng Đạo",
        "Thám Hiểm Bí Cảnh",
        "Chiến Đấu Với Ma Đạo",
        "Nhận Diện Pháp Bảo",
        "Luyện Đan Thành Công",
        "Trở Thành Tiên Nhân"
    ]
    return quest_names[min(index, len(quest_names) - 1)]


def _generate_quest_type(index: int) -> str:
    """Tạo loại nhiệm vụ"""
    quest_types = ["cultivation", "gather", "combat", "explore", "craft", "social"]
    return quest_types[index % len(quest_types)]


def _generate_quest_description(index: int, chain_name: str) -> str:
    """Tạo mô tả nhiệm vụ"""
    descriptions = [
        f"Bắt đầu hành trình tu tiên của bạn trong {chain_name}",
        f"Thu thập tài nguyên cần thiết để tu luyện",
        f"Vượt qua thử thách để đột phá cảnh giới",
        f"Đối mặt với kẻ thù đầu tiên trên con đường tu tiên",
        f"Kết nối với những người tu luyện khác"
    ]
    return descriptions[min(index, len(descriptions) - 1)]


def _generate_quest_objectives(index: int) -> List[str]:
    """Tạo mục tiêu nhiệm vụ"""
    objectives = [
        ["Đạt cảnh giới Luyện Khí tầng 1", "Thu thập 100 linh thạch"],
        ["Thu thập 50 linh thạch", "Đánh bại 10 quái vật"],
        ["Đột phá cảnh giới Trúc Cơ", "Sử dụng 5 đan dược"],
        ["Hoàn thành bí cảnh cấp thấp", "Nhận được pháp bảo"],
        ["Tham gia môn phái", "Hoàn thành nhiệm vụ hằng ngày"]
    ]
    return objectives[min(index, len(objectives) - 1)]


def _generate_quest_rewards(index: int, rewards_type: str) -> Dict[str, Any]:
    """Tạo phần thưởng nhiệm vụ"""
    base_rewards = {
        "experience": 100 * (index + 1),
        "linh_thach": 50 * (index + 1)
    }

    if rewards_type == "cultivation":
        base_rewards["cultivation_bonus"] = 10 * (index + 1)
    elif rewards_type == "items":
        base_rewards["items"] = [{"name": "Pháp bảo", "rarity": index + 1}]
    elif rewards_type == "story":
        base_rewards["story_unlock"] = f"Chương {index + 1}"

    return base_rewards


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "search_cultivation_story",
    "generate_cultivation_system",
    "generate_item_system",
    "generate_skill_system",
    "generate_faction_system",
    "generate_world_system",
    "balance_cultivation",
    "generate_quest_chain"
]