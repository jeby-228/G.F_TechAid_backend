"""
避難所管理 CRUD 操作
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text
from fastapi import HTTPException, status

from app.models.system import Shelter
from app.models.user import User
from app.schemas.shelter import (
    ShelterCreate, ShelterUpdate, ShelterSearchQuery,
    ShelterRecommendationQuery, BulkShelterUpdate
)
from app.utils.constants import UserRole
import uuid
import math


class ShelterCRUD:
    """避難所管理 CRUD 操作類"""
    
    def create_shelter(
        self, 
        db: Session, 
        shelter_data: ShelterCreate, 
        creator_id: str,
        creator_role: UserRole
    ) -> Shelter:
        """建立新避難所"""
        # 權限檢查 - 只有管理員可以建立避難所
        if creator_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理員可以建立避難所"
            )
        
        # 檢查管理者是否存在（如果指定了管理者）
        manager_id = None
        if shelter_data.managed_by:
            manager = db.query(User).filter(User.id == uuid.UUID(shelter_data.managed_by)).first()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="指定的管理者不存在"
                )
            manager_id = uuid.UUID(shelter_data.managed_by)
        
        # 建立避難所物件
        db_shelter = Shelter(
            id=uuid.uuid4(),
            name=shelter_data.name,
            address=shelter_data.address,
            location_data=shelter_data.location_data.dict(),
            capacity=shelter_data.capacity,
            current_occupancy=0,
            contact_info=shelter_data.contact_info.dict() if shelter_data.contact_info else None,
            facilities=shelter_data.facilities.dict() if shelter_data.facilities else None,
            status="active",
            managed_by=manager_id
        )
        
        db.add(db_shelter)
        db.commit()
        db.refresh(db_shelter)
        return db_shelter
    
    def get_shelter(self, db: Session, shelter_id: str) -> Optional[Shelter]:
        """根據 ID 獲取避難所"""
        return db.query(Shelter).options(
            joinedload(Shelter.manager)
        ).filter(Shelter.id == uuid.UUID(shelter_id)).first()
    
    def get_shelters(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search_query: Optional[ShelterSearchQuery] = None,
        user_role: Optional[UserRole] = None,
        user_id: Optional[str] = None
    ) -> Tuple[List[Shelter], int]:
        """獲取避難所列表"""
        query = db.query(Shelter).options(
            joinedload(Shelter.manager)
        )
        
        # 搜尋條件
        if search_query:
            if search_query.name:
                query = query.filter(Shelter.name.ilike(f"%{search_query.name}%"))
            
            if search_query.status:
                query = query.filter(Shelter.status == search_query.status)
            
            if search_query.has_capacity:
                if search_query.has_capacity:
                    # 有空位：目前入住人數 < 容量
                    query = query.filter(
                        and_(
                            Shelter.capacity.isnot(None),
                            Shelter.current_occupancy < Shelter.capacity,
                            Shelter.status == "active"
                        )
                    )
                else:
                    # 無空位：目前入住人數 >= 容量 或狀態不是 active
                    query = query.filter(
                        or_(
                            Shelter.capacity.is_(None),
                            Shelter.current_occupancy >= Shelter.capacity,
                            Shelter.status != "active"
                        )
                    )
            
            if search_query.manager_id:
                query = query.filter(Shelter.managed_by == uuid.UUID(search_query.manager_id))
            
            if search_query.min_capacity:
                query = query.filter(
                    and_(
                        Shelter.capacity.isnot(None),
                        Shelter.capacity >= search_query.min_capacity
                    )
                )
            
            if search_query.max_occupancy_rate is not None:
                # 入住率篩選
                query = query.filter(
                    and_(
                        Shelter.capacity.isnot(None),
                        Shelter.capacity > 0,
                        (Shelter.current_occupancy / Shelter.capacity) <= search_query.max_occupancy_rate
                    )
                )
            
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
                    lng_range = search_query.location_radius / (111.0 * math.cos(math.radians(search_query.center_lat)))
                    
                    query = query.filter(
                        and_(
                            func.json_extract(Shelter.location_data, '$.coordinates.lat').between(
                                search_query.center_lat - lat_range,
                                search_query.center_lat + lat_range
                            ),
                            func.json_extract(Shelter.location_data, '$.coordinates.lng').between(
                                search_query.center_lng - lng_range,
                                search_query.center_lng + lng_range
                            )
                        )
                    )
            
            # 設施篩選
            if search_query.has_facility:
                facility_filter = f"$.{search_query.has_facility}"
                query = query.filter(
                    func.json_extract(Shelter.facilities, facility_filter) == True
                )
        
        # 獲取總數
        total = query.count()
        
        # 排序和分頁
        shelters = query.order_by(
            Shelter.status.asc(),  # active 優先
            Shelter.name.asc()
        ).offset(skip).limit(limit).all()
        
        return shelters, total
    
    def update_shelter(
        self, 
        db: Session, 
        shelter_id: str, 
        shelter_update: ShelterUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Optional[Shelter]:
        """更新避難所"""
        shelter = self.get_shelter(db, shelter_id)
        if not shelter:
            return None
        
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or
            (shelter.managed_by and str(shelter.managed_by) == user_id)
        )
        
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限編輯此避難所"
            )
        
        # 檢查新管理者是否存在（如果要更新管理者）
        if shelter_update.managed_by is not None:
            if shelter_update.managed_by:
                manager = db.query(User).filter(User.id == uuid.UUID(shelter_update.managed_by)).first()
                if not manager:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="指定的管理者不存在"
                    )
        
        # 更新欄位
        update_data = shelter_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "location_data" and value:
                if hasattr(value, 'dict'):
                    setattr(shelter, field, value.dict())
                else:
                    setattr(shelter, field, value)
            elif field == "contact_info" and value:
                if hasattr(value, 'dict'):
                    setattr(shelter, field, value.dict())
                else:
                    setattr(shelter, field, value)
            elif field == "facilities" and value:
                if hasattr(value, 'dict'):
                    setattr(shelter, field, value.dict())
                else:
                    setattr(shelter, field, value)
            elif field == "managed_by" and value:
                setattr(shelter, field, uuid.UUID(value) if value else None)
            else:
                setattr(shelter, field, value)
        
        shelter.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(shelter)
        return shelter
    
    def delete_shelter(
        self, 
        db: Session, 
        shelter_id: str,
        user_id: str,
        user_role: UserRole
    ) -> bool:
        """刪除避難所"""
        shelter = self.get_shelter(db, shelter_id)
        if not shelter:
            return False
        
        # 權限檢查 - 只有管理員可以刪除避難所
        if user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理員可以刪除避難所"
            )
        
        # 檢查是否有人入住
        if shelter.current_occupancy > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="避難所仍有人入住，無法刪除"
            )
        
        db.delete(shelter)
        db.commit()
        return True
    
    def update_occupancy(
        self, 
        db: Session, 
        shelter_id: str,
        new_occupancy: int,
        user_id: str,
        user_role: UserRole,
        notes: Optional[str] = None
    ) -> Optional[Shelter]:
        """更新避難所入住人數"""
        shelter = self.get_shelter(db, shelter_id)
        if not shelter:
            return None
        
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or
            (shelter.managed_by and str(shelter.managed_by) == user_id)
        )
        
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限更新此避難所的入住人數"
            )
        
        # 檢查入住人數是否超過容量
        if shelter.capacity and new_occupancy > shelter.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"入住人數 ({new_occupancy}) 不能超過容量 ({shelter.capacity})"
            )
        
        # 更新入住人數
        old_occupancy = shelter.current_occupancy
        shelter.current_occupancy = new_occupancy
        
        # 根據入住情況自動更新狀態
        if shelter.capacity:
            if new_occupancy >= shelter.capacity:
                shelter.status = "full"
            elif shelter.status == "full" and new_occupancy < shelter.capacity:
                shelter.status = "active"
        
        shelter.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(shelter)
        
        # 記錄變更日誌（可選）
        if notes:
            from app.models.system import SystemLog
            log = SystemLog(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                action="update_shelter_occupancy",
                resource_type="shelter",
                resource_id=shelter.id,
                details={
                    "old_occupancy": old_occupancy,
                    "new_occupancy": new_occupancy,
                    "notes": notes
                }
            )
            db.add(log)
            db.commit()
        
        return shelter
    
    def update_status(
        self, 
        db: Session, 
        shelter_id: str,
        new_status: str,
        user_id: str,
        user_role: UserRole,
        reason: Optional[str] = None
    ) -> Optional[Shelter]:
        """更新避難所狀態"""
        shelter = self.get_shelter(db, shelter_id)
        if not shelter:
            return None
        
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or
            (shelter.managed_by and str(shelter.managed_by) == user_id)
        )
        
        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限更新此避難所的狀態"
            )
        
        # 驗證狀態
        valid_statuses = ['active', 'full', 'closed', 'maintenance']
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無效的狀態，必須是以下之一: {', '.join(valid_statuses)}"
            )
        
        # 更新狀態
        old_status = shelter.status
        shelter.status = new_status
        shelter.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(shelter)
        
        # 記錄變更日誌
        from app.models.system import SystemLog
        log = SystemLog(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            action="update_shelter_status",
            resource_type="shelter",
            resource_id=shelter.id,
            details={
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason
            }
        )
        db.add(log)
        db.commit()
        
        return shelter
    
    def get_shelter_map(
        self, 
        db: Session,
        center_lat: Optional[float] = None,
        center_lng: Optional[float] = None,
        radius: Optional[float] = None,
        status_filter: Optional[str] = None,
        has_capacity: Optional[bool] = None
    ) -> Dict[str, Any]:
        """獲取避難所地圖資料"""
        query = db.query(Shelter).options(
            joinedload(Shelter.manager)
        )
        
        # 狀態篩選
        if status_filter:
            query = query.filter(Shelter.status == status_filter)
        
        # 容量篩選
        if has_capacity is not None:
            if has_capacity:
                query = query.filter(
                    and_(
                        Shelter.capacity.isnot(None),
                        Shelter.current_occupancy < Shelter.capacity,
                        Shelter.status == "active"
                    )
                )
            else:
                query = query.filter(
                    or_(
                        Shelter.capacity.is_(None),
                        Shelter.current_occupancy >= Shelter.capacity,
                        Shelter.status != "active"
                    )
                )
        
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
                lng_range = radius / (111.0 * math.cos(math.radians(center_lat)))
                
                query = query.filter(
                    and_(
                        func.json_extract(Shelter.location_data, '$.coordinates.lat').between(
                            center_lat - lat_range,
                            center_lat + lat_range
                        ),
                        func.json_extract(Shelter.location_data, '$.coordinates.lng').between(
                            center_lng - lng_range,
                            center_lng + lng_range
                        )
                    )
                )
        
        shelters = query.all()
        
        # 準備地圖資料
        map_shelters = []
        for shelter in shelters:
            # 計算入住率和可用性
            occupancy_rate = 0.0
            is_available = shelter.status == "active"
            
            if shelter.capacity and shelter.capacity > 0:
                occupancy_rate = shelter.current_occupancy / shelter.capacity
                is_available = is_available and shelter.current_occupancy < shelter.capacity
            
            map_shelters.append({
                "id": str(shelter.id),
                "name": shelter.name,
                "address": shelter.address,
                "coordinates": shelter.location_data.get("coordinates", {}),
                "capacity": shelter.capacity,
                "current_occupancy": shelter.current_occupancy,
                "status": shelter.status,
                "contact_info": shelter.contact_info,
                "facilities": shelter.facilities,
                "occupancy_rate": occupancy_rate,
                "is_available": is_available
            })
        
        # 計算地圖中心點和邊界
        from app.utils.constants import GUANGFU_COORDINATES
        
        if center_lat and center_lng:
            map_center = {"lat": center_lat, "lng": center_lng}
        else:
            map_center = GUANGFU_COORDINATES["center"]
        
        map_bounds = GUANGFU_COORDINATES["bounds"]
        
        return {
            "shelters": map_shelters,
            "center": map_center,
            "bounds": map_bounds
        }
    
    def get_shelter_recommendations(
        self, 
        db: Session,
        query_data: ShelterRecommendationQuery
    ) -> List[Dict[str, Any]]:
        """獲取避難所推薦"""
        user_lat = query_data.user_location["lat"]
        user_lng = query_data.user_location["lng"]
        
        # 基本查詢
        query = db.query(Shelter).options(
            joinedload(Shelter.manager)
        )
        
        # 排除已滿的避難所
        if query_data.exclude_full:
            query = query.filter(
                and_(
                    Shelter.status == "active",
                    or_(
                        Shelter.capacity.is_(None),
                        Shelter.current_occupancy < Shelter.capacity
                    )
                )
            )
        
        # 容量篩選
        if query_data.required_capacity > 1:
            query = query.filter(
                and_(
                    Shelter.capacity.isnot(None),
                    (Shelter.capacity - Shelter.current_occupancy) >= query_data.required_capacity
                )
            )
        
        shelters = query.all()
        
        recommendations = []
        for shelter in shelters:
            # 計算距離
            try:
                # 使用 Haversine 公式計算距離
                shelter_coords = shelter.location_data.get("coordinates", {})
                if not shelter_coords or "lat" not in shelter_coords or "lng" not in shelter_coords:
                    continue
                
                shelter_lat = shelter_coords["lat"]
                shelter_lng = shelter_coords["lng"]
                
                # Haversine 公式
                R = 6371  # 地球半徑（公里）
                dlat = math.radians(shelter_lat - user_lat)
                dlng = math.radians(shelter_lng - user_lng)
                a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                     math.cos(math.radians(user_lat)) * math.cos(math.radians(shelter_lat)) * 
                     math.sin(dlng/2) * math.sin(dlng/2))
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance = R * c
                
                # 距離篩選
                if query_data.max_distance and distance > query_data.max_distance:
                    continue
                
            except Exception:
                continue
            
            # 計算可用容量
            available_capacity = 0
            if shelter.capacity:
                available_capacity = max(0, shelter.capacity - shelter.current_occupancy)
            
            # 檢查設施匹配
            matching_facilities = []
            if query_data.required_facilities and shelter.facilities:
                for facility in query_data.required_facilities:
                    if shelter.facilities.get(facility, False):
                        matching_facilities.append(facility)
            
            # 計算推薦分數
            score = 100.0
            
            # 距離因子（距離越近分數越高）
            if distance > 0:
                score -= min(distance * 5, 50)  # 最多扣50分
            
            # 容量因子
            if shelter.capacity:
                occupancy_rate = shelter.current_occupancy / shelter.capacity
                if occupancy_rate < 0.5:
                    score += 20  # 入住率低於50%加分
                elif occupancy_rate > 0.8:
                    score -= 20  # 入住率高於80%扣分
            
            # 設施匹配因子
            if query_data.required_facilities:
                facility_match_rate = len(matching_facilities) / len(query_data.required_facilities)
                score += facility_match_rate * 30  # 設施匹配度加分
            
            # 狀態因子
            if shelter.status == "active":
                score += 10
            elif shelter.status == "full":
                score -= 30
            elif shelter.status == "closed":
                score -= 50
            
            # 生成推薦原因
            reasons = []
            if distance < 2:
                reasons.append("距離很近")
            elif distance < 5:
                reasons.append("距離適中")
            
            if available_capacity >= query_data.required_capacity * 2:
                reasons.append("容量充足")
            elif available_capacity >= query_data.required_capacity:
                reasons.append("容量足夠")
            
            if matching_facilities:
                reasons.append(f"具備所需設施: {', '.join(matching_facilities)}")
            
            if shelter.status == "active":
                reasons.append("目前開放中")
            
            recommendation_reason = "、".join(reasons) if reasons else "符合基本條件"
            
            recommendations.append({
                "shelter": shelter,
                "distance": round(distance, 2),
                "available_capacity": available_capacity,
                "matching_facilities": matching_facilities,
                "recommendation_score": round(score, 1),
                "recommendation_reason": recommendation_reason
            })
        
        # 按推薦分數排序
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        
        return recommendations
    
    def get_shelter_statistics(self, db: Session) -> Dict[str, Any]:
        """獲取避難所統計資料"""
        # 基本統計
        total_shelters = db.query(Shelter).count()
        active_shelters = db.query(Shelter).filter(Shelter.status == "active").count()
        
        # 容量統計
        capacity_stats = db.query(
            func.sum(Shelter.capacity),
            func.sum(Shelter.current_occupancy)
        ).filter(Shelter.capacity.isnot(None)).first()
        
        total_capacity = capacity_stats[0] or 0
        total_occupancy = capacity_stats[1] or 0
        average_occupancy_rate = (total_occupancy / total_capacity) if total_capacity > 0 else 0
        
        # 各狀態統計
        status_stats = db.query(
            Shelter.status,
            func.count(Shelter.id)
        ).group_by(Shelter.status).all()
        shelters_by_status = {status: count for status, count in status_stats}
        
        # 容量範圍統計
        capacity_ranges = {
            "小型(1-50人)": 0,
            "中型(51-100人)": 0,
            "大型(101-200人)": 0,
            "超大型(200人以上)": 0,
            "未設定": 0
        }
        
        shelters_with_capacity = db.query(Shelter).filter(Shelter.capacity.isnot(None)).all()
        for shelter in shelters_with_capacity:
            if shelter.capacity <= 50:
                capacity_ranges["小型(1-50人)"] += 1
            elif shelter.capacity <= 100:
                capacity_ranges["中型(51-100人)"] += 1
            elif shelter.capacity <= 200:
                capacity_ranges["大型(101-200人)"] += 1
            else:
                capacity_ranges["超大型(200人以上)"] += 1
        
        capacity_ranges["未設定"] = db.query(Shelter).filter(Shelter.capacity.is_(None)).count()
        
        # 設施可用性統計
        facilities_availability = {
            "醫療設施": 0,
            "廚房": 0,
            "淋浴設施": 0,
            "無線網路": 0,
            "發電機": 0,
            "無障礙設施": 0,
            "允許寵物": 0
        }
        
        shelters_with_facilities = db.query(Shelter).filter(Shelter.facilities.isnot(None)).all()
        for shelter in shelters_with_facilities:
            if shelter.facilities:
                if shelter.facilities.get("has_medical", False):
                    facilities_availability["醫療設施"] += 1
                if shelter.facilities.get("has_kitchen", False):
                    facilities_availability["廚房"] += 1
                if shelter.facilities.get("has_shower", False):
                    facilities_availability["淋浴設施"] += 1
                if shelter.facilities.get("has_wifi", False):
                    facilities_availability["無線網路"] += 1
                if shelter.facilities.get("has_generator", False):
                    facilities_availability["發電機"] += 1
                if shelter.facilities.get("has_wheelchair_access", False):
                    facilities_availability["無障礙設施"] += 1
                if shelter.facilities.get("pet_friendly", False):
                    facilities_availability["允許寵物"] += 1
        
        return {
            "total_shelters": total_shelters,
            "active_shelters": active_shelters,
            "total_capacity": total_capacity,
            "total_occupancy": total_occupancy,
            "average_occupancy_rate": round(average_occupancy_rate, 3),
            "shelters_by_status": shelters_by_status,
            "shelters_by_capacity_range": capacity_ranges,
            "facilities_availability": facilities_availability
        }
    
    def bulk_update_shelters(
        self, 
        db: Session, 
        bulk_data: BulkShelterUpdate,
        user_id: str,
        user_role: UserRole
    ) -> Dict[str, Any]:
        """批量更新避難所"""
        # 權限檢查 - 只有管理員可以批量更新
        if user_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理員可以批量更新避難所"
            )
        
        result = {
            "success": True,
            "updated_count": 0,
            "failed_count": 0,
            "errors": [],
            "updated_shelters": []
        }
        
        try:
            for update_item in bulk_data.shelter_updates:
                try:
                    shelter_id = update_item.get("id")
                    if not shelter_id:
                        result["errors"].append("缺少避難所 ID")
                        result["failed_count"] += 1
                        continue
                    
                    shelter = self.get_shelter(db, shelter_id)
                    if not shelter:
                        result["errors"].append(f"避難所 {shelter_id} 不存在")
                        result["failed_count"] += 1
                        continue
                    
                    # 根據更新類型處理
                    if bulk_data.update_type == "occupancy":
                        new_occupancy = update_item.get("current_occupancy")
                        if new_occupancy is not None:
                            shelter.current_occupancy = new_occupancy
                            # 自動更新狀態
                            if shelter.capacity and new_occupancy >= shelter.capacity:
                                shelter.status = "full"
                            elif shelter.status == "full" and new_occupancy < shelter.capacity:
                                shelter.status = "active"
                    
                    elif bulk_data.update_type == "status":
                        new_status = update_item.get("status")
                        if new_status:
                            shelter.status = new_status
                    
                    elif bulk_data.update_type == "facilities":
                        new_facilities = update_item.get("facilities")
                        if new_facilities:
                            shelter.facilities = new_facilities
                    
                    elif bulk_data.update_type == "contact":
                        new_contact = update_item.get("contact_info")
                        if new_contact:
                            shelter.contact_info = new_contact
                    
                    shelter.updated_at = datetime.utcnow()
                    result["updated_count"] += 1
                    result["updated_shelters"].append(shelter_id)
                    
                except Exception as e:
                    result["errors"].append(f"更新避難所 {shelter_id} 時發生錯誤: {str(e)}")
                    result["failed_count"] += 1
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            result["success"] = False
            result["errors"].append(f"批量更新失敗: {str(e)}")
        
        return result


# 建立全域實例
shelter_crud = ShelterCRUD()