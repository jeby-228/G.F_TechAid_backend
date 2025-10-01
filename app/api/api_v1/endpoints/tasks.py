"""
任務管理 API 端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    TaskSearchQuery, TaskApprovalRequest, TaskClaimCreate,
    TaskClaimResponse, TaskClaimListResponse, TaskStatistics,
    TaskStatusUpdate, TaskActivityLog, TaskConflictCheck, TaskHistoryQuery
)
from app.services.task_service import task_service
from app.utils.constants import UserRole

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    建立新任務
    
    - **title**: 任務標題
    - **description**: 任務描述
    - **task_type**: 任務類型
    - **location_data**: 任務地點資訊
    - **required_volunteers**: 所需志工人數
    - **required_skills**: 所需技能（可選）
    - **deadline**: 截止時間（可選）
    - **priority_level**: 優先級 (1-5)
    """
    return task_service.create_task(
        db, task_data, str(current_user.id), current_user.role
    )


@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    title: Optional[str] = Query(None, description="標題搜尋"),
    task_type: Optional[str] = Query(None, description="任務類型篩選"),
    status: Optional[str] = Query(None, description="狀態篩選"),
    creator_id: Optional[str] = Query(None, description="建立者篩選"),
    priority_level: Optional[int] = Query(None, ge=1, le=5, description="優先級篩選"),
    location_radius: Optional[float] = Query(None, ge=0, description="位置半徑篩選(公里)"),
    center_lat: Optional[float] = Query(None, description="中心緯度"),
    center_lng: Optional[float] = Query(None, description="中心經度"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取任務列表
    
    支援多種篩選條件：
    - 標題搜尋
    - 任務類型篩選
    - 狀態篩選
    - 建立者篩選
    - 優先級篩選
    - 地理位置篩選
    """
    search_query = TaskSearchQuery(
        title=title,
        task_type=task_type,
        status=status,
        creator_id=creator_id,
        priority_level=priority_level,
        location_radius=location_radius,
        center_lat=center_lat,
        center_lng=center_lng
    )
    
    return task_service.get_tasks(
        db, skip, limit, search_query, str(current_user.id), current_user.role
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    根據 ID 獲取單一任務
    """
    task = task_service.get_task(db, task_id, str(current_user.id), current_user.role)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任務不存在"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新任務資訊
    
    只有任務建立者和管理員可以更新任務
    已認領或完成的任務無法更新基本資訊
    """
    task = task_service.update_task(
        db, task_id, task_update, str(current_user.id), current_user.role
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任務不存在"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    刪除任務
    
    只有任務建立者和管理員可以刪除任務
    已認領的任務無法刪除
    """
    success = task_service.delete_task(
        db, task_id, str(current_user.id), current_user.role
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任務不存在"
        )


@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_task(
    task_id: str,
    approval_request: TaskApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    審核任務（管理員專用）
    
    用於審核非正式組織建立的任務
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以審核任務"
        )
    
    task = task_service.approve_task(
        db, task_id, approval_request, str(current_user.id)
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任務不存在"
        )
    return task


@router.post("/claim", response_model=TaskClaimResponse, status_code=status.HTTP_201_CREATED)
async def claim_task(
    claim_data: TaskClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    認領任務
    
    志工可以認領可用的任務
    受災戶無法認領任務
    """
    return task_service.claim_task(
        db, claim_data, str(current_user.id), current_user.role
    )


@router.get("/claims/my", response_model=TaskClaimListResponse)
async def get_my_claims(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前用戶的任務認領記錄
    """
    return task_service.get_user_claims(db, str(current_user.id), skip, limit)


@router.get("/{task_id}/claims", response_model=List[TaskClaimResponse])
async def get_task_claims(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取任務的所有認領記錄
    
    只有任務建立者和管理員可以查看
    """
    return task_service.get_task_claims(
        db, task_id, str(current_user.id), current_user.role
    )


@router.put("/claims/{claim_id}/status")
async def update_claim_status(
    claim_id: str,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新認領狀態
    
    認領者可以更新自己的認領狀態：
    - claimed: 已認領
    - started: 開始執行
    - completed: 已完成
    - cancelled: 已取消
    """
    claim = task_service.update_claim_status(
        db, claim_id, status_update.status, str(current_user.id), status_update.notes
    )
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="認領記錄不存在"
        )
    return claim


@router.get("/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取任務統計資料（管理員專用）
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以查看統計資料"
        )
    
    return task_service.get_task_statistics(db)


@router.get("/pending-approval", response_model=TaskListResponse)
async def get_pending_approval_tasks(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取待審核任務列表（管理員專用）
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理員可以查看待審核任務"
        )
    
    search_query = TaskSearchQuery(status="pending")
    return task_service.get_tasks(
        db, skip, limit, search_query, str(current_user.id), current_user.role
    )


@router.get("/available", response_model=TaskListResponse)
async def get_available_tasks(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    location_radius: Optional[float] = Query(None, ge=0, description="位置半徑篩選(公里)"),
    center_lat: Optional[float] = Query(None, description="中心緯度"),
    center_lng: Optional[float] = Query(None, description="中心經度"),
    task_type: Optional[str] = Query(None, description="任務類型篩選"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取可認領任務列表
    
    所有用戶都可以查看可認領的任務
    """
    search_query = TaskSearchQuery(
        status="available",
        task_type=task_type,
        location_radius=location_radius,
        center_lat=center_lat,
        center_lng=center_lng
    )
    
    return task_service.get_tasks(
        db, skip, limit, search_query, str(current_user.id), current_user.role
    )


@router.get("/history/my", response_model=TaskClaimListResponse)
async def get_my_task_history(
    skip: int = Query(0, ge=0, description="跳過數量"),
    limit: int = Query(100, ge=1, le=1000, description="限制數量"),
    status_filter: Optional[str] = Query(None, description="狀態篩選"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前用戶的任務歷史記錄
    
    包含所有已認領、進行中、已完成和已取消的任務
    """
    return task_service.get_task_history(
        db, str(current_user.id), skip, limit, status_filter
    )


@router.get("/{task_id}/activity-log")
async def get_task_activity_log(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取任務活動日誌
    
    只有任務建立者、認領者和管理員可以查看
    """
    return task_service.get_task_activity_log(
        db, task_id, str(current_user.id), current_user.role
    )


@router.get("/{task_id}/conflicts")
async def check_task_conflicts(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    檢查任務認領衝突
    
    在認領任務前檢查是否有衝突
    """
    return task_service.check_task_conflicts(
        db, task_id, str(current_user.id)
    )


@router.post("/{task_id}/claim", response_model=TaskClaimResponse, status_code=status.HTTP_201_CREATED)
async def claim_task_by_id(
    task_id: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    認領指定任務（替代方案）
    
    提供更直觀的任務認領方式
    """
    from app.schemas.task import TaskClaimCreate
    
    claim_data = TaskClaimCreate(task_id=task_id, notes=notes)
    return task_service.claim_task(
        db, claim_data, str(current_user.id), current_user.role
    )