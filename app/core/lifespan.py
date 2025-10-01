"""
應用程式生命週期管理
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import engine
from app.core.redis import get_redis_client, close_redis_connection
from app.utils.logging import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    logger.info("應用程式啟動中...")
    
    try:
        # 檢查資料庫連線
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("資料庫連線檢查通過")
        
        # 檢查 Redis 連線（開發環境可選）
        try:
            redis_client = get_redis_client()
            redis_client.ping()
            logger.info("Redis 連線檢查通過")
        except Exception as redis_error:
            logger.warning(f"Redis 連線失敗，但繼續啟動: {redis_error}")
        
        logger.info("應用程式啟動完成")
        
    except Exception as e:
        logger.error(f"應用程式啟動失敗: {e}")
        raise
    
    yield
    
    # 關閉時執行
    logger.info("應用程式關閉中...")
    
    try:
        # 關閉 Redis 連線
        try:
            close_redis_connection()
            logger.info("Redis 連線已關閉")
        except Exception as redis_error:
            logger.warning(f"關閉 Redis 連線時發生錯誤: {redis_error}")
        
        # 關閉資料庫連線
        engine.dispose()
        logger.info("資料庫連線已關閉")
        
        logger.info("應用程式關閉完成")
        
    except Exception as e:
        logger.error(f"應用程式關閉時發生錯誤: {e}")