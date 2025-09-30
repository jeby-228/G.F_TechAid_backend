"""
任務管理 CRUD 測試
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.crud.task import task_crud
from app.models.task import Task, TaskClaim
from app.models.user import User
from app.schemas.task import TaskCreate, TaskSearchQuery, LocationData
from app.utils.constants import UserRole, TaskType, TaskStatus
from tests.conftest import create_test_user, create_test_task


class TestTaskCRUD:
    """任務 CRUD 測試類"""
    
    def test_create_task_official_org(self, db_session: Session):
        """測試正式組織建立任務"""
        user = create_test_user(db_session, role=UserRole.OFFICIAL_ORG)
        
        task_data = TaskCreate(
            title="災後清理工作",
            description="清理災區垃圾和雜物",
            task_type=TaskType.CLEANUP,
            location_data=LocationData(
                address="花蓮縣光復鄉中正路123號",
                coordinates={"lat": 23.5731, "lng": 121.4208},
                details="學校操場"
            ),
            required_volunteers=10,
            required_skills=["體力勞動", "垃圾分類"],
            priority_level=3
        )
        
        task = task_crud.create_task(db_session, task_data, str(user.id), user.role)
        
        assert task.title == task_data.title
        assert task.status == TaskStatus.AVAILABLE.value
        assert task.approval_status == "approved"
        assert task.creator_id == user.id
    
    def test_create_task_unofficial_org(self, db_session: Session):
        """測試非正式組織建立任務需要審核"""
        user = create_test_user(db_session, role=UserRole.UNOFFICIAL_ORG)
        
        task_data = TaskCreate(
            title="社區互助任務",
            description="協助社區居民搬運物資",
            task_type=TaskType.SUPPLY_DELIVERY,
            location_data=LocationData(
                address="花蓮縣光復鄉民族街456號",
                coordinates={"lat": 23.5800, "lng": 121.4300},
                details="社區活動中心"
            ),
            required_volunteers=5,
            priority_level=2
        )
        
        task = task_crud.create_task(db_session, task_data, str(user.id), user.role)
        
        assert task.title == task_data.title
        assert task.status == TaskStatus.PENDING.value
        assert task.approval_status == "pending"
    
    def test_get_tasks_with_role_filtering(self, db_session: Session):
        """測試基於角色的任務列表篩選"""
        # 建立不同角色的用戶
        admin = create_test_user(db_session, role=UserRole.ADMIN, email="admin@test.com")
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        victim = create_test_user(db_session, role=UserRole.VICTIM, email="victim@test.com")
        
        # 建立不同狀態的任務
        available_task = create_test_task(db_session, status=TaskStatus.AVAILABLE)
        pending_task = create_test_task(db_session, status=TaskStatus.PENDING, approval_status="pending")
        
        # 管理員可以看到所有任務
        admin_tasks, admin_total = task_crud.get_tasks(
            db_session, user_role=admin.role, user_id=str(admin.id)
        )
        assert admin_total >= 2
        
        # 志工只能看到可認領的任務
        volunteer_tasks, volunteer_total = task_crud.get_tasks(
            db_session, user_role=volunteer.role, user_id=str(volunteer.id)
        )
        task_statuses = [task.status for task in volunteer_tasks]
        assert TaskStatus.AVAILABLE.value in task_statuses
        assert TaskStatus.PENDING.value not in task_statuses
        
        # 受災戶只能看到可認領的任務
        victim_tasks, victim_total = task_crud.get_tasks(
            db_session, user_role=victim.role, user_id=str(victim.id)
        )
        task_statuses = [task.status for task in victim_tasks]
        assert TaskStatus.AVAILABLE.value in task_statuses
    
    def test_claim_task_success(self, db_session: Session):
        """測試成功認領任務"""
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE, required_volunteers=5)
        
        claim = task_crud.claim_task(db_session, str(task.id), str(user.id), "我有相關經驗")
        
        assert claim.task_id == task.id
        assert claim.user_id == user.id
        assert claim.status == "claimed"
        assert claim.notes == "我有相關經驗"
        
        # 檢查任務狀態未改變（因為還沒滿員）
        db_session.refresh(task)
        assert task.status == TaskStatus.AVAILABLE.value
    
    def test_claim_task_full_capacity(self, db_session: Session):
        """測試任務滿員時的狀態變更"""
        user1 = create_test_user(db_session, role=UserRole.VOLUNTEER, email="user1@test.com")
        user2 = create_test_user(db_session, role=UserRole.VOLUNTEER, email="user2@test.com")
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE, required_volunteers=2)
        
        # 第一個志工認領
        claim1 = task_crud.claim_task(db_session, str(task.id), str(user1.id))
        db_session.refresh(task)
        assert task.status == TaskStatus.AVAILABLE.value
        
        # 第二個志工認領，任務應該變為已認領狀態
        claim2 = task_crud.claim_task(db_session, str(task.id), str(user2.id))
        db_session.refresh(task)
        assert task.status == TaskStatus.CLAIMED.value
    
    def test_claim_task_conflicts(self, db_session: Session):
        """測試任務認領衝突檢查"""
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE)
        
        # 第一次認領成功
        claim1 = task_crud.claim_task(db_session, str(task.id), str(user.id))
        assert claim1.status == "claimed"
        
        # 第二次認領應該失敗
        with pytest.raises(HTTPException) as exc_info:
            task_crud.claim_task(db_session, str(task.id), str(user.id))
        assert exc_info.value.status_code == 400
        assert "已認領" in str(exc_info.value.detail)
    
    def test_claim_task_capacity_exceeded(self, db_session: Session):
        """測試超過認領人數限制"""
        user1 = create_test_user(db_session, role=UserRole.VOLUNTEER, email="user1@test.com")
        user2 = create_test_user(db_session, role=UserRole.VOLUNTEER, email="user2@test.com")
        user3 = create_test_user(db_session, role=UserRole.VOLUNTEER, email="user3@test.com")
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE, required_volunteers=2)
        
        # 前兩個志工認領成功
        task_crud.claim_task(db_session, str(task.id), str(user1.id))
        task_crud.claim_task(db_session, str(task.id), str(user2.id))
        
        # 第三個志工認領應該失敗
        with pytest.raises(HTTPException) as exc_info:
            task_crud.claim_task(db_session, str(task.id), str(user3.id))
        assert exc_info.value.status_code == 400
        assert "人數已滿" in str(exc_info.value.detail)
    
    def test_update_claim_status(self, db_session: Session):
        """測試更新認領狀態"""
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE)
        
        # 認領任務
        claim = task_crud.claim_task(db_session, str(task.id), str(user.id))
        
        # 更新為開始執行
        updated_claim = task_crud.update_claim_status(
            db_session, str(claim.id), "started", str(user.id), "開始執行任務"
        )
        assert updated_claim.status == "started"
        assert updated_claim.started_at is not None
        assert updated_claim.notes == "開始執行任務"
        
        # 更新為已完成
        completed_claim = task_crud.update_claim_status(
            db_session, str(claim.id), "completed", str(user.id), "任務完成"
        )
        assert completed_claim.status == "completed"
        assert completed_claim.completed_at is not None
    
    def test_get_task_history(self, db_session: Session):
        """測試獲取任務歷史記錄"""
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        task1 = create_test_task(db_session, title="任務1")
        task2 = create_test_task(db_session, title="任務2")
        
        # 認領兩個任務
        claim1 = task_crud.claim_task(db_session, str(task1.id), str(user.id))
        claim2 = task_crud.claim_task(db_session, str(task2.id), str(user.id))
        
        # 完成第一個任務
        task_crud.update_claim_status(db_session, str(claim1.id), "completed", str(user.id))
        
        # 獲取歷史記錄
        history, total = task_crud.get_task_history(db_session, str(user.id))
        
        assert total == 2
        assert len(history) == 2
        
        # 測試狀態篩選
        completed_history, completed_total = task_crud.get_task_history(
            db_session, str(user.id), status_filter="completed"
        )
        assert completed_total == 1
        assert completed_history[0].status == "completed"
    
    def test_get_task_activity_log(self, db_session: Session):
        """測試獲取任務活動日誌"""
        creator = create_test_user(db_session, role=UserRole.OFFICIAL_ORG, email="creator@test.com")
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        
        # 建立任務
        task = create_test_task(db_session, creator_id=str(creator.id))
        
        # 認領任務
        claim = task_crud.claim_task(db_session, str(task.id), str(volunteer.id))
        
        # 更新狀態
        task_crud.update_claim_status(db_session, str(claim.id), "started", str(volunteer.id))
        task_crud.update_claim_status(db_session, str(claim.id), "completed", str(volunteer.id))
        
        # 獲取活動日誌
        activity_log = task_crud.get_task_activity_log(db_session, str(task.id))
        
        assert len(activity_log) >= 4  # 建立、認領、開始、完成
        
        actions = [log["action"] for log in activity_log]
        assert "task_created" in actions
        assert "task_claimed" in actions
        assert "task_started" in actions
        assert "task_completed" in actions
    
    def test_check_task_conflicts(self, db_session: Session):
        """測試任務衝突檢查"""
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        
        # 測試不存在的任務
        conflicts = task_crud.check_task_conflicts(db_session, "non-existent-id", str(user.id))
        assert conflicts["has_conflicts"] is True
        assert "任務不存在" in conflicts["conflicts"]
        
        # 測試正常任務
        task = create_test_task(db_session, status=TaskStatus.AVAILABLE)
        conflicts = task_crud.check_task_conflicts(db_session, str(task.id), str(user.id))
        assert conflicts["has_conflicts"] is False
        
        # 認領任務後再次檢查
        task_crud.claim_task(db_session, str(task.id), str(user.id))
        conflicts = task_crud.check_task_conflicts(db_session, str(task.id), str(user.id))
        assert conflicts["has_conflicts"] is True
        assert "已認領" in " ".join(conflicts["conflicts"])
    
    def test_search_tasks_by_location(self, db_session: Session):
        """測試基於地理位置的任務搜尋"""
        user = create_test_user(db_session, role=UserRole.VOLUNTEER)
        
        # 建立不同位置的任務
        task1 = create_test_task(
            db_session, 
            title="近距離任務",
            location_data={"address": "花蓮縣光復鄉", "coordinates": {"lat": 23.5731, "lng": 121.4208}}
        )
        task2 = create_test_task(
            db_session,
            title="遠距離任務", 
            location_data={"address": "台北市", "coordinates": {"lat": 25.0330, "lng": 121.5654}}
        )
        
        # 搜尋光復鄉附近 50 公里內的任務
        search_query = TaskSearchQuery(
            center_lat=23.5731,
            center_lng=121.4208,
            location_radius=50.0
        )
        
        tasks, total = task_crud.get_tasks(
            db_session, search_query=search_query, user_role=user.role, user_id=str(user.id)
        )
        
        # 應該只找到近距離任務
        task_titles = [task.title for task in tasks]
        assert "近距離任務" in task_titles
        # 台北距離光復鄉超過 50 公里，不應該出現
        assert "遠距離任務" not in task_titles

