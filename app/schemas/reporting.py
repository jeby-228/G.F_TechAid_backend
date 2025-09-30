"""
報表系統相關的 Pydantic 模型
"""
from typing import Dict, Any, List, Optional
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, validator


class ReportQuery(BaseModel):
    """報表查詢參數"""
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    format_type: Literal["pdf", "csv", "excel"] = Field("pdf", description="報表格式")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('結束日期不能早於開始日期')
        return v
    
    @validator('start_date', 'end_date')
    def validate_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('日期不能是未來日期')
        return v


class ReportPeriod(BaseModel):
    """報表期間"""
    start_date: str = Field(..., description="開始日期")
    end_date: str = Field(..., description="結束日期")
    days: int = Field(..., description="天數")


class ReportMetadata(BaseModel):
    """報表元資料"""
    report_title: str = Field(..., description="報表標題")
    report_type: str = Field(..., description="報表類型")
    period: ReportPeriod = Field(..., description="報表期間")
    generated_at: str = Field(..., description="生成時間")
    generated_by: Optional[str] = Field(None, description="生成者")
    file_size: Optional[int] = Field(None, description="檔案大小(bytes)")
    format_type: str = Field(..., description="檔案格式")


class TaskDetail(BaseModel):
    """任務詳細資料"""
    task_id: str = Field(..., description="任務ID")
    title: str = Field(..., description="任務標題")
    task_type: str = Field(..., description="任務類型")
    status: str = Field(..., description="狀態")
    priority_level: int = Field(..., description="優先級")
    required_volunteers: int = Field(..., description="所需志工數")
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")


class NeedDetail(BaseModel):
    """需求詳細資料"""
    need_id: str = Field(..., description="需求ID")
    title: str = Field(..., description="需求標題")
    need_type: str = Field(..., description="需求類型")
    status: str = Field(..., description="狀態")
    urgency_level: int = Field(..., description="緊急程度")
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")


class TaskClaimDetail(BaseModel):
    """任務認領詳細資料"""
    task_id: str = Field(..., description="任務ID")
    task_title: str = Field(..., description="任務標題")
    task_type: str = Field(..., description="任務類型")
    volunteer_name: str = Field(..., description="志工姓名")
    volunteer_role: str = Field(..., description="志工角色")
    claimed_at: str = Field(..., description="認領時間")
    started_at: Optional[str] = Field(None, description="開始時間")
    completed_at: Optional[str] = Field(None, description="完成時間")
    completion_time_hours: Optional[float] = Field(None, description="完成耗時(小時)")
    status: str = Field(..., description="狀態")
    notes: Optional[str] = Field(None, description="備註")


class SupplyReservationDetail(BaseModel):
    """物資預訂詳細資料"""
    reservation_id: str = Field(..., description="預訂ID")
    station_name: str = Field(..., description="物資站點")
    requester_name: str = Field(..., description="預訂者")
    reserved_supplies: str = Field(..., description="預訂物資")
    status: str = Field(..., description="狀態")
    reserved_at: str = Field(..., description="預訂時間")
    confirmed_at: Optional[str] = Field(None, description="確認時間")
    picked_up_at: Optional[str] = Field(None, description="領取時間")
    delivered_at: Optional[str] = Field(None, description="配送時間")
    notes: Optional[str] = Field(None, description="備註")


class UserActivityDetail(BaseModel):
    """用戶活動詳細資料"""
    user_id: str = Field(..., description="用戶ID")
    user_name: str = Field(..., description="用戶姓名")
    user_role: str = Field(..., description="用戶角色")
    registered_at: str = Field(..., description="註冊時間")
    activity_count: int = Field(..., description="活動次數")


class DisasterReliefReportData(BaseModel):
    """救災活動報表資料"""
    metadata: ReportMetadata = Field(..., description="報表元資料")
    summary: Dict[str, Any] = Field(..., description="摘要統計")
    task_details: List[TaskDetail] = Field(..., description="任務詳細資料")
    need_details: List[NeedDetail] = Field(..., description="需求詳細資料")


class TaskCompletionReportData(BaseModel):
    """任務完成報表資料"""
    metadata: ReportMetadata = Field(..., description="報表元資料")
    summary: Dict[str, Any] = Field(..., description="摘要統計")
    task_claim_details: List[TaskClaimDetail] = Field(..., description="任務認領詳細資料")


class SupplyFlowReportData(BaseModel):
    """物資流向報表資料"""
    metadata: ReportMetadata = Field(..., description="報表元資料")
    summary: Dict[str, Any] = Field(..., description="摘要統計")
    reservation_details: List[SupplyReservationDetail] = Field(..., description="物資預訂詳細資料")


class SystemUsageReportData(BaseModel):
    """系統使用統計報表資料"""
    metadata: ReportMetadata = Field(..., description="報表元資料")
    summary: Dict[str, Any] = Field(..., description="摘要統計")
    user_activity_details: List[UserActivityDetail] = Field(..., description="用戶活動詳細資料")


class ReportGenerationRequest(BaseModel):
    """報表生成請求"""
    report_type: Literal["disaster_relief", "task_completion", "supply_flow", "system_usage"] = Field(
        ..., description="報表類型"
    )
    query: ReportQuery = Field(..., description="查詢參數")


class ReportGenerationResponse(BaseModel):
    """報表生成回應"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="回應訊息")
    metadata: Optional[ReportMetadata] = Field(None, description="報表元資料")
    download_url: Optional[str] = Field(None, description="下載連結")
    file_name: str = Field(..., description="檔案名稱")


class ReportListItem(BaseModel):
    """報表列表項目"""
    report_id: str = Field(..., description="報表ID")
    report_title: str = Field(..., description="報表標題")
    report_type: str = Field(..., description="報表類型")
    format_type: str = Field(..., description="檔案格式")
    period: ReportPeriod = Field(..., description="報表期間")
    generated_at: str = Field(..., description="生成時間")
    generated_by: str = Field(..., description="生成者")
    file_size: int = Field(..., description="檔案大小(bytes)")
    status: Literal["generating", "completed", "failed"] = Field(..., description="狀態")


class ReportListResponse(BaseModel):
    """報表列表回應"""
    reports: List[ReportListItem] = Field(..., description="報表列表")
    total_count: int = Field(..., description="總數量")
    page: int = Field(..., description="頁碼")
    page_size: int = Field(..., description="每頁數量")


class ReportStatistics(BaseModel):
    """報表統計"""
    total_reports: int = Field(..., description="總報表數")
    reports_by_type: Dict[str, int] = Field(..., description="按類型統計")
    reports_by_format: Dict[str, int] = Field(..., description="按格式統計")
    total_file_size: int = Field(..., description="總檔案大小(bytes)")
    most_popular_type: str = Field(..., description="最受歡迎的報表類型")
    average_generation_time: float = Field(..., description="平均生成時間(秒)")


class ExportOptions(BaseModel):
    """匯出選項"""
    include_summary: bool = Field(True, description="包含摘要")
    include_details: bool = Field(True, description="包含詳細資料")
    max_records: Optional[int] = Field(None, description="最大記錄數")
    sort_by: Optional[str] = Field(None, description="排序欄位")
    sort_order: Literal["asc", "desc"] = Field("desc", description="排序順序")


class BulkReportRequest(BaseModel):
    """批量報表請求"""
    report_types: List[Literal["disaster_relief", "task_completion", "supply_flow", "system_usage"]] = Field(
        ..., description="報表類型列表"
    )
    query: ReportQuery = Field(..., description="查詢參數")
    export_options: Optional[ExportOptions] = Field(None, description="匯出選項")


class BulkReportResponse(BaseModel):
    """批量報表回應"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="回應訊息")
    reports: List[ReportGenerationResponse] = Field(..., description="報表列表")
    zip_download_url: Optional[str] = Field(None, description="打包下載連結")


# 報表模板配置
class ReportTemplate(BaseModel):
    """報表模板"""
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名稱")
    report_type: str = Field(..., description="報表類型")
    description: str = Field(..., description="模板描述")
    default_format: str = Field(..., description="預設格式")
    fields: List[str] = Field(..., description="包含欄位")
    filters: Dict[str, Any] = Field(..., description="預設篩選條件")
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")


class ReportTemplateList(BaseModel):
    """報表模板列表"""
    templates: List[ReportTemplate] = Field(..., description="模板列表")
    total_count: int = Field(..., description="總數量")


# 報表排程配置
class ReportSchedule(BaseModel):
    """報表排程"""
    schedule_id: str = Field(..., description="排程ID")
    schedule_name: str = Field(..., description="排程名稱")
    report_type: str = Field(..., description="報表類型")
    format_type: str = Field(..., description="檔案格式")
    frequency: Literal["daily", "weekly", "monthly"] = Field(..., description="頻率")
    day_of_week: Optional[int] = Field(None, description="星期幾(1-7)")
    day_of_month: Optional[int] = Field(None, description="每月第幾天(1-31)")
    time_of_day: str = Field(..., description="執行時間(HH:MM)")
    recipients: List[str] = Field(..., description="收件人列表")
    is_active: bool = Field(True, description="是否啟用")
    created_at: str = Field(..., description="創建時間")
    last_run_at: Optional[str] = Field(None, description="最後執行時間")
    next_run_at: str = Field(..., description="下次執行時間")


class ReportScheduleList(BaseModel):
    """報表排程列表"""
    schedules: List[ReportSchedule] = Field(..., description="排程列表")
    total_count: int = Field(..., description="總數量")