"""
Direct Action Dispatcher for S.H.I.V.A.
Executes common system, git, media, email, and WhatsApp commands instantly without consuming API quota!
"""

import re
import urllib.parse
from typing import Optional, Tuple
from skills.system_skills import (
    get_system_health,
    open_in_chrome,
    search_google,
    open_portfolio,
    open_social_profile,
    close_browser_tab,
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
from skills.email_skills import (
    open_gmail,
    compose_email_in_browser,
    read_emails,
    send_email,
    get_24h_email_briefing,
    get_morning_briefing,
)
from skills.whatsapp_skills import (
    send_whatsapp_message,
    initiate_whatsapp_call,
    simulate_incoming_whatsapp,
    get_whatsapp_inbox,
    add_known_contact,
    list_known_contacts,
    toggle_whatsapp_auto_responder,
)
from skills.news_skills import (
    get_latest_news,
    get_weather,
    search_web_realtime,
)


def normalize_stt_text(text: str) -> str:
    """Fixes common microphone / SpeechRecognition mishearings and Hinglish phrasing."""
    t = text.lower().strip()

    replacements = {
        # Projects & Tech names
        "techno card": "technokart",
        "techno cart": "technokart",
        "technocart": "technokart",
        "techno guard": "technokart",
        "anti gravity": "antigravity",
        "anti-gravity": "antigravity",
        "kisan sathi": "kisansathi",
        "kisan saathi": "kisansathi",
        "kisaan sathi": "kisansathi",
        "thermal intelligence": "tims",
        # LeetCode phonetic fixes
        "lead code": "leetcode",
        "leet code": "leetcode",
        "late code": "leetcode",
        "leadcode": "leetcode",
        "liitcode": "leetcode",
        # VS Code phonetic fixes
        "bs4": "vscode",
        "bs 4": "vscode",
        "bs code": "vscode",
        "vs 4": "vscode",
        "v s code": "vscode",
        "vs cod": "vscode",
        "vs-code": "vscode",
        # Web & Socials
        "git hub": "github",
        "linked in": "linkedin",
        "port folio": "portfolio",
        "whatsup": "whatsapp",
        "whats app": "whatsapp",
        "watsp": "whatsapp",
        "whastapp": "whatsapp",
        # Actions / Hinglish
        "kholo": "open",
        "khol": "open",
        "chalao": "open",
        "dikhau": "show",
        "dikhao": "show",
        "band karo": "close",
        "band kar": "close",
        "hatao": "close",
        "bhejo": "send",
        "daalo": "send",
        "padho": "read",
        "padh ke batao": "read",
    }
    # Replace multi-word and phonetic variants with word boundaries, longest matches first
    for wrong in sorted(replacements.keys(), key=len, reverse=True):
        pattern = r'\b' + re.escape(wrong) + r'\b'
        t = re.sub(pattern, replacements[wrong], t)
    return t


def extract_whatsapp_info(text: str) -> Tuple[str, str]:
    """
    Extracts recipient (name or phone number) and message text from user command.
    Supports English & Hinglish formats:
    - 'send whatsapp to Rahul message hey how are you'
    - 'send whatsapp to 7869037289 message hello'
    - 'Rahul ko whatsapp message bhejo: meeting at 5'
    - 'whatsapp message to Mom: where are you'
    """
    raw = text.strip()

    # Quoted message has top priority
    quote_match = re.search(r'["\'](.*?)["\']', raw)
    if quote_match:
        msg = quote_match.group(1).strip()
        non_msg = raw.replace(quote_match.group(0), "")
    else:
        if ":" in raw:
            parts = raw.split(":", 1)
            non_msg = parts[0]
            msg = parts[1].strip()
        elif " saying " in raw.lower():
            idx = raw.lower().find(" saying ")
            non_msg = raw[:idx]
            msg = raw[idx + 8:].strip()
        elif re.search(r'\b(?:to|ko)\b.*\b(?:message|msg)\b', raw, re.IGNORECASE):
            parts = re.split(r'\b(?:message|msg)\b', raw, flags=re.IGNORECASE)
            non_msg = parts[0]
            msg = parts[1].strip() if len(parts) > 1 else ""
        elif re.search(r'\b(?:message|msg)\b.*\bto\s+([A-Za-z0-9_\-]+)', raw, re.IGNORECASE):
            to_match = re.search(r'\bto\s+([A-Za-z0-9_\-]+)\s*(.*)', raw, re.IGNORECASE)
            if to_match:
                non_msg = f"to {to_match.group(1)}"
                msg = to_match.group(2).strip()
            else:
                non_msg = raw
                msg = ""
        else:
            non_msg = raw
            msg = "Hello from Shivam Jaiswal via SHIVA!"

    # Clean msg text
    msg = re.sub(r'^(?:saying|that|is|\:)\s*', '', msg, flags=re.IGNORECASE)
    msg = re.sub(r'\s*\b(bhejo|send karo|drop karo)\b\s*$', '', msg, flags=re.IGNORECASE).strip()
    if not msg:
        msg = "Hello from Shivam Jaiswal via SHIVA!"

    # Check for phone number first
    phone_match = re.search(r'\+?\d{10,12}', raw)
    if phone_match:
        return phone_match.group(0), msg

    target = ""
    m_to = re.search(r'\bto\s+([A-Za-z0-9_\-]+)', non_msg, re.IGNORECASE)
    if m_to and m_to.group(1).lower() not in ["whatsapp", "the", "my"]:
        target = m_to.group(1).strip()
    elif re.search(r'([A-Za-z0-9_\-]+)\s+ko\b', non_msg, re.IGNORECASE):
        target = re.search(r'([A-Za-z0-9_\-]+)\s+ko\b', non_msg, re.IGNORECASE).group(1).strip()
    elif re.search(r'\bcall\s+([A-Za-z0-9_\-]+)', non_msg, re.IGNORECASE):
        cand = re.search(r'\bcall\s+([A-Za-z0-9_\-]+)', non_msg, re.IGNORECASE).group(1).strip()
        if cand.lower() not in ["whatsapp", "on"]:
            target = cand
    elif re.search(r'\bwhatsapp\s+([A-Za-z0-9_\-]+)', non_msg, re.IGNORECASE):
        cand = re.search(r'\bwhatsapp\s+([A-Za-z0-9_\-]+)', non_msg, re.IGNORECASE).group(1).strip()
        if cand.lower() not in ["message", "msg", "call", "web", "desktop", "bot", "par", "pe", "per"]:
            target = cand

    return target, msg


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

    # 2. Browser Tab Close vs Application Close
    # (Fixes Issue: "close my github on chrome" closing the entire Chrome browser process)
    if any(k in msg for k in ["close", "exit", "terminate", "kill"]):
        # A. Check if the user is targeting a browser tab / website
        is_tab_close = (
            "tab" in msg
            or any(site in msg for site in ["github", "leetcode", "portfolio", "website", "linkedin", "gmail"])
        )
        if is_tab_close:
            return (True, close_browser_tab())

        # B. Application process termination (Only when full app is targeted)
        for app in [
            "antigravity ide", "antigravity",
            "chrome", "spotify", "notepad", "calculator", "terminal", "whatsapp"
        ]:
            if app in msg:
                return (True, close_application(app))

        # Separate VS Code check using word boundaries to never match leetcode
        if re.search(r'\b(vscode|vs\s*code)\b', msg) or (re.search(r'\bcode\b', msg) and "leetcode" not in msg):
            return (True, close_application("vscode"))

    # 3. Personal Portfolio Direct Opening (Fixes Issue: Searching Google instead of opening live portfolio)
    # If Boss asks for portfolio and doesn't specify VS Code / project folder, open live portfolio directly!
    if "portfolio" in msg:
        # Check if Boss specifically meant the project folder in VS Code / IDE
        is_ide_request = any(k in msg for k in ["vscode", "vs code", "antigravity", "ide", "project folder", "code mai", "code me"])
        if is_ide_request:
            ide = "antigravity" if "antigravity" in msg else "vscode"
            return (True, open_project_in_ide("Shivam-Jaiswal Portfolio", ide=ide))
        else:
            return (True, open_portfolio())

    # 4. Social & Professional Profiles (Fixes Issue: "open leetcode" launching VS Code)
    # Check these BEFORE any generic application or project open logic!
    if "leetcode" in msg:
        return (True, open_social_profile("leetcode"))

    if "github" in msg:
        return (True, open_social_profile("github"))

    if "linkedin" in msg:
        return (True, open_social_profile("linkedin"))

    # 5. Gmail & Email Integration (24h Digest, Morning Briefing, Important Emails, Read & Send)
    if any(k in msg for k in ["gmail", "email", "mail"]):
        # A. 24-Hour Overall Digest & Count
        if any(k in msg for k in ["24 ghante", "24 hours", "24 hour", "24 ghant", "overall", "kitne mail", "digest", "briefing"]):
            res = get_24h_email_briefing(timeframe_hours=24)
            return (True, res["message"])

        # B. Night to Morning / Morning Digest
        if any(k in msg for k in ["night se morning", "raat se subah", "subah", "morning", "overnight"]):
            res = get_morning_briefing()
            return (True, res["message"])

        # C. Important / Priority Emails
        if any(k in msg for k in ["important", "priority", "urgent", "khas", "jaruri"]):
            res = get_24h_email_briefing(timeframe_hours=24)
            return (True, res["message"])

        # D. General Check / Read Inbox
        if any(k in msg for k in ["read", "check", "inbox", "unread", "dekho", "batao", "status", "list", "padh"]):
            res = read_emails(limit=5, unread_only=False)
            return (True, res["message"])

        # E. Send / Compose Email
        if any(k in msg for k in ["send", "write", "compose", "draft", "bhejo", "karo"]):
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
            to_email = email_match.group(0) if email_match else ""

            subject_match = re.search(r'["\'](.*?)["\']', user_input)
            subject = subject_match.group(1) if subject_match else "Note from Shivam Jaiswal"

            if to_email:
                res = send_email(to_email=to_email, subject=subject, body="Hello, sending this email via S.H.I.V.A.")
                return (True, res["message"])
            else:
                return (True, compose_email_in_browser(to_email="", subject=subject, body=""))

        # F. Simple "open gmail"
        if any(k in msg for k in ["open", "launch", "khol"]):
            return (True, open_gmail())

    # 6. Real-Time News & Headlines (Google News RSS - 100% Live)
    if any(k in msg for k in ["news", "khabar", "samachar", "headlines", "taaza khabar", "current affairs"]):
        is_browser_cmd = any(k in msg for k in ["open in chrome", "open browser", "open website", "kholo chrome", "chrome mein", "chrome mai"])
        if is_browser_cmd:
            open_in_chrome("https://news.google.com")
            return (True, "Boss, Google News Chrome browser mein open kar diya hai! 📰")

        category = "general"
        if any(k in msg for k in ["tech", "technology", "ai", "software", "coding"]):
            category = "technology"
        elif any(k in msg for k in ["cricket", "sports", "football", "khel"]):
            category = "sports"
        elif any(k in msg for k in ["business", "market", "finance", "crypto", "sensex", "nifty"]):
            category = "business"
        elif any(k in msg for k in ["bhopal", "delhi", "mumbai", "india"]):
            for loc in ["bhopal", "delhi", "mumbai", "india"]:
                if loc in msg:
                    category = loc
                    break

        news_res = get_latest_news(category=category, limit=5)
        return (True, news_res.get("message", "Boss, live news fetch karne mein network issue aaya."))

    # 7. Real-Time Weather & Temperature (wttr.in - 100% Live)
    if any(k in msg for k in ["weather", "mausam", "temperature", "forecast", "barsaat", "baarish"]):
        city = "Bhopal"
        for candidate in ["delhi", "mumbai", "indore", "bangalore", "pune", "kolkata", "bhopal", "chennai", "jaipur"]:
            if candidate in msg:
                city = candidate.capitalize()
                break
        weather_res = get_weather(city=city)
        return (True, weather_res.get("message", f"Boss, {city} ka live weather fetch nahi ho saka."))

    # 8. Contact Directory Management (add contact, save contact, list contacts)
    if any(k in msg for k in ["add contact", "save contact", "contact save"]):
        phone_match = re.search(r'\+?\d{10,12}', user_input)
        name_match = re.search(r'(?:contact|save)\s+([A-Za-z0-9_\-]+)', user_input, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else ""
        if name.lower() in ["number", "phone"]:
            m = re.search(r'([A-Za-z0-9_\-]+)\s+ka\s+number', user_input, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
        if name and phone_match:
            return (True, add_known_contact(name=name, phone=phone_match.group(0)))
        else:
            return (True, "Boss, please specify the contact name and 10-digit number. E.g., 'add contact Rahul phone 9876543210'")

    if any(k in msg for k in ["list contact", "show contact", "my contacts", "contacts list", "mere contacts"]):
        contacts_res = list_known_contacts()
        contacts = contacts_res.get("contacts", [])
        if not contacts:
            return (True, "Boss, you don't have any contacts saved yet.")
        lines = [f"📇 Saved Contacts ({len(contacts)}):"]
        for c in contacts:
            lines.append(f"• {c['name']}: {c['phone']} ({c.get('relationship', 'Contact')})")
        return (True, "\n".join(lines))

    # 7. WhatsApp & Call Integration
    if "whatsapp" in msg:
        # A. Auto-responder status / toggle
        if "bot" in msg or "auto responder" in msg or "auto-responder" in msg:
            if any(k in msg for k in ["off", "disable", "stop"]):
                return (True, toggle_whatsapp_auto_responder(False))
            elif any(k in msg for k in ["on", "enable", "start"]):
                return (True, toggle_whatsapp_auto_responder(True))

        # B. Check WhatsApp Inbox / inquiries
        if any(k in msg for k in ["inbox", "inquiries", "queries", "messages", "log"]):
            inbox = get_whatsapp_inbox()
            msgs = inbox.get("messages", [])
            if not msgs:
                return (True, "Boss, no new WhatsApp messages or unknown inquiries logged yet.")
            summary = [f"📱 WhatsApp Inquiries ({len(msgs)} total):"]
            for m in msgs[-3:]:
                summary.append(f"• From: {m['sender_name']} ({m['sender_phone']}) | Msg: {m['message']}")
            return (True, "\n".join(summary))

        # C. Simulate incoming message from unknown number
        if "simulate" in msg:
            phone_match = re.search(r'\+?\d{10,12}', msg)
            test_phone = phone_match.group(0) if phone_match else "+919876543210"
            return (True, simulate_incoming_whatsapp(test_phone, "Hi, I want to inquire about a project."))

        # D. Initiate WhatsApp Call (by name or number)
        if "call" in msg:
            target, _ = extract_whatsapp_info(user_input)
            if not target:
                target = "7869037289"
            return (True, initiate_whatsapp_call(target, call_type="video" if "video" in msg else "voice"))

        # E. Send WhatsApp Message (by name or number)
        if any(k in msg for k in ["send", "drop", "message", "msg", "bhejo"]):
            target, msg_content = extract_whatsapp_info(user_input)
            if target:
                return (True, send_whatsapp_message(target, msg_content))
            else:
                return (True, send_whatsapp_message("7869037289", msg_content))

        # F. Open WhatsApp application
        if any(k in msg for k in ["open", "launch", "khol"]):
            return (True, open_application("whatsapp"))

    # Direct Call request without 'whatsapp' keyword
    if "call" in msg and any(k in msg for k in ["make a call", "call lagao", "call karo"]):
        target, _ = extract_whatsapp_info(user_input)
        if target:
            return (True, initiate_whatsapp_call(target))

    # 7. Git Status
    if "status" in msg and ("git" in msg or "repo" in msg or "branch" in msg or "shiva" in msg):
        project = "SHIVA-AI"
        for p in ["technokart", "shiva-ai", "kisansathi", "tims", "contentforge"]:
            if p in msg:
                project = p
        raw_status = get_git_status(project)
        if "working tree clean" in raw_status.lower() or "nothing to commit" in raw_status.lower():
            return (True, f"Boss, {project} repository bilkul clean hai, koi uncommitted changes nahi hain.")
        else:
            return (True, f"Boss, {project} repository mein changes hain:\n\n{raw_status}")

    # 8. Git Commit
    if re.search(r'com+it', msg):
        match = re.search(r'["\'](.*?)["\']', user_input)
        if match:
            commit_msg = match.group(1).strip()
        else:
            commit_msg = "update via SHIVA"
            if "name se" in msg:
                parts = msg.split("name se")
                commit_msg = parts[0].replace('"', '').replace("'", "").strip()

        project = "SHIVA-AI"
        for p in ["technokart", "shiva-ai", "kisansathi", "tims", "contentforge"]:
            if p in msg:
                project = p

        res = git_add_and_commit(commit_msg, project)
        return (True, f"Boss, changes ko '{commit_msg}' message ke saath commit kar diya hai.")

    # 9. Media & Music
    if any(k in msg for k in ["play music", "pause music", "next song", "next track", "skip song", "prev song"]):
        if "next" in msg or "skip" in msg:
            control_media("next")
            return (True, "Next track play kar diya hai, Boss.")
        elif "prev" in msg:
            control_media("prev")
            return (True, "Previous track play kar diya hai, Boss.")
        else:
            control_media("play_pause")
            return (True, "Music toggle kar diya hai, Boss.")

    # 10. Volume
    if "volume" in msg or "mute" in msg:
        if "up" in msg or "increase" in msg or "loud" in msg:
            control_volume("up", 3)
            return (True, "Volume increase kar diya hai, Boss.")
        elif "down" in msg or "decrease" in msg or "low" in msg:
            control_volume("down", 3)
            return (True, "Volume kam kar diya hai, Boss.")
        elif "mute" in msg:
            control_volume("mute")
            return (True, "System mute toggle kar diya hai, Boss.")

    # 11. Open Spotify
    if "spotify" in msg and any(k in msg for k in ["open", "play", "start", "launch"]):
        return (True, open_spotify())

    # 12. System Health / Battery
    if re.search(r'\b(battery|ram|cpu|system status|system health|pc health|laptop health)\b', msg):
        stats = get_system_health()
        return (
            True,
            f"Boss, system healthy hai: Battery {stats['battery']} par hai, CPU {stats['cpu_usage']} aur RAM {stats['ram_usage']} chal raha hai."
        )

    # 13. List Projects
    if "list project" in msg or "what project" in msg or "show project" in msg:
        p_res = list_projects()
        if p_res.get("status") == "success":
            p_list = ", ".join(p_res.get("projects", []))
            return (True, f"Boss, here are your {p_res['total_projects']} projects in D:/Projects:\n{p_list}")

    # 14. Open Project or Desktop Application
    if any(k in msg for k in ["open", "launch", "start", "khol"]):
        # Check if Boss wants it in the same window / tab
        same_window = any(
            k in msg
            for k in [
                "same tab", "same window", "same vscode", "along with",
                "usi mai", "usi me", "ek sath", "add folder", "add to",
            ]
        )
        ide = "antigravity" if "antigravity" in msg else "vscode"

        # Catalog of projects in D:/Projects (excluding naked "portfolio" to prevent conflicts with live portfolio website)
        projects_catalog = [
            "shivam-jaiswal portfolio",
            "shivam jaiswal portfolio",
            "jharkhand civic issue",
            "student-management-system",
            "internova ai",
            "contentforge",
            "kisansathi",
            "technokart",
            "devflow",
            "internova",
            "shiva-ai",
            "shiva",
            "tims",
            "iiit-delhi",
            "iiit delhi",
        ]

        matches_with_index = []
        for p in projects_catalog:
            idx = msg.find(p)
            if idx != -1:
                matches_with_index.append((idx, len(p), p))

        if matches_with_index:
            open_idx = msg.find("open")
            if open_idx == -1:
                open_idx = 0

            after_open = [m for m in matches_with_index if m[0] >= open_idx]
            candidates = after_open if after_open else matches_with_index
            candidates.sort(key=lambda x: (x[0], -x[1]))
            best_match = candidates[0][2]

            return (True, open_project_in_ide(best_match, ide=ide, same_window=same_window))

        # Desktop Applications
        if "terminal" in msg:
            if re.search(r'\b(vscode|vs\s*code|code)\b', msg) and "leetcode" not in msg:
                open_application("vscode")
                return (
                    True,
                    "Boss, VS Code is open! In VS Code, press Ctrl + ` (tilde) to open the integrated terminal, or tell me what command to execute! 🚀"
                )
            for p in ["technokart", "shiva-ai", "kisansathi", "tims", "devflow", "contentforge"]:
                if p in msg:
                    from skills.project_skills import PROJECTS_DIR
                    import subprocess
                    proj_path = PROJECTS_DIR / p
                    subprocess.Popen(f'start "" wt.exe -d "{proj_path}"', shell=True)
                    return (True, f"Opened Windows Terminal inside '{p}' folder, Boss! 💻")
            return (True, open_application("terminal"))

        if "antigravity" in msg:
            return (True, open_application("antigravity"))
        # Strict VS Code regex: requires word boundaries and never matches 'leetcode'
        elif re.search(r'\b(vscode|vs\s*code)\b', msg) or (re.search(r'\bcode\b', msg) and "leetcode" not in msg):
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
        elif "whatsapp" in msg:
            return (True, open_application("whatsapp"))

    # 15. Real-Time Web Search & Google Integration (With co-reference resolution)
    if re.search(r'\b(?:search|google|dhoondo|pata karo)\b', msg) and not any(k in msg for k in ["open tab", "close"]):
        is_chrome_cmd = any(k in msg for k in ["in chrome", "on chrome", "open google", "chrome mein", "chrome mai", "browser mein"])
        clean_query = re.sub(r'^(?:please|can you|hey shiva|shiva|yes|okey|okay|bro)\s*', '', user_input, flags=re.IGNORECASE).strip()
        clean_query = re.sub(r'^(?:search|google|search for|google search|search its info|search about|pata karo|dhoondo)\s*', '', clean_query, flags=re.IGNORECASE).strip()
        clean_query = re.sub(r'\s*\b(?:on google|in google|karo|kar do|kar dijiye)\b\s*$', '', clean_query, flags=re.IGNORECASE).strip()

        # Resolve pronouns like "its info", "about it", "this" from conversation memory
        if not clean_query or clean_query.lower() in ["it", "its", "its info", "info", "this", "about it"]:
            from memory.memory_manager import MemoryManager
            mem = MemoryManager()
            last_topic = mem.get_last_topic()
            clean_query = f"{last_topic} in detail" if last_topic else "Next.js in detail"

        if is_chrome_cmd:
            search_google(clean_query)
            return (True, f"Boss, Google Chrome mein '{clean_query}' search kar diya hai! 🔍")

        # Autonomously fetch live web information and answer directly!
        realtime_res = search_web_realtime(clean_query)
        if realtime_res.get("status") == "success":
            return (True, realtime_res.get("message"))
        else:
            search_google(clean_query)
            return (True, f"Boss, Google Chrome mein '{clean_query}' search kar diya hai! 🔍")

    # 16. Personal Profile / Resume Knowledge Base (Only when asking about Boss's personal identity/profile!)
    is_personal_query = bool(re.search(r'\b(my|mera|meri|mere|mine|shivam|apna|apni)\b', msg))

    if is_personal_query and any(k in msg for k in ["skills", "skill", "tech stack", "languages", "language"]):
        return (
            True,
            "Boss, aapka core stack React.js, Next.js, Node.js, Express, MongoDB, Python, FastAPI, Docker, aur Gemini AI hai."
        )

    if is_personal_query and any(k in msg for k in ["contact", "phone", "mobile", "number"]):
        return (True, "Boss, your registered contact number is 7869037289.")

    if is_personal_query and any(k in msg for k in ["email", "mail id"]):
        return (True, "Boss, your email address is shivamjais2106@gmail.com.")

    if any(k in msg for k in ["who am i", "my name", "mera naam", "about me", "who is shivam"]):
        return (
            True,
            "You are Shivam Jaiswal, Boss! Full-Stack MERN Developer and AI Engineer currently interning at Fakhri IT Services."
        )

    if is_personal_query and any(k in msg for k in ["college", "university", "education", "degree"]):
        return (
            True,
            "Boss, you are pursuing B.Tech in Computer Science & Information Technology at Sagar Institute of Research and Technology (SIRT), Bhopal (2023–2027)."
        )

    if is_personal_query and any(k in msg for k in ["company", "internship", "job", "fakhri", "current work"]):
        return (
            True,
            "Boss, you are working as a MERN Stack Developer Intern at Fakhri IT Services, handling JamaatCloud, Fakhri Workspace chat audit, and Amazon Shipping API v2."
        )

    if any(k in msg for k in ["where do i live", "mera address", "meri city", "meri location"]):
        return (True, "Boss, you are based in Bhopal, Madhya Pradesh.")

    return (False, None)
