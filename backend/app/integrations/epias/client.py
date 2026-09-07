from typing import Dict, Any, List, Optional, Tuple

from app.integrations.epias.registry import get_endpoint_def
from app.integrations.epias.engine import request_engine


class EpiasClient:
    """
    High-level client wrapper for EPİAŞ API.
    Uses the Endpoint Registry to automatically resolve parameters for the Request Engine.
    """

    @classmethod
    async def fetch_data(
        cls,
        endpoint_id: str,
        start_date: str,
        end_date: str,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetches data dynamically based on endpoint registry configuration.
        Handles the 90-day partitioning and merging implicitly via request engine.
        """
        params = dict(additional_params or {})
        endpoint_def = get_endpoint_def(endpoint_id)
        params[endpoint_def.metadata.start_date_param] = start_date
        params[endpoint_def.metadata.end_date_param] = end_date

        records, _ = await cls._run(endpoint_def, params)
        return records

    @classmethod
    async def fetch_dataset(
        cls,
        endpoint_id: str,
        params: Optional[Dict[str, Any]] = None,
        page: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Generic catalog-driven fetch: pass EPİAŞ request params straight through.

        Returns ``(records, meta)`` where meta carries ``total``, ``truncated`` and
        ``intervals`` (how many date partitions were requested).
        """
        merged = {k: v for k, v in (params or {}).items() if v not in (None, "")}
        if page:
            merged["page"] = page
        return await cls._run(get_endpoint_def(endpoint_id), merged)

    @classmethod
    async def _run(
        cls, endpoint_def, params: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        meta: Dict[str, Any] = {}
        records = await request_engine.execute(
            endpoint_path=endpoint_def.path,
            method=endpoint_def.method,
            params=params,
            is_date_partitioned=endpoint_def.metadata.is_date_partitioned,
            start_date_param=endpoint_def.metadata.start_date_param,
            end_date_param=endpoint_def.metadata.end_date_param,
            date_format=endpoint_def.metadata.date_format,
            max_days=endpoint_def.metadata.max_days,
            paginated=endpoint_def.metadata.paginated,
            base_url=endpoint_def.metadata.base_url,
            collect_meta=meta,
        )
        return records, meta
