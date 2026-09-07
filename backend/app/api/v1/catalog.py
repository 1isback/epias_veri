"""Catalog API — browse every EPİAŞ transparency dataset and query it generically.

Backed by the generated catalog (``integrations/epias/catalog/electricity.json``).
No dataset is hard-coded here; adding one is a catalog regeneration.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.integrations.epias.catalog.featured import FEATURED_DATASET_IDS
from app.integrations.epias.catalog_loader import load_catalog
from app.integrations.epias.client import EpiasClient
from app.models.user import User

router = APIRouter()

# A wide default window for lookup endpoints that (oddly) require a date range.
_LOOKUP_WINDOW = {"startDate": "2015-01-01T00:00:00+03:00", "endDate": "2035-12-31T23:59:59+03:00"}

# lookup id -> which response fields become {value,label}. Falls back to heuristics.
_LOOKUP_FIELDS: dict[str, dict[str, str]] = {
    "region-list": {"value": "regionShortName", "label": "regionShortName"},
    "umm-region-list": {"value": "regionId", "label": "regionShortName"},
    "organization-list": {"value": "organizationId", "label": "organizationName"},
    "province-list": {"value": "id", "label": "name"},
    "powerplant-list": {"value": "id", "label": "name"},
    "distribution-region": {"value": "distributeId", "label": "distributeCode"},
    "umm-message-type-list": {"value": "id", "label": "typeName"},
}

_lookup_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_LOOKUP_TTL = 60 * 30  # 30 minutes


# --------------------------------------------------------------------------- models
class DatasetSummary(BaseModel):
    id: str
    name: str
    description: str | None = None
    category: str
    category_label: str
    param_count: int
    is_date_partitioned: bool
    paginated: bool
    featured: bool = False


class DatasetDetail(DatasetSummary):
    path: str
    method: str
    params: list[dict[str, Any]]
    columns: list[dict[str, Any]]


class QueryRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    page: dict[str, int] | None = None


# --------------------------------------------------------------------------- helpers
def _epias_status(exc: Exception) -> int:
    """A bad request to EPİAŞ (wrong filter value) is the caller's fault -> 400."""
    return 400 if "(400)" in str(exc) else 502


def _summary(entry) -> DatasetSummary:
    m = entry.metadata
    return DatasetSummary(
        id=entry.id, name=m.name, description=m.description,
        category=m.category, category_label=m.category_label,
        param_count=len(m.params), is_date_partitioned=m.is_date_partitioned,
        paginated=m.paginated, featured=entry.id in FEATURED_DATASET_IDS,
    )


def _columns_for(entry, rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    if entry.metadata.columns:
        return [
            {"field": c["field"], "headerName": c.get("label") or c["field"]}
            for c in entry.metadata.columns
        ]
    seen: list[str] = []
    for row in rows[:50]:
        for key in row:
            if key not in seen:
                seen.append(key)
    return [{"field": k, "headerName": k} for k in seen]


def _normalize_lookup(rows: list[Any], lookup_id: str) -> list[dict[str, Any]]:
    # Some EPİAŞ list endpoints wrap their rows one level deeper: {"items": [[...]]}.
    if len(rows) == 1 and isinstance(rows[0], list):
        rows = rows[0]
    cfg = _LOOKUP_FIELDS.get(lookup_id, {})
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            out.append({"label": str(row), "value": row})
            continue
        if cfg and cfg["value"] in row:
            out.append({"label": str(row.get(cfg["label"], row[cfg["value"]])), "value": row[cfg["value"]]})
            continue
        if "value" in row and "label" in row:
            out.append({"label": str(row["label"]), "value": row["value"]})
            continue
        if "id" in row:
            label = row.get("name") or row.get("shortName") or row.get("typeName") or row["id"]
            out.append({"label": str(label), "value": row["id"]})
            continue
        id_key = next((k for k in row if k.lower().endswith("id")), None)
        name_key = next((k for k in row if "name" in k.lower()), None)
        if id_key:
            out.append({"label": str(row.get(name_key, row[id_key])), "value": row[id_key]})
            continue
        keys = list(row)
        out.append({"label": str(row[keys[-1]]), "value": row[keys[0]]})
    # de-dupe on value, keep first occurrence / order
    unique: dict[str, dict[str, Any]] = {}
    for item in out:
        unique.setdefault(str(item["value"]), item)
    return list(unique.values())


# --------------------------------------------------------------------------- routes
@router.get("/categories")
async def list_categories(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    catalog = load_catalog()
    counts: dict[str, int] = {}
    for entry in catalog.endpoints.values():
        if entry.metadata.kind == "data":
            counts[entry.metadata.category] = counts.get(entry.metadata.category, 0) + 1
    categories = [
        {"id": cid, "label": catalog.categories.get(cid, cid), "dataset_count": count}
        for cid, count in counts.items()
    ]
    categories.sort(key=lambda c: c["label"])

    featured = []
    for did in FEATURED_DATASET_IDS:
        entry = catalog.endpoints.get(did)
        if entry:
            featured.append({"id": did, "name": entry.metadata.name,
                             "category_label": entry.metadata.category_label})
    return {"featured": featured, "categories": categories}


@router.get("/datasets", response_model=list[DatasetSummary])
async def list_datasets(
    category: str | None = None,
    q: str | None = None,
    featured: bool = False,
    current_user: User = Depends(get_current_user),
) -> list[DatasetSummary]:
    catalog = load_catalog()
    needle = (q or "").strip().lower()
    results: list[DatasetSummary] = []
    for entry in catalog.endpoints.values():
        if entry.metadata.kind != "data":
            continue
        if category and entry.metadata.category != category:
            continue
        if featured and entry.id not in FEATURED_DATASET_IDS:
            continue
        if needle and needle not in f"{entry.id} {entry.metadata.name} {entry.metadata.description or ''}".lower():
            continue
        results.append(_summary(entry))
    results.sort(key=lambda s: (not s.featured, s.category_label, s.name))
    return results


@router.get("/datasets/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(dataset_id: str, current_user: User = Depends(get_current_user)) -> DatasetDetail:
    catalog = load_catalog()
    entry = catalog.endpoints.get(dataset_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    return DatasetDetail(
        **_summary(entry).model_dump(),
        path=entry.path, method=entry.method,
        params=[p.model_dump(exclude_none=True) for p in entry.metadata.params],
        columns=entry.metadata.columns,
    )


@router.post("/datasets/{dataset_id}/query")
async def query_dataset(
    dataset_id: str, body: QueryRequest, current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    catalog = load_catalog()
    entry = catalog.endpoints.get(dataset_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

    supplied = {k: v for k, v in body.params.items() if v not in (None, "")}
    missing = [p.name for p in entry.metadata.params if p.required and p.name not in supplied]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required parameters: {', '.join(missing)}")

    try:
        rows, meta = await EpiasClient.fetch_dataset(dataset_id, supplied, body.page)
    except Exception as exc:  # surface EPİAŞ's own error text
        raise HTTPException(status_code=_epias_status(exc), detail=str(exc)) from exc

    return {"columns": _columns_for(entry, rows), "data": rows, "meta": meta}


@router.get("/lookups/{lookup_id}")
async def get_lookup(lookup_id: str, current_user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    cached = _lookup_cache.get(lookup_id)
    if cached and time.time() - cached[0] < _LOOKUP_TTL:
        return cached[1]

    catalog = load_catalog()
    entry = catalog.endpoints.get(lookup_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Lookup '{lookup_id}' not found")

    params = dict(_LOOKUP_WINDOW) if entry.metadata.is_date_partitioned else {}
    try:
        rows, _ = await EpiasClient.fetch_dataset(lookup_id, params)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    options = _normalize_lookup(rows, lookup_id)
    _lookup_cache[lookup_id] = (time.time(), options)
    return options
