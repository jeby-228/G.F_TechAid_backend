"""
用戶管理相關的 API 端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    UserRoleUpdate, UserApprovalUpdate, UserPasswordReset,
    UserSearchQuery, UserStatistics,
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationListResponse, OrganizationApprovalRequest,
    OrganizationSearchQuery
)
from app.crud.user import user_crud
from app.middleware.auth import get_current_user, AdminOnly
from app.schemas.auth import UserProfile
from app.utils.constants import UserRole
from app.services.notification_service import notification_service

router = APIRouter()


# 用戶管理端點
@router.get("/", response_model=UserListResponse, summary="取得用戶列表")
async def get_users(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    email: Optional[str] = Query(None, description="電子郵件搜尋"),
    name: Optional[str] = Query(None, description="姓名搜尋"),
    role: Optional[UserRole] = Query(None, description="角色篩選"),
    is_approved: Optional[bool] = Query(None, description="審核狀態篩選"),
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得用戶列表（僅管理員可用）
    
    支援搜尋和篩選功能：
    - **email**: 電子郵件模糊搜尋
    - **name**: 姓名模糊搜尋
    - **role**: 角色精確篩選
    - **is_approved**: 審核狀態篩選
    """
    search_query = UserSearchQuery(
        email=email,
        name=name,
        role=role,
        is_approved=is_approved
    )
    
    users = user_crud.get_multi(db, skip=skip, limit=limit, search_query=search_query)
    total = user_crud.count(db, search_query=search_query)
    
    user_responses = []
    for user in users:
        user_responses.append(UserResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            name=user.name,
            role=UserRole(user.role),
            is_approved=user.is_approved,
            profile_data=user.profile_data,
            created_at=user.created_at,
            updated_at=user.updated_at
        ))
    
    return UserListResponse(
        users=user_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/statistics", response_model=UserStatistics, summary="取得用戶統計資料")
async def get_user_statistics(
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得用戶統計資料（僅管理員可用）
    
    包含：
    - 總用戶數
    - 各角色用戶數
    - 已審核/待審核用戶數
    - 活躍/待審核組織數
    """
    return user_crud.get_statistics(db)


@router.get("/{user_id}", response_model=UserResponse, summary="取得特定用戶資訊")
async def get_user(
    user_id: str,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得特定用戶的詳細資訊（僅管理員可用）
    """
    user = user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        name=user.name,
        role=UserRole(user.role),
        is_approved=user.is_approved,
        profile_data=user.profile_data,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/", response_model=UserResponse, summary="建立新用戶")
async def create_user(
    user_data: UserCreate,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    建立新用戶（僅管理員可用）
    """
    try:
        user = user_crud.create(db, user_data)
        return UserResponse(
            id=str(user.id),
            email=user.email,
            phone=user.phone,
            name=user.name,
            role=UserRole(user.role),
            is_approved=user.is_approved,
            profile_data=user.profile_data,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserResponse, summary="更新用戶資料")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    更新用戶資料（僅管理員可用）
    """
    user = user_crud.update(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        name=user.name,
        role=UserRole(user.role),
        is_approved=user.is_approved,
        profile_data=user.profile_data,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.delete("/{user_id}", summary="刪除用戶")
async def delete_user(
    user_id: str,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    刪除用戶（僅管理員可用）
    
    注意：這將永久刪除用戶及其相關資料
    """
    success = user_crud.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return {"message": "用戶刪除成功"}


@router.put("/{user_id}/role", response_model=UserResponse, summary="更新用戶角色")
async def update_user_role(
    user_id: str,
    role_data: UserRoleUpdate,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    更新用戶角色（僅管理員可用）
    """
    user = user_crud.update_role(db, user_id, role_data.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    # 發送角色變更通知
    await notification_service.send_role_change_notification(
        db, user_id, role_data.role.value
    )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        name=user.name,
        role=UserRole(user.role),
        is_approved=user.is_approved,
        profile_data=user.profile_data,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/{user_id}/approval", response_model=UserResponse, summary="更新用戶審核狀態")
async def update_user_approval(
    user_id: str,
    approval_data: UserApprovalUpdate,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    更新用戶審核狀態（僅管理員可用）
    """
    user = user_crud.update_approval_status(db, user_id, approval_data.is_approved)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    # 發送審核結果通知
    await notification_service.send_approval_notification(
        db, user_id, approval_data.is_approved, approval_data.notes
    )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone=user.phone,
        name=user.name,
        role=UserRole(user.role),
        is_approved=user.is_approved,
        profile_data=user.profile_data,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.post("/{user_id}/reset-password", summary="重設用戶密碼")
async def reset_user_password(
    user_id: str,
    password_data: UserPasswordReset,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    重設用戶密碼（僅管理員可用）
    """
    success = user_crud.reset_password(db, user_id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    # 發送密碼重設通知
    await notification_service.send_password_reset_notification(db, user_id)
    
    return {"message": "密碼重設成功"}


# 組織管理端點
@router.get("/organizations/", response_model=OrganizationListResponse, summary="取得組織列表")
async def get_organizations(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    organization_name: Optional[str] = Query(None, description="組織名稱搜尋"),
    organization_type: Optional[str] = Query(None, description="組織類型篩選"),
    approval_status: Optional[str] = Query(None, description="審核狀態篩選"),
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得組織列表（僅管理員可用）
    
    支援搜尋和篩選功能：
    - **organization_name**: 組織名稱模糊搜尋
    - **organization_type**: 組織類型篩選
    - **approval_status**: 審核狀態篩選
    """
    search_query = OrganizationSearchQuery(
        organization_name=organization_name,
        organization_type=organization_type,
        approval_status=approval_status
    )
    
    organizations = user_crud.get_organizations(db, skip=skip, limit=limit, search_query=search_query)
    total = user_crud.count_organizations(db, search_query=search_query)
    
    org_responses = []
    for org in organizations:
        org_responses.append(OrganizationResponse(
            id=str(org.id),
            user_id=str(org.user_id),
            organization_name=org.organization_name,
            organization_type=org.organization_type,
            contact_person=org.contact_person,
            contact_phone=org.contact_phone,
            address=org.address,
            description=org.description,
            approval_status=org.approval_status,
            approved_by=str(org.approved_by) if org.approved_by else None,
            approved_at=org.approved_at,
            created_at=org.created_at,
            updated_at=org.updated_at,
            user_name=org.user.name if org.user else None,
            user_email=org.user.email if org.user else None,
            approver_name=org.approver.name if org.approver else None
        ))
    
    return OrganizationListResponse(
        organizations=org_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/organizations/pending", response_model=List[OrganizationResponse], summary="取得待審核組織列表")
async def get_pending_organizations(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得待審核的組織列表（僅管理員可用）
    """
    organizations = user_crud.get_pending_organizations(db, skip=skip, limit=limit)
    
    org_responses = []
    for org in organizations:
        org_responses.append(OrganizationResponse(
            id=str(org.id),
            user_id=str(org.user_id),
            organization_name=org.organization_name,
            organization_type=org.organization_type,
            contact_person=org.contact_person,
            contact_phone=org.contact_phone,
            address=org.address,
            description=org.description,
            approval_status=org.approval_status,
            approved_by=str(org.approved_by) if org.approved_by else None,
            approved_at=org.approved_at,
            created_at=org.created_at,
            updated_at=org.updated_at,
            user_name=org.user.name if org.user else None,
            user_email=org.user.email if org.user else None,
            approver_name=org.approver.name if org.approver else None
        ))
    
    return org_responses


@router.get("/organizations/{org_id}", response_model=OrganizationResponse, summary="取得特定組織資訊")
async def get_organization(
    org_id: str,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得特定組織的詳細資訊（僅管理員可用）
    """
    org = user_crud.get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="組織不存在"
        )
    
    # 載入關聯資料
    user = user_crud.get_by_id(db, str(org.user_id))
    approver = user_crud.get_by_id(db, str(org.approved_by)) if org.approved_by else None
    
    return OrganizationResponse(
        id=str(org.id),
        user_id=str(org.user_id),
        organization_name=org.organization_name,
        organization_type=org.organization_type,
        contact_person=org.contact_person,
        contact_phone=org.contact_phone,
        address=org.address,
        description=org.description,
        approval_status=org.approval_status,
        approved_by=str(org.approved_by) if org.approved_by else None,
        approved_at=org.approved_at,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_name=user.name if user else None,
        user_email=user.email if user else None,
        approver_name=approver.name if approver else None
    )


@router.post("/organizations/", response_model=OrganizationResponse, summary="建立新組織")
async def create_organization(
    org_data: OrganizationCreate,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    建立新組織（僅管理員可用）
    """
    try:
        org = user_crud.create_organization(db, org_data)
        user = user_crud.get_by_id(db, str(org.user_id))
        
        return OrganizationResponse(
            id=str(org.id),
            user_id=str(org.user_id),
            organization_name=org.organization_name,
            organization_type=org.organization_type,
            contact_person=org.contact_person,
            contact_phone=org.contact_phone,
            address=org.address,
            description=org.description,
            approval_status=org.approval_status,
            approved_by=str(org.approved_by) if org.approved_by else None,
            approved_at=org.approved_at,
            created_at=org.created_at,
            updated_at=org.updated_at,
            user_name=user.name if user else None,
            user_email=user.email if user else None,
            approver_name=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/organizations/{org_id}", response_model=OrganizationResponse, summary="更新組織資料")
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    更新組織資料（僅管理員可用）
    """
    org = user_crud.update_organization(db, org_id, org_data)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="組織不存在"
        )
    
    # 載入關聯資料
    user = user_crud.get_by_id(db, str(org.user_id))
    approver = user_crud.get_by_id(db, str(org.approved_by)) if org.approved_by else None
    
    return OrganizationResponse(
        id=str(org.id),
        user_id=str(org.user_id),
        organization_name=org.organization_name,
        organization_type=org.organization_type,
        contact_person=org.contact_person,
        contact_phone=org.contact_phone,
        address=org.address,
        description=org.description,
        approval_status=org.approval_status,
        approved_by=str(org.approved_by) if org.approved_by else None,
        approved_at=org.approved_at,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_name=user.name if user else None,
        user_email=user.email if user else None,
        approver_name=approver.name if approver else None
    )


@router.post("/organizations/{org_id}/approve", response_model=OrganizationResponse, summary="審核組織")
async def approve_organization(
    org_id: str,
    approval_data: OrganizationApprovalRequest,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    審核組織申請（僅管理員可用）
    """
    org = user_crud.approve_organization(db, org_id, current_user.id, approval_data.approved)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="組織不存在"
        )
    
    # 發送審核結果通知
    await notification_service.send_organization_approval_notification(
        db, str(org.user_id), approval_data.approved, approval_data.notes
    )
    
    # 載入關聯資料
    user = user_crud.get_by_id(db, str(org.user_id))
    approver = user_crud.get_by_id(db, current_user.id)
    
    return OrganizationResponse(
        id=str(org.id),
        user_id=str(org.user_id),
        organization_name=org.organization_name,
        organization_type=org.organization_type,
        contact_person=org.contact_person,
        contact_phone=org.contact_phone,
        address=org.address,
        description=org.description,
        approval_status=org.approval_status,
        approved_by=str(org.approved_by) if org.approved_by else None,
        approved_at=org.approved_at,
        created_at=org.created_at,
        updated_at=org.updated_at,
        user_name=user.name if user else None,
        user_email=user.email if user else None,
        approver_name=approver.name if approver else None
    )


@router.delete("/organizations/{org_id}", summary="刪除組織")
async def delete_organization(
    org_id: str,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    刪除組織（僅管理員可用）
    
    注意：這將永久刪除組織資料
    """
    success = user_crud.delete_organization(db, org_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="組織不存在"
        )
    
    return {"message": "組織刪除成功"}