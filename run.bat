@echo off
chcp 65001 >nul
cls
echo ======================================
echo   光復e互助平台 API 伺服器
echo ======================================
echo.
echo [啟動中...]
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause

