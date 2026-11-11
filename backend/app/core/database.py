import logging
from typing import Any, Dict

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from backend.app.core.config import settings, resolve_path

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine():
    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() == "sqlite":
        if url.database and url.database != ":memory:":
            url = url.set(database=resolve_path(url.database))
        logger.info("Using SQLite database at %s (local development mode)", url.database)
        eng = create_engine(url, connect_args={"check_same_thread": False})

        from sqlalchemy import event

        @event.listens_for(eng, "connect")
        def _sqlite_enable_foreign_keys(dbapi_conn, connection_record):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")

        return eng

    logger.info("Using %s database at %s", url.get_backend_name(), url.render_as_string(hide_password=True))
    return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20)


engine = get_engine()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database() -> Dict[str, Any]:
    """Run a real round-trip query and report the outcome."""
    info: Dict[str, Any] = {"backend": engine.dialect.name}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        info["status"] = "CONNECTED"
    except Exception as e:
        info["status"] = "UNAVAILABLE"
        info["error"] = str(e).splitlines()[0]
    return info


def init_db():
    """Bring the schema to the latest Alembic revision (the single source of schema truth)."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect
    from backend.app.core.config import PROJECT_ROOT

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "database" / "migrations"))
    cfg.attributes["configure_logging"] = False

    tables = set(inspect(engine).get_table_names())
    if "plants" in tables and "alembic_version" not in tables:
        # Schema created before migrations were used; record it as current instead of re-creating tables.
        command.stamp(cfg, "head")
        logger.info("Existing unversioned schema stamped at Alembic head.")
    else:
        command.upgrade(cfg, "head")
    logger.info("Database schema is at Alembic head.")
