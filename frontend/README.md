# 光復e互助平台 - 前端應用程式

這是光復e互助平台的前端應用程式，使用 React + TypeScript 開發。

## 技術堆疊

- **框架**: React 18 + TypeScript
- **狀態管理**: Redux Toolkit
- **UI 庫**: Ant Design
- **路由**: React Router v6
- **地圖**: Leaflet + React Leaflet
- **HTTP 客戶端**: Axios
- **PWA**: Service Worker + Workbox

## 功能特色

- 📱 響應式設計，支援行動裝置
- 🔄 PWA 支援，可離線使用
- 🗺️ 整合地圖功能
- 🔐 完整的身分驗證系統
- 📊 即時數據更新
- 🌐 多語言支援（中文）

## 開始使用

### 環境需求

- Node.js 16.0 或更高版本
- npm 或 yarn

### 安裝依賴

```bash
npm install
# 或
yarn install
```

### 環境設定

1. 複製環境變數範例檔案：
```bash
cp .env.example .env
```

2. 編輯 `.env` 檔案，設定必要的環境變數：
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_GOOGLE_MAPS_API_KEY=your_api_key_here
```

### 開發模式

```bash
npm start
# 或
yarn start
```

應用程式將在 http://localhost:3000 啟動。

### 建置生產版本

```bash
npm run build
# 或
yarn build
```

### 執行測試

```bash
npm test
# 或
yarn test
```

## 專案結構

```
src/
├── components/          # 可重用元件
│   ├── Layout/         # 佈局元件
│   └── ProtectedRoute/ # 路由保護元件
├── pages/              # 頁面元件
├── services/           # API 服務
├── store/              # Redux 狀態管理
│   └── slices/        # Redux slices
├── types/              # TypeScript 類型定義
├── utils/              # 工具函數
├── router/             # 路由配置
├── App.tsx            # 主應用程式元件
└── index.tsx          # 應用程式入口點
```

## 用戶角色與權限

系統支援以下用戶角色：

- **受災戶**: 可發布需求、查看任務
- **一般志工**: 可認領任務、查看需求
- **正式志工組織**: 可發布任務、管理組織
- **非正式志工組織**: 需審核後可發布任務
- **物資站點管理者**: 可管理物資庫存
- **系統管理員**: 完整系統管理權限

## PWA 功能

應用程式支援 Progressive Web App 功能：

- 可安裝到主畫面
- 離線瀏覽支援
- 背景同步
- 推播通知

## 開發指南

### 新增頁面

1. 在 `src/pages/` 建立新的頁面元件
2. 在 `src/router/index.tsx` 新增路由配置
3. 如需權限控制，使用 `ProtectedRoute` 包裝

### 新增 API 服務

1. 在 `src/services/` 建立服務檔案
2. 使用 `apiClient` 進行 HTTP 請求
3. 在對應的 Redux slice 中新增異步 actions

### 狀態管理

使用 Redux Toolkit 進行狀態管理：

```typescript
// 在元件中使用
const dispatch = useDispatch();
const { data, isLoading } = useSelector((state: RootState) => state.example);

// 派發 action
dispatch(fetchData());
```

## 部署

### 使用 Docker

```bash
# 建置 Docker 映像
docker build -t disaster-relief-frontend .

# 執行容器
docker run -p 3000:80 disaster-relief-frontend
```

### 部署到 GCP

應用程式可部署到 Google Cloud Platform：

1. 建置生產版本
2. 上傳到 Cloud Storage
3. 配置 Cloud CDN
4. 設定 Cloud Load Balancer

## 貢獻指南

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 授權

本專案採用 MIT 授權條款。詳見 [LICENSE](../LICENSE) 檔案。