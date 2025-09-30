"""
通知服務測試
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.notification_service import NotificationService
from app.models.system import Notification
from app.models.user import User
from app.utils.constants import NotificationType, UserRole

# AsyncMock for Python 3.7 compatibility
try:
    from unittest.mock import AsyncMock
except ImportError:
    class AsyncMock(Mock):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
        async def __call__(self, *args, **kwargs):
            return super().__call__(*args, **kwargs)


class TestNotificationService:
    """通知服務測試類"""
    
    @pytest.fixture
    def notification_service(self):
        """建立通知服務實例"""
        return NotificationService()
    
    @pytest.fixture
    def mock_db(self):
        """模擬資料庫會話"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_user(self):
        """建立測試用戶"""
        return User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            phone="0912345678",
            name="測試用戶",
            role=UserRole.VOLUNTEER
        )
    
    @pytest.mark.asyncio
    async def test_create_notification_basic(self, notification_service, mock_db, sample_user):
        """測試基本通知建立"""
        # 設定模擬
        mock_notification = Mock(spec=Notification)
        mock_notification.id = "notification-id"
        mock_notification.title = "測試通知"
        mock_notification.message = "這是測試訊息"
        mock_notification.notification_type = NotificationType.SYSTEM.value
        mock_notification.related_id = None
        mock_notification.is_read = False
        mock_notification.created_at = datetime.utcnow()
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch.object(notification_service, 'send_realtime_notification', new_callable=AsyncMock) as mock_realtime:
            # 執行測試
            result = await notification_service.create_notification(
                db=mock_db,
                user_id=str(sample_user.id),
                title="測試通知",
                message="這是測試訊息",
                notification_type=NotificationType.SYSTEM
            )
            
            # 驗證結果
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_realtime.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_notification_with_email(self, notification_service, mock_db, sample_user):
        """測試建立通知並發送 Email"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch.object(notification_service, 'send_email_notification', new_callable=AsyncMock) as mock_email, \
             patch.object(notification_service, 'send_realtime_notification', new_callable=AsyncMock):
            
            await notification_service.create_notification(
                db=mock_db,
                user_id=str(sample_user.id),
                title="測試通知",
                message="這是測試訊息",
                notification_type=NotificationType.SYSTEM,
                send_email=True
            )
            
            mock_email.assert_called_once_with(
                sample_user.email,
                "光復e互助平台 - 測試通知",
                notification_service._format_email_content("測試通知", "這是測試訊息")
            )
    
    @pytest.mark.asyncio
    async def test_create_notification_with_sms(self, notification_service, mock_db, sample_user):
        """測試建立通知並發送簡訊"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        with patch.object(notification_service, 'send_sms_notification', new_callable=AsyncMock) as mock_sms, \
             patch.object(notification_service, 'send_realtime_notification', new_callable=AsyncMock):
            
            await notification_service.create_notification(
                db=mock_db,
                user_id=str(sample_user.id),
                title="測試通知",
                message="這是測試訊息",
                notification_type=NotificationType.EMERGENCY,
                send_sms=True
            )
            
            mock_sms.assert_called_once_with(
                sample_user.phone,
                "測試通知: 這是測試訊息"
            )
    
    def test_get_user_notifications(self, notification_service, mock_db, sample_user):
        """測試取得用戶通知列表"""
        # 設定模擬通知
        mock_notifications = [
            Mock(spec=Notification, id="notif-1", title="通知1"),
            Mock(spec=Notification, id="notif-2", title="通知2")
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_notifications
        
        mock_db.query.return_value = mock_query
        
        # 執行測試
        result = notification_service.get_user_notifications(
            db=mock_db,
            user_id=str(sample_user.id),
            skip=0,
            limit=10
        )
        
        # 驗證結果
        assert len(result) == 2
        assert result[0].title == "通知1"
        assert result[1].title == "通知2"
    
    def test_get_user_notifications_unread_only(self, notification_service, mock_db, sample_user):
        """測試只取得未讀通知"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_db.query.return_value = mock_query
        
        # 執行測試
        notification_service.get_user_notifications(
            db=mock_db,
            user_id=str(sample_user.id),
            unread_only=True
        )
        
        # 驗證過濾條件被正確調用
        assert mock_query.filter.call_count >= 2  # user_id 和 is_read 過濾
    
    def test_mark_notification_as_read_success(self, notification_service, mock_db, sample_user):
        """測試成功標記通知為已讀"""
        # 設定模擬通知
        mock_notification = Mock(spec=Notification)
        mock_notification.is_read = False
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_notification
        
        # 執行測試
        result = notification_service.mark_notification_as_read(
            db=mock_db,
            notification_id="notification-id",
            user_id=str(sample_user.id)
        )
        
        # 驗證結果
        assert result is True
        assert mock_notification.is_read is True
        assert mock_notification.read_at is not None
        mock_db.commit.assert_called_once()
    
    def test_mark_notification_as_read_not_found(self, notification_service, mock_db, sample_user):
        """測試標記不存在的通知為已讀"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = notification_service.mark_notification_as_read(
            db=mock_db,
            notification_id="non-existent-id",
            user_id=str(sample_user.id)
        )
        
        assert result is False
        mock_db.commit.assert_not_called()
    
    def test_mark_notification_as_read_already_read(self, notification_service, mock_db, sample_user):
        """測試標記已讀通知為已讀"""
        mock_notification = Mock(spec=Notification)
        mock_notification.is_read = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_notification
        
        result = notification_service.mark_notification_as_read(
            db=mock_db,
            notification_id="notification-id",
            user_id=str(sample_user.id)
        )
        
        assert result is False
        mock_db.commit.assert_not_called()
    
    def test_mark_all_notifications_as_read(self, notification_service, mock_db, sample_user):
        """測試標記所有通知為已讀"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 5  # 模擬更新了 5 個通知
        
        mock_db.query.return_value = mock_query
        
        result = notification_service.mark_all_notifications_as_read(
            db=mock_db,
            user_id=str(sample_user.id)
        )
        
        assert result == 5
        mock_db.commit.assert_called_once()
    
    def test_get_unread_count(self, notification_service, mock_db, sample_user):
        """測試取得未讀通知數量"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 3
        
        mock_db.query.return_value = mock_query
        
        result = notification_service.get_unread_count(
            db=mock_db,
            user_id=str(sample_user.id)
        )
        
        assert result == 3
    
    @pytest.mark.asyncio
    async def test_send_supply_reservation_notification(self, notification_service, mock_db):
        """測試發送物資預訂通知"""
        with patch.object(notification_service, 'create_notification', new_callable=AsyncMock) as mock_create:
            await notification_service.send_supply_reservation_notification(
                db=mock_db,
                reservation_id="reservation-id",
                station_manager_id="manager-id",
                user_name="測試用戶",
                station_name="測試站點",
                task_title="測試任務"
            )
            
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[1]['title'] == "新的物資預訂"
            assert "測試用戶" in call_args[1]['message']
            assert "測試站點" in call_args[1]['message']
            assert "測試任務" in call_args[1]['message']
            assert call_args[1]['notification_type'] == NotificationType.SUPPLY
            assert call_args[1]['send_email'] is True
    
    @pytest.mark.asyncio
    async def test_send_emergency_notification(self, notification_service, mock_db):
        """測試發送緊急通知"""
        user_ids = ["user1", "user2", "user3"]
        
        with patch.object(notification_service, 'create_notification', new_callable=AsyncMock) as mock_create:
            await notification_service.send_emergency_notification(
                db=mock_db,
                user_ids=user_ids,
                title="緊急通知",
                message="這是緊急訊息"
            )
            
            assert mock_create.call_count == 3
            for call in mock_create.call_args_list:
                assert call[1]['title'] == "緊急通知"
                assert call[1]['message'] == "這是緊急訊息"
                assert call[1]['notification_type'] == NotificationType.EMERGENCY
                assert call[1]['send_email'] is True
                assert call[1]['send_sms'] is True
    
    @pytest.mark.asyncio
    async def test_websocket_connection_management(self, notification_service):
        """測試 WebSocket 連線管理"""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        user_id = "test-user"
        
        # 測試連線
        await notification_service.connect_websocket(mock_websocket, user_id)
        
        assert user_id in notification_service.active_connections
        assert mock_websocket in notification_service.active_connections[user_id]
        mock_websocket.accept.assert_called_once()
        
        # 測試斷線
        await notification_service.disconnect_websocket(mock_websocket, user_id)
        
        assert user_id not in notification_service.active_connections
    
    @pytest.mark.asyncio
    async def test_send_realtime_notification(self, notification_service):
        """測試發送即時通知"""
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        user_id = "test-user"
        
        # 建立連線
        notification_service.active_connections[user_id] = {mock_websocket}
        
        notification_data = {
            "id": "notif-id",
            "title": "測試通知",
            "message": "測試訊息"
        }
        
        await notification_service.send_realtime_notification(user_id, notification_data)
        
        mock_websocket.send_text.assert_called_once()
        sent_message = mock_websocket.send_text.call_args[0][0]
        assert "測試通知" in sent_message
        assert "測試訊息" in sent_message
    
    @pytest.mark.asyncio
    async def test_send_email_notification_success(self, notification_service):
        """測試成功發送 Email 通知"""
        with patch('smtplib.SMTP') as mock_smtp_class, \
             patch('app.core.config.settings') as mock_settings:
            
            mock_settings.SMTP_SERVER = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_FROM_EMAIL = "test@example.com"
            mock_settings.SMTP_USE_TLS = True
            mock_settings.SMTP_USERNAME = "username"
            mock_settings.SMTP_PASSWORD = "password"
            
            mock_server = Mock()
            mock_smtp_class.return_value = mock_server
            
            result = await notification_service.send_email_notification(
                "recipient@example.com",
                "測試主題",
                "測試內容"
            )
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_notification_no_smtp_config(self, notification_service):
        """測試沒有 SMTP 配置時的 Email 發送"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.SMTP_SERVER = None
            
            result = await notification_service.send_email_notification(
                "recipient@example.com",
                "測試主題",
                "測試內容"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_sms_notification(self, notification_service):
        """測試發送簡訊通知"""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.SMS_ENABLED = True
            
            result = await notification_service.send_sms_notification(
                "0912345678",
                "測試簡訊內容"
            )
            
            assert result is True
    
    def test_format_email_content(self, notification_service):
        """測試 Email 內容格式化"""
        title = "測試標題"
        message = "測試訊息"
        
        content = notification_service._format_email_content(title, message)
        
        assert title in content
        assert message in content
        assert "光復e互助平台通知" in content
        assert "<html>" in content
        assert "</html>" in content