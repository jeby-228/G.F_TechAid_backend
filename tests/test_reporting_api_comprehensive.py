"""
報表API綜合測試
"""
import pytest
from datetime import datetime, timedelta, date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.task import Task, TaskClaim
from app.models.need import Need
from app.models.supply import SupplyStation, SupplyReservation, ReservationItem
from app.models.system import SystemLog
from app.utils.constants import TaskStatus, NeedStatus, UserRole


class TestReportingAPIComprehensive:
    """報表API綜合測試類"""
    
    def test_generate_disaster_relief_report_pdf(self, client: TestClient, test_user: User, test_tasks: list, test_needs: list, auth_headers: dict):
        """測試生成救災活動PDF報表"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/disaster-relief",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0
        assert response.content.startswith(b'%PDF')
    
    def test_generate_disaster_relief_report_csv(self, client: TestClient, test_user: User, test_tasks: list, test_needs: list, auth_headers: dict):
        """測試生成救災活動CSV報表"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "csv"
        }
        
        response = client.post(
            "/api/v1/reports/generate/disaster-relief",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0
    
    def test_generate_disaster_relief_report_excel(self, client: TestClient, test_user: User, test_tasks: list, test_needs: list, auth_headers: dict):
        """測試生成救災活動Excel報表"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "excel"
        }
        
        response = client.post(
            "/api/v1/reports/generate/disaster-relief",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.content) > 0
        assert response.content.startswith(b'PK')  # ZIP格式標頭
    
    def test_generate_task_completion_report(self, client: TestClient, test_user: User, test_tasks: list, auth_headers: dict, db: Session):
        """測試生成任務完成報表"""
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
        
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/task-completion",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
    
    def test_generate_supply_flow_report(self, client: TestClient, test_user: User, test_supply_station: SupplyStation, auth_headers: dict, db: Session):
        """測試生成物資流向報表"""
        # 建立測試物資預訂記錄
        reservation = SupplyReservation(
            user_id=test_user.id,
            station_id=test_supply_station.id,
            status="confirmed",
            reserved_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(reservation)
        db.commit()
        
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/supply-flow",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
    
    def test_generate_system_usage_report_admin_only(self, client: TestClient, test_admin: User, admin_headers: dict):
        """測試生成系統使用統計報表（僅管理員）"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/system-usage",
            json=query_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
    
    def test_generate_system_usage_report_forbidden(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試非管理員無法生成系統使用統計報表"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/system-usage",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_generate_comprehensive_analysis_report(self, client: TestClient, test_admin: User, admin_headers: dict):
        """測試生成綜合分析報表"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/comprehensive-analysis",
            json=query_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
    
    def test_export_tasks_data_csv(self, client: TestClient, test_user: User, test_tasks: list, auth_headers: dict):
        """測試匯出任務資料為CSV"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "csv"
        }
        
        response = client.post(
            "/api/v1/reports/export/tasks",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "tasks_export" in response.headers["content-disposition"]
        assert len(response.content) > 0
    
    def test_export_needs_data_excel(self, client: TestClient, test_user: User, test_needs: list, auth_headers: dict):
        """測試匯出需求資料為Excel"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "excel"
        }
        
        response = client.post(
            "/api/v1/reports/export/needs",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]
        assert "needs_export" in response.headers["content-disposition"]
        assert len(response.content) > 0
    
    def test_export_supplies_data_json(self, client: TestClient, test_user: User, test_supply_station: SupplyStation, auth_headers: dict, db: Session):
        """測試匯出物資資料為JSON"""
        # 建立測試物資預訂記錄
        reservation = SupplyReservation(
            user_id=test_user.id,
            station_id=test_supply_station.id,
            status="confirmed",
            reserved_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(reservation)
        db.commit()
        
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "json"
        }
        
        response = client.post(
            "/api/v1/reports/export/supplies",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "supplies_export" in response.headers["content-disposition"]
        assert len(response.content) > 0
    
    def test_export_users_data_admin_only(self, client: TestClient, test_admin: User, admin_headers: dict):
        """測試匯出用戶資料（僅管理員）"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "csv"
        }
        
        response = client.post(
            "/api/v1/reports/export/users",
            json=query_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert len(response.content) > 0
    
    def test_export_users_data_forbidden(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試非管理員無法匯出用戶資料"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "csv"
        }
        
        response = client.post(
            "/api/v1/reports/export/users",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_export_logs_data_admin_only(self, client: TestClient, test_admin: User, admin_headers: dict, db: Session):
        """測試匯出系統日誌資料（僅管理員）"""
        # 建立測試系統日誌記錄
        system_log = SystemLog(
            user_id=test_admin.id,
            action="test_action",
            resource_type="test",
            resource_id=str(test_admin.id),
            details={"test": "data"},
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.add(system_log)
        db.commit()
        
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "csv"
        }
        
        response = client.post(
            "/api/v1/reports/export/logs",
            json=query_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert len(response.content) > 0
    
    def test_export_logs_data_forbidden(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試非管理員無法匯出系統日誌資料"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "csv"
        }
        
        response = client.post(
            "/api/v1/reports/export/logs",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    def test_generate_bulk_reports(self, client: TestClient, test_user: User, test_tasks: list, test_needs: list, auth_headers: dict):
        """測試批量生成報表"""
        request_data = {
            "report_types": ["disaster_relief", "task_completion"],
            "query": {
                "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
                "end_date": datetime.utcnow().date().isoformat(),
                "format_type": "pdf"
            }
        }
        
        response = client.post(
            "/api/v1/reports/generate/bulk",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["reports"]) == 2
        assert all(report["success"] for report in data["reports"])
    
    def test_get_report_statistics_admin_only(self, client: TestClient, test_admin: User, admin_headers: dict):
        """測試獲取報表統計資訊（僅管理員）"""
        response = client.get(
            "/api/v1/reports/statistics?days=30",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_reports" in data
        assert "reports_by_type" in data
        assert "reports_by_format" in data
    
    def test_get_report_templates(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試獲取報表模板列表"""
        response = client.get(
            "/api/v1/reports/templates",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "total_count" in data
        assert len(data["templates"]) > 0
    
    def test_get_quick_disaster_relief_summary(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試快速獲取救災活動摘要"""
        response = client.get(
            "/api/v1/reports/quick/disaster-relief-summary?days=7",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "task_summary" in data
        assert "need_summary" in data
        assert "overall_completion_rate" in data
    
    def test_get_quick_task_completion_summary(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試快速獲取任務完成摘要"""
        response = client.get(
            "/api/v1/reports/quick/task-completion-summary?days=7",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "overall_stats" in data
        assert "volunteer_efficiency" in data
    
    def test_get_analytics_trends(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試獲取趨勢分析資料"""
        response = client.get(
            "/api/v1/reports/analytics/trends?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "daily_statistics" in data
        assert "trend_analysis" in data
        assert isinstance(data["daily_statistics"], list)
    
    def test_get_performance_analytics(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試獲取效能分析資料"""
        response = client.get(
            "/api/v1/reports/analytics/performance?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "period_days" in data
        assert "key_performance_indicators" in data
        assert "performance_score" in data
        assert "performance_level" in data
        assert "recommendations" in data
    
    def test_health_check(self, client: TestClient):
        """測試報表系統健康檢查"""
        response = client.get("/api/v1/reports/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "reporting"
        assert "supported_formats" in data
        assert "available_reports" in data
    
    def test_invalid_date_range(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試無效日期範圍"""
        query_data = {
            "start_date": datetime.utcnow().date().isoformat(),
            "end_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/disaster-relief",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_future_date_validation(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試未來日期驗證"""
        query_data = {
            "start_date": (datetime.utcnow() + timedelta(days=1)).date().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/disaster-relief",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_format_type(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試無效格式類型"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "invalid_format"
        }
        
        response = client.post(
            "/api/v1/reports/generate/disaster-relief",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_export_invalid_data_type(self, client: TestClient, test_user: User, auth_headers: dict):
        """測試匯出無效資料類型"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "csv"
        }
        
        response = client.post(
            "/api/v1/reports/export/invalid_type",
            json=query_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "不支援的資料類型" in response.json()["detail"]
    
    def test_unauthorized_access(self, client: TestClient):
        """測試未授權訪問"""
        query_data = {
            "start_date": (datetime.utcnow() - timedelta(days=7)).date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "format_type": "pdf"
        }
        
        response = client.post(
            "/api/v1/reports/generate/disaster-relief",
            json=query_data
        )
        
        assert response.status_code == 401