@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title PHAN TICH DU LIEU KTXH 53 DTTS DAK LAK
cd /d "%~dp0"

echo ======================================================================
echo   UNG DUNG TRA CUU & PHAN TICH DU LIEU KTXH 53 DAN TOC THIEU SO
echo                       TINH DAK LAK
echo ======================================================================
echo.

set "PY_EXE="

if exist "C:\python\python.exe" (
    set "PY_EXE=C:\python\python.exe"
    goto FOUND_PYTHON
)

if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
    goto FOUND_PYTHON
)

if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
    goto FOUND_PYTHON
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_EXE=python"
    goto FOUND_PYTHON
)

echo [LOI] Khong tim thay Python tren may tinh!
echo Vui long kiem tra lai moi truong Python.
pause
exit /b 1

:FOUND_PYTHON
set PORT=443
echo [*] Trinh thuc thi Python: %PY_EXE%
echo [*] Dang khoi dong Web Server [HTTPS / Cong 443]...
echo [*] Dia chi truy cap: https://dtts-daklak.com
echo.
echo [Huong dan]
echo - Trinh duyet web se tu dong mo sau 3 giay.
echo - De DUNG may chu: Nhan to hop phim [Ctrl + C]
echo ======================================================================
echo.

start "" cmd /c "timeout /t 3 /nobreak >nul & start https://dtts-daklak.com"

"%PY_EXE%" policy_assistant/app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [CANH BAO] May chu da dung lai hoac gap su co.
    pause
)