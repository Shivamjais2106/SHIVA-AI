@echo off
title S.H.I.V.A. - Virtual Assistant
cd /d "%~dp0"

:: Clear Antigravity IDE IPC hooks so Microsoft VS Code can launch independently
set VSCODE_IPC_HOOK=
set VSCODE_PID=
set ELECTRON_RUN_AS_NODE=
set ANTIGRAVITY_VSCODE_HOST=

call .\venv\Scripts\activate
python main.py
pause
