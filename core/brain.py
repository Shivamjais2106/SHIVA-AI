import os
from typing import Optional
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, USER_TITLE, ASSISTANT_NAME
from memory.memory_manager import MemoryManager
from skills.registry import ALL_TOOLS


class ShivaBrain:
    """Core LLM Reasoning & Tool Execution Engine for S.H.I.V.A."""

    def __init__(self, memory: Optional[MemoryManager] = None):
        self.memory = memory or MemoryManager()
        self.api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self.chat = None

        if self.api_key:
            try:
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options={"api_version": "v1beta"}
                )
                self._initialize_chat()
            except Exception as e:
                print(f"[Warning] Failed to initialize Gemini Client: {e}")
                self.client = None

    def _initialize_chat(self):
        """Initializes a multi-turn chat session with tools enabled."""
        if not self.client:
            return

        system_instruction = self.memory.get_system_prompt()
        system_instruction += """

ACTION SKILL GUIDELINES:
- You have access to real automation tools on Boss's Windows machine.
- When Boss asks to open a project or folder, ask or check if they want VS Code or Antigravity IDE, then call `open_project_in_ide`.
- When Boss asks to open websites or search, use `open_in_chrome` or `search_google`.
- When Boss asks about system health, call `get_system_health`.
- When Boss asks to view, read, or edit files, use `list_files`, `read_file`, or `edit_file`.
- CRITICAL RULE ON DELETION: Never execute a deletion without warning Boss. If asked to delete, call `safe_delete_path` which enforces 2-stage verification.
- CRITICAL RULE ON GIT: Never run git commit or git push to remote. Boss will do that manually.
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
        return bool(self.api_key and self.client)

    def generate_response(self, user_message: str) -> str:
        """Sends message to the multi-turn chat with automatic tool calling."""
        if not self.has_api_key():
            return (
                f"Hello {USER_TITLE}! {ASSISTANT_NAME} is initialized, but your Gemini API key "
                "is not configured yet. Please check .env file."
            )

        if not self.chat:
            self._initialize_chat()

        try:
            response = self.chat.send_message(user_message)
            return response.text or f"Action executed, {USER_TITLE}."
        except Exception as e:
            # If session expired or failed, try re-initializing chat once
            try:
                self._initialize_chat()
                response = self.chat.send_message(user_message)
                return response.text or f"Understood, {USER_TITLE}."
            except Exception as err:
                return f"[SHIVA Brain Error]: {e} | Retry failed: {err}"
