from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1.api import api_router

app = FastAPI(
    title="光復e互助平台 API",
    description="花蓮光復鄉災害應變數位平台",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "光復e互助平台 API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}