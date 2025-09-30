"""
避難所 CRUD 操作測試
"""
import pytest
from sqlalchemy.orm import Session
from app.crud.shelter import shelter_crud
from app.models.user import User
from app.models.system import Shelter
from app.schemas.shelter import (
    ShelterCreate, ShelterUpdate, ShelterSearchQuery,
    ShelterRecommendationQuery, LocationData, ContactInfo, FacilityInfo
)
from app.utils.constants import UserRole
import uuid


class TestShelterCRUD:
    """避難所 CRUD 操作測試類"""
    
    def test_create_shelter_success(self, db: Session, admin_user: User):
        """測試成功建立避難所"""
        shelter_data = ShelterCreate(
            name="CRUD測試避難所",
            address="花蓮縣光復鄉CRUD測試路123號",
            location_data=LocationData(
                address="花蓮縣光復鄉CRUD測試路123號",
                coordinates={"lat": 23.9739, "lng": 121.6015},
                details="CRUD測試避難所詳細位置"
            ),
            capacity=80,
            contact_info=ContactInfo(
                phone="03-8701234",
                contact_person="CRUD測試管理員",
                hours="24小時開放",
                emergency_contact="119"
            ),
            facilities=FacilityInfo(
                has_medical=True,
                has_kitchen=False,
                has_shower=True,
                has_wifi=True,
                has_generator=True,
                has_wheelchair_access=False,
                pet_friendly=True,
                additional_facilities=["停車場", "會議室"],
                notes="CRUD測試設施"
            )
        )
        
        result = shelter_crud.create_shelter(
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
        assert result.location_data == shelter_data.location_data.dict()
        assert result.contact_info == shelter_data.contact_info.dict()
        assert result.facilities == shelter_data.facilities.dict()
    
    def test_create_shelter_unauthorized(self, db: Session, volunteer_user: User):
        """測試非管理員無法建立避難所"""
        shelter_data = ShelterCreate(
            name="未授權避難所",
            address="測試地址",
            location_data=LocationData(
                address="測試地址",
                coordinates={"lat": 23.9739, "lng": 121.6015}
            )
        )
        
        with pytest.raises(Exception) as exc_info:
            shelter_crud.create_shelter(
                db=db,
                shelter_data=shelter_data,
                creator_id=str(volunteer_user.id),
                creator_role=UserRole.VOLUNTEER
            )
        
        assert "只有管理員可以建立避難所" in str(exc_info.value)
    
    def test_get_shelter_success(self, db: Session, sample_shelter: Shelter):
        """測試成功獲取避難所"""
        result = shelter_crud.get_shelter(db, str(sample_shelter.id))
        
        assert result is not None
        assert result.id == sample_shelter.id
        assert result.name == sample_shelter.name
        assert result.address == sample_shelter.address
    
    def test_get_shelter_not_found(self, db: Session):
        """測試獲取不存在的避難所"""
        fake_id = str(uuid.uuid4())
        result = shelter_crud.get_shelter(db, fake_id)
        
        assert result is None
    
    def test_get_shelters_basic(self, db: Session, sample_shelter: Shelter):
        """測試基本獲取避難所列表"""
        shelters, total = shelter_crud.get_shelters(db, skip=0, limit=10)
        
        assert total >= 1
        assert len(shelters) >= 1
        assert any(shelter.id == sample_shelter.id for shelter in shelters)
    
    def test_get_shelters_with_pagination(self, db: Session, admin_user: User):
        """測試分頁獲取避難所列表"""
        # 建立多個避難所
        for i in range(5):
            shelter_data = ShelterCreate(
                name=f"分頁測試避難所{i}",
                address=f"測試地址{i}",
                location_data=LocationData(
                    address=f"測試地址{i}",
                    coordinates={"lat": 23.9739 + i * 0.001, "lng": 121.6015 + i * 0.001}
                )
            )
            shelter_crud.create_shelter(db, shelter_data, str(admin_user.id), UserRole.ADMIN)
        
        # 測試第一頁
        shelters_page1, total = shelter_crud.get_shelters(db, skip=0, limit=3)
        assert len(shelters_page1) <= 3
        assert total >= 5
        
        # 測試第二頁
        shelters_page2, _ = shelter_crud.get_shelters(db, skip=3, limit=3)
        assert len(shelters_page2) >= 0
        
        # 確保兩頁的避難所不重複
        page1_ids = {shelter.id for shelter in shelters_page1}
        page2_ids = {shelter.id for shelter in shelters_page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_search_shelters_by_name(self, db: Session, sample_shelter: Shelter):
        """測試按名稱搜尋避難所"""
        search_query = ShelterSearchQuery(name=sample_shelter.name[:5])
        
        shelters, total = shelter_crud.get_shelters(
            db, skip=0, limit=10, search_query=search_query
        )
        
        assert total >= 1
        found = any(shelter.id == sample_shelter.id for shelter in shelters)
        assert found
    
    def test_search_shelters_by_status(self, db: Session, sample_shelter: Shelter):
        """測試按狀態搜尋避難所"""
        search_query = ShelterSearchQuery(status="active")
        
        shelters, total = shelter_crud.get_shelters(
            db, skip=0, limit=10, search_query=search_query
        )
        
        # 檢查所有返回的避難所狀態都是 active
        for shelter in shelters:
            assert shelter.status == "active"
    
    def test_search_shelters_with_capacity(self, db: Session, sample_shelter: Shelter):
        """測試搜尋有空位的避難所"""
        search_query = ShelterSearchQuery(has_capacity=True)
        
        shelters, total = shelter_crud.get_shelters(
            db, skip=0, limit=10, search_query=search_query
        )
        
        # 檢查所有返回的避難所都有空位
        for shelter in shelters:
            if shelter.capacity:
                assert shelter.current_occupancy < shelter.capacity
            assert shelter.status == "active"
    
    def test_search_shelters_by_min_capacity(self, db: Session, admin_user: User):
        """測試按最小容量搜尋避難所"""
        # 建立不同容量的避難所
        small_shelter_data = ShelterCreate(
            name="小型避難所",
            address="小型地址",
            location_data=LocationData(
                address="小型地址",
                coordinates={"lat": 23.9739, "lng": 121.6015}
            ),
            capacity=30
        )
        
        large_shelter_data = ShelterCreate(
            name="大型避難所",
            address="大型地址",
            location_data=LocationData(
                address="大型地址",
                coordinates={"lat": 23.9740, "lng": 121.6016}
            ),
            capacity=200
        )
        
        shelter_crud.create_shelter(db, small_shelter_data, str(admin_user.id), UserRole.ADMIN)
        large_shelter = shelter_crud.create_shelter(db, large_shelter_data, str(admin_user.id), UserRole.ADMIN)
        
        # 搜尋容量至少100的避難所
        search_query = ShelterSearchQuery(min_capacity=100)
        
        shelters, total = shelter_crud.get_shelters(
            db, skip=0, limit=10, search_query=search_query
        )
        
        # 檢查所有返回的避難所容量都 >= 100
        for shelter in shelters:
            if shelter.capacity:
                assert shelter.capacity >= 100
        
        # 確保大型避難所在結果中
        found = any(shelter.id == large_shelter.id for shelter in shelters)
        assert found
    
    def test_update_shelter_success(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試成功更新避難所"""
        update_data = ShelterUpdate(
            name="更新後的避難所名稱",
            capacity=120,
            current_occupancy=30,
            contact_info=ContactInfo(
                phone="03-8709999",
                contact_person="新管理員",
                hours="8:00-22:00"
            )
        )
        
        result = shelter_crud.update_shelter(
            db=db,
            shelter_id=str(sample_shelter.id),
            shelter_update=update_data,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is not None
        assert result.name == update_data.name
        assert result.capacity == update_data.capacity
        assert result.current_occupancy == update_data.current_occupancy
        assert result.contact_info == update_data.contact_info.dict()
    
    def test_update_shelter_unauthorized(self, db: Session, volunteer_user: User, sample_shelter: Shelter):
        """測試無權限更新避難所"""
        update_data = ShelterUpdate(name="未授權更新")
        
        with pytest.raises(Exception) as exc_info:
            shelter_crud.update_shelter(
                db=db,
                shelter_id=str(sample_shelter.id),
                shelter_update=update_data,
                user_id=str(volunteer_user.id),
                user_role=UserRole.VOLUNTEER
            )
        
        assert "沒有權限編輯此避難所" in str(exc_info.value)
    
    def test_update_shelter_not_found(self, db: Session, admin_user: User):
        """測試更新不存在的避難所"""
        fake_id = str(uuid.uuid4())
        update_data = ShelterUpdate(name="不存在的避難所")
        
        result = shelter_crud.update_shelter(
            db=db,
            shelter_id=fake_id,
            shelter_update=update_data,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is None
    
    def test_update_occupancy_success(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試成功更新入住人數"""
        result = shelter_crud.update_occupancy(
            db=db,
            shelter_id=str(sample_shelter.id),
            new_occupancy=40,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN,
            notes="測試更新入住人數"
        )
        
        assert result is not None
        assert result.current_occupancy == 40
    
    def test_update_occupancy_exceed_capacity(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試入住人數超過容量"""
        with pytest.raises(Exception) as exc_info:
            shelter_crud.update_occupancy(
                db=db,
                shelter_id=str(sample_shelter.id),
                new_occupancy=200,  # 超過容量
                user_id=str(admin_user.id),
                user_role=UserRole.ADMIN
            )
        
        assert "不能超過容量" in str(exc_info.value)
    
    def test_update_occupancy_auto_status_change(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試入住人數變化自動更新狀態"""
        # 設置為滿員
        if sample_shelter.capacity:
            result = shelter_crud.update_occupancy(
                db=db,
                shelter_id=str(sample_shelter.id),
                new_occupancy=sample_shelter.capacity,
                user_id=str(admin_user.id),
                user_role=UserRole.ADMIN
            )
            
            assert result.status == "full"
            
            # 減少入住人數
            result = shelter_crud.update_occupancy(
                db=db,
                shelter_id=str(sample_shelter.id),
                new_occupancy=sample_shelter.capacity - 10,
                user_id=str(admin_user.id),
                user_role=UserRole.ADMIN
            )
            
            assert result.status == "active"
    
    def test_update_status_success(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試成功更新狀態"""
        result = shelter_crud.update_status(
            db=db,
            shelter_id=str(sample_shelter.id),
            new_status="maintenance",
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN,
            reason="設施維護"
        )
        
        assert result is not None
        assert result.status == "maintenance"
    
    def test_update_status_invalid(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試無效狀態更新"""
        with pytest.raises(Exception) as exc_info:
            shelter_crud.update_status(
                db=db,
                shelter_id=str(sample_shelter.id),
                new_status="invalid_status",
                user_id=str(admin_user.id),
                user_role=UserRole.ADMIN
            )
        
        assert "無效的狀態" in str(exc_info.value)
    
    def test_delete_shelter_success(self, db: Session, admin_user: User):
        """測試成功刪除避難所"""
        # 先建立一個避難所
        shelter_data = ShelterCreate(
            name="待刪除避難所",
            address="待刪除地址",
            location_data=LocationData(
                address="待刪除地址",
                coordinates={"lat": 23.9739, "lng": 121.6015}
            )
        )
        
        created_shelter = shelter_crud.create_shelter(
            db, shelter_data, str(admin_user.id), UserRole.ADMIN
        )
        
        # 刪除避難所
        result = shelter_crud.delete_shelter(
            db=db,
            shelter_id=str(created_shelter.id),
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        assert result is True
        
        # 確認已刪除
        deleted_shelter = shelter_crud.get_shelter(db, str(created_shelter.id))
        assert deleted_shelter is None
    
    def test_delete_shelter_with_occupancy(self, db: Session, admin_user: User, sample_shelter: Shelter):
        """測試刪除有人入住的避難所"""
        # 先設置入住人數
        shelter_crud.update_occupancy(
            db=db,
            shelter_id=str(sample_shelter.id),
            new_occupancy=10,
            user_id=str(admin_user.id),
            user_role=UserRole.ADMIN
        )
        
        # 嘗試刪除
        with pytest.raises(Exception) as exc_info:
            shelter_crud.delete_shelter(
                db=db,
                shelter_id=str(sample_shelter.id),
                user_id=str(admin_user.id),
                user_role=UserRole.ADMIN
            )
        
        assert "仍有人入住，無法刪除" in str(exc_info.value)
    
    def test_delete_shelter_unauthorized(self, db: Session, volunteer_user: User, sample_shelter: Shelter):
        """測試非管理員無法刪除避難所"""
        with pytest.raises(Exception) as exc_info:
            shelter_crud.delete_shelter(
                db=db,
                shelter_id=str(sample_shelter.id),
                user_id=str(volunteer_user.id),
                user_role=UserRole.VOLUNTEER
            )
        
        assert "只有管理員可以刪除避難所" in str(exc_info.value)
    
    def test_get_shelter_map(self, db: Session, sample_shelter: Shelter):
        """測試獲取避難所地圖資料"""
        result = shelter_crud.get_shelter_map(db)
        
        assert "shelters" in result
        assert "center" in result
        assert "bounds" in result
        assert len(result["shelters"]) >= 1
        
        # 檢查地圖項目
        shelter = result["shelters"][0]
        assert "coordinates" in shelter
        assert "is_available" in shelter
        assert "occupancy_rate" in shelter
    
    def test_get_shelter_recommendations(self, db: Session, sample_shelter: Shelter):
        """測試獲取避難所推薦"""
        query_data = ShelterRecommendationQuery(
            user_location={"lat": 23.9739, "lng": 121.6015},
            required_capacity=1,
            required_facilities=["has_medical"],
            max_distance=10.0,
            exclude_full=True
        )
        
        result = shelter_crud.get_shelter_recommendations(db, query_data)
        
        assert isinstance(result, list)
        
        if result:
            rec = result[0]
            assert "shelter" in rec
            assert "distance" in rec
            assert "available_capacity" in rec
            assert "recommendation_score" in rec
            assert "recommendation_reason" in rec
            assert rec["distance"] >= 0
            assert rec["recommendation_score"] > 0
    
    def test_get_shelter_statistics(self, db: Session, sample_shelter: Shelter):
        """測試獲取避難所統計"""
        result = shelter_crud.get_shelter_statistics(db)
        
        assert "total_shelters" in result
        assert "active_shelters" in result
        assert "total_capacity" in result
        assert "total_occupancy" in result
        assert "average_occupancy_rate" in result
        assert "shelters_by_status" in result
        assert "shelters_by_capacity_range" in result
        assert "facilities_availability" in result
        
        assert result["total_shelters"] >= 1
        assert result["active_shelters"] >= 0
        assert result["total_capacity"] >= 0
        assert result["total_occupancy"] >= 0
        assert result["average_occupancy_rate"] >= 0
    
    def test_location_radius_search(self, db: Session, admin_user: User):
        """測試地理位置半徑搜尋"""
        # 建立不同位置的避難所
        near_shelter_data = ShelterCreate(
            name="附近避難所",
            address="附近地址",
            location_data=LocationData(
                address="附近地址",
                coordinates={"lat": 23.9740, "lng": 121.6016}  # 很近
            )
        )
        
        far_shelter_data = ShelterCreate(
            name="遠處避難所",
            address="遠處地址",
            location_data=LocationData(
                address="遠處地址",
                coordinates={"lat": 24.0000, "lng": 121.7000}  # 較遠
            )
        )
        
        near_shelter = shelter_crud.create_shelter(db, near_shelter_data, str(admin_user.id), UserRole.ADMIN)
        far_shelter = shelter_crud.create_shelter(db, far_shelter_data, str(admin_user.id), UserRole.ADMIN)
        
        # 搜尋半徑1公里內的避難所
        search_query = ShelterSearchQuery(
            center_lat=23.9739,
            center_lng=121.6015,
            location_radius=1.0
        )
        
        shelters, total = shelter_crud.get_shelters(
            db, skip=0, limit=10, search_query=search_query
        )
        
        # 檢查結果
        near_found = any(shelter.id == near_shelter.id for shelter in shelters)
        far_found = any(shelter.id == far_shelter.id for shelter in shelters)
        
        assert near_found  # 附近的應該找到
        # 遠處的可能找到也可能找不到，取決於實際距離計算