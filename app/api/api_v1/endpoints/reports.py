"""
報表系統 API 端點
"""
import io
from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.models.user import User
from app.services.reporting_service import reporting_service
from app.schemas.reporting import (
    ReportQuery,
    ReportGenerationRequest,
    ReportGenerationResponse,
    ReportMetadata,
    ReportStatistics,
    ExportOptions,
    BulkReportRequest,
    BulkReportResponse
)

router = APIRouter()


@router.post("/generate/disaster-relief", response_model=ReportGenerationResponse)
async def generate_disaster_relief_report(
    query: ReportQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成救災活動報表
    
    - **start_date**: 開始日期
    - **end_date**: 結束日期  
    - **format_type**: 報表格式 (pdf, csv, excel)
    - **需要權限**: 已登入用戶
    - **返回**: 報表生成結果和下載資訊
    """
    try:
        start_datetime = datetime.combine(query.start_date, datetime.min.time())
        end_datetime = datetime.combine(query.end_date, datetime.max.time())
        
        # 生成報表
        report_bytes = reporting_service.generate_disaster_relief_report(
            db, start_datetime, end_datetime, query.format_type
        )
        
        # 建立檔案名稱
        date_str = f"{query.start_date.strftime('%Y%m%d')}-{query.end_date.strftime('%Y%m%d')}"
        file_extension = query.format_type.lower()
        file_name = f"救災活動報表_{date_str}.{file_extension}"
        
        # 建立回應
        metadata = ReportMetadata(
            report_title="救災活動報表",
            report_type="disaster_relief",
            period={
                "start_date": query.start_date.strftime("%Y-%m-%d"),
                "end_date": query.end_date.strftime("%Y-%m-%d"),
                "days": (query.end_date - query.start_date).days
            },
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            generated_by=current_user.name,
            file_size=len(report_bytes),
            format_type=query.format_type
        )
        
        # 設定回應標頭並返回檔案
        media_type_map = {
            "pdf": "application/pdf",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        return StreamingResponse(
            io.BytesIO(report_bytes),
            media_type=media_type_map.get(query.format_type, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"報表生成失敗: {str(e)}")


@router.post("/generate/task-completion", response_model=ReportGenerationResponse)
async def generate_task_completion_report(
    query: ReportQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成任務完成報表
    
    - **start_date**: 開始日期
    - **end_date**: 結束日期
    - **format_type**: 報表格式 (pdf, csv, excel)
    - **需要權限**: 已登入用戶
    - **返回**: 報表生成結果和下載資訊
    """
    try:
        start_datetime = datetime.combine(query.start_date, datetime.min.time())
        end_datetime = datetime.combine(query.end_date, datetime.max.time())
        
        # 生成報表
        report_bytes = reporting_service.generate_task_completion_report(
            db, start_datetime, end_datetime, query.format_type
        )
        
        # 建立檔案名稱
        date_str = f"{query.start_date.strftime('%Y%m%d')}-{query.end_date.strftime('%Y%m%d')}"
        file_extension = query.format_type.lower()
        file_name = f"任務完成報表_{date_str}.{file_extension}"
        
        # 設定回應標頭並返回檔案
        media_type_map = {
            "pdf": "application/pdf",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        return StreamingResponse(
            io.BytesIO(report_bytes),
            media_type=media_type_map.get(query.format_type, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"報表生成失敗: {str(e)}")


@router.post("/generate/supply-flow", response_model=ReportGenerationResponse)
async def generate_supply_flow_report(
    query: ReportQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成物資流向報表
    
    - **start_date**: 開始日期
    - **end_date**: 結束日期
    - **format_type**: 報表格式 (pdf, csv, excel)
    - **需要權限**: 已登入用戶
    - **返回**: 報表生成結果和下載資訊
    """
    try:
        start_datetime = datetime.combine(query.start_date, datetime.min.time())
        end_datetime = datetime.combine(query.end_date, datetime.max.time())
        
        # 生成報表
        report_bytes = reporting_service.generate_supply_flow_report(
            db, start_datetime, end_datetime, query.format_type
        )
        
        # 建立檔案名稱
        date_str = f"{query.start_date.strftime('%Y%m%d')}-{query.end_date.strftime('%Y%m%d')}"
        file_extension = query.format_type.lower()
        file_name = f"物資流向報表_{date_str}.{file_extension}"
        
        # 設定回應標頭並返回檔案
        media_type_map = {
            "pdf": "application/pdf",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        return StreamingResponse(
            io.BytesIO(report_bytes),
            media_type=media_type_map.get(query.format_type, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"報表生成失敗: {str(e)}")


@router.post("/generate/system-usage", response_model=ReportGenerationResponse)
async def generate_system_usage_report(
    query: ReportQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    生成系統使用統計報表
    
    - **start_date**: 開始日期
    - **end_date**: 結束日期
    - **format_type**: 報表格式 (pdf, csv, excel)
    - **需要權限**: 管理員
    - **返回**: 報表生成結果和下載資訊
    """
    try:
        start_datetime = datetime.combine(query.start_date, datetime.min.time())
        end_datetime = datetime.combine(query.end_date, datetime.max.time())
        
        # 生成報表
        report_bytes = reporting_service.generate_system_usage_report(
            db, start_datetime, end_datetime, query.format_type
        )
        
        # 建立檔案名稱
        date_str = f"{query.start_date.strftime('%Y%m%d')}-{query.end_date.strftime('%Y%m%d')}"
        file_extension = query.format_type.lower()
        file_name = f"系統使用統計報表_{date_str}.{file_extension}"
        
        # 設定回應標頭並返回檔案
        media_type_map = {
            "pdf": "application/pdf",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        return StreamingResponse(
            io.BytesIO(report_bytes),
            media_type=media_type_map.get(query.format_type, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"報表生成失敗: {str(e)}")


@router.post("/generate/bulk")
async def generate_bulk_reports(
    request: BulkReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量生成報表
    
    - **report_types**: 報表類型列表
    - **query**: 查詢參數
    - **export_options**: 匯出選項
    - **需要權限**: 已登入用戶（系統使用報表需要管理員權限）
    - **返回**: 批量報表生成結果
    """
    try:
        start_datetime = datetime.combine(request.query.start_date, datetime.min.time())
        end_datetime = datetime.combine(request.query.end_date, datetime.max.time())
        
        reports = []
        
        for report_type in request.report_types:
            # 檢查權限
            if report_type == "system_usage" and current_user.role != "admin":
                continue
            
            try:
                # 根據報表類型生成報表
                if report_type == "disaster_relief":
                    report_bytes = reporting_service.generate_disaster_relief_report(
                        db, start_datetime, end_datetime, request.query.format_type
                    )
                    title = "救災活動報表"
                elif report_type == "task_completion":
                    report_bytes = reporting_service.generate_task_completion_report(
                        db, start_datetime, end_datetime, request.query.format_type
                    )
                    title = "任務完成報表"
                elif report_type == "supply_flow":
                    report_bytes = reporting_service.generate_supply_flow_report(
                        db, start_datetime, end_datetime, request.query.format_type
                    )
                    title = "物資流向報表"
                elif report_type == "system_usage":
                    report_bytes = reporting_service.generate_system_usage_report(
                        db, start_datetime, end_datetime, request.query.format_type
                    )
                    title = "系統使用統計報表"
                else:
                    continue
                
                # 建立檔案名稱
                date_str = f"{request.query.start_date.strftime('%Y%m%d')}-{request.query.end_date.strftime('%Y%m%d')}"
                file_extension = request.query.format_type.lower()
                file_name = f"{title}_{date_str}.{file_extension}"
                
                # 建立報表回應
                metadata = ReportMetadata(
                    report_title=title,
                    report_type=report_type,
                    period={
                        "start_date": request.query.start_date.strftime("%Y-%m-%d"),
                        "end_date": request.query.end_date.strftime("%Y-%m-%d"),
                        "days": (request.query.end_date - request.query.start_date).days
                    },
                    generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    generated_by=current_user.name,
                    file_size=len(report_bytes),
                    format_type=request.query.format_type
                )
                
                reports.append(ReportGenerationResponse(
                    success=True,
                    message="報表生成成功",
                    metadata=metadata,
                    file_name=file_name
                ))
                
            except Exception as e:
                reports.append(ReportGenerationResponse(
                    success=False,
                    message=f"報表生成失敗: {str(e)}",
                    file_name=f"{report_type}_error.txt"
                ))
        
        return BulkReportResponse(
            success=True,
            message=f"批量報表生成完成，成功生成 {len([r for r in reports if r.success])} 個報表",
            reports=reports
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量報表生成失敗: {str(e)}")


@router.get("/statistics", response_model=ReportStatistics)
async def get_report_statistics(
    days: int = Query(30, ge=1, le=365, description="統計天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    獲取報表統計資訊
    
    - **days**: 統計天數
    - **需要權限**: 管理員
    - **返回**: 報表統計資訊
    """
    try:
        # 這裡可以實作報表使用統計的邏輯
        # 由於目前沒有報表歷史記錄表，這裡返回模擬資料
        
        return ReportStatistics(
            total_reports=0,
            reports_by_type={
                "disaster_relief": 0,
                "task_completion": 0,
                "supply_flow": 0,
                "system_usage": 0
            },
            reports_by_format={
                "pdf": 0,
                "csv": 0,
                "excel": 0
            },
            total_file_size=0,
            most_popular_type="disaster_relief",
            average_generation_time=2.5
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取報表統計失敗: {str(e)}")


@router.get("/templates")
async def get_report_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取報表模板列表
    
    - **需要權限**: 已登入用戶
    - **返回**: 可用的報表模板列表
    """
    templates = [
        {
            "template_id": "disaster_relief_basic",
            "template_name": "基本救災活動報表",
            "report_type": "disaster_relief",
            "description": "包含任務、需求和物資的基本統計資訊",
            "default_format": "pdf",
            "fields": ["tasks", "needs", "supplies", "summary"],
            "filters": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        },
        {
            "template_id": "task_completion_detailed",
            "template_name": "詳細任務完成報表",
            "report_type": "task_completion",
            "description": "包含任務完成詳情和志工效率分析",
            "default_format": "excel",
            "fields": ["task_claims", "volunteer_efficiency", "completion_trends"],
            "filters": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        },
        {
            "template_id": "supply_flow_analysis",
            "template_name": "物資流向分析報表",
            "report_type": "supply_flow",
            "description": "分析物資預訂、配送和使用情況",
            "default_format": "pdf",
            "fields": ["reservations", "delivery_efficiency", "station_activity"],
            "filters": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
    ]
    
    return {
        "templates": templates,
        "total_count": len(templates)
    }


@router.get("/health")
async def reporting_health_check():
    """
    報表系統健康檢查
    
    - **返回**: 報表系統狀態
    """
    return {
        "status": "healthy",
        "service": "reporting",
        "timestamp": datetime.utcnow().isoformat(),
        "supported_formats": ["pdf", "csv", "excel"],
        "available_reports": [
            "disaster_relief",
            "task_completion", 
            "supply_flow",
            "system_usage"
        ]
    }


# 快速報表端點
@router.get("/quick/disaster-relief-summary")
async def get_quick_disaster_relief_summary(
    days: int = Query(7, ge=1, le=30, description="查詢天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    快速獲取救災活動摘要
    
    - **days**: 查詢天數
    - **需要權限**: 已登入用戶
    - **返回**: 救災活動摘要資料
    """
    try:
        from app.services.monitoring_service import monitoring_service
        
        # 獲取救災進度資料
        progress = monitoring_service.get_disaster_relief_progress(db, days)
        
        return {
            "period_days": days,
            "task_summary": {
                "total_tasks": progress["task_progress"]["total_tasks"],
                "completed_tasks": progress["task_progress"]["completed_tasks"],
                "completion_rate": progress["task_progress"]["completion_rate"]
            },
            "need_summary": {
                "total_needs": progress["need_progress"]["total_needs"],
                "resolved_needs": progress["need_progress"]["resolved_needs"],
                "resolution_rate": progress["need_progress"]["resolution_rate"]
            },
            "overall_completion_rate": progress["overall_completion"]["overall_completion_rate"],
            "urgent_items": progress["urgency_analysis"]["total_urgent_items"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取摘要資料失敗: {str(e)}")


@router.get("/quick/task-completion-summary")
async def get_quick_task_completion_summary(
    days: int = Query(7, ge=1, le=30, description="查詢天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    快速獲取任務完成摘要
    
    - **days**: 查詢天數
    - **需要權限**: 已登入用戶
    - **返回**: 任務完成摘要資料
    """
    try:
        from app.services.monitoring_service import monitoring_service
        
        # 獲取任務完成統計
        stats = monitoring_service.get_task_completion_statistics(db, days)
        
        return {
            "period_days": days,
            "overall_stats": stats["overall"],
            "top_task_types": stats["by_task_type"][:5],  # 前5種任務類型
            "volunteer_efficiency": {
                "active_volunteers": stats["volunteer_efficiency"]["active_volunteers"],
                "avg_tasks_per_volunteer": stats["volunteer_efficiency"]["avg_tasks_per_volunteer"],
                "top_volunteers_count": len(stats["volunteer_efficiency"]["top_volunteers"])
            },
            "average_completion_time_hours": stats["average_completion_time_hours"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取摘要資料失敗: {str(e)}")


@router.post("/export/{data_type}")
async def export_data(
    data_type: str,
    query: ReportQuery,
    filters: dict = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    按類型匯出資料
    
    - **data_type**: 資料類型 (tasks, needs, supplies, users, logs)
    - **query**: 查詢參數
    - **filters**: 額外篩選條件
    - **需要權限**: 已登入用戶（logs需要管理員權限）
    - **返回**: 匯出檔案
    """
    try:
        # 檢查權限
        if data_type == "logs" and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理員權限才能匯出系統日誌")
        
        if data_type == "users" and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理員權限才能匯出用戶資料")
        
        start_datetime = datetime.combine(query.start_date, datetime.min.time())
        end_datetime = datetime.combine(query.end_date, datetime.max.time())
        
        # 匯出資料
        export_bytes = reporting_service.export_data_by_type(
            db, data_type, start_datetime, end_datetime, query.format_type, filters
        )
        
        # 建立檔案名稱
        date_str = f"{query.start_date.strftime('%Y%m%d')}-{query.end_date.strftime('%Y%m%d')}"
        file_extension = query.format_type.lower()
        file_name = f"{data_type}_export_{date_str}.{file_extension}"
        
        # 設定回應標頭並返回檔案
        media_type_map = {
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "json": "application/json"
        }
        
        return StreamingResponse(
            io.BytesIO(export_bytes),
            media_type=media_type_map.get(query.format_type, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"資料匯出失敗: {str(e)}")


@router.post("/generate/comprehensive-analysis")
async def generate_comprehensive_analysis_report(
    query: ReportQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    生成綜合分析報表
    
    - **start_date**: 開始日期
    - **end_date**: 結束日期
    - **format_type**: 報表格式 (pdf, csv, excel)
    - **需要權限**: 管理員
    - **返回**: 報表生成結果和下載資訊
    """
    try:
        start_datetime = datetime.combine(query.start_date, datetime.min.time())
        end_datetime = datetime.combine(query.end_date, datetime.max.time())
        
        # 生成報表
        report_bytes = reporting_service.generate_comprehensive_analysis_report(
            db, start_datetime, end_datetime, query.format_type
        )
        
        # 建立檔案名稱
        date_str = f"{query.start_date.strftime('%Y%m%d')}-{query.end_date.strftime('%Y%m%d')}"
        file_extension = query.format_type.lower()
        file_name = f"綜合分析報表_{date_str}.{file_extension}"
        
        # 設定回應標頭並返回檔案
        media_type_map = {
            "pdf": "application/pdf",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        return StreamingResponse(
            io.BytesIO(report_bytes),
            media_type=media_type_map.get(query.format_type, "application/octet-stream"),
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"報表生成失敗: {str(e)}")


@router.get("/analytics/trends")
async def get_analytics_trends(
    days: int = Query(30, ge=7, le=365, description="分析天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取趨勢分析資料
    
    - **days**: 分析天數
    - **需要權限**: 已登入用戶
    - **返回**: 趨勢分析資料
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 收集趨勢資料
        daily_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # 每日統計
            daily_tasks = db.query(Task).filter(
                Task.created_at >= current_date,
                Task.created_at < next_date
            ).count()
            
            daily_needs = db.query(Need).filter(
                Need.created_at >= current_date,
                Need.created_at < next_date
            ).count()
            
            completed_tasks = db.query(TaskClaim).filter(
                TaskClaim.completed_at >= current_date,
                TaskClaim.completed_at < next_date,
                TaskClaim.status == "completed"
            ).count()
            
            daily_stats.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "new_tasks": daily_tasks,
                "new_needs": daily_needs,
                "completed_tasks": completed_tasks,
                "total_activity": daily_tasks + daily_needs
            })
            
            current_date = next_date
        
        # 計算趨勢指標
        if len(daily_stats) >= 7:
            recent_week = daily_stats[-7:]
            previous_week = daily_stats[-14:-7] if len(daily_stats) >= 14 else daily_stats[:-7]
            
            recent_avg = sum(day["total_activity"] for day in recent_week) / len(recent_week)
            previous_avg = sum(day["total_activity"] for day in previous_week) / len(previous_week) if previous_week else recent_avg
            
            trend_change = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        else:
            trend_change = 0
        
        return {
            "period_days": days,
            "daily_statistics": daily_stats,
            "trend_analysis": {
                "trend_change_percentage": round(trend_change, 2),
                "trend_direction": "上升" if trend_change > 5 else "下降" if trend_change < -5 else "穩定"
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取趨勢分析失敗: {str(e)}")


@router.get("/analytics/performance")
async def get_performance_analytics(
    days: int = Query(30, ge=7, le=365, description="分析天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    獲取效能分析資料
    
    - **days**: 分析天數
    - **需要權限**: 已登入用戶
    - **返回**: 效能分析資料
    """
    try:
        from app.services.monitoring_service import monitoring_service
        
        # 獲取效能統計
        task_stats = monitoring_service.get_task_completion_statistics(db, days)
        supply_stats = monitoring_service.get_supply_flow_monitoring(db, days)
        
        # 計算關鍵效能指標
        kpis = {
            "task_completion_rate": task_stats["overall"]["completion_rate"],
            "average_task_completion_time": task_stats["average_completion_time_hours"],
            "active_volunteers": task_stats["volunteer_efficiency"]["active_volunteers"],
            "supply_delivery_efficiency": supply_stats["delivery_efficiency"]["avg_delivery_time_hours"],
            "station_utilization": len(supply_stats["station_activity"]["active_stations"])
        }
        
        # 效能等級評估
        performance_score = 0
        if kpis["task_completion_rate"] >= 80:
            performance_score += 25
        elif kpis["task_completion_rate"] >= 60:
            performance_score += 15
        
        if kpis["average_task_completion_time"] <= 24:
            performance_score += 25
        elif kpis["average_task_completion_time"] <= 48:
            performance_score += 15
        
        if kpis["active_volunteers"] >= 10:
            performance_score += 25
        elif kpis["active_volunteers"] >= 5:
            performance_score += 15
        
        if kpis["supply_delivery_efficiency"] <= 12:
            performance_score += 25
        elif kpis["supply_delivery_efficiency"] <= 24:
            performance_score += 15
        
        performance_level = "優秀" if performance_score >= 80 else "良好" if performance_score >= 60 else "需改善"
        
        return {
            "period_days": days,
            "key_performance_indicators": kpis,
            "performance_score": performance_score,
            "performance_level": performance_level,
            "recommendations": [
                "增加志工招募活動" if kpis["active_volunteers"] < 10 else None,
                "優化任務分配流程" if kpis["task_completion_rate"] < 80 else None,
                "改善物資配送效率" if kpis["supply_delivery_efficiency"] > 24 else None
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取效能分析失敗: {str(e)}")