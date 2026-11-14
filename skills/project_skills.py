import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

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


def find_best_project_match(query: str) -> Optional[Path]:
    """Finds the best matching project folder in D:/Projects with fuzzy & prefix matching."""
    if not PROJECTS_DIR.exists():
        return None

    clean_query = query.lower().replace("-", " ").replace("_", " ").strip()
    folders = [p for p in PROJECTS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")]

    # Sort folders by name length descending (match longer specific names first like 'Shivam-Jaiswal Portfolio' before 'Portfolio')
    folders_sorted = sorted(folders, key=lambda p: len(p.name), reverse=True)

    # 1. Exact match
    for f in folders_sorted:
        f_clean = f.name.lower().replace("-", " ").replace("_", " ")
        if f_clean == clean_query:
            return f

    # 2. Substring match
    for f in folders_sorted:
        f_clean = f.name.lower().replace("-", " ").replace("_", " ")
        if f_clean in clean_query or clean_query in f_clean:
            return f

    # 3. Word-level match (e.g. 'shivam jaiswal' matches 'Shivam-Jaiswal Portfolio')
    query_words = clean_query.split()
    for f in folders_sorted:
        f_clean = f.name.lower().replace("-", " ").replace("_", " ")
        if all(w in f_clean for w in query_words if len(w) > 2):
            return f

    return None


def open_project_in_ide(project_name: str, ide: str = "vscode", same_window: bool = False) -> str:
    """
    Opens a specific project folder from D:/Projects in either VS Code or Antigravity IDE.
    If same_window is True, adds the folder to the current VS Code workspace window.
    """
    target_path = find_best_project_match(project_name)
    if not target_path or not target_path.exists():
        target_path = PROJECTS_DIR / project_name
        if not target_path.exists():
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
            # VS Code
            executable = VSCODE_PATH if os.path.exists(VSCODE_PATH) else "code"
            # If same_window requested, use -a / --add to add folder to current window workspace!
            if same_window:
                cmd = f'"{executable}" -a "{str(target_path)}"'
                subprocess.Popen(cmd, shell=True)
                return f"Added '{target_path.name}' into your current VS Code workspace, Boss! 💻"
            else:
                cmd = f'"{executable}" "{str(target_path)}"'
                subprocess.Popen(cmd, shell=True)
                return f"Opened '{target_path.name}' in VS Code, Boss! 💻"

    except Exception as e:
        return f"Failed to open project in {ide}: {e}"
