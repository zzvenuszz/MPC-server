"""
MCP Programming Support Server - Minecraft Plugin Builder
Công cụ tạo và xây dựng Minecraft Paper plugin
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from config import get_settings
from utils import get_logger, MCPError, handle_exception, write_file_safe

logger = get_logger()


# =============================================================================
# TOOL: TẠO CẤU TRÚC PLUGIN
# =============================================================================

@handle_exception
def create_plugin_structure(
    plugin_name: str,
    package_name: str,
    author: str,
    version: str = "1.0.0",
    main_class: Optional[str] = None,
    description: str = "",
    website: str = "",
    depends: Optional[List[str]] = None,
    soft_depends: Optional[List[str]] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo cấu trúc dự án plugin Minecraft

    Args:
        plugin_name: Tên plugin (ví dụ: "CultivationPlugin")
        package_name: Package name (ví dụ: "com.example.cultivation")
        author: Tác giả
        version: Phiên bản
        main_class: Class chính (nếu None sẽ tự generate)
        description: Mô tả plugin
        website: Website
        depends: List plugins phụ thuộc (hard dependencies)
        soft_depends: List plugins phụ thuộc (soft dependencies)
        output_dir: Thư mục output (nếu None dùng workspace)

    Returns:
        Dict chứa thông tin cấu trúc đã tạo

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info("Tạo cấu trúc plugin", plugin_name=plugin_name, package_name=package_name)

    try:
        # Tạo main class name nếu không có
        if not main_class:
            main_class = f"{plugin_name}Main"

        # Tạo package path
        package_path = package_name.replace(".", "/")

        # Xác định output directory
        if output_dir:
            plugin_dir = settings.get_workspace_path(output_dir, plugin_name)
        else:
            plugin_dir = settings.get_workspace_path("plugins", plugin_name)

        # Tạo thư mục
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Tạo cấu trúc thư mục
        dirs_to_create = [
            "src/main/java/" + package_path,
            "src/main/resources",
            "src/test/java/" + package_path,
            "src/test/resources"
        ]

        for dir_path in dirs_to_create:
            (plugin_dir / dir_path).mkdir(parents=True, exist_ok=True)

        # Tạo các file
        files_created = []

        # 1. plugin.yml
        plugin_yml = _generate_plugin_yml(
            plugin_name, main_class, version, author, description, website, depends, soft_depends
        )
        plugin_yml_path = plugin_dir / "src/main/resources/plugin.yml"
        write_file_safe(str(plugin_yml_path), plugin_yml)
        files_created.append("src/main/resources/plugin.yml")

        # 2. Main class
        main_class_content = _generate_main_class(package_name, main_class, plugin_name)
        main_class_path = plugin_dir / f"src/main/java/{package_path}/{main_class}.java"
        write_file_safe(str(main_class_path), main_class_content)
        files_created.append(f"src/main/java/{package_path}/{main_class}.java")

        # 3. pom.xml (Maven)
        pom_xml = _generate_pom_xml(plugin_name, package_name, version, author)
        pom_xml_path = plugin_dir / "pom.xml"
        write_file_safe(str(pom_xml_path), pom_xml)
        files_created.append("pom.xml")

        # 4. README.md
        readme = _generate_readme(plugin_name, description)
        readme_path = plugin_dir / "README.md"
        write_file_safe(str(readme_path), readme)
        files_created.append("README.md")

        # 5. .gitignore
        gitignore = _generate_gitignore()
        gitignore_path = plugin_dir / ".gitignore"
        write_file_safe(str(gitignore_path), gitignore)
        files_created.append(".gitignore")

        result = {
            "success": True,
            "plugin_name": plugin_name,
            "package_name": package_name,
            "main_class": main_class,
            "output_dir": str(plugin_dir.relative_to(settings.workspace)),
            "files_created": files_created,
            "total_files": len(files_created),
            "version": version,
            "author": author
        }

        logger.info("Tạo cấu trúc plugin thành công", plugin_name=plugin_name, files=len(files_created))

        return result

    except Exception as e:
        logger.error("Lỗi tạo cấu trúc plugin", plugin_name=plugin_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo cấu trúc plugin: {str(e)}",
            code="PLUGIN_STRUCTURE_ERROR",
            details={"plugin_name": plugin_name}
        )


def _generate_plugin_yml(
    plugin_name: str,
    main_class: str,
    version: str,
    author: str,
    description: str,
    website: str,
    depends: Optional[List[str]],
    soft_depends: Optional[List[str]]
) -> str:
    """Tạo nội dung plugin.yml"""
    content = f"name: {plugin_name}\n"
    content += f"version: {version}\n"
    content += f"main: {main_class}\n"
    content += f"author: {author}\n"

    if description:
        content += f"description: {description}\n"

    if website:
        content += f"website: {website}\n"

    if depends:
        content += f"depend: {', '.join(depends)}\n"

    if soft_depends:
        content += f"softdepend: {', '.join(soft_depends)}\n"

    content += f"api-version: 1.20\n"

    return content


def _generate_main_class(package_name: str, main_class: str, plugin_name: str) -> str:
    """Tạo main class cho plugin"""
    package_stmt = f"package {package_name};\n\n"

    imports = """import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.event.Listener;
import org.bukkit.event.EventHandler;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.entity.Player;
import org.bukkit.ChatColor;

import java.util.logging.Level;
"""

    class_content = f"""
/**
 * {plugin_name} - Main Plugin Class
 * Tạo bởi MCP Programming Support Server
 */
public class {main_class} extends JavaPlugin implements Listener {{

    private static {main_class} instance;

    @Override
    public void onEnable() {{
        // Plugin startup logic
        instance = this;

        // Đăng ký events
        getServer().getPluginManager().registerEvents(this, this);

        getLogger().info(Level.INFO, "{plugin_name} đã được kích hoạt!");
    }}

    @Override
    public void onDisable() {{
        // Plugin shutdown logic
        getLogger().info(Level.INFO, "{plugin_name} đã tắt!");
    }}

    @EventHandler
    public void onPlayerJoin(PlayerJoinEvent event) {{
        Player player = event.getPlayer();
        player.sendMessage(ChatColor.GREEN + "Chào mừng đến với {plugin_name}!");
    }}

    public static {main_class} getInstance() {{
        return instance;
    }}
}}
"""

    return package_stmt + imports + class_content


def _generate_pom_xml(plugin_name: str, package_name: str, version: str, author: str) -> str:
    """Tạo pom.xml cho Maven"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>{package_name}</groupId>
    <artifactId>{plugin_name}</artifactId>
    <version>{version}</version>
    <packaging>jar</packaging>

    <name>{plugin_name}</name>
    <description>Minecraft Paper Plugin</description>
    <url>https://github.com/{author}/{plugin_name}</url>

    <properties>
        <java.version>17</java.version>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <repositories>
        <repository>
            <id>papermc</id>
            <url>https://repo.papermc.io/repository/maven-public/</url>
        </repository>
    </repositories>

    <dependencies>
        <dependency>
            <groupId>io.papermc.paper</groupId>
            <artifactId>paper-api</artifactId>
            <version>1.20.1-R0.1-SNAPSHOT</version>
            <scope>provided</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
"""


def _generate_readme(plugin_name: str, description: str) -> str:
    """Tạo README.md"""
    return f"""# {plugin_name}

{description if description else "Minecraft Paper Plugin"}

## Cài đặt

1. Build project với Maven: `mvn clean package`
2. Copy file `target/{plugin_name}-1.0.0.jar` vào thư mục `plugins/` của Paper server
3. Restart server

## Commands

- `/plugin` - Command chính

## Configuration

File cấu hình: `plugins/{plugin_name}/config.yml`

## Development

### Build

```bash
mvn clean package
```

### Test

```bash
mvn test
```

## License

MIT License

## Author

{plugin_name} Team
"""


def _generate_gitignore() -> str:
    """Tạo .gitignore"""
    return """# Maven
target/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
dependency-reduced-pom.xml
buildNumber.properties
.mvn/timing.properties
.mvn/wrapper/maven-wrapper.jar

# IDE
.idea/
*.iml
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Build output
*.jar
"""


# =============================================================================
# TOOL: TẠO PLUGIN.YML
# =============================================================================

@handle_exception
def generate_plugin_yml(
    plugin_name: str,
    main_class: str,
    version: str = "1.0.0",
    author: str = "",
    description: str = "",
    api_version: str = "1.20",
    depends: Optional[List[str]] = None,
    soft_depends: Optional[List[str]] = None,
    commands: Optional[List[Dict[str, Any]]] = None,
    permissions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Tạo file plugin.yml

    Args:
        plugin_name: Tên plugin
        main_class: Class chính
        version: Phiên bản
        author: Tác giả
        description: Mô tả
        api_version: Phiên bản API
        depends: List hard dependencies
        soft_depends: List soft dependencies
        commands: List commands
        permissions: List permissions

    Returns:
        Dict chứa nội dung plugin.yml

    Raises:
        MCPError: Nếu có lỗi
    """
    logger.info("Tạo plugin.yml", plugin_name=plugin_name)

    try:
        content = f"name: {plugin_name}\n"
        content += f"version: {version}\n"
        content += f"main: {main_class}\n"
        content += f"api-version: {api_version}\n"

        if author:
            content += f"author: {author}\n"

        if description:
            content += f"description: {description}\n"

        if depends:
            content += f"depend: {', '.join(depends)}\n"

        if soft_depends:
            content += f"softdepend: {', '.join(soft_depends)}\n"

        # Commands
        if commands:
            content += "\ncommands:\n"
            for cmd in commands:
                cmd_name = cmd.get("name", "")
                content += f"  {cmd_name}:\n"
                if "description" in cmd:
                    content += f"    description: {cmd['description']}\n"
                if "usage" in cmd:
                    content += f"    usage: /{cmd_name} {cmd['usage']}\n"
                if "aliases" in cmd:
                    content += f"    aliases: [{', '.join(cmd['aliases'])}]\n"
                if "permission" in cmd:
                    content += f"    permission: {cmd['permission']}\n"

        # Permissions
        if permissions:
            content += "\npermissions:\n"
            for perm in permissions:
                perm_name = perm.get("name", "")
                content += f"  {perm_name}:\n"
                if "description" in perm:
                    content += f"    description: {perm['description']}\n"
                if "default" in perm:
                    content += f"    default: {perm['default']}\n"

        result = {
            "success": True,
            "plugin_name": plugin_name,
            "plugin_yml": content,
            "line_count": len(content.split('\n'))
        }

        logger.info("Tạo plugin.yml thành công", plugin_name=plugin_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo plugin.yml", plugin_name=plugin_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo plugin.yml: {str(e)}",
            code="PLUGIN_YML_ERROR"
        )


# =============================================================================
# TOOL: TẠO LISTENER
# =============================================================================

@handle_exception
def implement_listener(
    listener_name: str,
    package_name: str,
    events: List[str],
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo event listener class

    Args:
        listener_name: Tên listener (ví dụ: "PlayerListener")
        package_name: Package name
        events: List events cần handle
        output_dir: Thư mục output

    Returns:
        Dict chứa nội dung listener class

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info("Tạo listener", listener_name=listener_name, events=len(events))

    try:
        package_path = package_name.replace(".", "/")

        # Tạo package statement
        content = f"package {package_name};\n\n"

        # Imports
        content += "import org.bukkit.event.Listener;\n"
        content += "import org.bukkit.event.EventHandler;\n"
        content += "import org.bukkit.event.Listener;\n"
        content += "import org.bukkit.entity.Player;\n"
        content += "import org.bukkit.ChatColor;\n"
        content += "import java.util.logging.Level;\n\n"

        # Event imports
        for event in events:
            event_import = _get_event_import(event)
            if event_import and event_import not in content:
                content += f"import {event_import};\n"

        content += "\n"

        # Class definition
        content += f"/**\n"
        content += f" * {listener_name} - Event Listener\n"
        content += f" */\n"
        content += f"public class {listener_name} implements Listener {{\n\n"

        # Event handlers
        for event in events:
            method_name = _get_event_handler_method(event)
            event_param = _get_event_handler_param(event)

            content += f"    @EventHandler\n"
            content += f"    public void on{method_name}({event_param} event) {{\n"
            content += f"        // TODO: Implement {event} handler\n"
            content += f"    }}\n\n"

        content += "}\n"

        # Ghi file
        if output_dir:
            output_path = settings.get_workspace_path(output_dir, f"{listener_name}.java")
        else:
            output_path = settings.get_workspace_path(f"src/main/java/{package_path}/{listener_name}.java")

        write_file_safe(str(output_path), content)

        result = {
            "success": True,
            "listener_name": listener_name,
            "package_name": package_name,
            "events_handled": len(events),
            "file_path": str(output_path.relative_to(settings.workspace)),
            "content": content
        }

        logger.info("Tạo listener thành công", listener_name=listener_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo listener", listener_name=listener_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo listener: {str(e)}",
            code="LISTENER_CREATE_ERROR",
            details={"listener_name": listener_name}
        )


def _get_event_import(event_name: str) -> Optional[str]:
    """Lấy import statement cho event"""
    event_map = {
        "PlayerJoinEvent": "org.bukkit.event.player.PlayerJoinEvent",
        "PlayerQuitEvent": "org.bukkit.event.player.PlayerQuitEvent",
        "PlayerInteractEvent": "org.bukkit.event.player.PlayerInteractEvent",
        "BlockBreakEvent": "org.bukkit.event.block.BlockBreakEvent",
        "BlockPlaceEvent": "org.bukkit.event.block.BlockPlaceEvent",
        "EntityDamageEvent": "org.bukkit.event.entity.EntityDamageEvent",
        "EntityDeathEvent": "org.bukkit.event.entity.EntityDeathEvent",
        "InventoryClickEvent": "org.bukkit.event.inventory.InventoryClickEvent",
        "InventoryOpenEvent": "org.bukkit.event.inventory.InventoryOpenEvent",
        "InventoryCloseEvent": "org.bukkit.event.inventory.InventoryCloseEvent",
    }
    return event_map.get(event_name)


def _get_event_handler_method(event_name: str) -> str:
    """Lấy tên method handler"""
    # PlayerJoinEvent -> PlayerJoin
    if event_name.endswith("Event"):
        return event_name[:-5]
    return event_name


def _get_event_handler_param(event_name: str) -> str:
    """Lấy parameter type cho event handler"""
    return event_name


# =============================================================================
# TOOL: TẠO COMMAND
# =============================================================================

@handle_exception
def implement_command(
    command_name: str,
    package_name: str,
    description: str = "",
    usage: str = "",
    permission: str = "",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo command class

    Args:
        command_name: Tên command (ví dụ: "cultivation")
        package_name: Package name
        description: Mô tả command
        usage: Cách sử dụng
        permission: Permission required
        output_dir: Thư mục output

    Returns:
        Dict chứa nội dung command class

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info("Tạo command", command_name=command_name)

    try:
        package_path = package_name.replace(".", "/")
        class_name = f"{command_name.capitalize()}Command"

        # Tạo package statement
        content = f"package {package_name};\n\n"

        # Imports
        content += "import org.bukkit.command.Command;\n"
        content += "import org.bukkit.command.CommandExecutor;\n"
        content += "import org.bukkit.command.CommandSender;\n"
        content += "import org.bukkit.entity.Player;\n"
        content += "import org.bukkit.ChatColor;\n\n"

        # Class definition
        content += f"/**\n"
        content += f" * {class_name} - Command Handler\n"
        content += f" */\n"
        content += f"public class {class_name} implements CommandExecutor {{\n\n"

        # onExecute method
        content += f"    @Override\n"
        content += f"    public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {{\n"
        content += f"        if (!(sender instanceof Player)) {{\n"
        content += f"            sender.sendMessage(ChatColor.RED + \"Chỉ người chơi mới có thể sử dụng command này!\");\n"
        content += f"            return true;\n"
        content += f"        }}\n\n"

        content += f"        Player player = (Player) sender;\n\n"

        content += f"        if (args.length == 0) {{\n"
        content += f"            player.sendMessage(ChatColor.GREEN + \"=== {command_name} Command ===\");\n"
        content += f"            player.sendMessage(ChatColor.YELLOW + \"Cách sử dụng: /{command_name} <subcommand>\");\n"
        content += f"            return true;\n"
        content += f"        }}\n\n"

        content += f"        // TODO: Implement subcommands\n"
        content += f"        String subcommand = args[0].toLowerCase();\n\n"

        content += f"        switch (subcommand) {{\n"
        content += f"            case \"help\":\n"
        content += f"                player.sendMessage(ChatColor.GREEN + \"Help message\");\n"
        content += f"                break;\n"
        content += f"            default:\n"
        content += f"                player.sendMessage(ChatColor.RED + \"Subcommand không hợp lệ!\");\n"
        content += f"                break;\n"
        content += f"        }}\n\n"

        content += f"        return true;\n"
        content += f"    }}\n"
        content += f"}}\n"

        # Ghi file
        if output_dir:
            output_path = settings.get_workspace_path(output_dir, f"{class_name}.java")
        else:
            output_path = settings.get_workspace_path(f"src/main/java/{package_path}/{class_name}.java")

        write_file_safe(str(output_path), content)

        result = {
            "success": True,
            "command_name": command_name,
            "class_name": class_name,
            "package_name": package_name,
            "file_path": str(output_path.relative_to(settings.workspace)),
            "content": content
        }

        logger.info("Tạo command thành công", command_name=command_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo command", command_name=command_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo command: {str(e)}",
            code="COMMAND_CREATE_ERROR",
            details={"command_name": command_name}
        )


# =============================================================================
# TOOL: TẠO CONFIG.YML
# =============================================================================

@handle_exception
def generate_config_yml(
    config_name: str,
    sections: List[Dict[str, Any]],
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo file config.yml cho plugin

    Args:
        config_name: Tên config (ví dụ: "config")
        sections: List các sections
        output_dir: Thư mục output

    Returns:
        Dict chứa nội dung config.yml

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_write:
        raise MCPError(
            message="Chức năng ghi file đã bị tắt (ALLOW_WRITE=false)",
            code="WRITE_DISABLED"
        )

    logger.info("Tạo config.yml", config_name=config_name, sections=len(sections))

    try:
        content = f"# {config_name} Configuration\n"
        content += f"# Tạo bởi MCP Programming Support Server\n\n"

        for section in sections:
            section_name = section.get("name", "general")
            content += f"{section_name}:\n"

            # Section header
            if "description" in section:
                content += f"  # {section['description']}\n"

            # Section values
            for key, value in section.get("values", {}).items():
                if isinstance(value, bool):
                    content += f"  {key}: {str(value).lower()}\n"
                elif isinstance(value, (int, float)):
                    content += f"  {key}: {value}\n"
                elif isinstance(value, list):
                    content += f"  {key}:\n"
                    for item in value:
                        content += f"    - {item}\n"
                else:
                    content += f"  {key}: \"{value}\"\n"

            content += "\n"

        # Ghi file
        if output_dir:
            output_path = settings.get_workspace_path(output_dir, f"{config_name}.yml")
        else:
            output_path = settings.get_workspace_path(f"src/main/resources/{config_name}.yml")

        write_file_safe(str(output_path), content)

        result = {
            "success": True,
            "config_name": config_name,
            "sections": len(sections),
            "file_path": str(output_path.relative_to(settings.workspace)),
            "content": content
        }

        logger.info("Tạo config.yml thành công", config_name=config_name)

        return result

    except Exception as e:
        logger.error("Lỗi tạo config.yml", config_name=config_name, error=str(e))
        raise MCPError(
            message=f"Không thể tạo config.yml: {str(e)}",
            code="CONFIG_YML_ERROR"
        )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "create_plugin_structure",
    "generate_plugin_yml",
    "implement_listener",
    "implement_command",
    "generate_config_yml"
]