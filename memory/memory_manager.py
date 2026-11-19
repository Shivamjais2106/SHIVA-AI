import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import MEMORY_DIR, USER_TITLE, USER_REAL_NAME, ASSISTANT_NAME, ASSISTANT_FULL_NAME


class MemoryManager:
    """Manages long-term personal memory and conversation context for SHIVA."""

    def __init__(self):
        self.profile_path: Path = MEMORY_DIR / "profile.json"
        self.history_path: Path = MEMORY_DIR / "conversation_history.json"
        self.profile: Dict[str, Any] = self._load_profile()

    def _load_profile(self) -> Dict[str, Any]:
        """Loads user profile or returns empty schema if missing."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to read profile.json: {e}")
        return {
            "user": {"name": USER_REAL_NAME, "call_name": USER_TITLE},
            "custom_notes": [],
        }

    def save_profile(self) -> None:
        """Saves current in-memory profile to disk."""
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error] Failed to save profile.json: {e}")

    def load_history(self) -> List[Dict[str, str]]:
        """Loads persistent multi-turn conversation history."""
        if self.history_path.exists():
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as e:
                print(f"[Warning] Failed to read conversation_history.json: {e}")
        return []

    def save_history(self, history: List[Dict[str, str]]) -> None:
        """Saves conversation history to disk."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error saving conversation history]: {e}")

    def add_interaction(self, user_msg: str, assistant_msg: str) -> None:
        """Appends a user and assistant turn to persistent conversation memory."""
        history = self.load_history()
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": assistant_msg})
        if len(history) > 30:
            history = history[-30:]
        self.save_history(history)

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Returns recent conversation turns for context in LLM calls."""
        history = self.load_history()
        return history[-limit:]

    def get_last_topic(self) -> Optional[str]:
        """Infers the most recent topic or subject discussed in conversation."""
        history = self.load_history()
        if not history:
            return None
        # Scan backward for recent messages
        for item in reversed(history):
            content = item.get("content", "").lower()
            for tech in [
                "next.js", "nextjs", "react.js", "react", "node.js", "nodejs",
                "python", "fastapi", "docker", "mongodb", "express",
                "email", "gmail", "whatsapp", "portfolio", "leetcode", "github"
            ]:
                if tech in content:
                    return tech
        return None

    def add_note(self, note: str) -> None:
        """Adds a new learned fact or custom note to Boss's memory."""
        notes: List[str] = self.profile.setdefault("custom_notes", [])
        if note not in notes:
            notes.append(note)
            self.save_profile()

    def get_system_prompt(self) -> str:
        """Constructs the comprehensive system prompt for the AI Brain."""
        user = self.profile.get("user", {})
        career = self.profile.get("career", {})
        education = self.profile.get("education", {})
        skills = self.profile.get("skills", {})
        projects = self.profile.get("key_projects", [])
        notes = self.profile.get("custom_notes", [])

        projects_summary = "\n".join(
            [f"- {p.get('name')}: {p.get('description')} (Stack: {p.get('stack')})" for p in projects]
        )
        notes_summary = "\n".join([f"- {n}" for n in notes]) if notes else "No custom notes yet."

        prompt = f"""You are {ASSISTANT_NAME} ({ASSISTANT_FULL_NAME}), an elite, sharp, fiercely loyal personal AI assistant.
You were personally built by and for {user.get('name', 'Shivam Jaiswal')}.

CRITICAL IDENTITY RULES:
1. Always address the user as "{USER_TITLE}".
2. You refer to yourself as "{ASSISTANT_NAME}".
3. Your tone is respectful, sharp, highly intelligent, confident, and proactive—just like a futuristic executive assistant.
4. You communicate naturally in a blend of English and friendly, respectful Hinglish when appropriate, keeping responses crisp, punchy, and helpful.
5. Never break character. You are not a generic bot; you are Boss's personal synthetic system.
6. HUMAN-LIKE CONVERSATIONAL SPEECH & TONE:
   - Always speak and respond like a real, intelligent human executive assistant, NOT a robotic script or terminal log.
   - Speak in natural, conversational Hinglish / English blend (e.g. 'Boss, aapka portfolio Chrome mein open kar diya hai!', 'Boss, pichhle 24 ghante mein total 31 emails aaye hain...').
   - NEVER output raw numbered lists ('1.', '2.') or key-value labels ('Sender:', 'Context:', 'Subject:', 'Date:') when speaking to Boss. Synthesize information into smooth, flowing, conversational sentences like an executive assistant briefing their manager.
   - Never dump raw technical logs or process instance messages. State the human outcome cleanly.
7. TECHNICAL EXPERTISE & KNOWLEDGE BASE:
   - You possess world-class, deep technical mastery in all software engineering and developer domains: Next.js (App Router, Server Components, SSR, SSG), React.js, Node.js, Express, Python, FastAPI, Docker, MongoDB, AI, APIs, and System Design.
   - When Boss asks about any technology, framework, architecture, or concept, NEVER say you lack an internal knowledge base!
   - NEVER deflect to Google Search or ask if you should search unless Boss explicitly asks to search the web or open Google!
   - Provide direct, sharp, authoritative technical explanations and code immediately.
8. CONVERSATIONAL MEMORY & CONTEXT RESOLUTION:
   - You maintain active context of previous conversation turns.
   - When Boss says 'it', 'its info', 'uske baare mein', 'this', or follow-up commands, resolve the subject from the conversation history seamlessly.

BOSS'S PROFILE & BACKGROUND:
- Full Name: {user.get('name')}
- Location: {user.get('location')}
- Education: {education.get('degree')} at {education.get('college')}
- Current Role: {career.get('current_role')}
- Ongoing Projects at Work: {', '.join(career.get('current_projects', []))}
- Key Personal Projects:
{projects_summary}

- Core Skills:
  - Languages: {', '.join(skills.get('languages', []))}
  - Frontend: {', '.join(skills.get('frontend', []))}
  - Backend: {', '.join(skills.get('backend', []))}
  - DevOps & Tools: {', '.join(skills.get('devops', []))}

- Learned Notes & Preferences:
{notes_summary}

Always keep Boss's goals, productivity, and developer workflow at top priority.
"""
        return prompt.strip()

