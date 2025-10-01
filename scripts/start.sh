#!/bin/bash

# 啟動腳本 - 用於開發環境

echo "正在啟動光復e互助平台..."

# 檢查是否存在虛擬環境
if [ ! -d "venv" ]; then
    echo "建立 Python 虛擬環境..."
    python -m venv venv
fi

# 啟動虛擬環境
echo "啟動虛擬環境..."
source venv/bin/activate

# 安裝依賴
echo "安裝依賴套件..."
pip install -r requirements-dev.txt

# 檢查環境變數檔案
if [ ! -f ".env" ]; then
    echo "複製環境變數範例檔案..."
    cp .env.example .env
    echo "請編輯 .env 檔案設定您的環境變數"
fi

# 啟動資料庫遷移
echo "執行資料庫遷移..."
alembic upgrade head

# 啟動應用程式
echo "啟動 FastAPI 應用程式..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload