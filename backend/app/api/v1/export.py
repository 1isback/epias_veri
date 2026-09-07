from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from typing import List, Dict, Any
from app.api.deps import get_current_user
from app.models.user import User
from app.operations.export_service import ExportService

router = APIRouter()

@router.post("/")
async def trigger_export(
    format: str,
    data: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    valid_formats = ["csv", "json", "excel", "xlsx", "parquet"]
    if format not in valid_formats:
        raise HTTPException(status_code=400, detail=f"Unsupported format. Use one of {valid_formats}")
    
    background_tasks.add_task(ExportService.export_async, data, format)
    
    return {"message": f"Export to {format} has been queued."}
