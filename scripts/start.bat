@echo off
REM 啟動腳本 - 用於 Windows 開發環境

echo 正在啟動光復e互助平台...

REM 檢查是否存在虛擬環境
if not exist "venv" (
    echo 建立 Python 虛擬環境...
    python -m venv venv
)

REM 啟動虛擬環境
echo 啟動虛擬環境...
call venv\Scripts\activate.bat

REM 安裝依賴
echo 安裝依賴套件...
pip install -r requirements-dev.txt

REM 檢查環境變數檔案
if not exist ".env" (
    echo 複製環境變數範例檔案...
    copy .env.example .env
    echo 請編輯 .env 檔案設定您的環境變數
)

REM 啟動資料庫遷移
echo 執行資料庫遷移...
alembic upgrade head

REM 啟動應用程式
echo 啟動 FastAPI 應用程式...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause