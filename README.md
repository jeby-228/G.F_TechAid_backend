README.md
@@ -0,0 +1,148 @@
# 光復e互助平台

花蓮光復鄉災害應變數位平台，旨在透過高效、可靠的系統優化災害應變流程。

## 功能特色

- 🚨 **災害應變管理** - 受災戶需求發布與志工任務協調
- 📦 **物資管理系統** - 物資站點管理與配送追蹤
- 🏠 **避難所資訊** - 即時避難所狀態與容量資訊
- 📱 **行動裝置支援** - 響應式設計，支援離線操作
- 🔐 **權限控制** - 基於角色的權限管理系統
- 📊 **資料監控** - 即時統計與救災進度追蹤

## 技術架構

- **後端**: FastAPI + Python 3.11
- **資料庫**: PostgreSQL + Redis
- **部署**: Docker + Google Cloud Platform
- **前端**: React.js (計劃中)

## 快速開始

### 使用 Docker (推薦)

1. 複製專案
```bash
git clone <repository-url>
cd disaster-relief-platform
```

2. 複製環境變數檔案
```bash
cp .env.example .env
```

3. 啟動服務
```bash
docker-compose up -d
```

4. 訪問應用程式
- API 文件: http://localhost:8000/docs
- 應用程式: http://localhost:8000
- pgAdmin: http://localhost:5050

### 本地開發

#### Windows
```bash
scripts\start.bat
```

#### Linux/macOS
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

## 專案結構

```
disaster-relief-platform/
├── app/                    # 應用程式主目錄
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── models/            # 資料庫模型
│   ├── schemas/           # Pydantic 模型
│   ├── services/          # 業務邏輯
│   └── utils/             # 工具函數
├── alembic/               # 資料庫遷移
├── scripts/               # 部署腳本
├── tests/                 # 測試檔案
├── docker-compose.yml     # Docker 開發環境
├── Dockerfile            # Docker 映像檔
