import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "memory"
CACHE_DIR = BASE_DIR / "cache"

# Ensure essential directories exist
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Core Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "SHIVA")
ASSISTANT_FULL_NAME = os.getenv(
    "ASSISTANT_FULL_NAME", "Synthetic High-Intelligence Virtual Assistant"
)
USER_TITLE = os.getenv("USER_TITLE", "Boss")
USER_REAL_NAME = os.getenv("USER_REAL_NAME", "Shivam Jaiswal")

# Voice
VOICE_NAME = os.getenv("VOICE_NAME", "en-GB-RyanNeural")
SPEECH_ENABLED = os.getenv("SPEECH_ENABLED", "false").lower() == "true"

# Workspaces
PROJECTS_ROOT = Path("D:/Projects")

