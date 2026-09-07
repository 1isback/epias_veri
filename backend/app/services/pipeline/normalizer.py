from typing import List, Dict, Any
from datetime import datetime

from app.models.market import PTFData
from app.models.raw import SyncJob

class Normalizer:
    @staticmethod
    def normalize_ptf(records: List[Dict[str, Any]], sync_job: SyncJob) -> List[PTFData]:
        normalized = []
        for record in records:
            try:
                # Handle ISO format with timezone
                dt = datetime.fromisoformat(record["date"])
            except (ValueError, KeyError):
                continue
                
            ptf = PTFData(
                timestamp=dt,
                price_tl=float(record.get("price", 0)),
                price_usd=float(record.get("priceUsd", 0)),
                price_eur=float(record.get("priceEur", 0)),
                dataset_id=sync_job.dataset_id,
                dataset_version_id=sync_job.dataset_version_id,
                sync_job_id=sync_job.id
            )
            normalized.append(ptf)
        return normalized
