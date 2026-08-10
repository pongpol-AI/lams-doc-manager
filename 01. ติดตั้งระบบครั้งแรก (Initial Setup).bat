@echo off
chcp 874 >nul
title LAMS Initial System Setup
cls
echo ===================================================================
echo     Laboratory Accreditation Management System (LAMS Setup)
echo ===================================================================
echo.

set "PY_CMD="

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    echo [1/2] พบ Python ในระบบเรียบร้อยแล้ว
    goto INSTALL_PIP
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    echo [1/2] พบ Python Launcher ในระบบเรียบร้อยแล้ว
    goto INSTALL_PIP
)

if exist "C:\Program Files\Python312\python.exe" (
    set "PY_CMD=C:\Program Files\Python312\python.exe"
    echo [1/2] พบ Python 3.12 ใน Program Files เรียบร้อยแล้ว
    goto INSTALL_PIP
)

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
    echo [1/2] พบ Python 3.12 ใน AppData เรียบร้อยแล้ว
    goto INSTALL_PIP
)

echo [1/2] ไม่พบ Python บนเครื่องนี้ ระบบกำลังดาวน์โหลดและติดตั้ง Python 3.12 ให้อัตโนมัติ...
echo (กรุณารอสักครู่ขณะดาวน์โหลด)...
echo.

powershell -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe' -OutFile '%temp%\python_installer.exe'"

if exist "%temp%\python_installer.exe" (
    echo กำลังติดตั้ง Python 3.12 ลงในระบบ...
    "%temp%\python_installer.exe" /passive InstallAllUsers=1 PrependPath=1 Include_pip=1
    del "%temp%\python_installer.exe"
    echo ติดตั้ง Python สำเร็จ!
    
    where python >nul 2>&1 && set "PY_CMD=python"
    if not defined PY_CMD if exist "C:\Program Files\Python312\python.exe" set "PY_CMD=C:\Program Files\Python312\python.exe"
    if not defined PY_CMD if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PY_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
) else (
    echo.
    echo [WARNING] ไม่สามารถดาวน์โหลดอัตโนมัติได้ กรุณาเชื่อมต่ออินเทอร์เน็ตแล้วลองใหม่อีกครั้ง
    echo.
    pause
    exit
)

:INSTALL_PIP
if not defined PY_CMD (
    echo.
    echo [ERROR] ไม่สามารถระบุตำแหน่ง Python ได้ กรุณาติดตั้ง Python 3.12 ด้วยตนเอง
    echo.
    pause
    exit
)

echo.
echo [2/2] กำลังติดตั้งไลบรารีที่จำเป็นสำหรับระบบ (Streamlit, OpenPyXL, Pandas, ฯลฯ)...
echo.

"%PY_CMD%" -m pip install --upgrade pip >nul 2>&1
"%PY_CMD%" -m pip install -r requirements.txt

echo.
echo ===================================================================
echo     ติดตั้งระบบเรียบร้อยแล้ว! สามารถเปิดใช้งานได้ที่ไฟล์:
echo    "02. เริ่มใช้งานระบบ LAMS (Launch Program).vbs"
echo ===================================================================
echo.
pause
