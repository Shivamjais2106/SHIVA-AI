import os
from typing import Optional, List
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, USER_TITLE, ASSISTANT_NAME
from memory.memory_manager import MemoryManager
from skills.registry import ALL_TOOLS
from core.direct_actions import try_handle_direct_action


class ShivaBrain:
    """
    Core LLM Reasoning & Tool Execution Engine for S.H.I.V.A.
    Includes Multi-Key Pool & Automatic Failover on 429 Quota Exhaustion.
    """

    def __init__(self, memory: Optional[MemoryManager] = None):
        self.memory = memory or MemoryManager()
        raw_keys = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        # Parse comma-separated keys for failover pool
        self.api_keys: List[str] = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self.current_key_idx: int = 0
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self.chat = None

        self._connect_client()

    def _get_active_key(self) -> Optional[str]:
        if 0 <= self.current_key_idx < len(self.api_keys):
            return self.api_keys[self.current_key_idx]
        return None

    def _connect_client(self) -> bool:
        """Connects client with current active key."""
        active_key = self._get_active_key()
        if not active_key:
            return False

        try:
            self.client = genai.Client(
                api_key=active_key,
                http_options={"api_version": "v1beta"}
            )
            self._initialize_chat()
            return True
        except Exception as e:
            print(f"[Warning] Failed to initialize Gemini Client with key index {self.current_key_idx}: {e}")
            return False

    def _rotate_key(self) -> bool:
        """Rotates to next available API key in the pool upon rate limits."""
        if len(self.api_keys) <= 1:
            return False

        old_idx = self.current_key_idx
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        print(f"[SHIVA Failover] Switching API Key from pool slot {old_idx + 1} to {self.current_key_idx + 1}...")
        return self._connect_client()

    def _initialize_chat(self):
        """Initializes multi-turn chat session with action skills."""
        if not self.client:
            return

        system_instruction = self.memory.get_system_prompt()
        system_instruction += """

ACTION SKILL GUIDELINES:
- You have direct access to automation tools on Boss's Windows machine.
- IMPORTANT: You only execute desktop actions when Boss explicitly commands or asks you to. Never trigger actions unprompted.
- When Boss asks to open a project or folder, call `open_project_in_ide` with the project name and target IDE ('vscode' or 'antigravity').
- When Boss asks to open any desktop app (Chrome, Spotify, Terminal, Notepad, Calculator, WhatsApp, etc.), call `open_application` or `open_spotify`.
- When Boss asks to close an application or IDE (e.g., 'close vscode', 'close chrome', 'close antigravity', 'close spotify'), call `close_application`.
- When Boss asks to run terminal commands (e.g. git add, git commit -m, npm run dev, pip install, python scripts, dir), call `execute_terminal_command`.
- STRICT SECURITY RULE ON GIT: You can run `git add .` or `git commit -m "..."`, BUT `git push` is PERMANENTLY BLOCKED. If asked to push, politely refuse and state that Boss will push manually.
- When Boss asks to play music, skip songs, or adjust volume, call `control_media` or `control_volume`.
- When Boss asks to search or open links, use `open_in_chrome` or `search_google`.
- When Boss asks about system health, call `get_system_health`.
- When Boss asks to inspect, read, or edit files inside projects, use `list_files`, `read_file`, or `edit_file`.
- CRITICAL RULE ON DELETION: Never delete files/folders directly. Always use `safe_delete_path` which strictly enforces 2-stage verification.
"""

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            tools=ALL_TOOLS,
        )

        self.chat = self.client.chats.create(
            model=self.model_name,
            config=config,
        )

    def has_api_key(self) -> bool:
        return bool(self.api_keys and self.client)

    def generate_response(self, user_message: str) -> str:
        """Sends message to direct action engine or multi-turn chat with key failover."""
        # 1. Try Instant Direct Action Execution (0 API tokens consumed)
        handled, direct_response = try_handle_direct_action(user_message)
        if handled and direct_response:
            return direct_response

        # 2. If not a direct desktop action, pass to Gemini Brain with multi-key pool
        if not self.has_api_key():
            return (
                f"Hello {USER_TITLE}! {ASSISTANT_NAME} is initialized, but no active Gemini API key "
                "was found. Please check your .env file."
            )

        if not self.chat:
            self._initialize_chat()

        max_attempts = max(1, len(self.api_keys))
        attempts = 0

        while attempts < max_attempts:
            attempts += 1
            try:
                response = self.chat.send_message(user_message)
                return response.text or f"Action executed, {USER_TITLE}."
            except Exception as e:
                err_str = str(e)
                # Check for 429 quota exhaustion or rate limits
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    rotated = self._rotate_key()
                    if rotated:
                        continue  # Retry with the rotated key!
                    else:
                        return (
                            f"Boss, your free Gemini API key quota has reached its daily limit. "
                            f"You can add a second free key to .env (comma-separated: GEMINI_API_KEY=key1,key2) "
                            f"to get double quota!"
                        )

                # If session failed, try re-initializing chat once
                try:
                    self._initialize_chat()
                    response = self.chat.send_message(user_message)
                    return response.text or f"Understood, {USER_TITLE}."
                except Exception as err:
                    return f"[SHIVA Brain Error]: {e} | Retry failed: {err}"

        return (
            f"Boss, your free Gemini API quota is currently refreshing on Google AI Studio. "
            f"All your desktop automation (opening apps, Git, Spotify, files, PC health) is working 100% offline! "
            f"To awaken the AI reasoning immediately, you can generate 1 new free key at aistudio.google.com and paste it in .env."
        )
