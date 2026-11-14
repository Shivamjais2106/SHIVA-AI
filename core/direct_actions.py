"""
Direct Action Dispatcher for S.H.I.V.A.
Executes common system, git, and media commands instantly without consuming API quota!
"""

import re
from typing import Optional, Tuple
from skills.system_skills import (
    get_system_health,
    open_in_chrome,
    search_google,
    open_social_profile,
    open_application,
    close_application,
)
from skills.project_skills import (
    list_projects,
    open_project_in_ide,
)
from skills.terminal_skills import (
    get_git_status,
    git_add_and_commit,
    execute_terminal_command,
)
from skills.media_skills import (
    control_media,
    control_volume,
    open_spotify,
)


def try_handle_direct_action(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Checks if user_input matches common desktop commands.
    Returns (handled: bool, response: Optional[str]).
    """
    msg = user_input.strip().lower()

    # 1. Blocked Git Push check
    if "git push" in msg or "push to git" in msg or "push to github" in msg:
        return (
            True,
            "⛔ [SECURITY RESTRICTION]: 'git push' is strictly disabled for automated execution. Boss, please push your changes to GitHub manually."
        )

    # 2. Git Status
    if "status" in msg and ("git" in msg or "repo" in msg or "branch" in msg or "shiva" in msg):
        project = "SHIVA-AI"
        for p in ["technokart", "shiva-ai", "kisansathi", "tims", "contentforge"]:
            if p in msg:
                project = p
        return (True, f"Boss, here is the git status:\n\n{get_git_status(project)}")

    # 3. Git Commit (e.g. "commit changes with message xyz", "commit karo ...", supports commmit/comit typos)
    if re.search(r'com+it', msg):
        # Extract commit message from quotes if present
        match = re.search(r'["\'](.*?)["\']', user_input)
        if match:
            commit_msg = match.group(1).strip()
        else:
            # Try to grab after 'message' or 'name se'
            commit_msg = "update via SHIVA"
            if "name se" in msg:
                parts = msg.split("name se")
                commit_msg = parts[0].replace('"', '').replace("'", "").strip()

        project = "SHIVA-AI"
        for p in ["technokart", "shiva-ai", "kisansathi", "tims", "contentforge"]:
            if p in msg:
                project = p

        res = git_add_and_commit(commit_msg, project)
        return (True, f"Understood, Boss! Running git add and commit:\n\n{res}")

    # 4. Media & Music
    if any(k in msg for k in ["play music", "pause music", "next song", "next track", "skip song", "prev song"]):
        if "next" in msg or "skip" in msg:
            return (True, control_media("next"))
        elif "prev" in msg:
            return (True, control_media("prev"))
        else:
            return (True, control_media("play_pause"))

    # 5. Volume
    if "volume" in msg or "mute" in msg:
        if "up" in msg or "increase" in msg or "loud" in msg:
            return (True, control_volume("up", 3))
        elif "down" in msg or "decrease" in msg or "low" in msg:
            return (True, control_volume("down", 3))
        elif "mute" in msg:
            return (True, control_volume("mute"))

    # 6. Open Spotify
    if "spotify" in msg and any(k in msg for k in ["open", "play", "start", "launch"]):
        return (True, open_spotify())

    # 7. System Health / Battery
    if any(k in msg for k in ["battery", "ram", "cpu", "system status", "system health", "health"]):
        stats = get_system_health()
        return (
            True,
            f"Boss, here is your system diagnostic:\n"
            f"• Battery: {stats['battery']}\n"
            f"• CPU Usage: {stats['cpu_usage']}\n"
            f"• RAM Usage: {stats['ram_usage']}"
        )

    # 8. List Projects
    if "list project" in msg or "what project" in msg or "show project" in msg:
        p_res = list_projects()
        if p_res.get("status") == "success":
            p_list = ", ".join(p_res.get("projects", []))
            return (True, f"Boss, here are your {p_res['total_projects']} projects in D:/Projects:\n{p_list}")

    # 9. Open Project in IDE
    # e.g. "open technokart in antigravity", "open portfolio in vscode"
    if "open" in msg and any(ide in msg for ide in ["vscode", "vs code", "antigravity"]):
        ide = "antigravity" if "antigravity" in msg else "vscode"
        # Find project name
        projects_check = ["technokart", "shiva-ai", "kisansathi", "tims", "portfolio", "contentforge", "devflow", "internova"]
        found_project = None
        for p in projects_check:
            if p in msg:
                found_project = p
                break
        if found_project:
            return (True, open_project_in_ide(found_project, ide))

    # 10. Close Application
    # e.g. "close vscode", "close chrome", "close antigravity"
    if "close" in msg:
        for app in ["vscode", "vs code", "chrome", "antigravity", "spotify", "notepad", "calculator"]:
            if app in msg:
                return (True, close_application(app))

    # 11. Social Profile
    if any(s in msg for s in ["github", "leetcode", "linkedin"]):
        if "github" in msg:
            return (True, open_social_profile("github"))
        elif "leetcode" in msg:
            return (True, open_social_profile("leetcode"))
        elif "linkedin" in msg:
            return (True, open_social_profile("linkedin"))

    return (False, None)
