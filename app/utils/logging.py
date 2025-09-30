"""
日誌工具
"""
import logging
import sys
from typing import Dict, Any, Optional
from app.core.config import settings

def setup_logging():
    """設定應用程式日誌"""
    # 設定日誌格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 設定日誌等級
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # 配置根日誌記錄器
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 設定第三方套件的日誌等級
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )

def get_logger(name: str) -> logging.Logger:
    """取得指定名稱的日誌記錄器"""
    return logging.getLogger(name)

def log_user_action(
    logger: logging.Logger,
    user_id: str,
    action: str,
    details: Optional[Dict[str, Any]] = None
):
    """記錄用戶操作日誌"""
    log_data = {
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    logger.info(f"User action: {action}", extra=log_data)

def log_system_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
):
    """記錄系統事件日誌"""
    log_data = {
        "event_type": event_type,
        "details": details or {}
    }
    logger.info(f"System event: {event_type} - {message}", extra=log_data)