import logging
import time
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.epias.client import EpiasClient
from app.models.raw import SyncJob, RawImport
from app.repositories.sync_repo import SyncJobRepository, RawImportRepository
from app.services.pipeline.validator import Validator
from app.services.pipeline.normalizer import Normalizer

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = SyncJobRepository(session)
        self.raw_repo = RawImportRepository(session)
        
    async def sync_endpoint(self, endpoint_id: str, start_date: str, end_date: str, dataset_id: str = None, dataset_version_id: str = None) -> SyncJob:
        start_time = time.time()
        
        # 1. Create SyncJob
        # Make timezone-aware UTC datetime so SQLAlchemy DateTime(timezone=True) won't complain
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        
        job = SyncJob(
            endpoint_id=endpoint_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            requested_start=start_dt,
            requested_end=end_dt,
            status="PENDING"
        )
        self.session.add(job)
        await self.session.flush() # get job.id
        
        try:
            # 2. Fetch from Epias API (using Phase 1 engine)
            logger.info(f"Syncing {endpoint_id} from {start_date} to {end_date}")
            data = await EpiasClient.fetch_data(endpoint_id, start_date, end_date)
            
            job.record_count = len(data)
            
            # 3. Save Raw JSON payload
            raw_import = RawImport(
                sync_job_id=job.id,
                payload=data,
                fetched_at=datetime.now(timezone.utc),
                validation_status="UNVALIDATED"
            )
            self.session.add(raw_import)
            
            # 4. Data Pipeline
            if endpoint_id == "ptf":
                valid, invalid = Validator.validate_ptf(data)
                raw_import.validation_status = "VALID" if not invalid else "PARTIAL_INVALID"
                
                ptf_models = Normalizer.normalize_ptf(valid, job)
                self.session.add_all(ptf_models)
                
            job.status = "SUCCESS"
            
        except Exception as e:
            logger.error(f"Sync failed for {endpoint_id}: {str(e)}")
            job.status = "FAILED"
            
        finally:
            job.duration_ms = (time.time() - start_time) * 1000
            await self.session.commit()
            
        return job
