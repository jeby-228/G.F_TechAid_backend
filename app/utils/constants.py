"""
應用程式常數定義
"""
from enum import Enum

class UserRole(str, Enum):
    """用戶角色枚舉"""
    ADMIN = "admin"                    # 系統管理員
    VICTIM = "victim"                  # 受災戶
    OFFICIAL_ORG = "official_org"      # 正式志工組織
    UNOFFICIAL_ORG = "unofficial_org"  # 非正式志工組織
    SUPPLY_MANAGER = "supply_manager"  # 物資站點管理者
    VOLUNTEER = "volunteer"            # 一般志工

class TaskStatus(str, Enum):
    """任務狀態枚舉"""
    PENDING = "pending"        # 待審核（非正式組織）
    AVAILABLE = "available"    # 可認領
    CLAIMED = "claimed"        # 已認領
    IN_PROGRESS = "in_progress" # 執行中
    COMPLETED = "completed"    # 已完成
    CANCELLED = "cancelled"    # 已取消

class TaskType(str, Enum):
    """任務類型枚舉"""
    CLEANUP = "cleanup"              # 清理工作
    RESCUE = "rescue"                # 救援任務
    SUPPLY_DELIVERY = "supply_delivery" # 物資配送
    MEDICAL_AID = "medical_aid"      # 醫療協助
    SHELTER_SUPPORT = "shelter_support" # 避難所支援

class NeedStatus(str, Enum):
    """需求狀態枚舉"""
    OPEN = "open"           # 待處理
    ASSIGNED = "assigned"   # 已分配
    IN_PROGRESS = "in_progress" # 處理中
    RESOLVED = "resolved"   # 已解決
    CLOSED = "closed"       # 已關閉

class NeedType(str, Enum):
    """需求類型枚舉"""
    FOOD = "food"           # 食物需求
    MEDICAL = "medical"     # 醫療需求
    SHELTER = "shelter"     # 住宿需求
    CLOTHING = "clothing"   # 衣物需求
    RESCUE = "rescue"       # 救援需求
    CLEANUP = "cleanup"     # 清理需求

class SupplyType(str, Enum):
    """物資類型枚舉"""
    WATER = "water"                 # 飲用水
    RICE = "rice"                   # 白米
    INSTANT_NOODLES = "instant_noodles" # 泡麵
    BLANKET = "blanket"             # 毛毯
    FIRST_AID_KIT = "first_aid_kit" # 急救包
    FLASHLIGHT = "flashlight"       # 手電筒

class ReservationStatus(str, Enum):
    """預訂狀態枚舉"""
    PENDING = "pending"     # 待確認
    CONFIRMED = "confirmed" # 已確認
    PICKED_UP = "picked_up" # 已領取
    DELIVERED = "delivered" # 已配送
    CANCELLED = "cancelled" # 已取消

class NotificationType(str, Enum):
    """通知類型枚舉"""
    TASK = "task"           # 任務相關
    SUPPLY = "supply"       # 物資相關
    SYSTEM = "system"       # 系統通知
    EMERGENCY = "emergency" # 緊急通知

class AnnouncementType(str, Enum):
    """公告類型枚舉"""
    GENERAL = "general"         # 一般公告
    EMERGENCY = "emergency"     # 緊急公告
    MAINTENANCE = "maintenance" # 維護公告

# 權限定義
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "all": True
    },
    UserRole.VICTIM: {
        "create_need": True,
        "view_shelters": True,
        "view_supplies": True
    },
    UserRole.OFFICIAL_ORG: {
        "create_task": True,
        "claim_task": True,
        "manage_supplies": True,
        "view_all_data": True
    },
    UserRole.UNOFFICIAL_ORG: {
        "create_task": False,  # 需要審核
        "claim_task": True,
        "view_supplies": True
    },
    UserRole.SUPPLY_MANAGER: {
        "manage_supplies": True,
        "create_task": True,
        "view_supply_requests": True
    },
    UserRole.VOLUNTEER: {
        "claim_task": True,
        "view_supplies": True
    }
}

# 花蓮光復鄉地理範圍
GUANGFU_COORDINATES = {
    "center": {"lat": 23.5731, "lng": 121.4208},
    "bounds": {
        "north": 23.6500,
        "south": 23.4500,
        "east": 121.5500,
        "west": 121.3000
    }
}