# 資料模型模組

# 匯入所有模型以確保它們被 SQLAlchemy 註冊
from app.models.base import BaseModel
from app.models.user import UserRole, User, Organization
from app.models.task import TaskType, TaskStatus, Task, TaskClaim
from app.models.need import NeedType, NeedStatus, Need, NeedAssignment
from app.models.supply import (
    SupplyType, SupplyStation, InventoryItem, 
    ReservationStatus, SupplyReservation, ReservationItem
)
from app.models.system import Announcement, Notification, SystemLog, Shelter

# 匯出所有模型
__all__ = [
    "BaseModel",
    # User models
    "UserRole", "User", "Organization",
    # Task models
    "TaskType", "TaskStatus", "Task", "TaskClaim",
    # Need models
    "NeedType", "NeedStatus", "Need", "NeedAssignment",
    # Supply models
    "SupplyType", "SupplyStation", "InventoryItem",
    "ReservationStatus", "SupplyReservation", "ReservationItem",
    # System models
    "Announcement", "Notification", "SystemLog", "Shelter"
]