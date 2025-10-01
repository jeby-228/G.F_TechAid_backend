"""
公告 API 測試
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.main import app
from app.models.system import Announcement
from app.models.user import User
from app.utils.constants import AnnouncementType, UserRole

# AsyncMock for Python 3.7 compatibility
try:
    from unittest.mock import AsyncMock
except ImportError:
    class AsyncMock(Mock):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
        async def __call__(self, *args, **kwargs):
            return super().__call__(*args, **kwargs)


class TestAnnouncementAPI:
    """公告 API 測試類"""
    
    @pytest.fixture
    def client(self):
        """建立測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_admin_user(self):
        """建立測試管理員用戶"""
        return User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="admin@example.com",
            name="管理員",
            role=UserRole.ADMIN
        )
    
    @pytest.fixture
    def sample_volunteer_user(self):
        """建立測試志工用戶"""
        return User(
            id="660e8400-e29b-41d4-a716-446655440001",
            email="volunteer@example.com",
            name="志工",
            role=UserRole.VOLUNTEER
        )
    
    @pytest.fixture
    def sample_announcement(self):
        """建立測試公告"""
        return Announcement(
            id="announcement-id",
            title="測試公告",
            content="這是測試公告內容",
            announcement_type=AnnouncementType.GENERAL.value,
            priority_level=1,
            target_roles=None,
            created_by="550e8400-e29b-41d4-a716-446655440000",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def test_create_announcement_success(self, client, sample_admin_user, sample_announcement):
        """測試成功建立公告"""
        announcement_data = {
            "title": "新公告",
            "content": "這是新公告內容",
            "announcement_type": "general",
            "priority_level": 2
        }
        
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.create_announcement', return_value=sample_announcement), \
             patch('app.api.deps.get_db'):
            
            response = client.post("/api/v1/announcements/", json=announcement_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == sample_announcement.title
            assert data["content"] == sample_announcement.content
    
    def test_create_announcement_unauthorized(self, client, sample_volunteer_user):
        """測試非管理員建立公告"""
        announcement_data = {
            "title": "新公告",
            "content": "這是新公告內容",
            "announcement_type": "general"
        }
        
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user):
            response = client.post("/api/v1/announcements/", json=announcement_data)
            
            assert response.status_code == 403
    
    def test_create_announcement_invalid_data(self, client, sample_admin_user):
        """測試無效資料建立公告"""
        announcement_data = {
            "title": "",  # 空標題
            "content": "內容",
            "announcement_type": "general"
        }
        
        with patch('app.api.deps.require_admin', return_value=sample_admin_user):
            response = client.post("/api/v1/announcements/", json=announcement_data)
            
            assert response.status_code == 422  # Validation error
    
    def test_get_announcements_success(self, client, sample_volunteer_user, sample_announcement):
        """測試成功取得公告列表"""
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user), \
             patch('app.services.announcement_service.announcement_service.get_announcements', return_value=[sample_announcement]), \
             patch('app.services.announcement_service.announcement_service.get_announcements_count', return_value=1), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = sample_volunteer_user
            mock_get_db.return_value = mock_db
            
            response = client.get("/api/v1/announcements/")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["announcements"]) == 1
            assert data["total_count"] == 1
    
    def test_get_announcements_with_filters(self, client, sample_volunteer_user):
        """測試帶過濾條件的公告查詢"""
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user), \
             patch('app.services.announcement_service.announcement_service.get_announcements', return_value=[]), \
             patch('app.services.announcement_service.announcement_service.get_announcements_count', return_value=0), \
             patch('app.api.deps.get_db'):
            
            response = client.get("/api/v1/announcements/?announcement_type=emergency&active_only=true&skip=10&limit=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["skip"] == 10
            assert data["limit"] == 20
    
    def test_get_public_announcements(self, client, sample_announcement):
        """測試取得公開公告"""
        with patch('app.services.announcement_service.announcement_service.get_announcements', return_value=[sample_announcement]), \
             patch('app.api.deps.get_db'):
            
            response = client.get("/api/v1/announcements/public")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == sample_announcement.title
            # 確保不包含敏感資訊
            assert "created_by" not in data[0]
    
    def test_get_emergency_announcements(self, client, sample_volunteer_user, sample_announcement):
        """測試取得緊急公告"""
        emergency_announcement = sample_announcement
        emergency_announcement.announcement_type = AnnouncementType.EMERGENCY.value
        
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user), \
             patch('app.services.announcement_service.announcement_service.get_emergency_announcements', return_value=[emergency_announcement]), \
             patch('app.api.deps.get_db'):
            
            response = client.get("/api/v1/announcements/emergency")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["announcement_type"] == "emergency"
    
    def test_get_announcement_stats(self, client, sample_admin_user):
        """測試取得公告統計"""
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.get_announcements_count') as mock_count, \
             patch('app.api.deps.get_db'):
            
            mock_count.side_effect = [10, 8, 2, 2]  # total, active, emergency, expired
            
            response = client.get("/api/v1/announcements/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] == 10
            assert data["active_count"] == 8
            assert data["emergency_count"] == 2
            assert data["expired_count"] == 2
    
    def test_get_announcement_by_id_success(self, client, sample_volunteer_user, sample_announcement):
        """測試成功取得單一公告"""
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user), \
             patch('app.services.announcement_service.announcement_service.get_announcement_by_id', return_value=sample_announcement), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = sample_volunteer_user
            mock_get_db.return_value = mock_db
            
            response = client.get(f"/api/v1/announcements/{sample_announcement.id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == sample_announcement.id
            assert data["title"] == sample_announcement.title
    
    def test_get_announcement_by_id_not_found(self, client, sample_volunteer_user):
        """測試取得不存在的公告"""
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user), \
             patch('app.services.announcement_service.announcement_service.get_announcement_by_id', return_value=None), \
             patch('app.api.deps.get_db'):
            
            response = client.get("/api/v1/announcements/non-existent-id")
            
            assert response.status_code == 404
    
    def test_get_announcement_permission_denied(self, client, sample_volunteer_user, sample_announcement):
        """測試無權限查看公告"""
        # 設定公告只給管理員看
        sample_announcement.target_roles = [UserRole.ADMIN.value]
        
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user), \
             patch('app.services.announcement_service.announcement_service.get_announcement_by_id', return_value=sample_announcement), \
             patch('app.api.deps.get_db'):
            
            response = client.get(f"/api/v1/announcements/{sample_announcement.id}")
            
            assert response.status_code == 403
    
    def test_update_announcement_success(self, client, sample_admin_user, sample_announcement):
        """測試成功更新公告"""
        update_data = {
            "title": "更新後的標題",
            "content": "更新後的內容",
            "priority_level": 3
        }
        
        updated_announcement = sample_announcement
        updated_announcement.title = "更新後的標題"
        updated_announcement.content = "更新後的內容"
        updated_announcement.priority_level = 3
        
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.update_announcement', return_value=updated_announcement), \
             patch('app.api.deps.get_db'):
            
            response = client.put(f"/api/v1/announcements/{sample_announcement.id}", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "更新後的標題"
            assert data["content"] == "更新後的內容"
            assert data["priority_level"] == 3
    
    def test_update_announcement_not_found(self, client, sample_admin_user):
        """測試更新不存在的公告"""
        update_data = {"title": "新標題"}
        
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.update_announcement', return_value=None), \
             patch('app.api.deps.get_db'):
            
            response = client.put("/api/v1/announcements/non-existent-id", json=update_data)
            
            assert response.status_code == 404
    
    def test_delete_announcement_success(self, client, sample_admin_user):
        """測試成功刪除公告"""
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.delete_announcement', return_value=True), \
             patch('app.api.deps.get_db'):
            
            response = client.delete("/api/v1/announcements/announcement-id")
            
            assert response.status_code == 200
            data = response.json()
            assert "已刪除" in data["message"]
    
    def test_delete_announcement_not_found(self, client, sample_admin_user):
        """測試刪除不存在的公告"""
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.delete_announcement', return_value=False), \
             patch('app.api.deps.get_db'):
            
            response = client.delete("/api/v1/announcements/non-existent-id")
            
            assert response.status_code == 404
    
    def test_create_emergency_announcement_success(self, client, sample_admin_user, sample_announcement):
        """測試成功建立緊急公告"""
        emergency_data = {
            "title": "緊急公告",
            "content": "這是緊急公告內容",
            "send_notifications": True
        }
        
        emergency_announcement = sample_announcement
        emergency_announcement.announcement_type = AnnouncementType.EMERGENCY.value
        emergency_announcement.priority_level = 5
        
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.publish_emergency_announcement', new_callable=AsyncMock, return_value=emergency_announcement), \
             patch('app.api.deps.get_db'):
            
            response = client.post("/api/v1/announcements/emergency", json=emergency_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["announcement_type"] == "emergency"
            assert data["priority_level"] == 5
    
    def test_expire_announcement_success(self, client, sample_admin_user):
        """測試成功過期公告"""
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.expire_announcement', return_value=True), \
             patch('app.api.deps.get_db'):
            
            response = client.put("/api/v1/announcements/announcement-id/expire")
            
            assert response.status_code == 200
            data = response.json()
            assert "已過期" in data["message"]
    
    def test_expire_announcement_not_found(self, client, sample_admin_user):
        """測試過期不存在的公告"""
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.expire_announcement', return_value=False), \
             patch('app.api.deps.get_db'):
            
            response = client.put("/api/v1/announcements/non-existent-id/expire")
            
            assert response.status_code == 404
    
    def test_get_my_announcements(self, client, sample_admin_user, sample_announcement):
        """測試取得我建立的公告"""
        with patch('app.api.deps.require_admin', return_value=sample_admin_user), \
             patch('app.services.announcement_service.announcement_service.get_announcements_by_creator', return_value=[sample_announcement]), \
             patch('app.api.deps.get_db') as mock_get_db:
            
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            mock_get_db.return_value = mock_db
            
            response = client.get("/api/v1/announcements/my/created")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["announcements"]) == 1
            assert data["total_count"] == 1
    
    def test_pagination_validation(self, client, sample_volunteer_user):
        """測試分頁參數驗證"""
        with patch('app.api.deps.get_current_user', return_value=sample_volunteer_user):
            # 測試負數 skip
            response = client.get("/api/v1/announcements/?skip=-1")
            assert response.status_code == 422
            
            # 測試超過限制的 limit
            response = client.get("/api/v1/announcements/?limit=200")
            assert response.status_code == 422
    
    def test_announcement_type_validation(self, client, sample_admin_user):
        """測試公告類型驗證"""
        invalid_data = {
            "title": "測試公告",
            "content": "內容",
            "announcement_type": "invalid_type"
        }
        
        with patch('app.api.deps.require_admin', return_value=sample_admin_user):
            response = client.post("/api/v1/announcements/", json=invalid_data)
            assert response.status_code == 422
    
    def test_priority_level_validation(self, client, sample_admin_user):
        """測試優先級驗證"""
        invalid_data = {
            "title": "測試公告",
            "content": "內容",
            "announcement_type": "general",
            "priority_level": 10  # 超過最大值 5
        }
        
        with patch('app.api.deps.require_admin', return_value=sample_admin_user):
            response = client.post("/api/v1/announcements/", json=invalid_data)
            assert response.status_code == 422