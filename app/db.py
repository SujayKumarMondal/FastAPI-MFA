import logging
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from .core import settings

logger = logging.getLogger("app.db")

DATABASE_URL = settings.database_url

engine = create_engine(DATABASE_URL, echo=False)
logger.info("Database configured for engine=%s host=%s db=%s schema=%s", settings.DB_ENGINE, settings.DB_HOST, settings.DB_NAME, settings.DB_SCHEMA)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    # If a Postgres schema is configured, ensure it exists and use it
    if settings.DB_ENGINE and settings.DB_ENGINE.startswith("postgres") and settings.DB_SCHEMA:
        with engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.DB_SCHEMA}"))
            conn.execute(text(f"SET search_path TO {settings.DB_SCHEMA}"))
            SQLModel.metadata.create_all(bind=conn)
    else:
        SQLModel.metadata.create_all(engine)
