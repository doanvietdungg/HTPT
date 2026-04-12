import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

def create_db_engine(retries: int = 10, delay: int = 3):
    """
    Create engine with retry logic — waits for MySQL to be ready on startup.
    """
    for attempt in range(retries):
        try:
            engine = create_engine(
                settings.DB_URL,
                pool_pre_ping=True,       # auto-reconnect if connection dropped
                pool_recycle=300,          # recycle connections every 5 min
                pool_size=5,
                max_overflow=10,
            )
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"[DB] Connected to MySQL successfully on attempt {attempt + 1}")
            return engine
        except Exception as e:
            logger.warning(f"[DB] MySQL not ready (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise RuntimeError(f"Could not connect to MySQL after {retries} attempts") from e

engine = create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
