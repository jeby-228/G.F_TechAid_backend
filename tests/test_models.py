"""
測試資料庫模型
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import *
import uuid


# 測試資料庫設定（使用 SQLite 記憶體資料庫）
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """建立測試資料庫會話"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


def test_user_role_model(db_session):
    """測試用戶角色模型"""
    # 建立用戶角色
    role = UserRole(
        role="test_role",
        display_name="測試角色",
        permissions={"test": True}
    )
    
    db_session.add(role)
    db_session.commit()
    
    # 查詢驗證
    saved_role = db_session.query(UserRole).filter_by(role="test_role").first()
    assert saved_role is not None
    assert saved_role.display_name == "測試角色"
    assert saved_role.permissions == {"test": True}


def test_user_model(db_session):
    """測試用戶模型"""
    # 先建立用戶角色
    role = UserRole(
        role="volunteer",
        display_name="志工",
        permissions={"claim_task": True}
    )
    db_session.add(role)
    db_session.commit()
    
    # 建立用戶
    user = User(
        email="test@example.com",
        name="測試用戶",
        password_hash="hashed_password",
        role="volunteer",
        is_approved=True
    )
    
    db_session.add(user)
    db_session.commit()
    
    # 查詢驗證
    saved_user = db_session.query(User).filter_by(email="test@example.com").first()
    assert saved_user is not None
    assert saved_user.name == "測試用戶"
    assert saved_user.role == "volunteer"
    assert saved_user.is_approved is True
    assert saved_user.user_role.display_name == "志工"


def test_task_model(db_session):
    """測試任務模型"""
    # 建立必要的基礎資料
    role = UserRole(role="official_org", display_name="正式組織", permissions={})
    task_type = TaskType(type="cleanup", display_name="清理工作", description="清理任務")
    task_status = TaskStatus(status="available", display_name="可認領", description="可認領狀態")
    
    db_session.add_all([role, task_type, task_status])
    db_session.commit()
    
    user = User(
        email="org@example.com",
        name="組織用戶",
        password_hash="hashed_password",
        role="official_org"
    )
    db_session.add(user)
    db_session.commit()
    
    # 建立任務
    task = Task(
        creator_id=user.id,
        title="測試清理任務",
        description="這是一個測試清理任務",
        task_type="cleanup",
        status="available",
        location_data={"address": "花蓮縣光復鄉", "coordinates": {"lat": 23.9739, "lng": 121.6015}},
        required_volunteers=5
    )
    
    db_session.add(task)
    db_session.commit()
    
    # 查詢驗證
    saved_task = db_session.query(Task).filter_by(title="測試清理任務").first()
    assert saved_task is not None
    assert saved_task.description == "這是一個測試清理任務"
    assert saved_task.task_type == "cleanup"
    assert saved_task.required_volunteers == 5
    assert saved_task.creator.name == "組織用戶"


def test_need_model(db_session):
    """測試需求模型"""
    # 建立必要的基礎資料
    role = UserRole(role="victim", display_name="受災戶", permissions={})
    need_type = NeedType(type="food", display_name="食物需求", description="食物相關需求")
    need_status = NeedStatus(status="open", display_name="待處理", description="新需求")
    
    db_session.add_all([role, need_type, need_status])
    db_session.commit()
    
    user = User(
        email="victim@example.com",
        name="受災戶",
        password_hash="hashed_password",
        role="victim"
    )
    db_session.add(user)
    db_session.commit()
    
    # 建立需求
    need = Need(
        reporter_id=user.id,
        title="急需食物",
        description="家中食物不足，急需協助",
        need_type="food",
        status="open",
        location_data={"address": "花蓮縣光復鄉中正路123號"},
        requirements={"food_items": ["米", "泡麵", "飲用水"], "quantity": 3},
        urgency_level=4
    )
    
    db_session.add(need)
    db_session.commit()
    
    # 查詢驗證
    saved_need = db_session.query(Need).filter_by(title="急需食物").first()
    assert saved_need is not None
    assert saved_need.description == "家中食物不足，急需協助"
    assert saved_need.urgency_level == 4
    assert saved_need.reporter.name == "受災戶"


def test_supply_station_model(db_session):
    """測試物資站點模型"""
    # 建立必要的基礎資料
    role = UserRole(role="supply_manager", display_name="物資管理者", permissions={})
    db_session.add(role)
    db_session.commit()
    
    user = User(
        email="manager@example.com",
        name="物資管理者",
        password_hash="hashed_password",
        role="supply_manager"
    )
    db_session.add(user)
    db_session.commit()
    
    # 建立物資站點
    station = SupplyStation(
        manager_id=user.id,
        name="光復鄉物資站",
        address="花蓮縣光復鄉中山路456號",
        location_data={"coordinates": {"lat": 23.9739, "lng": 121.6015}},
        contact_info={"phone": "03-1234567", "email": "station@example.com"},
        is_active=True
    )
    
    db_session.add(station)
    db_session.commit()
    
    # 查詢驗證
    saved_station = db_session.query(SupplyStation).filter_by(name="光復鄉物資站").first()
    assert saved_station is not None
    assert saved_station.address == "花蓮縣光復鄉中山路456號"
    assert saved_station.is_active is True
    assert saved_station.manager.name == "物資管理者"


def test_model_relationships(db_session):
    """測試模型關聯"""
    # 建立基礎資料
    role = UserRole(role="volunteer", display_name="志工", permissions={})
    task_type = TaskType(type="cleanup", display_name="清理工作")
    task_status = TaskStatus(status="available", display_name="可認領")
    
    db_session.add_all([role, task_type, task_status])
    db_session.commit()
    
    # 建立用戶
    creator = User(email="creator@example.com", name="任務建立者", password_hash="hash", role="volunteer")
    volunteer = User(email="volunteer@example.com", name="志工", password_hash="hash", role="volunteer")
    
    db_session.add_all([creator, volunteer])
    db_session.commit()
    
    # 建立任務
    task = Task(
        creator_id=creator.id,
        title="測試任務",
        description="測試任務描述",
        task_type="cleanup",
        status="available",
        location_data={"address": "測試地址"}
    )
    
    db_session.add(task)
    db_session.commit()
    
    # 建立任務認領
    claim = TaskClaim(
        task_id=task.id,
        user_id=volunteer.id,
        status="claimed"
    )
    
    db_session.add(claim)
    db_session.commit()
    
    # 測試關聯查詢
    saved_task = db_session.query(Task).filter_by(title="測試任務").first()
    assert len(saved_task.task_claims) == 1
    assert saved_task.task_claims[0].user.name == "志工"
    assert saved_task.creator.name == "任務建立者"