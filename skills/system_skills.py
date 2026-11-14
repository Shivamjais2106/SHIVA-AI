import os
import subprocess
import webbrowser
import psutil
from typing import Dict, Any

CHROME_PATH = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def get_system_health() -> Dict[str, Any]:
    """Returns CPU, RAM, and Battery statistics of Boss's laptop."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    battery = psutil.sensors_battery()

    battery_info = "No battery detected (Desktop/AC)"
    if battery:
        plugged = "Plugged In ⚡" if battery.power_plugged else "On Battery 🔋"
        battery_info = f"{battery.percent}% ({plugged})"

    return {
        "status": "success",
        "cpu_usage": f"{cpu_percent}%",
        "ram_usage": f"{ram.percent}% ({round(ram.used / (1024**3), 2)} GB used of {round(ram.total / (1024**3), 2)} GB)",
        "battery": battery_info,
    }


def open_in_chrome(url: str = "https://www.google.com") -> str:
    """Opens a specific URL or webpage in Google Chrome."""
    try:
        if os.path.exists(CHROME_PATH):
            subprocess.Popen([CHROME_PATH, url])
            return f"Opened '{url}' in Google Chrome, Boss."
        else:
            webbrowser.open(url)
            return f"Opened '{url}' in default browser, Boss."
    except Exception as e:
        return f"Failed to open Chrome: {e}"


def search_google(query: str) -> str:
    """Searches Google in Chrome for Boss's query."""
    encoded_query = query.replace(" ", "+")
    url = f"https://www.google.com/search?q={encoded_query}"
    return open_in_chrome(url)


def open_social_profile(platform: str) -> str:
    """Opens Boss's GitHub, LeetCode, or LinkedIn profile in Chrome."""
    platform_lower = platform.lower()
    if "github" in platform_lower:
        return open_in_chrome("https://github.com/Shivamjais2106")
    elif "leetcode" in platform_lower:
        return open_in_chrome("https://leetcode.com/Shivamjais2303")
    elif "linkedin" in platform_lower:
        return open_in_chrome("https://linkedin.com/in/shivam-jaiswal-37a951369")
    else:
        return f"Boss, unknown profile platform '{platform}'. Options are GitHub, LeetCode, or LinkedIn."


def get_clean_env() -> dict:
    """Removes Antigravity IDE and VS Code IPC hooks so Microsoft VS Code can launch independently."""
    env = os.environ.copy()
    for k in list(env.keys()):
        if any(prefix in k for prefix in ["VSCODE", "ELECTRON", "ANTIGRAVITY"]):
            del env[k]
    return env


def open_application(app_name: str) -> str:
    """Launches any desktop application or system tool on Windows."""
    app = app_name.lower().strip()
    
    # Special handling for VS Code to clear Antigravity IDE hooks
    if app in ["vscode", "vs code", "code"]:
        vscode_cmd = r"C:\Users\HP\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd"
        executable = vscode_cmd if os.path.exists(vscode_cmd) else "code"
        try:
            subprocess.Popen([executable, "-n"], env=get_clean_env(), shell=True)
            return "Launched VS Code successfully, Boss! 🚀"
        except Exception as e:
            return f"Failed to launch VS Code: {e}"

    cmd_map = {
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "notepad": "notepad.exe",
        "terminal": "wt.exe",
        "powershell": "powershell.exe",
        "cmd": "cmd.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "chrome": CHROME_PATH,
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "settings": "start ms-settings:",
        "spotify": "cmd /c start spotify:",
        "antigravity": r'"C:\Users\HP\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe"',
        "antigravity ide": r'"C:\Users\HP\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe"',
    }

    executable = cmd_map.get(app, f"start {app}")
    try:
        subprocess.Popen(executable, shell=True)
        return f"Launched {app_name} successfully, Boss. 🚀"
    except Exception as e:
        return f"Failed to launch {app_name}: {e}"


def close_application(app_name: str) -> str:
    """Closes any running desktop application or process on Windows."""
    app = app_name.lower().strip()
    proc_map = {
        "vscode": ["Code.exe"],
        "vs code": ["Code.exe"],
        "code": ["Code.exe"],
        "chrome": ["chrome.exe"],
        "notepad": ["notepad.exe"],
        "antigravity": ["Antigravity IDE.exe"],
        "antigravity ide": ["Antigravity IDE.exe"],
        "calculator": ["CalculatorApp.exe", "calc.exe"],
        "calc": ["CalculatorApp.exe", "calc.exe"],
        "spotify": ["Spotify.exe"],
        "discord": ["Discord.exe"],
        "whatsapp": ["WhatsApp.exe"],
        "terminal": ["WindowsTerminal.exe", "wt.exe"],
    }

    target_procs = proc_map.get(app, [f"{app}.exe", app])
    closed = 0
    for p in psutil.process_iter(["name"]):
        try:
            p_name = p.info["name"] or ""
            if any(t.lower() in p_name.lower() for t in target_procs):
                p.terminate()
                closed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if closed > 0:
        return f"Closed {app_name} ({closed} process instance(s) terminated), Boss. ✅"
    else:
        return f"Boss, {app_name} doesn't appear to be running right now."



