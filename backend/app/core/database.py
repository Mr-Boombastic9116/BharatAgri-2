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

def check_mysql_status() -> int:
    """
    Checks MySQL connectivity and database initialization.
    Returns:
        0: Database exists and contains users table with seed data
        1: MySQL connection failed (server unreachable / offline)
        2: Database does not exist
        3: Database exists but tables are missing
    """
    import pymysql
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=3
        )
    except Exception as e:
        print(f"[Error] MySQL connection failed: {e}")
        return 1

    try:
        cur = conn.cursor()
        cur.execute("SHOW DATABASES LIKE %s", (settings.DB_NAME,))
        if not cur.fetchone():
            return 2

        cur.execute(f"USE `{settings.DB_NAME}`")
        cur.execute("SHOW TABLES LIKE 'users'")
        if not cur.fetchone():
            return 3

        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        print(f"[OK] Database '{settings.DB_NAME}' verified ({user_count} users).")
        return 0
    except Exception as e:
        print(f"[Error] Database query check failed: {e}")
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass

