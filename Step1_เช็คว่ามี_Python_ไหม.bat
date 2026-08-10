@echo off
chcp 874 >nul
title Step 1: Check Python Environment
cls
echo ===================================================================
echo     Step 1: ตรวจสอบการติดตั้ง Python บนเครื่องนี้
echo ===================================================================
echo.

echo [1] ทดสอบคำสั่ง 'python':
python --version
if %errorlevel% equ 0 (
    echo --> ผลลัพธ์: พบ python ใน PATH เรียบร้อยแล้ว!
) else (
    echo --> ผลลัพธ์: ไม่พบคำสั่ง python ใน PATH
)
echo.

echo [2] ทดสอบคำสั่ง 'py' (Python Launcher):
py --version
if %errorlevel% equ 0 (
    echo --> ผลลัพธ์: พบ py ใน PATH เรียบร้อยแล้ว!
) else (
    echo --> ผลลัพธ์: ไม่พบคำสั่ง py ใน PATH
)
echo.

echo [3] ตรวจสอบไฟล์ใน Program Files:
if exist "C:\Program Files\Python312\python.exe" (
    echo --> พบ C:\Program Files\Python312\python.exe
) else (
    echo --> ไม่พบใน C:\Program Files\Python312\python.exe
)
echo.

echo [4] ตรวจสอบไฟล์ใน AppData:
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    echo --> พบ %LocalAppData%\Programs\Python\Python312\python.exe
) else (
    echo --> ไม่พบใน AppData
)

echo.
echo ===================================================================
echo     กดปุ่มใดก็ได้เพื่อปิดหน้าต่างนี้...
echo ===================================================================
pause
