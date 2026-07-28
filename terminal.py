"""
Terminal Routes - PTY-based Terminal
Implement terminal thực sự với PTY (pseudo-terminal)
"""

import os
import pty
import select
import signal
import termios
import struct
import fcntl
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("mcp-server")

# Store terminal sessions
terminal_sessions: Dict[str, Dict[str, Any]] = {}


def set_winsize(fd, rows, cols):
    """Set terminal window size"""
    try:
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
    except Exception as e:
        logger.warning(f"Failed to set window size: {e}")


def create_terminal_session(session_id: str, cols: int = 80, rows: int = 24, cwd: str = "/data") -> Dict[str, Any]:
    """Create a new terminal session with PTY"""
    try:
        master_fd, slave_fd = pty.openpty()
        
        # Set window size
        set_winsize(master_fd, rows, cols)
        
        # Fork child process
        pid = os.fork()
        if pid == 0:  # Child process
            os.close(master_fd)
            os.setsid()
            
            # Duplicate slave_fd to stdin, stdout, stderr
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            
            # Close slave_fd if it's not one of the standard fds
            if slave_fd > 2:
                os.close(slave_fd)
            
            # Change to working directory
            os.chdir(cwd)
            
            # Set environment variables
            os.environ["TERM"] = "xterm-256color"
            os.environ["HOME"] = os.path.expanduser("~")
            os.environ["SHELL"] = "/bin/bash"
            
            # Execute bash
            os.execve("/bin/bash", ["/bin/bash", "--login"], os.environ)
            os._exit(1)
        
        # Parent process
        os.close(slave_fd)
        
        # Store session
        terminal_sessions[session_id] = {
            "master_fd": master_fd,
            "child_pid": pid,
            "buffer": b"",
            "started": True,
            "cols": cols,
            "rows": rows,
            "cwd": cwd
        }
        
        # Give bash a moment to start
        time.sleep(0.1)
        
        logger.info(f"Terminal session {session_id} started, PID: {pid}")
        return {"status": "success", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Failed to create terminal session: {e}")
        return {"status": "error", "message": str(e)}


def write_to_terminal(session_id: str, data: str) -> Dict[str, Any]:
    """Write input to terminal"""
    if session_id not in terminal_sessions:
        return {"status": "error", "message": "Session not found"}
    
    session = terminal_sessions[session_id]
    if not session["started"]:
        return {"status": "error", "message": "Terminal not started"}
    
    try:
        os.write(session["master_fd"], data.encode("utf-8"))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to write to terminal: {e}")
        return {"status": "error", "message": str(e)}


def read_from_terminal(session_id: str) -> Dict[str, Any]:
    """Read output from terminal"""
    if session_id not in terminal_sessions:
        return {"status": "error", "message": "Session not found", "output": "", "alive": False}
    
    session = terminal_sessions[session_id]
    if not session["started"]:
        return {"status": "error", "message": "Terminal not started", "output": "", "alive": False}
    
    try:
        # Read all available data
        while True:
            r, _, _ = select.select([session["master_fd"]], [], [], 0.01)
            if r:
                data = os.read(session["master_fd"], 4096)
                if not data:
                    # EOF - child process terminated
                    cleanup_terminal_session(session_id)
                    break
                session["buffer"] += data
            else:
                break
        
        # Get output
        output = session["buffer"]
        session["buffer"] = b""
        
        # Check if child is still alive
        is_alive = session["started"]
        if is_alive:
            try:
                pid, status = os.waitpid(session["child_pid"], os.WNOHANG)
                if pid > 0:
                    # Child terminated
                    is_alive = False
                    cleanup_terminal_session(session_id)
            except Exception:
                pass
        
        return {
            "status": "success",
            "output": output.decode("utf-8", errors="replace"),
            "alive": is_alive
        }
        
    except Exception as e:
        logger.error(f"Failed to read from terminal: {e}")
        cleanup_terminal_session(session_id)
        return {"status": "error", "message": str(e), "output": "", "alive": False}


def resize_terminal(session_id: str, cols: int, rows: int) -> Dict[str, Any]:
    """Resize terminal"""
    if session_id not in terminal_sessions:
        return {"status": "error", "message": "Session not found"}
    
    session = terminal_sessions[session_id]
    if not session["started"]:
        return {"status": "error", "message": "Terminal not started"}
    
    try:
        set_winsize(session["master_fd"], rows, cols)
        session["cols"] = cols
        session["rows"] = rows
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to resize terminal: {e}")
        return {"status": "error", "message": str(e)}


def cleanup_terminal_session(session_id: str):
    """Clean up terminal session"""
    if session_id not in terminal_sessions:
        return
    
    session = terminal_sessions[session_id]
    
    try:
        # Kill child process
        if session["child_pid"]:
            try:
                os.kill(session["child_pid"], signal.SIGHUP)
                time.sleep(0.1)
                os.kill(session["child_pid"], signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception as e:
                logger.warning(f"Error killing child process: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    # Close master fd
    try:
        if session["master_fd"] is not None:
            os.close(session["master_fd"])
    except Exception:
        pass
    
    # Remove session
    terminal_sessions.pop(session_id, None)
    logger.info(f"Terminal session {session_id} cleaned up")


def cleanup_all_sessions():
    """Clean up all terminal sessions"""
    for session_id in list(terminal_sessions.keys()):
        cleanup_terminal_session(session_id)