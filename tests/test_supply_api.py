"""
物資管理 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.supply import SupplyStation, InventoryItem
from app.utils.constants import UserRole
import uuid


class TestSupplyStationAPI:
    """物資站點 API 測試"""
    
    def test_create_supply_station_success(self, client: TestClient, db: Session, supply_manager_token: str):
        """測試成功建立物資站點"""
        station_data = {
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
            }
        }
        
        response = client.post(
            "/api/v1/supplies/stations",
            json=station_data,
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == station_data["name"]
        assert data["address"] == station_data["address"]
        assert data["is_active"] == True
        assert data["can_edit"] == True
    
    def test_create_supply_station_unauthorized(self, client: TestClient, victim_token: str):
        """測試未授權用戶無法建立物資站點"""
        station_data = {
            "name": "測試物資站點",
            "address": "花蓮縣光復鄉中正路123號",
            "location_data": {
                "address": "花蓮縣光復鄉中正路123號",
                "coordinates": {"lat": 23.5731, "lng": 121.4208}
            },
            "contact_info": {
                "phone": "03-8701234"
            }
        }
        
        response = client.post(
            "/api/v1/supplies/stations",
            json=station_data,
            headers={"Authorization": f"Bearer {victim_token}"}
        )
        
        assert response.status_code == 403
    
    def test_get_supply_stations(self, client: TestClient, db: Session, volunteer_token: str, supply_station: SupplyStation):
        """測試獲取物資站點列表"""
        response = client.get(
            "/api/v1/supplies/stations",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["stations"]) >= 1
        
        # 檢查站點資料
        station = data["stations"][0]
        assert "id" in station
        assert "name" in station
        assert "address" in station
        assert "location_data" in station
        assert "contact_info" in station
    
    def test_get_supply_station_by_id(self, client: TestClient, volunteer_token: str, supply_station: SupplyStation):
        """測試根據 ID 獲取物資站點"""
        response = client.get(
            f"/api/v1/supplies/stations/{supply_station.id}",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(supply_station.id)
        assert data["name"] == supply_station.name
    
    def test_get_supply_station_not_found(self, client: TestClient, volunteer_token: str):
        """測試獲取不存在的物資站點"""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/supplies/stations/{fake_id}",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 404
    
    def test_update_supply_station_success(self, client: TestClient, supply_manager_token: str, supply_station: SupplyStation):
        """測試成功更新物資站點"""
        update_data = {
            "name": "更新後的物資站點",
            "contact_info": {
                "phone": "03-8705678",
                "email": "updated@example.com"
            }
        }
        
        response = client.put(
            f"/api/v1/supplies/stations/{supply_station.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
    
    def test_update_supply_station_unauthorized(self, client: TestClient, volunteer_token: str, supply_station: SupplyStation):
        """測試未授權用戶無法更新物資站點"""
        update_data = {"name": "未授權更新"}
        
        response = client.put(
            f"/api/v1/supplies/stations/{supply_station.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403
    
    def test_delete_supply_station_success(self, client: TestClient, db: Session, supply_manager_token: str):
        """測試成功刪除物資站點"""
        # 建立測試站點
        station = SupplyStation(
            id=uuid.uuid4(),
            manager_id=uuid.uuid4(),  # 會在 fixture 中設定正確的 manager_id
            name="待刪除站點",
            address="測試地址",
            location_data={"coordinates": {"lat": 23.5731, "lng": 121.4208}},
            contact_info={"phone": "123456789"},
            is_active=True
        )
        db.add(station)
        db.commit()
        
        response = client.delete(
            f"/api/v1/supplies/stations/{station.id}",
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 204
    
    def test_search_supply_stations_by_name(self, client: TestClient, volunteer_token: str, supply_station: SupplyStation):
        """測試按名稱搜尋物資站點"""
        response = client.get(
            f"/api/v1/supplies/stations?name={supply_station.name[:5]}",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    def test_search_supply_stations_by_location(self, client: TestClient, volunteer_token: str):
        """測試按地理位置搜尋物資站點"""
        response = client.get(
            "/api/v1/supplies/stations?center_lat=23.5731&center_lng=121.4208&location_radius=10",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert "total" in data


class TestInventoryAPI:
    """庫存管理 API 測試"""
    
    def test_create_inventory_item_success(self, client: TestClient, supply_manager_token: str, supply_station: SupplyStation):
        """測試成功建立庫存物資"""
        item_data = {
            "station_id": str(supply_station.id),
            "supply_type": "water",
            "description": "礦泉水 600ml",
            "is_available": True,
            "notes": "保存期限至2024年12月"
        }
        
        response = client.post(
            "/api/v1/supplies/inventory",
            json=item_data,
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["supply_type"] == item_data["supply_type"]
        assert data["description"] == item_data["description"]
        assert data["is_available"] == True
    
    def test_create_inventory_item_unauthorized(self, client: TestClient, volunteer_token: str, supply_station: SupplyStation):
        """測試未授權用戶無法建立庫存物資"""
        item_data = {
            "station_id": str(supply_station.id),
            "supply_type": "water",
            "description": "礦泉水 600ml"
        }
        
        response = client.post(
            "/api/v1/supplies/inventory",
            json=item_data,
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403
    
    def test_get_station_inventory(self, client: TestClient, volunteer_token: str, supply_station: SupplyStation, inventory_item: InventoryItem):
        """測試獲取站點庫存列表"""
        response = client.get(
            f"/api/v1/supplies/stations/{supply_station.id}/inventory",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        
        # 檢查庫存資料
        item = data["items"][0]
        assert "id" in item
        assert "supply_type" in item
        assert "is_available" in item
    
    def test_update_inventory_item_success(self, client: TestClient, supply_manager_token: str, inventory_item: InventoryItem):
        """測試成功更新庫存物資"""
        update_data = {
            "description": "更新後的描述",
            "is_available": False,
            "notes": "暫時缺貨"
        }
        
        response = client.put(
            f"/api/v1/supplies/inventory/{inventory_item.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["is_available"] == False
    
    def test_delete_inventory_item_success(self, client: TestClient, db: Session, supply_manager_token: str, supply_station: SupplyStation):
        """測試成功刪除庫存物資"""
        # 建立測試庫存
        item = InventoryItem(
            id=uuid.uuid4(),
            station_id=supply_station.id,
            supply_type="test_item",
            description="待刪除物資",
            is_available=True
        )
        db.add(item)
        db.commit()
        
        response = client.delete(
            f"/api/v1/supplies/inventory/{item.id}",
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 204
    
    def test_bulk_update_inventory_success(self, client: TestClient, supply_manager_token: str, supply_station: SupplyStation):
        """測試批量更新庫存成功"""
        bulk_data = {
            "station_id": str(supply_station.id),
            "items": [
                {
                    "supply_type": "water",
                    "description": "礦泉水",
                    "is_available": True
                },
                {
                    "supply_type": "rice",
                    "description": "白米",
                    "is_available": True
                }
            ],
            "replace_existing": True
        }
        
        response = client.post(
            "/api/v1/supplies/inventory/bulk-update",
            json=bulk_data,
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["created_count"] >= 2


class TestSupplyMapAPI:
    """物資地圖 API 測試"""
    
    def test_get_supply_map(self, client: TestClient, volunteer_token: str, supply_station: SupplyStation):
        """測試獲取物資地圖資料"""
        response = client.get(
            "/api/v1/supplies/map",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert "center" in data
        assert "bounds" in data
        
        # 檢查地圖資料結構
        if data["stations"]:
            station = data["stations"][0]
            assert "id" in station
            assert "name" in station
            assert "coordinates" in station
            assert "available_supplies" in station
    
    def test_get_supply_map_with_filters(self, client: TestClient, volunteer_token: str):
        """測試帶篩選條件的物資地圖"""
        response = client.get(
            "/api/v1/supplies/map?center_lat=23.5731&center_lng=121.4208&radius=5&supply_type_filter=water",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data


class TestSupplyStatisticsAPI:
    """物資統計 API 測試"""
    
    def test_get_supply_statistics_success(self, client: TestClient, admin_token: str):
        """測試管理員獲取物資統計"""
        response = client.get(
            "/api/v1/supplies/statistics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_stations" in data
        assert "active_stations" in data
        assert "total_supply_types" in data
        assert "available_supply_types" in data
        assert "pending_reservations" in data
        assert "completed_reservations" in data
        assert "stations_by_manager_role" in data
        assert "supplies_by_type" in data
    
    def test_get_supply_statistics_unauthorized(self, client: TestClient, volunteer_token: str):
        """測試非管理員無法獲取統計資料"""
        response = client.get(
            "/api/v1/supplies/statistics",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 403


class TestMyStationsAPI:
    """我的站點 API 測試"""
    
    def test_get_my_supply_stations(self, client: TestClient, supply_manager_token: str, supply_station: SupplyStation):
        """測試獲取我管理的物資站點"""
        response = client.get(
            "/api/v1/supplies/my-stations",
            headers={"Authorization": f"Bearer {supply_manager_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert "total" in data
    
    def test_get_active_supply_stations(self, client: TestClient, volunteer_token: str):
        """測試獲取啟用的物資站點"""
        response = client.get(
            "/api/v1/supplies/active-stations",
            headers={"Authorization": f"Bearer {volunteer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "stations" in data
        assert "total" in data
        
        # 檢查所有站點都是啟用狀態
        for station in data["stations"]:
            assert station["is_active"] == True