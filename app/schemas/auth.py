"""
身分驗證相關的 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from app.utils.constants import UserRole


class UserRegistration(BaseModel):
    """用戶註冊請求模型"""
    email: EmailStr = Field(..., description="電子郵件地址")
    phone: Optional[str] = Field(None, max_length=20, description="手機號碼")
    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    password: str = Field(..., min_length=6, max_length=50, description="密碼")
    role: UserRole = Field(..., description="用戶角色")
    
    # 組織相關資訊（當角色為組織負責人時需要）
    organization_name: Optional[str] = Field(None, max_length=200, description="組織名稱")
    organization_type: Optional[str] = Field(None, description="組織類型")
    contact_person: Optional[str] = Field(None, max_length=100, description="聯絡人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="聯絡電話")
    address: Optional[str] = Field(None, description="地址")
    description: Optional[str] = Field(None, description="組織描述")
    
    @validator('organization_name')
    def validate_organization_name(cls, v, values):
        """驗證組織名稱（組織負責人必填）"""
        role = values.get('role')
        if role in [UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG] and not v:
            raise ValueError('組織負責人必須提供組織名稱')
        return v
    
    @validator('organization_type')
    def validate_organization_type(cls, v, values):
        """驗證組織類型"""
        role = values.get('role')
        if role in [UserRole.OFFICIAL_ORG, UserRole.UNOFFICIAL_ORG]:
            if role == UserRole.OFFICIAL_ORG and v != 'official':
                return 'official'
            elif role == UserRole.UNOFFICIAL_ORG and v != 'unofficial':
                return 'unofficial'
        return v


class UserLogin(BaseModel):
    """用戶登入請求模型"""
    email: EmailStr = Field(..., description="電子郵件地址")
    password: str = Field(..., description="密碼")


class Token(BaseModel):
    """JWT Token 回應模型"""
    access_token: str = Field(..., description="存取權杖")
    token_type: str = Field(default="bearer", description="權杖類型")
    expires_in: int = Field(..., description="權杖有效期（秒）")


class TokenData(BaseModel):
    """JWT Token 資料模型"""
    user_id: Optional[str] = None


class UserProfile(BaseModel):
    """用戶個人資料模型"""
    id: str = Field(..., description="用戶 ID")
    email: str = Field(..., description="電子郵件地址")
    phone: Optional[str] = Field(None, description="手機號碼")
    name: str = Field(..., description="姓名")
    role: UserRole = Field(..., description="用戶角色")
    is_approved: bool = Field(..., description="是否已審核通過")
    created_at: str = Field(..., description="建立時間")
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """用戶個人資料更新模型"""
    phone: Optional[str] = Field(None, max_length=20, description="手機號碼")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="姓名")


class PasswordChange(BaseModel):
    """密碼變更模型"""
    current_password: str = Field(..., description="目前密碼")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密碼")


class OrganizationApproval(BaseModel):
    """組織審核模型"""
    organization_id: str = Field(..., description="組織 ID")
    approved: bool = Field(..., description="是否通過審核")
    notes: Optional[str] = Field(None, description="審核備註")