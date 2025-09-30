"""
通知服務
"""
from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import asyncio
import json
import logging
from fastapi import WebSocket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.models.system import Notification
from app.models.user import User
from app.utils.constants import NotificationType, UserRole
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服務類"""
    
    def __init__(self):
        # WebSocket 連線管理
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect_websocket(self, websocket: WebSocket, user_id: str):
        """建立 WebSocket 連線"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    async def disconnect_websocket(self, websocket: WebSocket, user_id: str):
        """斷開 WebSocket 連線"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_realtime_notification(self, user_id: str, notification_data: dict):
        """發送即時通知到 WebSocket"""
        if user_id in self.active_connections:
            message = json.dumps(notification_data, ensure_ascii=False, default=str)
            disconnected_connections = set()
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send WebSocket message to user {user_id}: {e}")
                    disconnected_connections.add(connection)
            
            # 清理斷開的連線
            for connection in disconnected_connections:
                self.active_connections[user_id].discard(connection)
    
    async def send_email_notification(self, email: str, subject: str, content: str):
        """發送 Email 通知"""
        try:
            if not hasattr(settings, 'SMTP_SERVER') or not settings.SMTP_SERVER:
                logger.warning("SMTP server not configured, skipping email notification")
                return False
                
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'html', 'utf-8'))
            
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False
    
    async def send_sms_notification(self, phone: str, message: str):
        """發送簡訊通知 (模擬實作)"""
        try:
            # 這裡應該整合實際的簡訊服務提供商 API
            # 例如：Twilio, AWS SNS, 或台灣的簡訊服務商
            logger.info(f"SMS would be sent to {phone}: {message}")
            
            # 模擬簡訊發送
            if hasattr(settings, 'SMS_ENABLED') and settings.SMS_ENABLED:
                # 實際的簡訊發送邏輯
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False
    
    async def create_notification(
        self,
        db: Session,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType,
        related_id: Optional[str] = None,
        send_email: bool = False,
        send_sms: bool = False
    ) -> Notification:
        """建立通知記錄"""
        notification = Notification(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            title=title,
            message=message,
            notification_type=notification_type.value,
            related_id=uuid.UUID(related_id) if related_id else None,
            is_read=False
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # 發送即時通知
        notification_data = {
            "id": str(notification.id),
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "related_id": str(notification.related_id) if notification.related_id else None,
            "created_at": notification.created_at.isoformat(),
            "is_read": notification.is_read
        }
        
        await self.send_realtime_notification(user_id, notification_data)
        
        # 發送 Email 通知
        if send_email:
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            if user and user.email:
                await self.send_email_notification(
                    user.email,
                    f"光復e互助平台 - {title}",
                    self._format_email_content(title, message)
                )
        
        # 發送簡訊通知
        if send_sms:
            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            if user and user.phone:
                await self.send_sms_notification(user.phone, f"{title}: {message}")
        
        return notification
    
    def _format_email_content(self, title: str, message: str) -> str:
        """格式化 Email 內容"""
        return f"""
        <html>
        <body>
            <h2>光復e互助平台通知</h2>
            <h3>{title}</h3>
            <p>{message}</p>
            <hr>
            <p><small>此為系統自動發送的通知郵件，請勿直接回覆。</small></p>
        </body>
        </html>
        """
    
    def get_user_notifications(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """取得用戶通知列表"""
        query = db.query(Notification).filter(Notification.user_id == uuid.UUID(user_id))
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    def mark_notification_as_read(self, db: Session, notification_id: str, user_id: str) -> bool:
        """標記通知為已讀"""
        notification = db.query(Notification).filter(
            Notification.id == uuid.UUID(notification_id),
            Notification.user_id == uuid.UUID(user_id)
        ).first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            return True
        
        return False
    
    def mark_all_notifications_as_read(self, db: Session, user_id: str) -> int:
        """標記所有通知為已讀"""
        updated_count = db.query(Notification).filter(
            Notification.user_id == uuid.UUID(user_id),
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        
        db.commit()
        return updated_count
    
    def get_unread_count(self, db: Session, user_id: str) -> int:
        """取得未讀通知數量"""
        return db.query(Notification).filter(
            Notification.user_id == uuid.UUID(user_id),
            Notification.is_read == False
        ).count()
    
    async def send_supply_reservation_notification(
        self,
        db: Session,
        reservation_id: str,
        station_manager_id: str,
        user_name: str,
        station_name: str,
        task_title: Optional[str] = None
    ):
        """發送物資預訂通知給站點管理者"""
        title = "新的物資預訂"
        
        if task_title:
            message = f"{user_name} 為任務「{task_title}」預訂了您站點「{station_name}」的物資，請查看並確認。"
        else:
            message = f"{user_name} 預訂了您站點「{station_name}」的物資，請查看並確認。"
        
        await self.create_notification(
            db=db,
            user_id=station_manager_id,
            title=title,
            message=message,
            notification_type=NotificationType.SUPPLY,
            related_id=reservation_id,
            send_email=True  # 物資預訂通知發送 Email
        )
    
    async def send_reservation_confirmed_notification(
        self,
        db: Session,
        reservation_id: str,
        user_id: str,
        station_name: str
    ):
        """發送預訂確認通知給預訂者"""
        title = "物資預訂已確認"
        message = f"您在「{station_name}」的物資預訂已確認，請前往領取。"
        
        await self.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.SUPPLY,
            related_id=reservation_id,
            send_sms=True  # 預訂確認發送簡訊
        )
    
    async def send_reservation_status_notification(
        self,
        db: Session,
        reservation_id: str,
        user_id: str,
        status: str,
        station_name: str
    ):
        """發送預訂狀態更新通知"""
        status_messages = {
            "confirmed": "已確認",
            "picked_up": "已領取",
            "delivered": "已配送完成",
            "cancelled": "已取消"
        }
        
        title = "物資預訂狀態更新"
        status_text = status_messages.get(status, status)
        message = f"您在「{station_name}」的物資預訂狀態已更新為：{status_text}"
        
        await self.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.SUPPLY,
            related_id=reservation_id
        )
    
    # 任務相關通知方法
    async def send_task_assignment_notification(
        self,
        db: Session,
        task_id: str,
        user_id: str,
        task_title: str
    ):
        """發送任務分配通知"""
        title = "新任務分配"
        message = f"您被分配了新任務：{task_title}"
        
        await self.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.TASK,
            related_id=task_id,
            send_sms=True
        )
    
    async def send_task_status_notification(
        self,
        db: Session,
        task_id: str,
        user_id: str,
        task_title: str,
        status: str
    ):
        """發送任務狀態更新通知"""
        status_messages = {
            "approved": "已審核通過",
            "rejected": "已被拒絕",
            "completed": "已完成",
            "cancelled": "已取消"
        }
        
        title = "任務狀態更新"
        status_text = status_messages.get(status, status)
        message = f"您的任務「{task_title}」狀態已更新為：{status_text}"
        
        await self.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.TASK,
            related_id=task_id
        )
    
    # 緊急通知方法
    async def send_emergency_notification(
        self,
        db: Session,
        user_ids: List[str],
        title: str,
        message: str,
        related_id: Optional[str] = None
    ):
        """發送緊急通知給多個用戶"""
        for user_id in user_ids:
            await self.create_notification(
                db=db,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=NotificationType.EMERGENCY,
                related_id=related_id,
                send_email=True,
                send_sms=True
            )


# 建立全域實例
notification_service = NotificationService()