"""
公告相關 API 端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.models.user import User
from app.models.system import Announcement
from app.services.announcement_service import announcement_service
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementUpdate,
    AnnouncementResponse,
    AnnouncementListResponse,
    EmergencyAnnouncementCreate,
    AnnouncementStatsResponse,
    PublicAnnouncementResponse
)
from app.utils.constants import AnnouncementType, UserRole

router = APIRouter()


@router.post("/", response_model=AnnouncementResponse)
def create_announcement(
    announcement_data: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """建立系統公告（僅管理員）"""
    announcement = announcement_service.create_announcement(
        db=db,
        title=announcement_data.title,
        content=announcement_data.content,
        announcement_type=announcement_data.announcement_type,
        created_by=str(current_user.id),
        priority_level=announcement_data.priority_level,
        target_roles=announcement_data.target_roles,
        expires_at=announcement_data.expires_at
    )
    
    return _format_announcement_response(announcement, current_user.name)


@router.get("/", response_model=AnnouncementListResponse)
def get_announcements(
    announcement_type: Optional[AnnouncementType] = Query(None, description="公告類型"),
    active_only: bool = Query(True, description="只顯示活躍公告"),
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(50, ge=1, le=100, description="限制數量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取得公告列表"""
    announcements = announcement_service.get_announcements(
        db=db,
        user_role=UserRole(current_user.role),
        announcement_type=announcement_type,
        active_only=active_only,
        skip=skip,
        limit=limit
    )
    
    total_count = announcement_service.get_announcements_count(
        db=db,
        user_role=UserRole(current_user.role),
        announcement_type=announcement_type,
        active_only=active_only
    )
    
    # 取得創建者資訊
    announcement_responses = []
    for announcement in announcements:
        creator = db.query(User).filter(User.id == announcement.created_by).first()
        creator_name = creator.name if creator else "未知用戶"
        announcement_responses.append(_format_announcement_response(announcement, creator_name))
    
    return AnnouncementListResponse(
        announcements=announcement_responses,
        total_count=total_count,
        skip=skip,
        limit=limit
    )


@router.get("/public", response_model=List[PublicAnnouncementResponse])
def get_public_announcements(
    announcement_type: Optional[AnnouncementType] = Query(None, description="公告類型"),
    limit: int = Query(10, ge=1, le=50, description="限制數量"),
    db: Session = Depends(get_db)
):
    """取得公開公告（無需登入）"""
    announcements = announcement_service.get_announcements(
        db=db,
        user_role=None,  # 不過濾角色
        announcement_type=announcement_type,
        active_only=True,
        limit=limit
    )
    
    return [
        PublicAnnouncementResponse(
            id=str(announcement.id),
            title=announcement.title,
            content=announcement.content,
            announcement_type=announcement.announcement_type,
            priority_level=announcement.priority_level,
            created_at=announcement.created_at,
            expires_at=announcement.expires_at
        )
        for announcement in announcements
    ]


@router.get("/emergency", response_model=List[PublicAnnouncementResponse])
def get_emergency_announcements(
    limit: int = Query(5, ge=1, le=20, description="限制數量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取得緊急公告"""
    announcements = announcement_service.get_emergency_announcements(
        db=db,
        user_role=UserRole(current_user.role),
        limit=limit
    )
    
    return [
        PublicAnnouncementResponse(
            id=str(announcement.id),
            title=announcement.title,
            content=announcement.content,
            announcement_type=announcement.announcement_type,
            priority_level=announcement.priority_level,
            created_at=announcement.created_at,
            expires_at=announcement.expires_at
        )
        for announcement in announcements
    ]


@router.get("/stats", response_model=AnnouncementStatsResponse)
def get_announcement_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """取得公告統計（僅管理員）"""
    user_role = UserRole(current_user.role)
    
    total_count = announcement_service.get_announcements_count(
        db=db, user_role=user_role, active_only=False
    )
    active_count = announcement_service.get_announcements_count(
        db=db, user_role=user_role, active_only=True
    )
    emergency_count = announcement_service.get_announcements_count(
        db=db, user_role=user_role, announcement_type=AnnouncementType.EMERGENCY, active_only=True
    )
    expired_count = total_count - active_count
    
    return AnnouncementStatsResponse(
        total_count=total_count,
        active_count=active_count,
        emergency_count=emergency_count,
        expired_count=expired_count
    )


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取得單一公告詳情"""
    announcement = announcement_service.get_announcement_by_id(db, announcement_id)
    
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    # 檢查用戶是否有權限查看此公告
    if announcement.target_roles:
        if current_user.role not in announcement.target_roles:
            raise HTTPException(status_code=403, detail="無權限查看此公告")
    
    creator = db.query(User).filter(User.id == announcement.created_by).first()
    creator_name = creator.name if creator else "未知用戶"
    
    return _format_announcement_response(announcement, creator_name)


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: str,
    announcement_data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """更新公告（僅管理員）"""
    announcement = announcement_service.update_announcement(
        db=db,
        announcement_id=announcement_id,
        title=announcement_data.title,
        content=announcement_data.content,
        announcement_type=announcement_data.announcement_type,
        priority_level=announcement_data.priority_level,
        target_roles=announcement_data.target_roles,
        expires_at=announcement_data.expires_at,
        is_active=announcement_data.is_active
    )
    
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    return _format_announcement_response(announcement, current_user.name)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """刪除公告（僅管理員）"""
    success = announcement_service.delete_announcement(db, announcement_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    return {"message": "公告已刪除"}


@router.post("/emergency", response_model=AnnouncementResponse)
async def create_emergency_announcement(
    announcement_data: EmergencyAnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """發布緊急公告並推播通知（僅管理員）"""
    announcement = await announcement_service.publish_emergency_announcement(
        db=db,
        title=announcement_data.title,
        content=announcement_data.content,
        created_by=str(current_user.id),
        target_roles=announcement_data.target_roles,
        send_notifications=announcement_data.send_notifications
    )
    
    return _format_announcement_response(announcement, current_user.name)


@router.put("/{announcement_id}/expire")
def expire_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """手動過期公告（僅管理員）"""
    success = announcement_service.expire_announcement(db, announcement_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    return {"message": "公告已過期"}


@router.get("/my/created", response_model=AnnouncementListResponse)
def get_my_announcements(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(50, ge=1, le=100, description="限制數量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """取得我建立的公告（僅管理員）"""
    announcements = announcement_service.get_announcements_by_creator(
        db=db,
        creator_id=str(current_user.id),
        skip=skip,
        limit=limit
    )
    
    total_count = db.query(Announcement).filter(
        Announcement.created_by == current_user.id
    ).count()
    
    announcement_responses = [
        _format_announcement_response(announcement, current_user.name)
        for announcement in announcements
    ]
    
    return AnnouncementListResponse(
        announcements=announcement_responses,
        total_count=total_count,
        skip=skip,
        limit=limit
    )


def _format_announcement_response(announcement: Announcement, creator_name: str) -> AnnouncementResponse:
    """格式化公告回應"""
    return AnnouncementResponse(
        id=str(announcement.id),
        title=announcement.title,
        content=announcement.content,
        announcement_type=AnnouncementType(announcement.announcement_type),
        priority_level=announcement.priority_level,
        target_roles=announcement.target_roles,
        is_active=announcement.is_active,
        expires_at=announcement.expires_at,
        created_by=str(announcement.created_by),
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
        creator_name=creator_name
    )