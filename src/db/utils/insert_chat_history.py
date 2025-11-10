# Cell 4: create + insert + select (all async, all awaited)
from sqlalchemy import select
from src.db.database import AsyncSessionLocal, init_db
from src.db.models import FirstTable

async def insert_into_first_table(name: str = "Temp"):
    await init_db()

    async with AsyncSessionLocal() as session:
        row = FirstTable(name=name)
        session.add(row)
        await session.commit()

        # Because expire_on_commit=False, row.id is usable without triggering a lazy load:
        print("Inserted id:", row.id)

        # Query
        stmt = select(FirstTable).where(FirstTable.name == name)
        res = await session.execute(stmt)
        output = res.scalar_one()
        print("Fetched:", output.id, output.name)

