"""
物資管理服務層
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.crud.supply import supply_crud
from app.services.notification_service import notification_service
from app.schemas.supply import (
    SupplyStationCreate, SupplyStationUpdate, SupplyStationResponse, 
    SupplyStationListResponse, SupplyStationSearchQuery,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    InventoryListResponse, BulkInventoryUpdate, BulkInventoryResponse,
    SupplyReservationCreate, SupplyReservationUpdate, SupplyReservationResponse,
    SupplyReservationListResponse, ReservationItemUpdate,
    SupplyMapResponse, SupplyStatistics
)
from app.utils.constants import UserRole, ReservationStatus


class SupplyService:
    """物資管理服務類"""
    
    def create_supply_station(
        self, 
        db: Session, 
        station_data: SupplyStationCreate, 
        manager_id: str,
        manager_role: UserRole
    ) -> SupplyStationResponse:
        """建立物資站點"""
        # 權限檢查
        if manager_role not in [UserRole.ADMIN, UserRole.SUPPLY_MANAGER, UserRole.OFFICIAL_ORG]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限建立物資站點"
            )
        
        # 建立站點
        station = supply_crud.create_supply_station(db, station_data, manager_id)
        
        # 轉換為回應模型
        return self._convert_station_to_response(station, manager_id, manager_role)
    
    def get_supply_station(
        self, 
        db: Session, 
        station_id: str,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyStationResponse]:
        """獲取單一物資站點"""
        station = supply_crud.get_supply_station(db, station_id)
        if not station:
            return None
        
        # 權限檢查 - 非啟用站點只有管理者和管理員可以查看
        if not station.is_active and user_role != UserRole.ADMIN and str(station.manager_id) != user_id:
            return None
        
        return self._convert_station_to_response(station, user_id, user_role)
    
    def get_supply_stations(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search_query: Optional[SupplyStationSearchQuery] = None,
        user_id: str = None,
        user_role: UserRole = None
    ) -> SupplyStationListResponse:
        """獲取物資站點列表"""
        stations, total = supply_crud.get_supply_stations(
            db, skip, limit, search_query, user_role, user_id
        )
        
        # 轉換為回應模型
        station_responses = [
            self._convert_station_to_response(station, user_id, user_role)
            for station in stations
        ]
        
        return SupplyStationListResponse(
            stations=station_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    def update_supply_station(
        self, 
        db: Session, 
        station_id: str, 
        station_update: SupplyStationUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyStationResponse]:
        """更新物資站點"""
        station = supply_crud.update_supply_station(
            db, station_id, station_update, user_id, user_role
        )
        if not station:
            return None
        
        return self._convert_station_to_response(station, user_id, user_role)
    
    def delete_supply_station(
        self, 
        db: Session, 
        station_id: str,
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """刪除物資站點"""
        return supply_crud.delete_supply_station(db, station_id, user_id, user_role)
    
    # 庫存管理相關方法
    def create_inventory_item(
        self, 
        db: Session, 
        item_data: InventoryItemCreate,
        user_id: str,
        user_role: UserRole
    ) -> InventoryItemResponse:
        """建立庫存物資"""
        item = supply_crud.create_inventory_item(db, item_data, user_id, user_role)
        return self._convert_inventory_to_response(item, user_id, user_role)
    
    def get_station_inventory(
        self, 
        db: Session, 
        station_id: str,
        user_id: str,
        user_role: UserRole,
        include_unavailable: bool = False
    ) -> InventoryListResponse:
        """獲取站點庫存列表"""
        # 權限檢查
        station = supply_crud.get_supply_station(db, station_id)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物資站點不存在"
            )
        
        # 非啟用站點只有管理者和管理員可以查看
        if not station.is_active and user_role != UserRole.ADMIN and str(station.manager_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限查看此站點庫存"
            )
        
        items = supply_crud.get_station_inventory(db, station_id, include_unavailable)
        
        # 轉換為回應模型
        item_responses = [
            self._convert_inventory_to_response(item, user_id, user_role)
            for item in items
        ]
        
        return InventoryListResponse(
            items=item_responses,
            total=len(item_responses),
            skip=0,
            limit=len(item_responses)
        )
    
    def update_inventory_item(
        self, 
        db: Session, 
        item_id: str, 
        item_update: InventoryItemUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[InventoryItemResponse]:
        """更新庫存物資"""
        item = supply_crud.update_inventory_item(
            db, item_id, item_update, user_id, user_role
        )
        if not item:
            return None
        
        return self._convert_inventory_to_response(item, user_id, user_role)
    
    def delete_inventory_item(
        self, 
        db: Session, 
        item_id: str,
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """刪除庫存物資"""
        return supply_crud.delete_inventory_item(db, item_id, user_id, user_role)
    
    def bulk_update_inventory(
        self, 
        db: Session, 
        bulk_data: BulkInventoryUpdate,
        user_id: str,
        user_role: UserRole
    ) -> BulkInventoryResponse:
        """批量更新庫存"""
        result = supply_crud.bulk_update_inventory(db, bulk_data, user_id, user_role)
        
        return BulkInventoryResponse(
            success=result["success"],
            created_count=result["created_count"],
            updated_count=result["updated_count"],
            deleted_count=result["deleted_count"],
            errors=result["errors"]
        )
    
    # 物資地圖相關方法
    def get_supply_map(
        self, 
        db: Session,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        radius: Optional[float] = None,
        supply_type_filter: Optional[str] = None
    ) -> SupplyMapResponse:
        """獲取物資地圖資料"""
        map_data = supply_crud.get_supply_map(
            db, center_lat, center_lng, radius, supply_type_filter
        )
        
        return SupplyMapResponse(
            stations=map_data["stations"],
            center=map_data["center"],
            bounds=map_data["bounds"]
        )
    
    # 統計相關方法
    def get_supply_statistics(self, db: Session) -> SupplyStatistics:
        """獲取物資統計資料"""
        stats = supply_crud.get_supply_statistics(db)
        
        return SupplyStatistics(
            total_stations=stats["total_stations"],
            active_stations=stats["active_stations"],
            total_supply_types=stats["total_supply_types"],
            available_supply_types=stats["available_supply_types"],
            pending_reservations=stats["pending_reservations"],
            completed_reservations=stats["completed_reservations"],
            stations_by_manager_role=stats["stations_by_manager_role"],
            supplies_by_type=stats["supplies_by_type"]
        )
    
    # 物資預訂相關方法
    def create_supply_reservation(
        self, 
        db: Session, 
        reservation_data: SupplyReservationCreate,
        user_id: str,
        user_role: UserRole
    ) -> SupplyReservationResponse:
        """建立物資預訂"""
        reservation = supply_crud.create_supply_reservation(
            db, reservation_data, user_id, user_role
        )
        
        # 發送通知給站點管理者
        try:
            notification_service.send_supply_reservation_notification(
                db=db,
                reservation_id=str(reservation.id),
                station_manager_id=str(reservation.station.manager_id),
                user_name=reservation.user.name,
                station_name=reservation.station.name,
                task_title=reservation.task.title if reservation.task else None
            )
        except Exception as e:
            # 通知發送失敗不應該影響預訂創建
            print(f"Failed to send reservation notification: {e}")
        
        return self._convert_reservation_to_response(reservation, user_id, user_role)
    
    def get_supply_reservation(
        self, 
        db: Session, 
        reservation_id: str,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyReservationResponse]:
        """獲取單一物資預訂"""
        reservation = supply_crud.get_supply_reservation(db, reservation_id)
        if not reservation:
            return None
        
        # 權限檢查
        can_view = (
            user_role == UserRole.ADMIN or
            str(reservation.user_id) == user_id or  # 預訂者
            str(reservation.station.manager_id) == user_id  # 站點管理者
        )
        
        if not can_view:
            return None
        
        return self._convert_reservation_to_response(reservation, user_id, user_role)
    
    def get_supply_reservations(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: str = None,
        user_role: UserRole = None,
        station_id: Optional[str] = None,
        status_filter: Optional[ReservationStatus] = None,
        task_id: Optional[str] = None,
        need_id: Optional[str] = None
    ) -> SupplyReservationListResponse:
        """獲取物資預訂列表"""
        reservations, total = supply_crud.get_supply_reservations(
            db, skip, limit, user_id, user_role, station_id, status_filter, task_id, need_id
        )
        
        # 轉換為回應模型
        reservation_responses = [
            self._convert_reservation_to_response(reservation, user_id, user_role)
            for reservation in reservations
        ]
        
        return SupplyReservationListResponse(
            reservations=reservation_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    def update_supply_reservation(
        self, 
        db: Session, 
        reservation_id: str, 
        reservation_update: SupplyReservationUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyReservationResponse]:
        """更新物資預訂"""
        reservation = supply_crud.update_supply_reservation(
            db, reservation_id, reservation_update, user_id, user_role
        )
        if not reservation:
            return None
        
        return self._convert_reservation_to_response(reservation, user_id, user_role)
    
    def confirm_supply_reservation(
        self, 
        db: Session, 
        reservation_id: str,
        confirmed_items: List[Dict[str, Any]],
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyReservationResponse]:
        """確認物資預訂（站點管理者操作）"""
        reservation = supply_crud.confirm_supply_reservation(
            db, reservation_id, confirmed_items, user_id, user_role
        )
        if not reservation:
            return None
        
        # 發送確認通知給預訂者
        try:
            notification_service.send_reservation_confirmed_notification(
                db=db,
                reservation_id=str(reservation.id),
                user_id=str(reservation.user_id),
                station_name=reservation.station.name
            )
        except Exception as e:
            print(f"Failed to send confirmation notification: {e}")
        
        return self._convert_reservation_to_response(reservation, user_id, user_role)
    
    def update_reservation_status(
        self, 
        db: Session, 
        reservation_id: str,
        new_status: ReservationStatus,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyReservationResponse]:
        """更新預訂狀態"""
        reservation = supply_crud.update_reservation_status(
            db, reservation_id, new_status, user_id, user_role
        )
        if not reservation:
            return None
        
        # 發送狀態更新通知
        try:
            notification_service.send_reservation_status_notification(
                db=db,
                reservation_id=str(reservation.id),
                user_id=str(reservation.user_id),
                status=new_status.value,
                station_name=reservation.station.name
            )
        except Exception as e:
            print(f"Failed to send status update notification: {e}")
        
        return self._convert_reservation_to_response(reservation, user_id, user_role)
    
    def cancel_supply_reservation(
        self, 
        db: Session, 
        reservation_id: str,
        user_id: str,
        user_role: UserRole,
        reason: Optional[str] = None
    ) -> bool:
        """取消物資預訂"""
        return supply_crud.cancel_supply_reservation(
            db, reservation_id, user_id, user_role, reason
        )
    
    def get_station_reservations(
        self, 
        db: Session, 
        station_id: str,
        user_id: str,
        user_role: UserRole,
        status_filter: Optional[ReservationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> SupplyReservationListResponse:
        """獲取特定站點的預訂列表"""
        # 權限檢查
        station = supply_crud.get_supply_station(db, station_id)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物資站點不存在"
            )
        
        if (user_role != UserRole.ADMIN and 
            str(station.manager_id) != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限查看此站點的預訂"
            )
        
        reservations, total = supply_crud.get_station_reservations(
            db, station_id, status_filter, skip, limit
        )
        
        # 轉換為回應模型
        reservation_responses = [
            self._convert_reservation_to_response(reservation, user_id, user_role)
            for reservation in reservations
        ]
        
        return SupplyReservationListResponse(
            reservations=reservation_responses,
            total=total,
            skip=skip,
            limit=limit
        )
    
    # 私有輔助方法
    def _convert_station_to_response(
        self, 
        station, 
        user_id: str, 
        user_role: UserRole
    ) -> SupplyStationResponse:
        """轉換站點模型為回應模型"""
        # 計算庫存相關資訊
        inventory_count = len([item for item in station.inventory_items if item.is_available])
        available_supplies = [
            item.supply_type for item in station.inventory_items 
            if item.is_available
        ]
        
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or 
            str(station.manager_id) == user_id
        )
        
        return SupplyStationResponse(
            id=str(station.id),
            manager_id=str(station.manager_id),
            name=station.name,
            address=station.address,
            location_data=station.location_data,
            contact_info=station.contact_info,
            capacity_info=station.capacity_info,
            is_active=station.is_active,
            created_at=station.created_at,
            updated_at=station.updated_at,
            manager_name=station.manager.name if station.manager else None,
            manager_role=UserRole(station.manager.role) if station.manager else None,
            inventory_count=inventory_count,
            available_supplies=available_supplies,
            can_edit=can_edit
        )
    
    def _convert_inventory_to_response(
        self, 
        item, 
        user_id: str, 
        user_role: UserRole
    ) -> InventoryItemResponse:
        """轉換庫存模型為回應模型"""
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or 
            str(item.station.manager_id) == user_id
        )
        
        return InventoryItemResponse(
            id=str(item.id),
            station_id=str(item.station_id),
            supply_type=item.supply_type,
            description=item.description,
            is_available=item.is_available,
            notes=item.notes,
            updated_at=item.updated_at,
            station_name=item.station.name if item.station else None,
            supply_type_display=(
                item.supply_type_rel.display_name 
                if item.supply_type_rel else item.supply_type
            ),
            can_edit=can_edit
        )
    
    def _convert_reservation_to_response(
        self, 
        reservation, 
        user_id: str, 
        user_role: UserRole
    ) -> SupplyReservationResponse:
        """轉換預訂模型為回應模型"""
        from app.schemas.supply import ReservationItemResponse
        
        # 轉換預訂物資項目
        reservation_items = []
        for item in reservation.reservation_items:
            reservation_items.append(ReservationItemResponse(
                id=str(item.id),
                reservation_id=str(item.reservation_id),
                supply_type=item.supply_type,
                requested_quantity=item.requested_quantity,
                confirmed_quantity=item.confirmed_quantity,
                notes=item.notes,
                supply_type_display=(
                    item.supply_type_rel.display_name 
                    if item.supply_type_rel else item.supply_type
                )
            ))
        
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or 
            str(reservation.user_id) == user_id
        )
        
        can_confirm = (
            user_role == UserRole.ADMIN or 
            str(reservation.station.manager_id) == user_id
        )
        
        return SupplyReservationResponse(
            id=str(reservation.id),
            user_id=str(reservation.user_id),
            station_id=str(reservation.station_id),
            task_id=str(reservation.task_id) if reservation.task_id else None,
            need_id=str(reservation.need_id) if reservation.need_id else None,
            status=ReservationStatus(reservation.status),
            reserved_at=reservation.reserved_at,
            confirmed_at=reservation.confirmed_at,
            picked_up_at=reservation.picked_up_at,
            delivered_at=reservation.delivered_at,
            notes=reservation.notes,
            user_name=reservation.user.name if reservation.user else None,
            station_name=reservation.station.name if reservation.station else None,
            task_title=reservation.task.title if reservation.task else None,
            need_title=reservation.need.title if reservation.need else None,
            reservation_items=reservation_items,
            can_edit=can_edit,
            can_confirm=can_confirm
        )


# 建立全域實例
supply_service = SupplyService()