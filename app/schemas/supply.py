"""
物資管理相關的 Pydantic 模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.utils.constants import UserRole, ReservationStatus


class LocationData(BaseModel):
    """地理位置資料模型"""
    address: str = Field(..., description="地址")
    coordinates: Dict[str, float] = Field(..., description="座標 {lat, lng}")
    details: Optional[str] = Field(None, description="位置詳細說明")
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if not isinstance(v, dict) or 'lat' not in v or 'lng' not in v:
            raise ValueError('座標必須包含 lat 和 lng')
        if not (-90 <= v['lat'] <= 90):
            raise ValueError('緯度必須在 -90 到 90 之間')
        if not (-180 <= v['lng'] <= 180):
            raise ValueError('經度必須在 -180 到 180 之間')
        return v


class ContactInfo(BaseModel):
    """聯絡資訊模型"""
    phone: Optional[str] = Field(None, description="聯絡電話")
    email: Optional[str] = Field(None, description="電子郵件")
    hours: Optional[str] = Field(None, description="開放時間")
    contact_person: Optional[str] = Field(None, description="聯絡人")


# 物資站點相關模型
class SupplyStationBase(BaseModel):
    """物資站點基礎模型"""
    name: str = Field(..., min_length=1, max_length=200, description="站點名稱")
    address: str = Field(..., min_length=1, description="站點地址")
    location_data: LocationData = Field(..., description="地理位置資訊")
    contact_info: ContactInfo = Field(..., description="聯絡資訊")
    capacity_info: Optional[Dict[str, Any]] = Field(None, description="容量資訊")


class SupplyStationCreate(SupplyStationBase):
    """物資站點建立模型"""
    pass


class SupplyStationUpdate(BaseModel):
    """物資站點更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="站點名稱")
    address: Optional[str] = Field(None, min_length=1, description="站點地址")
    location_data: Optional[LocationData] = Field(None, description="地理位置資訊")
    contact_info: Optional[ContactInfo] = Field(None, description="聯絡資訊")
    capacity_info: Optional[Dict[str, Any]] = Field(None, description="容量資訊")
    is_active: Optional[bool] = Field(None, description="是否啟用")


class SupplyStationInDB(SupplyStationBase):
    """資料庫中的物資站點模型"""
    id: str = Field(..., description="站點 ID")
    manager_id: str = Field(..., description="管理者 ID")
    is_active: bool = Field(..., description="是否啟用")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class SupplyStationResponse(SupplyStationInDB):
    """物資站點回應模型"""
    manager_name: Optional[str] = Field(None, description="管理者姓名")
    manager_role: Optional[UserRole] = Field(None, description="管理者角色")
    inventory_count: int = Field(0, description="庫存品項數量")
    available_supplies: List[str] = Field([], description="可用物資列表")
    can_edit: bool = Field(False, description="當前用戶是否可編輯")


class SupplyStationListResponse(BaseModel):
    """物資站點列表回應模型"""
    stations: List[SupplyStationResponse] = Field(..., description="站點列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


class SupplyStationSearchQuery(BaseModel):
    """物資站點搜尋查詢模型"""
    name: Optional[str] = Field(None, description="名稱搜尋")
    is_active: Optional[bool] = Field(None, description="啟用狀態篩選")
    manager_id: Optional[str] = Field(None, description="管理者篩選")
    location_radius: Optional[float] = Field(None, ge=0, description="位置半徑篩選(公里)")
    center_lat: Optional[float] = Field(None, description="中心緯度")
    center_lng: Optional[float] = Field(None, description="中心經度")
    has_supply_type: Optional[str] = Field(None, description="包含特定物資類型")


# 庫存物資相關模型
class InventoryItemBase(BaseModel):
    """庫存物資基礎模型"""
    supply_type: str = Field(..., description="物資類型")
    description: Optional[str] = Field(None, description="物資描述")
    is_available: bool = Field(True, description="是否可用")
    notes: Optional[str] = Field(None, description="備註說明")


class InventoryItemCreate(InventoryItemBase):
    """庫存物資建立模型"""
    station_id: str = Field(..., description="物資站點 ID")


class InventoryItemUpdate(BaseModel):
    """庫存物資更新模型"""
    supply_type: Optional[str] = Field(None, description="物資類型")
    description: Optional[str] = Field(None, description="物資描述")
    is_available: Optional[bool] = Field(None, description="是否可用")
    notes: Optional[str] = Field(None, description="備註說明")


class InventoryItemInDB(InventoryItemBase):
    """資料庫中的庫存物資模型"""
    id: str = Field(..., description="庫存 ID")
    station_id: str = Field(..., description="物資站點 ID")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class InventoryItemResponse(InventoryItemInDB):
    """庫存物資回應模型"""
    station_name: Optional[str] = Field(None, description="站點名稱")
    supply_type_display: Optional[str] = Field(None, description="物資類型顯示名稱")
    can_edit: bool = Field(False, description="當前用戶是否可編輯")


class InventoryListResponse(BaseModel):
    """庫存列表回應模型"""
    items: List[InventoryItemResponse] = Field(..., description="庫存列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


# 物資預訂相關模型
class ReservationItemBase(BaseModel):
    """預訂物資項目基礎模型"""
    supply_type: str = Field(..., description="物資類型")
    requested_quantity: int = Field(1, ge=1, description="請求數量")
    notes: Optional[str] = Field(None, description="備註")


class ReservationItemCreate(ReservationItemBase):
    """預訂物資項目建立模型"""
    pass


class ReservationItemUpdate(BaseModel):
    """預訂物資項目更新模型"""
    confirmed_quantity: Optional[int] = Field(None, ge=0, description="確認數量")
    notes: Optional[str] = Field(None, description="備註")


class ReservationItemInDB(ReservationItemBase):
    """資料庫中的預訂物資項目模型"""
    id: str = Field(..., description="項目 ID")
    reservation_id: str = Field(..., description="預訂 ID")
    confirmed_quantity: Optional[int] = Field(None, description="確認數量")
    
    class Config:
        from_attributes = True


class ReservationItemResponse(ReservationItemInDB):
    """預訂物資項目回應模型"""
    supply_type_display: Optional[str] = Field(None, description="物資類型顯示名稱")


class SupplyReservationBase(BaseModel):
    """物資預訂基礎模型"""
    station_id: str = Field(..., description="物資站點 ID")
    task_id: Optional[str] = Field(None, description="關聯任務 ID")
    need_id: Optional[str] = Field(None, description="關聯需求 ID")
    notes: Optional[str] = Field(None, description="預訂備註")


class SupplyReservationCreate(SupplyReservationBase):
    """物資預訂建立模型"""
    reservation_items: List[ReservationItemCreate] = Field(..., description="預訂物資項目")


class SupplyReservationUpdate(BaseModel):
    """物資預訂更新模型"""
    status: Optional[ReservationStatus] = Field(None, description="預訂狀態")
    notes: Optional[str] = Field(None, description="備註")
    confirmed_at: Optional[datetime] = Field(None, description="確認時間")
    picked_up_at: Optional[datetime] = Field(None, description="領取時間")
    delivered_at: Optional[datetime] = Field(None, description="配送時間")


class SupplyReservationInDB(SupplyReservationBase):
    """資料庫中的物資預訂模型"""
    id: str = Field(..., description="預訂 ID")
    user_id: str = Field(..., description="預訂者 ID")
    status: ReservationStatus = Field(..., description="預訂狀態")
    reserved_at: datetime = Field(..., description="預訂時間")
    confirmed_at: Optional[datetime] = Field(None, description="確認時間")
    picked_up_at: Optional[datetime] = Field(None, description="領取時間")
    delivered_at: Optional[datetime] = Field(None, description="配送時間")
    
    class Config:
        from_attributes = True


class SupplyReservationResponse(SupplyReservationInDB):
    """物資預訂回應模型"""
    user_name: Optional[str] = Field(None, description="預訂者姓名")
    station_name: Optional[str] = Field(None, description="站點名稱")
    task_title: Optional[str] = Field(None, description="關聯任務標題")
    need_title: Optional[str] = Field(None, description="關聯需求標題")
    reservation_items: List[ReservationItemResponse] = Field([], description="預訂物資項目")
    can_edit: bool = Field(False, description="當前用戶是否可編輯")
    can_confirm: bool = Field(False, description="當前用戶是否可確認")


class SupplyReservationListResponse(BaseModel):
    """物資預訂列表回應模型"""
    reservations: List[SupplyReservationResponse] = Field(..., description="預訂列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


# 物資地圖相關模型
class SupplyMapStation(BaseModel):
    """物資地圖站點模型"""
    id: str = Field(..., description="站點 ID")
    name: str = Field(..., description="站點名稱")
    address: str = Field(..., description="地址")
    coordinates: Dict[str, float] = Field(..., description="座標")
    contact_info: ContactInfo = Field(..., description="聯絡資訊")
    available_supplies: List[Dict[str, Any]] = Field([], description="可用物資")
    is_active: bool = Field(..., description="是否啟用")


class SupplyMapResponse(BaseModel):
    """物資地圖回應模型"""
    stations: List[SupplyMapStation] = Field(..., description="站點列表")
    center: Dict[str, float] = Field(..., description="地圖中心點")
    bounds: Dict[str, float] = Field(..., description="地圖邊界")


# 統計相關模型
class SupplyStatistics(BaseModel):
    """物資統計模型"""
    total_stations: int = Field(..., description="總站點數")
    active_stations: int = Field(..., description="啟用站點數")
    total_supply_types: int = Field(..., description="總物資類型數")
    available_supply_types: int = Field(..., description="可用物資類型數")
    pending_reservations: int = Field(..., description="待處理預訂數")
    completed_reservations: int = Field(..., description="已完成預訂數")
    stations_by_manager_role: Dict[str, int] = Field(..., description="各角色管理的站點數")
    supplies_by_type: Dict[str, int] = Field(..., description="各類型物資數量")


class SupplyActivityLog(BaseModel):
    """物資活動日誌模型"""
    timestamp: datetime = Field(..., description="時間戳")
    action: str = Field(..., description="動作類型")
    description: str = Field(..., description="動作描述")
    user_id: Optional[str] = Field(None, description="操作用戶ID")
    user_name: Optional[str] = Field(None, description="操作用戶姓名")
    station_id: Optional[str] = Field(None, description="相關站點ID")
    station_name: Optional[str] = Field(None, description="相關站點名稱")
    notes: Optional[str] = Field(None, description="備註")


# 批量操作模型
class BulkInventoryUpdate(BaseModel):
    """批量庫存更新模型"""
    station_id: str = Field(..., description="物資站點 ID")
    items: List[InventoryItemCreate] = Field(..., description="庫存項目列表")
    replace_existing: bool = Field(False, description="是否替換現有庫存")


class BulkInventoryResponse(BaseModel):
    """批量庫存更新回應模型"""
    success: bool = Field(..., description="是否成功")
    created_count: int = Field(..., description="新建數量")
    updated_count: int = Field(..., description="更新數量")
    deleted_count: int = Field(..., description="刪除數量")
    errors: List[str] = Field([], description="錯誤訊息")