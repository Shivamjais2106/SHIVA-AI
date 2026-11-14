import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any

PROJECTS_DIR = Path("D:/Projects")
VSCODE_PATH = r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd"
ANTIGRAVITY_PATH = r"C:\Users\HP\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe"


def list_projects() -> Dict[str, Any]:
    """Lists all active projects inside D:/Projects."""
    if not PROJECTS_DIR.exists():
        return {"status": "error", "message": f"Projects folder {PROJECTS_DIR} does not exist."}

    projects = []
    for item in PROJECTS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            projects.append(item.name)

    return {
        "status": "success",
        "total_projects": len(projects),
        "projects": sorted(projects),
    }


def open_project_in_ide(project_name: str, ide: str = "vscode") -> str:
    """
    Opens a specific project folder from D:/Projects in either VS Code or Antigravity IDE.
    ide can be: 'vscode' or 'antigravity'
    """
    target_path = PROJECTS_DIR / project_name
    if not target_path.exists():
        # Fuzzy match if project name was slightly mistyped
        matches = [p for p in PROJECTS_DIR.iterdir() if p.is_dir() and project_name.lower() in p.name.lower()]
        if matches:
            target_path = matches[0]
        else:
            return f"Boss, I couldn't find a project named '{project_name}' in {PROJECTS_DIR}."

    ide_choice = ide.lower().strip()

    try:
        if "antigravity" in ide_choice:
            if os.path.exists(ANTIGRAVITY_PATH):
                subprocess.Popen([ANTIGRAVITY_PATH, str(target_path)])
                return f"Opened '{target_path.name}' in Antigravity IDE, Boss! 🚀"
            else:
                return f"Antigravity IDE executable not found at {ANTIGRAVITY_PATH}."
        else:
            # Default to VS Code
            if os.path.exists(VSCODE_PATH):
                subprocess.Popen([VSCODE_PATH, str(target_path)], shell=True)
            else:
                subprocess.Popen(["code", str(target_path)], shell=True)
            return f"Opened '{target_path.name}' in VS Code, Boss! 💻"

    except Exception as e:
        return f"Failed to open project in {ide}: {e}"

