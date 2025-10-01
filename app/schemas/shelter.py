"""
避難所管理相關的 Pydantic 模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.utils.constants import UserRole


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
    emergency_contact: Optional[str] = Field(None, description="緊急聯絡方式")


class FacilityInfo(BaseModel):
    """設施資訊模型"""
    has_medical: bool = Field(False, description="是否有醫療設施")
    has_kitchen: bool = Field(False, description="是否有廚房")
    has_shower: bool = Field(False, description="是否有淋浴設施")
    has_wifi: bool = Field(False, description="是否有無線網路")
    has_generator: bool = Field(False, description="是否有發電機")
    has_wheelchair_access: bool = Field(False, description="是否有無障礙設施")
    pet_friendly: bool = Field(False, description="是否允許寵物")
    additional_facilities: Optional[List[str]] = Field([], description="其他設施")
    notes: Optional[str] = Field(None, description="設施備註")


# 避難所相關模型
class ShelterBase(BaseModel):
    """避難所基礎模型"""
    name: str = Field(..., min_length=1, max_length=200, description="避難所名稱")
    address: str = Field(..., min_length=1, description="避難所地址")
    location_data: LocationData = Field(..., description="地理位置資訊")
    capacity: Optional[int] = Field(None, ge=0, description="容量")
    contact_info: Optional[ContactInfo] = Field(None, description="聯絡資訊")
    facilities: Optional[FacilityInfo] = Field(None, description="設施資訊")


class ShelterCreate(ShelterBase):
    """避難所建立模型"""
    managed_by: Optional[str] = Field(None, description="管理者 ID")


class ShelterUpdate(BaseModel):
    """避難所更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="避難所名稱")
    address: Optional[str] = Field(None, min_length=1, description="避難所地址")
    location_data: Optional[LocationData] = Field(None, description="地理位置資訊")
    capacity: Optional[int] = Field(None, ge=0, description="容量")
    current_occupancy: Optional[int] = Field(None, ge=0, description="目前入住人數")
    contact_info: Optional[ContactInfo] = Field(None, description="聯絡資訊")
    facilities: Optional[FacilityInfo] = Field(None, description="設施資訊")
    status: Optional[str] = Field(None, description="狀態")
    managed_by: Optional[str] = Field(None, description="管理者 ID")
    
    @validator('current_occupancy')
    def validate_occupancy(cls, v, values):
        if v is not None and 'capacity' in values and values['capacity'] is not None:
            if v > values['capacity']:
                raise ValueError('目前入住人數不能超過容量')
        return v


class ShelterInDB(ShelterBase):
    """資料庫中的避難所模型"""
    id: str = Field(..., description="避難所 ID")
    current_occupancy: int = Field(0, description="目前入住人數")
    status: str = Field("active", description="狀態")
    managed_by: Optional[str] = Field(None, description="管理者 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class ShelterResponse(ShelterInDB):
    """避難所回應模型"""
    manager_name: Optional[str] = Field(None, description="管理者姓名")
    manager_role: Optional[UserRole] = Field(None, description="管理者角色")
    occupancy_rate: float = Field(0.0, description="入住率")
    is_available: bool = Field(True, description="是否可入住")
    distance_from_center: Optional[float] = Field(None, description="距離中心點距離(公里)")
    can_edit: bool = Field(False, description="當前用戶是否可編輯")


class ShelterListResponse(BaseModel):
    """避難所列表回應模型"""
    shelters: List[ShelterResponse] = Field(..., description="避難所列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


class ShelterSearchQuery(BaseModel):
    """避難所搜尋查詢模型"""
    name: Optional[str] = Field(None, description="名稱搜尋")
    status: Optional[str] = Field(None, description="狀態篩選")
    has_capacity: Optional[bool] = Field(None, description="是否有空位")
    manager_id: Optional[str] = Field(None, description="管理者篩選")
    location_radius: Optional[float] = Field(None, ge=0, description="位置半徑篩選(公里)")
    center_lat: Optional[float] = Field(None, description="中心緯度")
    center_lng: Optional[float] = Field(None, description="中心經度")
    has_facility: Optional[str] = Field(None, description="包含特定設施")
    min_capacity: Optional[int] = Field(None, ge=0, description="最小容量")
    max_occupancy_rate: Optional[float] = Field(None, ge=0, le=1, description="最大入住率")


# 避難所地圖相關模型
class ShelterMapItem(BaseModel):
    """避難所地圖項目模型"""
    id: str = Field(..., description="避難所 ID")
    name: str = Field(..., description="避難所名稱")
    address: str = Field(..., description="地址")
    coordinates: Dict[str, float] = Field(..., description="座標")
    capacity: Optional[int] = Field(None, description="容量")
    current_occupancy: int = Field(0, description="目前入住人數")
    status: str = Field(..., description="狀態")
    contact_info: Optional[ContactInfo] = Field(None, description="聯絡資訊")
    facilities: Optional[FacilityInfo] = Field(None, description="設施資訊")
    occupancy_rate: float = Field(0.0, description="入住率")
    is_available: bool = Field(True, description="是否可入住")


class ShelterMapResponse(BaseModel):
    """避難所地圖回應模型"""
    shelters: List[ShelterMapItem] = Field(..., description="避難所列表")
    center: Dict[str, float] = Field(..., description="地圖中心點")
    bounds: Dict[str, float] = Field(..., description="地圖邊界")


# 避難所推薦相關模型
class ShelterRecommendationQuery(BaseModel):
    """避難所推薦查詢模型"""
    user_location: Dict[str, float] = Field(..., description="用戶位置座標")
    required_capacity: int = Field(1, ge=1, description="所需容量")
    required_facilities: Optional[List[str]] = Field([], description="所需設施")
    max_distance: Optional[float] = Field(10.0, ge=0, description="最大距離(公里)")
    exclude_full: bool = Field(True, description="是否排除已滿的避難所")


class ShelterRecommendation(BaseModel):
    """避難所推薦模型"""
    shelter: ShelterResponse = Field(..., description="避難所資訊")
    distance: float = Field(..., description="距離(公里)")
    available_capacity: int = Field(..., description="可用容量")
    matching_facilities: List[str] = Field([], description="符合的設施")
    recommendation_score: float = Field(..., description="推薦分數")
    recommendation_reason: str = Field(..., description="推薦原因")


class ShelterRecommendationResponse(BaseModel):
    """避難所推薦回應模型"""
    recommendations: List[ShelterRecommendation] = Field(..., description="推薦列表")
    query_location: Dict[str, float] = Field(..., description="查詢位置")
    total_found: int = Field(..., description="找到的避難所總數")


# 統計相關模型
class ShelterStatistics(BaseModel):
    """避難所統計模型"""
    total_shelters: int = Field(..., description="總避難所數")
    active_shelters: int = Field(..., description="啟用避難所數")
    total_capacity: int = Field(..., description="總容量")
    total_occupancy: int = Field(..., description="總入住人數")
    average_occupancy_rate: float = Field(..., description="平均入住率")
    shelters_by_status: Dict[str, int] = Field(..., description="各狀態避難所數量")
    shelters_by_capacity_range: Dict[str, int] = Field(..., description="各容量範圍避難所數量")
    facilities_availability: Dict[str, int] = Field(..., description="各設施可用性統計")


class ShelterOccupancyUpdate(BaseModel):
    """避難所入住人數更新模型"""
    current_occupancy: int = Field(..., ge=0, description="目前入住人數")
    notes: Optional[str] = Field(None, description="更新備註")


class ShelterStatusUpdate(BaseModel):
    """避難所狀態更新模型"""
    status: str = Field(..., description="新狀態")
    reason: Optional[str] = Field(None, description="狀態變更原因")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'full', 'closed', 'maintenance']
        if v not in valid_statuses:
            raise ValueError(f'狀態必須是以下之一: {", ".join(valid_statuses)}')
        return v


# 批量操作模型
class BulkShelterUpdate(BaseModel):
    """批量避難所更新模型"""
    shelter_updates: List[Dict[str, Any]] = Field(..., description="避難所更新列表")
    update_type: str = Field(..., description="更新類型")
    
    @validator('update_type')
    def validate_update_type(cls, v):
        valid_types = ['occupancy', 'status', 'facilities', 'contact']
        if v not in valid_types:
            raise ValueError(f'更新類型必須是以下之一: {", ".join(valid_types)}')
        return v


class BulkShelterResponse(BaseModel):
    """批量避難所更新回應模型"""
    success: bool = Field(..., description="是否成功")
    updated_count: int = Field(..., description="更新數量")
    failed_count: int = Field(..., description="失敗數量")
    errors: List[str] = Field([], description="錯誤訊息")
    updated_shelters: List[str] = Field([], description="已更新的避難所ID列表")