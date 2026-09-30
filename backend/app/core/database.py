from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

Base = declarative_base()

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"[Warning] Failed to initialize SQLAlchemy engine: {e}")
    engine = None
    SessionLocal = None

def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database engine is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_health() -> bool:
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[HealthCheck] Database connection check failed: {e}")
        return False

check_db_connection = check_db_health

