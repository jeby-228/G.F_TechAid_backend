from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SupplyType(BaseModel):
    """物資類型表"""
    __tablename__ = "supply_types"
    
    type = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    category = Column(String(50))  # 'food', 'medical', 'clothing', 'tools', etc.
    unit = Column(String(20))  # 'piece', 'box', 'kg', 'liter', etc.
    description = Column(Text)
    
    # 關聯
    inventory_items = relationship("InventoryItem", back_populates="supply_type_rel")
    reservation_items = relationship("ReservationItem", back_populates="supply_type_rel")


class SupplyStation(BaseModel):
    """物資站點表"""
    __tablename__ = "supply_stations"
    
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    location_data = Column(JSON, nullable=False)  # {coordinates, details}
    contact_info = Column(JSON, nullable=False)  # {phone, email, hours}
    capacity_info = Column(JSON)  # 容量資訊
    is_active = Column(Boolean, default=True, index=True)
    
    # 關聯
    manager = relationship("User", back_populates="supply_stations")
    inventory_items = relationship("InventoryItem", back_populates="station")
    supply_reservations = relationship("SupplyReservation", back_populates="station")


class InventoryItem(BaseModel):
    """物資庫存表"""
    __tablename__ = "inventory_items"
    
    station_id = Column(UUID(as_uuid=True), ForeignKey("supply_stations.id", ondelete="CASCADE"), nullable=False)
    supply_type = Column(String(50), ForeignKey("supply_types.type"), nullable=False)
    description = Column(Text)
    is_available = Column(Boolean, default=True, index=True)
    notes = Column(Text)  # 額外說明（如保存期限、狀況等）
    
    # 關聯
    station = relationship("SupplyStation", back_populates="inventory_items")
    supply_type_rel = relationship("SupplyType", back_populates="inventory_items")
    
    # 唯一約束
    __table_args__ = (
        {"schema": None},
    )


class ReservationStatus(BaseModel):
    """物資預訂狀態表"""
    __tablename__ = "reservation_statuses"
    
    status = Column(String(50), primary_key=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 關聯
    supply_reservations = relationship("SupplyReservation", back_populates="reservation_status")


class SupplyReservation(BaseModel):
    """物資預訂表"""
    __tablename__ = "supply_reservations"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    station_id = Column(UUID(as_uuid=True), ForeignKey("supply_stations.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))  # 關聯的任務
    need_id = Column(UUID(as_uuid=True), ForeignKey("needs.id"))  # 關聯的需求
    status = Column(String(50), ForeignKey("reservation_statuses.status"), nullable=False, default="pending", index=True)
    reserved_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    picked_up_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    
    # 關聯
    user = relationship("User", back_populates="supply_reservations")
    station = relationship("SupplyStation", back_populates="supply_reservations")
    task = relationship("Task", back_populates="supply_reservations")
    need = relationship("Need", back_populates="supply_reservations")
    reservation_status = relationship("ReservationStatus", back_populates="supply_reservations")
    reservation_items = relationship("ReservationItem", back_populates="reservation")


class ReservationItem(BaseModel):
    """預訂物資明細表"""
    __tablename__ = "reservation_items"
    
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("supply_reservations.id", ondelete="CASCADE"), nullable=False)
    supply_type = Column(String(50), ForeignKey("supply_types.type"), nullable=False)
    requested_quantity = Column(Integer, default=1)
    confirmed_quantity = Column(Integer)
    notes = Column(Text)
    
    # 關聯
    reservation = relationship("SupplyReservation", back_populates="reservation_items")
    supply_type_rel = relationship("SupplyType", back_populates="reservation_items")