"""Configuração do banco de dados SQLite assíncrono com SQLAlchemy."""

from __future__ import annotations
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from sqlite3 import Connection as SQLite3Connection

DB_PATH = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vespera.db")

engine = create_async_engine(
    DB_PATH,
    echo=False,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Habilita modo WAL (Write-Ahead Logging) e chaves estrangeiras no SQLite."""
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def init_db() -> None:
    """Cria todas as tabelas caso não existam."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
