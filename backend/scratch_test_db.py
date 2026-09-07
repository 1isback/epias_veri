import asyncio
import asyncpg
from urllib.parse import urlparse

async def test_conn():
    db_url = "postgresql://postgres:postgres@localhost:5432/epias_db"
    try:
        conn = await asyncpg.connect(db_url)
        print("CONNECTION_SUCCESS")
        await conn.close()
    except Exception as e:
        print(f"CONNECTION_ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
