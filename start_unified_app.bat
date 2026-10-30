@echo off
title EnterpriseFlow AI
cd /d "%~dp0"
echo ====================================================================
echo  Launching EnterpriseFlow AI Unified Multi-Agent Onboarding Platform
echo ====================================================================
call .venv\Scripts\activate.bat
python run_app.py
pause
