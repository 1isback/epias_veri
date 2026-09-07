import asyncio
import logging
from datetime import datetime, timedelta
import httpx
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AuthenticationManager:
    """
    Centralized Authentication Manager for EPÄ°AÅ TGT mechanism.
    Handles obtaining, caching, and renewing the Ticket Granting Ticket (TGT).
    Thread-safe implementation using asyncio.Lock.
    """
    def __init__(self):
        self.tgt: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        # EPÄ°AÅ TGT expires in 2 hours. We renew 15 minutes before expiration.
        self.RENEW_BEFORE_MINUTES = 15
        self._lock: Optional[asyncio.Lock] = None

    @property
    def lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def get_valid_tgt(self) -> str:
        """
        Returns a valid TGT. If it's expired or close to expiration,
        it will safely renew it ensuring no concurrent renewals.
        """
        async with self.lock:
            if self._is_tgt_valid():
                return self.tgt
            
            logger.info("TGT is missing or expiring. Obtaining a new TGT from EPÄ°AÅ...")
            await self._fetch_new_tgt()
            return self.tgt

    async def is_tgt_valid(self) -> bool:
        return self._is_tgt_valid()

    def _is_tgt_valid(self) -> bool:
        if not self.tgt or not self.expires_at:
            return False
        
        now = datetime.utcnow()
        renew_threshold = self.expires_at - timedelta(minutes=self.RENEW_BEFORE_MINUTES)
        return now < renew_threshold

    def invalidate_tgt(self) -> None:
        self.tgt = None
        self.expires_at = None

    async def _fetch_new_tgt(self) -> None:
        """
        Fetches the TGT from EPÄ°AÅ authentication endpoint.
        """
        if not settings.EPIAS_USERNAME or not settings.EPIAS_PASSWORD:
            logger.warning("EPÄ°AÅ Credentials missing in configuration.")
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Based on tgt_istek.py
                payload = f"username={settings.EPIAS_USERNAME}&password={settings.EPIAS_PASSWORD}"
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/plain"
                }
                
                response = await client.post(
                    settings.EPIAS_AUTH_URL,
                    content=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                # The response text is directly the TGT
                self.tgt = response.text.strip()
                self.expires_at = datetime.utcnow() + timedelta(hours=2)
                
                logger.info("Successfully obtained new EPİAŞ TGT.")
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to authenticate with EPÄ°AÅ API: {str(e)}")
            raise

# A single instance shared across all EPÄ°AÅ services
auth_manager = AuthenticationManager()
