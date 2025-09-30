from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Announcement(BaseModel):
    """系統公告表"""
    __tablename__ = "announcements"
    
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    announcement_type = Column(String(50), default="general")  # 'emergency', 'general', 'maintenance'
    priority_level = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    target_roles = Column(JSON)  # 目標用戶角色
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    
    # 關聯
    creator = relationship("User", back_populates="created_announcements")


class Notification(BaseModel):
    """通知記錄表"""
    __tablename__ = "notifications"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # 'task', 'supply', 'system', etc.
    related_id = Column(UUID(as_uuid=True))  # 關聯的任務、需求或預訂ID
    is_read = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))
    
    # 關聯
    user = relationship("User", back_populates="notifications")


class SystemLog(BaseModel):
    """系統日誌表"""
    __tablename__ = "system_logs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))  # 'task', 'need', 'supply', etc.
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSON)
    ip_address = Column(String(45))  # IPv4 (15) or IPv6 (45) address
    user_agent = Column(Text)
    
    # 關聯
    user = relationship("User", back_populates="system_logs")


class Shelter(BaseModel):
    """避難所資訊表"""
    __tablename__ = "shelters"
    
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    location_data = Column(JSON, nullable=False)
    capacity = Column(Integer)
    current_occupancy = Column(Integer, default=0)
    contact_info = Column(JSON)
    facilities = Column(JSON)  # 設施資訊
    status = Column(String(50), default="active")  # 'active', 'full', 'closed'
    managed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # 關聯
    manager = relationship("User", back_populates="managed_shelters")