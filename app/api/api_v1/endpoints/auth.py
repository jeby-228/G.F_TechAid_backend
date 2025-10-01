"""
身分驗證相關的 API 端點
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import (
    UserRegistration, UserLogin, Token, UserProfile, 
    UserProfileUpdate, PasswordChange, OrganizationApproval
)
from app.services.auth_service import auth_service
from app.crud.user import user_crud
from app.middleware.auth import get_current_user, get_current_user_id, AdminOnly
from app.models.user import Organization
from app.utils.constants import UserRole

router = APIRouter()


@router.post("/register", response_model=Dict[str, Any], summary="用戶註冊")
async def register(
    user_data: UserRegistration,
    db: Session = Depends(get_db)
):
    """
    用戶註冊端點
    
    - **email**: 電子郵件地址（必填）
    - **phone**: 手機號碼（選填）
    - **name**: 姓名（必填）
    - **password**: 密碼（必填，至少6個字元）
    - **role**: 用戶角色（必填）
    - **organization_name**: 組織名稱（組織負責人必填）
    - **organization_type**: 組織類型（自動根據角色設定）
    - **contact_person**: 聯絡人（選填）
    - **contact_phone**: 聯絡電話（選填）
    - **address**: 地址（選填）
    - **description**: 組織描述（選填）
    
    回傳用戶資訊、JWT token 和註冊訊息
    """
    return auth_service.register_user(db, user_data)


@router.post("/login", response_model=Dict[str, Any], summary="用戶登入")
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    用戶登入端點
    
    - **email**: 電子郵件地址
    - **password**: 密碼
    
    回傳用戶資訊和 JWT token
    """
    return auth_service.login_user(db, login_data)


@router.get("/me", response_model=UserProfile, summary="取得當前用戶資訊")
async def get_current_user_info(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    取得當前登入用戶的個人資訊
    
    需要有效的 JWT token
    """
    return current_user


@router.put("/me", response_model=UserProfile, summary="更新個人資料")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新當前用戶的個人資料
    
    - **phone**: 手機號碼（選填）
    - **name**: 姓名（選填）
    """
    updated_user = user_crud.update_profile(db, current_user.id, profile_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return auth_service._user_to_profile(updated_user)


@router.post("/change-password", summary="變更密碼")
async def change_password(
    password_data: PasswordChange,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    變更當前用戶的密碼
    
    - **current_password**: 目前密碼
    - **new_password**: 新密碼（至少6個字元）
    """
    success = user_crud.change_password(
        db, 
        current_user.id, 
        password_data.current_password, 
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="目前密碼錯誤"
        )
    
    return {"message": "密碼變更成功"}


@router.get("/permissions", summary="取得當前用戶權限")
async def get_user_permissions(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    取得當前用戶的權限列表
    """
    permissions = auth_service.get_user_permissions(UserRole(current_user.role))
    return {
        "role": current_user.role,
        "permissions": permissions
    }


# 管理員專用端點
@router.get("/admin/pending-organizations", summary="取得待審核組織列表")
async def get_pending_organizations(
    skip: int = 0,
    limit: int = 100,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得待審核的組織列表（僅管理員可用）
    
    - **skip**: 跳過的記錄數（分頁用）
    - **limit**: 每頁記錄數（分頁用）
    """
    organizations = user_crud.get_pending_organizations(db, skip, limit)
    
    result = []
    for org in organizations:
        user = user_crud.get_by_id(db, str(org.user_id))
        result.append({
            "id": str(org.id),
            "user_id": str(org.user_id),
            "user_name": user.name if user else "未知",
            "user_email": user.email if user else "未知",
            "organization_name": org.organization_name,
            "organization_type": org.organization_type,
            "contact_person": org.contact_person,
            "contact_phone": org.contact_phone,
            "address": org.address,
            "description": org.description,
            "created_at": org.created_at.isoformat() if org.created_at else ""
        })
    
    return result


@router.post("/admin/approve-organization", summary="審核組織")
async def approve_organization(
    approval_data: OrganizationApproval,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    審核組織申請（僅管理員可用）
    
    - **organization_id**: 組織 ID
    - **approved**: 是否通過審核
    - **notes**: 審核備註（選填）
    """
    organization = user_crud.approve_organization(
        db, 
        approval_data.organization_id, 
        current_user.id, 
        approval_data.approved
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="組織不存在"
        )
    
    status_text = "通過" if approval_data.approved else "拒絕"
    return {
        "message": f"組織審核{status_text}成功",
        "organization_id": str(organization.id),
        "approval_status": organization.approval_status
    }


@router.get("/admin/users", summary="取得用戶列表")
async def get_users(
    role: UserRole = None,
    skip: int = 0,
    limit: int = 100,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得用戶列表（僅管理員可用）
    
    - **role**: 篩選特定角色的用戶（選填）
    - **skip**: 跳過的記錄數（分頁用）
    - **limit**: 每頁記錄數（分頁用）
    """
    if role:
        users = user_crud.get_users_by_role(db, role, skip, limit)
    else:
        # 如果沒有指定角色，取得所有用戶
        users = db.query(user_crud.model).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        result.append({
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_approved": user.is_approved,
            "created_at": user.created_at.isoformat() if user.created_at else ""
        })
    
    return result