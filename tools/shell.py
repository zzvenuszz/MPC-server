"""
MCP Programming Support Server - Công cụ Shell
Thực thi shell commands an toàn với whitelist
"""

from typing import Optional, Dict, Any, List
import subprocess
import shlex
import os

from config import get_settings
from utils import get_logger, MCPError, handle_exception, is_safe_command

logger = get_logger()


# =============================================================================
# DANH SÁCH COMMANDS NGUY HIỂM - KHÔNG BAO GIỜ CHO PHÉP
# =============================================================================

DANGEROUS_COMMANDS = [
    # File system destruction
    "rm", "rmdir", "shred", "dd", "mkfs", "fdisk", "parted",
    # System control
    "shutdown", "reboot", "poweroff", "halt", "init",
    "systemctl", "service", "systemd-run",
    # User management
    "sudo", "su", "passwd", "useradd", "userdel", "usermod",
    "chsh", "chfn", "newgrp",
    # Network manipulation
    "iptables", "firewall-cmd", "ufw", "netsh",
    # Process manipulation
    "kill", "killall", "pkill", "xkill",
    # Dangerous pipes
    "|", ">", ">>", "<", "<<",  # These are shell operators, not commands
    # Other dangerous
    "chmod 777", "chown", "mount", "umount", "docker", "kubectl",
    "terraform", "ansible", "chef", "puppet"
]


# =============================================================================
# TOOL: THỰC THI SHELL COMMAND
# =============================================================================

@handle_exception
def shell_execute(
    command: str,
    working_directory: Optional[str] = None,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    shell: bool = False
) -> Dict[str, Any]:
    """
    Thực thi shell command an toàn

    Args:
        command: Command cần thực thi
        working_directory: Thư mục làm việc (mặc định: workspace)
        timeout: Timeout (giây)
        capture_output: Capture stdout/stderr
        shell: Sử dụng shell=True (False an toàn hơn)

    Returns:
        Dict chứa kết quả thực thi

    Raises:
        MCPError: Nếu có lỗi hoặc command không được phép
    """
    settings = get_settings()

    if not settings.allow_shell:
        raise MCPError(
            message="Chức năng shell đã bị tắt (ALLOW_SHELL=false)",
            code="SHELL_DISABLED"
        )

    logger.info(
        "Thực thi shell command",
        command=command[:100],
        working_directory=working_directory,
        timeout=timeout
    )

    try:
        # Validate command
        _validate_command(command)

        # Xác định working directory
        if working_directory:
            work_dir = settings.get_workspace_path(working_directory)
        else:
            work_dir = settings.workspace

        # Ensure directory exists
        work_dir.mkdir(parents=True, exist_ok=True)

        # Timeout
        exec_timeout = timeout or settings.request_timeout

        # Parse command
        if not shell:
            # Safe: sử dụng list of args
            args = shlex.split(command)
        else:
            # Less safe: shell=True
            args = command

        logger.info(
            "Thực thi command",
            command=command[:100],
            args=str(args)[:100] if isinstance(args, list) else args[:100],
            working_directory=str(work_dir),
            timeout=exec_timeout
        )

        # Thực thi command
        result = subprocess.run(
            args,
            cwd=work_dir,
            capture_output=capture_output,
            text=True,
            timeout=exec_timeout,
            shell=shell
        )

        # Xử lý output
        stdout = result.stdout if capture_output else ""
        stderr = result.stderr if capture_output else ""
        return_code = result.returncode

        # Truncate output nếu quá lớn
        max_output_length = 10000
        if len(stdout) > max_output_length:
            stdout = stdout[:max_output_length] + "\n... (output bị cắt ngắn)"
        if len(stderr) > max_output_length:
            stderr = stderr[:max_output_length] + "\n... (output bị cắt ngắn)"

        # Xác định success
        success = return_code == 0

        response = {
            "success": success,
            "command": command,
            "working_directory": str(work_dir),
            "return_code": return_code,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": False
        }

        if success:
            logger.info(
                "Thực thi command thành công",
                command=command[:100],
                return_code=return_code
            )
        else:
            logger.warning(
                "Thực thi command thất bại",
                command=command[:100],
                return_code=return_code,
                stderr=stderr[:200]
            )

        return response

    except subprocess.TimeoutExpired:
        logger.error("Command timeout", command=command[:100], timeout=exec_timeout)
        return {
            "success": False,
            "command": command,
            "working_directory": str(work_dir) if working_directory else str(settings.workspace),
            "return_code": -1,
            "stdout": "",
            "stderr": f"Command timeout sau {exec_timeout}s",
            "timed_out": True
        }

    except Exception as e:
        logger.error("Lỗi thực thi shell command", command=command[:100], error=str(e))
        raise MCPError(
            message=f"Không thể thực thi command: {str(e)}",
            code="SHELL_EXECUTE_ERROR",
            details={"command": command}
        )


def _validate_command(command: str) -> None:
    """
    Validate command có được phép chạy không

    Args:
        command: Command cần validate

    Raises:
        MCPError: Nếu command không được phép
    """
    settings = get_settings()

    # Parse command name
    command_stripped = command.strip()

    # Handle shell operators
    if any(op in command_stripped for op in ["|", ">", ">>", "<", "<<", "&&", "||", ";"]):
        raise MCPError(
            message="Shell operators (|, >, >>, <, &&, ||, ;) không được phép",
            code="SHELL_OPERATOR_NOT_ALLOWED"
        )

    # Get command name (first word)
    if not shell:
        try:
            args = shlex.split(command_stripped)
            cmd_name = args[0] if args else ""
        except ValueError:
            raise MCPError(
                message="Command không hợp lệ",
                code="INVALID_COMMAND"
            )
    else:
        # For shell=True, get first word
        cmd_name = command_stripped.split()[0] if command_stripped else ""

    # Check if command is in allowed list
    allowed_commands = settings.allowed_shell_commands

    if not is_safe_command(cmd_name, allowed_commands):
        # Check if it's dangerous
        if cmd_name in DANGEROUS_COMMANDS or any(cmd_name.startswith(dc) for dc in DANGEROUS_COMMANDS):
            raise MCPError(
                message=f"Command nguy hiểm không được phép: {cmd_name}",
                code="DANGEROUS_COMMAND",
                details={"command": cmd_name}
            )

        raise MCPError(
            message=f"Command không được phép: {cmd_name}. "
                    f"Commands được phép: {', '.join(allowed_commands)}",
            code="COMMAND_NOT_ALLOWED",
            details={"command": cmd_name, "allowed": allowed_commands}
        )

    # Check for dangerous patterns
    command_lower = command.lower()
    dangerous_patterns = [
        "rm -rf", "rm -r", "del /", "format", "mkfs",
        "sudo", "su ", "passwd", "shadow",
        "chmod 777", "chown root",
        "iptables", "firewall",
        "kill -9", "killall",
        "> /dev/", ">> /dev/",
        "curl | bash", "wget | bash",
        "eval $(", "$((", "`"
    ]

    for pattern in dangerous_patterns:
        if pattern in command_lower:
            raise MCPError(
                message=f"Command chứa pattern nguy hiểm: {pattern}",
                code="DANGEROUS_PATTERN",
                details={"pattern": pattern, "command": command}
            )


# =============================================================================
# TOOL: CHẠY COMMAND AN TOÀN (WRAPPER)
# =============================================================================

@handle_exception
def run_command_safe(
    command: str,
    args: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Chạy command an toàn với list of args (không dùng shell)

    Args:
        command: Command name
        args: List các arguments
        cwd: Working directory
        env: Environment variables

    Returns:
        Dict chứa kết quả

    Raises:
        MCPError: Nếu có lỗi
    """
    settings = get_settings()

    if not settings.allow_shell:
        raise MCPError(
            message="Chức năng shell đã bị tắt (ALLOW_SHELL=false)",
            code="SHELL_DISABLED"
        )

    # Build full command
    if args:
        full_command = f"{command} {' '.join(args)}"
    else:
        full_command = command

    # Validate
    _validate_command(full_command)

    # Set working directory
    if cwd:
        work_dir = settings.get_workspace_path(cwd)
    else:
        work_dir = settings.workspace

    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Chạy command an toàn",
        command=command,
        args=args,
        cwd=str(work_dir)
    )

    try:
        # Prepare environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        # Run command
        result = subprocess.run(
            [command] + (args or []),
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=settings.request_timeout,
            env=exec_env
        )

        stdout = result.stdout
        stderr = result.stderr

        # Truncate
        max_output = 10000
        if len(stdout) > max_output:
            stdout = stdout[:max_output] + "\n... (output bị cắt)"
        if len(stderr) > max_output:
            stderr = stderr[:max_output] + "\n... (output bị cắt)"

        return {
            "success": result.returncode == 0,
            "command": command,
            "args": args,
            "return_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "command": command,
            "args": args,
            "return_code": -1,
            "stdout": "",
            "stderr": f"Timeout sau {settings.request_timeout}s",
            "timed_out": True
        }

    except Exception as e:
        logger.error("Lỗi chạy command", command=command, error=str(e))
        raise MCPError(
            message=f"Không thể chạy command: {str(e)}",
            code="COMMAND_EXECUTE_ERROR",
            details={"command": command}
        )


# =============================================================================
# TOOL: LIỆT KÊ COMMANDS ĐƯỢC PHÉP
# =============================================================================

@handle_exception
def list_allowed_commands() -> Dict[str, Any]:
    """
    Liệt kê các shell commands được phép chạy

    Returns:
        Dict chứa danh sách commands được phép
    """
    settings = get_settings()

    logger.info("Liệt kê commands được phép")

    result = {
        "success": True,
        "allowed_commands": settings.allowed_shell_commands,
        "total_allowed": len(settings.allowed_shell_commands),
        "dangerous_commands_blocked": DANGEROUS_COMMANDS,
        "shell_enabled": settings.allow_shell
    }

    logger.info("Liệt kê commands thành công", total=len(settings.allowed_shell_commands))

    return result


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "shell_execute",
    "run_command_safe",
    "list_allowed_commands",
    "DANGEROUS_COMMANDS"
]