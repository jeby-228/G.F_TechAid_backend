"""
物資管理 CRUD 測試
"""
import pytest
from sqlalchemy.orm import Session
from app.crud.supply import supply_crud
from app.models.user import User
from app.models.supply import SupplyStation, InventoryItem
from app.schemas.supply import (
    SupplyStationCreate, SupplyStationUpdate, SupplyStationSearchQuery,
    InventoryItemCreate, InventoryItemUpdate, BulkInventoryUpdate,
    LocationData, ContactInfo
)
from app.utils.constants import UserRole
import uuid


class TestSupplyStationCRUD:
    """物資站點 CRUD 測試"""
    
    def test_create_supply_station(self, db_session: Session, supply_manager: User):
        """測試建立物資站點"""
        station_data = SupplyStationCreate(
            name="測試物資站點",
            address="花蓮縣光復鄉中正路123號",
            location_data=LocationData(
                address="花蓮縣光復鄉中正路123號",
                coordinates={"lat": 23.5731, "lng": 121.4208},
                details="靠近光復國小"
            ),
            contact_info=ContactInfo(
                phone="03-8701234",
                email="station@example.com",
                hours="08:00-17:00",
                contact_person="張站長"
            ),
            capacity_info={
                "max_items": 1000,
                "storage_area": "200平方公尺"
            }
        )
        
        station = supply_crud.create_supply_station(db_session, station_data, str(supply_manager.id))
        
        assert station.name == station_data.name
        assert station.address == station_data.address
        assert station.manager_id == supply_manager.id
        assert station.is_active == True
        assert station.location_data["coordinates"]["lat"] == 23.5731
        assert station.contact_info["phone"] == "03-8701234"
    
    def test_get_supply_station(self, db_session: Session, supply_station: SupplyStation):
        """測試獲取物資站點"""
        station = supply_crud.get_supply_station(db_session, str(supply_station.id))
        
        assert station is not None
        assert station.id == supply_station.id
        assert station.name == supply_station.name
        assert station.manager is not None
    
    def test_get_supply_station_not_found(self, db_session: Session):
        """測試獲取不存在的物資站點"""
        fake_id = str(uuid.uuid4())
        station = supply_crud.get_supply_station(db_session, fake_id)
        
        assert station is None
    
    def test_get_supply_stations_all(self, db_session: Session, supply_station: SupplyStation):
        """測試獲取所有物資站點"""
        stations, total = supply_crud.get_supply_stations(db_session, user_role=UserRole.ADMIN)
        
        assert total >= 1
        assert len(stations) >= 1
        assert any(s.id == supply_station.id for s in stations)
    
    def test_update_supply_station(self, db_session: Session, supply_station: SupplyStation, supply_manager: User):
        """測試更新物資站點"""
        update_data = SupplyStationUpdate(
            name="更新後的站點名稱",
            contact_info=ContactInfo(
                phone="03-8705678",
                email="updated@example.com"
            ),
            is_active=False
        )
        
        updated_station = supply_crud.update_supply_station(
            db_session, str(supply_station.id), update_data, str(supply_manager.id), UserRole.SUPPLY_MANAGER
        )
        
        assert updated_station is not None
        assert updated_station.name == "更新後的站點名稱"
        assert updated_station.contact_info["phone"] == "03-8705678"
        assert updated_station.is_active == False


class TestInventoryCRUD:
    """庫存管理 CRUD 測試"""
    
    def test_create_inventory_item(self, db_session: Session, supply_station: SupplyStation, supply_manager: User):
        """測試建立庫存物資"""
        item_data = InventoryItemCreate(
            station_id=str(supply_station.id),
            supply_type="water",
            description="礦泉水 600ml",
            is_available=True,
            notes="保存期限至2024年12月"
        )
        
        item = supply_crud.create_inventory_item(db_session, item_data, str(supply_manager.id), UserRole.SUPPLY_MANAGER)
        
        assert item.station_id == supply_station.id
        assert item.supply_type == "water"
        assert item.description == "礦泉水 600ml"
        assert item.is_available == True
        assert item.notes == "保存期限至2024年12月"
    
    def test_get_inventory_item(self, db_session: Session, inventory_item: InventoryItem):
        """測試獲取庫存物資"""
        item = supply_crud.get_inventory_item(db_session, str(inventory_item.id))
        
        assert item is not None
        assert item.id == inventory_item.id
        assert item.supply_type == inventory_item.supply_type
        assert item.station is not None
    
    def test_get_station_inventory(self, db_session: Session, supply_station: SupplyStation, inventory_item: InventoryItem):
        """測試獲取站點庫存列表"""
        items = supply_crud.get_station_inventory(db_session, str(supply_station.id))
        
        assert len(items) >= 1
        assert any(item.id == inventory_item.id for item in items)
        assert all(item.is_available for item in items)  # 預設只返回可用物資


class TestSupplyMapCRUD:
    """物資地圖 CRUD 測試"""
    
    def test_get_supply_map(self, db_session: Session, supply_station: SupplyStation, inventory_item: InventoryItem):
        """測試獲取物資地圖資料"""
        map_data = supply_crud.get_supply_map(db_session)
        
        assert "stations" in map_data
        assert "center" in map_data
        assert "bounds" in map_data
        
        # 檢查站點資料
        stations = map_data["stations"]
        assert len(stations) >= 1
        
        station = next((s for s in stations if s["id"] == str(supply_station.id)), None)
        assert station is not None
        assert station["name"] == supply_station.name
        assert "available_supplies" in station


class TestSupplyStatisticsCRUD:
    """物資統計 CRUD 測試"""
    
    def test_get_supply_statistics(self, db_session: Session, supply_station: SupplyStation, inventory_item: InventoryItem):
        """測試獲取物資統計資料"""
        stats = supply_crud.get_supply_statistics(db_session)
        
        assert "total_stations" in stats
        assert "active_stations" in stats
        assert "total_supply_types" in stats
        assert "available_supply_types" in stats
        assert "pending_reservations" in stats
        assert "completed_reservations" in stats
        assert "stations_by_manager_role" in stats
        assert "supplies_by_type" in stats
        
        # 檢查統計數據
        assert stats["total_stations"] >= 1
        assert stats["active_stations"] >= 1
        assert stats["total_supply_types"] >= 1
        assert stats["available_supply_types"] >= 1
        
        # 檢查角色統計
        assert isinstance(stats["stations_by_manager_role"], dict)
        assert isinstance(stats["supplies_by_type"], dict)