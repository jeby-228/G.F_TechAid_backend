@echo off
chcp 65001 >nul
cls
echo ======================================
echo   API 連接測試
echo ======================================
echo.

echo [1] 測試根路徑...
curl.exe -s http://localhost:8000/
echo.
echo.

echo [2] 測試健康檢查...
curl.exe -s http://localhost:8000/health
echo.
echo.

echo [3] 測試 API 版本...
curl.exe -s http://localhost:8000/api/v1/docs -I | findstr "HTTP"
echo.
echo.

echo ======================================
echo   測試完成
echo ======================================
echo.
echo 如果所有測試都顯示正常回應，表示 API 運行正常
echo 您可以訪問 http://localhost:8000/api/v1/docs 查看完整文件
echo.

pause
