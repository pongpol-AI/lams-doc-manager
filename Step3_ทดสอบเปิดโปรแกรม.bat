@echo off
chcp 874 >nul
title Step 3: Run Streamlit Program
cls
echo ===================================================================
echo     Step 3: ทดสอบเปิดรันโปรแกรม Streamlit (LAMS)
echo ===================================================================
echo.

cd /d "%~dp0"

set "PY_EXEC="
where python >nul 2>&1 && set "PY_EXEC=python"
if not defined PY_EXEC where py >nul 2>&1 && set "PY_EXEC=py"
if not defined PY_EXEC if exist "C:\Program Files\Python312\python.exe" set "PY_EXEC=C:\Program Files\Python312\python.exe"
if not defined PY_EXEC if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_EXEC=%LocalAppData%\Programs\Python\Python312\python.exe"

if not defined PY_EXEC (
    echo [ERROR] ไม่พบ Python บนเครื่องนี้!
    pause
    exit
)

echo กำลังเรียกใช้ Python จาก: %PY_EXEC%
echo กำลังเปิดโปรแกรม...
echo.

"%PY_EXEC%" -m streamlit run app.py --server.headless=false --server.port=8501

echo.
echo ===================================================================
echo     โปรแกรมจบการทำงานแล้ว กดปุ่มใดก็ได้เพื่อปิด...
echo ===================================================================
pause
