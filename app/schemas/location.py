"""
地理位置相關的 Pydantic 模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class Coordinates(BaseModel):
    """座標模型"""
    lat: float = Field(..., description="緯度", ge=-90, le=90)
    lng: float = Field(..., description="經度", ge=-180, le=180)
    
    @field_validator('lat', 'lng')
    @classmethod
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('座標必須是數字')
        return float(v)


class AddressComponent(BaseModel):
    """地址組件模型"""
    long_name: str = Field(..., description="完整名稱")
    short_name: str = Field(..., description="簡短名稱")
    types: List[str] = Field(..., description="地址類型")


class GeocodeRequest(BaseModel):
    """地理編碼請求模型"""
    address: str = Field(..., description="要編碼的地址", min_length=1, max_length=500)


class GeocodeResponse(BaseModel):
    """地理編碼回應模型"""
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    formatted_address: str = Field(..., description="格式化地址")
    place_id: Optional[str] = Field(None, description="Google Place ID")
    address_components: List[AddressComponent] = Field(default_factory=list, description="地址組件")
    geometry: Optional[Dict[str, Any]] = Field(None, description="幾何資訊")


class ReverseGeocodeRequest(BaseModel):
    """反向地理編碼請求模型"""
    latitude: float = Field(..., description="緯度", ge=-90, le=90)
    longitude: float = Field(..., description="經度", ge=-180, le=180)


class ReverseGeocodeResponse(BaseModel):
    """反向地理編碼回應模型"""
    formatted_address: str = Field(..., description="格式化地址")
    address_components: List[AddressComponent] = Field(default_factory=list, description="地址組件")
    place_id: Optional[str] = Field(None, description="Google Place ID")
    geometry: Optional[Dict[str, Any]] = Field(None, description="幾何資訊")


class DistanceRequest(BaseModel):
    """距離計算請求模型"""
    origin: Coordinates = Field(..., description="起點座標")
    destination: Coordinates = Field(..., description="終點座標")


class DistanceResponse(BaseModel):
    """距離計算回應模型"""
    distance_km: float = Field(..., description="距離（公里）")
    origin: Coordinates = Field(..., description="起點座標")
    destination: Coordinates = Field(..., description="終點座標")


class NearbySearchRequest(BaseModel):
    """附近搜尋請求模型"""
    latitude: float = Field(..., description="中心點緯度", ge=-90, le=90)
    longitude: float = Field(..., description="中心點經度", ge=-180, le=180)
    radius_km: float = Field(10.0, description="搜尋半徑（公里）", gt=0, le=50)
    limit: int = Field(10, description="返回結果數量限制", gt=0, le=50)


class SupplyStationLocation(BaseModel):
    """物資站點位置資訊"""
    id: str = Field(..., description="站點ID")
    name: str = Field(..., description="站點名稱")
    address: str = Field(..., description="站點地址")
    coordinates: Coordinates = Field(..., description="站點座標")
    contact_info: Dict[str, Any] = Field(..., description="聯絡資訊")
    distance_km: float = Field(..., description="距離（公里）")
    is_active: bool = Field(..., description="是否活躍")


class ShelterLocation(BaseModel):
    """避難所位置資訊"""
    id: str = Field(..., description="避難所ID")
    name: str = Field(..., description="避難所名稱")
    address: str = Field(..., description="避難所地址")
    coordinates: Coordinates = Field(..., description="避難所座標")
    capacity: Optional[int] = Field(None, description="容量")
    current_occupancy: Optional[int] = Field(None, description="目前入住人數")
    status: str = Field(..., description="狀態")
    distance_km: float = Field(..., description="距離（公里）")
    facilities: Optional[Dict[str, Any]] = Field(None, description="設施資訊")


class NearbySupplyStationsResponse(BaseModel):
    """附近物資站點回應模型"""
    center: Coordinates = Field(..., description="搜尋中心點")
    radius_km: float = Field(..., description="搜尋半徑")
    total_found: int = Field(..., description="找到的總數")
    stations: List[SupplyStationLocation] = Field(..., description="物資站點列表")


class NearbySheltersResponse(BaseModel):
    """附近避難所回應模型"""
    center: Coordinates = Field(..., description="搜尋中心點")
    radius_km: float = Field(..., description="搜尋半徑")
    total_found: int = Field(..., description="找到的總數")
    shelters: List[ShelterLocation] = Field(..., description="避難所列表")


class RouteRequest(BaseModel):
    """路線查詢請求模型"""
    origin: Coordinates = Field(..., description="起點座標")
    destination: Coordinates = Field(..., description="終點座標")


class RouteDistance(BaseModel):
    """路線距離資訊"""
    text: str = Field(..., description="距離文字描述")
    value: int = Field(..., description="距離值（公尺）")


class RouteDuration(BaseModel):
    """路線時間資訊"""
    text: str = Field(..., description="時間文字描述")
    value: int = Field(..., description="時間值（秒）")


class RouteResponse(BaseModel):
    """路線查詢回應模型"""
    origin: Coordinates = Field(..., description="起點座標")
    destination: Coordinates = Field(..., description="終點座標")
    distance: RouteDistance = Field(..., description="距離資訊")
    duration: RouteDuration = Field(..., description="時間資訊")
    status: str = Field(..., description="查詢狀態")


class LocationValidationRequest(BaseModel):
    """位置驗證請求模型"""
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")


class LocationValidationResponse(BaseModel):
    """位置驗證回應模型"""
    is_valid: bool = Field(..., description="座標是否有效")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    message: Optional[str] = Field(None, description="驗證訊息")


class LocationData(BaseModel):
    """通用位置資料模型（用於資料庫儲存）"""
    address: str = Field(..., description="地址")
    coordinates: Coordinates = Field(..., description="座標")
    formatted_address: Optional[str] = Field(None, description="格式化地址")
    place_id: Optional[str] = Field(None, description="Google Place ID")
    details: Optional[Dict[str, Any]] = Field(None, description="額外詳細資訊")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "花蓮縣光復鄉中正路一段1號",
                "coordinates": {
                    "lat": 23.6739,
                    "lng": 121.4015
                },
                "formatted_address": "970花蓮縣光復鄉中正路一段1號",
                "place_id": "ChIJ...",
                "details": {
                    "landmark": "光復鄉公所",
                    "notes": "主要辦公地點"
                }
            }
        }