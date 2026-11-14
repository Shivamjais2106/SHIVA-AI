"""
Terminal & Command Execution Skill for S.H.I.V.A.
Executes developer and system shell commands safely.
STRICT SECURITY POLICY:
- Blocks 'git push' (Boss retains 100% manual push control).
- Blocks destructive system wiping commands.
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

PROJECTS_DIR = Path("D:/Projects")

# Explicitly banned command substrings
BLOCKED_PATTERNS = [
    "git push",
    "rmdir /s /q c:",
    "rmdir /s /q c:\\",
    "del /f /s /q c:",
    "format c:",
    ":(){ :|:& };:",
]


def execute_terminal_command(command: str, working_directory: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a terminal/PowerShell command (e.g. git add, git commit, npm, python, dir).
    STRICT SECURITY RULE: 'git push' is permanently blocked.
    """
    cmd_clean = command.strip()
    cmd_lower = cmd_clean.lower()

    # Security check: Git push block
    if "git push" in cmd_lower:
        return {
            "status": "blocked",
            "message": "⛔ [SECURITY RESTRICTION]: 'git push' is strictly disabled for automated execution. Boss, please push your changes to GitHub manually.",
        }

    # Security check: Destructive wiping commands
    for pattern in BLOCKED_PATTERNS:
        if pattern in cmd_lower:
            return {
                "status": "blocked",
                "message": f"⛔ [SECURITY ALERT]: Dangerous command blocked by SHIVA core security rules: '{command}'",
            }

    # Determine working directory
    cwd = PROJECTS_DIR
    if working_directory:
        candidate = Path(working_directory)
        if candidate.is_absolute() and candidate.exists():
            cwd = candidate
        elif (PROJECTS_DIR / working_directory).exists():
            cwd = PROJECTS_DIR / working_directory
        elif (Path.cwd() / working_directory).exists():
            cwd = Path.cwd() / working_directory

    try:
        # Run command via powershell
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd_clean],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=45,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        return {
            "status": "success" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "cwd": str(cwd),
            "output": stdout if stdout else (stderr if stderr else "Command finished with no output."),
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "message": f"Command timed out after 45 seconds: '{command}'. (If you started a long dev server, it might be running in background).",
        }
    except Exception as e:
        return {"status": "error", "message": f"Execution error: {e}"}



def get_git_status(project_name: str = "SHIVA-AI") -> str:
    """
    Directly checks the git status (uncommitted, modified, untracked files) of any project folder in D:/Projects.
    """
    res = execute_terminal_command("git status", project_name)
    if res.get("status") == "success":
        return f"Git Status for '{project_name}':\n{res.get('output')}"
    return f"Could not get git status for '{project_name}': {res.get('message', res.get('output'))}"


def git_add_and_commit(commit_message: str, project_name: str = "SHIVA-AI") -> str:
    """
    Runs 'git add .' and 'git commit -m <commit_message>' on a project.
    Remember: 'git push' is NOT allowed.
    """
    res_add = execute_terminal_command("git add .", project_name)
    if res_add.get("status") != "success":
        return f"Failed to git add: {res_add.get('output')}"

    res_commit = execute_terminal_command(f'git commit -m "{commit_message}"', project_name)
    return f"Git Commit Result for '{project_name}':\n{res_commit.get('output')}"
