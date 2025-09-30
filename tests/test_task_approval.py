"""
任務審核功能測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.utils.constants import UserRole, TaskStatus
from tests.conftest import create_test_user, create_test_task


class TestTaskApproval:
    """任務審核測試類"""
    
    def test_unofficial_org_task_needs_approval(self, client: TestClient, db_session: Session):
        """測試非正式組織建立的任務需要審核"""
        # 建立非正式組織用戶
        unofficial_org = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG)
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": unofficial_org.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 建立任務資料
        task_data = {
            "title": "社區互助任務",
            "description": "協助社區居民搬運物資",
            "task_type": "supply_delivery",
            "location_data": {
                "address": "花蓮縣光復鄉民族街456號",
                "coordinates": {"lat": 23.5800, "lng": 121.4300},
                "details": "社區活動中心"
            },
            "required_volunteers": 5,
            "priority_level": 2
        }
        
        # 發送建立任務請求
        response = client.post("/api/v1/tasks/", json=task_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["status"] == "pending"  # 非正式組織任務需要審核
        assert data["approval_status"] == "pending"
        
        return data["id"]  # 返回任務 ID 供其他測試使用
    
    def test_admin_approve_task(self, client: TestClient, db_session: Session):
        """測試管理員審核通過任務"""
        # 建立管理員和非正式組織用戶
        admin = create_test_user(db_session, role=UserRole.ADMIN, email="admin@test.com")
        unofficial_org = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG, email="unofficial@test.com")
        
        # 非正式組織建立任務
        task = create_test_task(
            db_session, 
            creator_id=str(unofficial_org.id),
            status=TaskStatus.PENDING,
            approval_status="pending"
        )
        
        # 管理員登入
        admin_login = client.post("/api/v1/auth/login", json={
            "email": admin.email,
            "password": "testpassword123"
        })
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 審核通過任務
        approval_data = {
            "approved": True,
            "notes": "任務內容符合規範，審核通過"
        }
        
        response = client.post(f"/api/v1/tasks/{task.id}/approve", json=approval_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"
        assert data["status"] == "available"  # 審核通過後變為可認領
        assert data["approved_by"] == str(admin.id)
        assert data["approver_name"] == admin.name
    
    def test_admin_reject_task(self, client: TestClient, db_session: Session):
        """測試管理員拒絕任務"""
        # 建立管理員和非正式組織用戶
        admin = create_test_user(db_session, role=UserRole.ADMIN, email="admin@test.com")
        unofficial_org = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG, email="unofficial@test.com")
        
        # 非正式組織建立任務
        task = create_test_task(
            db_session, 
            creator_id=str(unofficial_org.id),
            status=TaskStatus.PENDING,
            approval_status="pending"
        )
        
        # 管理員登入
        admin_login = client.post("/api/v1/auth/login", json={
            "email": admin.email,
            "password": "testpassword123"
        })
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 拒絕任務
        approval_data = {
            "approved": False,
            "notes": "任務描述不夠詳細，請重新提交"
        }
        
        response = client.post(f"/api/v1/tasks/{task.id}/approve", json=approval_data, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "rejected"
        assert data["status"] == "cancelled"  # 拒絕後變為已取消
        assert data["approved_by"] == str(admin.id)
    
    def test_non_admin_cannot_approve(self, client: TestClient, db_session: Session):
        """測試非管理員無法審核任務"""
        # 建立志工和任務
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session, status=TaskStatus.PENDING, approval_status="pending")
        
        # 志工登入
        volunteer_login = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        volunteer_token = volunteer_login.json()["token"]["access_token"]
        volunteer_headers = {"Authorization": f"Bearer {volunteer_token}"}
        
        # 嘗試審核任務
        approval_data = {
            "approved": True,
            "notes": "我想審核這個任務"
        }
        
        response = client.post(f"/api/v1/tasks/{task.id}/approve", json=approval_data, headers=volunteer_headers)
        
        assert response.status_code == 403
        assert "只有管理員可以審核任務" in response.json()["detail"]
    
    def test_get_pending_approval_tasks(self, client: TestClient, db_session: Session):
        """測試獲取待審核任務列表"""
        # 建立管理員和非正式組織用戶
        admin = create_test_user(db_session, role=UserRole.ADMIN, email="admin@test.com")
        unofficial_org = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG, email="unofficial@test.com")
        
        # 建立待審核任務
        pending_task1 = create_test_task(
            db_session, 
            creator_id=str(unofficial_org.id),
            title="待審核任務1",
            status=TaskStatus.PENDING,
            approval_status="pending"
        )
        pending_task2 = create_test_task(
            db_session, 
            creator_id=str(unofficial_org.id),
            title="待審核任務2",
            status=TaskStatus.PENDING,
            approval_status="pending"
        )
        
        # 建立已審核任務（不應該出現在列表中）
        approved_task = create_test_task(
            db_session, 
            creator_id=str(unofficial_org.id),
            title="已審核任務",
            status=TaskStatus.AVAILABLE,
            approval_status="approved"
        )
        
        # 管理員登入
        admin_login = client.post("/api/v1/auth/login", json={
            "email": admin.email,
            "password": "testpassword123"
        })
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 獲取待審核任務列表
        response = client.get("/api/v1/tasks/pending-approval", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        
        # 檢查只返回待審核的任務
        task_titles = [task["title"] for task in data["tasks"]]
        assert "待審核任務1" in task_titles
        assert "待審核任務2" in task_titles
        assert "已審核任務" not in task_titles
        
        # 檢查所有任務都是待審核狀態
        for task in data["tasks"]:
            if task["title"] in ["待審核任務1", "待審核任務2"]:
                assert task["approval_status"] == "pending"
                assert task["status"] == "pending"
    
    def test_non_admin_cannot_view_pending_approval_tasks(self, client: TestClient, db_session: Session):
        """測試非管理員無法查看待審核任務列表"""
        # 建立志工用戶
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        
        # 志工登入
        volunteer_login = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        volunteer_token = volunteer_login.json()["token"]["access_token"]
        volunteer_headers = {"Authorization": f"Bearer {volunteer_token}"}
        
        # 嘗試獲取待審核任務列表
        response = client.get("/api/v1/tasks/pending-approval", headers=volunteer_headers)
        
        assert response.status_code == 403
        assert "只有管理員可以查看待審核任務" in response.json()["detail"]
    
    def test_approval_workflow_integration(self, client: TestClient, db_session: Session):
        """測試完整的審核工作流程"""
        # 建立用戶
        admin = create_test_user(db_session, role=UserRole.ADMIN, email="admin@test.com")
        unofficial_org = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG, email="unofficial@test.com")
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        
        # 1. 非正式組織建立任務
        unofficial_login = client.post("/api/v1/auth/login", json={
            "email": unofficial_org.email,
            "password": "testpassword123"
        })
        unofficial_token = unofficial_login.json()["token"]["access_token"]
        unofficial_headers = {"Authorization": f"Bearer {unofficial_token}"}
        
        task_data = {
            "title": "完整流程測試任務",
            "description": "測試從建立到審核到認領的完整流程",
            "task_type": "cleanup",
            "location_data": {
                "address": "花蓮縣光復鄉測試路123號",
                "coordinates": {"lat": 23.5731, "lng": 121.4208}
            },
            "required_volunteers": 2,
            "priority_level": 3
        }
        
        create_response = client.post("/api/v1/tasks/", json=task_data, headers=unofficial_headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        assert create_response.json()["status"] == "pending"
        
        # 2. 志工無法認領待審核任務
        volunteer_login = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        volunteer_token = volunteer_login.json()["token"]["access_token"]
        volunteer_headers = {"Authorization": f"Bearer {volunteer_token}"}
        
        claim_response = client.post("/api/v1/tasks/claim", json={
            "task_id": task_id,
            "notes": "我想認領這個任務"
        }, headers=volunteer_headers)
        assert claim_response.status_code == 400  # 應該失敗，因為任務還在待審核
        
        # 3. 管理員審核通過任務
        admin_login = client.post("/api/v1/auth/login", json={
            "email": admin.email,
            "password": "testpassword123"
        })
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        approve_response = client.post(f"/api/v1/tasks/{task_id}/approve", json={
            "approved": True,
            "notes": "審核通過"
        }, headers=admin_headers)
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "available"
        
        # 4. 志工現在可以認領任務
        claim_response = client.post("/api/v1/tasks/claim", json={
            "task_id": task_id,
            "notes": "現在可以認領了"
        }, headers=volunteer_headers)
        assert claim_response.status_code == 201
        assert claim_response.json()["task_id"] == task_id
        assert claim_response.json()["user_id"] == str(volunteer.id)
    
    def test_cannot_approve_already_approved_task(self, client: TestClient, db_session: Session):
        """測試無法重複審核已審核的任務"""
        # 建立管理員和已審核任務
        admin = create_test_user(db_session, role=UserRole.ADMIN)
        task = create_test_task(
            db_session, 
            status=TaskStatus.AVAILABLE,
            approval_status="approved"
        )
        
        # 管理員登入
        admin_login = client.post("/api/v1/auth/login", json={
            "email": admin.email,
            "password": "testpassword123"
        })
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 嘗試重複審核
        approval_data = {
            "approved": True,
            "notes": "重複審核"
        }
        
        response = client.post(f"/api/v1/tasks/{task.id}/approve", json=approval_data, headers=admin_headers)
        
        assert response.status_code == 400
        assert "不在待審核狀態" in response.json()["detail"]