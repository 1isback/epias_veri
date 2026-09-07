import asyncio
from datetime import datetime
from app.integrations.epias.client import EpiasClient

async def test_epias():
    today = datetime.now().strftime("%Y-%m-%dT00:00:00+03:00")
    print(f"Fetching PTF for {today}")
    
    try:
        results = await EpiasClient.fetch_data(
            endpoint_id="ptf",
            start_date=today,
            end_date=today
        )
        print(f"Got {len(results)} records.")
        if results:
            print(results[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_epias())
