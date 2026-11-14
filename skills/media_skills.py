"""
Media & Audio Control Skills for S.H.I.V.A.
Controls Spotify, media playback, and system volume using native Windows APIs.
"""

import os
import subprocess
import ctypes
from typing import Dict, Any

# Windows Virtual Key codes
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_KEYUP = 0x0002


def _send_key(vk_code: int):
    """Sends a hardware media key press and release event."""
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def control_media(action: str) -> str:
    """
    Controls media playback (Spotify, YouTube, VLC, etc.).
    Actions: 'play', 'pause', 'play_pause', 'next', 'previous'
    """
    act = action.lower().strip()
    if act in ["play", "pause", "play_pause", "toggle"]:
        _send_key(VK_MEDIA_PLAY_PAUSE)
        return "Toggled media Play/Pause, Boss. 🎵"
    elif act in ["next", "next_track", "skip"]:
        _send_key(VK_MEDIA_NEXT_TRACK)
        return "Skipped to next track, Boss. ⏭️"
    elif act in ["previous", "prev", "prev_track"]:
        _send_key(VK_MEDIA_PREV_TRACK)
        return "Rewound to previous track, Boss. ⏮️"
    else:
        return f"Unknown media action '{action}'. Options: play, pause, next, previous."


def control_volume(action: str, steps: int = 5) -> str:
    """
    Controls system volume.
    Actions: 'up', 'down', 'mute', 'unmute'
    """
    act = action.lower().strip()
    if act in ["mute", "unmute", "toggle_mute"]:
        _send_key(VK_VOLUME_MUTE)
        return "Toggled system mute, Boss. 🔇"
    elif act in ["up", "increase", "louder"]:
        for _ in range(steps):
            _send_key(VK_VOLUME_UP)
        return f"Turned volume UP by {steps * 2}%, Boss. 🔊"
    elif act in ["down", "decrease", "softer", "lower"]:
        for _ in range(steps):
            _send_key(VK_VOLUME_DOWN)
        return f"Turned volume DOWN by {steps * 2}%, Boss. 🔉"
    else:
        return f"Unknown volume action '{action}'. Options: up, down, mute."


def open_spotify() -> str:
    """Launches Spotify desktop app or web player."""
    try:
        # Try URI protocol scheme
        subprocess.Popen(["cmd", "/c", "start", "spotify:"], shell=True)
        return "Launched Spotify for you, Boss! 🎧"
    except Exception:
        # Fallback to web player
        from skills.system_skills import open_in_chrome
        return open_in_chrome("https://open.spotify.com")

