from fastapi import APIRouter

api_router = APIRouter()

# 未來將在此處包含各個功能模組的路由
# api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# api_router.include_router(needs.router, prefix="/needs", tags=["needs"])
# api_router.include_router(supplies.router, prefix="/supplies", tags=["supplies"])

@api_router.get("/")
async def api_info():
    return {"message": "災害救援平台 API v1", "status": "active"}