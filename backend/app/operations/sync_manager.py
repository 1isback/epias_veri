import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sync_service import SyncService
from app.core.logger import log, set_correlation_id
from app.core.metrics import metrics

class SyncManager:
    """
    Wraps Phase 2 SyncService to provide operational features:
    Queueing, overlap prevention, retries.
    """
    def __init__(self):
        self.active_syncs = set()

    async def execute_sync(self, session: AsyncSession, endpoint_id: str, start_date: str, end_date: str, dataset_id: str = None, dataset_version_id: str = None) -> bool:
        if endpoint_id in self.active_syncs:
            log.warning(f"Sync for {endpoint_id} is already running. Skipping execution to prevent overlap.")
            return False

        set_correlation_id()
        self.active_syncs.add(endpoint_id)
        metrics.inc_scheduler_execution()
        
        sync_service = SyncService(session)
        max_retries = 3
        
        try:
            for attempt in range(max_retries):
                try:
                    job = await sync_service.sync_endpoint(endpoint_id, start_date, end_date, dataset_id, dataset_version_id)
                    if job.status == "SUCCESS":
                        log.info(f"SyncManager successfully completed sync for {endpoint_id}")
                        return True
                    else:
                        log.warning(f"SyncManager attempt {attempt+1} failed for {endpoint_id}. Retrying...")
                except Exception as e:
                    log.error(f"SyncManager attempt {attempt+1} encountered error for {endpoint_id}: {str(e)}")
                
                await asyncio.sleep(2 ** attempt)
            
            log.error(f"SyncManager permanently failed for {endpoint_id} after {max_retries} attempts.")
            metrics.inc_failed_import()
            return False
            
        finally:
            self.active_syncs.remove(endpoint_id)

sync_manager = SyncManager()
