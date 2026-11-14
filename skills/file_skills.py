import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from skills.safety import request_deletion, verify_and_clear_deletion

PROJECTS_DIR = Path("D:/Projects")


def resolve_path(path_str: str) -> Path:
    """Resolves relative or project-relative paths cleanly."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    # Check if inside D:/Projects
    candidate = PROJECTS_DIR / path_str
    if candidate.exists():
        return candidate
    return Path.cwd() / path_str


def list_files(folder_path: str) -> Dict[str, Any]:
    """Lists files and folders inside a directory."""
    target = resolve_path(folder_path)
    if not target.exists() or not target.is_dir():
        return {"status": "error", "message": f"Folder '{folder_path}' does not exist, Boss."}

    items: List[Dict[str, Any]] = []
    try:
        for entry in target.iterdir():
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size_bytes": entry.stat().st_size if entry.is_file() else None,
            })
        return {
            "status": "success",
            "path": str(target),
            "total_items": len(items),
            "items": sorted(items, key=lambda x: (not x["is_dir"], x["name"])),
        }
    except Exception as e:
        return {"status": "error", "message": f"Error reading folder: {e}"}


def read_file(file_path: str, max_lines: int = 150) -> Dict[str, Any]:
    """Reads content of a specific file."""
    target = resolve_path(file_path)
    if not target.exists() or not target.is_file():
        return {"status": "error", "message": f"File '{file_path}' does not exist, Boss."}

    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(max_lines)]
            content = "".join(lines)
            return {
                "status": "success",
                "file": str(target),
                "content": content,
                "lines_read": len(lines),
            }
    except Exception as e:
        return {"status": "error", "message": f"Error reading file '{file_path}': {e}"}


def edit_file(file_path: str, find_text: str, replace_text: str) -> str:
    """Finds and replaces specific text in a file."""
    target = resolve_path(file_path)
    if not target.exists() or not target.is_file():
        return f"Boss, the file '{file_path}' does not exist."

    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()

        if find_text not in content:
            return f"Boss, the target text was not found inside '{target.name}'. No changes were made."

        new_content = content.replace(find_text, replace_text)
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"Successfully updated '{target.name}', Boss! Target text was replaced."
    except Exception as e:
        return f"Failed to edit file '{target.name}': {e}"


def create_or_write_file(file_path: str, content: str) -> str:
    """Creates a new file or writes content to it."""
    target = resolve_path(file_path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File '{target.name}' written successfully at {target.parent}, Boss."
    except Exception as e:
        return f"Failed to write file '{file_path}': {e}"


def safe_delete_path(target_path: str, confirmation_stage: str = "") -> str:
    """
    STRICT SAFETY RULE:
    Enforces mandatory 2-step verification before deleting ANY file or folder.
    """
    target = resolve_path(target_path)
    if not target.exists():
        return f"Boss, '{target_path}' does not exist on disk."

    normalized_path = str(target.resolve())

    if confirmation_stage == "":
        return request_deletion(normalized_path)

    confirmed, message = verify_and_clear_deletion(normalized_path, confirmation_stage)
    if not confirmed:
        return message

    # If confirmed past stage 2:
    try:
        if target.is_dir():
            shutil.rmtree(target)
            return f"✅ [DELETED]: Folder '{target.name}' has been permanently deleted after 2x confirmations, Boss."
        else:
            target.unlink()
            return f"✅ [DELETED]: File '{target.name}' has been permanently deleted after 2x confirmations, Boss."
    except Exception as e:
        return f"Failed to delete '{target.name}': {e}"

