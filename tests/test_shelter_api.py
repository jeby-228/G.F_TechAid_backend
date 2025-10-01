"""
避難所 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.system import Shelter
from app.utils.constants import UserRole
import uuid


client = TestClient(app)


class TestShelterAPI:
    """避難所 API 測試類"""
    
    def test_create_shelter_success(self, db: Session, admin_user: User, admin_token: str):
        """測試成功建立避難所"""
        shelter_data = {
            "name": "光復國小避難所",
            "address": "花蓮縣光復鄉中正路123號",
            "location_data": {
                "address": "花蓮縣光復鄉中正路123號",
                "coordinates": {"lat": 23.9739, "lng": 121.6015},
                "details": "光復國小體育館"
            },
            "capacity": 100,
            "contact_info": {
                "phone": "03-8701234",
                "contact_person": "王管理員",
                "hours": "24小時開放"
            },
            "facilities": {
                "has_medical": True,
                "has_kitchen": True,
                "has_shower": True,
                "has_wifi": True,
                "has_generator": False,
                "has_wheelchair_access": True,
                "pet_friendly": False,
                "additional_facilities": ["投影設備", "廣播系統"],
                "notes": "體育館設施完善"
            }
        }
        
        response = client.post(
            "/api/v1/shelters/",
            json=shelter_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == shelter_data["name"]
        assert data["address"] == shelter_data["address"]
        assert data["capacity"] == shelter_data["capacity"]
        assert data["current_occupancy"] == 0
        assert data["status"] == "active"
        assert data["is_available"] is True
        assert data["can_edit"] is True
    
    def test_create_shelter_unauthorized(self, db: Session, volunteer_user: User, volunteer_token: str):
        """測試非管理員無法建立避難所"""
        shelter_data = {
            "name": "測試避難所",
            "address": "測試地址",
            "location_data": {
                "address": "測試地址",
                "coordinates": {"lat": 23.9739, "lng": 121.6015}
            }
        }
        
        response = client.post(
            "/api/v1/shelters/",
            json=shelter_data,
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "只有管理員可以建立避難所" in response.json()["detail"]
    
    def test_get_shelters_list(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試獲取避難所列表"""
        response = client.get(
            "/api/v1/shelters/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "shelters" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["shelters"]) >= 1
        
        # 檢查避難所資料
        shelter = data["shelters"][0]
        assert "id" in shelter
        assert "name" in shelter
        assert "address" in shelter
        assert "capacity" in shelter
        assert "current_occupancy" in shelter
        assert "status" in shelter
        assert "is_available" in shelter
    
    def test_get_shelter_by_id(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試根據 ID 獲取避難所"""
        response = client.get(
            f"/api/v1/shelters/{sample_shelter.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_shelter.id)
        assert data["name"] == sample_shelter.name
        assert data["address"] == sample_shelter.address
    
    def test_get_shelter_not_found(self, db: Session, admin_user: User, admin_token: str):
        """測試獲取不存在的避難所"""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/shelters/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 404
        assert "避難所不存在" in response.json()["detail"]
    
    def test_update_shelter_success(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試成功更新避難所"""
        update_data = {
            "name": "更新後的避難所名稱",
            "capacity": 150,
            "status": "maintenance"
        }
        
        response = client.put(
            f"/api/v1/shelters/{sample_shelter.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["capacity"] == update_data["capacity"]
        assert data["status"] == update_data["status"]
    
    def test_update_shelter_unauthorized(self, db: Session, volunteer_user: User, volunteer_token: str, sample_shelter: Shelter):
        """測試無權限更新避難所"""
        update_data = {"name": "未授權更新"}
        
        response = client.put(
            f"/api/v1/shelters/{sample_shelter.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "沒有權限編輯此避難所" in response.json()["detail"]
    
    def test_update_occupancy_success(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試成功更新入住人數"""
        occupancy_data = {
            "current_occupancy": 50,
            "notes": "更新入住人數"
        }
        
        response = client.patch(
            f"/api/v1/shelters/{sample_shelter.id}/occupancy",
            json=occupancy_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_occupancy"] == 50
        assert data["occupancy_rate"] > 0
    
    def test_update_occupancy_exceed_capacity(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試入住人數超過容量"""
        occupancy_data = {
            "current_occupancy": 200  # 超過容量
        }
        
        response = client.patch(
            f"/api/v1/shelters/{sample_shelter.id}/occupancy",
            json=occupancy_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 400
        assert "不能超過容量" in response.json()["detail"]
    
    def test_update_status_success(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試成功更新狀態"""
        status_data = {
            "status": "closed",
            "reason": "維護中"
        }
        
        response = client.patch(
            f"/api/v1/shelters/{sample_shelter.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "closed"
        assert data["is_available"] is False
    
    def test_update_status_invalid(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試無效狀態更新"""
        status_data = {
            "status": "invalid_status"
        }
        
        response = client.patch(
            f"/api/v1/shelters/{sample_shelter.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_shelter_map(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試獲取避難所地圖"""
        response = client.get(
            "/api/v1/shelters/map",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "shelters" in data
        assert "center" in data
        assert "bounds" in data
        assert len(data["shelters"]) >= 1
        
        # 檢查地圖項目
        shelter = data["shelters"][0]
        assert "coordinates" in shelter
        assert "is_available" in shelter
        assert "occupancy_rate" in shelter
    
    def test_get_shelter_recommendations(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試獲取避難所推薦"""
        recommendation_data = {
            "user_location": {"lat": 23.9739, "lng": 121.6015},
            "required_capacity": 1,
            "required_facilities": ["has_medical", "has_kitchen"],
            "max_distance": 10.0,
            "exclude_full": True
        }
        
        response = client.post(
            "/api/v1/shelters/recommendations",
            json=recommendation_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "query_location" in data
        assert "total_found" in data
        
        if data["recommendations"]:
            rec = data["recommendations"][0]
            assert "shelter" in rec
            assert "distance" in rec
            assert "available_capacity" in rec
            assert "recommendation_score" in rec
            assert "recommendation_reason" in rec
    
    def test_get_nearby_shelters(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試獲取附近避難所"""
        response = client.get(
            "/api/v1/shelters/nearby",
            params={
                "user_lat": 23.9739,
                "user_lng": 121.6015,
                "radius": 10.0,
                "limit": 5
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            shelter = data[0]
            assert "distance_from_center" in shelter
            assert shelter["distance_from_center"] is not None
    
    def test_get_available_shelters(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試獲取可用避難所"""
        response = client.get(
            "/api/v1/shelters/available",
            params={"required_capacity": 1},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "shelters" in data
        assert "total" in data
        
        # 檢查所有返回的避難所都是可用的
        for shelter in data["shelters"]:
            assert shelter["is_available"] is True
            assert shelter["status"] == "active"
    
    def test_get_shelter_statistics(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試獲取避難所統計"""
        response = client.get(
            "/api/v1/shelters/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_shelters" in data
        assert "active_shelters" in data
        assert "total_capacity" in data
        assert "total_occupancy" in data
        assert "average_occupancy_rate" in data
        assert "shelters_by_status" in data
        assert "shelters_by_capacity_range" in data
        assert "facilities_availability" in data
        
        assert data["total_shelters"] >= 1
    
    def test_get_statistics_unauthorized(self, db: Session, volunteer_user: User, volunteer_token: str):
        """測試非管理員無法查看統計"""
        response = client.get(
            "/api/v1/shelters/statistics",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "沒有權限查看統計資料" in response.json()["detail"]
    
    def test_get_my_shelters(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試獲取我管理的避難所"""
        response = client.get(
            "/api/v1/shelters/my-shelters",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "shelters" in data
        assert "total" in data
    
    def test_delete_shelter_success(self, db: Session, admin_user: User, admin_token: str):
        """測試成功刪除避難所"""
        # 先建立一個避難所
        shelter_data = {
            "name": "待刪除避難所",
            "address": "測試地址",
            "location_data": {
                "address": "測試地址",
                "coordinates": {"lat": 23.9739, "lng": 121.6015}
            }
        }
        
        create_response = client.post(
            "/api/v1/shelters/",
            json=shelter_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        shelter_id = create_response.json()["id"]
        
        # 刪除避難所
        response = client.delete(
            f"/api/v1/shelters/{shelter_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 204
        
        # 確認已刪除
        get_response = client.get(
            f"/api/v1/shelters/{shelter_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404
    
    def test_delete_shelter_unauthorized(self, db: Session, volunteer_user: User, volunteer_token: str, sample_shelter: Shelter):
        """測試非管理員無法刪除避難所"""
        response = client.delete(
            f"/api/v1/shelters/{sample_shelter.id}",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "只有管理員可以刪除避難所" in response.json()["detail"]
    
    def test_search_shelters_by_name(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試按名稱搜尋避難所"""
        response = client.get(
            "/api/v1/shelters/",
            params={"name": sample_shelter.name[:5]},  # 部分名稱搜尋
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        
        # 檢查搜尋結果包含目標避難所
        found = any(shelter["id"] == str(sample_shelter.id) for shelter in data["shelters"])
        assert found
    
    def test_search_shelters_by_status(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試按狀態篩選避難所"""
        response = client.get(
            "/api/v1/shelters/",
            params={"status": "active"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 檢查所有返回的避難所狀態都是 active
        for shelter in data["shelters"]:
            assert shelter["status"] == "active"
    
    def test_search_shelters_with_capacity(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試篩選有空位的避難所"""
        response = client.get(
            "/api/v1/shelters/",
            params={"has_capacity": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 檢查所有返回的避難所都有空位
        for shelter in data["shelters"]:
            if shelter["capacity"]:
                assert shelter["current_occupancy"] < shelter["capacity"]
            assert shelter["is_available"] is True
    
    def test_bulk_update_shelters(self, db: Session, admin_user: User, admin_token: str, sample_shelter: Shelter):
        """測試批量更新避難所"""
        bulk_data = {
            "update_type": "occupancy",
            "shelter_updates": [
                {
                    "id": str(sample_shelter.id),
                    "current_occupancy": 30
                }
            ]
        }
        
        response = client.post(
            "/api/v1/shelters/bulk-update",
            json=bulk_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["updated_count"] == 1
        assert data["failed_count"] == 0
        assert str(sample_shelter.id) in data["updated_shelters"]
    
    def test_bulk_update_unauthorized(self, db: Session, volunteer_user: User, volunteer_token: str, sample_shelter: Shelter):
        """測試非管理員無法批量更新"""
        bulk_data = {
            "update_type": "occupancy",
            "shelter_updates": [
                {
                    "id": str(sample_shelter.id),
                    "current_occupancy": 30
                }
            ]
        }
        
        response = client.post(
            "/api/v1/shelters/bulk-update",
            json=bulk_data,
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "只有管理員可以批量更新避難所" in response.json()["detail"]