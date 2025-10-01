"""
通知 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime

from app.main import app
from app.models.system import Notification
from app.models.user import User
from app.utils.constants import NotificationType, UserRole


class TestNotificationAPI:
    """通知 API 測試類"""
    
    @pytest.fixture
    def client(self):
        """建立測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_user(self):
        """建立測試用戶"""
        return User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            name="測試用戶",
            role=UserRole.VOLUNTEER
        )
    
    @pytest.fixture
    def sample_notifications(self):
        """建立測試通知"""
        return [
            Notification(
                id="notif-1",
                user_id="550e8400-e29b-41d4-a716-446655440000",
                title="通知1",
                message="這是第一個通知",
                notification_type=NotificationType.TASK.value,
                is_read=False,
                created_at=datetime.utcnow()
            ),
            Notification(
                id="notif-2",
                user_id="550e8400-e29b-41d4-a716-446655440000",
                title="通知2",
                message="這是第二個通知",
                notification_type=NotificationType.SUPPLY.value,
                is_read=True,
                created_at=datetime.utcnow(),
                read_at=datetime.utcnow()
            )
        ]
    
    def test_get_notifications_success(self, client, sample_user, sample_notifications):
        """測試成功取得通知列表"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.get_user_notifications', return_value=sample_notifications), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.count.return_value = 2
            mock_get_db.return_value = mock_db
            
            with patch('app.services.notification_service.notification_service.get_unread_count', return_value=1):
                response = client.get("/api/v1/notifications/")
                
                assert response.status_code == 200
                data = response.json()
                
                assert len(data["notifications"]) == 2
                assert data["total_count"] == 2
                assert data["unread_count"] == 1
                assert data["notifications"][0]["title"] == "通知1"
                assert data["notifications"][1]["title"] == "通知2"
    
    def test_get_notifications_with_pagination(self, client, sample_user):
        """測試帶分頁的通知列表"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.get_user_notifications', return_value=[]), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            mock_get_db.return_value = mock_db
            
            with patch('app.services.notification_service.notification_service.get_unread_count', return_value=0):
                response = client.get("/api/v1/notifications/?skip=10&limit=20")
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["skip"] == 10
                assert data["limit"] == 20
    
    def test_get_notifications_unread_only(self, client, sample_user):
        """測試只取得未讀通知"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.get_user_notifications') as mock_get_notifications, \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            mock_get_db.return_value = mock_db
            
            with patch('app.services.notification_service.notification_service.get_unread_count', return_value=0):
                response = client.get("/api/v1/notifications/?unread_only=true")
                
                assert response.status_code == 200
                mock_get_notifications.assert_called_once()
                call_args = mock_get_notifications.call_args[1]
                assert call_args['unread_only'] is True
    
    def test_get_notification_stats(self, client, sample_user):
        """測試取得通知統計"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.get_unread_count', return_value=5), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.count.return_value = 20
            mock_get_db.return_value = mock_db
            
            response = client.get("/api/v1/notifications/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["unread_count"] == 5
            assert data["total_count"] == 20
    
    def test_mark_notification_as_read_success(self, client, sample_user):
        """測試成功標記通知為已讀"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.mark_notification_as_read', return_value=True), \
             patch('app.api.deps.get_db'):
            
            response = client.put("/api/v1/notifications/notif-1/read")
            
            assert response.status_code == 200
            data = response.json()
            assert "已標記為已讀" in data["message"]
    
    def test_mark_notification_as_read_not_found(self, client, sample_user):
        """測試標記不存在的通知為已讀"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.mark_notification_as_read', return_value=False), \
             patch('app.api.deps.get_db'):
            
            response = client.put("/api/v1/notifications/non-existent/read")
            
            assert response.status_code == 404
            data = response.json()
            assert "不存在" in data["detail"]
    
    def test_mark_all_notifications_as_read(self, client, sample_user):
        """測試標記所有通知為已讀"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.mark_all_notifications_as_read', return_value=3), \
             patch('app.api.deps.get_db'):
            
            response = client.put("/api/v1/notifications/read-all")
            
            assert response.status_code == 200
            data = response.json()
            assert data["updated_count"] == 3
            assert "已標記 3 個通知為已讀" in data["message"]
    
    def test_get_single_notification_success(self, client, sample_user, sample_notifications):
        """測試成功取得單一通知"""
        notification = sample_notifications[0]
        
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = notification
            mock_get_db.return_value = mock_db
            
            response = client.get(f"/api/v1/notifications/{notification.id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == notification.id
            assert data["title"] == notification.title
            assert data["message"] == notification.message
            assert data["notification_type"] == notification.notification_type
            assert data["is_read"] == notification.is_read
    
    def test_get_single_notification_not_found(self, client, sample_user):
        """測試取得不存在的通知"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value = mock_db
            
            response = client.get("/api/v1/notifications/non-existent")
            
            assert response.status_code == 404
            data = response.json()
            assert "不存在" in data["detail"]
    
    def test_get_single_notification_invalid_id(self, client, sample_user):
        """測試無效的通知 ID 格式"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.side_effect = ValueError("Invalid UUID")
            mock_get_db.return_value = mock_db
            
            response = client.get("/api/v1/notifications/invalid-id")
            
            assert response.status_code == 400
            data = response.json()
            assert "無效的通知 ID 格式" in data["detail"]
    
    def test_get_notifications_unauthorized(self, client):
        """測試未授權訪問通知"""
        response = client.get("/api/v1/notifications/")
        
        # 應該返回 401 或重定向到登入頁面
        assert response.status_code in [401, 403]
    
    def test_pagination_limits(self, client, sample_user):
        """測試分頁限制"""
        with patch('app.api.deps.get_current_user', return_value=sample_user), \
             patch('app.services.notification_service.notification_service.get_user_notifications', return_value=[]), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            mock_get_db.return_value = mock_db
            
            with patch('app.services.notification_service.notification_service.get_unread_count', return_value=0):
                # 測試超過最大限制
                response = client.get("/api/v1/notifications/?limit=200")
                
                # FastAPI 會自動驗證並限制在 100
                assert response.status_code == 422  # Validation error
    
    def test_negative_pagination_values(self, client, sample_user):
        """測試負數分頁值"""
        with patch('app.api.deps.get_current_user', return_value=sample_user):
            # 測試負數 skip
            response = client.get("/api/v1/notifications/?skip=-1")
            assert response.status_code == 422  # Validation error
            
            # 測試負數 limit
            response = client.get("/api/v1/notifications/?limit=-1")
            assert response.status_code == 422  # Validation error