"""
監控服務單元測試
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.services.monitoring_service import monitoring_service
from app.models.user import User
from app.models.task import Task, TaskClaim
from app.models.need import Need, NeedAssignment
from app.models.supply import SupplyStation, InventoryItem, SupplyReservation, ReservationItem
from app.models.system import SystemLog
from app.utils.constants import UserRole, TaskStatus, NeedStatus


class TestMonitoringService:
    """監控服務測試類"""
    
    def test_get_real_time_statistics(self, db: Session, sample_users, sample_tasks, sample_needs, sample_supply_stations):
        """測試獲取即時統計資料"""
        # 執行測試
        stats = monitoring_service.get_real_time_statistics(db)
        
        # 驗證結果結構
        assert "overview" in stats
        assert "today_stats" in stats
        assert "user_distribution" in stats
        assert "last_updated" in stats
        
        # 驗證總覽統計
        overview = stats["overview"]
        assert "total_users" in overview
        assert "total_tasks" in overview
        assert "total_needs" in overview
        assert "total_supply_stations" in overview
        assert "active_tasks" in overview
        assert "open_needs" in overview
        
        # 驗證數據類型
        assert isinstance(overview["total_users"], int)
        assert isinstance(overview["total_tasks"], int)
        assert isinstance(overview["total_needs"], int)
        assert isinstance(overview["total_supply_stations"], int)
        assert isinstance(overview["active_tasks"], int)
        assert isinstance(overview["open_needs"], int)
        
        # 驗證今日統計
        today_stats = stats["today_stats"]
        assert "new_users" in today_stats
        assert "new_tasks" in today_stats
        assert "new_needs" in today_stats
        
        # 驗證用戶分布
        user_distribution = stats["user_distribution"]
        assert isinstance(user_distribution, dict)
    
    def test_get_disaster_relief_progress(self, db: Session, sample_tasks, sample_needs):
        """測試獲取救災進度追蹤統計"""
        days = 7
        
        # 執行測試
        progress = monitoring_service.get_disaster_relief_progress(db, days)
        
        # 驗證結果結構
        assert "period" in progress
        assert "task_progress" in progress
        assert "need_progress" in progress
        assert "overall_completion" in progress
        assert "daily_progress" in progress
        assert "urgency_analysis" in progress
        
        # 驗證時間段資訊
        period = progress["period"]
        assert "start_date" in period
        assert "end_date" in period
        assert period["days"] == days
        
        # 驗證任務進度
        task_progress = progress["task_progress"]
        assert "status_distribution" in task_progress
        assert "total_tasks" in task_progress
        assert "completed_tasks" in task_progress
        assert "completion_rate" in task_progress
        
        # 驗證需求進度
        need_progress = progress["need_progress"]
        assert "status_distribution" in need_progress
        assert "total_needs" in need_progress
        assert "resolved_needs" in need_progress
        assert "resolution_rate" in need_progress
        
        # 驗證整體完成率
        overall_completion = progress["overall_completion"]
        assert "task_completion_rate" in overall_completion
        assert "need_resolution_rate" in overall_completion
        assert "overall_completion_rate" in overall_completion
        
        # 驗證每日進度是列表
        assert isinstance(progress["daily_progress"], list)
        
        # 驗證緊急程度分析
        urgency_analysis = progress["urgency_analysis"]
        assert "need_urgency_distribution" in urgency_analysis
        assert "high_priority_tasks" in urgency_analysis
        assert "high_urgency_needs" in urgency_analysis
    
    def test_get_task_completion_statistics(self, db: Session, sample_tasks, sample_task_claims):
        """測試獲取任務完成率統計"""
        days = 30
        
        # 執行測試
        stats = monitoring_service.get_task_completion_statistics(db, days)
        
        # 驗證結果結構
        assert "period" in stats
        assert "overall" in stats
        assert "by_task_type" in stats
        assert "average_completion_time_hours" in stats
        assert "volunteer_efficiency" in stats
        
        # 驗證整體統計
        overall = stats["overall"]
        assert "total_tasks" in overall
        assert "completed_tasks" in overall
        assert "completion_rate" in overall
        
        # 驗證按任務類型統計
        by_task_type = stats["by_task_type"]
        assert isinstance(by_task_type, list)
        
        if by_task_type:
            task_type_stat = by_task_type[0]
            assert "task_type" in task_type_stat
            assert "total" in task_type_stat
            assert "completed" in task_type_stat
            assert "completion_rate" in task_type_stat
        
        # 驗證志工效率統計
        volunteer_efficiency = stats["volunteer_efficiency"]
        assert "active_volunteers" in volunteer_efficiency
        assert "total_completed_tasks" in volunteer_efficiency
        assert "avg_tasks_per_volunteer" in volunteer_efficiency
        assert "top_volunteers" in volunteer_efficiency
        
        # 驗證平均完成時間是數字
        assert isinstance(stats["average_completion_time_hours"], (int, float))
    
    def test_get_supply_flow_monitoring(self, db: Session, sample_supply_reservations):
        """測試獲取物資流向監控統計"""
        days = 7
        
        # 執行測試
        monitoring = monitoring_service.get_supply_flow_monitoring(db, days)
        
        # 驗證結果結構
        assert "period" in monitoring
        assert "reservation_stats" in monitoring
        assert "station_activity" in monitoring
        assert "supply_type_flow" in monitoring
        assert "delivery_efficiency" in monitoring
        
        # 驗證預訂統計
        reservation_stats = monitoring["reservation_stats"]
        assert "status_distribution" in reservation_stats
        assert "total_reservations" in reservation_stats
        assert "delivered_reservations" in reservation_stats
        assert "delivery_rate" in reservation_stats
        
        # 驗證站點活動是列表
        assert isinstance(monitoring["station_activity"], list)
        
        # 驗證物資類型流向是列表
        assert isinstance(monitoring["supply_type_flow"], list)
        
        # 驗證配送效率
        delivery_efficiency = monitoring["delivery_efficiency"]
        assert "avg_delivery_time_hours" in delivery_efficiency
        assert "total_confirmed_reservations" in delivery_efficiency
        assert "total_delivered_reservations" in delivery_efficiency
        assert "delivery_success_rate" in delivery_efficiency
    
    def test_get_inventory_statistics(self, db: Session, sample_supply_stations, sample_inventory_items):
        """測試獲取庫存統計"""
        # 執行測試
        stats = monitoring_service.get_inventory_statistics(db)
        
        # 驗證結果結構
        assert "overview" in stats
        assert "by_supply_type" in stats
        assert "by_station" in stats
        assert "low_inventory_alerts" in stats
        assert "last_updated" in stats
        
        # 驗證總覽
        overview = stats["overview"]
        assert "total_active_stations" in overview
        assert "total_available_items" in overview
        
        # 驗證按物資類型統計
        by_supply_type = stats["by_supply_type"]
        assert isinstance(by_supply_type, dict)
        
        # 驗證按站點統計
        by_station = stats["by_station"]
        assert isinstance(by_station, list)
        
        # 驗證低庫存警告
        low_inventory_alerts = stats["low_inventory_alerts"]
        assert isinstance(low_inventory_alerts, list)
    
    def test_get_system_activity_log(self, db: Session, sample_system_logs):
        """測試獲取系統活動日誌"""
        hours = 24
        limit = 100
        
        # 執行測試
        activity_log = monitoring_service.get_system_activity_log(db, hours, limit)
        
        # 驗證結果結構
        assert "period" in activity_log
        assert "summary" in activity_log
        assert "activity_counts" in activity_log
        assert "recent_logs" in activity_log
        
        # 驗證時間段
        period = activity_log["period"]
        assert "start_time" in period
        assert "end_time" in period
        assert period["hours"] == hours
        
        # 驗證摘要
        summary = activity_log["summary"]
        assert "active_users" in summary
        assert "total_actions" in summary
        
        # 驗證活動計數
        activity_counts = activity_log["activity_counts"]
        assert isinstance(activity_counts, dict)
        
        # 驗證最近日誌
        recent_logs = activity_log["recent_logs"]
        assert isinstance(recent_logs, list)
        assert len(recent_logs) <= limit
    
    def test_calculate_overall_completion_rate(self, db: Session):
        """測試計算整體完成率"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 執行測試
        completion = monitoring_service._calculate_overall_completion_rate(db, start_date, end_date)
        
        # 驗證結果結構
        assert "task_completion_rate" in completion
        assert "need_resolution_rate" in completion
        assert "overall_completion_rate" in completion
        assert "total_items" in completion
        assert "completed_items" in completion
        
        # 驗證數據類型和範圍
        assert isinstance(completion["task_completion_rate"], (int, float))
        assert isinstance(completion["need_resolution_rate"], (int, float))
        assert isinstance(completion["overall_completion_rate"], (int, float))
        assert 0 <= completion["task_completion_rate"] <= 100
        assert 0 <= completion["need_resolution_rate"] <= 100
        assert 0 <= completion["overall_completion_rate"] <= 100
    
    def test_get_daily_progress_trend(self, db: Session):
        """測試獲取每日進度趨勢"""
        start_date = datetime.utcnow() - timedelta(days=3)
        end_date = datetime.utcnow()
        
        # 執行測試
        daily_trends = monitoring_service._get_daily_progress_trend(db, start_date, end_date)
        
        # 驗證結果是列表
        assert isinstance(daily_trends, list)
        
        # 驗證每日趨勢項目結構
        if daily_trends:
            trend = daily_trends[0]
            assert "date" in trend
            assert "completed_tasks" in trend
            assert "resolved_needs" in trend
            assert "new_tasks" in trend
            assert "new_needs" in trend
            assert "total_completed" in trend
            assert "total_new" in trend
            
            # 驗證數據類型
            assert isinstance(trend["completed_tasks"], int)
            assert isinstance(trend["resolved_needs"], int)
            assert isinstance(trend["new_tasks"], int)
            assert isinstance(trend["new_needs"], int)
    
    def test_get_urgency_analysis(self, db: Session):
        """測試獲取緊急程度分析"""
        # 執行測試
        urgency_analysis = monitoring_service._get_urgency_analysis(db)
        
        # 驗證結果結構
        assert "need_urgency_distribution" in urgency_analysis
        assert "high_priority_tasks" in urgency_analysis
        assert "high_urgency_needs" in urgency_analysis
        assert "total_urgent_items" in urgency_analysis
        
        # 驗證數據類型
        assert isinstance(urgency_analysis["need_urgency_distribution"], dict)
        assert isinstance(urgency_analysis["high_priority_tasks"], int)
        assert isinstance(urgency_analysis["high_urgency_needs"], int)
        assert isinstance(urgency_analysis["total_urgent_items"], int)
    
    def test_calculate_average_completion_time(self, db: Session, sample_task_claims):
        """測試計算平均完成時間"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        # 執行測試
        avg_time = monitoring_service._calculate_average_completion_time(db, start_date, end_date)
        
        # 驗證結果是數字且非負
        assert isinstance(avg_time, (int, float))
        assert avg_time >= 0
    
    def test_get_volunteer_efficiency_stats(self, db: Session, sample_task_claims):
        """測試獲取志工效率統計"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        # 執行測試
        efficiency = monitoring_service._get_volunteer_efficiency_stats(db, start_date, end_date)
        
        # 驗證結果結構
        assert "active_volunteers" in efficiency
        assert "total_completed_tasks" in efficiency
        assert "avg_tasks_per_volunteer" in efficiency
        assert "top_volunteers" in efficiency
        
        # 驗證數據類型
        assert isinstance(efficiency["active_volunteers"], int)
        assert isinstance(efficiency["total_completed_tasks"], int)
        assert isinstance(efficiency["avg_tasks_per_volunteer"], (int, float))
        assert isinstance(efficiency["top_volunteers"], list)
        
        # 驗證頂級志工結構
        if efficiency["top_volunteers"]:
            top_volunteer = efficiency["top_volunteers"][0]
            assert "user_id" in top_volunteer
            assert "user_name" in top_volunteer
            assert "completed_tasks" in top_volunteer
    
    def test_get_supply_reservation_stats(self, db: Session):
        """測試獲取物資預訂統計"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 執行測試
        reservation_stats = monitoring_service._get_supply_reservation_stats(db, start_date, end_date)
        
        # 驗證結果結構
        assert "status_distribution" in reservation_stats
        assert "total_reservations" in reservation_stats
        assert "delivered_reservations" in reservation_stats
        assert "delivery_rate" in reservation_stats
        
        # 驗證數據類型
        assert isinstance(reservation_stats["status_distribution"], dict)
        assert isinstance(reservation_stats["total_reservations"], int)
        assert isinstance(reservation_stats["delivered_reservations"], int)
        assert isinstance(reservation_stats["delivery_rate"], (int, float))
        assert 0 <= reservation_stats["delivery_rate"] <= 100
    
    def test_get_station_activity_stats(self, db: Session):
        """測試獲取物資站點活動統計"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 執行測試
        station_stats = monitoring_service._get_station_activity_stats(db, start_date, end_date)
        
        # 驗證結果是列表
        assert isinstance(station_stats, list)
        
        # 驗證站點統計項目結構
        if station_stats:
            station_stat = station_stats[0]
            assert "station_name" in station_stat
            assert "reservation_count" in station_stat
            assert isinstance(station_stat["reservation_count"], int)
    
    def test_get_supply_type_flow_stats(self, db: Session):
        """測試獲取物資類型流向統計"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 執行測試
        flow_stats = monitoring_service._get_supply_type_flow_stats(db, start_date, end_date)
        
        # 驗證結果是列表
        assert isinstance(flow_stats, list)
        
        # 驗證流向統計項目結構
        if flow_stats:
            flow_stat = flow_stats[0]
            assert "supply_type" in flow_stat
            assert "total_quantity" in flow_stat
            assert "reservation_count" in flow_stat
            assert isinstance(flow_stat["total_quantity"], int)
            assert isinstance(flow_stat["reservation_count"], int)
    
    def test_get_delivery_efficiency_stats(self, db: Session):
        """測試獲取配送效率統計"""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        # 執行測試
        efficiency = monitoring_service._get_delivery_efficiency_stats(db, start_date, end_date)
        
        # 驗證結果結構
        assert "avg_delivery_time_hours" in efficiency
        assert "total_confirmed_reservations" in efficiency
        assert "total_delivered_reservations" in efficiency
        assert "delivery_success_rate" in efficiency
        
        # 驗證數據類型和範圍
        assert isinstance(efficiency["avg_delivery_time_hours"], (int, float))
        assert isinstance(efficiency["total_confirmed_reservations"], int)
        assert isinstance(efficiency["total_delivered_reservations"], int)
        assert isinstance(efficiency["delivery_success_rate"], (int, float))
        assert efficiency["avg_delivery_time_hours"] >= 0
        assert 0 <= efficiency["delivery_success_rate"] <= 100
    
    def test_empty_database_statistics(self, db: Session):
        """測試空資料庫的統計資料"""
        # 執行測試
        stats = monitoring_service.get_real_time_statistics(db)
        
        # 驗證空資料庫的統計結果
        overview = stats["overview"]
        assert overview["total_users"] == 0
        assert overview["total_tasks"] == 0
        assert overview["total_needs"] == 0
        assert overview["total_supply_stations"] == 0
        assert overview["active_tasks"] == 0
        assert overview["open_needs"] == 0
        
        today_stats = stats["today_stats"]
        assert today_stats["new_users"] == 0
        assert today_stats["new_tasks"] == 0
        assert today_stats["new_needs"] == 0
    
    def test_monitoring_service_error_handling(self, db: Session):
        """測試監控服務的錯誤處理"""
        # 測試無效的天數參數
        with patch.object(db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database error")
            
            # 應該能夠處理資料庫錯誤
            try:
                monitoring_service.get_real_time_statistics(db)
            except Exception as e:
                assert "Database error" in str(e)
    
    def test_monitoring_service_performance(self, db: Session):
        """測試監控服務的效能"""
        import time
        
        # 測試即時統計的執行時間
        start_time = time.time()
        monitoring_service.get_real_time_statistics(db)
        execution_time = time.time() - start_time
        
        # 驗證執行時間在合理範圍內（應該小於1秒）
        assert execution_time < 1.0, f"Real-time statistics took too long: {execution_time}s"
        
        # 測試救災進度統計的執行時間
        start_time = time.time()
        monitoring_service.get_disaster_relief_progress(db, 7)
        execution_time = time.time() - start_time
        
        # 驗證執行時間在合理範圍內（應該小於2秒）
        assert execution_time < 2.0, f"Disaster relief progress took too long: {execution_time}s"


# 測試數據 fixtures
@pytest.fixture
def sample_users(db: Session):
    """創建測試用戶數據"""
    users = []
    for i in range(5):
        user = User(
            email=f"user{i}@test.com",
            name=f"Test User {i}",
            role=UserRole.VOLUNTEER.value,
            password_hash="hashed_password"
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    return users


@pytest.fixture
def sample_tasks(db: Session, sample_users):
    """創建測試任務數據"""
    tasks = []
    for i in range(10):
        task = Task(
            creator_id=sample_users[0].id,
            title=f"Test Task {i}",
            description=f"Description for task {i}",
            task_type="cleanup",
            status=TaskStatus.AVAILABLE.value if i % 2 == 0 else TaskStatus.COMPLETED.value,
            location_data={"address": f"Test Address {i}", "coordinates": {"lat": 23.5, "lng": 121.4}},
            required_volunteers=2,
            priority_level=3 if i < 5 else 5
        )
        db.add(task)
        tasks.append(task)
    
    db.commit()
    return tasks


@pytest.fixture
def sample_needs(db: Session, sample_users):
    """創建測試需求數據"""
    needs = []
    for i in range(8):
        need = Need(
            reporter_id=sample_users[1].id,
            title=f"Test Need {i}",
            description=f"Description for need {i}",
            need_type="food",
            status=NeedStatus.OPEN.value if i % 2 == 0 else NeedStatus.RESOLVED.value,
            location_data={"address": f"Test Address {i}", "coordinates": {"lat": 23.5, "lng": 121.4}},
            requirements={"items": ["water", "food"]},
            urgency_level=2 if i < 4 else 4
        )
        db.add(need)
        needs.append(need)
    
    db.commit()
    return needs


@pytest.fixture
def sample_supply_stations(db: Session, sample_users):
    """創建測試物資站點數據"""
    stations = []
    for i in range(3):
        station = SupplyStation(
            manager_id=sample_users[2].id,
            name=f"Test Station {i}",
            address=f"Station Address {i}",
            location_data={"coordinates": {"lat": 23.5, "lng": 121.4}},
            contact_info={"phone": f"123-456-789{i}"},
            is_active=True
        )
        db.add(station)
        stations.append(station)
    
    db.commit()
    return stations


@pytest.fixture
def sample_inventory_items(db: Session, sample_supply_stations):
    """創建測試庫存項目數據"""
    items = []
    for station in sample_supply_stations:
        for supply_type in ["water", "rice", "blanket"]:
            item = InventoryItem(
                station_id=station.id,
                supply_type=supply_type,
                description=f"{supply_type} at {station.name}",
                is_available=True
            )
            db.add(item)
            items.append(item)
    
    db.commit()
    return items


@pytest.fixture
def sample_task_claims(db: Session, sample_tasks, sample_users):
    """創建測試任務認領數據"""
    claims = []
    for i, task in enumerate(sample_tasks[:5]):
        claim = TaskClaim(
            task_id=task.id,
            user_id=sample_users[3].id,
            status="completed" if i % 2 == 0 else "claimed",
            claimed_at=datetime.utcnow() - timedelta(days=i),
            completed_at=datetime.utcnow() - timedelta(hours=i) if i % 2 == 0 else None
        )
        db.add(claim)
        claims.append(claim)
    
    db.commit()
    return claims


@pytest.fixture
def sample_supply_reservations(db: Session, sample_users, sample_supply_stations):
    """創建測試物資預訂數據"""
    reservations = []
    for i, station in enumerate(sample_supply_stations):
        reservation = SupplyReservation(
            user_id=sample_users[4].id,
            station_id=station.id,
            status="delivered" if i % 2 == 0 else "pending",
            reserved_at=datetime.utcnow() - timedelta(days=i),
            confirmed_at=datetime.utcnow() - timedelta(days=i, hours=1) if i % 2 == 0 else None,
            delivered_at=datetime.utcnow() - timedelta(hours=i) if i % 2 == 0 else None
        )
        db.add(reservation)
        reservations.append(reservation)
    
    db.commit()
    return reservations


@pytest.fixture
def sample_system_logs(db: Session, sample_users):
    """創建測試系統日誌數據"""
    logs = []
    actions = ["create_task", "claim_task", "update_need", "reserve_supply"]
    
    for i in range(20):
        log = SystemLog(
            user_id=sample_users[i % len(sample_users)].id,
            action=actions[i % len(actions)],
            resource_type="task" if i % 2 == 0 else "need",
            details={"action_details": f"Action {i}"},
            ip_address=f"192.168.1.{i % 255}",
            created_at=datetime.utcnow() - timedelta(hours=i)
        )
        db.add(log)
        logs.append(log)
    
    db.commit()
    return logs