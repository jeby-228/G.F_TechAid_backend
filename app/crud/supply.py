"""
物資管理 CRUD 操作
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text
from fastapi import HTTPException, status

from app.models.supply import SupplyStation, InventoryItem, SupplyReservation, ReservationItem, SupplyType
from app.models.user import User
from app.models.task import Task
from app.models.need import Need
from app.schemas.supply import (
    SupplyStationCreate, SupplyStationUpdate, SupplyStationSearchQuery,
    InventoryItemCreate, InventoryItemUpdate, BulkInventoryUpdate,
    SupplyReservationCreate, SupplyReservationUpdate
)
from app.utils.constants import UserRole, ReservationStatus
import uuid


class SupplyCRUD:
    """物資管理 CRUD 操作類"""
    
    # 物資站點相關操作
    def create_supply_station(
        self, 
        db: Session, 
        station_data: SupplyStationCreate, 
        manager_id: str
    ) -> SupplyStation:
        """建立新物資站點"""
        # 建立物資站點物件
        db_station = SupplyStation(
            id=uuid.uuid4(),
            manager_id=uuid.UUID(manager_id),
            name=station_data.name,
            address=station_data.address,
            location_data=station_data.location_data.dict(),
            contact_info=station_data.contact_info.dict(),
            capacity_info=station_data.capacity_info,
            is_active=True
        )
        
        db.add(db_station)
        db.commit()
        db.refresh(db_station)
        return db_station
    
    def get_supply_station(self, db: Session, station_id: str) -> Optional[SupplyStation]:
        """根據 ID 獲取物資站點"""
        return db.query(SupplyStation).options(
            joinedload(SupplyStation.manager),
            joinedload(SupplyStation.inventory_items).joinedload(InventoryItem.supply_type_rel),
            joinedload(SupplyStation.supply_reservations)
        ).filter(SupplyStation.id == uuid.UUID(station_id)).first()
    
    def get_supply_stations(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search_query: Optional[SupplyStationSearchQuery] = None,
        user_role: Optional[UserRole] = None,
        user_id: Optional[str] = None
    ) -> Tuple[List[SupplyStation], int]:
        """獲取物資站點列表"""
        query = db.query(SupplyStation).options(
            joinedload(SupplyStation.manager),
            joinedload(SupplyStation.inventory_items).joinedload(InventoryItem.supply_type_rel)
        )
        
        # 基於用戶角色的權限篩選
        if user_role and user_role != UserRole.ADMIN:
            if user_role == UserRole.SUPPLY_MANAGER:
                # 物資管理者只能看到自己管理的站點和啟用的站點
                query = query.filter(
                    or_(
                        SupplyStation.manager_id == uuid.UUID(user_id),
                        SupplyStation.is_active == True
                    )
                )
            else:
                # 其他角色只能看到啟用的站點
                query = query.filter(SupplyStation.is_active == True)
        
        # 搜尋條件
        if search_query:
            if search_query.name:
                query = query.filter(SupplyStation.name.ilike(f"%{search_query.name}%"))
            if search_query.is_active is not None:
                query = query.filter(SupplyStation.is_active == search_query.is_active)
            if search_query.manager_id:
                query = query.filter(SupplyStation.manager_id == uuid.UUID(search_query.manager_id))
            
            # 地理位置篩選
            if (search_query.location_radius and 
                search_query.center_lat is not None and 
                search_query.center_lng is not None):
                try:
                    # PostgreSQL 版本
                    distance_query = text("""
                        (6371 * acos(cos(radians(:lat)) * cos(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))) 
                        * cos(radians(CAST(location_data->>'coordinates'->>'lng' AS FLOAT)) - radians(:lng)) 
                        + sin(radians(:lat)) * sin(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))))) <= :radius
                    """)
                    query = query.filter(distance_query.params(
                        lat=search_query.center_lat,
                        lng=search_query.center_lng,
                        radius=search_query.location_radius
                    ))
                except Exception:
                    # SQLite 簡化版本
                    lat_range = search_query.location_radius / 111.0
                    lng_range = search_query.location_radius / (111.0 * func.cos(func.radians(search_query.center_lat)))
                    
                    query = query.filter(
                        and_(
                            func.json_extract(SupplyStation.location_data, '$.coordinates.lat').between(
                                search_query.center_lat - lat_range,
                                search_query.center_lat + lat_range
                            ),
                            func.json_extract(SupplyStation.location_data, '$.coordinates.lng').between(
                                search_query.center_lng - lng_range,
                                search_query.center_lng + lng_range
                            )
                        )
                    )
            
            # 篩選包含特定物資類型的站點
            if search_query.has_supply_type:
                query = query.join(InventoryItem).filter(
                    and_(
                        InventoryItem.supply_type == search_query.has_supply_type,
                        InventoryItem.is_available == True
                    )
                )
        
        # 獲取總數
        total = query.count()
        
        # 排序和分頁
        stations = query.order_by(
            SupplyStation.is_active.desc(),
            SupplyStation.name.asc()
        ).offset(skip).limit(limit).all()
        
        return stations, total
    
    def update_supply_station(
        self, 
        db: Session, 
        station_id: str, 
        station_update: SupplyStationUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyStation]:
        """更新物資站點"""
        station = self.get_supply_station(db, station_id)
        if not station:
            return None
        
        # 權限檢查
        if user_role != UserRole.ADMIN and str(station.manager_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限編輯此物資站點"
            )
        
        # 更新欄位
        update_data = station_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "location_data" and value:
                if hasattr(value, 'dict'):
                    setattr(station, field, value.dict())
                else:
                    setattr(station, field, value)
            elif field == "contact_info" and value:
                if hasattr(value, 'dict'):
                    setattr(station, field, value.dict())
                else:
                    setattr(station, field, value)
            else:
                setattr(station, field, value)
        
        station.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(station)
        return station
    
    def delete_supply_station(
        self, 
        db: Session, 
        station_id: str,
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """刪除物資站點"""
        station = self.get_supply_station(db, station_id)
        if not station:
            return False
        
        # 權限檢查
        if user_role != UserRole.ADMIN and str(station.manager_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限刪除此物資站點"
            )
        
        # 檢查是否有進行中的預訂
        active_reservations = db.query(SupplyReservation).filter(
            and_(
                SupplyReservation.station_id == uuid.UUID(station_id),
                SupplyReservation.status.in_([
                    ReservationStatus.PENDING.value,
                    ReservationStatus.CONFIRMED.value
                ])
            )
        ).count()
        
        if active_reservations > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="站點有進行中的預訂，無法刪除"
            )
        
        db.delete(station)
        db.commit()
        return True
    
    # 庫存管理相關操作
    def create_inventory_item(
        self, 
        db: Session, 
        item_data: InventoryItemCreate,
        user_id: str,
        user_role: UserRole
    ) -> InventoryItem:
        """建立庫存物資"""
        # 權限檢查
        station = self.get_supply_station(db, item_data.station_id)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物資站點不存在"
            )
        
        if user_role != UserRole.ADMIN and str(station.manager_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限管理此站點的庫存"
            )
        
        # 檢查是否已存在相同物資類型
        existing_item = db.query(InventoryItem).filter(
            and_(
                InventoryItem.station_id == uuid.UUID(item_data.station_id),
                InventoryItem.supply_type == item_data.supply_type
            )
        ).first()
        
        if existing_item:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="此站點已存在相同類型的物資"
            )
        
        # 建立庫存物資
        db_item = InventoryItem(
            id=uuid.uuid4(),
            station_id=uuid.UUID(item_data.station_id),
            supply_type=item_data.supply_type,
            description=item_data.description,
            is_available=item_data.is_available,
            notes=item_data.notes
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    
    def get_inventory_item(self, db: Session, item_id: str) -> Optional[InventoryItem]:
        """根據 ID 獲取庫存物資"""
        return db.query(InventoryItem).options(
            joinedload(InventoryItem.station),
            joinedload(InventoryItem.supply_type_rel)
        ).filter(InventoryItem.id == uuid.UUID(item_id)).first()
    
    def get_station_inventory(
        self, 
        db: Session, 
        station_id: str,
        include_unavailable: bool = False
    ) -> List[InventoryItem]:
        """獲取站點庫存列表"""
        query = db.query(InventoryItem).options(
            joinedload(InventoryItem.supply_type_rel)
        ).filter(InventoryItem.station_id == uuid.UUID(station_id))
        
        if not include_unavailable:
            query = query.filter(InventoryItem.is_available == True)
        
        return query.order_by(InventoryItem.supply_type).all()
    
    def update_inventory_item(
        self, 
        db: Session, 
        item_id: str, 
        item_update: InventoryItemUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[InventoryItem]:
        """更新庫存物資"""
        item = self.get_inventory_item(db, item_id)
        if not item:
            return None
        
        # 權限檢查
        if user_role != UserRole.ADMIN and str(item.station.manager_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限編輯此庫存物資"
            )
        
        # 更新欄位
        update_data = item_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return item
    
    def delete_inventory_item(
        self, 
        db: Session, 
        item_id: str,
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """刪除庫存物資"""
        item = self.get_inventory_item(db, item_id)
        if not item:
            return False
        
        # 權限檢查
        if user_role != UserRole.ADMIN and str(item.station.manager_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限刪除此庫存物資"
            )
        
        # 檢查是否有進行中的預訂
        active_reservations = db.query(ReservationItem).join(SupplyReservation).filter(
            and_(
                ReservationItem.supply_type == item.supply_type,
                SupplyReservation.station_id == item.station_id,
                SupplyReservation.status.in_([
                    ReservationStatus.PENDING.value,
                    ReservationStatus.CONFIRMED.value
                ])
            )
        ).count()
        
        if active_reservations > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此物資有進行中的預訂，無法刪除"
            )
        
        db.delete(item)
        db.commit()
        return True
    
    def bulk_update_inventory(
        self, 
        db: Session, 
        bulk_data: BulkInventoryUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Dict[str, Any]:
        """批量更新庫存"""
        # 權限檢查
        station = self.get_supply_station(db, bulk_data.station_id)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物資站點不存在"
            )
        
        if user_role != UserRole.ADMIN and str(station.manager_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限管理此站點的庫存"
            )
        
        result = {
            "success": True,
            "created_count": 0,
            "updated_count": 0,
            "deleted_count": 0,
            "errors": []
        }
        
        try:
            # 如果要替換現有庫存，先刪除所有現有項目
            if bulk_data.replace_existing:
                deleted_count = db.query(InventoryItem).filter(
                    InventoryItem.station_id == uuid.UUID(bulk_data.station_id)
                ).delete()
                result["deleted_count"] = deleted_count
            
            # 處理新的庫存項目
            for item_data in bulk_data.items:
                try:
                    # 檢查是否已存在
                    existing_item = db.query(InventoryItem).filter(
                        and_(
                            InventoryItem.station_id == uuid.UUID(bulk_data.station_id),
                            InventoryItem.supply_type == item_data.supply_type
                        )
                    ).first()
                    
                    if existing_item and not bulk_data.replace_existing:
                        # 更新現有項目
                        existing_item.description = item_data.description
                        existing_item.is_available = item_data.is_available
                        existing_item.notes = item_data.notes
                        existing_item.updated_at = datetime.utcnow()
                        result["updated_count"] += 1
                    else:
                        # 建立新項目
                        new_item = InventoryItem(
                            id=uuid.uuid4(),
                            station_id=uuid.UUID(bulk_data.station_id),
                            supply_type=item_data.supply_type,
                            description=item_data.description,
                            is_available=item_data.is_available,
                            notes=item_data.notes
                        )
                        db.add(new_item)
                        result["created_count"] += 1
                        
                except Exception as e:
                    result["errors"].append(f"處理物資 {item_data.supply_type} 時發生錯誤: {str(e)}")
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            result["success"] = False
            result["errors"].append(f"批量更新失敗: {str(e)}")
        
        return result
    
    # 物資地圖相關操作
    def get_supply_map(
        self, 
        db: Session,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        radius: Optional[float] = None,
        supply_type_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """獲取物資地圖資料"""
        query = db.query(SupplyStation).options(
            joinedload(SupplyStation.inventory_items).joinedload(InventoryItem.supply_type_rel)
        ).filter(SupplyStation.is_active == True)
        
        # 地理位置篩選
        if center_lat is not None and center_lng is not None and radius:
            try:
                # PostgreSQL 版本
                distance_query = text("""
                    (6371 * acos(cos(radians(:lat)) * cos(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))) 
                    * cos(radians(CAST(location_data->>'coordinates'->>'lng' AS FLOAT)) - radians(:lng)) 
                    + sin(radians(:lat)) * sin(radians(CAST(location_data->>'coordinates'->>'lat' AS FLOAT))))) <= :radius
                """)
                query = query.filter(distance_query.params(
                    lat=center_lat,
                    lng=center_lng,
                    radius=radius
                ))
            except Exception:
                # SQLite 簡化版本
                lat_range = radius / 111.0
                lng_range = radius / (111.0 * func.cos(func.radians(center_lat)))
                
                query = query.filter(
                    and_(
                        func.json_extract(SupplyStation.location_data, '$.coordinates.lat').between(
                            center_lat - lat_range,
                            center_lat + lat_range
                        ),
                        func.json_extract(SupplyStation.location_data, '$.coordinates.lng').between(
                            center_lng - lng_range,
                            center_lng + lng_range
                        )
                    )
                )
        
        # 物資類型篩選
        if supply_type_filter:
            query = query.join(InventoryItem).filter(
                and_(
                    InventoryItem.supply_type == supply_type_filter,
                    InventoryItem.is_available == True
                )
            )
        
        stations = query.all()
        
        # 準備地圖資料
        map_stations = []
        for station in stations:
            available_supplies = []
            for item in station.inventory_items:
                if item.is_available:
                    available_supplies.append({
                        "type": item.supply_type,
                        "display_name": item.supply_type_rel.display_name if item.supply_type_rel else item.supply_type,
                        "description": item.description,
                        "notes": item.notes
                    })
            
            map_stations.append({
                "id": str(station.id),
                "name": station.name,
                "address": station.address,
                "coordinates": station.location_data.get("coordinates", {}),
                "contact_info": station.contact_info,
                "available_supplies": available_supplies,
                "is_active": station.is_active
            })
        
        # 計算地圖中心點和邊界
        from app.utils.constants import GUANGFU_COORDINATES
        
        if center_lat and center_lng:
            map_center = {"lat": center_lat, "lng": center_lng}
        else:
            map_center = GUANGFU_COORDINATES["center"]
        
        map_bounds = GUANGFU_COORDINATES["bounds"]
        
        return {
            "stations": map_stations,
            "center": map_center,
            "bounds": map_bounds
        }
    
    # 統計相關操作
    def get_supply_statistics(self, db: Session) -> Dict[str, Any]:
        """獲取物資統計資料"""
        # 總站點數和啟用站點數
        total_stations = db.query(SupplyStation).count()
        active_stations = db.query(SupplyStation).filter(SupplyStation.is_active == True).count()
        
        # 總物資類型數和可用物資類型數
        total_supply_types = db.query(InventoryItem.supply_type).distinct().count()
        available_supply_types = db.query(InventoryItem.supply_type).filter(
            InventoryItem.is_available == True
        ).distinct().count()
        
        # 預訂統計
        pending_reservations = db.query(SupplyReservation).filter(
            SupplyReservation.status == ReservationStatus.PENDING.value
        ).count()
        completed_reservations = db.query(SupplyReservation).filter(
            SupplyReservation.status == ReservationStatus.DELIVERED.value
        ).count()
        
        # 各角色管理的站點數
        manager_role_stats = db.query(
            User.role,
            func.count(SupplyStation.id)
        ).join(SupplyStation, User.id == SupplyStation.manager_id).group_by(User.role).all()
        stations_by_manager_role = {role: count for role, count in manager_role_stats}
        
        # 各類型物資數量
        supply_type_stats = db.query(
            InventoryItem.supply_type,
            func.count(InventoryItem.id)
        ).filter(InventoryItem.is_available == True).group_by(InventoryItem.supply_type).all()
        supplies_by_type = {supply_type: count for supply_type, count in supply_type_stats}
        
        return {
            "total_stations": total_stations,
            "active_stations": active_stations,
            "total_supply_types": total_supply_types,
            "available_supply_types": available_supply_types,
            "pending_reservations": pending_reservations,
            "completed_reservations": completed_reservations,
            "stations_by_manager_role": stations_by_manager_role,
            "supplies_by_type": supplies_by_type
        }
    
    # 物資預訂相關操作
    def create_supply_reservation(
        self, 
        db: Session, 
        reservation_data: SupplyReservationCreate,
        user_id: str,
        user_role: UserRole
    ) -> SupplyReservation:
        """建立物資預訂"""
        # 權限檢查 - 只有志工、組織和管理員可以預訂物資
        if user_role not in [UserRole.VOLUNTEER, UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG, 
                            UserRole.SUPPLY_MANAGER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限預訂物資"
            )
        
        # 檢查物資站點是否存在且啟用
        station = self.get_supply_station(db, reservation_data.station_id)
        if not station or not station.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物資站點不存在或未啟用"
            )
        
        # 檢查關聯的任務或需求是否存在
        if reservation_data.task_id:
            task = db.query(Task).filter(Task.id == uuid.UUID(reservation_data.task_id)).first()
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="關聯的任務不存在"
                )
        
        if reservation_data.need_id:
            need = db.query(Need).filter(Need.id == uuid.UUID(reservation_data.need_id)).first()
            if not need:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="關聯的需求不存在"
                )
        
        # 檢查預訂的物資是否可用
        for item_data in reservation_data.reservation_items:
            inventory_item = db.query(InventoryItem).filter(
                and_(
                    InventoryItem.station_id == uuid.UUID(reservation_data.station_id),
                    InventoryItem.supply_type == item_data.supply_type,
                    InventoryItem.is_available == True
                )
            ).first()
            
            if not inventory_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"物資類型 {item_data.supply_type} 在此站點不可用"
                )
        
        # 建立預訂記錄
        db_reservation = SupplyReservation(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            station_id=uuid.UUID(reservation_data.station_id),
            task_id=uuid.UUID(reservation_data.task_id) if reservation_data.task_id else None,
            need_id=uuid.UUID(reservation_data.need_id) if reservation_data.need_id else None,
            status=ReservationStatus.PENDING.value,
            notes=reservation_data.notes
        )
        
        db.add(db_reservation)
        db.flush()  # 獲取 ID
        
        # 建立預訂物資明細
        for item_data in reservation_data.reservation_items:
            db_item = ReservationItem(
                id=uuid.uuid4(),
                reservation_id=db_reservation.id,
                supply_type=item_data.supply_type,
                requested_quantity=item_data.requested_quantity,
                notes=item_data.notes
            )
            db.add(db_item)
        
        db.commit()
        db.refresh(db_reservation)
        return db_reservation
    
    def get_supply_reservation(self, db: Session, reservation_id: str) -> Optional[SupplyReservation]:
        """根據 ID 獲取物資預訂"""
        return db.query(SupplyReservation).options(
            joinedload(SupplyReservation.user),
            joinedload(SupplyReservation.station),
            joinedload(SupplyReservation.task),
            joinedload(SupplyReservation.need),
            joinedload(SupplyReservation.reservation_items).joinedload(ReservationItem.supply_type_rel)
        ).filter(SupplyReservation.id == uuid.UUID(reservation_id)).first()
    
    def get_supply_reservations(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        user_id: Optional[str] = None,
        user_role: Optional[UserRole] = None,
        station_id: Optional[str] = None,
        status_filter: Optional[ReservationStatus] = None,
        task_id: Optional[str] = None,
        need_id: Optional[str] = None
    ) -> Tuple[List[SupplyReservation], int]:
        """獲取物資預訂列表"""
        query = db.query(SupplyReservation).options(
            joinedload(SupplyReservation.user),
            joinedload(SupplyReservation.station),
            joinedload(SupplyReservation.task),
            joinedload(SupplyReservation.need),
            joinedload(SupplyReservation.reservation_items).joinedload(ReservationItem.supply_type_rel)
        )
        
        # 基於用戶角色的權限篩選
        if user_role and user_role != UserRole.ADMIN:
            if user_role == UserRole.SUPPLY_MANAGER:
                # 物資管理者可以看到自己管理站點的預訂和自己的預訂
                query = query.join(SupplyStation).filter(
                    or_(
                        SupplyStation.manager_id == uuid.UUID(user_id),
                        SupplyReservation.user_id == uuid.UUID(user_id)
                    )
                )
            else:
                # 其他角色只能看到自己的預訂
                query = query.filter(SupplyReservation.user_id == uuid.UUID(user_id))
        
        # 其他篩選條件
        if station_id:
            query = query.filter(SupplyReservation.station_id == uuid.UUID(station_id))
        if status_filter:
            query = query.filter(SupplyReservation.status == status_filter.value)
        if task_id:
            query = query.filter(SupplyReservation.task_id == uuid.UUID(task_id))
        if need_id:
            query = query.filter(SupplyReservation.need_id == uuid.UUID(need_id))
        
        # 獲取總數
        total = query.count()
        
        # 排序和分頁
        reservations = query.order_by(
            SupplyReservation.reserved_at.desc()
        ).offset(skip).limit(limit).all()
        
        return reservations, total
    
    def update_supply_reservation(
        self, 
        db: Session, 
        reservation_id: str, 
        reservation_update: SupplyReservationUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyReservation]:
        """更新物資預訂"""
        reservation = self.get_supply_reservation(db, reservation_id)
        if not reservation:
            return None
        
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or
            str(reservation.user_id) == user_id or  # 預訂者
            str(reservation.station.manager_id) == user_id  # 站點管理者
        )
        
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限編輯此預訂"
            )
        
        # 更新欄位
        update_data = reservation_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(reservation, field, value)
        
        db.commit()
        db.refresh(reservation)
        return reservation
    
    def confirm_supply_reservation(
        self, 
        db: Session, 
        reservation_id: str,
        confirmed_items: List[Dict[str, Any]],
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyReservation]:
        """確認物資預訂（站點管理者操作）"""
        reservation = self.get_supply_reservation(db, reservation_id)
        if not reservation:
            return None
        
        # 權限檢查 - 只有站點管理者和管理員可以確認
        if (user_role != UserRole.ADMIN and 
            str(reservation.station.manager_id) != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限確認此預訂"
            )
        
        # 檢查預訂狀態
        if reservation.status != ReservationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能確認待處理狀態的預訂"
            )
        
        # 更新預訂物資明細的確認數量
        for confirmed_item in confirmed_items:
            item = db.query(ReservationItem).filter(
                and_(
                    ReservationItem.reservation_id == reservation.id,
                    ReservationItem.supply_type == confirmed_item["supply_type"]
                )
            ).first()
            
            if item:
                item.confirmed_quantity = confirmed_item.get("confirmed_quantity", 0)
                if "notes" in confirmed_item:
                    item.notes = confirmed_item["notes"]
        
        # 更新預訂狀態
        reservation.status = ReservationStatus.CONFIRMED.value
        reservation.confirmed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(reservation)
        return reservation
    
    def update_reservation_status(
        self, 
        db: Session, 
        reservation_id: str,
        new_status: ReservationStatus,
        user_id: str,
        user_role: UserRole
    ) -> Optional[SupplyReservation]:
        """更新預訂狀態"""
        reservation = self.get_supply_reservation(db, reservation_id)
        if not reservation:
            return None
        
        # 權限檢查
        can_update = (
            user_role == UserRole.ADMIN or
            str(reservation.user_id) == user_id or  # 預訂者
            str(reservation.station.manager_id) == user_id  # 站點管理者
        )
        
        if not can_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限更新此預訂狀態"
            )
        
        # 狀態轉換邏輯檢查
        current_status = ReservationStatus(reservation.status)
        
        # 定義允許的狀態轉換
        allowed_transitions = {
            ReservationStatus.PENDING: [ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED],
            ReservationStatus.CONFIRMED: [ReservationStatus.PICKED_UP, ReservationStatus.CANCELLED],
            ReservationStatus.PICKED_UP: [ReservationStatus.DELIVERED],
            ReservationStatus.DELIVERED: [],  # 已完成，不能再轉換
            ReservationStatus.CANCELLED: []   # 已取消，不能再轉換
        }
        
        if new_status not in allowed_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不能從 {current_status.value} 狀態轉換到 {new_status.value} 狀態"
            )
        
        # 更新狀態和對應時間戳
        reservation.status = new_status.value
        
        if new_status == ReservationStatus.CONFIRMED:
            reservation.confirmed_at = datetime.utcnow()
        elif new_status == ReservationStatus.PICKED_UP:
            reservation.picked_up_at = datetime.utcnow()
        elif new_status == ReservationStatus.DELIVERED:
            reservation.delivered_at = datetime.utcnow()
        
        db.commit()
        db.refresh(reservation)
        return reservation
    
    def cancel_supply_reservation(
        self, 
        db: Session, 
        reservation_id: str,
        user_id: str,
        user_role: UserRole,
        reason: Optional[str] = None
    ) -> bool:
        """取消物資預訂"""
        reservation = self.get_supply_reservation(db, reservation_id)
        if not reservation:
            return False
        
        # 權限檢查
        can_cancel = (
            user_role == UserRole.ADMIN or
            str(reservation.user_id) == user_id or  # 預訂者
            str(reservation.station.manager_id) == user_id  # 站點管理者
        )
        
        if not can_cancel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限取消此預訂"
            )
        
        # 檢查是否可以取消
        if reservation.status in [ReservationStatus.DELIVERED.value, ReservationStatus.CANCELLED.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已完成或已取消的預訂無法再次取消"
            )
        
        # 更新狀態
        reservation.status = ReservationStatus.CANCELLED.value
        if reason:
            reservation.notes = f"{reservation.notes or ''}\n取消原因: {reason}".strip()
        
        db.commit()
        return True
    
    def get_station_reservations(
        self, 
        db: Session, 
        station_id: str,
        status_filter: Optional[ReservationStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[SupplyReservation], int]:
        """獲取特定站點的預訂列表"""
        query = db.query(SupplyReservation).options(
            joinedload(SupplyReservation.user),
            joinedload(SupplyReservation.task),
            joinedload(SupplyReservation.need),
            joinedload(SupplyReservation.reservation_items).joinedload(ReservationItem.supply_type_rel)
        ).filter(SupplyReservation.station_id == uuid.UUID(station_id))
        
        if status_filter:
            query = query.filter(SupplyReservation.status == status_filter.value)
        
        total = query.count()
        reservations = query.order_by(
            SupplyReservation.reserved_at.desc()
        ).offset(skip).limit(limit).all()
        
        return reservations, total


# 建立全域實例
supply_crud = SupplyCRUD()