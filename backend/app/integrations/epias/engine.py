import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings
from app.integrations.epias.auth import auth_manager

logger = logging.getLogger(__name__)

# Safety ceiling for a single generic query so a wide date range on an hourly
# dataset cannot pull an unbounded amount of rows into memory / the browser.
MAX_COLLECTED_ROWS = 50_000
PAGE_SIZE = 1000
MAX_PAGES = 200


class RequestEngineError(Exception):
    pass

class EpiasBadRequestError(RequestEngineError):
    pass

class EpiasServerError(RequestEngineError):
    pass

class EpiasTimeoutError(RequestEngineError):
    pass
class GenericRequestEngine:
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.max_retries = 3
        self.retry_delay = 2.0  # seconds

    def _base(self, base_url: Optional[str]) -> str:
        return base_url or settings.EPIAS_BASE_URL

    async def _execute_single_request(self, method: str, url: str, params: dict, headers: dict) -> Any:
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "POST":
                        response = await client.request(method, url, json=params, headers=headers)
                    else:
                        response = await client.request(method, url, params=params, headers=headers)

                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.warning("Received 401 Unauthorized from EPİAŞ API; refreshing TGT.")
                    auth_manager.invalidate_tgt()

                logger.warning("EPİAŞ HTTP request failed with status %s", e.response.status_code)
                if e.response.status_code == 400 or attempt == self.max_retries - 1:
                    detail = e.response.text[:300]
                    raise RequestEngineError(
                        f"EPİAŞ request failed ({e.response.status_code}): {detail}"
                    ) from e
            except Exception as e:
                logger.error(f"Unexpected error on {url}: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise RequestEngineError(f"API request failed after {self.max_retries} attempts.") from e

            await asyncio.sleep(self.retry_delay * (attempt + 1))

    async def execute_raw(
        self,
        endpoint_path: str,
        method: str,
        params: Optional[dict] = None,
        base_url: Optional[str] = None,
    ) -> Any:
        """Execute one authenticated request and retain the response wrapper."""
        tgt = await auth_manager.get_valid_tgt()
        headers = {"TGT": tgt, "Accept": "application/json"}
        if method.upper() == "POST":
            headers["Content-Type"] = "application/json"
        return await self._execute_single_request(
            method, f"{self._base(base_url)}{endpoint_path}", params or {}, headers
        )

    async def _fetch_all_pages(
        self, method: str, url: str, params: dict, headers: dict, collected_before: int
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Walk EPİAŞ ``page`` pagination until exhausted or the safety cap is hit."""
        records: List[Dict[str, Any]] = []
        total: Optional[int] = None
        for page_number in range(1, MAX_PAGES + 1):
            page_params = {**params, "page": {"number": page_number, "size": PAGE_SIZE}}
            result = await self._execute_single_request(method, url, page_params, headers)
            page_items = self._extract_items_from_response(result)
            records.extend(page_items)

            if isinstance(result, dict) and isinstance(result.get("page"), dict):
                total = result["page"].get("total", total)

            if not page_items or len(page_items) < PAGE_SIZE:
                break
            if total is not None and len(records) >= total:
                break
            if collected_before + len(records) >= MAX_COLLECTED_ROWS:
                return records[: MAX_COLLECTED_ROWS - collected_before], True
            await asyncio.sleep(0.2)
        return records, False

    async def execute(
        self,
        endpoint_path: str,
        method: str = "POST",
        params: Optional[dict] = None,
        is_date_partitioned: bool = False,
        start_date_param: str = "startDate",
        end_date_param: str = "endDate",
        date_format: str = "%Y-%m-%dT%H:%M:%S%z",
        max_days: int = 90,
        paginated: bool = False,
        base_url: Optional[str] = None,
        collect_meta: Optional[dict] = None,
    ) -> List[Dict[str, Any]]:
        params = params or {}
        auto_paginate = paginated and "page" not in params

        tgt = await auth_manager.get_valid_tgt()
        headers = {
            "tgt": tgt,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        url = f"{self._base(base_url)}{endpoint_path}"
        truncated = False

        if is_date_partitioned and start_date_param in params and end_date_param in params:
            start_str = params[start_date_param]
            end_str = params[end_date_param]

            try:
                # Assuming UI sends standard YYYY-MM-DD
                start_date = datetime.strptime(start_str.split("T")[0], "%Y-%m-%d")
                end_date = datetime.strptime(end_str.split("T")[0], "%Y-%m-%d")
            except ValueError:
                start_date = datetime.now()
                end_date = datetime.now()

            intervals = self._split_date_range(start_date, end_date, max_days)
            logger.info(f"Splitting request for {endpoint_path} into {len(intervals)} intervals.")

            all_records: List[Dict[str, Any]] = []
            for s_date, e_date in intervals:
                interval_params = params.copy()

                # Format to EPİAŞ specific ISO 8601: %Y-%m-%dT00:00:00+03:00
                interval_params[start_date_param] = f"{s_date.strftime('%Y-%m-%d')}T00:00:00+03:00"
                interval_params[end_date_param] = f"{e_date.strftime('%Y-%m-%d')}T23:59:59+03:00"

                if auto_paginate:
                    records, hit_cap = await self._fetch_all_pages(
                        method, url, interval_params, headers, len(all_records)
                    )
                else:
                    result = await self._execute_single_request(method, url, interval_params, headers)
                    records, hit_cap = self._extract_items_from_response(result), False
                all_records.extend(records)

                if hit_cap or len(all_records) >= MAX_COLLECTED_ROWS:
                    truncated = truncated or hit_cap or len(all_records) > MAX_COLLECTED_ROWS
                    all_records = all_records[:MAX_COLLECTED_ROWS]
                    break

                await asyncio.sleep(0.5)

            if collect_meta is not None:
                collect_meta.update(intervals=len(intervals), truncated=truncated, total=len(all_records))
            return all_records

        if auto_paginate:
            all_records, truncated = await self._fetch_all_pages(method, url, params, headers, 0)
        else:
            result = await self._execute_single_request(method, url, params, headers)
            all_records = self._extract_items_from_response(result)

        if collect_meta is not None:
            collect_meta.update(intervals=1, truncated=truncated, total=len(all_records))
        return all_records

    def _split_date_range(self, start_date: datetime, end_date: datetime, max_days: int) -> List[tuple]:
        intervals = []
        current_start = start_date

        while current_start <= end_date:
            current_end = current_start + timedelta(days=max_days - 1)
            if current_end > end_date:
                current_end = end_date

            intervals.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)

        return intervals

    def _extract_items_from_response(self, response_data: dict) -> List[Dict[str, Any]]:
        if not isinstance(response_data, dict):
            return [response_data] if response_data else []

        if "items" in response_data:
            return response_data["items"]

        if "data" in response_data and isinstance(response_data["data"], dict) and "items" in response_data["data"]:
            return response_data["data"]["items"]

        # Some list endpoints use their own wrapper key, e.g. {"damList": [...]}.
        list_values = [v for v in response_data.values() if isinstance(v, list)]
        if len(list_values) == 1:
            return list_values[0]

        return [response_data]

request_engine = GenericRequestEngine()
