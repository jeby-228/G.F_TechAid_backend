"""
需求管理相關的 API 端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.need import (
    NeedCreate, NeedUpdate, NeedResponse, NeedListResponse,
    NeedSearchQuery, NeedStatistics, NeedStatusUpdate, 
    NeedAssignment, NeedAssignmentResponse, LocationData,
    ContactInfo, NeedRequirements
)
from app.crud.need import need_crud
from app.middleware.auth import get_current_user
from app.schemas.auth import UserProfile
from app.utils.constants import UserRole, NeedType, NeedStatus
from app.services.notification_service import notification_service
from app.services.need_service import need_service

router = APIRouter()


def _can_create_need(user_role: UserRole) -> bool:
    """檢查用戶是否可以建立需求"""
    return user_role in [UserRole.VICTIM, UserRole.ADMIN]


def _can_manage_need(user_role: UserRole) -> bool:
    """檢查用戶是否可以管理需求"""
    return user_role in [UserRole.ADMIN, UserRole.OFFICIAL_ORG, UserRole.SUPPLY_MANAGER]


def _can_assign_need(user_role: UserRole) -> bool:
    """檢查用戶是否可以分配需求"""
    return user_role in [UserRole.ADMIN, UserRole.OFFICIAL_ORG]


def _convert_need_to_response(need, assignment_count: int = 0) -> NeedResponse:
    """轉換需求模型為回應模型"""
    return NeedResponse(
        id=str(need.id),
        reporter_id=str(need.reporter_id),
        title=need.title,
        description=need.description,
        need_type=NeedType(need.need_type),
        status=NeedStatus(need.status),
        location_data=LocationData(**need.location_data),
        requirements=NeedRequirements(**need.requirements),
        urgency_level=need.urgency_level,
        contact_info=ContactInfo(**need.contact_info) if need.contact_info else None,
        assigned_to=str(need.assigned_to) if need.assigned_to else None,
        assigned_at=need.assigned_at,
        resolved_at=need.resolved_at,
        created_at=need.created_at,
        updated_at=need.updated_at,
        reporter_name=need.reporter.name if need.reporter else None,
        reporter_phone=need.reporter.phone if need.reporter else None,
        assignee_name=need.assignee.name if need.assignee else None,
        assignment_count=assignment_count
    )


# 需求管理端點
@router.get("/", response_model=NeedListResponse, summary="取得需求列表")
async def get_needs(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    title: Optional[str] = Query(None, description="標題搜尋"),
    need_type: Optional[NeedType] = Query(None, description="需求類型篩選"),
    status: Optional[NeedStatus] = Query(None, description="狀態篩選"),
    urgency_level: Optional[int] = Query(None, ge=1, le=5, description="緊急程度篩選"),
    reporter_id: Optional[str] = Query(None, description="報告者ID篩選"),
    assigned_to: Optional[str] = Query(None, description="負責人ID篩選"),
    location_radius: Optional[float] = Query(None, ge=0, description="位置搜尋半徑(公里)"),
    center_lat: Optional[float] = Query(None, description="搜尋中心緯度"),
    center_lng: Optional[float] = Query(None, description="搜尋中心經度"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得需求列表
    
    支援搜尋和篩選功能：
    - **title**: 標題模糊搜尋
    - **need_type**: 需求類型篩選
    - **status**: 狀態篩選
    - **urgency_level**: 緊急程度篩選
    - **location_radius**: 地理位置搜尋（需配合 center_lat, center_lng）
    
    權限控制：
    - 受災戶只能看到自己的需求
    - 志工可以看到待處理和已分配給自己的需求
    - 管理員和正式組織可以看到所有需求
    """
    search_query = NeedSearchQuery(
        title=title,
        need_type=need_type,
        status=status,
        urgency_level=urgency_level,
        reporter_id=reporter_id,
        assigned_to=assigned_to,
        location_radius=location_radius,
        center_lat=center_lat,
        center_lng=center_lng
    )
    
    # 根據用戶角色調整搜尋條件
    if current_user.role == UserRole.VICTIM:
        # 受災戶只能看到自己的需求
        search_query.reporter_id = current_user.id
    elif current_user.role == UserRole.VOLUNTEER:
        # 一般志工只能看到待處理的需求和分配給自己的需求
        if not search_query.status:
            search_query.status = NeedStatus.OPEN
        if search_query.assigned_to is None:
            # 如果沒有指定負責人，則顯示待處理的需求
            pass
    
    needs = need_crud.get_multi(db, skip=skip, limit=limit, search_query=search_query)
    total = need_crud.count(db, search_query=search_query)
    
    need_responses = []
    for need in needs:
        # 取得分配記錄數量
        assignments = need_crud.get_assignments_by_need(db, str(need.id))
        need_responses.append(_convert_need_to_response(need, len(assignments)))
    
    return NeedListResponse(
        needs=need_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/statistics", response_model=NeedStatistics, summary="取得需求統計資料")
async def get_need_statistics(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得需求統計資料
    
    包含：
    - 總需求數和各類型分布
    - 各狀態需求數
    - 緊急程度分布
    - 平均解決時間
    
    權限：管理員和正式組織可用
    """
    if not _can_manage_need(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    return need_crud.get_statistics(db)


@router.get("/open", response_model=List[NeedResponse], summary="取得待處理需求列表")
async def get_open_needs(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得待處理的需求列表（按緊急程度排序）
    
    權限：志工以上角色可用
    """
    if current_user.role == UserRole.VICTIM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    needs = need_crud.get_open_needs(db, skip=skip, limit=limit)
    
    need_responses = []
    for need in needs:
        assignments = need_crud.get_assignments_by_need(db, str(need.id))
        need_responses.append(_convert_need_to_response(need, len(assignments)))
    
    return need_responses


@router.get("/urgent", response_model=List[NeedResponse], summary="取得緊急需求列表")
async def get_urgent_needs(
    urgency_threshold: int = Query(4, ge=1, le=5, description="緊急程度門檻"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得緊急需求列表
    
    權限：志工以上角色可用
    """
    if current_user.role == UserRole.VICTIM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    needs = need_crud.get_urgent_needs(db, urgency_threshold=urgency_threshold)
    
    need_responses = []
    for need in needs:
        assignments = need_crud.get_assignments_by_need(db, str(need.id))
        need_responses.append(_convert_need_to_response(need, len(assignments)))
    
    return need_responses


@router.get("/nearby", response_model=List[NeedResponse], summary="取得附近需求列表")
async def get_nearby_needs(
    center_lat: float = Query(..., description="中心點緯度"),
    center_lng: float = Query(..., description="中心點經度"),
    radius_km: float = Query(5.0, ge=0.1, le=50, description="搜尋半徑(公里)"),
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得附近的需求列表
    
    權限：志工以上角色可用
    """
    if current_user.role == UserRole.VICTIM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    needs = need_crud.get_nearby_needs(
        db, center_lat, center_lng, radius_km, skip=skip, limit=limit
    )
    
    need_responses = []
    for need in needs:
        assignments = need_crud.get_assignments_by_need(db, str(need.id))
        need_responses.append(_convert_need_to_response(need, len(assignments)))
    
    return need_responses


@router.get("/my", response_model=List[NeedResponse], summary="取得我的需求列表")
async def get_my_needs(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得當前用戶的需求列表
    
    - 受災戶：取得自己報告的需求
    - 志工/組織：取得分配給自己的需求
    """
    if current_user.role == UserRole.VICTIM:
        # 受災戶取得自己報告的需求
        needs = need_crud.get_by_reporter(db, current_user.id, skip=skip, limit=limit)
    else:
        # 志工取得分配給自己的需求
        needs = need_crud.get_by_assignee(db, current_user.id, skip=skip, limit=limit)
    
    need_responses = []
    for need in needs:
        assignments = need_crud.get_assignments_by_need(db, str(need.id))
        need_responses.append(_convert_need_to_response(need, len(assignments)))
    
    return need_responses


@router.get("/{need_id}", response_model=NeedResponse, summary="取得特定需求資訊")
async def get_need(
    need_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得特定需求的詳細資訊
    
    權限控制：
    - 需求報告者可以查看
    - 需求負責人可以查看
    - 管理員和正式組織可以查看所有需求
    """
    need = need_crud.get_by_id(db, need_id)
    if not need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    # 權限檢查
    can_view = (
        current_user.id == str(need.reporter_id) or  # 報告者
        current_user.id == str(need.assigned_to) if need.assigned_to else False or  # 負責人
        _can_manage_need(current_user.role)  # 管理員/正式組織
    )
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    assignments = need_crud.get_assignments_by_need(db, need_id)
    return _convert_need_to_response(need, len(assignments))


@router.post("/", response_model=NeedResponse, summary="建立新需求")
async def create_need(
    need_data: NeedCreate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    建立新需求
    
    權限：受災戶和管理員可用
    """
    if not _can_create_need(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足，只有受災戶可以建立需求"
        )
    
    try:
        need = need_crud.create(db, need_data, current_user.id)
        
        # 發送需求建立通知給管理員和正式組織
        await notification_service.send_new_need_notification(db, str(need.id))
        
        assignments = need_crud.get_assignments_by_need(db, str(need.id))
        return _convert_need_to_response(need, len(assignments))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{need_id}", response_model=NeedResponse, summary="更新需求資料")
async def update_need(
    need_id: str,
    need_data: NeedUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新需求資料
    
    權限：需求報告者和管理員可用
    """
    need = need_crud.get_by_id(db, need_id)
    if not need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    # 權限檢查
    can_edit = (
        current_user.id == str(need.reporter_id) or  # 報告者
        current_user.role == UserRole.ADMIN  # 管理員
    )
    
    if not can_edit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    updated_need = need_crud.update(db, need_id, need_data)
    if not updated_need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    assignments = need_crud.get_assignments_by_need(db, need_id)
    return _convert_need_to_response(updated_need, len(assignments))


@router.put("/{need_id}/status", response_model=NeedResponse, summary="更新需求狀態")
async def update_need_status(
    need_id: str,
    status_data: NeedStatusUpdate,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新需求狀態
    
    權限：需求負責人、管理員和正式組織可用
    """
    need = need_crud.get_by_id(db, need_id)
    if not need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    # 權限檢查
    can_update_status = (
        current_user.id == str(need.assigned_to) if need.assigned_to else False or  # 負責人
        _can_manage_need(current_user.role)  # 管理員/正式組織
    )
    
    if not can_update_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    updated_need = need_crud.update_status(db, need_id, status_data)
    if not updated_need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    # 發送狀態更新通知
    await notification_service.send_need_status_update_notification(
        db, need_id, status_data.status.value, status_data.notes
    )
    
    assignments = need_crud.get_assignments_by_need(db, need_id)
    return _convert_need_to_response(updated_need, len(assignments))


@router.post("/{need_id}/assign", response_model=NeedResponse, summary="分配需求給用戶")
async def assign_need(
    need_id: str,
    assignment_data: NeedAssignment,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    分配需求給用戶
    
    權限：管理員和正式組織可用
    """
    if not _can_assign_need(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    try:
        need = need_crud.assign_to_user(db, need_id, assignment_data)
        if not need:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )
        
        # 發送分配通知
        await notification_service.send_need_assignment_notification(
            db, need_id, assignment_data.assigned_to
        )
        
        assignments = need_crud.get_assignments_by_need(db, need_id)
        return _convert_need_to_response(need, len(assignments))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{need_id}/assign", response_model=NeedResponse, summary="取消需求分配")
async def unassign_need(
    need_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消需求分配
    
    權限：管理員和正式組織可用
    """
    if not _can_assign_need(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    need = need_crud.unassign(db, need_id)
    if not need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    assignments = need_crud.get_assignments_by_need(db, need_id)
    return _convert_need_to_response(need, len(assignments))


@router.delete("/{need_id}", summary="刪除需求")
async def delete_need(
    need_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刪除需求
    
    權限：需求報告者和管理員可用
    """
    need = need_crud.get_by_id(db, need_id)
    if not need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    # 權限檢查
    can_delete = (
        current_user.id == str(need.reporter_id) or  # 報告者
        current_user.role == UserRole.ADMIN  # 管理員
    )
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    success = need_crud.delete(db, need_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    return {"message": "需求刪除成功"}


# 需求分配記錄相關端點
@router.get("/{need_id}/assignments", response_model=List[NeedAssignmentResponse], summary="取得需求分配記錄")
async def get_need_assignments(
    need_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得需求的所有分配記錄
    
    權限：需求相關人員和管理員可用
    """
    need = need_crud.get_by_id(db, need_id)
    if not need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    # 權限檢查
    can_view = (
        current_user.id == str(need.reporter_id) or  # 報告者
        current_user.id == str(need.assigned_to) if need.assigned_to else False or  # 負責人
        _can_manage_need(current_user.role)  # 管理員/正式組織
    )
    
    if not can_view:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    assignments = need_crud.get_assignments_by_need(db, need_id)
    
    assignment_responses = []
    for assignment in assignments:
        assignment_responses.append(NeedAssignmentResponse(
            id=str(assignment.id),
            need_id=str(assignment.need_id),
            task_id=str(assignment.task_id) if assignment.task_id else None,
            user_id=str(assignment.user_id),
            assigned_at=assignment.assigned_at,
            completed_at=assignment.completed_at,
            notes=assignment.notes,
            status=assignment.status,
            need_title=assignment.need.title if assignment.need else None,
            task_title=assignment.task.title if assignment.task else None,
            user_name=assignment.user.name if assignment.user else None
        ))
    
    return assignment_responses


@router.post("/{need_id}/complete", response_model=NeedResponse, summary="完成需求")
async def complete_need(
    need_id: str,
    completion_notes: Optional[str] = None,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    標記需求為完成
    
    權限：需求負責人、管理員和正式組織可用
    """
    need = need_crud.get_by_id(db, need_id)
    if not need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    # 權限檢查
    if not need_service.can_user_manage_need(current_user.role, need, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    completed_need = await need_service.complete_need(db, need_id, completion_notes)
    if not completed_need:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="需求不存在"
        )
    
    assignments = need_crud.get_assignments_by_need(db, need_id)
    return _convert_need_to_response(completed_need, len(assignments))


@router.get("/available", response_model=List[NeedResponse], summary="取得可用需求列表")
async def get_available_needs(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁記錄數"),
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    根據用戶角色取得可用的需求列表
    
    - 受災戶：只能看到自己的需求
    - 志工：可以看到待處理的需求和分配給自己的需求
    - 管理員/正式組織：可以看到所有需求
    """
    needs = need_service.get_available_needs_for_user(
        db, current_user.role, current_user.id, skip=skip, limit=limit
    )
    
    need_responses = []
    for need in needs:
        assignments = need_crud.get_assignments_by_need(db, str(need.id))
        need_responses.append(_convert_need_to_response(need, len(assignments)))
    
    return need_responses


@router.post("/{need_id}/reassign", response_model=NeedResponse, summary="重新分配需求")
async def reassign_need(
    need_id: str,
    assignment_data: NeedAssignment,
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    重新分配需求給其他志工
    
    權限：管理員和正式組織可用
    """
    if not need_service.can_user_assign_need(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    # 先取消原有分配
    need_crud.unassign(db, need_id)
    
    # 重新分配
    try:
        need = await need_service.assign_need_to_volunteer(
            db, need_id, assignment_data, current_user.id
        )
        if not need:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="需求不存在"
            )
        
        assignments = need_crud.get_assignments_by_need(db, need_id)
        return _convert_need_to_response(need, len(assignments))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/status-summary", summary="取得需求狀態摘要")
async def get_need_status_summary(
    current_user: UserProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取得需求狀態摘要統計
    
    權限：管理員和正式組織可用
    """
    if not _can_manage_need(current_user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足"
        )
    
    stats = need_crud.get_statistics(db)
    
    # 計算處理效率
    total_processed = stats.resolved_needs + stats.assigned_needs
    processing_rate = (total_processed / stats.total_needs * 100) if stats.total_needs > 0 else 0
    
    return {
        "total_needs": stats.total_needs,
        "open_needs": stats.open_needs,
        "assigned_needs": stats.assigned_needs,
        "resolved_needs": stats.resolved_needs,
        "processing_rate": round(processing_rate, 2),
        "average_resolution_time_hours": stats.average_resolution_time,
        "needs_by_type": stats.needs_by_type,
        "needs_by_urgency": stats.needs_by_urgency
    }