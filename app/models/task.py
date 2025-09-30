from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class TaskType(BaseModel):
    """任務類型表"""
    __tablename__ = "task_types"
    
    type = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(100))
    
    # 關聯
    tasks = relationship("Task")


class TaskStatus(BaseModel):
    """任務狀態表"""
    __tablename__ = "task_statuses"
    
    status = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 關聯
    tasks = relationship("Task")


class Task(BaseModel):
    """任務表"""
    __tablename__ = "tasks"
    
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(String(50), ForeignKey("task_types.type"), nullable=False)
    status = Column(String(50), ForeignKey("task_statuses.status"), nullable=False, default="available", index=True)
    location_data = Column(JSON, nullable=False)  # {address, coordinates, details}
    required_volunteers = Column(Integer, default=1)
    required_skills = Column(JSON)  # 所需技能或資格
    deadline = Column(DateTime(timezone=True))
    priority_level = Column(Integer, default=1)  # 1-5, 5為最高優先級
    approval_status = Column(String(20), default="approved")  # 'pending', 'approved', 'rejected'
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # 關聯
    creator = relationship("User", foreign_keys=[creator_id])
    approver = relationship("User", foreign_keys=[approved_by])
    task_type_obj = relationship("TaskType")
    task_status_obj = relationship("TaskStatus")
    task_claims = relationship("TaskClaim")
    need_assignments = relationship("NeedAssignment")
    supply_reservations = relationship("SupplyReservation")


class TaskClaim(BaseModel):
    """任務認領表"""
    __tablename__ = "task_claims"
    
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    claimed_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    status = Column(String(20), default="claimed")  # 'claimed', 'started', 'completed', 'cancelled'
    
    # 關聯
    task = relationship("Task")
    user = relationship("User")
    
    # 唯一約束
    __table_args__ = (
        {"schema": None},
    )