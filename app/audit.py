import os
import json
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, DateTime, Text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from .models import ActionRequest

DATABASE_URL = os.getenv("AUDIT_DB_URL", "sqlite+aiosqlite:///./audit.db")

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class AuditEntry(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_email = Column(String)
    action = Column(String)
    org = Column(String)
    repo = Column(String)
    parameters = Column(Text)
    result = Column(String)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def log_action(user: dict, action: ActionRequest, result: str):
    async with SessionLocal() as session:
        record = AuditEntry(
            user_email=user.get("email"),
            action=action.action,
            org=action.org,
            repo=action.repo,
            parameters=json.dumps(action.parameters),
            result=result
        )
        session.add(record)
        await session.commit()

async def query_audit_logs(
    email: Optional[str] = None,
    action: Optional[str] = None,
    org: Optional[str] = None,
    repo: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[dict]:
    async with SessionLocal() as session:
        stmt = select(AuditEntry)

        if email:
            stmt = stmt.where(AuditEntry.user_email == email)
        if action:
            stmt = stmt.where(AuditEntry.action == action)
        if org:
            stmt = stmt.where(AuditEntry.org == org)
        if repo:
            stmt = stmt.where(AuditEntry.repo == repo)

        stmt = stmt.order_by(AuditEntry.timestamp.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        return [entry_to_dict(e) for e in result.scalars().all()]

def entry_to_dict(entry: AuditEntry) -> dict:
    return {
        "timestamp": entry.timestamp.isoformat(),
        "email": entry.user_email,
        "action": entry.action,
        "org": entry.org,
        "repo": entry.repo,
        "parameters": entry.parameters,
        "result": entry.result
    }
