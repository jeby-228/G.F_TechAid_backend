"""
報表服務測試
"""
import pytest
import io
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.reporting_service import reporting_service
from app.models.user import User
from app.models.task import Task, TaskClaim
from app.models.need import Need
from app.models.supply import SupplyStation, SupplyReservation, ReservationItem
from app.models.system import SystemLog
from app.utils.constants import TaskStatus, NeedStatus, UserRole


class TestReportingService:
    """報表服務測試類"""
    
    def test_generate_disaster_relief_report_pdf(self, db: Session, test_user: User, test_tasks: list, test_needs: list):
        """測試生成救災活動PDF報表"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 生成PDF報表
        pdf_bytes = reporting_service.generate_disaster_relief_report(
            db, start_date, end_date, "pdf"
        )
        
        # 驗證返回的是bytes類型
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # 驗證PDF檔案標頭
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_generate_disaster_relief_report_csv(self, db: Session, test_user: User, test_tasks: list, test_needs: list):
        """測試生成救災活動CSV報表"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 生成CSV報表
        csv_bytes = reporting_service.generate_disaster_relief_report(
            db, start_date, end_date, "csv"
        )
        
        # 驗證返回的是bytes類型
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0
        
        # 驗證CSV內容包含BOM和標題
        csv_content = csv_bytes.decode('utf-8-sig')
        assert "救災活動報表" in csv_content
        assert "報表期間" in csv_content
    
    def test_generate_disaster_relief_report_excel(self, db: Session, test_user: User, test_tasks: list, test_needs: list):
        """測試生成救災活動Excel報表"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 生成Excel報表
        excel_bytes = reporting_service.generate_disaster_relief_report(
            db, start_date, end_date, "excel"
        )
        
        # 驗證返回的是bytes類型
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0
        
        # 驗證Excel檔案標頭（ZIP格式）
        assert excel_bytes.startswith(b'PK')
    
    def test_generate_task_completion_report_pdf(self, db: Session, test_user: User, test_tasks: list):
        """測試生成任務完成PDF報表"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 建立測試任務認領記錄
        task_claim = TaskClaim(
            task_id=test_tasks[0].id,
            user_id=test_user.id,
            claimed_at=datetime.utcnow() - timedelta(days=2),
            started_at=datetime.utcnow() - timedelta(days=2),
            completed_at=datetime.utcnow() - timedelta(days=1),
            status="completed"
        )
        db.add(task_claim)
        db.commit()
        
        # 生成PDF報表
        pdf_bytes = reporting_service.generate_task_completion_report(
            db, start_date, end_date, "pdf"
        )
        
        # 驗證返回的是bytes類型
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_generate_supply_flow_report_pdf(self, db: Session, test_user: User, test_supply_station: SupplyStation):
        """測試生成物資流向PDF報表"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 建立測試物資預訂記錄
        reservation = SupplyReservation(
            user_id=test_user.id,
            station_id=test_supply_station.id,
            status="confirmed",
            reserved_at=datetime.utcnow() - timedelta(days=2),
            confirmed_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(reservation)
        db.commit()
        
        # 建立預訂物資明細
        reservation_item = ReservationItem(
            reservation_id=reservation.id,
            supply_type="water",
            requested_quantity=10,
            confirmed_quantity=10
        )
        db.add(reservation_item)
        db.commit()
        
        # 生成PDF報表
        pdf_bytes = reporting_service.generate_supply_flow_report(
            db, start_date, end_date, "pdf"
        )
        
        # 驗證返回的是bytes類型
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_generate_system_usage_report_pdf(self, db: Session, test_user: User):
        """測試生成系統使用統計PDF報表"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 建立測試系統日誌記錄
        system_log = SystemLog(
            user_id=test_user.id,
            action="login",
            resource_type="user",
            resource_id=str(test_user.id),
            details={"ip_address": "127.0.0.1"},
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(system_log)
        db.commit()
        
        # 生成PDF報表
        pdf_bytes = reporting_service.generate_system_usage_report(
            db, start_date, end_date, "pdf"
        )
        
        # 驗證返回的是bytes類型
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_generate_report_invalid_format(self, db: Session):
        """測試無效格式的報表生成"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 測試無效格式
        with pytest.raises(ValueError, match="不支援的格式類型"):
            reporting_service.generate_disaster_relief_report(
                db, start_date, end_date, "invalid_format"
            )
    
    def test_collect_disaster_relief_data(self, db: Session, test_user: User, test_tasks: list, test_needs: list):
        """測試收集救災活動資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 收集資料
        data = reporting_service._collect_disaster_relief_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert "report_title" in data
        assert "period" in data
        assert "summary" in data
        assert "details" in data
        assert "generated_at" in data
        
        # 驗證期間資訊
        assert data["period"]["start_date"] == start_date.strftime("%Y-%m-%d")
        assert data["period"]["end_date"] == end_date.strftime("%Y-%m-%d")
        assert data["period"]["days"] == (end_date - start_date).days
        
        # 驗證詳細資料
        assert "tasks" in data["details"]
        assert "needs" in data["details"]
        assert isinstance(data["details"]["tasks"], list)
        assert isinstance(data["details"]["needs"], list)
    
    def test_collect_task_completion_data(self, db: Session, test_user: User, test_tasks: list):
        """測試收集任務完成資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 建立測試任務認領記錄
        task_claim = TaskClaim(
            task_id=test_tasks[0].id,
            user_id=test_user.id,
            claimed_at=datetime.utcnow() - timedelta(days=2),
            completed_at=datetime.utcnow() - timedelta(days=1),
            status="completed"
        )
        db.add(task_claim)
        db.commit()
        
        # 收集資料
        data = reporting_service._collect_task_completion_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert "report_title" in data
        assert "period" in data
        assert "summary" in data
        assert "details" in data
        
        # 驗證詳細資料
        assert "task_claims" in data["details"]
        assert isinstance(data["details"]["task_claims"], list)
        
        # 如果有任務認領記錄，驗證資料內容
        if data["details"]["task_claims"]:
            claim_data = data["details"]["task_claims"][0]
            assert "任務ID" in claim_data
            assert "志工姓名" in claim_data
            assert "認領時間" in claim_data
    
    def test_collect_supply_flow_data(self, db: Session, test_user: User, test_supply_station: SupplyStation):
        """測試收集物資流向資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 建立測試物資預訂記錄
        reservation = SupplyReservation(
            user_id=test_user.id,
            station_id=test_supply_station.id,
            status="confirmed",
            reserved_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(reservation)
        db.commit()
        
        # 收集資料
        data = reporting_service._collect_supply_flow_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert "report_title" in data
        assert "period" in data
        assert "summary" in data
        assert "details" in data
        
        # 驗證詳細資料
        assert "reservations" in data["details"]
        assert isinstance(data["details"]["reservations"], list)
    
    def test_collect_system_usage_data(self, db: Session, test_user: User):
        """測試收集系統使用資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 收集資料
        data = reporting_service._collect_system_usage_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert "report_title" in data
        assert "period" in data
        assert "summary" in data
        assert "details" in data
        
        # 驗證摘要資料
        assert "total_users" in data["summary"]
        assert "new_users" in data["summary"]
        assert "role_distribution" in data["summary"]
        
        # 驗證詳細資料
        assert "user_activities" in data["details"]
        assert isinstance(data["details"]["user_activities"], list)
    
    def test_generate_pdf_report_structure(self, db: Session):
        """測試PDF報表結構生成"""
        # 建立測試資料
        test_data = {
            "report_title": "測試報表",
            "period": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "days": 7
            },
            "summary": {
                "total_items": 10,
                "completed_items": 8,
                "completion_rate": 80.0
            },
            "details": {
                "items": [
                    {"項目": "測試項目1", "狀態": "完成", "數量": 5},
                    {"項目": "測試項目2", "狀態": "進行中", "數量": 3}
                ]
            },
            "generated_at": "2024-01-07 12:00:00"
        }
        
        # 生成PDF
        pdf_bytes = reporting_service._generate_pdf_report(test_data, "測試報表")
        
        # 驗證PDF生成成功
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_generate_csv_report_structure(self, db: Session):
        """測試CSV報表結構生成"""
        # 建立測試資料
        test_data = {
            "report_title": "測試報表",
            "period": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "days": 7
            },
            "details": {
                "items": [
                    {"項目": "測試項目1", "狀態": "完成", "數量": 5},
                    {"項目": "測試項目2", "狀態": "進行中", "數量": 3}
                ]
            },
            "generated_at": "2024-01-07 12:00:00"
        }
        
        # 生成CSV
        csv_bytes = reporting_service._generate_csv_report(test_data)
        
        # 驗證CSV生成成功
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0
        
        # 驗證CSV內容
        csv_content = csv_bytes.decode('utf-8-sig')
        assert "測試報表" in csv_content
        assert "項目,狀態,數量" in csv_content
        assert "測試項目1,完成,5" in csv_content
    
    def test_generate_excel_report_structure(self, db: Session):
        """測試Excel報表結構生成"""
        # 建立測試資料
        test_data = {
            "report_title": "測試報表",
            "period": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "days": 7
            },
            "summary": {
                "total_items": 10,
                "completed_items": 8
            },
            "details": {
                "items": [
                    {"項目": "測試項目1", "狀態": "完成", "數量": 5},
                    {"項目": "測試項目2", "狀態": "進行中", "數量": 3}
                ]
            },
            "generated_at": "2024-01-07 12:00:00"
        }
        
        # 生成Excel
        excel_bytes = reporting_service._generate_excel_report(test_data, "測試報表")
        
        # 驗證Excel生成成功
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0
        assert excel_bytes.startswith(b'PK')  # ZIP格式標頭
    
    def test_report_date_range_validation(self, db: Session):
        """測試報表日期範圍驗證"""
        # 測試正常日期範圍
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 這應該正常工作
        data = reporting_service._collect_disaster_relief_data(db, start_date, end_date)
        assert data is not None
        
        # 測試開始日期晚於結束日期的情況
        invalid_start = datetime.utcnow()
        invalid_end = datetime.utcnow() - timedelta(days=7)
        
        # 這應該仍然工作，但天數會是負數
        data = reporting_service._collect_disaster_relief_data(db, invalid_start, invalid_end)
        assert data["period"]["days"] < 0
    
    def test_empty_data_handling(self, db: Session):
        """測試空資料處理"""
        # 使用未來日期確保沒有資料
        start_date = datetime.utcnow() + timedelta(days=1)
        end_date = datetime.utcnow() + timedelta(days=7)
        
        # 生成報表應該仍然成功，只是沒有詳細資料
        pdf_bytes = reporting_service.generate_disaster_relief_report(
            db, start_date, end_date, "pdf"
        )
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_large_dataset_handling(self, db: Session, test_user: User):
        """測試大量資料處理"""
        # 建立多個測試任務
        tasks = []
        for i in range(100):
            task = Task(
                creator_id=test_user.id,
                title=f"測試任務 {i}",
                description=f"這是第 {i} 個測試任務",
                task_type="cleanup",
                status=TaskStatus.COMPLETED if i % 2 == 0 else TaskStatus.AVAILABLE,
                location_data={"address": f"測試地址 {i}", "coordinates": {"lat": 23.9739, "lng": 121.6015}},
                required_volunteers=1,
                priority_level=1,
                created_at=datetime.utcnow() - timedelta(days=1)
            )
            db.add(task)
            tasks.append(task)
        
        db.commit()
        
        # 生成報表
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        pdf_bytes = reporting_service.generate_disaster_relief_report(
            db, start_date, end_date, "pdf"
        )
        
        # 驗證大量資料也能正常處理
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
        
        # 清理測試資料
        for task in tasks:
            db.delete(task)
        db.commit()
    
    def test_export_tasks_data(self, db: Session, test_user: User, test_tasks: list):
        """測試匯出任務資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 匯出任務資料
        task_data = reporting_service._export_tasks_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert isinstance(task_data, list)
        if task_data:
            assert "任務ID" in task_data[0]
            assert "任務標題" in task_data[0]
            assert "任務類型" in task_data[0]
            assert "狀態" in task_data[0]
    
    def test_export_needs_data(self, db: Session, test_user: User, test_needs: list):
        """測試匯出需求資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 匯出需求資料
        need_data = reporting_service._export_needs_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert isinstance(need_data, list)
        if need_data:
            assert "需求ID" in need_data[0]
            assert "需求標題" in need_data[0]
            assert "需求類型" in need_data[0]
            assert "狀態" in need_data[0]
    
    def test_export_supplies_data(self, db: Session, test_user: User, test_supply_station: SupplyStation):
        """測試匯出物資資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 建立測試物資預訂記錄
        reservation = SupplyReservation(
            user_id=test_user.id,
            station_id=test_supply_station.id,
            status="confirmed",
            reserved_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(reservation)
        db.commit()
        
        # 匯出物資資料
        supply_data = reporting_service._export_supplies_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert isinstance(supply_data, list)
        if supply_data:
            assert "預訂ID" in supply_data[0]
            assert "物資站點" in supply_data[0]
            assert "預訂者" in supply_data[0]
            assert "狀態" in supply_data[0]
    
    def test_export_users_data(self, db: Session, test_user: User):
        """測試匯出用戶資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 匯出用戶資料
        user_data = reporting_service._export_users_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert isinstance(user_data, list)
        if user_data:
            assert "用戶ID" in user_data[0]
            assert "用戶姓名" in user_data[0]
            assert "用戶角色" in user_data[0]
            assert "審核狀態" in user_data[0]
    
    def test_export_logs_data(self, db: Session, test_user: User):
        """測試匯出系統日誌資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 建立測試系統日誌記錄
        system_log = SystemLog(
            user_id=test_user.id,
            action="test_action",
            resource_type="test",
            resource_id=str(test_user.id),
            details={"test": "data"},
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(system_log)
        db.commit()
        
        # 匯出日誌資料
        log_data = reporting_service._export_logs_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert isinstance(log_data, list)
        if log_data:
            assert "日誌ID" in log_data[0]
            assert "用戶" in log_data[0]
            assert "操作" in log_data[0]
            assert "創建時間" in log_data[0]
    
    def test_export_data_by_type_csv(self, db: Session, test_user: User, test_tasks: list):
        """測試按類型匯出CSV資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 匯出任務資料為CSV
        csv_bytes = reporting_service.export_data_by_type(
            db, "tasks", start_date, end_date, "csv"
        )
        
        # 驗證CSV匯出
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0
        
        # 驗證CSV內容
        csv_content = csv_bytes.decode('utf-8-sig')
        assert "任務ID" in csv_content
    
    def test_export_data_by_type_excel(self, db: Session, test_user: User, test_tasks: list):
        """測試按類型匯出Excel資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 匯出任務資料為Excel
        excel_bytes = reporting_service.export_data_by_type(
            db, "tasks", start_date, end_date, "excel"
        )
        
        # 驗證Excel匯出
        assert isinstance(excel_bytes, bytes)
        assert len(excel_bytes) > 0
        assert excel_bytes.startswith(b'PK')  # ZIP格式標頭
    
    def test_export_data_by_type_json(self, db: Session, test_user: User, test_tasks: list):
        """測試按類型匯出JSON資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 匯出任務資料為JSON
        json_bytes = reporting_service.export_data_by_type(
            db, "tasks", start_date, end_date, "json"
        )
        
        # 驗證JSON匯出
        assert isinstance(json_bytes, bytes)
        assert len(json_bytes) > 0
        
        # 驗證JSON內容
        import json
        json_content = json.loads(json_bytes.decode('utf-8'))
        assert isinstance(json_content, list)
    
    def test_export_data_invalid_type(self, db: Session):
        """測試無效資料類型匯出"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 測試無效資料類型
        with pytest.raises(ValueError, match="不支援的資料類型"):
            reporting_service.export_data_by_type(
                db, "invalid_type", start_date, end_date, "csv"
            )
    
    def test_export_data_invalid_format(self, db: Session):
        """測試無效格式匯出"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 測試無效格式
        with pytest.raises(ValueError, match="不支援的格式類型"):
            reporting_service.export_data_by_type(
                db, "tasks", start_date, end_date, "invalid_format"
            )
    
    def test_export_with_filters(self, db: Session, test_user: User, test_tasks: list):
        """測試帶篩選條件的資料匯出"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 使用篩選條件匯出任務資料
        filters = {"status": "available", "task_type": "cleanup"}
        task_data = reporting_service._export_tasks_data(db, start_date, end_date, filters)
        
        # 驗證篩選結果
        assert isinstance(task_data, list)
        for task in task_data:
            if task.get("狀態"):
                assert task["狀態"] == "available"
            if task.get("任務類型"):
                assert task["任務類型"] == "cleanup"
    
    def test_generate_comprehensive_analysis_report(self, db: Session, test_user: User, test_tasks: list, test_needs: list):
        """測試生成綜合分析報表"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 生成綜合分析報表
        pdf_bytes = reporting_service.generate_comprehensive_analysis_report(
            db, start_date, end_date, "pdf"
        )
        
        # 驗證報表生成
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')
    
    def test_collect_comprehensive_analysis_data(self, db: Session, test_user: User, test_tasks: list, test_needs: list):
        """測試收集綜合分析資料"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 收集綜合分析資料
        data = reporting_service._collect_comprehensive_analysis_data(db, start_date, end_date)
        
        # 驗證資料結構
        assert "report_title" in data
        assert "period" in data
        assert "summary" in data
        assert "details" in data
        
        # 驗證摘要資料
        assert "disaster_progress" in data["summary"]
        assert "task_completion" in data["summary"]
        assert "supply_flow" in data["summary"]
        assert "user_activity" in data["summary"]
        assert "location_analysis" in data["summary"]
        
        # 驗證詳細資料
        assert "daily_trends" in data["details"]
        assert isinstance(data["details"]["daily_trends"], list)
    
    def test_empty_export_data_handling(self, db: Session):
        """測試空資料匯出處理"""
        # 測試空資料的CSV匯出
        empty_data = []
        csv_bytes = reporting_service._generate_csv_export(empty_data)
        assert csv_bytes == b""
        
        # 測試空資料的Excel匯出
        excel_bytes = reporting_service._generate_excel_export(empty_data)
        assert excel_bytes == b""
        
        # 測試空資料的JSON匯出
        json_bytes = reporting_service._generate_json_export(empty_data)
        assert json_bytes == b"[]"