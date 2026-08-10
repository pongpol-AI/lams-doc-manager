@echo off
chcp 874 >nul
title Launch LAMS (Developer Mode)
cls
echo ===================================================================
echo     Starting LAMS Server (Developer Console Mode)...
echo ===================================================================
echo.
cd /d "%~dp0"

set "PY_EXEC="
where python >nul 2>&1 && set "PY_EXEC=python"
if not defined PY_EXEC where py >nul 2>&1 && set "PY_EXEC=py"
if not defined PY_EXEC if exist "C:\Program Files\Python312\python.exe" set "PY_EXEC=C:\Program Files\Python312\python.exe"
if not defined PY_EXEC if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_EXEC=%LocalAppData%\Programs\Python\Python312\python.exe"

if defined PY_EXEC (
    "%PY_EXEC%" -m streamlit run app.py --server.headless=false
    goto END
)

echo.
echo [ERROR] ไม่พบ Python บนเครื่องนี้ หรือยังไม่ได้ติดตั้งระบบ!
echo กรุณารันไฟล์ "01. ติดตั้งระบบครั้งแรก (Initial Setup).bat" เพื่อติดตั้งระบบก่อนครับ
echo.

:END
echo.
echo กดปุ่มใดก็ได้เพื่อปิดหน้าต่างนี้...
pause
