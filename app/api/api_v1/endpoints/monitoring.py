"""
監控系統 API 端點
"""
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.models.user import User
from app.services.monitoring_service import monitoring_service
from app.schemas.monitoring import (
    RealTimeStatistics,
    DisasterReliefProgress,
    TaskCompletionStatistics,
    SupplyFlowMonitoring,
    InventoryStatistics,
    SystemActivityLog,
    MonitoringDashboard,
    MonitoringQuery
)

router = APIRouter()


@router.get("/real-time", response_model=RealTimeStatistics)
async def get_real_time_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取即時統計資料
    
    - **需要權限**: 已登入用戶
    - **返回**: 即時統計資料，包含總覽、今日統計和用戶分布
    """
    stats = monitoring_service.get_real_time_statistics(db)
    return RealTimeStatistics(**stats)


@router.get("/disaster-relief-progress", response_model=DisasterReliefProgress)
async def get_disaster_relief_progress(
    days: int = Query(7, ge=1, le=365, description="查詢天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取救災進度追蹤統計
    
    - **days**: 查詢天數（1-365天）
    - **需要權限**: 已登入用戶
    - **返回**: 救災進度統計，包含任務和需求進度、整體完成率等
    """
    progress = monitoring_service.get_disaster_relief_progress(db, days)
    return DisasterReliefProgress(**progress)


@router.get("/task-completion", response_model=TaskCompletionStatistics)
async def get_task_completion_statistics(
    days: int = Query(30, ge=1, le=365, description="查詢天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取任務完成率統計
    
    - **days**: 查詢天數（1-365天）
    - **需要權限**: 已登入用戶
    - **返回**: 任務完成率統計，包含整體完成率、按類型統計、志工效率等
    """
    stats = monitoring_service.get_task_completion_statistics(db, days)
    return TaskCompletionStatistics(**stats)


@router.get("/supply-flow", response_model=SupplyFlowMonitoring)
async def get_supply_flow_monitoring(
    days: int = Query(7, ge=1, le=365, description="查詢天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取物資流向監控統計
    
    - **days**: 查詢天數（1-365天）
    - **需要權限**: 已登入用戶
    - **返回**: 物資流向監控，包含預訂統計、站點活動、配送效率等
    """
    monitoring = monitoring_service.get_supply_flow_monitoring(db, days)
    return SupplyFlowMonitoring(**monitoring)


@router.get("/inventory", response_model=InventoryStatistics)
async def get_inventory_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取庫存統計
    
    - **需要權限**: 已登入用戶
    - **返回**: 庫存統計，包含總覽、按類型和站點統計、低庫存警告
    """
    stats = monitoring_service.get_inventory_statistics(db)
    return InventoryStatistics(**stats)


@router.get("/system-activity", response_model=SystemActivityLog)
async def get_system_activity_log(
    hours: int = Query(24, ge=1, le=168, description="查詢小時數"),
    limit: int = Query(100, ge=1, le=1000, description="日誌條目限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    獲取系統活動日誌
    
    - **hours**: 查詢小時數（1-168小時）
    - **limit**: 日誌條目限制（1-1000條）
    - **需要權限**: 管理員
    - **返回**: 系統活動日誌，包含活動摘要和最近日誌
    """
    activity_log = monitoring_service.get_system_activity_log(db, hours, limit)
    return SystemActivityLog(**activity_log)


@router.get("/dashboard", response_model=MonitoringDashboard)
async def get_monitoring_dashboard(
    query: MonitoringQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取監控儀表板綜合資料
    
    - **days**: 查詢天數（預設7天）
    - **hours**: 系統活動查詢小時數（預設24小時）
    - **limit**: 日誌條目限制（預設100條）
    - **需要權限**: 已登入用戶（系統活動需要管理員權限）
    - **返回**: 綜合監控儀表板資料
    """
    # 獲取各項統計資料
    real_time_stats = monitoring_service.get_real_time_statistics(db)
    disaster_relief_progress = monitoring_service.get_disaster_relief_progress(db, query.days)
    task_completion_stats = monitoring_service.get_task_completion_statistics(db, query.days)
    supply_flow_monitoring = monitoring_service.get_supply_flow_monitoring(db, query.days)
    inventory_stats = monitoring_service.get_inventory_statistics(db)
    
    # 系統活動日誌需要管理員權限
    try:
        if current_user.role == "admin":
            system_activity = monitoring_service.get_system_activity_log(db, query.hours, query.limit)
        else:
            # 非管理員用戶返回空的系統活動日誌
            system_activity = {
                "period": {
                    "start_time": datetime.utcnow().isoformat(),
                    "end_time": datetime.utcnow().isoformat(),
                    "hours": 0
                },
                "summary": {
                    "active_users": 0,
                    "total_actions": 0
                },
                "activity_counts": {},
                "recent_logs": []
            }
    except Exception:
        # 如果獲取系統活動失敗，返回空資料
        system_activity = {
            "period": {
                "start_time": datetime.utcnow().isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "hours": 0
            },
            "summary": {
                "active_users": 0,
                "total_actions": 0
            },
            "activity_counts": {},
            "recent_logs": []
        }
    
    dashboard_data = {
        "real_time_stats": real_time_stats,
        "disaster_relief_progress": disaster_relief_progress,
        "task_completion_stats": task_completion_stats,
        "supply_flow_monitoring": supply_flow_monitoring,
        "inventory_stats": inventory_stats,
        "system_activity": system_activity,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    return MonitoringDashboard(**dashboard_data)


@router.get("/health")
async def monitoring_health_check():
    """
    監控系統健康檢查
    
    - **返回**: 監控系統狀態
    """
    return {
        "status": "healthy",
        "service": "monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }


# 管理員專用端點
@router.get("/admin/detailed-stats", response_model=Dict[str, Any])
async def get_detailed_admin_statistics(
    days: int = Query(30, ge=1, le=365, description="查詢天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    獲取詳細的管理員統計資料
    
    - **days**: 查詢天數（1-365天）
    - **需要權限**: 管理員
    - **返回**: 詳細的系統統計資料
    """
    # 獲取所有統計資料
    real_time_stats = monitoring_service.get_real_time_statistics(db)
    disaster_relief_progress = monitoring_service.get_disaster_relief_progress(db, days)
    task_completion_stats = monitoring_service.get_task_completion_statistics(db, days)
    supply_flow_monitoring = monitoring_service.get_supply_flow_monitoring(db, days)
    inventory_stats = monitoring_service.get_inventory_statistics(db)
    system_activity = monitoring_service.get_system_activity_log(db, 24, 200)
    
    return {
        "real_time_statistics": real_time_stats,
        "disaster_relief_progress": disaster_relief_progress,
        "task_completion_statistics": task_completion_stats,
        "supply_flow_monitoring": supply_flow_monitoring,
        "inventory_statistics": inventory_stats,
        "system_activity_log": system_activity,
        "query_period_days": days,
        "generated_at": datetime.utcnow().isoformat(),
        "generated_by": {
            "user_id": str(current_user.id),
            "user_name": current_user.name,
            "user_role": current_user.role
        }
    }