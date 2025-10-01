"""
避難所管理服務層
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

print("Importing shelter_crud...")
from app.crud.shelter import shelter_crud
print("shelter_crud imported successfully")
from app.schemas.shelter import (
    ShelterCreate, ShelterUpdate, ShelterResponse, 
    ShelterListResponse, ShelterSearchQuery,
    ShelterMapResponse, ShelterMapItem,
    ShelterRecommendationQuery, ShelterRecommendation, ShelterRecommendationResponse,
    ShelterStatistics, ShelterOccupancyUpdate, ShelterStatusUpdate,
    BulkShelterUpdate, BulkShelterResponse,
    ContactInfo, FacilityInfo, LocationData
)
from app.utils.constants import UserRole


class ShelterService:
    """避難所管理服務類"""
    
    def create_shelter(
        self, 
        db: Session, 
        shelter_data: ShelterCreate, 
        creator_id: str,
        creator_role: UserRole
    ) -> ShelterResponse:
        """建立避難所"""
        shelter = shelter_crud.create_shelter(db, shelter_data, creator_id, creator_role)
        return self._convert_shelter_to_response(shelter, creator_id, creator_role)
    
    def get_shelter(
        self, 
        db: Session, 
        shelter_id: str,
        user_id: str,
        user_role: UserRole
    ) -> Optional[ShelterResponse]:
        """獲取單一避難所"""
        shelter = shelter_crud.get_shelter(db, shelter_id)
        if not shelter:
            return None
        
        return self._convert_shelter_to_response(shelter, user_id, user_role)
    
    def _convert_shelter_to_response(
        self, 
        shelter, 
        user_id: Optional[str], 
        user_role: UserRole
    ) -> ShelterResponse:
        """轉換避難所模型為回應模型"""
        # 計算入住率
        occupancy_rate = 0.0
        if shelter.capacity and shelter.capacity > 0:
            occupancy_rate = shelter.current_occupancy / shelter.capacity
        
        # 判斷是否可入住
        is_available = (
            shelter.status == "active" and
            (not shelter.capacity or shelter.current_occupancy < shelter.capacity)
        )
        
        # 權限檢查
        can_edit = (
            user_role == UserRole.ADMIN or
            (shelter.managed_by and user_id and str(shelter.managed_by) == user_id)
        )
        
        # 轉換聯絡資訊
        contact_info = None
        if shelter.contact_info:
            contact_info = ContactInfo(**shelter.contact_info)
        
        # 轉換設施資訊
        facilities = None
        if shelter.facilities:
            facilities = FacilityInfo(**shelter.facilities)
        
        # 轉換地理位置資訊
        location_data = LocationData(**shelter.location_data)
        
        return ShelterResponse(
            id=str(shelter.id),
            name=shelter.name,
            address=shelter.address,
            location_data=location_data,
            capacity=shelter.capacity,
            current_occupancy=shelter.current_occupancy,
            contact_info=contact_info,
            facilities=facilities,
            status=shelter.status,
            managed_by=str(shelter.managed_by) if shelter.managed_by else None,
            created_at=shelter.created_at,
            updated_at=shelter.updated_at,
            manager_name=shelter.manager.name if shelter.manager else None,
            manager_role=UserRole(shelter.manager.role) if shelter.manager else None,
            occupancy_rate=round(occupancy_rate, 3),
            is_available=is_available,
            distance_from_center=None,
            can_edit=can_edit
        )


# 建立全域實例
shelter_service = ShelterService()