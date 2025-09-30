"""
地理位置服務模組

提供地理位置相關功能：
- 地址地理編碼和反向地理編碼
- 距離計算
- 附近站點查詢
"""

import math
from typing import List, Optional, Dict, Any, Tuple
import httpx
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.supply import SupplyStation
from app.models.system import Shelter


class LocationService:
    """地理位置服務類別"""
    
    def __init__(self):
        self.google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"
        
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        地址地理編碼 - 將地址轉換為經緯度座標
        
        Args:
            address: 地址字串
            
        Returns:
            包含座標和詳細資訊的字典，如果失敗則返回 None
        """
        if not self.google_maps_api_key:
            # 如果沒有 API Key，返回預設的光復鄉座標
            return self._get_default_coordinates(address)
            
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "address": address,
                    "key": self.google_maps_api_key,
                    "language": "zh-TW",
                    "region": "tw"
                }
                
                response = await client.get(
                    f"{self.base_url}/geocode/json",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data["status"] == "OK" and data["results"]:
                        result = data["results"][0]
                        location = result["geometry"]["location"]
                        
                        return {
                            "latitude": location["lat"],
                            "longitude": location["lng"],
                            "formatted_address": result["formatted_address"],
                            "place_id": result.get("place_id"),
                            "address_components": result.get("address_components", []),
                            "geometry": result["geometry"]
                        }
                        
        except Exception as e:
            print(f"Geocoding error: {e}")
            
        # 如果 API 調用失敗，返回預設座標
        return self._get_default_coordinates(address)
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        反向地理編碼 - 將經緯度座標轉換為地址
        
        Args:
            latitude: 緯度
            longitude: 經度
            
        Returns:
            包含地址資訊的字典，如果失敗則返回 None
        """
        if not self.google_maps_api_key:
            return {
                "formatted_address": f"緯度: {latitude}, 經度: {longitude}",
                "address_components": []
            }
            
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "latlng": f"{latitude},{longitude}",
                    "key": self.google_maps_api_key,
                    "language": "zh-TW",
                    "result_type": "street_address|route|locality|administrative_area_level_1"
                }
                
                response = await client.get(
                    f"{self.base_url}/geocode/json",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data["status"] == "OK" and data["results"]:
                        result = data["results"][0]
                        
                        return {
                            "formatted_address": result["formatted_address"],
                            "address_components": result.get("address_components", []),
                            "place_id": result.get("place_id"),
                            "geometry": result["geometry"]
                        }
                        
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            
        return {
            "formatted_address": f"緯度: {latitude}, 經度: {longitude}",
            "address_components": []
        }
    
    def calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        計算兩點間的距離（使用 Haversine 公式）
        
        Args:
            lat1, lon1: 第一個點的緯度和經度
            lat2, lon2: 第二個點的緯度和經度
            
        Returns:
            距離（公里）
        """
        # 將度數轉換為弧度
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine 公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公里）
        earth_radius = 6371.0
        
        return earth_radius * c
    
    def find_nearby_supply_stations(
        self, 
        db: Session,
        latitude: float, 
        longitude: float, 
        radius_km: float = 10.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查找附近的物資站點
        
        Args:
            db: 資料庫會話
            latitude: 中心點緯度
            longitude: 中心點經度
            radius_km: 搜尋半徑（公里）
            limit: 返回結果數量限制
            
        Returns:
            附近物資站點列表，包含距離資訊
        """
        # 查詢所有活躍的物資站點
        stations = db.query(SupplyStation).filter(
            SupplyStation.is_active == True
        ).all()
        
        nearby_stations = []
        
        for station in stations:
            if station.location_data and "coordinates" in station.location_data:
                coords = station.location_data["coordinates"]
                if "lat" in coords and "lng" in coords:
                    distance = self.calculate_distance(
                        latitude, longitude,
                        coords["lat"], coords["lng"]
                    )
                    
                    if distance <= radius_km:
                        nearby_stations.append({
                            "station": station,
                            "distance_km": round(distance, 2)
                        })
        
        # 按距離排序
        nearby_stations.sort(key=lambda x: x["distance_km"])
        
        return nearby_stations[:limit]
    
    def find_nearby_shelters(
        self, 
        db: Session,
        latitude: float, 
        longitude: float, 
        radius_km: float = 15.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查找附近的避難所
        
        Args:
            db: 資料庫會話
            latitude: 中心點緯度
            longitude: 中心點經度
            radius_km: 搜尋半徑（公里）
            limit: 返回結果數量限制
            
        Returns:
            附近避難所列表，包含距離資訊
        """
        # 查詢所有活躍的避難所
        shelters = db.query(Shelter).filter(
            Shelter.status.in_(["active", "full"])
        ).all()
        
        nearby_shelters = []
        
        for shelter in shelters:
            if shelter.location_data and "coordinates" in shelter.location_data:
                coords = shelter.location_data["coordinates"]
                if "lat" in coords and "lng" in coords:
                    distance = self.calculate_distance(
                        latitude, longitude,
                        coords["lat"], coords["lng"]
                    )
                    
                    if distance <= radius_km:
                        nearby_shelters.append({
                            "shelter": shelter,
                            "distance_km": round(distance, 2)
                        })
        
        # 按距離排序
        nearby_shelters.sort(key=lambda x: x["distance_km"])
        
        return nearby_shelters[:limit]
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        驗證座標是否有效
        
        Args:
            latitude: 緯度
            longitude: 經度
            
        Returns:
            座標是否有效
        """
        # 檢查緯度範圍 (-90 到 90)
        if not (-90 <= latitude <= 90):
            return False
            
        # 檢查經度範圍 (-180 到 180)
        if not (-180 <= longitude <= 180):
            return False
            
        # 檢查是否在台灣範圍內（大致範圍）
        # 台灣緯度約 21.9-25.3，經度約 120.1-122.0
        if not (21.0 <= latitude <= 26.0 and 119.0 <= longitude <= 123.0):
            return False
            
        return True
    
    def _get_default_coordinates(self, address: str) -> Dict[str, Any]:
        """
        獲取預設座標（光復鄉中心）
        
        Args:
            address: 原始地址
            
        Returns:
            預設座標資訊
        """
        # 光復鄉公所座標
        return {
            "latitude": 23.6739,
            "longitude": 121.4015,
            "formatted_address": f"花蓮縣光復鄉 - {address}",
            "place_id": None,
            "address_components": [
                {
                    "long_name": "光復鄉",
                    "short_name": "光復鄉",
                    "types": ["locality", "political"]
                },
                {
                    "long_name": "花蓮縣",
                    "short_name": "花蓮縣",
                    "types": ["administrative_area_level_1", "political"]
                },
                {
                    "long_name": "台灣",
                    "short_name": "TW",
                    "types": ["country", "political"]
                }
            ],
            "geometry": {
                "location": {
                    "lat": 23.6739,
                    "lng": 121.4015
                },
                "location_type": "APPROXIMATE"
            }
        }
    
    async def get_route_distance_duration(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float
    ) -> Optional[Dict[str, Any]]:
        """
        獲取兩點間的路線距離和時間
        
        Args:
            origin_lat, origin_lng: 起點座標
            dest_lat, dest_lng: 終點座標
            
        Returns:
            包含距離和時間的字典
        """
        if not self.google_maps_api_key:
            # 如果沒有 API Key，使用直線距離估算
            distance_km = self.calculate_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            # 假設平均速度 30 km/h
            duration_minutes = int((distance_km / 30) * 60)
            
            return {
                "distance": {
                    "text": f"{distance_km:.1f} 公里",
                    "value": int(distance_km * 1000)  # 轉換為公尺
                },
                "duration": {
                    "text": f"{duration_minutes} 分鐘",
                    "value": duration_minutes * 60  # 轉換為秒
                },
                "status": "ESTIMATED"
            }
            
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "origins": f"{origin_lat},{origin_lng}",
                    "destinations": f"{dest_lat},{dest_lng}",
                    "key": self.google_maps_api_key,
                    "language": "zh-TW",
                    "units": "metric",
                    "mode": "driving"
                }
                
                response = await client.get(
                    f"{self.base_url}/distancematrix/json",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if (data["status"] == "OK" and 
                        data["rows"] and 
                        data["rows"][0]["elements"] and
                        data["rows"][0]["elements"][0]["status"] == "OK"):
                        
                        element = data["rows"][0]["elements"][0]
                        return {
                            "distance": element["distance"],
                            "duration": element["duration"],
                            "status": "OK"
                        }
                        
        except Exception as e:
            print(f"Route calculation error: {e}")
            
        return None


# 創建全域服務實例
location_service = LocationService()