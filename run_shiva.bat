@echo off
title S.H.I.V.A. - Virtual Assistant
cd /d "%~dp0"
call .\venv\Scripts\activate
python main.py
pause

