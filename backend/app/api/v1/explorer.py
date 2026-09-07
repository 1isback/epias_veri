from fastapi import APIRouter, HTTPException, Query, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.integrations.epias.client import EpiasClient
from app.integrations.epias.registry import get_endpoint_def

router = APIRouter()

# Maps the dataset ids the frontend dropdown uses to registry endpoint ids.
DATASET_ALIASES = {
    "DayAheadMarket": "ptf",
    "BalancingMarket": "smf",
}


@router.get("/data")
async def get_explorer_data(
    dataset: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
):
    endpoint_id = DATASET_ALIASES.get(dataset, dataset)
    try:
        endpoint_def = get_endpoint_def(endpoint_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        data = await EpiasClient.fetch_data(
            endpoint_id=endpoint_id,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")

    columns = [
        {"field": col["field"], "headerName": col.get("label", col["field"])}
        for col in endpoint_def.metadata.columns
    ]
    return {"columns": columns, "data": data}
