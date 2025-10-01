"""
需求狀態管理測試
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
from app.services.need_service import need_service
from app.crud.need import need_crud
from app.schemas.need import NeedStatusUpdate, NeedAssignment as NeedAssignmentSchema
from tests.conftest import TestingSessionLocal, override_get_db

# 覆蓋資料庫依賴
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestNeedStatusManagement:
    """需求狀態管理測試類"""
    
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
            NeedTypeModel(type="medical", display_name="醫療需求")
        ]
        need_statuses = [
            NeedStatusModel(status="open", display_name="待處理"),
            NeedStatusModel(status="assigned", display_name="已分配"),
            NeedStatusModel(status="in_progress", display_name="處理中"),
            NeedStatusModel(status="resolved", display_name="已解決")
        ]
        
        self.db.add_all(need_types + need_statuses)
        self.db.commit()
        
        # 建立測試需求
        self.test_need = Need(
            reporter_id=self.victim_user.id,
            title="測試需求",
            description="測試需求描述",
            need_type=NeedType.FOOD.value,
            status=NeedStatus.OPEN.value,
            location_data={
                "address": "測試地址",
                "coordinates": {"lat": 23.5731, "lng": 121.4208}
            },
            requirements={
                "items": [{"name": "白米", "quantity": 5}],
                "people_count": 2
            },
            urgency_level=3
        )
        
        self.db.add(self.test_need)
        self.db.commit()
        
        # 建立認證 token
        self.victim_token = create_access_token(subject=str(self.victim_user.id))
        self.volunteer_token = create_access_token(subject=str(self.volunteer_user.id))
        self.admin_token = create_access_token(subject=str(self.admin_user.id))
    
    def test_update_need_status_success(self):
        """測試成功更新需求狀態"""
        status_data = {
            "status": "in_progress",
            "notes": "開始處理需求"
        }
        
        response = client.put(
            f"/api/v1/needs/{self.test_need.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
    
    def test_assign_need_to_volunteer_success(self):
        """測試成功分配需求給志工"""
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
        assert data["assigned_to"] == str(self.volunteer_user.id)
        assert data["status"] == "assigned"
    
    def test_complete_need_success(self):
        """測試成功完成需求"""
        # 先分配需求
        assignment_data = NeedAssignmentSchema(
            assigned_to=self.volunteer_user.id
        )
        need_crud.assign_to_user(self.db, str(self.test_need.id), assignment_data)
        
        response = client.post(
            f"/api/v1/needs/{self.test_need.id}/complete",
            params={"completion_notes": "需求已成功完成"},
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None
    
    def test_reassign_need_success(self):
        """測試成功重新分配需求"""
        # 先分配給一個志工
        assignment_data = NeedAssignmentSchema(
            assigned_to=self.volunteer_user.id
        )
        need_crud.assign_to_user(self.db, str(self.test_need.id), assignment_data)
        
        # 建立另一個志工
        another_volunteer = User(
            email="volunteer2@test.com",
            name="另一個志工",
            password_hash="hashed_password",
            role=UserRole.VOLUNTEER.value,
            is_approved=True
        )
        self.db.add(another_volunteer)
        self.db.commit()
        
        # 重新分配
        reassignment_data = {
            "assigned_to": str(another_volunteer.id),
            "notes": "重新分配給其他志工"
        }
        
        response = client.post(
            f"/api/v1/needs/{self.test_need.id}/reassign",
            json=reassignment_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == str(another_volunteer.id)
    
    def test_get_available_needs_victim(self):
        """測試受災戶取得可用需求"""
        response = client.get(
            "/api/v1/needs/available",
            headers={"Authorization": f"Bearer {self.victim_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["reporter_id"] == str(self.victim_user.id)
    
    def test_get_available_needs_volunteer(self):
        """測試志工取得可用需求"""
        response = client.get(
            "/api/v1/needs/available",
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1  # 至少包含待處理的需求
    
    def test_get_need_status_summary(self):
        """測試取得需求狀態摘要"""
        response = client.get(
            "/api/v1/needs/status-summary",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_needs" in data
        assert "open_needs" in data
        assert "processing_rate" in data
        assert data["total_needs"] > 0
    
    def test_unauthorized_status_update(self):
        """測試無權限更新狀態"""
        status_data = {
            "status": "resolved",
            "notes": "嘗試無權限更新"
        }
        
        response = client.put(
            f"/api/v1/needs/{self.test_need.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {self.volunteer_token}"}
        )
        
        assert response.status_code == 403
        assert "權限不足" in response.json()["detail"]
    
    def test_unauthorized_assignment(self):
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
    
    def test_need_service_can_user_manage_need(self):
        """測試需求服務權限檢查"""
        # 管理員可以管理所有需求
        assert need_service.can_user_manage_need(
            UserRole.ADMIN, self.test_need, str(self.admin_user.id)
        ) == True
        
        # 需求報告者可以管理自己的需求
        assert need_service.can_user_manage_need(
            UserRole.VICTIM, self.test_need, str(self.victim_user.id)
        ) == True
        
        # 其他用戶不能管理不相關的需求
        assert need_service.can_user_manage_need(
            UserRole.VOLUNTEER, self.test_need, str(self.volunteer_user.id)
        ) == False
    
    def test_need_service_can_user_assign_need(self):
        """測試需求分配權限檢查"""
        # 管理員可以分配需求
        assert need_service.can_user_assign_need(UserRole.ADMIN) == True
        
        # 正式組織可以分配需求
        assert need_service.can_user_assign_need(UserRole.OFFICIAL_ORG) == True
        
        # 一般志工不能分配需求
        assert need_service.can_user_assign_need(UserRole.VOLUNTEER) == False
        
        # 受災戶不能分配需求
        assert need_service.can_user_assign_need(UserRole.VICTIM) == False
    
    def test_need_status_workflow(self):
        """測試完整的需求狀態流程"""
        need_id = str(self.test_need.id)
        
        # 1. 初始狀態為 open
        need = need_crud.get_by_id(self.db, need_id)
        assert need.status == NeedStatus.OPEN.value
        
        # 2. 分配給志工
        assignment_data = NeedAssignmentSchema(
            assigned_to=self.volunteer_user.id,
            notes="分配給志工處理"
        )
        assigned_need = need_crud.assign_to_user(self.db, need_id, assignment_data)
        assert assigned_need.status == NeedStatus.ASSIGNED.value
        assert assigned_need.assigned_to == self.volunteer_user.id
        
        # 3. 更新為處理中
        status_data = NeedStatusUpdate(
            status=NeedStatus.IN_PROGRESS,
            notes="開始處理需求"
        )
        in_progress_need = need_crud.update_status(self.db, need_id, status_data)
        assert in_progress_need.status == NeedStatus.IN_PROGRESS.value
        
        # 4. 完成需求
        resolved_status = NeedStatusUpdate(
            status=NeedStatus.RESOLVED,
            notes="需求已完成"
        )
        resolved_need = need_crud.update_status(self.db, need_id, resolved_status)
        assert resolved_need.status == NeedStatus.RESOLVED.value
        assert resolved_need.resolved_at is not None
    
    def test_invalid_need_id(self):
        """測試無效的需求 ID"""
        response = client.get(
            "/api/v1/needs/invalid-id",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]
    
    def test_assign_to_nonexistent_user(self):
        """測試分配給不存在的用戶"""
        assignment_data = {
            "assigned_to": "nonexistent-user-id"
        }
        
        response = client.post(
            f"/api/v1/needs/{self.test_need.id}/assign",
            json=assignment_data,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        assert response.status_code == 400
        assert "不存在" in response.json()["detail"]