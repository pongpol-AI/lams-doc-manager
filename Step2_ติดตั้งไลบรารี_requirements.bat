@echo off
chcp 874 >nul
title Step 2: Install Requirements
cls
echo ===================================================================
echo     Step 2: ติดตั้งแพ็กเกจไลบรารีลงเครื่อง (pip install)
echo ===================================================================
echo.

cd /d "%~dp0"

set "PY_EXEC="
where python >nul 2>&1 && set "PY_EXEC=python"
if not defined PY_EXEC where py >nul 2>&1 && set "PY_EXEC=py"
if not defined PY_EXEC if exist "C:\Program Files\Python312\python.exe" set "PY_EXEC=C:\Program Files\Python312\python.exe"
if not defined PY_EXEC if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_EXEC=%LocalAppData%\Programs\Python\Python312\python.exe"

if not defined PY_EXEC (
    echo [ERROR] ไม่พบ Python บนเครื่องนี้! กรุณาติดตั้ง Python 3.12 ก่อนครับ
    pause
    exit
)

echo กำลังเรียกใช้ Python จาก: %PY_EXEC%
echo.
"%PY_EXEC%" -m pip install --upgrade pip
echo.
"%PY_EXEC%" -m pip install -r requirements.txt

echo.
echo ===================================================================
echo     ติดตั้งแพ็กเกจเสร็จสิ้น! กดปุ่มใดก็ได้เพื่อปิด...
echo ===================================================================
pause
