@echo off
chcp 65001 >nul
title Stop LAMS Program
cls
echo ==========================================================
echo    Shutting down LAMS System Server...
echo ==========================================================
echo.
powershell -Command "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe' and CommandLine like '%%streamlit%%'\" | Foreach-Object { Stop-Process $_.ProcessId -Force }"
echo.
echo LAMS System Server stopped successfully!
timeout /t 2 >nul
