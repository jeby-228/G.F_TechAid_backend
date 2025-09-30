from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 建立資料庫引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG
)

# 建立會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立基礎模型類別
Base = declarative_base()

# 資料庫依賴注入
def get_db():
    """取得資料庫會話的依賴注入函數"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 資料庫會話管理類別
class DatabaseManager:
    """資料庫會話管理器"""
    
    @staticmethod
    def create_tables():
        """建立所有資料表"""
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def drop_tables():
        """刪除所有資料表"""
        Base.metadata.drop_all(bind=engine)
    
    @staticmethod
    def get_session():
        """取得資料庫會話"""
        return SessionLocal()
    
    @staticmethod
    def close_session(db):
        """關閉資料庫會話"""
        if db:
            db.close()


# 資料庫連線測試函數
def test_database_connection():
    """測試資料庫連線"""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        # 執行簡單查詢測試連線
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"資料庫連線失敗: {e}")
        return False