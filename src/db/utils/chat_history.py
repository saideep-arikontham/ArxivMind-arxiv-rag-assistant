from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import AsyncSessionLocal
from src.db.models import FirstTable, ChatHistory
from datetime import datetime

async def insert_into_first_table(name: str = "Temp", session: Optional[AsyncSession] = None) -> int:
    """
    Insert a row into first_table and return the inserted id.
    If a session is provided, reuse it. Otherwise create a short-lived one.
    """
    if session is not None:
        row = FirstTable(name=name)
        session.add(row)
        await session.commit()
        return row.id

    async with AsyncSessionLocal() as local_sess:
        row = FirstTable(name=name)
        local_sess.add(row)
        await local_sess.commit()

        # Optional verification (reads the row we just wrote)
        res = await local_sess.execute(select(FirstTable).where(FirstTable.id == row.id))
        saved = res.scalar_one()
        return saved.id


async def insert_into_chat_history(
    user_query: str,
    model_response: str,
    model_used: str,
    user_query_timestamp: Optional[datetime] = None,
    model_response_timestamp: Optional[datetime] = None,
    session: Optional[AsyncSession] = None,
) -> int:


    if session is not None:
        entry = ChatHistory(
            user_query=user_query,
            model_response=model_response,
            model_used=model_used,
            user_query_timestamp=user_query_timestamp,
            model_response_timestamp=model_response_timestamp,
        )
        session.add(entry)
        await session.commit()
        return entry.id

    async with AsyncSessionLocal() as local_session:
        entry = ChatHistory(
            user_query=user_query,
            model_response=model_response,
            model_used=model_used,
            user_query_timestamp=user_query_timestamp,
            model_response_timestamp=model_response_timestamp,
        )
        local_session.add(entry)
        await local_session.commit()
        return entry.id
