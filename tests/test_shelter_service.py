"""
避難所服務層測試
"""
import pytest
from sqlalchemy.orm import Session
from app.services.shelter_service import shelter_service
from app.models.user import User
from app.models.system import Shelter
from app.schemas.shelter import (
    ShelterCreate, ShelterUpdate, ShelterSearchQuery,
    ShelterRecommendationQuery, ShelterOccupancyUpdate, ShelterStatusUpdate,
    LocationData, ContactInfo, FacilityInfo
)
from app.utils.constants import UserRole
import uuid


class TestShelterService:
    """避難所服務層測試類"""
    
    def test_create_shelter_success(self, db: Session, admin_user: User):
        """測試成功建立避難所"""
        shelter_data = ShelterCreate(
            name="測試避難所",
            address="花蓮縣光復鄉測試路123號",
            location_data=LocationData(
                address="花蓮縣光復鄉測試路123號",
                coordinates={"lat": 23.9739, "lng": 121.6015},
                details="測試避難所詳細位置"
            ),
            capacity=100,
            contact_info=ContactInfo(
                phone="03-8701234",
                contact_person="測試管理員",
                hours="24小時開放"
            ),
            facilities=FacilityInfo(
                has_medical=True,
                has_kitchen=True,
                has_shower=False,
                has_wifi=True,
                pet_friendly=False
            )
        )
        
        result = shelter_service.create_shelter(
            db=db,
            shelter_data=shelter_data,
            creator_id=str(admin_user.id),
            creator_role=UserRole.ADMIN
        )
        
        assert result.name == shelter_data.name
        assert result.address == shelter_data.address
        assert result.capacity == shelter_data.capacity
        assert result.current_occupancy == 0
        assert result.status == "active"
        assert result.is_available is True
        assert result.can_edit is True
    
    def test_create_shelter_unauthorized(self, db: Session, volunteer_user: User):
        """測試非管理員無法建立避難所"""
        shelter_data = ShelterCreate(
            name="測試避難所",
            address="測試地址",
            location_data=LocationData(
                address="測試地址",
                coordinates={"lat": 23.9739, "lng": 121.6015}
            )
        )
        
        with pytest.raises(Exception) as exc_info:
            shelter_service.create_shelter(
                db=db,
                shelter_data=shelter_data,
                creator_id=str(volunteer_user.id),
                creator_role=UserRole.VOLUNTEER
            )
        
        assert "只有管理員可以建立避難所" in str(exc_info.value)
    
    def test_get_shelter_success(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試成功獲取避難所"""
        result = shelter_service.get_shelter(
            db=db,
            shelter_id=str(sample_shelter.id),
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is not None
        assert result.id == str(sample_shelter.id)
        assert result.name == sample_shelter.name
        assert result.address == sample_shelter.address
    
    def test_get_shelter_not_found(self, db: Session, admin_user: User):
        """測試獲取不存在的避難所"""
        fake_id = str(uuid.uuid4())
        result = shelter_service.get_shelter(
            db=db,
            shelter_id=fake_id,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is None
    
    def test_get_shelters_list(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試獲取避難所列表"""
        result = shelter_service.get_shelters(
            db=db,
            skip=0,
            limit=10,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result.total >= 1
        assert len(result.shelters) >= 1
        assert any(shelter.id == str(sample_shelter.id) for shelter in result.shelters)
    
    def test_search_shelters_by_name(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試按名稱搜尋避難所"""
        search_query = ShelterSearchQuery(name=sample_shelter.name[:5])
        
        result = shelter_service.get_shelters(
            db=db,
            skip=0,
            limit=10,
            search_query=search_query,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result.total >= 1
        found = any(shelter.id == str(sample_shelter.id) for shelter in result.shelters)
        assert found
    
    def test_search_shelters_with_capacity(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試搜尋有空位的避難所"""
        search_query = ShelterSearchQuery(has_capacity=True)
        
        result = shelter_service.get_shelters(
            db=db,
            skip=0,
            limit=10,
            search_query=search_query,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        # 檢查所有返回的避難所都有空位
        for shelter in result.shelters:
            assert shelter.is_available is True
    
    def test_update_shelter_success(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試成功更新避難所"""
        update_data = ShelterUpdate(
            name="更新後的避難所名稱",
            capacity=150
        )
        
        result = shelter_service.update_shelter(
            db=db,
            shelter_id=str(sample_shelter.id),
            shelter_update=update_data,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is not None
        assert result.name == update_data.name
        assert result.capacity == update_data.capacity
    
    def test_update_shelter_unauthorized(self, db: Session, volunteer_user: User, sample_shelter: Shelter):
        """測試無權限更新避難所"""
        update_data = ShelterUpdate(name="未授權更新")
        
        with pytest.raises(Exception) as exc_info:
            shelter_service.update_shelter(
                db=db,
                shelter_id=str(sample_shelter.id),
                shelter_update=update_data,
                user_id=str(volunteer_user.id),
                user_role=UserRole.VOLUNTEER
            )
        
        assert "沒有權限編輯此避難所" in str(exc_info.value)
    
    def test_update_occupancy_success(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試成功更新入住人數"""
        occupancy_update = ShelterOccupancyUpdate(
            current_occupancy=50,
            notes="測試更新入住人數"
        )
        
        result = shelter_service.update_occupancy(
            db=db,
            shelter_id=str(sample_shelter.id),
            occupancy_update=occupancy_update,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is not None
        assert result.current_occupancy == 50
        assert result.occupancy_rate > 0
    
    def test_update_occupancy_exceed_capacity(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試入住人數超過容量"""
        occupancy_update = ShelterOccupancyUpdate(
            current_occupancy=200  # 超過容量
        )
        
        with pytest.raises(Exception) as exc_info:
            shelter_service.update_occupancy(
                db=db,
                shelter_id=str(sample_shelter.id),
                occupancy_update=occupancy_update,
                user_id=str(admin_user.id),
                user_role=UserRole.ADMIN
            )
        
        assert "不能超過容量" in str(exc_info.value)
    
    def test_update_status_success(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試成功更新狀態"""
        status_update = ShelterStatusUpdate(
            status="maintenance",
            reason="設施維護"
        )
        
        result = shelter_service.update_status(
            db=db,
            shelter_id=str(sample_shelter.id),
            status_update=status_update,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is not None
        assert result.status == "maintenance"
        assert result.is_available is False
    
    def test_delete_shelter_success(self, db: Session, admin_user: User):
        """測試成功刪除避難所"""
        # 先建立一個避難所
        shelter_data = ShelterCreate(
            name="待刪除避難所",
            address="測試地址",
            location_data=LocationData(
                address="測試地址",
                coordinates={"lat": 23.9739, "lng": 121.6015}
            )
        )
        
        created_shelter = shelter_service.create_shelter(
            db=db,
            shelter_data=shelter_data,
            creator_id=str(admin_user.id),
            creator_role=UserRole.ADMIN
        )
        
        # 刪除避難所
        result = shelter_service.delete_shelter(
            db=db,
            shelter_id=created_shelter.id,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is True
        
        # 確認已刪除
        deleted_shelter = shelter_service.get_shelter(
            db=db,
            shelter_id=created_shelter.id,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        assert deleted_shelter is None
    
    def test_delete_shelter_unauthorized(self, db: Session, volunteer_user: User, sample_shelter: Shelter):
        """測試非管理員無法刪除避難所"""
        with pytest.raises(Exception) as exc_info:
            shelter_service.delete_shelter(
                db=db,
                shelter_id=str(sample_shelter.id),
                user_id=str(volunteer_user.id),
                user_role=UserRole.VOLUNTEER
            )
        
        assert "只有管理員可以刪除避難所" in str(exc_info.value)
    
    def test_get_shelter_map(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試獲取避難所地圖"""
        result = shelter_service.get_shelter_map(db=db)
        
        assert result.shelters is not None
        assert result.center is not None
        assert result.bounds is not None
        assert len(result.shelters) >= 1
        
        # 檢查地圖項目
        shelter = result.shelters[0]
        assert shelter.coordinates is not None
        assert "lat" in shelter.coordinates
        assert "lng" in shelter.coordinates
    
    def test_get_shelter_recommendations(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試獲取避難所推薦"""
        query_data = ShelterRecommendationQuery(
            user_location={"lat": 23.9739, "lng": 121.6015},
            required_capacity=1,
            required_facilities=["has_medical"],
            max_distance=10.0,
            exclude_full=True
        )
        
        result = shelter_service.get_shelter_recommendations(db=db, query_data=query_data)
        
        assert result.recommendations is not None
        assert result.query_location == query_data.user_location
        assert result.total_found >= 0
        
        if result.recommendations:
            rec = result.recommendations[0]
            assert rec.shelter is not None
            assert rec.distance >= 0
            assert rec.recommendation_score > 0
            assert rec.recommendation_reason is not None
    
    def test_get_nearby_shelters(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試獲取附近避難所"""
        result = shelter_service.get_nearby_shelters(
            db=db,
            user_lat=23.9739,
            user_lng=121.6015,
            radius=10.0,
            limit=5,
            has_capacity=True
        )
        
        assert isinstance(result, list)
        
        if result:
            shelter = result[0]
            assert shelter.distance_from_center is not None
            assert shelter.distance_from_center >= 0
    
    def test_get_available_shelters(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試獲取可用避難所"""
        result = shelter_service.get_available_shelters(
            db=db,
            required_capacity=1,
            skip=0,
            limit=10
        )
        
        assert result.total >= 0
        
        # 檢查所有返回的避難所都是可用的
        for shelter in result.shelters:
            assert shelter.is_available is True
            assert shelter.status == "active"
    
    def test_get_shelter_statistics(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試獲取避難所統計"""
        result = shelter_service.get_shelter_statistics(db=db)
        
        assert result.total_shelters >= 1
        assert result.active_shelters >= 0
        assert result.total_capacity >= 0
        assert result.total_occupancy >= 0
        assert result.average_occupancy_rate >= 0
        assert result.shelters_by_status is not None
        assert result.shelters_by_capacity_range is not None
        assert result.facilities_availability is not None
    
    def test_get_shelter_by_manager(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試獲取特定管理者的避難所"""
        result = shelter_service.get_shelter_by_manager(
            db=db,
            manager_id=str(admin_user.id),
            skip=0,
            limit=10
        )
        
        assert result.total >= 0
        assert result.shelters is not None
    
    def test_occupancy_rate_calculation(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試入住率計算"""
        # 更新入住人數
        occupancy_update = ShelterOccupancyUpdate(current_occupancy=25)
        
        result = shelter_service.update_occupancy(
            db=db,
            shelter_id=str(sample_shelter.id),
            occupancy_update=occupancy_update,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        # 檢查入住率計算
        if result.capacity and result.capacity > 0:
            expected_rate = result.current_occupancy / result.capacity
            assert abs(result.occupancy_rate - expected_rate) < 0.001
    
    def test_availability_logic(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試可用性邏輯"""
        # 測試 active 狀態且有空位
        occupancy_update = ShelterOccupancyUpdate(current_occupancy=50)
        result = shelter_service.update_occupancy(
            db=db,
            shelter_id=str(sample_shelter.id),
            occupancy_update=occupancy_update,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        if result.capacity and result.current_occupancy < result.capacity:
            assert result.is_available is True
        
        # 測試滿員狀態
        if result.capacity:
            full_occupancy = ShelterOccupancyUpdate(current_occupancy=result.capacity)
            full_result = shelter_service.update_occupancy(
                db=db,
                shelter_id=str(sample_shelter.id),
                occupancy_update=full_occupancy,
                user_id=str(admin_user.id),
                user_role=UserRole.ADMIN
            )
            
            assert full_result.status == "full"
            assert full_result.is_available is False
        
        # 測試關閉狀態
        status_update = ShelterStatusUpdate(status="closed")
        closed_result = shelter_service.update_status(
            db=db,
            shelter_id=str(sample_shelter.id),
            status_update=status_update,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert closed_result.is_available is False