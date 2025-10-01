"""
地理位置相關的 API 端點
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.location_service import location_service
from app.schemas.location import (
    GeocodeRequest, GeocodeResponse,
    ReverseGeocodeRequest, ReverseGeocodeResponse,
    DistanceRequest, DistanceResponse,
    NearbySearchRequest, NearbySupplyStationsResponse, NearbySheltersResponse,
    RouteRequest, RouteResponse,
    LocationValidationRequest, LocationValidationResponse,
    Coordinates, SupplyStationLocation, ShelterLocation
)

router = APIRouter()


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    request: GeocodeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    地址地理編碼 - 將地址轉換為座標
    """
    try:
        result = await location_service.geocode_address(request.address)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="無法找到指定地址的座標資訊"
            )
        
        return GeocodeResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"地理編碼失敗: {str(e)}"
        )


@router.post("/reverse-geocode", response_model=ReverseGeocodeResponse)
async def reverse_geocode_coordinates(
    request: ReverseGeocodeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    反向地理編碼 - 將座標轉換為地址
    """
    try:
        # 驗證座標
        if not location_service.validate_coordinates(request.latitude, request.longitude):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的座標範圍"
            )
        
        result = await location_service.reverse_geocode(request.latitude, request.longitude)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="無法找到指定座標的地址資訊"
            )
        
        return ReverseGeocodeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"反向地理編碼失敗: {str(e)}"
        )


@router.post("/distance", response_model=DistanceResponse)
async def calculate_distance(
    request: DistanceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    計算兩點間的直線距離
    """
    try:
        # 驗證座標
        if not location_service.validate_coordinates(request.origin.lat, request.origin.lng):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="起點座標無效"
            )
        
        if not location_service.validate_coordinates(request.destination.lat, request.destination.lng):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="終點座標無效"
            )
        
        distance_km = location_service.calculate_distance(
            request.origin.lat, request.origin.lng,
            request.destination.lat, request.destination.lng
        )
        
        return DistanceResponse(
            distance_km=round(distance_km, 2),
            origin=request.origin,
            destination=request.destination
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"距離計算失敗: {str(e)}"
        )


@router.post("/nearby/supply-stations", response_model=NearbySupplyStationsResponse)
async def find_nearby_supply_stations(
    request: NearbySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查找附近的物資站點
    """
    try:
        # 驗證座標
        if not location_service.validate_coordinates(request.latitude, request.longitude):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的座標範圍"
            )
        
        nearby_stations = location_service.find_nearby_supply_stations(
            db, request.latitude, request.longitude, 
            request.radius_km, request.limit
        )
        
        stations = []
        for item in nearby_stations:
            station = item["station"]
            coordinates = station.location_data.get("coordinates", {})
            
            stations.append(SupplyStationLocation(
                id=str(station.id),
                name=station.name,
                address=station.address,
                coordinates=Coordinates(
                    lat=coordinates.get("lat", 0),
                    lng=coordinates.get("lng", 0)
                ),
                contact_info=station.contact_info,
                distance_km=item["distance_km"],
                is_active=station.is_active
            ))
        
        return NearbySupplyStationsResponse(
            center=Coordinates(lat=request.latitude, lng=request.longitude),
            radius_km=request.radius_km,
            total_found=len(stations),
            stations=stations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找附近物資站點失敗: {str(e)}"
        )


@router.post("/nearby/shelters", response_model=NearbySheltersResponse)
async def find_nearby_shelters(
    request: NearbySearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查找附近的避難所
    """
    try:
        # 驗證座標
        if not location_service.validate_coordinates(request.latitude, request.longitude):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的座標範圍"
            )
        
        nearby_shelters = location_service.find_nearby_shelters(
            db, request.latitude, request.longitude, 
            request.radius_km, request.limit
        )
        
        shelters = []
        for item in nearby_shelters:
            shelter = item["shelter"]
            coordinates = shelter.location_data.get("coordinates", {})
            
            shelters.append(ShelterLocation(
                id=str(shelter.id),
                name=shelter.name,
                address=shelter.address,
                coordinates=Coordinates(
                    lat=coordinates.get("lat", 0),
                    lng=coordinates.get("lng", 0)
                ),
                capacity=shelter.capacity,
                current_occupancy=shelter.current_occupancy,
                status=shelter.status,
                distance_km=item["distance_km"],
                facilities=shelter.facilities
            ))
        
        return NearbySheltersResponse(
            center=Coordinates(lat=request.latitude, lng=request.longitude),
            radius_km=request.radius_km,
            total_found=len(shelters),
            shelters=shelters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查找附近避難所失敗: {str(e)}"
        )


@router.post("/route", response_model=RouteResponse)
async def get_route_info(
    request: RouteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    獲取兩點間的路線資訊（距離和時間）
    """
    try:
        # 驗證座標
        if not location_service.validate_coordinates(request.origin.lat, request.origin.lng):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="起點座標無效"
            )
        
        if not location_service.validate_coordinates(request.destination.lat, request.destination.lng):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="終點座標無效"
            )
        
        route_info = await location_service.get_route_distance_duration(
            request.origin.lat, request.origin.lng,
            request.destination.lat, request.destination.lng
        )
        
        if not route_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="無法計算路線資訊"
            )
        
        return RouteResponse(
            origin=request.origin,
            destination=request.destination,
            distance=route_info["distance"],
            duration=route_info["duration"],
            status=route_info["status"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"路線查詢失敗: {str(e)}"
        )


@router.post("/validate", response_model=LocationValidationResponse)
async def validate_coordinates(
    request: LocationValidationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    驗證座標是否有效
    """
    try:
        is_valid = location_service.validate_coordinates(request.latitude, request.longitude)
        
        message = None
        if not is_valid:
            if not (-90 <= request.latitude <= 90):
                message = "緯度必須在 -90 到 90 之間"
            elif not (-180 <= request.longitude <= 180):
                message = "經度必須在 -180 到 180 之間"
            elif not (21.0 <= request.latitude <= 26.0 and 119.0 <= request.longitude <= 123.0):
                message = "座標不在台灣範圍內"
            else:
                message = "無效的座標"
        
        return LocationValidationResponse(
            is_valid=is_valid,
            latitude=request.latitude,
            longitude=request.longitude,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"座標驗證失敗: {str(e)}"
        )