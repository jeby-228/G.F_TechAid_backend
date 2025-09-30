"""
任務管理相關的 Pydantic 模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.utils.constants import TaskType, TaskStatus, UserRole


class LocationData(BaseModel):
    """地理位置資料模型"""
    address: str = Field(..., description="地址")
    coordinates: Dict[str, float] = Field(..., description="座標 {lat, lng}")
    details: Optional[str] = Field(None, description="位置詳細說明")
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        if not isinstance(v, dict) or 'lat' not in v or 'lng' not in v:
            raise ValueError('座標必須包含 lat 和 lng')
        if not (-90 <= v['lat'] <= 90):
            raise ValueError('緯度必須在 -90 到 90 之間')
        if not (-180 <= v['lng'] <= 180):
            raise ValueError('經度必須在 -180 到 180 之間')
        return v


class TaskBase(BaseModel):
    """任務基礎模型"""
    title: str = Field(..., min_length=1, max_length=200, description="任務標題")
    description: str = Field(..., min_length=1, description="任務描述")
    task_type: TaskType = Field(..., description="任務類型")
    location_data: LocationData = Field(..., description="任務地點資訊")
    required_volunteers: int = Field(1, ge=1, le=100, description="所需志工人數")
    required_skills: Optional[List[str]] = Field(None, description="所需技能或資格")
    deadline: Optional[datetime] = Field(None, description="截止時間")
    priority_level: int = Field(1, ge=1, le=5, description="優先級 (1-5)")


class TaskCreate(TaskBase):
    """任務建立模型"""
    pass


class TaskUpdate(BaseModel):
    """任務更新模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="任務標題")
    description: Optional[str] = Field(None, min_length=1, description="任務描述")
    task_type: Optional[TaskType] = Field(None, description="任務類型")
    location_data: Optional[LocationData] = Field(None, description="任務地點資訊")
    required_volunteers: Optional[int] = Field(None, ge=1, le=100, description="所需志工人數")
    required_skills: Optional[List[str]] = Field(None, description="所需技能或資格")
    deadline: Optional[datetime] = Field(None, description="截止時間")
    priority_level: Optional[int] = Field(None, ge=1, le=5, description="優先級 (1-5)")


class TaskInDB(TaskBase):
    """資料庫中的任務模型"""
    id: str = Field(..., description="任務 ID")
    creator_id: str = Field(..., description="建立者 ID")
    status: TaskStatus = Field(..., description="任務狀態")
    approval_status: str = Field(..., description="審核狀態")
    approved_by: Optional[str] = Field(None, description="審核者 ID")
    approved_at: Optional[datetime] = Field(None, description="審核時間")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class TaskResponse(TaskInDB):
    """任務回應模型"""
    creator_name: Optional[str] = Field(None, description="建立者姓名")
    creator_role: Optional[UserRole] = Field(None, description="建立者角色")
    approver_name: Optional[str] = Field(None, description="審核者姓名")
    claimed_count: int = Field(0, description="已認領人數")
    can_claim: bool = Field(False, description="當前用戶是否可認領")
    can_edit: bool = Field(False, description="當前用戶是否可編輯")


class TaskListResponse(BaseModel):
    """任務列表回應模型"""
    tasks: List[TaskResponse] = Field(..., description="任務列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


class TaskSearchQuery(BaseModel):
    """任務搜尋查詢模型"""
    title: Optional[str] = Field(None, description="標題搜尋")
    task_type: Optional[TaskType] = Field(None, description="任務類型篩選")
    status: Optional[TaskStatus] = Field(None, description="狀態篩選")
    creator_id: Optional[str] = Field(None, description="建立者篩選")
    priority_level: Optional[int] = Field(None, ge=1, le=5, description="優先級篩選")
    location_radius: Optional[float] = Field(None, ge=0, description="位置半徑篩選(公里)")
    center_lat: Optional[float] = Field(None, description="中心緯度")
    center_lng: Optional[float] = Field(None, description="中心經度")


class TaskApprovalRequest(BaseModel):
    """任務審核請求模型"""
    approved: bool = Field(..., description="是否通過審核")
    notes: Optional[str] = Field(None, description="審核備註")


class TaskStatusUpdate(BaseModel):
    """任務狀態更新模型"""
    status: TaskStatus = Field(..., description="新狀態")
    notes: Optional[str] = Field(None, description="狀態更新備註")


# 任務認領相關模型
class TaskClaimBase(BaseModel):
    """任務認領基礎模型"""
    notes: Optional[str] = Field(None, description="認領備註")


class TaskClaimCreate(TaskClaimBase):
    """任務認領建立模型"""
    task_id: str = Field(..., description="任務 ID")


class TaskClaimUpdate(BaseModel):
    """任務認領更新模型"""
    status: str = Field(..., description="認領狀態")
    notes: Optional[str] = Field(None, description="更新備註")
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")


class TaskClaimInDB(TaskClaimBase):
    """資料庫中的任務認領模型"""
    id: str = Field(..., description="認領 ID")
    task_id: str = Field(..., description="任務 ID")
    user_id: str = Field(..., description="認領者 ID")
    status: str = Field(..., description="認領狀態")
    claimed_at: datetime = Field(..., description="認領時間")
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    
    class Config:
        from_attributes = True


class TaskClaimResponse(TaskClaimInDB):
    """任務認領回應模型"""
    task_title: Optional[str] = Field(None, description="任務標題")
    task_type: Optional[TaskType] = Field(None, description="任務類型")
    user_name: Optional[str] = Field(None, description="認領者姓名")
    user_role: Optional[UserRole] = Field(None, description="認領者角色")


class TaskClaimListResponse(BaseModel):
    """任務認領列表回應模型"""
    claims: List[TaskClaimResponse] = Field(..., description="認領列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


class TaskStatistics(BaseModel):
    """任務統計模型"""
    total_tasks: int = Field(..., description="總任務數")
    tasks_by_status: Dict[str, int] = Field(..., description="各狀態任務數")
    tasks_by_type: Dict[str, int] = Field(..., description="各類型任務數")
    pending_approval: int = Field(..., description="待審核任務數")
    available_tasks: int = Field(..., description="可認領任務數")
    completed_tasks: int = Field(..., description="已完成任務數")
    active_volunteers: int = Field(..., description="活躍志工數")


class TaskActivityLog(BaseModel):
    """任務活動日誌模型"""
    timestamp: datetime = Field(..., description="時間戳")
    action: str = Field(..., description="動作類型")
    description: str = Field(..., description="動作描述")
    user_id: Optional[str] = Field(None, description="操作用戶ID")
    user_name: Optional[str] = Field(None, description="操作用戶姓名")
    notes: Optional[str] = Field(None, description="備註")


class TaskConflictCheck(BaseModel):
    """任務衝突檢查模型"""
    has_conflicts: bool = Field(..., description="是否有衝突")
    conflicts: List[str] = Field(..., description="衝突列表")


class TaskHistoryQuery(BaseModel):
    """任務歷史查詢模型"""
    status_filter: Optional[str] = Field(None, description="狀態篩選")
    skip: int = Field(0, ge=0, description="跳過數量")
    limit: int = Field(100, ge=1, le=1000, description="限制數量")