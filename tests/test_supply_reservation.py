"""
物資預訂和配送系統整合測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.supply import SupplyStation, InventoryItem, SupplyReservation, ReservationItem
from app.models.task import Task
from app.models.need import Need
from app.utils.constants import UserRole, ReservationStatus, TaskStatus, NeedStatus
from tests.conftest import create_test_user, create_test_supply_station, create_test_task, create_test_need


class TestSupplyReservationSystem:
    """物資預訂系統測試"""
    
    def test_create_supply_reservation_success(self, client: TestClient, db: Session):
        """測試成功建立物資預訂"""
        # 建立測試資料
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        task = create_test_task(db, creator_id=str(volunteer.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="water",
            description="飲用水",
            is_available=True
        )
        db.add(inventory)
        db.commit()
        
        # 登入志工
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        # 建立預訂
        reservation_data = {
            "station_id": str(station.id),
            "task_id": str(task.id),
            "notes": "緊急需要飲用水",
            "reservation_items": [
                {
                    "supply_type": "water",
                    "requested_quantity": 10,
                    "notes": "瓶裝水"
                }
            ]
        }
        
        response = client.post("/api/v1/supplies/reservations", json=reservation_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["station_id"] == str(station.id)
        assert data["task_id"] == str(task.id)
        assert data["status"] == ReservationStatus.PENDING.value
        assert len(data["reservation_items"]) == 1
        assert data["reservation_items"][0]["supply_type"] == "water"
        assert data["reservation_items"][0]["requested_quantity"] == 10
    
    def test_create_reservation_invalid_station(self, client: TestClient, db: Session):
        """測試預訂不存在的站點"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        reservation_data = {
            "station_id": "00000000-0000-0000-0000-000000000000",
            "reservation_items": [
                {
                    "supply_type": "water",
                    "requested_quantity": 10
                }
            ]
        }
        
        response = client.post("/api/v1/supplies/reservations", json=reservation_data)
        assert response.status_code == 404
        assert "物資站點不存在" in response.json()["detail"]
    
    def test_create_reservation_unavailable_supply(self, client: TestClient, db: Session):
        """測試預訂不可用的物資"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        reservation_data = {
            "station_id": str(station.id),
            "reservation_items": [
                {
                    "supply_type": "unavailable_item",
                    "requested_quantity": 10
                }
            ]
        }
        
        response = client.post("/api/v1/supplies/reservations", json=reservation_data)
        assert response.status_code == 400
        assert "不可用" in response.json()["detail"]
    
    def test_get_supply_reservations(self, client: TestClient, db: Session):
        """測試獲取預訂列表"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value,
            notes="測試預訂"
        )
        db.add(reservation)
        db.commit()
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        response = client.get("/api/v1/supplies/reservations")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert len(data["reservations"]) == 1
        assert data["reservations"][0]["id"] == str(reservation.id)
    
    def test_confirm_supply_reservation(self, client: TestClient, db: Session):
        """測試確認物資預訂"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立預訂和預訂項目
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db.add(reservation)
        db.flush()
        
        reservation_item = ReservationItem(
            reservation_id=reservation.id,
            supply_type="water",
            requested_quantity=10
        )
        db.add(reservation_item)
        db.commit()
        
        # 登入站點管理者
        client.post("/api/v1/auth/login", json={
            "email": "manager@test.com",
            "password": "testpass123"
        })
        
        # 確認預訂
        confirmed_items = [
            {
                "supply_type": "water",
                "confirmed_quantity": 8,
                "notes": "庫存不足，只能提供8瓶"
            }
        ]
        
        response = client.post(
            f"/api/v1/supplies/reservations/{reservation.id}/confirm",
            json=confirmed_items
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == ReservationStatus.CONFIRMED.value
        assert data["confirmed_at"] is not None
        assert data["reservation_items"][0]["confirmed_quantity"] == 8
    
    def test_update_reservation_status_workflow(self, client: TestClient, db: Session):
        """測試預訂狀態更新工作流程"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立已確認的預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.CONFIRMED.value,
            confirmed_at=datetime.utcnow()
        )
        db.add(reservation)
        db.commit()
        
        # 登入志工
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        # 更新為已領取
        response = client.put(
            f"/api/v1/supplies/reservations/{reservation.id}/status",
            params={"new_status": ReservationStatus.PICKED_UP.value}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == ReservationStatus.PICKED_UP.value
        assert data["picked_up_at"] is not None
        
        # 更新為已配送
        response = client.put(
            f"/api/v1/supplies/reservations/{reservation.id}/status",
            params={"new_status": ReservationStatus.DELIVERED.value}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == ReservationStatus.DELIVERED.value
        assert data["delivered_at"] is not None
    
    def test_invalid_status_transition(self, client: TestClient, db: Session):
        """測試無效的狀態轉換"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立待處理的預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db.add(reservation)
        db.commit()
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        # 嘗試直接從 pending 跳到 delivered（無效轉換）
        response = client.put(
            f"/api/v1/supplies/reservations/{reservation.id}/status",
            params={"new_status": ReservationStatus.DELIVERED.value}
        )
        assert response.status_code == 400
        assert "不能從" in response.json()["detail"]
    
    def test_cancel_supply_reservation(self, client: TestClient, db: Session):
        """測試取消物資預訂"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db.add(reservation)
        db.commit()
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        response = client.delete(
            f"/api/v1/supplies/reservations/{reservation.id}",
            params={"reason": "不再需要"}
        )
        assert response.status_code == 204
        
        # 驗證預訂已取消
        db.refresh(reservation)
        assert reservation.status == ReservationStatus.CANCELLED.value
        assert "不再需要" in reservation.notes
    
    def test_get_station_reservations(self, client: TestClient, db: Session):
        """測試獲取站點預訂列表"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立多個預訂
        for i in range(3):
            reservation = SupplyReservation(
                user_id=volunteer.id,
                station_id=station.id,
                status=ReservationStatus.PENDING.value,
                notes=f"預訂 {i+1}"
            )
            db.add(reservation)
        db.commit()
        
        # 登入站點管理者
        client.post("/api/v1/auth/login", json={
            "email": "manager@test.com",
            "password": "testpass123"
        })
        
        response = client.get(f"/api/v1/supplies/stations/{station.id}/reservations")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 3
        assert len(data["reservations"]) == 3
    
    def test_get_my_reservations(self, client: TestClient, db: Session):
        """測試獲取我的預訂列表"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db.add(reservation)
        db.commit()
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        response = client.get("/api/v1/supplies/my-reservations")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 1
        assert data["reservations"][0]["id"] == str(reservation.id)
    
    def test_supply_map_with_reservations(self, client: TestClient, db: Session):
        """測試物資地圖顯示（需求 6.1, 6.2）"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立庫存
        inventory_items = [
            InventoryItem(
                station_id=station.id,
                supply_type="water",
                description="飲用水",
                is_available=True
            ),
            InventoryItem(
                station_id=station.id,
                supply_type="rice",
                description="白米",
                is_available=True
            )
        ]
        for item in inventory_items:
            db.add(item)
        db.commit()
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        response = client.get("/api/v1/supplies/map")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["stations"]) == 1
        station_data = data["stations"][0]
        assert station_data["id"] == str(station.id)
        assert len(station_data["available_supplies"]) == 2
        
        # 驗證物資清單
        supply_types = [supply["type"] for supply in station_data["available_supplies"]]
        assert "water" in supply_types
        assert "rice" in supply_types
    
    def test_permission_checks(self, client: TestClient, db: Session):
        """測試權限控制"""
        victim = create_test_user(db, role=UserRole.VICTIM, email="victim@test.com")
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="water",
            is_available=True
        )
        db.add(inventory)
        db.commit()
        
        # 受災戶不能預訂物資
        client.post("/api/v1/auth/login", json={
            "email": "victim@test.com",
            "password": "testpass123"
        })
        
        reservation_data = {
            "station_id": str(station.id),
            "reservation_items": [{"supply_type": "water", "requested_quantity": 1}]
        }
        
        response = client.post("/api/v1/supplies/reservations", json=reservation_data)
        assert response.status_code == 403
        
        # 志工可以預訂物資
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        response = client.post("/api/v1/supplies/reservations", json=reservation_data)
        assert response.status_code == 201


class TestSupplyDeliveryTracking:
    """物資配送追蹤測試"""
    
    def test_delivery_workflow_integration(self, client: TestClient, db: Session):
        """測試完整的配送工作流程整合（需求 6.3, 6.4, 6.5）"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        need = create_test_need(db, reporter_id=str(volunteer.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="water",
            is_available=True
        )
        db.add(inventory)
        db.commit()
        
        # 步驟1: 志工預訂物資
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        reservation_data = {
            "station_id": str(station.id),
            "need_id": str(need.id),
            "notes": "為受災戶配送物資",
            "reservation_items": [
                {
                    "supply_type": "water",
                    "requested_quantity": 5,
                    "notes": "緊急需要"
                }
            ]
        }
        
        response = client.post("/api/v1/supplies/reservations", json=reservation_data)
        assert response.status_code == 201
        reservation_id = response.json()["id"]
        
        # 步驟2: 站點管理者確認預訂
        client.post("/api/v1/auth/login", json={
            "email": "manager@test.com",
            "password": "testpass123"
        })
        
        confirmed_items = [
            {
                "supply_type": "water",
                "confirmed_quantity": 5,
                "notes": "已備貨完成"
            }
        ]
        
        response = client.post(
            f"/api/v1/supplies/reservations/{reservation_id}/confirm",
            json=confirmed_items
        )
        assert response.status_code == 200
        assert response.json()["status"] == ReservationStatus.CONFIRMED.value
        
        # 步驟3: 志工領取物資
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        response = client.put(
            f"/api/v1/supplies/reservations/{reservation_id}/status",
            params={"new_status": ReservationStatus.PICKED_UP.value}
        )
        assert response.status_code == 200
        assert response.json()["status"] == ReservationStatus.PICKED_UP.value
        
        # 步驟4: 配送完成確認
        response = client.put(
            f"/api/v1/supplies/reservations/{reservation_id}/status",
            params={"new_status": ReservationStatus.DELIVERED.value}
        )
        assert response.status_code == 200
        
        final_data = response.json()
        assert final_data["status"] == ReservationStatus.DELIVERED.value
        assert final_data["delivered_at"] is not None
        
        # 驗證完整的配送記錄
        response = client.get(f"/api/v1/supplies/reservations/{reservation_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["need_id"] == str(need.id)
        assert data["reserved_at"] is not None
        assert data["confirmed_at"] is not None
        assert data["picked_up_at"] is not None
        assert data["delivered_at"] is not None
    
    def test_supply_reservation_with_task(self, client: TestClient, db: Session):
        """測試關聯任務的物資預訂"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        task = create_test_task(db, creator_id=str(volunteer.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="first_aid_kit",
            is_available=True
        )
        db.add(inventory)
        db.commit()
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        reservation_data = {
            "station_id": str(station.id),
            "task_id": str(task.id),
            "notes": "任務所需醫療用品",
            "reservation_items": [
                {
                    "supply_type": "first_aid_kit",
                    "requested_quantity": 2
                }
            ]
        }
        
        response = client.post("/api/v1/supplies/reservations", json=reservation_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["task_id"] == str(task.id)
        assert data["task_title"] == task.title
    
    def test_reservation_filtering(self, client: TestClient, db: Session):
        """測試預訂篩選功能"""
        volunteer = create_test_user(db, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db, manager_id=str(manager.id))
        task = create_test_task(db, creator_id=str(volunteer.id))
        
        # 建立不同狀態的預訂
        reservations = []
        for i, status in enumerate([ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.DELIVERED]):
            reservation = SupplyReservation(
                user_id=volunteer.id,
                station_id=station.id,
                task_id=task.id if i == 0 else None,
                status=status.value,
                notes=f"預訂 {i+1}"
            )
            db.add(reservation)
            reservations.append(reservation)
        db.commit()
        
        client.post("/api/v1/auth/login", json={
            "email": "volunteer@test.com",
            "password": "testpass123"
        })
        
        # 測試狀態篩選
        response = client.get(
            "/api/v1/supplies/reservations",
            params={"status": ReservationStatus.PENDING.value}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["reservations"][0]["status"] == ReservationStatus.PENDING.value
        
        # 測試任務篩選
        response = client.get(
            "/api/v1/supplies/reservations",
            params={"task_id": str(task.id)}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["reservations"][0]["task_id"] == str(task.id)
        
        # 測試站點篩選
        response = client.get(
            "/api/v1/supplies/reservations",
            params={"station_id": str(station.id)}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3