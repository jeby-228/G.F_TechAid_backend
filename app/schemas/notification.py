"""
通知相關的 Pydantic 模型
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """通知基礎模型"""
    title: str = Field(..., description="通知標題")
    message: str = Field(..., description="通知內容")
    notification_type: str = Field(..., description="通知類型")


class NotificationCreate(NotificationBase):
    """建立通知的請求模型"""
    user_id: str = Field(..., description="接收通知的用戶 ID")
    related_id: Optional[str] = Field(None, description="關聯的資源 ID")


class NotificationResponse(NotificationBase):
    """通知回應模型"""
    id: str = Field(..., description="通知 ID")
    related_id: Optional[str] = Field(None, description="關聯的資源 ID")
    is_read: bool = Field(..., description="是否已讀")
    created_at: datetime = Field(..., description="建立時間")
    read_at: Optional[datetime] = Field(None, description="已讀時間")
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表回應模型"""
    notifications: List[NotificationResponse] = Field(..., description="通知列表")
    total_count: int = Field(..., description="總通知數量")
    unread_count: int = Field(..., description="未讀通知數量")
    skip: int = Field(..., description="跳過的數量")
    limit: int = Field(..., description="限制數量")


class NotificationStatsResponse(BaseModel):
    """通知統計回應模型"""
    unread_count: int = Field(..., description="未讀通知數量")
    total_count: int = Field(..., description="總通知數量")


class NotificationMarkReadRequest(BaseModel):
    """標記通知已讀的請求模型"""
    notification_ids: List[str] = Field(..., description="要標記為已讀的通知 ID 列表")


class BulkNotificationCreate(BaseModel):
    """批量建立通知的請求模型"""
    user_ids: List[str] = Field(..., description="接收通知的用戶 ID 列表")
    title: str = Field(..., description="通知標題")
    message: str = Field(..., description="通知內容")
    notification_type: str = Field(..., description="通知類型")
    related_id: Optional[str] = Field(None, description="關聯的資源 ID")
    send_email: bool = Field(False, description="是否發送 Email")
    send_sms: bool = Field(False, description="是否發送簡訊")


class WebSocketMessage(BaseModel):
    """WebSocket 訊息模型"""
    type: str = Field(..., description="訊息類型")
    data: dict = Field(..., description="訊息資料")


class NotificationPreferences(BaseModel):
    """通知偏好設定模型"""
    email_enabled: bool = Field(True, description="是否啟用 Email 通知")
    sms_enabled: bool = Field(True, description="是否啟用簡訊通知")
    push_enabled: bool = Field(True, description="是否啟用推播通知")
    task_notifications: bool = Field(True, description="是否接收任務通知")
    supply_notifications: bool = Field(True, description="是否接收物資通知")
    emergency_notifications: bool = Field(True, description="是否接收緊急通知")