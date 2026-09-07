from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.raw import SyncJob, RawImport
from app.models.market import PTFData

class SyncJobRepository(BaseRepository[SyncJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(SyncJob, session)

class RawImportRepository(BaseRepository[RawImport]):
    def __init__(self, session: AsyncSession):
        super().__init__(RawImport, session)

class PTFDataRepository(BaseRepository[PTFData]):
    def __init__(self, session: AsyncSession):
        super().__init__(PTFData, session)
