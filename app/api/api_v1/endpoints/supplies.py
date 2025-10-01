"""
物資管理 API 端點
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.supply import (
    SupplyStationCreate, SupplyStationUpdate, SupplyStationResponse, 
    SupplyStationListResponse, SupplyStationSearchQuery,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    InventoryListResponse, BulkInventoryUpdate, BulkInventoryResponse,
    SupplyReservationCreate, SupplyReservationUpdate, SupplyReservationResponse,
    SupplyReservationListResponse, ReservationItemUpdate,
    SupplyMapResponse, SupplyStatistics
)
from app.services.supply_service import supply_service
from app.utils.constants import UserRole, ReservationStatus

router = APIRouter()


@router.post("/stations", response_model=SupplyStationResponse, status_code=status.HTTP_201_CREATED)
async def create_supply_station(
    station_data: SupplyStationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    建立新物資站點
    
    - **name**: 站點名稱
    - **address**: 站點地址
    - **location_data**: 地理位置資訊
    - **contact_info**: 聯絡資訊
    - **capacity_info**: 容量資訊（可選）
    """
    return supply_service.create_supply_station(
        db, station_data, str(current_user.id), current_user.role
    )


@router.get("/stations", response_model=SupplyStationListResponse)
async def get_supply_stations(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    name: Optional[str] = Query(None, description="名稱搜尋"),
    is_active: Optional[bool] = Query(None, description="啟用狀態篩選"),
    manager_id: Optional[str] = Query(None, description="管理者篩選"),
    location_radius: Optional[float] = Query(None, ge=0, description="位置半徑篩選(公里)"),
    center_lat: Optional[float] = Query(None, description="中心緯度"),
    center_lng: Optional[float] = Query(None, description="中心經度"),
    has_supply_type: Optional[str] = Query(None, description="包含特定物資類型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取物資站點列表
    
    支援多種篩選條件：
    - 名稱搜尋
    - 啟用狀態篩選
    - 管理者篩選
    - 地理位置篩選
    - 物資類型篩選
    """
    search_query = SupplyStationSearchQuery(
        name=name,
        is_active=is_active,
        manager_id=manager_id,
        location_radius=location_radius,
        center_lat=center_lat,
        center_lng=center_lng,
        has_supply_type=has_supply_type
    )
    
    return supply_service.get_supply_stations(
        db, skip, limit, search_query, str(current_user.id), current_user.role
    )


# 物資預訂相關端點
@router.post("/reservations", response_model=SupplyReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_supply_reservation(
    reservation_data: SupplyReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    建立物資預訂
    
    - **station_id**: 物資站點 ID
    - **task_id**: 關聯任務 ID（可選）
    - **need_id**: 關聯需求 ID（可選）
    - **reservation_items**: 預訂物資項目列表
    - **notes**: 預訂備註（可選）
    """
    return supply_service.create_supply_reservation(
        db, reservation_data, str(current_user.id), current_user.role
    )


@router.get("/reservations", response_model=SupplyReservationListResponse)
async def get_supply_reservations(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    station_id: Optional[str] = Query(None, description="物資站點篩選"),
    status: Optional[ReservationStatus] = Query(None, description="狀態篩選"),
    task_id: Optional[str] = Query(None, description="任務篩選"),
    need_id: Optional[str] = Query(None, description="需求篩選"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取物資預訂列表
    
    支援多種篩選條件：
    - 物資站點篩選
    - 狀態篩選
    - 任務篩選
    - 需求篩選
    """
    return supply_service.get_supply_reservations(
        db, skip, limit, str(current_user.id), current_user.role,
        station_id, status, task_id, need_id
    )


@router.get("/reservations/{reservation_id}", response_model=SupplyReservationResponse)
async def get_supply_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根據 ID 獲取單一物資預訂
    """
    reservation = supply_service.get_supply_reservation(
        db, reservation_id, str(current_user.id), current_user.role
    )
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資預訂不存在"
        )
    return reservation


@router.put("/reservations/{reservation_id}", response_model=SupplyReservationResponse)
async def update_supply_reservation(
    reservation_id: str,
    reservation_update: SupplyReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新物資預訂
    
    預訂者和站點管理者可以更新預訂
    """
    reservation = supply_service.update_supply_reservation(
        db, reservation_id, reservation_update, str(current_user.id), current_user.role
    )
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資預訂不存在"
        )
    return reservation


@router.post("/reservations/{reservation_id}/confirm", response_model=SupplyReservationResponse)
async def confirm_supply_reservation(
    reservation_id: str,
    confirmed_items: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    確認物資預訂（站點管理者操作）
    
    confirmed_items 格式：
    [
        {
            "supply_type": "water",
            "confirmed_quantity": 10,
            "notes": "確認備貨"
        }
    ]
    """
    reservation = supply_service.confirm_supply_reservation(
        db, reservation_id, confirmed_items, str(current_user.id), current_user.role
    )
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資預訂不存在"
        )
    return reservation


@router.put("/reservations/{reservation_id}/status", response_model=SupplyReservationResponse)
async def update_reservation_status(
    reservation_id: str,
    new_status: ReservationStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新預訂狀態
    
    支援的狀態轉換：
    - pending -> confirmed (站點管理者確認)
    - confirmed -> picked_up (志工領取)
    - picked_up -> delivered (配送完成)
    - 任何狀態 -> cancelled (取消)
    """
    reservation = supply_service.update_reservation_status(
        db, reservation_id, new_status, str(current_user.id), current_user.role
    )
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資預訂不存在"
        )
    return reservation


@router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_supply_reservation(
    reservation_id: str,
    reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    取消物資預訂
    
    預訂者和站點管理者可以取消預訂
    """
    success = supply_service.cancel_supply_reservation(
        db, reservation_id, str(current_user.id), current_user.role, reason
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資預訂不存在"
        )


@router.get("/stations/{station_id}/reservations", response_model=SupplyReservationListResponse)
async def get_station_reservations(
    station_id: str,
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    status: Optional[ReservationStatus] = Query(None, description="狀態篩選"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取特定站點的預訂列表（站點管理者專用）
    """
    return supply_service.get_station_reservations(
        db, station_id, str(current_user.id), current_user.role, status, skip, limit
    )


# 我的預訂相關端點
@router.get("/my-reservations", response_model=SupplyReservationListResponse)
async def get_my_reservations(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    status: Optional[ReservationStatus] = Query(None, description="狀態篩選"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前用戶的預訂列表
    """
    return supply_service.get_supply_reservations(
        db, skip, limit, str(current_user.id), current_user.role,
        status_filter=status
    )


@router.get("/stations/{station_id}", response_model=SupplyStationResponse)
async def get_supply_station(
    station_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根據 ID 獲取單一物資站點
    """
    station = supply_service.get_supply_station(
        db, station_id, str(current_user.id), current_user.role
    )
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資站點不存在"
        )
    return station


@router.put("/stations/{station_id}", response_model=SupplyStationResponse)
async def update_supply_station(
    station_id: str,
    station_update: SupplyStationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新物資站點資訊
    
    只有站點管理者和管理員可以更新站點
    """
    station = supply_service.update_supply_station(
        db, station_id, station_update, str(current_user.id), current_user.role
    )
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資站點不存在"
        )
    return station


@router.delete("/stations/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supply_station(
    station_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    刪除物資站點
    
    只有站點管理者和管理員可以刪除站點
    有進行中預訂的站點無法刪除
    """
    success = supply_service.delete_supply_station(
        db, station_id, str(current_user.id), current_user.role
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="物資站點不存在"
        )


# 庫存管理相關端點
@router.post("/inventory", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item_data: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    建立庫存物資
    
    - **station_id**: 物資站點 ID
    - **supply_type**: 物資類型
    - **description**: 物資描述（可選）
    - **is_available**: 是否可用
    - **notes**: 備註說明（可選）
    """
    return supply_service.create_inventory_item(
        db, item_data, str(current_user.id), current_user.role
    )


@router.get("/stations/{station_id}/inventory", response_model=InventoryListResponse)
async def get_station_inventory(
    station_id: str,
    include_unavailable: bool = Query(False, description="是否包含不可用物資"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取站點庫存列表
    """
    return supply_service.get_station_inventory(
        db, station_id, str(current_user.id), current_user.role, include_unavailable
    )


@router.put("/inventory/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: str,
    item_update: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新庫存物資
    
    只有站點管理者和管理員可以更新庫存
    """
    item = supply_service.update_inventory_item(
        db, item_id, item_update, str(current_user.id), current_user.role
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="庫存物資不存在"
        )
    return item


@router.delete("/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    刪除庫存物資
    
    只有站點管理者和管理員可以刪除庫存
    有進行中預訂的物資無法刪除
    """
    success = supply_service.delete_inventory_item(
        db, item_id, str(current_user.id), current_user.role
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="庫存物資不存在"
        )


@router.post("/inventory/bulk-update", response_model=BulkInventoryResponse)
async def bulk_update_inventory(
    bulk_data: BulkInventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量更新庫存
    
    - **station_id**: 物資站點 ID
    - **items**: 庫存項目列表
    - **replace_existing**: 是否替換現有庫存
    """
    return supply_service.bulk_update_inventory(
        db, bulk_data, str(current_user.id), current_user.role
    )


# 物資地圖相關端點
@router.get("/map", response_model=SupplyMapResponse)
async def get_supply_map(
    center_lat: Optional[float] = Query(None, description="中心緯度"),
    center_lng: Optional[float] = Query(None, description="中心經度"),
    radius: Optional[float] = Query(None, ge=0, description="搜尋半徑(公里)"),
    supply_type_filter: Optional[str] = Query(None, description="物資類型篩選"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取物資地圖資料
    
    顯示所有啟用的物資站點及其可用物資
    支援地理位置和物資類型篩選
    """
    return supply_service.get_supply_map(
        db, center_lat, center_lng, radius, supply_type_filter
    )


# 統計相關端點
@router.get("/statistics", response_model=SupplyStatistics)
async def get_supply_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取物資統計資料（管理員專用）
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以查看統計資料"
        )
    
    return supply_service.get_supply_statistics(db)


# 我的站點相關端點
@router.get("/my-stations", response_model=SupplyStationListResponse)
async def get_my_supply_stations(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前用戶管理的物資站點列表
    """
    search_query = SupplyStationSearchQuery(manager_id=str(current_user.id))
    
    return supply_service.get_supply_stations(
        db, skip, limit, search_query, str(current_user.id), current_user.role
    )


@router.get("/active-stations", response_model=SupplyStationListResponse)
async def get_active_supply_stations(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    location_radius: Optional[float] = Query(None, ge=0, description="位置半徑篩選(公里)"),
    center_lat: Optional[float] = Query(None, description="中心緯度"),
    center_lng: Optional[float] = Query(None, description="中心經度"),
    has_supply_type: Optional[str] = Query(None, description="包含特定物資類型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取啟用的物資站點列表
    
    所有用戶都可以查看啟用的物資站點
    """
    search_query = SupplyStationSearchQuery(
        is_active=True,
        location_radius=location_radius,
        center_lat=center_lat,
        center_lng=center_lng,
        has_supply_type=has_supply_type
    )
    
    return supply_service.get_supply_stations(
        db, skip, limit, search_query, str(current_user.id), current_user.role
    )