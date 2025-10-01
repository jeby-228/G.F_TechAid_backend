# 地理位置服務文件

## 概述

地理位置服務提供了完整的地理位置處理功能，包括地址地理編碼、反向地理編碼、距離計算和附近站點查詢等功能。

## 核心功能

### 1. 地址地理編碼 (Geocoding)
將地址轉換為經緯度座標。

```python
from app.services.location_service import location_service

# 地理編碼
result = await location_service.geocode_address("花蓮縣光復鄉中正路一段1號")
print(f"座標: {result['latitude']}, {result['longitude']}")
```

### 2. 反向地理編碼 (Reverse Geocoding)
將經緯度座標轉換為地址。

```python
# 反向地理編碼
result = await location_service.reverse_geocode(23.6739, 121.4015)
print(f"地址: {result['formatted_address']}")
```

### 3. 距離計算
計算兩點間的直線距離（使用 Haversine 公式）。

```python
# 計算距離
distance = location_service.calculate_distance(
    23.6739, 121.4015,  # 光復鄉
    23.9739, 121.6015   # 花蓮市
)
print(f"距離: {distance:.2f} 公里")
```

### 4. 座標驗證
驗證座標是否有效且在台灣範圍內。

```python
# 座標驗證
is_valid = location_service.validate_coordinates(23.6739, 121.4015)
print(f"座標有效: {is_valid}")
```

### 5. 附近站點查詢
查找指定位置附近的物資站點或避難所。

```python
from app.database import SessionLocal

db = SessionLocal()

# 查找附近物資站點
nearby_stations = location_service.find_nearby_supply_stations(
    db, 23.6739, 121.4015, radius_km=10.0, limit=5
)

# 查找附近避難所
nearby_shelters = location_service.find_nearby_shelters(
    db, 23.6739, 121.4015, radius_km=15.0, limit=5
)
```

### 6. 路線查詢
獲取兩點間的路線距離和時間（需要 Google Maps API Key）。

```python
# 路線查詢
route_info = await location_service.get_route_distance_duration(
    23.6739, 121.4015,  # 起點
    23.9739, 121.6015   # 終點
)
print(f"路線距離: {route_info['distance']['text']}")
print(f"預估時間: {route_info['duration']['text']}")
```

## API 端點

### 地理編碼
```http
POST /api/v1/locations/geocode
Content-Type: application/json
Authorization: Bearer <token>

{
  "address": "花蓮縣光復鄉中正路一段1號"
}
```

### 反向地理編碼
```http
POST /api/v1/locations/reverse-geocode
Content-Type: application/json
Authorization: Bearer <token>

{
  "latitude": 23.6739,
  "longitude": 121.4015
}
```

### 距離計算
```http
POST /api/v1/locations/distance
Content-Type: application/json
Authorization: Bearer <token>

{
  "origin": {"lat": 23.6739, "lng": 121.4015},
  "destination": {"lat": 23.9739, "lng": 121.6015}
}
```

### 查找附近物資站點
```http
POST /api/v1/locations/nearby/supply-stations
Content-Type: application/json
Authorization: Bearer <token>

{
  "latitude": 23.6739,
  "longitude": 121.4015,
  "radius_km": 10.0,
  "limit": 10
}
```

### 查找附近避難所
```http
POST /api/v1/locations/nearby/shelters
Content-Type: application/json
Authorization: Bearer <token>

{
  "latitude": 23.6739,
  "longitude": 121.4015,
  "radius_km": 15.0,
  "limit": 10
}
```

### 路線查詢
```http
POST /api/v1/locations/route
Content-Type: application/json
Authorization: Bearer <token>

{
  "origin": {"lat": 23.6739, "lng": 121.4015},
  "destination": {"lat": 23.9739, "lng": 121.6015}
}
```

### 座標驗證
```http
POST /api/v1/locations/validate
Content-Type: application/json
Authorization: Bearer <token>

{
  "latitude": 23.6739,
  "longitude": 121.4015
}
```

## 輔助工具

### 位置資料處理
使用 `app.utils.location_helpers` 模組提供的輔助函數：

```python
from app.utils.location_helpers import (
    process_location_data,
    extract_coordinates_from_location_data,
    calculate_distance_between_locations,
    validate_location_data,
    format_location_for_display
)

# 處理位置資料
location_data = await process_location_data(
    "光復鄉公所", 
    {"lat": 23.6739, "lng": 121.4015}
)

# 提取座標
coords = extract_coordinates_from_location_data(location_data)

# 格式化顯示
display_text = format_location_for_display(location_data)
```

## 配置

### 環境變數
在 `.env` 檔案中設定以下變數：

```env
# Google Maps API Key（可選，沒有時使用預設座標）
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 預設行為
- 如果沒有設定 Google Maps API Key，系統會使用預設的光復鄉座標
- 座標驗證會檢查是否在台灣範圍內（緯度 21-26，經度 119-123）
- 距離計算使用 Haversine 公式，適用於短距離計算

## 錯誤處理

### 常見錯誤
1. **無效座標**: 座標超出有效範圍或不在台灣境內
2. **地理編碼失敗**: 地址無法找到對應座標
3. **API 限制**: Google Maps API 配額用盡或網路錯誤

### 錯誤回應格式
```json
{
  "detail": "錯誤訊息",
  "error_code": "VALIDATION_ERROR"
}
```

## 效能考量

### 快取策略
- 地理編碼結果可以快取以減少 API 調用
- 距離計算結果可以快取常用的路線

### 批次處理
對於大量位置資料處理，建議使用批次處理：

```python
# 批次處理多個地址
addresses = ["地址1", "地址2", "地址3"]
results = []

for address in addresses:
    result = await location_service.geocode_address(address)
    results.append(result)
    # 添加延遲避免 API 限制
    await asyncio.sleep(0.1)
```

## 測試

### 單元測試
```bash
python -m pytest tests/test_location_service.py -v
```

### 整合測試
```bash
python -m pytest tests/test_location_integration.py -v
```

### API 測試
```bash
python -m pytest tests/test_location_api.py -v
```

## 使用範例

### 在任務創建時處理位置
```python
from app.utils.location_helpers import process_location_data

async def create_task_with_location(task_data):
    # 處理位置資料
    location_data = await process_location_data(
        task_data["address"],
        task_data.get("coordinates")
    )
    
    # 創建任務
    task = Task(
        title=task_data["title"],
        description=task_data["description"],
        location_data=location_data,
        # ... 其他欄位
    )
    
    return task
```

### 查找最近的物資站點
```python
async def find_nearest_supply_station(user_location):
    coords = extract_coordinates_from_location_data(user_location)
    if not coords:
        return None
    
    nearby_stations = location_service.find_nearby_supply_stations(
        db, coords[0], coords[1], radius_km=20.0, limit=1
    )
    
    return nearby_stations[0] if nearby_stations else None
```

## 注意事項

1. **API 配額**: Google Maps API 有使用限制，請合理使用
2. **座標精度**: 使用適當的座標精度，避免過度精確
3. **錯誤處理**: 始終處理地理編碼可能失敗的情況
4. **快取**: 對於重複查詢，考慮使用快取機制
5. **隱私**: 處理位置資料時注意用戶隱私保護