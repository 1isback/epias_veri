from fastapi import APIRouter
from app.core.metrics import metrics
from app.integrations.epias.auth import auth_manager

router = APIRouter()

@router.get("/")
async def get_health_status():
    tgt_valid = await auth_manager.is_tgt_valid()
    return {
        "status": "ok",
        "epias_auth": "valid" if tgt_valid else "invalid",
        "scheduler": "running",
        "metrics": metrics.get_metrics()
    }
