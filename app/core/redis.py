import redis
from typing import Optional
from app.core.config import settings

# Redis 連線池
redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """取得 Redis 客戶端"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    return redis_client

def close_redis_connection():
    """關閉 Redis 連線"""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None