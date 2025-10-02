@echo off
chcp 65001 >nul
cls
echo ======================================
echo   光復e互助平台 - 開發模式
echo ======================================
echo.
echo [啟動開發伺服器...]
echo 提示：修改程式碼後會自動重載
echo.

set PYTHONPATH=.
python -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True, reload_delay=2, log_level='info')"

pause

