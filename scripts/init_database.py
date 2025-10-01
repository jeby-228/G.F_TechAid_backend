#!/usr/bin/env python3
"""
資料庫初始化腳本
用於建立資料庫表格和插入初始資料
"""

import sys
import os
from pathlib import Path

# 將專案根目錄加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import DatabaseManager, test_database_connection
from app.core.config import settings
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化資料庫"""
    logger.info("開始初始化資料庫...")
    
    # 測試資料庫連線
    logger.info("測試資料庫連線...")
    if not test_database_connection():
        logger.error("資料庫連線失敗，請檢查資料庫設定")
        return False
    
    logger.info("資料庫連線成功")
    
    try:
        # 建立資料表
        logger.info("建立資料表...")
        DatabaseManager.create_tables()
        logger.info("資料表建立完成")
        
        logger.info("資料庫初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {e}")
        return False


def reset_database():
    """重置資料庫（刪除所有資料表後重新建立）"""
    logger.warning("警告：這將刪除所有現有資料！")
    
    try:
        # 刪除所有資料表
        logger.info("刪除現有資料表...")
        DatabaseManager.drop_tables()
        logger.info("資料表刪除完成")
        
        # 重新建立資料表
        return init_database()
        
    except Exception as e:
        logger.error(f"資料庫重置失敗: {e}")
        return False


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="資料庫初始化工具")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="重置資料庫（刪除所有資料表後重新建立）"
    )
    
    args = parser.parse_args()
    
    logger.info(f"資料庫 URL: {settings.DATABASE_URL}")
    
    if args.reset:
        success = reset_database()
    else:
        success = init_database()
    
    if success:
        logger.info("操作完成")
        sys.exit(0)
    else:
        logger.error("操作失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()