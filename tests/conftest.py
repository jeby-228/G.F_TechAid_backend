import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.core.database import get_db, Base
from app.utils.constants import UserRole

# 模擬 Redis 客戶端（避免 fakeredis 版本問題）
class MockRedis:
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value, ex=None):
        self.data[key] = value
        return True
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]
            return 1
        return 0
    
    def exists(self, key):
        return key in self.data
    
    def flushall(self):
        self.data.clear()
        return True

# 確保所有模型都被匯入，以便建立資料表
from app.models import user, task, need, supply, system

# 測試資料庫 URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# 建立測試資料庫引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db() -> Generator[Session, None, None]:
    """覆寫資料庫依賴注入"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

def override_get_redis():
    """覆寫 Redis 依賴注入"""
    return MockRedis()

# 覆寫依賴注入
app.dependency_overrides[get_db] = override_get_db
# 只有在 Redis 客戶端存在時才覆寫
try:
    from app.core.redis import get_redis_client
    app.dependency_overrides[get_redis_client] = override_get_redis
except ImportError:
    pass

@pytest.fixture(scope="session")
def event_loop():
    """建立事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """建立資料庫會話"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # 初始化必要的參考資料
    _initialize_reference_data(session)
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db() -> Generator[Session, None, None]:
    """建立資料庫會話 (別名)"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # 初始化必要的參考資料
    _initialize_reference_data(session)
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """建立測試客戶端"""
    Base.metadata.create_all(bind=engine)
    
    # 初始化必要的參考資料
    session = TestingSessionLocal()
    _initialize_reference_data(session)
    session.close()
    
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def redis_client():
    """建立測試 Redis 客戶端"""
    return MockRedis()

# 測試資料工廠
class TestDataFactory:
    """測試資料工廠"""
    
    @staticmethod
    def create_user_data(role: UserRole = UserRole.VOLUNTEER, **kwargs):
        """建立測試用戶資料"""
        default_data = {
            "email": "test@example.com",
            "name": "測試用戶",
            "phone": "0912345678",
            "password": "testpassword123",
            "role": role
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_task_data(**kwargs):
        """建立測試任務資料"""
        default_data = {
            "title": "測試任務",
            "description": "這是一個測試任務",
            "task_type": "cleanup",
            "location_data": {
                "address": "花蓮縣光復鄉",
                "coordinates": {"lat": 23.5731, "lng": 121.4208}
            },
            "required_volunteers": 5
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_need_data(**kwargs):
        """建立測試需求資料"""
        default_data = {
            "title": "測試需求",
            "description": "這是一個測試需求",
            "need_type": "food",
            "location_data": {
                "address": "花蓮縣光復鄉",
                "coordinates": {"lat": 23.5731, "lng": 121.4208}
            },
            "requirements": {"food_items": ["rice", "water"]}
        }
        default_data.update(kwargs)
        return default_data

def _initialize_reference_data(session: Session):
    """初始化參考資料"""
    from app.models.user import UserRole
    from app.models.task import TaskType, TaskStatus
    from app.models.need import NeedType, NeedStatus
    from app.models.supply import SupplyType, ReservationStatus
    
    # 檢查是否已經初始化
    existing_roles = session.query(UserRole).first()
    if existing_roles:
        return
    
    # 初始化用戶角色
    roles_data = [
        ('admin', '系統管理員', {'all': True}),
        ('victim', '受災戶', {'create_need': True, 'view_shelters': True}),
        ('official_org', '正式志工組織', {'create_task': True, 'claim_task': True, 'manage_supplies': True}),
        ('unofficial_org', '非正式志工組織', {'create_task': False, 'claim_task': True}),
        ('supply_manager', '物資站點管理者', {'manage_supplies': True, 'create_task': True}),
        ('volunteer', '一般志工', {'claim_task': True})
    ]
    
    for role, display_name, permissions in roles_data:
        db_role = UserRole(role=role, display_name=display_name, permissions=permissions)
        session.add(db_role)
    
    # 初始化任務類型
    task_types_data = [
        ('cleanup', '清理工作', '災後清理、垃圾清運等工作'),
        ('rescue', '救援任務', '人員搜救、緊急救援'),
        ('supply_delivery', '物資配送', '物資運送、分發工作'),
        ('medical_aid', '醫療協助', '醫療救護、健康檢查'),
        ('shelter_support', '避難所支援', '避難所管理、服務工作')
    ]
    
    for task_type, display_name, description in task_types_data:
        db_task_type = TaskType(type=task_type, display_name=display_name, description=description)
        session.add(db_task_type)
    
    # 初始化任務狀態
    task_statuses_data = [
        ('pending', '待審核'),
        ('available', '可認領'),
        ('claimed', '已認領'),
        ('in_progress', '執行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消')
    ]
    
    for status, display_name in task_statuses_data:
        db_task_status = TaskStatus(status=status, display_name=display_name)
        session.add(db_task_status)
    
    # 初始化需求類型
    need_types_data = [
        ('food', '食物需求', '食品、飲水等基本需求'),
        ('medical', '醫療需求', '醫療用品、藥品需求'),
        ('shelter', '住宿需求', '臨時住所、避難需求'),
        ('clothing', '衣物需求', '衣服、棉被等保暖用品'),
        ('rescue', '救援需求', '人員搜救、緊急救援'),
        ('cleanup', '清理需求', '環境清理、修繕協助')
    ]
    
    for need_type, display_name, description in need_types_data:
        db_need_type = NeedType(type=need_type, display_name=display_name, description=description)
        session.add(db_need_type)
    
    # 初始化需求狀態
    need_statuses_data = [
        ('open', '待處理'),
        ('assigned', '已分配'),
        ('in_progress', '處理中'),
        ('resolved', '已解決'),
        ('closed', '已關閉')
    ]
    
    for status, display_name in need_statuses_data:
        db_need_status = NeedStatus(status=status, display_name=display_name)
        session.add(db_need_status)
    
    # 初始化物資類型
    supply_types_data = [
        ('water', '飲用水', 'food', 'bottle'),
        ('rice', '白米', 'food', 'kg'),
        ('instant_noodles', '泡麵', 'food', 'pack'),
        ('blanket', '毛毯', 'clothing', 'piece'),
        ('first_aid_kit', '急救包', 'medical', 'kit'),
        ('flashlight', '手電筒', 'tools', 'piece')
    ]
    
    for supply_type, display_name, category, unit in supply_types_data:
        db_supply_type = SupplyType(
            type=supply_type, 
            display_name=display_name, 
            category=category, 
            unit=unit
        )
        session.add(db_supply_type)
    
    # 初始化預訂狀態
    reservation_statuses_data = [
        ('pending', '待確認'),
        ('confirmed', '已確認'),
        ('picked_up', '已領取'),
        ('delivered', '已配送'),
        ('cancelled', '已取消')
    ]
    
    for status, display_name in reservation_statuses_data:
        db_reservation_status = ReservationStatus(status=status, display_name=display_name)
        session.add(db_reservation_status)
    
    session.commit()

@pytest.fixture
def test_data_factory():
    """測試資料工廠 fixture"""
    return TestDataFactory

# 測試輔助函數
def create_test_user(db: Session, role: UserRole = UserRole.VOLUNTEER, **kwargs):
    """建立測試用戶"""
    from app.models.user import User
    from app.core.security import get_password_hash
    import uuid
    
    user_data = {
        "id": uuid.uuid4(),
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "name": "測試用戶",
        "phone": "0912345678",
        "password_hash": get_password_hash("testpassword123"),
        "role": role.value,
        "is_approved": True
    }
    user_data.update(kwargs)
    
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_task(db: Session, creator_id: str = None, **kwargs):
    """建立測試任務"""
    from app.models.task import Task
    from app.utils.constants import TaskStatus
    import uuid
    
    if not creator_id:
        # 建立預設建立者
        creator = create_test_user(db, role=UserRole.OFFICIAL_ORG)
        creator_id = str(creator.id)
    
    task_data = {
        "id": uuid.uuid4(),
        "creator_id": uuid.UUID(creator_id),
        "title": "測試任務",
        "description": "這是一個測試任務",
        "task_type": "cleanup",
        "status": TaskStatus.AVAILABLE.value,
        "location_data": {
            "address": "花蓮縣光復鄉",
            "coordinates": {"lat": 23.5731, "lng": 121.4208}
        },
        "required_volunteers": 5,
        "priority_level": 1,
        "approval_status": "approved"
    }
    task_data.update(kwargs)
    
    task = Task(**task_data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def create_test_supply_station(db: Session, manager_id: str = None, **kwargs):
    """建立測試物資站點"""
    from app.models.supply import SupplyStation
    import uuid
    
    if not manager_id:
        # 建立預設管理者
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER)
        manager_id = str(manager.id)
    
    station_data = {
        "id": uuid.uuid4(),
        "manager_id": uuid.UUID(manager_id),
        "name": "測試物資站點",
        "address": "花蓮縣光復鄉中正路123號",
        "location_data": {
            "address": "花蓮縣光復鄉中正路123號",
            "coordinates": {"lat": 23.5731, "lng": 121.4208},
            "details": "靠近光復國小"
        },
        "contact_info": {
            "phone": "03-8701234",
            "email": "station@example.com",
            "hours": "08:00-17:00",
            "contact_person": "張站長"
        },
        "capacity_info": {
            "max_items": 1000,
            "storage_area": "200平方公尺"
        },
        "is_active": True
    }
    station_data.update(kwargs)
    
    station = SupplyStation(**station_data)
    db.add(station)
    db.commit()
    db.refresh(station)
    return station

def create_test_inventory_item(db: Session, station_id: str = None, **kwargs):
    """建立測試庫存物資"""
    from app.models.supply import InventoryItem
    import uuid
    
    if not station_id:
        # 建立預設站點
        station = create_test_supply_station(db)
        station_id = str(station.id)
    
    item_data = {
        "id": uuid.uuid4(),
        "station_id": uuid.UUID(station_id),
        "supply_type": "water",
        "description": "礦泉水 600ml",
        "is_available": True,
        "notes": "保存期限至2024年12月"
    }
    item_data.update(kwargs)
    
    item = InventoryItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def create_test_need(db: Session, reporter_id: str = None, **kwargs):
    """建立測試需求"""
    from app.models.need import Need
    from app.utils.constants import NeedStatus
    import uuid
    
    if not reporter_id:
        # 建立預設報告者
        reporter = create_test_user(db, role=UserRole.VICTIM)
        reporter_id = str(reporter.id)
    
    need_data = {
        "id": uuid.uuid4(),
        "reporter_id": uuid.UUID(reporter_id),
        "title": "測試需求",
        "description": "這是一個測試需求",
        "need_type": "food",
        "status": NeedStatus.OPEN.value,
        "location_data": {
            "address": "花蓮縣光復鄉",
            "coordinates": {"lat": 23.5731, "lng": 121.4208}
        },
        "requirements": {"food_items": ["rice", "water"]},
        "urgency_level": 1
    }
    need_data.update(kwargs)
    
    need = Need(**need_data)
    db.add(need)
    db.commit()
    db.refresh(need)
    return need

def create_test_shelter(db: Session, manager_id: str = None, **kwargs):
    """建立測試避難所"""
    from app.models.system import Shelter
    import uuid
    
    if manager_id:
        manager_uuid = uuid.UUID(manager_id)
    else:
        manager_uuid = None
    
    shelter_data = {
        "id": uuid.uuid4(),
        "name": "測試避難所",
        "address": "花蓮縣光復鄉中正路456號",
        "location_data": {
            "address": "花蓮縣光復鄉中正路456號",
            "coordinates": {"lat": 23.9739, "lng": 121.6015},
            "details": "光復國小體育館"
        },
        "capacity": 100,
        "current_occupancy": 0,
        "contact_info": {
            "phone": "03-8701234",
            "contact_person": "避難所管理員",
            "hours": "24小時開放",
            "emergency_contact": "119"
        },
        "facilities": {
            "has_medical": True,
            "has_kitchen": True,
            "has_shower": False,
            "has_wifi": True,
            "has_generator": False,
            "has_wheelchair_access": True,
            "pet_friendly": False,
            "additional_facilities": ["廣播系統", "投影設備"],
            "notes": "體育館設施完善"
        },
        "status": "active",
        "managed_by": manager_uuid
    }
    shelter_data.update(kwargs)
    
    shelter = Shelter(**shelter_data)
    db.add(shelter)
    db.commit()
    db.refresh(shelter)
    return shelter

# 用戶相關 fixtures
@pytest.fixture
def admin_user(db_session: Session):
    """管理員用戶"""
    return create_test_user(db_session, role=UserRole.ADMIN, name="管理員")

@pytest.fixture
def admin(db_session: Session):
    """管理員用戶 (別名)"""
    return create_test_user(db_session, role=UserRole.ADMIN, name="管理員")

@pytest.fixture
def supply_manager_user(db_session: Session):
    """物資管理者用戶"""
    return create_test_user(db_session, role=UserRole.SUPPLY_MANAGER, name="物資管理者")

@pytest.fixture
def supply_manager(db_session: Session):
    """物資管理者用戶 (別名)"""
    return create_test_user(db_session, role=UserRole.SUPPLY_MANAGER, name="物資管理者")

@pytest.fixture
def volunteer_user(db_session: Session):
    """志工用戶"""
    return create_test_user(db_session, role=UserRole.VOLUNTEER, name="志工")

@pytest.fixture
def volunteer(db_session: Session):
    """志工用戶 (別名)"""
    return create_test_user(db_session, role=UserRole.VOLUNTEER, name="志工")

@pytest.fixture
def victim_user(db_session: Session):
    """受災戶用戶"""
    return create_test_user(db_session, role=UserRole.VICTIM, name="受災戶")

@pytest.fixture
def victim(db_session: Session):
    """受災戶用戶 (別名)"""
    return create_test_user(db_session, role=UserRole.VICTIM, name="受災戶")

# 物資相關 fixtures
@pytest.fixture
def supply_station(db_session: Session, supply_manager):
    """測試物資站點"""
    return create_test_supply_station(db_session, manager_id=str(supply_manager.id))

@pytest.fixture
def inventory_item(db_session: Session, supply_station):
    """測試庫存物資"""
    return create_test_inventory_item(db_session, station_id=str(supply_station.id))

# 避難所相關 fixtures
@pytest.fixture
def sample_shelter(db_session: Session, admin):
    """測試避難所"""
    return create_test_shelter(db_session, manager_id=str(admin.id))

# Token fixtures (需要實際的認證服務)
@pytest.fixture
def admin_token():
    """管理員 token"""
    return "admin_test_token"

@pytest.fixture
def supply_manager_token():
    """物資管理者 token"""
    return "supply_manager_test_token"

@pytest.fixture
def volunteer_token():
    """志工 token"""
    return "volunteer_test_token"

@pytest.fixture
def victim_token():
    """受災戶 token"""
    return "victim_test_token"