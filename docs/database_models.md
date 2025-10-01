# 資料庫模型文件

## 概述

本文件描述了光復e互助平台的資料庫模型結構。系統使用 SQLAlchemy ORM 來管理資料庫操作，並使用 Alembic 進行資料庫遷移管理。

## 模型架構

### 基礎模型 (BaseModel)

所有模型都繼承自 `BaseModel`，包含以下共用欄位：
- `id`: UUID 主鍵
- `created_at`: 建立時間
- `updated_at`: 更新時間

## 用戶管理模組

### UserRole (用戶角色表)
- **表格名稱**: `user_roles`
- **主鍵**: `role` (String)
- **欄位**:
  - `role`: 角色代碼 (admin, victim, official_org, unofficial_org, supply_manager, volunteer)
  - `display_name`: 角色顯示名稱
  - `permissions`: 權限設定 (JSON)

### User (用戶表)
- **表格名稱**: `users`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `email`: 電子郵件 (唯一)
  - `phone`: 電話號碼
  - `name`: 姓名
  - `password_hash`: 密碼雜湊
  - `role`: 用戶角色 (外鍵到 user_roles)
  - `is_approved`: 是否已審核
  - `profile_data`: 個人資料 (JSON)

### Organization (組織資訊表)
- **表格名稱**: `organizations`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `user_id`: 關聯用戶 (外鍵到 users)
  - `organization_name`: 組織名稱
  - `organization_type`: 組織類型 (official/unofficial)
  - `contact_person`: 聯絡人
  - `contact_phone`: 聯絡電話
  - `address`: 地址
  - `description`: 組織描述
  - `approval_status`: 審核狀態
  - `approved_by`: 審核者 (外鍵到 users)
  - `approved_at`: 審核時間

## 任務管理模組

### TaskType (任務類型表)
- **表格名稱**: `task_types`
- **主鍵**: `type` (String)
- **欄位**:
  - `type`: 任務類型代碼
  - `display_name`: 顯示名稱
  - `description`: 描述
  - `icon`: 圖示

### TaskStatus (任務狀態表)
- **表格名稱**: `task_statuses`
- **主鍵**: `status` (String)
- **欄位**:
  - `status`: 狀態代碼
  - `display_name`: 顯示名稱
  - `description`: 描述

### Task (任務表)
- **表格名稱**: `tasks`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `creator_id`: 建立者 (外鍵到 users)
  - `title`: 任務標題
  - `description`: 任務描述
  - `task_type`: 任務類型 (外鍵到 task_types)
  - `status`: 任務狀態 (外鍵到 task_statuses)
  - `location_data`: 位置資料 (JSON)
  - `required_volunteers`: 所需志工人數
  - `required_skills`: 所需技能 (JSON)
  - `deadline`: 截止時間
  - `priority_level`: 優先級 (1-5)
  - `approval_status`: 審核狀態
  - `approved_by`: 審核者 (外鍵到 users)
  - `approved_at`: 審核時間

### TaskClaim (任務認領表)
- **表格名稱**: `task_claims`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `task_id`: 任務 (外鍵到 tasks)
  - `user_id`: 認領者 (外鍵到 users)
  - `claimed_at`: 認領時間
  - `started_at`: 開始時間
  - `completed_at`: 完成時間
  - `notes`: 備註
  - `status`: 認領狀態

## 需求管理模組

### NeedType (需求類型表)
- **表格名稱**: `need_types`
- **主鍵**: `type` (String)
- **欄位**:
  - `type`: 需求類型代碼
  - `display_name`: 顯示名稱
  - `description`: 描述
  - `icon`: 圖示

### NeedStatus (需求狀態表)
- **表格名稱**: `need_statuses`
- **主鍵**: `status` (String)
- **欄位**:
  - `status`: 狀態代碼
  - `display_name`: 顯示名稱
  - `description`: 描述

### Need (受災戶需求表)
- **表格名稱**: `needs`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `reporter_id`: 回報者 (外鍵到 users)
  - `title`: 需求標題
  - `description`: 需求描述
  - `need_type`: 需求類型 (外鍵到 need_types)
  - `status`: 需求狀態 (外鍵到 need_statuses)
  - `location_data`: 位置資料 (JSON)
  - `requirements`: 具體需求 (JSON)
  - `urgency_level`: 緊急程度 (1-5)
  - `contact_info`: 聯絡資訊 (JSON)
  - `assigned_to`: 分配給 (外鍵到 users)
  - `assigned_at`: 分配時間
  - `resolved_at`: 解決時間

### NeedAssignment (需求處理記錄表)
- **表格名稱**: `need_assignments`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `need_id`: 需求 (外鍵到 needs)
  - `task_id`: 關聯任務 (外鍵到 tasks)
  - `user_id`: 處理者 (外鍵到 users)
  - `assigned_at`: 分配時間
  - `completed_at`: 完成時間
  - `notes`: 備註
  - `status`: 處理狀態

## 物資管理模組

### SupplyType (物資類型表)
- **表格名稱**: `supply_types`
- **主鍵**: `type` (String)
- **欄位**:
  - `type`: 物資類型代碼
  - `display_name`: 顯示名稱
  - `category`: 物資分類
  - `unit`: 計量單位
  - `description`: 描述

### SupplyStation (物資站點表)
- **表格名稱**: `supply_stations`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `manager_id`: 管理者 (外鍵到 users)
  - `name`: 站點名稱
  - `address`: 地址
  - `location_data`: 位置資料 (JSON)
  - `contact_info`: 聯絡資訊 (JSON)
  - `capacity_info`: 容量資訊 (JSON)
  - `is_active`: 是否啟用

### InventoryItem (物資庫存表)
- **表格名稱**: `inventory_items`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `station_id`: 站點 (外鍵到 supply_stations)
  - `supply_type`: 物資類型 (外鍵到 supply_types)
  - `description`: 描述
  - `is_available`: 是否可用
  - `notes`: 備註

### ReservationStatus (物資預訂狀態表)
- **表格名稱**: `reservation_statuses`
- **主鍵**: `status` (String)
- **欄位**:
  - `status`: 狀態代碼
  - `display_name`: 顯示名稱
  - `description`: 描述

### SupplyReservation (物資預訂表)
- **表格名稱**: `supply_reservations`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `user_id`: 預訂者 (外鍵到 users)
  - `station_id`: 站點 (外鍵到 supply_stations)
  - `task_id`: 關聯任務 (外鍵到 tasks)
  - `need_id`: 關聯需求 (外鍵到 needs)
  - `status`: 預訂狀態 (外鍵到 reservation_statuses)
  - `reserved_at`: 預訂時間
  - `confirmed_at`: 確認時間
  - `picked_up_at`: 領取時間
  - `delivered_at`: 配送時間
  - `notes`: 備註

### ReservationItem (預訂物資明細表)
- **表格名稱**: `reservation_items`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `reservation_id`: 預訂 (外鍵到 supply_reservations)
  - `supply_type`: 物資類型 (外鍵到 supply_types)
  - `requested_quantity`: 請求數量
  - `confirmed_quantity`: 確認數量
  - `notes`: 備註

## 系統管理模組

### Announcement (系統公告表)
- **表格名稱**: `announcements`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `title`: 公告標題
  - `content`: 公告內容
  - `announcement_type`: 公告類型
  - `priority_level`: 優先級
  - `is_active`: 是否啟用
  - `target_roles`: 目標角色 (JSON)
  - `created_by`: 建立者 (外鍵到 users)
  - `expires_at`: 過期時間

### Notification (通知記錄表)
- **表格名稱**: `notifications`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `user_id`: 用戶 (外鍵到 users)
  - `title`: 通知標題
  - `message`: 通知內容
  - `notification_type`: 通知類型
  - `related_id`: 關聯ID
  - `is_read`: 是否已讀
  - `sent_at`: 發送時間
  - `read_at`: 閱讀時間

### SystemLog (系統日誌表)
- **表格名稱**: `system_logs`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `user_id`: 用戶 (外鍵到 users)
  - `action`: 操作
  - `resource_type`: 資源類型
  - `resource_id`: 資源ID
  - `details`: 詳細資訊 (JSON)
  - `ip_address`: IP地址
  - `user_agent`: 用戶代理

### Shelter (避難所資訊表)
- **表格名稱**: `shelters`
- **主鍵**: `id` (UUID)
- **欄位**:
  - `name`: 避難所名稱
  - `address`: 地址
  - `location_data`: 位置資料 (JSON)
  - `capacity`: 容量
  - `current_occupancy`: 目前入住人數
  - `contact_info`: 聯絡資訊 (JSON)
  - `facilities`: 設施資訊 (JSON)
  - `status`: 狀態
  - `managed_by`: 管理者 (外鍵到 users)

## 資料庫遷移

### 初始遷移檔案
- `001_initial_database_schema.py`: 建立所有資料表結構
- `002_insert_initial_data.py`: 插入初始資料 (角色、類型、狀態等)

### 使用 Alembic 管理遷移

```bash
# 生成新的遷移檔案
alembic revision --autogenerate -m "描述變更"

# 執行遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1
```

## 索引設計

為了提升查詢效能，系統在以下欄位建立了索引：
- `users.email` (唯一索引)
- `users.role`
- `tasks.creator_id`
- `tasks.status`
- `needs.reporter_id`
- `needs.status`
- `supply_stations.is_active`
- `inventory_items.is_available`
- `supply_reservations.status`
- `notifications.user_id`
- `notifications.is_read`
- `system_logs.created_at`

## 關聯關係

系統中的主要關聯關係：
1. **用戶與角色**: 一對多關係
2. **用戶與組織**: 一對多關係
3. **任務與用戶**: 多對一關係 (建立者)
4. **任務與認領**: 一對多關係
5. **需求與用戶**: 多對一關係 (回報者)
6. **物資站點與用戶**: 多對一關係 (管理者)
7. **預訂與用戶/站點**: 多對一關係
8. **通知與用戶**: 多對一關係

## 資料完整性

系統使用以下機制確保資料完整性：
1. **外鍵約束**: 確保關聯資料的一致性
2. **唯一約束**: 防止重複資料
3. **非空約束**: 確保必要欄位有值
4. **級聯刪除**: 適當的級聯刪除設定
5. **檢查約束**: 在應用層實作資料驗證