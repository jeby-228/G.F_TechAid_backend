"""
監控系統相關的 Pydantic 模型
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    """總覽統計"""
    total_users: int = Field(..., description="總用戶數")
    total_tasks: int = Field(..., description="總任務數")
    total_needs: int = Field(..., description="總需求數")
    total_supply_stations: int = Field(..., description="總物資站點數")
    active_tasks: int = Field(..., description="活躍任務數")
    open_needs: int = Field(..., description="開放需求數")


class TodayStats(BaseModel):
    """今日統計"""
    new_users: int = Field(..., description="今日新用戶數")
    new_tasks: int = Field(..., description="今日新任務數")
    new_needs: int = Field(..., description="今日新需求數")


class RealTimeStatistics(BaseModel):
    """即時統計資料"""
    overview: OverviewStats
    today_stats: TodayStats
    user_distribution: Dict[str, int] = Field(..., description="用戶角色分布")
    last_updated: str = Field(..., description="最後更新時間")


class ProgressStats(BaseModel):
    """進度統計基礎模型"""
    status_distribution: Dict[str, int] = Field(..., description="狀態分布")
    total_tasks: int = Field(..., description="總數量")
    completed_tasks: int = Field(..., description="完成數量")
    completion_rate: float = Field(..., description="完成率")


class TaskProgressStats(ProgressStats):
    """任務進度統計"""
    pass


class NeedProgressStats(BaseModel):
    """需求進度統計"""
    status_distribution: Dict[str, int] = Field(..., description="狀態分布")
    total_needs: int = Field(..., description="總需求數")
    resolved_needs: int = Field(..., description="已解決需求數")
    resolution_rate: float = Field(..., description="解決率")


class OverallCompletion(BaseModel):
    """整體完成率"""
    task_completion_rate: float = Field(..., description="任務完成率")
    need_resolution_rate: float = Field(..., description="需求解決率")
    overall_completion_rate: float = Field(..., description="整體完成率")
    total_items: int = Field(..., description="總項目數")
    completed_items: int = Field(..., description="已完成項目數")


class DailyProgress(BaseModel):
    """每日進度"""
    date: str = Field(..., description="日期")
    completed_tasks: int = Field(..., description="完成任務數")
    resolved_needs: int = Field(..., description="解決需求數")
    new_tasks: int = Field(..., description="新任務數")
    new_needs: int = Field(..., description="新需求數")
    total_completed: int = Field(..., description="總完成數")
    total_new: int = Field(..., description="總新增數")


class UrgencyAnalysis(BaseModel):
    """緊急程度分析"""
    need_urgency_distribution: Dict[str, int] = Field(..., description="需求緊急程度分布")
    high_priority_tasks: int = Field(..., description="高優先級任務數")
    high_urgency_needs: int = Field(..., description="高緊急需求數")
    total_urgent_items: int = Field(..., description="總緊急項目數")


class PeriodInfo(BaseModel):
    """時間段資訊"""
    start_date: str = Field(..., description="開始日期")
    end_date: str = Field(..., description="結束日期")
    days: int = Field(..., description="天數")


class DisasterReliefProgress(BaseModel):
    """救災進度追蹤"""
    period: PeriodInfo
    task_progress: TaskProgressStats
    need_progress: NeedProgressStats
    overall_completion: OverallCompletion
    daily_progress: List[DailyProgress]
    urgency_analysis: UrgencyAnalysis


class TaskTypeCompletion(BaseModel):
    """任務類型完成統計"""
    task_type: str = Field(..., description="任務類型")
    total: int = Field(..., description="總數")
    completed: int = Field(..., description="完成數")
    completion_rate: float = Field(..., description="完成率")


class TopVolunteer(BaseModel):
    """頂級志工"""
    user_id: str = Field(..., description="用戶ID")
    user_name: str = Field(..., description="用戶姓名")
    completed_tasks: int = Field(..., description="完成任務數")


class VolunteerEfficiency(BaseModel):
    """志工效率統計"""
    active_volunteers: int = Field(..., description="活躍志工數")
    total_completed_tasks: int = Field(..., description="總完成任務數")
    avg_tasks_per_volunteer: float = Field(..., description="平均每志工完成任務數")
    top_volunteers: List[TopVolunteer] = Field(..., description="頂級志工列表")


class TaskCompletionOverall(BaseModel):
    """任務完成總覽"""
    total_tasks: int = Field(..., description="總任務數")
    completed_tasks: int = Field(..., description="完成任務數")
    completion_rate: float = Field(..., description="完成率")


class TaskCompletionStatistics(BaseModel):
    """任務完成率統計"""
    period: PeriodInfo
    overall: TaskCompletionOverall
    by_task_type: List[TaskTypeCompletion]
    average_completion_time_hours: float = Field(..., description="平均完成時間（小時）")
    volunteer_efficiency: VolunteerEfficiency


class SupplyReservationStats(BaseModel):
    """物資預訂統計"""
    status_distribution: Dict[str, int] = Field(..., description="狀態分布")
    total_reservations: int = Field(..., description="總預訂數")
    delivered_reservations: int = Field(..., description="已配送預訂數")
    delivery_rate: float = Field(..., description="配送率")


class StationActivity(BaseModel):
    """物資站點活動"""
    station_name: str = Field(..., description="站點名稱")
    reservation_count: int = Field(..., description="預訂數量")


class SupplyTypeFlow(BaseModel):
    """物資類型流向"""
    supply_type: str = Field(..., description="物資類型")
    total_quantity: int = Field(..., description="總數量")
    reservation_count: int = Field(..., description="預訂次數")


class DeliveryEfficiency(BaseModel):
    """配送效率"""
    avg_delivery_time_hours: float = Field(..., description="平均配送時間（小時）")
    total_confirmed_reservations: int = Field(..., description="總確認預訂數")
    total_delivered_reservations: int = Field(..., description="總配送預訂數")
    delivery_success_rate: float = Field(..., description="配送成功率")


class SupplyFlowMonitoring(BaseModel):
    """物資流向監控"""
    period: PeriodInfo
    reservation_stats: SupplyReservationStats
    station_activity: List[StationActivity]
    supply_type_flow: List[SupplyTypeFlow]
    delivery_efficiency: DeliveryEfficiency


class InventoryOverview(BaseModel):
    """庫存總覽"""
    total_active_stations: int = Field(..., description="總活躍站點數")
    total_available_items: int = Field(..., description="總可用物品數")


class LowInventoryAlert(BaseModel):
    """低庫存警告"""
    station_name: str = Field(..., description="站點名稱")
    inventory_count: int = Field(..., description="庫存數量")


class InventoryStatistics(BaseModel):
    """庫存統計"""
    overview: InventoryOverview
    by_supply_type: Dict[str, int] = Field(..., description="按物資類型統計")
    by_station: List[StationActivity] = Field(..., description="按站點統計")
    low_inventory_alerts: List[LowInventoryAlert] = Field(..., description="低庫存警告")
    last_updated: str = Field(..., description="最後更新時間")


class SystemLogEntry(BaseModel):
    """系統日誌條目"""
    id: str = Field(..., description="日誌ID")
    user_id: Optional[str] = Field(None, description="用戶ID")
    action: str = Field(..., description="操作")
    resource_type: Optional[str] = Field(None, description="資源類型")
    resource_id: Optional[str] = Field(None, description="資源ID")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細資訊")
    ip_address: Optional[str] = Field(None, description="IP地址")
    created_at: str = Field(..., description="創建時間")


class ActivitySummary(BaseModel):
    """活動摘要"""
    active_users: int = Field(..., description="活躍用戶數")
    total_actions: int = Field(..., description="總操作數")


class ActivityPeriod(BaseModel):
    """活動時間段"""
    start_time: str = Field(..., description="開始時間")
    end_time: str = Field(..., description="結束時間")
    hours: int = Field(..., description="小時數")


class SystemActivityLog(BaseModel):
    """系統活動日誌"""
    period: ActivityPeriod
    summary: ActivitySummary
    activity_counts: Dict[str, int] = Field(..., description="活動計數")
    recent_logs: List[SystemLogEntry] = Field(..., description="最近日誌")


# 監控儀表板綜合回應
class MonitoringDashboard(BaseModel):
    """監控儀表板"""
    real_time_stats: RealTimeStatistics
    disaster_relief_progress: DisasterReliefProgress
    task_completion_stats: TaskCompletionStatistics
    supply_flow_monitoring: SupplyFlowMonitoring
    inventory_stats: InventoryStatistics
    system_activity: SystemActivityLog
    generated_at: str = Field(..., description="生成時間")


# API 查詢參數
class MonitoringQuery(BaseModel):
    """監控查詢參數"""
    days: Optional[int] = Field(7, ge=1, le=365, description="查詢天數")
    hours: Optional[int] = Field(24, ge=1, le=168, description="查詢小時數")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="限制數量")