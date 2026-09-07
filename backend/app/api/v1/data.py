from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict, Any

from app.api.deps import get_current_user
from app.models.user import User
from app.integrations.epias.client import EpiasClient
from app.integrations.epias.registry import get_endpoint_def

router = APIRouter()

@router.get("/{endpoint_id}", response_model=List[Dict[str, Any]])
async def get_epias_data(
    endpoint_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
):
    """
    Generic endpoint to fetch data from EPİAŞ based on registry configuration.
    The backend automatically handles:
    - Authentication (TGT)
    - 90-day Partitioning & Merging
    - Rate limits & Retries
    """
    try:
        # Validate endpoint exists early
        _ = get_endpoint_def(endpoint_id)
        
        # Fetch data
        data = await EpiasClient.fetch_data(
            endpoint_id=endpoint_id,
            start_date=start_date,
            end_date=end_date
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # In production, we'd log this properly and not expose raw errors.
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")
