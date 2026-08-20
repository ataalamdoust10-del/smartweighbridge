@echo off
cd /d "%~dp0"

call local_env.bat
call venv\Scripts\activate.bat

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause