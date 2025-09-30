"""
物資預訂和配送系統簡化測試（不需要認證）
"""
import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.models.supply import SupplyStation, InventoryItem, SupplyReservation, ReservationItem
from app.models.task import Task
from app.models.need import Need
from app.utils.constants import UserRole, ReservationStatus, TaskStatus, NeedStatus
from app.crud.supply import supply_crud
from app.services.supply_service import supply_service
from tests.conftest import create_test_user, create_test_supply_station, create_test_task, create_test_need


class TestSupplyReservationCRUD:
    """物資預訂 CRUD 測試"""
    
    def test_create_supply_reservation_crud(self, db_session: Session):
        """測試建立物資預訂 CRUD 操作"""
        # 建立測試資料
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER, email="volunteer@test.com")
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER, email="manager@test.com")
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        task = create_test_task(db_session, creator_id=str(volunteer.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="water",
            description="飲用水",
            is_available=True
        )
        db_session.add(inventory)
        db_session.commit()
        
        # 建立預訂資料
        from app.schemas.supply import SupplyReservationCreate, ReservationItemCreate
        
        reservation_data = SupplyReservationCreate(
            station_id=str(station.id),
            task_id=str(task.id),
            notes="緊急需要飲用水",
            reservation_items=[
                ReservationItemCreate(
                    supply_type="water",
                    requested_quantity=10,
                    notes="瓶裝水"
                )
            ]
        )
        
        # 測試建立預訂
        reservation = supply_crud.create_supply_reservation(
            db_session, reservation_data, str(volunteer.id), volunteer.role
        )
        
        assert reservation.station_id == station.id
        assert reservation.task_id == task.id
        assert reservation.status == ReservationStatus.PENDING.value
        assert len(reservation.reservation_items) == 1
        assert reservation.reservation_items[0].supply_type == "water"
        assert reservation.reservation_items[0].requested_quantity == 10
    
    def test_get_supply_reservation_crud(self, db_session: Session):
        """測試獲取物資預訂 CRUD 操作"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value,
            notes="測試預訂"
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 測試獲取預訂
        retrieved_reservation = supply_crud.get_supply_reservation(db_session, str(reservation.id))
        
        assert retrieved_reservation is not None
        assert retrieved_reservation.id == reservation.id
        assert retrieved_reservation.user_id == volunteer.id
        assert retrieved_reservation.station_id == station.id
    
    def test_confirm_supply_reservation_crud(self, db_session: Session):
        """測試確認物資預訂 CRUD 操作"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立預訂和預訂項目
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db_session.add(reservation)
        db_session.flush()
        
        reservation_item = ReservationItem(
            reservation_id=reservation.id,
            supply_type="water",
            requested_quantity=10
        )
        db_session.add(reservation_item)
        db_session.commit()
        
        # 測試確認預訂
        confirmed_items = [
            {
                "supply_type": "water",
                "confirmed_quantity": 8,
                "notes": "庫存不足，只能提供8瓶"
            }
        ]
        
        confirmed_reservation = supply_crud.confirm_supply_reservation(
            db_session, str(reservation.id), confirmed_items, str(manager.id), manager.role
        )
        
        assert confirmed_reservation.status == ReservationStatus.CONFIRMED.value
        assert confirmed_reservation.confirmed_at is not None
        assert confirmed_reservation.reservation_items[0].confirmed_quantity == 8
    
    def test_update_reservation_status_crud(self, db_session: Session):
        """測試更新預訂狀態 CRUD 操作"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立已確認的預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.CONFIRMED.value,
            confirmed_at=datetime.utcnow()
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 測試更新為已領取
        updated_reservation = supply_crud.update_reservation_status(
            db_session, str(reservation.id), ReservationStatus.PICKED_UP, 
            str(volunteer.id), volunteer.role
        )
        
        assert updated_reservation.status == ReservationStatus.PICKED_UP.value
        assert updated_reservation.picked_up_at is not None
        
        # 測試更新為已配送
        delivered_reservation = supply_crud.update_reservation_status(
            db_session, str(reservation.id), ReservationStatus.DELIVERED, 
            str(volunteer.id), volunteer.role
        )
        
        assert delivered_reservation.status == ReservationStatus.DELIVERED.value
        assert delivered_reservation.delivered_at is not None
    
    def test_invalid_status_transition_crud(self, db_session: Session):
        """測試無效的狀態轉換"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立待處理的預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 嘗試直接從 pending 跳到 delivered（無效轉換）
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            supply_crud.update_reservation_status(
                db_session, str(reservation.id), ReservationStatus.DELIVERED, 
                str(volunteer.id), volunteer.role
            )
        
        assert "不能從" in str(exc_info.value.detail)
    
    def test_cancel_supply_reservation_crud(self, db_session: Session):
        """測試取消物資預訂 CRUD 操作"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 測試取消預訂
        success = supply_crud.cancel_supply_reservation(
            db_session, str(reservation.id), str(volunteer.id), volunteer.role, "不再需要"
        )
        
        assert success is True
        
        # 驗證預訂已取消
        db_session.refresh(reservation)
        assert reservation.status == ReservationStatus.CANCELLED.value
        assert "不再需要" in reservation.notes
    
    def test_get_station_reservations_crud(self, db_session: Session):
        """測試獲取站點預訂列表 CRUD 操作"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立多個預訂
        reservations = []
        for i in range(3):
            reservation = SupplyReservation(
                user_id=volunteer.id,
                station_id=station.id,
                status=ReservationStatus.PENDING.value,
                notes=f"預訂 {i+1}"
            )
            db_session.add(reservation)
            reservations.append(reservation)
        db_session.commit()
        
        # 測試獲取站點預訂列表
        station_reservations, total = supply_crud.get_station_reservations(
            db_session, str(station.id)
        )
        
        assert total == 3
        assert len(station_reservations) == 3
        
        # 測試狀態篩選
        filtered_reservations, filtered_total = supply_crud.get_station_reservations(
            db_session, str(station.id), ReservationStatus.PENDING
        )
        
        assert filtered_total == 3
        assert all(r.status == ReservationStatus.PENDING.value for r in filtered_reservations)


class TestSupplyReservationService:
    """物資預訂服務測試"""
    
    def test_create_supply_reservation_service(self, db_session: Session):
        """測試建立物資預訂服務"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="water",
            is_available=True
        )
        db_session.add(inventory)
        db_session.commit()
        
        from app.schemas.supply import SupplyReservationCreate, ReservationItemCreate
        
        reservation_data = SupplyReservationCreate(
            station_id=str(station.id),
            reservation_items=[
                ReservationItemCreate(
                    supply_type="water",
                    requested_quantity=5
                )
            ]
        )
        
        # 測試服務層建立預訂
        reservation_response = supply_service.create_supply_reservation(
            db_session, reservation_data, str(volunteer.id), volunteer.role
        )
        
        assert reservation_response.station_id == str(station.id)
        assert reservation_response.status == ReservationStatus.PENDING
        assert len(reservation_response.reservation_items) == 1
        assert reservation_response.can_edit is True  # 預訂者可以編輯
    
    def test_get_supply_reservations_service(self, db_session: Session):
        """測試獲取物資預訂列表服務"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立預訂
        reservation = SupplyReservation(
            user_id=volunteer.id,
            station_id=station.id,
            status=ReservationStatus.PENDING.value
        )
        db_session.add(reservation)
        db_session.commit()
        
        # 測試服務層獲取預訂列表
        reservation_list = supply_service.get_supply_reservations(
            db_session, user_id=str(volunteer.id), user_role=volunteer.role
        )
        
        assert reservation_list.total == 1
        assert len(reservation_list.reservations) == 1
        assert reservation_list.reservations[0].id == str(reservation.id)
    
    def test_permission_checks_service(self, db_session: Session):
        """測試權限控制服務"""
        victim = create_test_user(db_session, role=UserRole.VICTIM)
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="water",
            is_available=True
        )
        db_session.add(inventory)
        db_session.commit()
        
        from app.schemas.supply import SupplyReservationCreate, ReservationItemCreate
        
        reservation_data = SupplyReservationCreate(
            station_id=str(station.id),
            reservation_items=[
                ReservationItemCreate(
                    supply_type="water",
                    requested_quantity=1
                )
            ]
        )
        
        # 受災戶不能預訂物資
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            supply_service.create_supply_reservation(
                db_session, reservation_data, str(victim.id), victim.role
            )
        
        assert "沒有權限預訂物資" in str(exc_info.value.detail)
        
        # 志工可以預訂物資
        reservation_response = supply_service.create_supply_reservation(
            db_session, reservation_data, str(volunteer.id), volunteer.role
        )
        
        assert reservation_response is not None
        assert reservation_response.status == ReservationStatus.PENDING


class TestSupplyDeliveryWorkflow:
    """物資配送工作流程測試"""
    
    def test_complete_delivery_workflow(self, db_session: Session):
        """測試完整的配送工作流程"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        need = create_test_need(db_session, reporter_id=str(volunteer.id))
        
        # 建立庫存
        inventory = InventoryItem(
            station_id=station.id,
            supply_type="water",
            is_available=True
        )
        db_session.add(inventory)
        db_session.commit()
        
        from app.schemas.supply import SupplyReservationCreate, ReservationItemCreate
        
        # 步驟1: 志工預訂物資
        reservation_data = SupplyReservationCreate(
            station_id=str(station.id),
            need_id=str(need.id),
            notes="為受災戶配送物資",
            reservation_items=[
                ReservationItemCreate(
                    supply_type="water",
                    requested_quantity=5,
                    notes="緊急需要"
                )
            ]
        )
        
        reservation_response = supply_service.create_supply_reservation(
            db_session, reservation_data, str(volunteer.id), volunteer.role
        )
        reservation_id = reservation_response.id
        
        # 步驟2: 站點管理者確認預訂
        confirmed_items = [
            {
                "supply_type": "water",
                "confirmed_quantity": 5,
                "notes": "已備貨完成"
            }
        ]
        
        confirmed_response = supply_service.confirm_supply_reservation(
            db_session, reservation_id, confirmed_items, str(manager.id), manager.role
        )
        
        assert confirmed_response.status == ReservationStatus.CONFIRMED
        
        # 步驟3: 志工領取物資
        picked_up_response = supply_service.update_reservation_status(
            db_session, reservation_id, ReservationStatus.PICKED_UP, 
            str(volunteer.id), volunteer.role
        )
        
        assert picked_up_response.status == ReservationStatus.PICKED_UP
        
        # 步驟4: 配送完成確認
        delivered_response = supply_service.update_reservation_status(
            db_session, reservation_id, ReservationStatus.DELIVERED, 
            str(volunteer.id), volunteer.role
        )
        
        assert delivered_response.status == ReservationStatus.DELIVERED
        assert delivered_response.delivered_at is not None
        
        # 驗證完整的配送記錄
        final_reservation = supply_service.get_supply_reservation(
            db_session, reservation_id, str(volunteer.id), volunteer.role
        )
        
        assert final_reservation.need_id == str(need.id)
        assert final_reservation.reserved_at is not None
        assert final_reservation.confirmed_at is not None
        assert final_reservation.picked_up_at is not None
        assert final_reservation.delivered_at is not None
    
    def test_supply_map_functionality(self, db_session: Session):
        """測試物資地圖功能（需求 6.1, 6.2）"""
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        
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
            db_session.add(item)
        db_session.commit()
        
        # 測試物資地圖
        map_response = supply_service.get_supply_map(db_session)
        
        assert len(map_response.stations) == 1
        station_data = map_response.stations[0]
        assert station_data.id == str(station.id)
        assert len(station_data.available_supplies) == 2
        
        # 驗證物資清單
        supply_types = [supply["type"] for supply in station_data.available_supplies]
        assert "water" in supply_types
        assert "rice" in supply_types
    
    def test_reservation_filtering(self, db_session: Session):
        """測試預訂篩選功能"""
        volunteer = create_test_user(db_session, role=UserRole.VOLUNTEER)
        manager = create_test_user(db_session, role=UserRole.SUPPLY_MANAGER)
        station = create_test_supply_station(db_session, manager_id=str(manager.id))
        task = create_test_task(db_session, creator_id=str(volunteer.id))
        
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
            db_session.add(reservation)
            reservations.append(reservation)
        db_session.commit()
        
        # 測試狀態篩選
        pending_reservations = supply_service.get_supply_reservations(
            db_session, user_id=str(volunteer.id), user_role=volunteer.role,
            status_filter=ReservationStatus.PENDING
        )
        
        assert pending_reservations.total == 1
        assert pending_reservations.reservations[0].status == ReservationStatus.PENDING
        
        # 測試任務篩選
        task_reservations = supply_service.get_supply_reservations(
            db_session, user_id=str(volunteer.id), user_role=volunteer.role,
            task_id=str(task.id)
        )
        
        assert task_reservations.total == 1
        assert task_reservations.reservations[0].task_id == str(task.id)
        
        # 測試站點篩選
        station_reservations = supply_service.get_supply_reservations(
            db_session, user_id=str(volunteer.id), user_role=volunteer.role,
            station_id=str(station.id)
        )
        
        assert station_reservations.total == 3