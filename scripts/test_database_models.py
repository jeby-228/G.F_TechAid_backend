#!/usr/bin/env python3
"""
測試資料庫模型腳本
驗證所有模型是否正確定義
"""

import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_model_imports():
    """測試模型匯入"""
    print("測試模型匯入...")
    
    try:
        # 測試基礎模型
        from app.models.base import BaseModel
        print("✓ BaseModel 匯入成功")
        
        # 測試用戶相關模型
        from app.models.user import UserRole, User, Organization
        print("✓ 用戶模型匯入成功")
        
        # 測試任務相關模型
        from app.models.task import TaskType, TaskStatus, Task, TaskClaim
        print("✓ 任務模型匯入成功")
        
        # 測試需求相關模型
        from app.models.need import NeedType, NeedStatus, Need, NeedAssignment
        print("✓ 需求模型匯入成功")
        
        # 測試物資相關模型
        from app.models.supply import (
            SupplyType, SupplyStation, InventoryItem,
            ReservationStatus, SupplyReservation, ReservationItem
        )
        print("✓ 物資模型匯入成功")
        
        # 測試系統相關模型
        from app.models.system import Announcement, Notification, SystemLog, Shelter
        print("✓ 系統模型匯入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 模型匯入失敗: {e}")
        return False


def test_model_attributes():
    """測試模型屬性"""
    print("\n測試模型屬性...")
    
    try:
        from app.models.user import UserRole, User, Organization
        from app.models.task import TaskType, TaskStatus, Task, TaskClaim
        from app.models.need import NeedType, NeedStatus, Need, NeedAssignment
        from app.models.supply import (
            SupplyType, SupplyStation, InventoryItem,
            ReservationStatus, SupplyReservation, ReservationItem
        )
        from app.models.system import Announcement, Notification, SystemLog, Shelter
        
        # 測試表格名稱
        models_and_tables = [
            (UserRole, "user_roles"),
            (User, "users"),
            (Organization, "organizations"),
            (TaskType, "task_types"),
            (TaskStatus, "task_statuses"),
            (Task, "tasks"),
            (TaskClaim, "task_claims"),
            (NeedType, "need_types"),
            (NeedStatus, "need_statuses"),
            (Need, "needs"),
            (NeedAssignment, "need_assignments"),
            (SupplyType, "supply_types"),
            (SupplyStation, "supply_stations"),
            (InventoryItem, "inventory_items"),
            (ReservationStatus, "reservation_statuses"),
            (SupplyReservation, "supply_reservations"),
            (ReservationItem, "reservation_items"),
            (Announcement, "announcements"),
            (Notification, "notifications"),
            (SystemLog, "system_logs"),
            (Shelter, "shelters")
        ]
        
        for model_class, expected_table in models_and_tables:
            actual_table = model_class.__tablename__
            if actual_table == expected_table:
                print(f"✓ {model_class.__name__}: {actual_table}")
            else:
                print(f"✗ {model_class.__name__}: 期望 {expected_table}, 實際 {actual_table}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ 模型屬性測試失敗: {e}")
        return False


def test_database_metadata():
    """測試資料庫元資料"""
    print("\n測試資料庫元資料...")
    
    try:
        from app.core.database import Base
        # 匯入所有模型以確保它們被註冊
        import app.models
        
        # 檢查所有表格是否在元資料中
        tables = Base.metadata.tables
        print(f"發現 {len(tables)} 個資料表:")
        
        for table_name in sorted(tables.keys()):
            print(f"  - {table_name}")
        
        # 驗證關鍵表格存在
        required_tables = [
            "user_roles", "users", "organizations",
            "task_types", "task_statuses", "tasks", "task_claims",
            "need_types", "need_statuses", "needs", "need_assignments",
            "supply_types", "supply_stations", "inventory_items",
            "reservation_statuses", "supply_reservations", "reservation_items",
            "announcements", "notifications", "system_logs", "shelters"
        ]
        
        missing_tables = []
        for table in required_tables:
            if table not in tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"✗ 缺少表格: {missing_tables}")
            return False
        
        print("✓ 所有必要的表格都已定義")
        return True
        
    except Exception as e:
        print(f"✗ 資料庫元資料測試失敗: {e}")
        return False


def main():
    """主函數"""
    print("開始測試資料庫模型...")
    print("=" * 50)
    
    tests = [
        test_model_imports,
        test_model_attributes,
        test_database_metadata
    ]
    
    all_passed = True
    for test_func in tests:
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有測試通過！資料庫模型定義正確。")
        return 0
    else:
        print("✗ 部分測試失敗，請檢查模型定義。")
        return 1


if __name__ == "__main__":
    sys.exit(main())