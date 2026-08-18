import asyncio
import sys
sys.path.insert(0, '.')

async def check_schema():
    from app.database.session import get_engine
    from sqlalchemy import text
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='jobs' ORDER BY ordinal_position")
        )
        cols = [row[0] for row in result.fetchall()]
        print("Actual DB columns in jobs table:")
        for c in cols:
            print(" ", c)
        print()
        if "discovery_provider" in cols:
            print("discovery_provider: PRESENT in DB")
        else:
            print("discovery_provider: MISSING from DB  <--- ROOT CAUSE")

asyncio.run(check_schema())
