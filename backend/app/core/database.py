import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    # Check if PostgreSQL URL
    if db_url.startswith("postgresql"):
        try:
            logger.info("Attempting to connect to PostgreSQL at %s", db_url)
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            # Test connection
            with engine.connect() as conn:
                logger.info("PostgreSQL connection verified successfully.")
            return engine
        except Exception as e:
            if settings.SQLITE_FALLBACK:
                logger.warning(
                    "Failed to connect to PostgreSQL: %s. Falling back to SQLite at %s",
                    e,
                    settings.SQLITE_URL
                )
                return create_engine(
                    settings.SQLITE_URL,
                    connect_args={"check_same_thread": False}
                )
            else:
                raise e
    else:
        # SQLite or other configured URL
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        return create_engine(db_url, connect_args=connect_args)

engine = get_engine()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models to ensure metadata registration
    import backend.app.models
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
