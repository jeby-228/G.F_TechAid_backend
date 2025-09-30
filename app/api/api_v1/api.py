from fastapi import APIRouter
from app.api.api_v1.endpoints import auth, users, organization_approval, needs, tasks, supplies, notifications, announcements, locations, shelters, monitoring, reports

api_router = APIRouter()

# 包含身分驗證路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# 包含用戶管理路由
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 包含組織審核路由
api_router.include_router(organization_approval.router, prefix="/organization-approval", tags=["organization-approval"])

# 包含需求管理路由
api_router.include_router(needs.router, prefix="/needs", tags=["needs"])

# 包含任務管理路由
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# 包含物資管理路由
api_router.include_router(supplies.router, prefix="/supplies", tags=["supplies"])

# 包含通知管理路由
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# 包含公告管理路由
api_router.include_router(announcements.router, prefix="/announcements", tags=["announcements"])

# 包含地理位置服務路由
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])

# 包含避難所管理路由
api_router.include_router(shelters.router, prefix="/shelters", tags=["shelters"])

# 包含監控系統路由
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

# 包含報表系統路由
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

@api_router.get("/")
async def api_info():
    return {"message": "災害救援平台 API v1", "status": "active"}