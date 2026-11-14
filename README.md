# S.H.I.V.A. (Synthetic High-Intelligence Virtual Assistant) ⚡

Personal AI Assistant built specifically for **Shivam Jaiswal** (Boss).

## 🚀 Phase 1: Core Engine & Personal Memory (COMPLETED)
- **AI Brain**: Google Gemini 2.5 Flash via `google-genai` SDK (Free Tier).
- **Personal Memory**: Persistent knowledge base in `memory/profile.json` (extracted from resume).
- **Executive Identity**: Addresses user as **"Boss"**, identifies itself as **"SHIVA"**, sharp, loyal, and tech-savvy.
- **Terminal UI**: Futuristic banner and interactive loop built with `rich`.

## 🛠️ Phase 2: Action Skills & Automation (COMPLETED)
- **IDE Project Launcher**:
  - `open_project_in_ide`: Opens any project from `D:/Projects` directly in **VS Code** or **Antigravity IDE**.
- **Chrome & Web Control**:
  - `open_in_chrome`: Opens any webpage in Google Chrome.
  - `search_google`: Searches topics and queries in Google Chrome.
  - `open_social_profile`: Instantly launches Boss's GitHub, LeetCode, or LinkedIn profiles.
- **File System Inspection & Editing**:
  - `list_files`: View contents and sizes inside any folder.
  - `read_file`: Reads source code and text files.
  - `edit_file`: Finds and replaces specific code/text inside target files.
  - `create_or_write_file`: Safely creates or writes code to files.
- **Strict 2-Step Deletion Guard**:
  - `safe_delete_path`: **MANDATORY 2x Confirmation** required before any file or directory can be deleted.
- **System Health & Diagnostic**:
  - `get_system_health`: Real-time Battery (%), CPU (%), and RAM metrics.

## 🔒 Security & Git Policies
- **ZERO Auto-Commits**: SHIVA will NEVER commit or push to Git/GitHub automatically. Boss retains 100% manual Git control.
- **ZERO Accidental Deletions**: Enforces two-tier confirmation gates.

## 💻 How to Run
Double-click `run_shiva.bat` or run:
```powershell
.\run_shiva.bat
```
