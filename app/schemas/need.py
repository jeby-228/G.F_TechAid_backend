"""
需求管理相關的 Pydantic 模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.utils.constants import NeedType, NeedStatus


class LocationData(BaseModel):
    """地理位置資料模型"""
    address: str = Field(..., description="地址")
    coordinates: Optional[Dict[str, float]] = Field(None, description="GPS座標 {lat, lng}")
    details: Optional[str] = Field(None, description="位置詳細說明")


class ContactInfo(BaseModel):
    """聯絡資訊模型"""
    phone: Optional[str] = Field(None, description="聯絡電話")
    alternative_phone: Optional[str] = Field(None, description="備用電話")
    notes: Optional[str] = Field(None, description="聯絡備註")


class NeedRequirements(BaseModel):
    """需求詳細內容模型"""
    items: Optional[List[Dict[str, Any]]] = Field(None, description="物資清單")
    people_count: Optional[int] = Field(None, ge=1, description="需要協助的人數")
    special_needs: Optional[str] = Field(None, description="特殊需求說明")
    medical_conditions: Optional[str] = Field(None, description="醫療狀況")
    accessibility_needs: Optional[str] = Field(None, description="無障礙需求")


class NeedBase(BaseModel):
    """需求基礎模型"""
    title: str = Field(..., min_length=1, max_length=200, description="需求標題")
    description: str = Field(..., min_length=1, description="需求詳細描述")
    need_type: NeedType = Field(..., description="需求類型")
    location_data: LocationData = Field(..., description="地理位置資料")
    requirements: NeedRequirements = Field(..., description="具體需求內容")
    urgency_level: int = Field(1, ge=1, le=5, description="緊急程度 (1-5, 5最緊急)")
    contact_info: Optional[ContactInfo] = Field(None, description="聯絡資訊")


class NeedCreate(NeedBase):
    """需求建立模型"""
    pass


class NeedUpdate(BaseModel):
    """需求更新模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="需求標題")
    description: Optional[str] = Field(None, min_length=1, description="需求詳細描述")
    need_type: Optional[NeedType] = Field(None, description="需求類型")
    location_data: Optional[LocationData] = Field(None, description="地理位置資料")
    requirements: Optional[NeedRequirements] = Field(None, description="具體需求內容")
    urgency_level: Optional[int] = Field(None, ge=1, le=5, description="緊急程度")
    contact_info: Optional[ContactInfo] = Field(None, description="聯絡資訊")


class NeedStatusUpdate(BaseModel):
    """需求狀態更新模型"""
    status: NeedStatus = Field(..., description="新狀態")
    notes: Optional[str] = Field(None, description="狀態更新備註")


class NeedAssignment(BaseModel):
    """需求分配模型"""
    assigned_to: str = Field(..., description="分配給的用戶ID")
    task_id: Optional[str] = Field(None, description="關聯的任務ID")
    notes: Optional[str] = Field(None, description="分配備註")


class NeedInDB(NeedBase):
    """資料庫中的需求模型"""
    id: str = Field(..., description="需求 ID")
    reporter_id: str = Field(..., description="報告者 ID")
    status: NeedStatus = Field(..., description="需求狀態")
    assigned_to: Optional[str] = Field(None, description="分配給的用戶ID")
    assigned_at: Optional[datetime] = Field(None, description="分配時間")
    resolved_at: Optional[datetime] = Field(None, description="解決時間")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class NeedResponse(NeedInDB):
    """需求回應模型"""
    reporter_name: Optional[str] = Field(None, description="報告者姓名")
    reporter_phone: Optional[str] = Field(None, description="報告者電話")
    assignee_name: Optional[str] = Field(None, description="負責人姓名")
    assignment_count: int = Field(0, description="分配記錄數量")


class NeedListResponse(BaseModel):
    """需求列表回應模型"""
    needs: List[NeedResponse] = Field(..., description="需求列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


class NeedSearchQuery(BaseModel):
    """需求搜尋查詢模型"""
    title: Optional[str] = Field(None, description="標題搜尋")
    need_type: Optional[NeedType] = Field(None, description="需求類型篩選")
    status: Optional[NeedStatus] = Field(None, description="狀態篩選")
    urgency_level: Optional[int] = Field(None, ge=1, le=5, description="緊急程度篩選")
    reporter_id: Optional[str] = Field(None, description="報告者ID篩選")
    assigned_to: Optional[str] = Field(None, description="負責人ID篩選")
    location_radius: Optional[float] = Field(None, ge=0, description="位置搜尋半徑(公里)")
    center_lat: Optional[float] = Field(None, description="搜尋中心緯度")
    center_lng: Optional[float] = Field(None, description="搜尋中心經度")


class NeedAssignmentInDB(BaseModel):
    """需求分配記錄模型"""
    id: str = Field(..., description="分配記錄 ID")
    need_id: str = Field(..., description="需求 ID")
    task_id: Optional[str] = Field(None, description="任務 ID")
    user_id: str = Field(..., description="用戶 ID")
    assigned_at: datetime = Field(..., description="分配時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    notes: Optional[str] = Field(None, description="備註")
    status: str = Field(..., description="分配狀態")
    
    class Config:
        from_attributes = True


class NeedAssignmentResponse(NeedAssignmentInDB):
    """需求分配回應模型"""
    need_title: Optional[str] = Field(None, description="需求標題")
    task_title: Optional[str] = Field(None, description="任務標題")
    user_name: Optional[str] = Field(None, description="用戶姓名")


class NeedStatistics(BaseModel):
    """需求統計模型"""
    total_needs: int = Field(..., description="總需求數")
    needs_by_type: Dict[str, int] = Field(..., description="各類型需求數")
    needs_by_status: Dict[str, int] = Field(..., description="各狀態需求數")
    needs_by_urgency: Dict[str, int] = Field(..., description="各緊急程度需求數")
    open_needs: int = Field(..., description="待處理需求數")
    assigned_needs: int = Field(..., description="已分配需求數")
    resolved_needs: int = Field(..., description="已解決需求數")
    average_resolution_time: Optional[float] = Field(None, description="平均解決時間(小時)")


# 需求類型和狀態的顯示名稱映射
NEED_TYPE_DISPLAY = {
    NeedType.FOOD: "食物需求",
    NeedType.MEDICAL: "醫療需求", 
    NeedType.SHELTER: "住宿需求",
    NeedType.CLOTHING: "衣物需求",
    NeedType.RESCUE: "救援需求",
    NeedType.CLEANUP: "清理需求"
}

NEED_STATUS_DISPLAY = {
    NeedStatus.OPEN: "待處理",
    NeedStatus.ASSIGNED: "已分配",
    NeedStatus.IN_PROGRESS: "處理中",
    NeedStatus.RESOLVED: "已解決",
    NeedStatus.CLOSED: "已關閉"
}