"""
任務管理 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.task import Task, TaskClaim
from app.utils.constants import UserRole, TaskType, TaskStatus
from tests.conftest import create_test_user, create_test_task


class TestTaskAPI:
    """任務 API 測試類"""
    
    def test_create_task_official_org(self, client: TestClient, db_session: Session):
        """測試正式組織建立任務"""
        # 建立正式組織用戶
        user = create_test_user(db_session, role=UserRole.OFFICIAL_ORG)
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 建立任務資料
        task_data = {
            "title": "災後清理工作",
            "description": "清理災區垃圾和雜物",
            "task_type": "cleanup",
            "location_data": {
                "address": "花蓮縣光復鄉中正路123號",
                "coordinates": {"lat": 23.5731, "lng": 121.4208},
                "details": "學校操場"
            },
            "required_volunteers": 10,
            "required_skills": ["體力勞動", "垃圾分類"],
            "priority_level": 3
        }
        
        # 發送建立任務請求
        response = client.post("/api/v1/tasks/", json=task_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["status"] == "available"  # 正式組織任務直接可用
        assert data["approval_status"] == "approved"
        assert data["creator_id"] == str(user.id)
    
    def test_create_task_unofficial_org(self, client: TestClient, db_session: Session):
        """測試非正式組織建立任務需要審核"""
        # 建立非正式組織用戶
        user = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG)
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
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
    
    def test_create_task_victim_forbidden(self, client: TestClient, db_session: Session):
        """測試受災戶無法建立任務"""
        # 建立受災戶用戶
        user = create_test_user(db_session, role=UserRole.VICTIM)
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 建立任務資料
        task_data = {
            "title": "測試任務",
            "description": "測試描述",
            "task_type": "cleanup",
            "location_data": {
                "address": "測試地址",
                "coordinates": {"lat": 23.5731, "lng": 121.4208}
            },
            "required_volunteers": 1,
            "priority_level": 1
        }
        
        # 發送建立任務請求
        response = client.post("/api/v1/tasks/", json=task_data, headers=headers)
        
        assert response.status_code == 403
        assert "受災戶無法建立任務" in response.json()["detail"]    

    def test_get_tasks_list(self, client: TestClient, db_session: Session):
        """測試獲取任務列表"""
        # 建立測試用戶和任務
        user = create_test_user(db_session, role=UserRole.OFFICIAL_ORG)
        task = create_test_task(db_session, creator_id=str(user.id))
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 獲取任務列表
        response = client.get("/api/v1/tasks/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["tasks"]) >= 1
        assert data["tasks"][0]["id"] == str(task.id)
    
    def test_get_task_by_id(self, client: TestClient, db_session: Session):
        """測試根據 ID 獲取任務"""
        # 建立測試用戶和任務
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session, creator_id=str(user.id))
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 獲取特定任務
        response = client.get(f"/api/v1/tasks/{task.id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(task.id)
        assert data["title"] == task.title
    
    def test_claim_task(self, client: TestClient, db_session: Session):
        """測試認領任務"""
        # 建立任務建立者和志工
        creator = create_test_user(db_session, role=UserRole.OFFICIAL_ORG, email="creator@test.com")
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        
        # 建立可認領任務
        task = create_test_task(db_session, creator_id=str(creator.id), status=TaskStatus.AVAILABLE)
        
        # 志工登入
        login_response = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 認領任務
        claim_data = {
            "task_id": str(task.id),
            "notes": "我有相關經驗，可以協助完成此任務"
        }
        
        response = client.post("/api/v1/tasks/claim", json=claim_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(task.id)
        assert data["user_id"] == str(volunteer.id)
        assert data["status"] == "claimed"
    
    def test_get_my_claims(self, client: TestClient, db_session: Session):
        """測試獲取我的認領記錄"""
        # 建立用戶和任務
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session)
        
        # 建立認領記錄
        claim = TaskClaim(
            task_id=task.id,
            user_id=user.id,
            status="claimed",
            notes="測試認領"
        )
        db_session.add(claim)
        db_session.commit()
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 獲取認領記錄
        response = client.get("/api/v1/tasks/claims/my", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["claims"]) >= 1
    
    def test_get_available_tasks(self, client: TestClient, db_session: Session):
        """測試獲取可認領任務列表"""
        # 建立用戶
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        
        # 建立不同狀態的任務
        available_task = create_test_task(db_session, title="可認領任務", status=TaskStatus.AVAILABLE)
        claimed_task = create_test_task(db_session, title="已認領任務", status=TaskStatus.CLAIMED)
        
        # 登入獲取 token
        login_response = client.post("/api/v1/auth/login", json={
            "email": user.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 獲取可認領任務
        response = client.get("/api/v1/tasks/available", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 檢查只返回可認領的任務
        task_titles = [task["title"] for task in data["tasks"]]
        assert "可認領任務" in task_titles
        assert "已認領任務" not in task_titles
    
    def test_claim_task_conflict_handling(self, client: TestClient, db_session: Session):
        """測試任務認領衝突處理"""
        # 建立任務建立者和兩個志工
        creator = create_test_user(db_session, role=UserRole.OFFICIAL_ORG, email="creator@test.com")
        volunteer1 = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer1@test.com")
        volunteer2 = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer2@test.com")
        
        # 建立只需要一個志工的任務
        task = create_test_task(db_session, creator_id=str(creator.id), required_volunteers=1)
        
        # 第一個志工登入並認領任務
        login_response1 = client.post("/api/v1/auth/login", json={
            "email": volunteer1.email,
            "password": "testpassword123"
        })
        token1 = login_response1.json()["token"]["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        claim_data = {
            "task_id": str(task.id),
            "notes": "我要認領這個任務"
        }
        
        response1 = client.post("/api/v1/tasks/claim", json=claim_data, headers=headers1)
        assert response1.status_code == 201
        
        # 第二個志工嘗試認領同一個任務，應該失敗
        login_response2 = client.post("/api/v1/auth/login", json={
            "email": volunteer2.email,
            "password": "testpassword123"
        })
        token2 = login_response2.json()["token"]["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        response2 = client.post("/api/v1/tasks/claim", json=claim_data, headers=headers2)
        assert response2.status_code == 400
        assert "人數已滿" in response2.json()["detail"]
    
    def test_update_claim_status_workflow(self, client: TestClient, db_session: Session):
        """測試認領狀態更新工作流程"""
        # 建立用戶和任務
        creator = create_test_user(db_session, role=UserRole.OFFICIAL_ORG, email="creator@test.com")
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        task = create_test_task(db_session, creator_id=str(creator.id))
        
        # 志工登入
        login_response = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 認領任務
        claim_data = {"task_id": str(task.id), "notes": "我要認領"}
        claim_response = client.post("/api/v1/tasks/claim", json=claim_data, headers=headers)
        assert claim_response.status_code == 201
        claim_id = claim_response.json()["id"]
        
        # 更新為開始執行
        status_update = {"status": "started", "notes": "開始執行任務"}
        start_response = client.put(f"/api/v1/tasks/claims/{claim_id}/status", json=status_update, headers=headers)
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "started"
        
        # 更新為已完成
        status_update = {"status": "completed", "notes": "任務完成"}
        complete_response = client.put(f"/api/v1/tasks/claims/{claim_id}/status", json=status_update, headers=headers)
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "completed"
    
    def test_get_task_history(self, client: TestClient, db_session: Session):
        """測試獲取任務歷史記錄"""
        # 建立用戶和任務
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task1 = create_test_task(db_session, title="歷史任務1")
        task2 = create_test_task(db_session, title="歷史任務2")
        
        # 志工登入
        login_response = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 認領兩個任務
        client.post("/api/v1/tasks/claim", json={"task_id": str(task1.id)}, headers=headers)
        client.post("/api/v1/tasks/claim", json={"task_id": str(task2.id)}, headers=headers)
        
        # 獲取任務歷史
        response = client.get("/api/v1/tasks/history/my", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["claims"]) == 2
        
        # 檢查任務標題
        task_titles = [claim["task_title"] for claim in data["claims"]]
        assert "歷史任務1" in task_titles
        assert "歷史任務2" in task_titles
    
    def test_get_task_activity_log(self, client: TestClient, db_session: Session):
        """測試獲取任務活動日誌"""
        # 建立用戶和任務
        creator = create_test_user(db_session, role=UserRole.OFFICIAL_ORG, email="creator@test.com")
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        task = create_test_task(db_session, creator_id=str(creator.id))
        
        # 建立者登入
        login_response = client.post("/api/v1/auth/login", json={
            "email": creator.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 志工認領任務
        volunteer_login = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        volunteer_token = volunteer_login.json()["token"]["access_token"]
        volunteer_headers = {"Authorization": f"Bearer {volunteer_token}"}
        
        claim_response = client.post("/api/v1/tasks/claim", json={"task_id": str(task.id)}, headers=volunteer_headers)
        claim_id = claim_response.json()["id"]
        
        # 更新任務狀態
        client.put(f"/api/v1/tasks/claims/{claim_id}/status", 
                  json={"status": "completed", "notes": "任務完成"}, 
                  headers=volunteer_headers)
        
        # 獲取活動日誌
        response = client.get(f"/api/v1/tasks/{task.id}/activity-log", headers=headers)
        
        assert response.status_code == 200
        activity_log = response.json()
        assert len(activity_log) >= 3  # 建立、認領、完成
        
        actions = [log["action"] for log in activity_log]
        assert "task_created" in actions
        assert "task_claimed" in actions
        assert "task_completed" in actions
    
    def test_check_task_conflicts_api(self, client: TestClient, db_session: Session):
        """測試任務衝突檢查 API"""
        # 建立用戶和任務
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE)
        
        # 志工登入
        login_response = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 檢查衝突（應該沒有衝突）
        response = client.get(f"/api/v1/tasks/{task.id}/conflicts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_conflicts"] is False
        assert len(data["conflicts"]) == 0
        
        # 認領任務
        client.post("/api/v1/tasks/claim", json={"task_id": str(task.id)}, headers=headers)
        
        # 再次檢查衝突（應該有衝突）
        response = client.get(f"/api/v1/tasks/{task.id}/conflicts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_conflicts"] is True
        assert len(data["conflicts"]) > 0
        assert any("已認領" in conflict for conflict in data["conflicts"])
    
    def test_role_based_task_access(self, client: TestClient, db_session: Session):
        """測試基於角色的任務存取權限"""
        # 建立不同角色的用戶
        admin = create_test_user(db_session, role=UserRole.ADMIN, email="admin@test.com")
        victim = create_test_user(db_session, role=UserRole.VICTIM, email="victim@test.com")
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        unofficial_org = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG, email="unofficial@test.com")
        
        # 建立不同狀態的任務
        available_task = create_test_task(db_session, title="可認領任務", status=TaskStatus.AVAILABLE)
        pending_task = create_test_task(db_session, title="待審核任務", status=TaskStatus.PENDING, approval_status="pending")
        
        # 測試受災戶權限
        victim_login = client.post("/api/v1/auth/login", json={
            "email": victim.email,
            "password": "testpassword123"
        })
        victim_token = victim_login.json()["token"]["access_token"]
        victim_headers = {"Authorization": f"Bearer {victim_token}"}
        
        victim_response = client.get("/api/v1/tasks/", headers=victim_headers)
        assert victim_response.status_code == 200
        victim_tasks = victim_response.json()["tasks"]
        victim_titles = [task["title"] for task in victim_tasks]
        assert "可認領任務" in victim_titles
        assert "待審核任務" not in victim_titles  # 受災戶看不到待審核任務
        
        # 測試管理員權限
        admin_login = client.post("/api/v1/auth/login", json={
            "email": admin.email,
            "password": "testpassword123"
        })
        admin_token = admin_login.json()["token"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        admin_response = client.get("/api/v1/tasks/", headers=admin_headers)
        assert admin_response.status_code == 200
        admin_tasks = admin_response.json()["tasks"]
        admin_titles = [task["title"] for task in admin_tasks]
        assert "可認領任務" in admin_titles
        assert "待審核任務" in admin_titles  # 管理員可以看到所有任務
    
    def test_task_claiming_by_id_endpoint(self, client: TestClient, db_session: Session):
        """測試通過任務 ID 認領任務的端點"""
        # 建立用戶和任務
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE)
        
        # 志工登入
        login_response = client.post("/api/v1/auth/login", json={
            "email": volunteer.email,
            "password": "testpassword123"
        })
        token = login_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 通過任務 ID 認領任務
        response = client.post(f"/api/v1/tasks/{task.id}/claim", 
                              json={"notes": "通過 ID 認領"}, 
                              headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(task.id)
        assert data["user_id"] == str(volunteer.id)
        assert data["notes"] == "通過 ID 認領"