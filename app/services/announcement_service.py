"""
公告服務
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models.system import Announcement
from app.models.user import User
from app.utils.constants import AnnouncementType, UserRole, NotificationType
from app.services.notification_service import notification_service


class AnnouncementService:
    """公告服務類"""
    
    def create_announcement(
        self,
        db: Session,
        title: str,
        content: str,
        announcement_type: AnnouncementType,
        created_by: str,
        priority_level: int = 1,
        target_roles: Optional[List[UserRole]] = None,
        expires_at: Optional[datetime] = None
    ) -> Announcement:
        """建立系統公告"""
        announcement = Announcement(
            id=uuid.uuid4(),
            title=title,
            content=content,
            announcement_type=announcement_type.value,
            priority_level=priority_level,
            target_roles=[role.value for role in target_roles] if target_roles else None,
            created_by=uuid.UUID(created_by),
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(announcement)
        db.commit()
        db.refresh(announcement)
        
        return announcement
    
    def get_announcements(
        self,
        db: Session,
        user_role: Optional[UserRole] = None,
        announcement_type: Optional[AnnouncementType] = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50
    ) -> List[Announcement]:
        """取得公告列表"""
        query = db.query(Announcement)
        
        # 過濾活躍公告
        if active_only:
            query = query.filter(Announcement.is_active == True)
            # 過濾未過期的公告
            query = query.filter(
                (Announcement.expires_at.is_(None)) | 
                (Announcement.expires_at > datetime.utcnow())
            )
        
        # 過濾公告類型
        if announcement_type:
            query = query.filter(Announcement.announcement_type == announcement_type.value)
        
        # 過濾目標角色
        if user_role:
            query = query.filter(
                (Announcement.target_roles.is_(None)) |
                (Announcement.target_roles.contains([user_role.value]))
            )
        
        return query.order_by(
            Announcement.priority_level.desc(),
            Announcement.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def get_announcement_by_id(self, db: Session, announcement_id: str) -> Optional[Announcement]:
        """根據 ID 取得公告"""
        try:
            return db.query(Announcement).filter(
                Announcement.id == uuid.UUID(announcement_id)
            ).first()
        except ValueError:
            return None
    
    def update_announcement(
        self,
        db: Session,
        announcement_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        announcement_type: Optional[AnnouncementType] = None,
        priority_level: Optional[int] = None,
        target_roles: Optional[List[UserRole]] = None,
        expires_at: Optional[datetime] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Announcement]:
        """更新公告"""
        announcement = self.get_announcement_by_id(db, announcement_id)
        if not announcement:
            return None
        
        if title is not None:
            announcement.title = title
        if content is not None:
            announcement.content = content
        if announcement_type is not None:
            announcement.announcement_type = announcement_type.value
        if priority_level is not None:
            announcement.priority_level = priority_level
        if target_roles is not None:
            announcement.target_roles = [role.value for role in target_roles]
        if expires_at is not None:
            announcement.expires_at = expires_at
        if is_active is not None:
            announcement.is_active = is_active
        
        announcement.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(announcement)
        
        return announcement
    
    def delete_announcement(self, db: Session, announcement_id: str) -> bool:
        """刪除公告（軟刪除）"""
        announcement = self.get_announcement_by_id(db, announcement_id)
        if not announcement:
            return False
        
        announcement.is_active = False
        announcement.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    async def publish_emergency_announcement(
        self,
        db: Session,
        title: str,
        content: str,
        created_by: str,
        target_roles: Optional[List[UserRole]] = None,
        send_notifications: bool = True
    ) -> Announcement:
        """發布緊急公告並推播通知"""
        # 建立緊急公告
        announcement = self.create_announcement(
            db=db,
            title=title,
            content=content,
            announcement_type=AnnouncementType.EMERGENCY,
            created_by=created_by,
            priority_level=5,  # 最高優先級
            target_roles=target_roles
        )
        
        # 發送推播通知
        if send_notifications:
            await self._send_announcement_notifications(
                db=db,
                announcement=announcement,
                target_roles=target_roles
            )
        
        return announcement
    
    async def _send_announcement_notifications(
        self,
        db: Session,
        announcement: Announcement,
        target_roles: Optional[List[UserRole]] = None
    ):
        """發送公告通知給目標用戶"""
        # 查詢目標用戶
        query = db.query(User)
        
        if target_roles:
            query = query.filter(User.role.in_([role.value for role in target_roles]))
        
        target_users = query.all()
        user_ids = [str(user.id) for user in target_users]
        
        # 發送通知
        if user_ids:
            notification_type = (
                NotificationType.EMERGENCY 
                if announcement.announcement_type == AnnouncementType.EMERGENCY.value
                else NotificationType.SYSTEM
            )
            
            await notification_service.send_emergency_notification(
                db=db,
                user_ids=user_ids,
                title=f"系統公告：{announcement.title}",
                message=announcement.content[:200] + ("..." if len(announcement.content) > 200 else ""),
                related_id=str(announcement.id)
            )
    
    def get_announcements_count(
        self,
        db: Session,
        user_role: Optional[UserRole] = None,
        announcement_type: Optional[AnnouncementType] = None,
        active_only: bool = True
    ) -> int:
        """取得公告總數"""
        query = db.query(Announcement)
        
        if active_only:
            query = query.filter(Announcement.is_active == True)
            query = query.filter(
                (Announcement.expires_at.is_(None)) | 
                (Announcement.expires_at > datetime.utcnow())
            )
        
        if announcement_type:
            query = query.filter(Announcement.announcement_type == announcement_type.value)
        
        if user_role:
            query = query.filter(
                (Announcement.target_roles.is_(None)) |
                (Announcement.target_roles.contains([user_role.value]))
            )
        
        return query.count()
    
    def get_emergency_announcements(
        self,
        db: Session,
        user_role: Optional[UserRole] = None,
        limit: int = 5
    ) -> List[Announcement]:
        """取得緊急公告（用於首頁顯示）"""
        return self.get_announcements(
            db=db,
            user_role=user_role,
            announcement_type=AnnouncementType.EMERGENCY,
            active_only=True,
            limit=limit
        )
    
    def expire_announcement(self, db: Session, announcement_id: str) -> bool:
        """手動過期公告"""
        announcement = self.get_announcement_by_id(db, announcement_id)
        if not announcement:
            return False
        
        announcement.expires_at = datetime.utcnow()
        announcement.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    def get_announcements_by_creator(
        self,
        db: Session,
        creator_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Announcement]:
        """取得特定創建者的公告"""
        try:
            return db.query(Announcement).filter(
                Announcement.created_by == uuid.UUID(creator_id)
            ).order_by(
                Announcement.created_at.desc()
            ).offset(skip).limit(limit).all()
        except ValueError:
            return []


# 建立全域實例
announcement_service = AnnouncementService()