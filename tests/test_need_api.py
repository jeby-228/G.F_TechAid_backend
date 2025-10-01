"""
需求管理 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.models.need import Need, NeedType as NeedTypeModel, NeedStatus as NeedStatusModel
from app.utils.constants import UserRole, NeedType, NeedStatus
from app.core.security import create_access_token
from tests.conftest import TestingSessionLocal, override_get_db
import json

# 覆蓋資料庫依賴
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestNeedAPI:
    """需求 API 測試類"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, db_session: Session):
        """每個測試方法前的設置"""
        self.db = db_session
        
        # 建立測試用戶
        self.victim_user = User(
            email="victim@test.com",
            name="測試受災戶",
            password_hash="hashed_password",
            role=UserRole.VICTIM.value,
            is_approved=True
        )
        self.volunteer_user = User(
            email="volunteer@test.com",
            name="測試志工",
            password_hash="hashed_password",
            role=UserRole.VOLUNTEER.value,
            is_approved=True
        )
        self.admin_user = User(
            email="admin@test.com",
            name="測試管理員",
            password_hash="hashed_password",
            role=UserRole.ADMIN.value,
            is_approved=True
        )
        
        self.db.add_all([self.victim_user, self.volunteer_user, self.admin_user])
        self.db.commit()
        
        # 建立需求類型和狀態
        need_types = [
            NeedTypeModel(type="food", display_name="食物需求"),
            NeedTypeModel(type="medical", display_name="醫療需求"),
            NeedTypeModel(type="shelter", display_name="住宿需求")
        ]
        need_statuses = [
            NeedStatusModel(status="open", display_name="待處理"),
            NeedStatusModel(status="assigned", display_name="已分配"),
            NeedStatusModel(status="resolved", display_name="已解決")
        ]
        
        self.db.add_all(need_types + need_statuses)
        self.db.commit()
        
        # 建立測試需求
        self.test_need = Need(
            reporter_id=self.victim_user.id,
            title="緊急食物需求",
            description="家中食物短缺，需要緊急補給",
            need_type=NeedType.FOOD.value,
            status=NeedStatus.OPEN.value,
            location_data={
                "address": "花蓮縣光復鄉中正路123號",
                "coordinates": {"lat": 23.5731, "lng": 121.4208},
                "details": "靠近光復國小"
            },
            requirements={
                "items": [
                    {"name": "白米", "quantity": 5, "unit": "公斤"},
                    {"name": "罐頭", "quantity": 10, "unit": "罐"}
                ],
                "people_count": 4,
                "special_needs": "家中有老人和小孩"
            },
            urgency_level=4,
            contact_info={
                "phone": "0912345678",
                "notes": "請於上午聯絡"
            }
        )
        
        self.db.add(self.test_need)
        self.db.commit()
        
        # 建立認證 token
        self.victim_token = create_access_token(data={"sub": str(self.victim_user.id)})
        self.volunteer_token = create_access_token(data={"sub": str(self.volunteer_user.id)})
        self.admin_token = create_access_token(data={"sub": str(self.admin_user.id)})
    
    def test_create_need_success(self):
        """測試成功建立需求"""
        need_data = {
            "title": "醫療協助需求",
            "description": "需要醫療人員協助檢查",
            "need_type": "medical",
            "location_data": {
                "address": "花蓮縣光復鄉民族路456號",
                "coordinates": {"lat": 23.5800, "lng": 121.4300},
                "details": "二樓住戶"
            },
            "requirements": {
                "people_count": 1,
                "medical_conditions": "高血壓患者",
                "special_needs": "需要血壓計檢查"
            },
            "urgency_level": 3,
            "contact_info": {
                "phone": "0987654321",
                "notes": "請於下午聯絡"
            }
        }
        
        response = client.post(
            "/api/v1/needs/",
            json=need_data,
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == need_data["title"]
        assert data["need_type"] == need_data["need_type"]
        assert data["status"] == "open"
        assert data["reporter_id"] == str(self.victim_user.id)
    
    def test_create_need_unauthorized(self):
        """測試非受災戶建立需求被拒絕"""
        need_data = {
            "title": "測試需求",
            "description": "測試描述",
            "need_type": "food",
            "location_data": {
                "address": "測試地址",
                "coordinates": {"lat": 23.5731, "lng": 121.4208}
            },
            "requirements": {
                "people_count": 1
            },
            "urgency_level": 1
        }
        
        response = client.post(
            "/api/v1/needs/",
            json=need_data,
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "權限不足" in response.json()["detail"]
    
    def test_get_needs_list(self):
        """測試取得需求列表"""
        response = client.get(
            "/api/v1/needs/",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "needs" in data
        assert "total" in data
        assert len(data["needs"]) > 0
        assert data["needs"][0]["id"] == str(self.test_need.id)
    
    def test_get_needs_list_victim_filter(self):
        """測試受災戶只能看到自己的需求"""
        response = client.get(
            "/api/v1/needs/",
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["needs"]) == 1
        assert data["needs"][0]["reporter_id"] == str(self.victim_user.id)
    
    def test_get_need_by_id(self):
        """測試取得特定需求詳情"""
        response = client.get(
            f"/api/v1/needs/{self.test_need.id}",
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(self.test_need.id)
        assert data["title"] == self.test_need.title
        assert data["need_type"] == self.test_need.need_type
    
    def test_get_need_unauthorized(self):
        """測試無權限查看需求"""
        response = client.get(
            f"/api/v1/needs/{self.test_need.id}",
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "權限不足" in response.json()["detail"]
    
    def test_update_need_success(self):
        """測試成功更新需求"""
        update_data = {
            "title": "更新後的需求標題",
            "urgency_level": 5
        }
        
        response = client.put(
            f"/api/v1/needs/{self.test_need.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["urgency_level"] == update_data["urgency_level"]
    
    def test_update_need_status_admin(self):
        """測試管理員更新需求狀態"""
        status_data = {
            "status": "assigned",
            "notes": "已分配給志工處理"
        }
        
        response = client.put(
            f"/api/v1/needs/{self.test_need.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == status_data["status"]
    
    def test_assign_need_success(self):
        """測試成功分配需求"""
        assignment_data = {
            "assigned_to": str(self.volunteer_user.id),
            "notes": "分配給經驗豐富的志工"
        }
        
        response = client.post(
            f"/api/v1/needs/{self.test_need.id}/assign",
            json=assignment_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == assignment_data["assigned_to"]
        assert data["status"] == "assigned"
    
    def test_assign_need_unauthorized(self):
        """測試無權限分配需求"""
        assignment_data = {
            "assigned_to": str(self.volunteer_user.id)
        }
        
        response = client.post(
            f"/api/v1/needs/{self.test_need.id}/assign",
            json=assignment_data,
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "權限不足" in response.json()["detail"]
    
    def test_get_open_needs(self):
        """測試取得待處理需求列表"""
        response = client.get(
            "/api/v1/needs/open",
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all(need["status"] == "open" for need in data)
    
    def test_get_urgent_needs(self):
        """測試取得緊急需求列表"""
        response = client.get(
            "/api/v1/needs/urgent?urgency_threshold=3",
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 檢查返回的需求緊急程度都 >= 3
        assert all(need["urgency_level"] >= 3 for need in data)
    
    def test_get_nearby_needs(self):
        """測試取得附近需求列表"""
        response = client.get(
            "/api/v1/needs/nearby?center_lat=23.5731&center_lng=121.4208&radius_km=10",
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_my_needs_victim(self):
        """測試受災戶取得自己的需求"""
        response = client.get(
            "/api/v1/needs/my",
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["reporter_id"] == str(self.victim_user.id)
    
    def test_get_my_needs_volunteer(self):
        """測試志工取得分配給自己的需求"""
        # 先分配需求給志工
        self.test_need.assigned_to = self.volunteer_user.id
        self.test_need.status = NeedStatus.ASSIGNED.value
        self.db.commit()
        
        response = client.get(
            "/api/v1/needs/my",
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["assigned_to"] == str(self.volunteer_user.id)
    
    def test_get_need_statistics(self):
        """測試取得需求統計資料"""
        response = client.get(
            "/api/v1/needs/statistics",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_needs" in data
        assert "needs_by_type" in data
        assert "needs_by_status" in data
        assert "open_needs" in data
        assert data["total_needs"] > 0
    
    def test_get_need_assignments(self):
        """測試取得需求分配記錄"""
        response = client.get(
            f"/api/v1/needs/{self.test_need.id}/assignments",
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_delete_need_success(self):
        """測試成功刪除需求"""
        response = client.delete(
            f"/api/v1/needs/{self.test_need.id}",
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        assert "刪除成功" in response.json()["message"]
    
    def test_delete_need_unauthorized(self):
        """測試無權限刪除需求"""
        response = client.delete(
            f"/api/v1/needs/{self.test_need.id}",
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "權限不足" in response.json()["detail"]
    
    def test_search_needs_by_type(self):
        """測試按類型搜尋需求"""
        response = client.get(
            "/api/v1/needs/?need_type=food",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(need["need_type"] == "food" for need in data["needs"])
    
    def test_search_needs_by_urgency(self):
        """測試按緊急程度搜尋需求"""
        response = client.get(
            "/api/v1/needs/?urgency_level=4",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(need["urgency_level"] == 4 for need in data["needs"])
    
    def test_search_needs_by_title(self):
        """測試按標題搜尋需求"""
        response = client.get(
            "/api/v1/needs/?title=食物",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all("食物" in need["title"] for need in data["needs"])
    
    def test_pagination(self):
        """測試分頁功能"""
        response = client.get(
            "/api/v1/needs/?skip=0&limit=1",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["needs"]) <= 1
        assert data["skip"] == 0
        assert data["limit"] == 1
        assert "total" in data
    
    def test_invalid_need_id(self):
        """測試無效的需求 ID"""
        response = client.get(
            "/api/v1/needs/invalid-id",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]
    
    def test_create_need_invalid_data(self):
        """測試建立需求時資料驗證失敗"""
        invalid_data = {
            "title": "",  # 空標題
            "description": "測試描述",
            "need_type": "invalid_type",  # 無效類型
            "urgency_level": 10  # 超出範圍
        }
        
        response = client.post(
            "/api/v1/needs/",
            json=invalid_data,
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 422  # Validation error