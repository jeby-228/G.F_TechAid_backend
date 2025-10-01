"""
監控系統 API 端點測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, Mock

from app.main import app
from app.models.user import User
from app.utils.constants import UserRole


class TestMonitoringAPI:
    """監控系統 API 測試類"""
    
    def test_get_real_time_statistics_success(self, client: TestClient, normal_user_token_headers):
        """測試成功獲取即時統計資料"""
        response = client.get(
            "/api/v1/monitoring/real-time",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        assert "overview" in data
        assert "today_stats" in data
        assert "user_distribution" in data
        assert "last_updated" in data
        
        # 驗證總覽統計
        overview = data["overview"]
        required_fields = [
            "total_users", "total_tasks", "total_needs", 
            "total_supply_stations", "active_tasks", "open_needs"
        ]
        for field in required_fields:
            assert field in overview
            assert isinstance(overview[field], int)
        
        # 驗證今日統計
        today_stats = data["today_stats"]
        today_fields = ["new_users", "new_tasks", "new_needs"]
        for field in today_fields:
            assert field in today_stats
            assert isinstance(today_stats[field], int)
    
    def test_get_real_time_statistics_unauthorized(self, client: TestClient):
        """測試未授權訪問即時統計資料"""
        response = client.get("/api/v1/monitoring/real-time")
        assert response.status_code == 401
    
    def test_get_disaster_relief_progress_success(self, client: TestClient, normal_user_token_headers):
        """測試成功獲取救災進度追蹤統計"""
        response = client.get(
            "/api/v1/monitoring/disaster-relief-progress?days=7",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        required_fields = [
            "period", "task_progress", "need_progress", 
            "overall_completion", "daily_progress", "urgency_analysis"
        ]
        for field in required_fields:
            assert field in data
        
        # 驗證時間段資訊
        period = data["period"]
        assert "start_date" in period
        assert "end_date" in period
        assert period["days"] == 7
        
        # 驗證任務進度
        task_progress = data["task_progress"]
        assert "status_distribution" in task_progress
        assert "completion_rate" in task_progress
        assert isinstance(task_progress["completion_rate"], (int, float))
        
        # 驗證每日進度是列表
        assert isinstance(data["daily_progress"], list)
    
    def test_get_disaster_relief_progress_invalid_days(self, client: TestClient, normal_user_token_headers):
        """測試無效天數參數"""
        response = client.get(
            "/api/v1/monitoring/disaster-relief-progress?days=400",
            headers=normal_user_token_headers
        )
        assert response.status_code == 422  # Validation error
    
    def test_get_task_completion_statistics_success(self, client: TestClient, normal_user_token_headers):
        """測試成功獲取任務完成率統計"""
        response = client.get(
            "/api/v1/monitoring/task-completion?days=30",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        required_fields = [
            "period", "overall", "by_task_type", 
            "average_completion_time_hours", "volunteer_efficiency"
        ]
        for field in required_fields:
            assert field in data
        
        # 驗證整體統計
        overall = data["overall"]
        assert "total_tasks" in overall
        assert "completed_tasks" in overall
        assert "completion_rate" in overall
        assert 0 <= overall["completion_rate"] <= 100
        
        # 驗證按任務類型統計
        assert isinstance(data["by_task_type"], list)
        
        # 驗證志工效率統計
        volunteer_efficiency = data["volunteer_efficiency"]
        assert "active_volunteers" in volunteer_efficiency
        assert "avg_tasks_per_volunteer" in volunteer_efficiency
        assert "top_volunteers" in volunteer_efficiency
        assert isinstance(volunteer_efficiency["top_volunteers"], list)
    
    def test_get_supply_flow_monitoring_success(self, client: TestClient, normal_user_token_headers):
        """測試成功獲取物資流向監控統計"""
        response = client.get(
            "/api/v1/monitoring/supply-flow?days=7",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        required_fields = [
            "period", "reservation_stats", "station_activity", 
            "supply_type_flow", "delivery_efficiency"
        ]
        for field in required_fields:
            assert field in data
        
        # 驗證預訂統計
        reservation_stats = data["reservation_stats"]
        assert "status_distribution" in reservation_stats
        assert "delivery_rate" in reservation_stats
        assert 0 <= reservation_stats["delivery_rate"] <= 100
        
        # 驗證站點活動和物資流向是列表
        assert isinstance(data["station_activity"], list)
        assert isinstance(data["supply_type_flow"], list)
        
        # 驗證配送效率
        delivery_efficiency = data["delivery_efficiency"]
        assert "avg_delivery_time_hours" in delivery_efficiency
        assert "delivery_success_rate" in delivery_efficiency
        assert delivery_efficiency["avg_delivery_time_hours"] >= 0
        assert 0 <= delivery_efficiency["delivery_success_rate"] <= 100
    
    def test_get_inventory_statistics_success(self, client: TestClient, normal_user_token_headers):
        """測試成功獲取庫存統計"""
        response = client.get(
            "/api/v1/monitoring/inventory",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        required_fields = [
            "overview", "by_supply_type", "by_station", 
            "low_inventory_alerts", "last_updated"
        ]
        for field in required_fields:
            assert field in data
        
        # 驗證總覽
        overview = data["overview"]
        assert "total_active_stations" in overview
        assert "total_available_items" in overview
        assert isinstance(overview["total_active_stations"], int)
        assert isinstance(overview["total_available_items"], int)
        
        # 驗證按物資類型統計
        assert isinstance(data["by_supply_type"], dict)
        
        # 驗證按站點統計和低庫存警告
        assert isinstance(data["by_station"], list)
        assert isinstance(data["low_inventory_alerts"], list)
    
    def test_get_system_activity_log_admin_success(self, client: TestClient, admin_user_token_headers):
        """測試管理員成功獲取系統活動日誌"""
        response = client.get(
            "/api/v1/monitoring/system-activity?hours=24&limit=50",
            headers=admin_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        required_fields = ["period", "summary", "activity_counts", "recent_logs"]
        for field in required_fields:
            assert field in data
        
        # 驗證時間段
        period = data["period"]
        assert "start_time" in period
        assert "end_time" in period
        assert period["hours"] == 24
        
        # 驗證摘要
        summary = data["summary"]
        assert "active_users" in summary
        assert "total_actions" in summary
        
        # 驗證活動計數和最近日誌
        assert isinstance(data["activity_counts"], dict)
        assert isinstance(data["recent_logs"], list)
        assert len(data["recent_logs"]) <= 50
    
    def test_get_system_activity_log_non_admin_forbidden(self, client: TestClient, normal_user_token_headers):
        """測試非管理員用戶無法獲取系統活動日誌"""
        response = client.get(
            "/api/v1/monitoring/system-activity",
            headers=normal_user_token_headers
        )
        assert response.status_code == 403
    
    def test_get_monitoring_dashboard_success(self, client: TestClient, normal_user_token_headers):
        """測試成功獲取監控儀表板"""
        response = client.get(
            "/api/v1/monitoring/dashboard?days=7&hours=24&limit=100",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        required_fields = [
            "real_time_stats", "disaster_relief_progress", "task_completion_stats",
            "supply_flow_monitoring", "inventory_stats", "system_activity", "generated_at"
        ]
        for field in required_fields:
            assert field in data
        
        # 驗證各個統計模塊的基本結構
        assert "overview" in data["real_time_stats"]
        assert "period" in data["disaster_relief_progress"]
        assert "overall" in data["task_completion_stats"]
        assert "reservation_stats" in data["supply_flow_monitoring"]
        assert "overview" in data["inventory_stats"]
        assert "period" in data["system_activity"]
        
        # 驗證生成時間
        assert "generated_at" in data
    
    def test_get_monitoring_dashboard_admin_with_system_activity(self, client: TestClient, admin_user_token_headers):
        """測試管理員獲取包含系統活動的監控儀表板"""
        response = client.get(
            "/api/v1/monitoring/dashboard",
            headers=admin_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 管理員應該能獲取系統活動日誌
        system_activity = data["system_activity"]
        assert "summary" in system_activity
        assert "recent_logs" in system_activity
    
    def test_monitoring_health_check(self, client: TestClient):
        """測試監控系統健康檢查"""
        response = client.get("/api/v1/monitoring/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "monitoring"
        assert "timestamp" in data
    
    def test_get_detailed_admin_statistics_success(self, client: TestClient, admin_user_token_headers):
        """測試管理員成功獲取詳細統計資料"""
        response = client.get(
            "/api/v1/monitoring/admin/detailed-stats?days=30",
            headers=admin_user_token_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 驗證回應結構
        required_fields = [
            "real_time_statistics", "disaster_relief_progress", "task_completion_statistics",
            "supply_flow_monitoring", "inventory_statistics", "system_activity_log",
            "query_period_days", "generated_at", "generated_by"
        ]
        for field in required_fields:
            assert field in data
        
        # 驗證查詢參數
        assert data["query_period_days"] == 30
        
        # 驗證生成者資訊
        generated_by = data["generated_by"]
        assert "user_id" in generated_by
        assert "user_name" in generated_by
        assert "user_role" in generated_by
        assert generated_by["user_role"] == "admin"
    
    def test_get_detailed_admin_statistics_non_admin_forbidden(self, client: TestClient, normal_user_token_headers):
        """測試非管理員用戶無法獲取詳細統計資料"""
        response = client.get(
            "/api/v1/monitoring/admin/detailed-stats",
            headers=normal_user_token_headers
        )
        assert response.status_code == 403
    
    def test_monitoring_api_parameter_validation(self, client: TestClient, normal_user_token_headers):
        """測試監控 API 參數驗證"""
        # 測試無效的天數參數
        response = client.get(
            "/api/v1/monitoring/disaster-relief-progress?days=0",
            headers=normal_user_token_headers
        )
        assert response.status_code == 422
        
        response = client.get(
            "/api/v1/monitoring/disaster-relief-progress?days=400",
            headers=normal_user_token_headers
        )
        assert response.status_code == 422
        
        # 測試無效的小時數參數
        response = client.get(
            "/api/v1/monitoring/system-activity?hours=0",
            headers=admin_user_token_headers
        )
        assert response.status_code == 422
        
        response = client.get(
            "/api/v1/monitoring/system-activity?hours=200",
            headers=admin_user_token_headers
        )
        assert response.status_code == 422
        
        # 測試無效的限制參數
        response = client.get(
            "/api/v1/monitoring/system-activity?limit=0",
            headers=admin_user_token_headers
        )
        assert response.status_code == 422
        
        response = client.get(
            "/api/v1/monitoring/system-activity?limit=2000",
            headers=admin_user_token_headers
        )
        assert response.status_code == 422
    
    def test_monitoring_api_with_database_error(self, client: TestClient, normal_user_token_headers):
        """測試監控 API 資料庫錯誤處理"""
        with patch('app.services.monitoring_service.monitoring_service.get_real_time_statistics') as mock_service:
            mock_service.side_effect = Exception("Database connection error")
            
            response = client.get(
                "/api/v1/monitoring/real-time",
                headers=normal_user_token_headers
            )
            
            # 應該返回 500 內部伺服器錯誤
            assert response.status_code == 500
    
    def test_monitoring_api_performance(self, client: TestClient, normal_user_token_headers):
        """測試監控 API 效能"""
        import time
        
        # 測試即時統計 API 的回應時間
        start_time = time.time()
        response = client.get(
            "/api/v1/monitoring/real-time",
            headers=normal_user_token_headers
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # API 回應時間應該在合理範圍內（小於2秒）
        assert response_time < 2.0, f"API response too slow: {response_time}s"
        
        # 測試儀表板 API 的回應時間
        start_time = time.time()
        response = client.get(
            "/api/v1/monitoring/dashboard",
            headers=normal_user_token_headers
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # 儀表板 API 回應時間應該在合理範圍內（小於5秒）
        assert response_time < 5.0, f"Dashboard API response too slow: {response_time}s"
    
    def test_monitoring_api_data_consistency(self, client: TestClient, normal_user_token_headers):
        """測試監控 API 資料一致性"""
        # 獲取即時統計
        real_time_response = client.get(
            "/api/v1/monitoring/real-time",
            headers=normal_user_token_headers
        )
        assert real_time_response.status_code == 200
        real_time_data = real_time_response.json()
        
        # 獲取儀表板資料
        dashboard_response = client.get(
            "/api/v1/monitoring/dashboard",
            headers=normal_user_token_headers
        )
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        
        # 驗證即時統計資料在儀表板中的一致性
        real_time_overview = real_time_data["overview"]
        dashboard_overview = dashboard_data["real_time_stats"]["overview"]
        
        # 基本統計數據應該一致
        assert real_time_overview["total_users"] == dashboard_overview["total_users"]
        assert real_time_overview["total_tasks"] == dashboard_overview["total_tasks"]
        assert real_time_overview["total_needs"] == dashboard_overview["total_needs"]
    
    def test_monitoring_api_caching_headers(self, client: TestClient, normal_user_token_headers):
        """測試監控 API 快取標頭"""
        response = client.get(
            "/api/v1/monitoring/real-time",
            headers=normal_user_token_headers
        )
        
        assert response.status_code == 200
        
        # 檢查是否有適當的快取控制標頭
        # 注意：這取決於你的 FastAPI 配置
        # 如果沒有設定快取標頭，這個測試可能需要調整
        headers = response.headers
        # 可以檢查 Cache-Control, ETag 等標頭
    
    def test_monitoring_api_concurrent_requests(self, client: TestClient, normal_user_token_headers):
        """測試監控 API 併發請求處理"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = client.get(
                    "/api/v1/monitoring/real-time",
                    headers=normal_user_token_headers
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # 創建多個併發請求
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有請求完成
        for thread in threads:
            thread.join()
        
        # 驗證所有請求都成功
        assert len(errors) == 0, f"Concurrent request errors: {errors}"
        assert all(status == 200 for status in results), f"Some requests failed: {results}"
        assert len(results) == 5


# 測試 fixtures
@pytest.fixture
def admin_user_token_headers(client: TestClient, db: Session):
    """創建管理員用戶的認證標頭"""
    # 這個 fixture 需要根據你的認證系統實現
    # 假設你有一個創建管理員用戶和獲取 token 的方法
    from app.models.user import User
    from app.utils.security import create_access_token
    
    admin_user = User(
        email="admin@test.com",
        name="Admin User",
        role=UserRole.ADMIN.value,
        password_hash="hashed_password",
        is_approved=True
    )
    db.add(admin_user)
    db.commit()
    
    access_token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def normal_user_token_headers(client: TestClient, db: Session):
    """創建普通用戶的認證標頭"""
    from app.models.user import User
    from app.utils.security import create_access_token
    
    normal_user = User(
        email="user@test.com",
        name="Normal User",
        role=UserRole.VOLUNTEER.value,
        password_hash="hashed_password",
        is_approved=True
    )
    db.add(normal_user)
    db.commit()
    
    access_token = create_access_token(data={"sub": str(normal_user.id)})
    return {"Authorization": f"Bearer {access_token}"}