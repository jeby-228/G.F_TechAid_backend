from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class NeedType(BaseModel):
    """需求類型表"""
    __tablename__ = "need_types"
    
    type = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    
    # 關聯
    needs = relationship("Need", back_populates="need_type_obj")


class NeedStatus(BaseModel):
    """需求狀態表"""
    __tablename__ = "need_statuses"
    
    status = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 關聯
    needs = relationship("Need", back_populates="need_status_obj")


class Need(BaseModel):
    """受災戶需求表"""
    __tablename__ = "needs"
    
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    need_type = Column(String(50), ForeignKey("need_types.type"), nullable=False)
    status = Column(String(50), ForeignKey("need_statuses.status"), nullable=False, default="open", index=True)
    location_data = Column(JSON, nullable=False)  # {address, coordinates, details}
    requirements = Column(JSON, nullable=False)  # 具體需求清單
    urgency_level = Column(Integer, default=1)  # 1-5, 5為最緊急
    contact_info = Column(JSON)  # 聯絡方式
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # 分配給哪個志工/組織
    assigned_at = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    
    # 關聯
    reporter = relationship("User", back_populates="reported_needs", foreign_keys=[reporter_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    need_type_obj = relationship("NeedType", back_populates="needs")
    need_status_obj = relationship("NeedStatus", back_populates="needs")
    need_assignments = relationship("NeedAssignment", back_populates="need")
    supply_reservations = relationship("SupplyReservation", back_populates="need")


class NeedAssignment(BaseModel):
    """需求處理記錄表"""
    __tablename__ = "need_assignments"
    
    need_id = Column(UUID(as_uuid=True), ForeignKey("needs.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))  # 關聯的任務
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    status = Column(String(20), default="assigned")  # 'assigned', 'in_progress', 'completed'
    
    # 關聯
    need = relationship("Need", back_populates="need_assignments")
    task = relationship("Task", back_populates="need_assignments")
    user = relationship("User", back_populates="need_assignments")