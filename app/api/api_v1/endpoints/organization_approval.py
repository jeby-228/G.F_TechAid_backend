"""
組織審核相關的 API 端點
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import (
    OrganizationApprovalRequest, OrganizationResponse,
    OrganizationUpdate
)
from app.services.organization_service import organization_service
from app.middleware.auth import get_current_user, AdminOnly
from app.schemas.auth import UserProfile
from app.utils.constants import UserRole

router = APIRouter()


@router.post("/submit", response_model=OrganizationResponse, summary="提交組織審核申請")
async def submit_organization_application(
    organization_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交組織審核申請（非正式組織專用）
    
    - **organization_name**: 組織名稱（必填）
    - **contact_person**: 聯絡人（選填）
    - **contact_phone**: 聯絡電話（選填）
    - **address**: 地址（選填）
    - **description**: 組織描述（選填）
    """
    # 檢查用戶角色
    if current_user.role != UserRole.UNOFFICIAL_ORG.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有非正式組織可以提交審核申請"
        )
    
    try:
        organization = await organization_service.submit_organization_for_approval(
            db, current_user.id, organization_data
        )
        
        return OrganizationResponse(
            id=str(organization.id),
            user_id=str(organization.user_id),
            organization_name=organization.organization_name,
            organization_type=organization.organization_type,
            contact_person=organization.contact_person,
            contact_phone=organization.contact_phone,
            address=organization.address,
            description=organization.description,
            approval_status=organization.approval_status,
            approved_by=str(organization.approved_by) if organization.approved_by else None,
            approved_at=organization.approved_at,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            user_name=current_user.name,
            user_email=current_user.email,
            approver_name=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/pending", summary="取得待審核組織列表")
async def get_pending_applications(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得待審核的組織申請列表（僅管理員可用）
    """
    organizations = await organization_service.get_pending_applications(db, skip, limit)
    
    from app.crud.user import user_crud
    
    org_responses = []
    for org in organizations:
        user = user_crud.get_by_id(db, str(org.user_id))
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
            user_name=user.name if user else None,
            user_email=user.email if user else None,
            approver_name=None
        ))
    
    return org_responses


@router.post("/{organization_id}/approve", response_model=OrganizationResponse, summary="審核組織申請")
async def approve_organization_application(
    organization_id: str,
    approval_data: OrganizationApprovalRequest,
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    審核組織申請（僅管理員可用）
    
    - **approved**: 是否通過審核
    - **notes**: 審核備註（選填）
    """
    try:
        organization = await organization_service.approve_organization(
            db, organization_id, current_user.id, approval_data
        )
        
        from app.crud.user import user_crud
        user = user_crud.get_by_id(db, str(organization.user_id))
        
        return OrganizationResponse(
            id=str(organization.id),
            user_id=str(organization.user_id),
            organization_name=organization.organization_name,
            organization_type=organization.organization_type,
            contact_person=organization.contact_person,
            contact_phone=organization.contact_phone,
            address=organization.address,
            description=organization.description,
            approval_status=organization.approval_status,
            approved_by=str(organization.approved_by) if organization.approved_by else None,
            approved_at=organization.approved_at,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            user_name=user.name if user else None,
            user_email=user.email if user else None,
            approver_name=current_user.name
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{organization_id}/resubmit", response_model=OrganizationResponse, summary="重新提交組織申請")
async def resubmit_organization_application(
    organization_id: str,
    updated_data: OrganizationUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新提交組織申請（被拒絕後可重新提交）
    
    - **organization_name**: 組織名稱（選填）
    - **contact_person**: 聯絡人（選填）
    - **contact_phone**: 聯絡電話（選填）
    - **address**: 地址（選填）
    - **description**: 組織描述（選填）
    """
    try:
        organization = await organization_service.resubmit_organization(
            db, organization_id, current_user.id, updated_data.dict(exclude_unset=True)
        )
        
        return OrganizationResponse(
            id=str(organization.id),
            user_id=str(organization.user_id),
            organization_name=organization.organization_name,
            organization_type=organization.organization_type,
            contact_person=organization.contact_person,
            contact_phone=organization.contact_phone,
            address=organization.address,
            description=organization.description,
            approval_status=organization.approval_status,
            approved_by=str(organization.approved_by) if organization.approved_by else None,
            approved_at=organization.approved_at,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
            user_name=current_user.name,
            user_email=current_user.email,
            approver_name=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/statistics", summary="取得組織統計資料")
async def get_organization_statistics(
    current_user: UserProfile = Depends(AdminOnly),
    db: Session = Depends(get_db)
):
    """
    取得組織統計資料（僅管理員可用）
    
    包含：
    - 總組織數
    - 各狀態組織數
    - 各類型組織數
    """
    stats = await organization_service.get_organization_statistics(db)
    return stats


@router.get("/my-application", response_model=OrganizationResponse, summary="取得我的組織申請")
async def get_my_organization_application(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得當前用戶的組織申請狀態
    """
    from app.crud.user import user_crud
    
    organization = user_crud.get_organization_by_user_id(db, current_user.id)
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="尚未提交組織申請"
        )
    
    approver = None
    if organization.approved_by:
        approver = user_crud.get_by_id(db, str(organization.approved_by))
    
    return OrganizationResponse(
        id=str(organization.id),
        user_id=str(organization.user_id),
        organization_name=organization.organization_name,
        organization_type=organization.organization_type,
        contact_person=organization.contact_person,
        contact_phone=organization.contact_phone,
        address=organization.address,
        description=organization.description,
        approval_status=organization.approval_status,
        approved_by=str(organization.approved_by) if organization.approved_by else None,
        approved_at=organization.approved_at,
        created_at=organization.created_at,
        updated_at=organization.updated_at,
        user_name=current_user.name,
        user_email=current_user.email,
        approver_name=approver.name if approver else None
    )