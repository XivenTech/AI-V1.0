import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


# 确保 sqlite 存储目录存在
db_url = os.getenv("DATABASE_URL", "sqlite:///./data/factory.db")
if db_url.startswith("sqlite:///"):
    sqlite_path = db_url.replace("sqlite:///", "")
    parent_dir = Path(sqlite_path).parent
    parent_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    echo=False,
    future=True
)

# 为 SQLite 开启外键约束支持
if "sqlite" in db_url:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
