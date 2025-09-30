"""
避難所管理 API 端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.shelter_service import shelter_service
from app.schemas.shelter import (
    ShelterCreate, ShelterUpdate, ShelterResponse, 
    ShelterListResponse, ShelterSearchQuery,
    ShelterMapResponse, ShelterRecommendationQuery, ShelterRecommendationResponse,
    ShelterStatistics, ShelterOccupancyUpdate, ShelterStatusUpdate,
    BulkShelterUpdate, BulkShelterResponse
)
from app.utils.constants import UserRole

router = APIRouter()


@router.post("/", response_model=ShelterResponse, status_code=status.HTTP_201_CREATED)
def create_shelter(
    shelter_data: ShelterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    建立新避難所
    
    - **只有管理員可以建立避難所**
    - 可以指定管理者，如果不指定則由建立者管理
    """
    return shelter_service.create_shelter(
        db=db,
        shelter_data=shelter_data,
        creator_id=str(current_user.id),
        creator_role=UserRole(current_user.role)
    )


@router.get("/", response_model=ShelterListResponse)
def get_shelters(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="返回的記錄數"),
    name: Optional[str] = Query(None, description="名稱搜尋"),
    status: Optional[str] = Query(None, description="狀態篩選"),
    has_capacity: Optional[bool] = Query(None, description="是否有空位"),
    manager_id: Optional[str] = Query(None, description="管理者篩選"),
    location_radius: Optional[float] = Query(None, ge=0, description="位置半徑篩選(公里)"),
    center_lat: Optional[float] = Query(None, description="中心緯度"),
    center_lng: Optional[float] = Query(None, description="中心經度"),
    has_facility: Optional[str] = Query(None, description="包含特定設施"),
    min_capacity: Optional[int] = Query(None, ge=0, description="最小容量"),
    max_occupancy_rate: Optional[float] = Query(None, ge=0, le=1, description="最大入住率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取避難所列表
    
    支援多種篩選條件：
    - 名稱搜尋
    - 狀態篩選
    - 容量篩選
    - 地理位置篩選
    - 設施篩選
    """
    search_query = ShelterSearchQuery(
        name=name,
        status=status,
        has_capacity=has_capacity,
        manager_id=manager_id,
        location_radius=location_radius,
        center_lat=center_lat,
        center_lng=center_lng,
        has_facility=has_facility,
        min_capacity=min_capacity,
        max_occupancy_rate=max_occupancy_rate
    )
    
    return shelter_service.get_shelters(
        db=db,
        skip=skip,
        limit=limit,
        search_query=search_query,
        user_id=str(current_user.id),
        user_role=UserRole(current_user.role)
    )


@router.get("/map", response_model=ShelterMapResponse)
def get_shelter_map(
    center_lat: Optional[float] = Query(None, description="中心緯度"),
    center_lng: Optional[float] = Query(None, description="中心經度"),
    radius: Optional[float] = Query(None, ge=0, description="搜尋半徑(公里)"),
    status_filter: Optional[str] = Query(None, description="狀態篩選"),
    has_capacity: Optional[bool] = Query(None, description="是否有空位"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取避難所地圖資料
    
    返回適合在地圖上顯示的避難所資訊
    """
    return shelter_service.get_shelter_map(
        db=db,
        center_lat=center_lat,
        center_lng=center_lng,
        radius=radius,
        status_filter=status_filter,
        has_capacity=has_capacity
    )


@router.post("/recommendations", response_model=ShelterRecommendationResponse)
def get_shelter_recommendations(
    query_data: ShelterRecommendationQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取避難所推薦
    
    根據用戶位置、需求容量和設施需求推薦最適合的避難所
    """
    return shelter_service.get_shelter_recommendations(db=db, query_data=query_data)


@router.get("/nearby", response_model=List[ShelterResponse])
def get_nearby_shelters(
    user_lat: float = Query(..., description="用戶緯度"),
    user_lng: float = Query(..., description="用戶經度"),
    radius: float = Query(10.0, ge=0, description="搜尋半徑(公里)"),
    limit: int = Query(10, ge=1, le=50, description="返回數量"),
    has_capacity: bool = Query(True, description="是否只顯示有空位的避難所"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取附近的避難所
    
    根據用戶位置返回附近的避難所，按距離排序
    """
    return shelter_service.get_nearby_shelters(
        db=db,
        user_lat=user_lat,
        user_lng=user_lng,
        radius=radius,
        limit=limit,
        has_capacity=has_capacity
    )


@router.get("/available", response_model=ShelterListResponse)
def get_available_shelters(
    required_capacity: int = Query(1, ge=1, description="所需容量"),
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="返回的記錄數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取可用的避難所
    
    返回狀態為 active 且有足夠容量的避難所
    """
    return shelter_service.get_available_shelters(
        db=db,
        required_capacity=required_capacity,
        skip=skip,
        limit=limit
    )


@router.get("/statistics", response_model=ShelterStatistics)
def get_shelter_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取避難所統計資料
    
    包含總數、容量、入住率、設施等統計資訊
    """
    # 權限檢查 - 只有管理員和管理者可以查看統計
    if UserRole(current_user.role) not in [UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="沒有權限查看統計資料"
        )
    
    return shelter_service.get_shelter_statistics(db=db)


@router.get("/my-shelters", response_model=ShelterListResponse)
def get_my_shelters(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="返回的記錄數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取我管理的避難所
    
    返回當前用戶管理的所有避難所
    """
    return shelter_service.get_shelter_by_manager(
        db=db,
        manager_id=str(current_user.id),
        skip=skip,
        limit=limit
    )


@router.get("/{shelter_id}", response_model=ShelterResponse)
def get_shelter(
    shelter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取單一避難所詳細資訊
    """
    shelter = shelter_service.get_shelter(
        db=db,
        shelter_id=shelter_id,
        user_id=str(current_user.id),
        user_role=UserRole(current_user.role)
    )
    
    if not shelter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="避難所不存在"
        )
    
    return shelter


@router.put("/{shelter_id}", response_model=ShelterResponse)
def update_shelter(
    shelter_id: str,
    shelter_update: ShelterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新避難所資訊
    
    - 管理員可以更新任何避難所
    - 避難所管理者只能更新自己管理的避難所
    """
    shelter = shelter_service.update_shelter(
        db=db,
        shelter_id=shelter_id,
        shelter_update=shelter_update,
        user_id=str(current_user.id),
        user_role=UserRole(current_user.role)
    )
    
    if not shelter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="避難所不存在"
        )
    
    return shelter


@router.delete("/{shelter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shelter(
    shelter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    刪除避難所
    
    - 只有管理員可以刪除避難所
    - 有人入住的避難所無法刪除
    """
    success = shelter_service.delete_shelter(
        db=db,
        shelter_id=shelter_id,
        user_id=str(current_user.id),
        user_role=UserRole(current_user.role)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="避難所不存在"
        )


@router.patch("/{shelter_id}/occupancy", response_model=ShelterResponse)
def update_shelter_occupancy(
    shelter_id: str,
    occupancy_update: ShelterOccupancyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新避難所入住人數
    
    - 管理員和避難所管理者可以更新入住人數
    - 系統會自動根據入住情況更新狀態
    """
    shelter = shelter_service.update_occupancy(
        db=db,
        shelter_id=shelter_id,
        occupancy_update=occupancy_update,
        user_id=str(current_user.id),
        user_role=UserRole(current_user.role)
    )
    
    if not shelter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="避難所不存在"
        )
    
    return shelter


@router.patch("/{shelter_id}/status", response_model=ShelterResponse)
def update_shelter_status(
    shelter_id: str,
    status_update: ShelterStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新避難所狀態
    
    - 管理員和避難所管理者可以更新狀態
    - 支援的狀態：active, full, closed, maintenance
    """
    shelter = shelter_service.update_status(
        db=db,
        shelter_id=shelter_id,
        status_update=status_update,
        user_id=str(current_user.id),
        user_role=UserRole(current_user.role)
    )
    
    if not shelter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="避難所不存在"
        )
    
    return shelter


@router.post("/bulk-update", response_model=BulkShelterResponse)
def bulk_update_shelters(
    bulk_data: BulkShelterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量更新避難所
    
    - 只有管理員可以批量更新
    - 支援批量更新入住人數、狀態、設施、聯絡資訊
    """
    return shelter_service.bulk_update_shelters(
        db=db,
        bulk_data=bulk_data,
        user_id=str(current_user.id),
        user_role=UserRole(current_user.role)
    )