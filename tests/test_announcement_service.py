"""
公告服務測試
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.announcement_service import AnnouncementService
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


class TestAnnouncementService:
    """公告服務測試類"""
    
    @pytest.fixture
    def announcement_service(self):
        """建立公告服務實例"""
        return AnnouncementService()
    
    @pytest.fixture
    def mock_db(self):
        """模擬資料庫會話"""
        return Mock(spec=Session)
    
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
    
    def test_create_announcement_basic(self, announcement_service, mock_db, sample_admin_user):
        """測試基本公告建立"""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        result = announcement_service.create_announcement(
            db=mock_db,
            title="測試公告",
            content="這是測試內容",
            announcement_type=AnnouncementType.GENERAL,
            created_by=str(sample_admin_user.id)
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_announcement_with_target_roles(self, announcement_service, mock_db, sample_admin_user):
        """測試建立指定目標角色的公告"""
        target_roles = [UserRole.VOLUNTEER, UserRole.VICTIM]
        
        result = announcement_service.create_announcement(
            db=mock_db,
            title="志工公告",
            content="這是給志工的公告",
            announcement_type=AnnouncementType.GENERAL,
            created_by=str(sample_admin_user.id),
            target_roles=target_roles
        )
        
        mock_db.add.assert_called_once()
        # 驗證傳入的公告物件有正確的 target_roles
        added_announcement = mock_db.add.call_args[0][0]
        assert added_announcement.target_roles == [role.value for role in target_roles]
    
    def test_create_announcement_with_expiry(self, announcement_service, mock_db, sample_admin_user):
        """測試建立有過期時間的公告"""
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        result = announcement_service.create_announcement(
            db=mock_db,
            title="限時公告",
            content="這是限時公告",
            announcement_type=AnnouncementType.GENERAL,
            created_by=str(sample_admin_user.id),
            expires_at=expires_at
        )
        
        added_announcement = mock_db.add.call_args[0][0]
        assert added_announcement.expires_at == expires_at
    
    def test_get_announcements_basic(self, announcement_service, mock_db, sample_announcement):
        """測試取得公告列表"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_announcement]
        
        mock_db.query.return_value = mock_query
        
        result = announcement_service.get_announcements(
            db=mock_db,
            user_role=UserRole.VOLUNTEER
        )
        
        assert len(result) == 1
        assert result[0].title == "測試公告"
    
    def test_get_announcements_with_filters(self, announcement_service, mock_db):
        """測試帶過濾條件的公告查詢"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        announcement_service.get_announcements(
            db=mock_db,
            user_role=UserRole.VOLUNTEER,
            announcement_type=AnnouncementType.EMERGENCY,
            active_only=True
        )
        
        # 驗證過濾條件被正確應用
        assert mock_query.filter.call_count >= 3  # active, type, role filters
    
    def test_get_announcement_by_id_success(self, announcement_service, mock_db, sample_announcement):
        """測試成功根據 ID 取得公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_announcement
        
        result = announcement_service.get_announcement_by_id(mock_db, "announcement-id")
        
        assert result == sample_announcement
    
    def test_get_announcement_by_id_not_found(self, announcement_service, mock_db):
        """測試取得不存在的公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = announcement_service.get_announcement_by_id(mock_db, "non-existent-id")
        
        assert result is None
    
    def test_get_announcement_by_id_invalid_uuid(self, announcement_service, mock_db):
        """測試無效的 UUID 格式"""
        result = announcement_service.get_announcement_by_id(mock_db, "invalid-uuid")
        
        assert result is None
    
    def test_update_announcement_success(self, announcement_service, mock_db, sample_announcement):
        """測試成功更新公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_announcement
        
        result = announcement_service.update_announcement(
            db=mock_db,
            announcement_id="announcement-id",
            title="更新後的標題",
            content="更新後的內容",
            priority_level=3
        )
        
        assert result.title == "更新後的標題"
        assert result.content == "更新後的內容"
        assert result.priority_level == 3
        mock_db.commit.assert_called_once()
    
    def test_update_announcement_not_found(self, announcement_service, mock_db):
        """測試更新不存在的公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = announcement_service.update_announcement(
            db=mock_db,
            announcement_id="non-existent-id",
            title="新標題"
        )
        
        assert result is None
        mock_db.commit.assert_not_called()
    
    def test_delete_announcement_success(self, announcement_service, mock_db, sample_announcement):
        """測試成功刪除公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_announcement
        
        result = announcement_service.delete_announcement(mock_db, "announcement-id")
        
        assert result is True
        assert sample_announcement.is_active is False
        mock_db.commit.assert_called_once()
    
    def test_delete_announcement_not_found(self, announcement_service, mock_db):
        """測試刪除不存在的公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = announcement_service.delete_announcement(mock_db, "non-existent-id")
        
        assert result is False
        mock_db.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_emergency_announcement(self, announcement_service, mock_db, sample_admin_user):
        """測試發布緊急公告"""
        with patch.object(announcement_service, 'create_announcement') as mock_create, \
             patch.object(announcement_service, '_send_announcement_notifications', new_callable=AsyncMock) as mock_send:
            
            mock_announcement = Mock()
            mock_create.return_value = mock_announcement
            
            result = await announcement_service.publish_emergency_announcement(
                db=mock_db,
                title="緊急公告",
                content="這是緊急公告",
                created_by=str(sample_admin_user.id),
                send_notifications=True
            )
            
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args['announcement_type'] == AnnouncementType.EMERGENCY
            assert call_args['priority_level'] == 5
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_announcement_notifications(self, announcement_service, mock_db, sample_announcement):
        """測試發送公告通知"""
        # 模擬用戶查詢
        mock_users = [
            Mock(id="user1"),
            Mock(id="user2")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_users
        
        with patch('app.services.announcement_service.notification_service.send_emergency_notification', new_callable=AsyncMock) as mock_send:
            await announcement_service._send_announcement_notifications(
                db=mock_db,
                announcement=sample_announcement,
                target_roles=[UserRole.VOLUNTEER]
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert len(call_args['user_ids']) == 2
            assert "系統公告" in call_args['title']
    
    def test_get_announcements_count(self, announcement_service, mock_db):
        """測試取得公告總數"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        
        mock_db.query.return_value = mock_query
        
        result = announcement_service.get_announcements_count(
            db=mock_db,
            user_role=UserRole.VOLUNTEER,
            active_only=True
        )
        
        assert result == 5
    
    def test_get_emergency_announcements(self, announcement_service, mock_db):
        """測試取得緊急公告"""
        with patch.object(announcement_service, 'get_announcements') as mock_get:
            mock_get.return_value = []
            
            announcement_service.get_emergency_announcements(
                db=mock_db,
                user_role=UserRole.VOLUNTEER,
                limit=3
            )
            
            mock_get.assert_called_once()
            call_args = mock_get.call_args[1]
            assert call_args['announcement_type'] == AnnouncementType.EMERGENCY
            assert call_args['limit'] == 3
    
    def test_expire_announcement_success(self, announcement_service, mock_db, sample_announcement):
        """測試手動過期公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_announcement
        
        result = announcement_service.expire_announcement(mock_db, "announcement-id")
        
        assert result is True
        assert sample_announcement.expires_at is not None
        mock_db.commit.assert_called_once()
    
    def test_expire_announcement_not_found(self, announcement_service, mock_db):
        """測試過期不存在的公告"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = announcement_service.expire_announcement(mock_db, "non-existent-id")
        
        assert result is False
        mock_db.commit.assert_not_called()
    
    def test_get_announcements_by_creator(self, announcement_service, mock_db, sample_announcement):
        """測試取得特定創建者的公告"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_announcement]
        
        mock_db.query.return_value = mock_query
        
        result = announcement_service.get_announcements_by_creator(
            db=mock_db,
            creator_id="550e8400-e29b-41d4-a716-446655440000"
        )
        
        assert len(result) == 1
        assert result[0].title == "測試公告"
    
    def test_get_announcements_by_creator_invalid_uuid(self, announcement_service, mock_db):
        """測試無效創建者 UUID"""
        result = announcement_service.get_announcements_by_creator(
            db=mock_db,
            creator_id="invalid-uuid"
        )
        
        assert result == []
    
    def test_get_announcements_role_filtering(self, announcement_service, mock_db):
        """測試角色過濾功能"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        announcement_service.get_announcements(
            db=mock_db,
            user_role=UserRole.VOLUNTEER
        )
        
        # 驗證角色過濾被正確應用
        filter_calls = mock_query.filter.call_args_list
        # 應該有多個過濾條件：active, expires_at, target_roles
        assert len(filter_calls) >= 3
    
    def test_announcement_priority_ordering(self, announcement_service, mock_db):
        """測試公告優先級排序"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        announcement_service.get_announcements(db=mock_db)
        
        # 驗證排序被正確應用
        mock_query.order_by.assert_called_once()
        # 排序應該是按優先級降序，然後按建立時間降序