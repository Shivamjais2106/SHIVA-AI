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


def normalize_stt_text(text: str) -> str:
    """Fixes common microphone / SpeechRecognition mishearings and Hinglish phrasing."""
    t = text.lower()
    
    # Common STT phonetic replacements
    replacements = {
        "techno card": "technokart",
        "techno cart": "technokart",
        "technocart": "technokart",
        "techno guard": "technokart",
        "bs4": "vscode",
        "bs 4": "vscode",
        "bs code": "vscode",
        "vs 4": "vscode",
        "v s code": "vscode",
        "vs cod": "vscode",
        "vs-code": "vscode",
        "anti gravity": "antigravity",
        "anti-gravity": "antigravity",
        "kisan sathi": "kisansathi",
        "kisan saathi": "kisansathi",
        "kisaan sathi": "kisansathi",
        "thermal intelligence": "tims",
        "kholo": "open",
        "khol": "open",
        "chalao": "open",
        "band karo": "close",
        "band kar": "close",
        "hatao": "close",
    }
    for wrong, right in replacements.items():
        t = t.replace(wrong, right)
    return t


def try_handle_direct_action(user_input: str) -> Tuple[bool, Optional[str]]:
    """
    Checks if user_input matches common desktop commands.
    Returns (handled: bool, response: Optional[str]).
    """
    msg = normalize_stt_text(user_input.strip())

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

    # 9. Open Project or Desktop Application (100% Offline, ZERO API Key required!)
    if any(k in msg for k in ["open", "launch", "start", "khol"]):
        # Check if Boss wants it in the same window / tab
        same_window = any(
            k in msg
            for k in [
                "same tab",
                "same window",
                "same vscode",
                "along with",
                "usi mai",
                "usi me",
                "ek sath",
                "add folder",
                "add to",
            ]
        )
        ide = "antigravity" if "antigravity" in msg else "vscode"

        # Catalog of projects in D:/Projects (longest names first)
        projects_catalog = [
            "shivam-jaiswal portfolio",
            "shivam jaiswal portfolio",
            "shivam jaiswal",
            "jharkhand civic issue",
            "student-management-system",
            "internova ai",
            "contentforge",
            "kisansathi",
            "kisan sathi",
            "technokart",
            "techno card",
            "devflow",
            "internova",
            "portfolio",
            "shiva-ai",
            "shiva",
            "tims",
            "iiit-delhi",
            "iiit delhi",
        ]

        # Find ALL candidate projects mentioned in the message
        matches_with_index = []
        for p in projects_catalog:
            idx = msg.find(p)
            if idx != -1:
                matches_with_index.append((idx, len(p), p))

        if matches_with_index:
            # Determine reference position of 'open' command
            open_idx = msg.find("open")
            if open_idx == -1:
                open_idx = msg.find("khol")
            if open_idx == -1:
                open_idx = 0

            # Filter candidates appearing after 'open'
            after_open = [m for m in matches_with_index if m[0] >= open_idx]
            candidates = after_open if after_open else matches_with_index

            # Sort by lowest index (closest to 'open'), tie-break with longer string length
            candidates.sort(key=lambda x: (x[0], -x[1]))
            best_match = candidates[0][2]

            return (True, open_project_in_ide(best_match, ide=ide, same_window=same_window))

        # B. Standalone IDEs or Apps
        if "terminal" in msg:
            if "vs code" in msg or "vscode" in msg or "code" in msg:
                open_application("vscode")
                return (
                    True,
                    "Boss, VS Code is open! In VS Code, press Ctrl + ` (tilde) to open the integrated terminal, or simply tell me what command you want to run and I'll execute it right here! 🚀"
                )
            for p in ["technokart", "shiva-ai", "kisansathi", "tims", "devflow", "contentforge"]:
                if p in msg:
                    proj_path = PROJECTS_DIR / p
                    subprocess.Popen(f'start "" wt.exe -d "{proj_path}"', shell=True)
                    return (True, f"Opened Windows Terminal inside '{p}' folder, Boss! 💻")
            return (True, open_application("terminal"))

        if "antigravity" in msg:
            return (True, open_application("antigravity"))
        elif "vscode" in msg or "vs code" in msg or "code" in msg:
            return (True, open_application("vscode"))
        elif "chrome" in msg or "browser" in msg:
            return (True, open_application("chrome"))
        elif "calculator" in msg or "calc" in msg:
            return (True, open_application("calculator"))
        elif "notepad" in msg:
            return (True, open_application("notepad"))
        elif "terminal" in msg or "powershell" in msg or "cmd" in msg:
            return (True, open_application("terminal"))
        elif "explorer" in msg or "files" in msg:
            return (True, open_application("explorer"))
        elif "settings" in msg:
            return (True, open_application("settings"))
        elif "spotify" in msg:
            return (True, open_spotify())

    # 10. Close Application (100% Offline, ZERO API Key required!)
    if any(k in msg for k in ["close", "exit", "terminate", "kill"]):
        for app in [
            "vscode", "vs code", "code", "antigravity", "antigravity ide",
            "chrome", "spotify", "notepad", "calculator", "terminal"
        ]:
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

    # 12. Personal Profile / Resume Knowledge Base (100% Offline & Instant)
    if any(k in msg for k in ["contact", "phone", "mobile", "number"]):
        return (True, "Boss, your registered contact number is 7869037289.")

    if any(k in msg for k in ["email", "mail id"]):
        return (True, "Boss, your email address is shivamjais2106@gmail.com.")

    if any(k in msg for k in ["who am i", "my name", "mera naam", "about me"]):
        return (
            True,
            "You are Shivam Jaiswal, Boss! Full-Stack MERN Developer and AI Engineer currently interning at Fakhri IT Services."
        )

    if any(k in msg for k in ["college", "university", "education", "degree", "study"]):
        return (
            True,
            "Boss, you are pursuing B.Tech in Computer Science & Information Technology at Sagar Institute of Research and Technology (SIRT), Bhopal (2023–2027)."
        )

    if any(k in msg for k in ["company", "internship", "job", "fakhri", "current work"]):
        return (
            True,
            "Boss, you are working as a MERN Stack Developer Intern at Fakhri IT Services, handling JamaatCloud, Fakhri Workspace chat audit, and Amazon Shipping API v2."
        )

    if any(k in msg for k in ["my skills", "tech stack", "languages"]):
        return (
            True,
            "Boss, your core stack includes React.js, Next.js, Node.js, Express, MongoDB, Python, FastAPI, Docker, and Gemini AI."
        )

    if any(k in msg for k in ["city", "location", "address", "where do i live"]):
        return (True, "Boss, you are based in Bhopal, Madhya Pradesh.")

    return (False, None)

