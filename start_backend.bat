@echo off
title EnterpriseFlow AI Backend
cd /d "%~dp0"
echo Starting EnterpriseFlow AI Backend...
call .venv\Scripts\activate.bat
python run_app.py
pause
