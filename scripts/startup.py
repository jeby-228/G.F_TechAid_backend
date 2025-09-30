#!/usr/bin/env python3
"""
應用程式啟動腳本
"""
import asyncio
import logging
from app.core.database import engine, Base
from app.core.redis import get_redis_client, close_redis_connection
from app.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

async def check_database_connection():
    """檢查資料庫連線"""
    try:
        # 測試資料庫連線
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("資料庫連線成功")
        return True
    except Exception as e:
        logger.error(f"資料庫連線失敗: {e}")
        return False

async def check_redis_connection():
    """檢查 Redis 連線"""
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        logger.info("Redis 連線成功")
        return True
    except Exception as e:
        logger.error(f"Redis 連線失敗: {e}")
        return False
    finally:
        close_redis_connection()

async def create_tables():
    """建立資料庫表格（僅用於開發環境）"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("資料庫表格建立成功")
        return True
    except Exception as e:
        logger.error(f"資料庫表格建立失敗: {e}")
        return False

async def startup_checks():
    """啟動前檢查"""
    logger.info("開始啟動檢查...")
    
    # 檢查資料庫連線
    if not await check_database_connection():
        logger.error("資料庫連線檢查失敗")
        return False
    
    # 檢查 Redis 連線
    if not await check_redis_connection():
        logger.error("Redis 連線檢查失敗")
        return False
    
    logger.info("所有啟動檢查通過")
    return True

if __name__ == "__main__":
    # 設定日誌
    setup_logging()
    
    # 執行啟動檢查
    success = asyncio.run(startup_checks())
    
    if success:
        logger.info("應用程式準備就緒")
        exit(0)
    else:
        logger.error("啟動檢查失敗")
        exit(1)