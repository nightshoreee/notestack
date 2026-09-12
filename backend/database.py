"""
SQLAlchemy engine + session setup. get_db() is used as a FastAPI dependency
in every router so each request gets its own DB session that's cleanly
closed afterward.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

# check_same_thread=False is required for SQLite + FastAPI's threaded request handling
engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
