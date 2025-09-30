"""
公告相關的 Pydantic 模型
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.utils.constants import AnnouncementType, UserRole


class AnnouncementBase(BaseModel):
    """公告基礎模型"""
    title: str = Field(..., min_length=1, max_length=200, description="公告標題")
    content: str = Field(..., min_length=1, description="公告內容")
    announcement_type: AnnouncementType = Field(AnnouncementType.GENERAL, description="公告類型")
    priority_level: int = Field(1, ge=1, le=5, description="優先級 (1-5)")


class AnnouncementCreate(AnnouncementBase):
    """建立公告的請求模型"""
    target_roles: Optional[List[UserRole]] = Field(None, description="目標用戶角色")
    expires_at: Optional[datetime] = Field(None, description="過期時間")


class AnnouncementUpdate(BaseModel):
    """更新公告的請求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="公告標題")
    content: Optional[str] = Field(None, min_length=1, description="公告內容")
    announcement_type: Optional[AnnouncementType] = Field(None, description="公告類型")
    priority_level: Optional[int] = Field(None, ge=1, le=5, description="優先級 (1-5)")
    target_roles: Optional[List[UserRole]] = Field(None, description="目標用戶角色")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    is_active: Optional[bool] = Field(None, description="是否啟用")


class AnnouncementResponse(AnnouncementBase):
    """公告回應模型"""
    id: str = Field(..., description="公告 ID")
    target_roles: Optional[List[str]] = Field(None, description="目標用戶角色")
    is_active: bool = Field(..., description="是否啟用")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    created_by: str = Field(..., description="創建者 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    # 創建者資訊
    creator_name: Optional[str] = Field(None, description="創建者姓名")
    
    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    """公告列表回應模型"""
    announcements: List[AnnouncementResponse] = Field(..., description="公告列表")
    total_count: int = Field(..., description="總公告數量")
    skip: int = Field(..., description="跳過的數量")
    limit: int = Field(..., description="限制數量")


class EmergencyAnnouncementCreate(BaseModel):
    """緊急公告建立請求模型"""
    title: str = Field(..., min_length=1, max_length=200, description="緊急公告標題")
    content: str = Field(..., min_length=1, description="緊急公告內容")
    target_roles: Optional[List[UserRole]] = Field(None, description="目標用戶角色")
    send_notifications: bool = Field(True, description="是否發送推播通知")


class AnnouncementStatsResponse(BaseModel):
    """公告統計回應模型"""
    total_count: int = Field(..., description="總公告數量")
    active_count: int = Field(..., description="活躍公告數量")
    emergency_count: int = Field(..., description="緊急公告數量")
    expired_count: int = Field(..., description="已過期公告數量")


class AnnouncementFilterParams(BaseModel):
    """公告過濾參數"""
    announcement_type: Optional[AnnouncementType] = Field(None, description="公告類型")
    active_only: bool = Field(True, description="只顯示活躍公告")
    skip: int = Field(0, ge=0, description="跳過數量")
    limit: int = Field(50, ge=1, le=100, description="限制數量")


class PublicAnnouncementResponse(BaseModel):
    """公開公告回應模型（不包含敏感資訊）"""
    id: str = Field(..., description="公告 ID")
    title: str = Field(..., description="公告標題")
    content: str = Field(..., description="公告內容")
    announcement_type: str = Field(..., description="公告類型")
    priority_level: int = Field(..., description="優先級")
    created_at: datetime = Field(..., description="建立時間")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    
    class Config:
        from_attributes = True