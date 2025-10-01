"""
地理位置處理輔助函數

提供與現有模型整合的地理位置處理功能
"""

from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.services.location_service import location_service
from app.schemas.location import LocationData, Coordinates


async def process_location_data(
    address: str, 
    coordinates: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    處理位置資料，結合地址和座標資訊
    
    Args:
        address: 地址字串
        coordinates: 可選的座標字典 {"lat": float, "lng": float}
        
    Returns:
        標準化的位置資料字典
    """
    location_data = {
        "address": address,
        "coordinates": {},
        "formatted_address": None,
        "place_id": None,
        "details": {}
    }
    
    # 如果提供了座標，先驗證
    if coordinates and "lat" in coordinates and "lng" in coordinates:
        lat, lng = coordinates["lat"], coordinates["lng"]
        
        if location_service.validate_coordinates(lat, lng):
            location_data["coordinates"] = {"lat": lat, "lng": lng}
            
            # 進行反向地理編碼獲取格式化地址
            try:
                reverse_result = await location_service.reverse_geocode(lat, lng)
                if reverse_result:
                    location_data["formatted_address"] = reverse_result["formatted_address"]
                    location_data["place_id"] = reverse_result.get("place_id")
            except Exception as e:
                print(f"Reverse geocoding failed: {e}")
        else:
            # 座標無效，清除座標資訊
            coordinates = None
    
    # 如果沒有有效座標，進行地理編碼
    if not location_data["coordinates"]:
        try:
            geocode_result = await location_service.geocode_address(address)
            if geocode_result:
                location_data["coordinates"] = {
                    "lat": geocode_result["latitude"],
                    "lng": geocode_result["longitude"]
                }
                location_data["formatted_address"] = geocode_result["formatted_address"]
                location_data["place_id"] = geocode_result.get("place_id")
        except Exception as e:
            print(f"Geocoding failed: {e}")
    
    return location_data


def extract_coordinates_from_location_data(location_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """
    從位置資料中提取座標
    
    Args:
        location_data: 位置資料字典
        
    Returns:
        座標元組 (lat, lng) 或 None
    """
    if not location_data or not isinstance(location_data, dict):
        return None
    
    coordinates = location_data.get("coordinates", {})
    if not coordinates or not isinstance(coordinates, dict):
        return None
    
    lat = coordinates.get("lat")
    lng = coordinates.get("lng")
    
    if lat is not None and lng is not None:
        try:
            return float(lat), float(lng)
        except (ValueError, TypeError):
            return None
    
    return None


def calculate_distance_between_locations(
    location1: Dict[str, Any], 
    location2: Dict[str, Any]
) -> Optional[float]:
    """
    計算兩個位置之間的距離
    
    Args:
        location1: 第一個位置資料
        location2: 第二個位置資料
        
    Returns:
        距離（公里）或 None
    """
    coords1 = extract_coordinates_from_location_data(location1)
    coords2 = extract_coordinates_from_location_data(location2)
    
    if not coords1 or not coords2:
        return None
    
    return location_service.calculate_distance(
        coords1[0], coords1[1], coords2[0], coords2[1]
    )


def validate_location_data(location_data: Dict[str, Any]) -> bool:
    """
    驗證位置資料是否有效
    
    Args:
        location_data: 位置資料字典
        
    Returns:
        是否有效
    """
    if not location_data or not isinstance(location_data, dict):
        return False
    
    # 檢查必要欄位
    if "address" not in location_data or not location_data["address"]:
        return False
    
    # 檢查座標
    coordinates = extract_coordinates_from_location_data(location_data)
    if coordinates:
        return location_service.validate_coordinates(coordinates[0], coordinates[1])
    
    return True  # 沒有座標但有地址也算有效


def format_location_for_display(location_data: Dict[str, Any]) -> str:
    """
    格式化位置資料用於顯示
    
    Args:
        location_data: 位置資料字典
        
    Returns:
        格式化的位置字串
    """
    if not location_data:
        return "未知位置"
    
    # 優先使用格式化地址
    formatted_address = location_data.get("formatted_address")
    if formatted_address:
        return formatted_address
    
    # 其次使用原始地址
    address = location_data.get("address")
    if address:
        return address
    
    # 最後使用座標
    coordinates = extract_coordinates_from_location_data(location_data)
    if coordinates:
        return f"緯度: {coordinates[0]:.4f}, 經度: {coordinates[1]:.4f}"
    
    return "未知位置"


async def enrich_location_data(location_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    豐富位置資料，補充缺失的資訊
    
    Args:
        location_data: 原始位置資料
        
    Returns:
        豐富後的位置資料
    """
    if not location_data:
        return {}
    
    enriched_data = location_data.copy()
    
    # 如果有座標但沒有格式化地址，進行反向地理編碼
    coordinates = extract_coordinates_from_location_data(location_data)
    if coordinates and not enriched_data.get("formatted_address"):
        try:
            reverse_result = await location_service.reverse_geocode(coordinates[0], coordinates[1])
            if reverse_result:
                enriched_data["formatted_address"] = reverse_result["formatted_address"]
                if not enriched_data.get("place_id"):
                    enriched_data["place_id"] = reverse_result.get("place_id")
        except Exception as e:
            print(f"Failed to enrich location data: {e}")
    
    # 如果有地址但沒有座標，進行地理編碼
    elif enriched_data.get("address") and not coordinates:
        try:
            geocode_result = await location_service.geocode_address(enriched_data["address"])
            if geocode_result:
                enriched_data["coordinates"] = {
                    "lat": geocode_result["latitude"],
                    "lng": geocode_result["longitude"]
                }
                if not enriched_data.get("formatted_address"):
                    enriched_data["formatted_address"] = geocode_result["formatted_address"]
                if not enriched_data.get("place_id"):
                    enriched_data["place_id"] = geocode_result.get("place_id")
        except Exception as e:
            print(f"Failed to enrich location data: {e}")
    
    return enriched_data


def create_location_data_from_coordinates(
    lat: float, 
    lng: float, 
    address: Optional[str] = None
) -> Dict[str, Any]:
    """
    從座標創建位置資料
    
    Args:
        lat: 緯度
        lng: 經度
        address: 可選的地址
        
    Returns:
        位置資料字典
    """
    return {
        "address": address or f"緯度: {lat}, 經度: {lng}",
        "coordinates": {"lat": lat, "lng": lng},
        "formatted_address": None,
        "place_id": None,
        "details": {}
    }


def create_location_data_from_address(address: str) -> Dict[str, Any]:
    """
    從地址創建位置資料
    
    Args:
        address: 地址
        
    Returns:
        位置資料字典
    """
    return {
        "address": address,
        "coordinates": {},
        "formatted_address": None,
        "place_id": None,
        "details": {}
    }