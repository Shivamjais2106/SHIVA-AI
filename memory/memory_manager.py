import json
from pathlib import Path
from typing import Dict, Any, List
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

