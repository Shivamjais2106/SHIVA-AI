import os
import requests
from typing import Optional, List
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GROQ_API_KEY, USER_TITLE, ASSISTANT_NAME
from memory.memory_manager import MemoryManager
from skills.registry import ALL_TOOLS
from core.direct_actions import try_handle_direct_action


class ShivaBrain:
    """
    Core LLM Reasoning & Tool Execution Engine for S.H.I.V.A.
    Features:
    1. Direct Instant Desktop Actions (100% offline, 0 API tokens)
    2. Primary Brain: Gemini 2.5 Flash with Multi-Key Auto-Rotation
    3. Ultra-Fast Secondary Brain: Groq AI Fallback (14,400 free requests/day)
    """

    def __init__(self, memory: Optional[MemoryManager] = None):
        self.memory = memory or MemoryManager()
        
        # Gemini API Key pool
        raw_gemini_keys = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.api_keys: List[str] = [k.strip() for k in raw_gemini_keys.split(",") if k.strip()]
        self.current_key_idx: int = 0
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self.chat = None

        # Groq API Key pool for instant failover
        raw_groq_keys = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.groq_keys: List[str] = [k.strip() for k in raw_groq_keys.split(",") if k.strip()]

        self._connect_client()

    def _get_active_key(self) -> Optional[str]:
        if 0 <= self.current_key_idx < len(self.api_keys):
            return self.api_keys[self.current_key_idx]
        return None

    def _connect_client(self) -> bool:
        """Connects client with current active Gemini key."""
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
            print(f"[Warning] Failed to initialize Gemini Client with key slot {self.current_key_idx + 1}: {e}")
            return False

    def _rotate_key(self) -> bool:
        """Rotates to next available Gemini API key in the pool upon rate limits."""
        if len(self.api_keys) <= 1:
            return False

        old_idx = self.current_key_idx
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        # Avoid infinite looping if wrapped around
        if self.current_key_idx == 0:
            return False

        print(f"[SHIVA Failover] Switching Gemini API Key from slot {old_idx + 1} to {self.current_key_idx + 1}...")
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
- PORTFOLIO & PROFILES:
  - When Boss asks to open or view their personal portfolio ('my portfolio', 'open my portfolio', 'portfolio in chrome'), call `open_portfolio`. NEVER search Google for Boss's personal portfolio!
  - When Boss asks to open GitHub, LeetCode, or LinkedIn, call `open_social_profile`. Note: LeetCode is Boss's competitive programming profile, NOT VS Code!
- TAB VS APPLICATION CLOSING:
  - When Boss asks to close a specific website or tab (e.g. 'close github on chrome', 'close leetcode tab', 'close active tab', 'close tab'), call `close_browser_tab`.
  - NEVER call `close_application` on Chrome when Boss only wanted to close a tab or website! Only call `close_application('chrome')` if Boss explicitly commands closing the whole Chrome browser app.
- When Boss asks to open a project or folder, call `open_project_in_ide` with the project name and target IDE ('vscode' or 'antigravity').
- When Boss asks to open any desktop app (Chrome, Spotify, Terminal, Notepad, Calculator, WhatsApp, etc.), call `open_application` or `open_spotify`.
- When Boss asks to close an application or IDE (e.g., 'close vscode', 'close chrome', 'close antigravity', 'close spotify'), call `close_application`.
- GMAIL & EMAIL SKILLS:
  - When Boss asks to check, read, or list emails, call `read_emails` or `open_gmail`.
  - When Boss asks to write, send, or compose an email, call `send_email` or `compose_email_in_browser`.
- WHATSAPP & CALL SKILLS:
  - When Boss asks to send a WhatsApp message, call `send_whatsapp_message`.
  - When Boss asks to make a call or WhatsApp call, call `initiate_whatsapp_call`.
  - When Boss asks to check incoming messages or test the unknown number auto-greeting, call `get_whatsapp_inbox` or `simulate_incoming_whatsapp`.
- When Boss asks to check git status of any project, call `get_git_status`.
- When Boss asks to run terminal commands (e.g. git add, git commit -m, npm run dev, pip install, python scripts, dir), call `execute_terminal_command` or `git_add_and_commit`.
- STRICT SECURITY RULE ON GIT: You can run `git add .` or `git commit -m "..."`, BUT `git push` is PERMANENTLY BLOCKED. If asked to push, politely refuse and state that Boss will push manually.
- When Boss asks to play music, skip songs, or adjust volume, call `control_media` or `control_volume`.
- When Boss asks to search or open links, use `open_in_chrome` or `search_google`.
- REAL-TIME NEWS, WEATHER & LIVE WEB RETRIEVAL:
  - When Boss asks about the latest news, today's news, current events, or headlines, call `get_latest_news`. NEVER ask 'Shall I search Google?'—fetch the news and present the live briefing directly!
  - When Boss asks about the weather, temperature, or rain, call `get_weather`.
  - When Boss asks for real-time web information, live facts, or web search, call `search_web_realtime` to retrieve the facts and answer directly.
  - Only call `search_google` or `open_in_chrome` if Boss explicitly commands opening a browser window or website (e.g. 'open google in chrome', 'open link in browser').
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
        return bool(self.api_keys and self.client) or bool(self.groq_keys)

    def call_groq_fallback(self, user_message: str) -> Optional[str]:
        """High-speed failover fallback using Groq free tier API with persistent conversation memory."""
        if not self.groq_keys:
            return None

        system_prompt = self.memory.get_system_prompt()
        history = self.memory.get_recent_history(limit=8)
        
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-120b"
        ]

        for key in self.groq_keys:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            for model in models:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                }
                try:
                    res = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=10,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                except Exception:
                    continue
        return None

    def generate_response(self, user_message: str) -> str:
        """Sends message to direct action engine or multi-turn chat with key failover and persistent memory."""
        # 1. Try Instant Direct Action Execution (0 API tokens consumed, 100% offline)
        handled, direct_response = try_handle_direct_action(user_message)
        if handled and direct_response:
            self.memory.add_interaction(user_message, direct_response)
            return direct_response

        # 2. Try Gemini Brain with auto-failover pool
        if self.client:
            if not self.chat:
                self._initialize_chat()

            max_attempts = max(1, len(self.api_keys))
            attempts = 0

            while attempts < max_attempts:
                attempts += 1
                try:
                    response = self.chat.send_message(user_message)
                    resp_text = response.text or f"Action executed, {USER_TITLE}."
                    self.memory.add_interaction(user_message, resp_text)
                    return resp_text
                except Exception as e:
                    err_str = str(e)
                    # Check for 429 quota exhaustion or rate limits
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        rotated = self._rotate_key()
                        if rotated:
                            continue
                        else:
                            break  # Drop through to Groq fallback!

                    # Session error fallback
                    try:
                        self._initialize_chat()
                        response = self.chat.send_message(user_message)
                        resp_text = response.text or f"Understood, {USER_TITLE}."
                        self.memory.add_interaction(user_message, resp_text)
                        return resp_text
                    except Exception:
                        break

        # 3. Automatic Groq Fallback when Gemini is on rate limit
        print("[SHIVA Failover] Gemini quota reached. Auto-switching to high-speed Groq Brain with conversation memory...")
        groq_resp = self.call_groq_fallback(user_message)
        if groq_resp:
            self.memory.add_interaction(user_message, groq_resp)
            return groq_resp

        fallback_msg = (
            f"Boss, your free Gemini API quota is currently refreshing on Google AI Studio. "
            f"All your desktop automation (opening apps, Git, Spotify, files, PC health) is working 100% offline! "
            f"Please check your API keys in .env."
        )
        self.memory.add_interaction(user_message, fallback_msg)
        return fallback_msg
