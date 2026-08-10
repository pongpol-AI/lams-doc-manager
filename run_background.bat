@echo off
cd /d "%~dp0"

set "PY_EXEC="
where python >nul 2>&1 && set "PY_EXEC=python"
if not defined PY_EXEC where py >nul 2>&1 && set "PY_EXEC=py"
if not defined PY_EXEC if exist "C:\Program Files\Python312\python.exe" set "PY_EXEC=C:\Program Files\Python312\python.exe"
if not defined PY_EXEC if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_EXEC=%LocalAppData%\Programs\Python\Python312\python.exe"

if defined PY_EXEC (
    start "" "%PY_EXEC%" -m streamlit run app.py --server.headless=false
)
