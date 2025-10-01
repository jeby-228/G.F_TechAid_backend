"""
通知相關 API 端點
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.system import Notification
from app.services.notification_service import notification_service
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationStatsResponse
)

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket 端點用於即時通知"""
    await notification_service.connect_websocket(websocket, user_id)
    try:
        while True:
            # 保持連線活躍
            await websocket.receive_text()
    except WebSocketDisconnect:
        await notification_service.disconnect_websocket(websocket, user_id)


@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取得用戶通知列表"""
    notifications = notification_service.get_user_notifications(
        db=db,
        user_id=str(current_user.id),
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    total_count = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).count()
    
    unread_count = notification_service.get_unread_count(
        db=db,
        user_id=str(current_user.id)
    )
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=str(notification.id),
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                related_id=str(notification.related_id) if notification.related_id else None,
                is_read=notification.is_read,
                created_at=notification.created_at,
                read_at=notification.read_at
            )
            for notification in notifications
        ],
        total_count=total_count,
        unread_count=unread_count,
        skip=skip,
        limit=limit
    )


@router.get("/stats", response_model=NotificationStatsResponse)
def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取得通知統計資訊"""
    unread_count = notification_service.get_unread_count(
        db=db,
        user_id=str(current_user.id)
    )
    
    total_count = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).count()
    
    return NotificationStatsResponse(
        unread_count=unread_count,
        total_count=total_count
    )


@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """標記單一通知為已讀"""
    success = notification_service.mark_notification_as_read(
        db=db,
        notification_id=notification_id,
        user_id=str(current_user.id)
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="通知不存在或已經是已讀狀態")
    
    return {"message": "通知已標記為已讀"}


@router.put("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """標記所有通知為已讀"""
    updated_count = notification_service.mark_all_notifications_as_read(
        db=db,
        user_id=str(current_user.id)
    )
    
    return {
        "message": f"已標記 {updated_count} 個通知為已讀",
        "updated_count": updated_count
    }


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """取得單一通知詳情"""
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="通知不存在")
        
        return NotificationResponse(
            id=str(notification.id),
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            related_id=str(notification.related_id) if notification.related_id else None,
            is_read=notification.is_read,
            created_at=notification.created_at,
            read_at=notification.read_at
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="無效的通知 ID 格式")