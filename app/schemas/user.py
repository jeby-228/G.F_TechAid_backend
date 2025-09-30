"""
用戶管理相關的 Pydantic 模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
from app.utils.constants import UserRole


class UserBase(BaseModel):
    """用戶基礎模型"""
    email: EmailStr = Field(..., description="電子郵件地址")
    phone: Optional[str] = Field(None, max_length=20, description="手機號碼")
    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    role: UserRole = Field(..., description="用戶角色")


class UserCreate(UserBase):
    """用戶建立模型"""
    password: str = Field(..., min_length=6, max_length=50, description="密碼")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="額外個人資料")


class UserUpdate(BaseModel):
    """用戶更新模型"""
    phone: Optional[str] = Field(None, max_length=20, description="手機號碼")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="姓名")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="額外個人資料")


class UserInDB(UserBase):
    """資料庫中的用戶模型"""
    id: str = Field(..., description="用戶 ID")
    is_approved: bool = Field(..., description="是否已審核通過")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="額外個人資料")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class UserResponse(UserInDB):
    """用戶回應模型（不包含敏感資訊）"""
    pass


class UserListResponse(BaseModel):
    """用戶列表回應模型"""
    users: List[UserResponse] = Field(..., description="用戶列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


class UserRoleUpdate(BaseModel):
    """用戶角色更新模型（管理員專用）"""
    role: UserRole = Field(..., description="新角色")


class UserApprovalUpdate(BaseModel):
    """用戶審核狀態更新模型（管理員專用）"""
    is_approved: bool = Field(..., description="是否通過審核")
    notes: Optional[str] = Field(None, description="審核備註")


class UserPasswordReset(BaseModel):
    """用戶密碼重設模型（管理員專用）"""
    new_password: str = Field(..., min_length=6, max_length=50, description="新密碼")


class UserSearchQuery(BaseModel):
    """用戶搜尋查詢模型"""
    email: Optional[str] = Field(None, description="電子郵件搜尋")
    name: Optional[str] = Field(None, description="姓名搜尋")
    role: Optional[UserRole] = Field(None, description="角色篩選")
    is_approved: Optional[bool] = Field(None, description="審核狀態篩選")


# 組織相關模型
class OrganizationBase(BaseModel):
    """組織基礎模型"""
    organization_name: str = Field(..., max_length=200, description="組織名稱")
    organization_type: str = Field(..., description="組織類型")
    contact_person: Optional[str] = Field(None, max_length=100, description="聯絡人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="聯絡電話")
    address: Optional[str] = Field(None, description="地址")
    description: Optional[str] = Field(None, description="組織描述")


class OrganizationCreate(OrganizationBase):
    """組織建立模型"""
    user_id: str = Field(..., description="用戶 ID")


class OrganizationUpdate(BaseModel):
    """組織更新模型"""
    organization_name: Optional[str] = Field(None, max_length=200, description="組織名稱")
    contact_person: Optional[str] = Field(None, max_length=100, description="聯絡人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="聯絡電話")
    address: Optional[str] = Field(None, description="地址")
    description: Optional[str] = Field(None, description="組織描述")


class OrganizationInDB(OrganizationBase):
    """資料庫中的組織模型"""
    id: str = Field(..., description="組織 ID")
    user_id: str = Field(..., description="用戶 ID")
    approval_status: str = Field(..., description="審核狀態")
    approved_by: Optional[str] = Field(None, description="審核者 ID")
    approved_at: Optional[datetime] = Field(None, description="審核時間")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class OrganizationResponse(OrganizationInDB):
    """組織回應模型"""
    user_name: Optional[str] = Field(None, description="用戶姓名")
    user_email: Optional[str] = Field(None, description="用戶電子郵件")
    approver_name: Optional[str] = Field(None, description="審核者姓名")


class OrganizationListResponse(BaseModel):
    """組織列表回應模型"""
    organizations: List[OrganizationResponse] = Field(..., description="組織列表")
    total: int = Field(..., description="總數量")
    skip: int = Field(..., description="跳過數量")
    limit: int = Field(..., description="限制數量")


class OrganizationApprovalRequest(BaseModel):
    """組織審核請求模型"""
    approved: bool = Field(..., description="是否通過審核")
    notes: Optional[str] = Field(None, description="審核備註")


class OrganizationSearchQuery(BaseModel):
    """組織搜尋查詢模型"""
    organization_name: Optional[str] = Field(None, description="組織名稱搜尋")
    organization_type: Optional[str] = Field(None, description="組織類型篩選")
    approval_status: Optional[str] = Field(None, description="審核狀態篩選")


# 用戶統計模型
class UserStatistics(BaseModel):
    """用戶統計模型"""
    total_users: int = Field(..., description="總用戶數")
    users_by_role: Dict[str, int] = Field(..., description="各角色用戶數")
    approved_users: int = Field(..., description="已審核用戶數")
    pending_approvals: int = Field(..., description="待審核用戶數")
    active_organizations: int = Field(..., description="活躍組織數")
    pending_organizations: int = Field(..., description="待審核組織數")