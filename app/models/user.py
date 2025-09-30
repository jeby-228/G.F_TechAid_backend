from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class UserRole(BaseModel):
    """用戶角色表"""
    __tablename__ = "user_roles"
    
    role = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    permissions = Column(JSON, nullable=False)
    
    # 關聯
    users = relationship("User")


class User(BaseModel):
    """用戶表"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), ForeignKey("user_roles.role"), nullable=False, index=True)
    is_approved = Column(Boolean, default=False)
    profile_data = Column(JSON)
    
    # 關聯
    user_role = relationship("UserRole")
    organizations = relationship("Organization", foreign_keys="Organization.user_id")
    created_tasks = relationship("Task", foreign_keys="Task.creator_id")
    reported_needs = relationship("Need", foreign_keys="Need.reporter_id")
    task_claims = relationship("TaskClaim")
    need_assignments = relationship("NeedAssignment", foreign_keys="NeedAssignment.user_id")
    supply_stations = relationship("SupplyStation")
    supply_reservations = relationship("SupplyReservation")
    notifications = relationship("Notification")
    system_logs = relationship("SystemLog")
    managed_shelters = relationship("Shelter")
    created_announcements = relationship("Announcement")


class Organization(BaseModel):
    """組織資訊表（針對志工組織）"""
    __tablename__ = "organizations"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_name = Column(String(200), nullable=False)
    organization_type = Column(String(50), nullable=False)  # 'official' or 'unofficial'
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    address = Column(Text)
    description = Column(Text)
    approval_status = Column(String(20), default="pending")  # 'pending', 'approved', 'rejected'
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # 關聯
    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])