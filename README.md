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
├── pyproject.toml        # Python 專案配置
└── requirements.txt      # Python 依賴
```

## 開發指南

### 環境設定

1. Python 3.9+
2. PostgreSQL 13+
3. Redis 6+

### 資料庫遷移

```bash
# 建立新的遷移檔案
alembic revision --autogenerate -m "描述"

# 執行遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1
```

### 程式碼品質

```bash
# 格式化程式碼
black app/
isort app/

# 型別檢查
mypy app/

# 執行測試
pytest
```

## API 文件

啟動應用程式後，可以在以下位置查看 API 文件：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 部署

### Google Cloud Platform

1. 建立 GCP 專案
2. 設定 Cloud SQL 和 Cloud Run
3. 配置環境變數
4. 部署應用程式

詳細部署指南請參考 `docs/deployment.md`

## 貢獻指南

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 聯絡資訊

- 專案維護者: 災害救援平台開發團隊
- 電子郵件: contact@disaster-relief.com
- 專案網址: https://github.com/disaster-relief-platform