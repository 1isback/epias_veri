"""Load the generated EPİAŞ dataset catalog into registry objects.

The catalog JSON files under ``catalog/<service>.json`` are produced by
``scripts/generate_catalog.py`` from EPİAŞ's own Swagger spec. This module turns
them into the :class:`EndpointDefinition` objects the rest of the backend already
speaks, so adding a dataset never requires touching Python.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

CATALOG_DIR = Path(__file__).resolve().parent / "catalog"


class ParamDef(BaseModel):
    name: str
    type: str = "string"
    required: bool = False
    label: str = ""
    format: str | None = None
    enum: list[str] | None = None
    description: str | None = None
    lookup_id: str | None = None


class EndpointMetadata(BaseModel):
    name: str = Field(..., description="Human readable name of the endpoint")
    description: str | None = None
    category: str = "diger"
    category_label: str = "Diğer"
    service: str = "electricity"
    kind: str = "data"  # "data" | "lookup"
    base_url: str | None = None  # None -> settings.EPIAS_BASE_URL

    is_date_partitioned: bool = False
    paginated: bool = False
    start_date_param: str = "startDate"
    end_date_param: str = "endDate"
    date_format: str = "%Y-%m-%dT%H:%M:%S+03:00"
    max_days: int = 90

    supported_exports: list[str] = Field(default_factory=lambda: ["CSV", "EXCEL", "JSON"])
    supported_charts: list[str] = Field(default_factory=list)
    params: list[ParamDef] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)


class EndpointDefinition(BaseModel):
    id: str
    path: str
    method: str = "POST"
    metadata: EndpointMetadata


class LookupDefinition(BaseModel):
    id: str
    path: str
    method: str = "GET"
    name: str = ""
    columns: list[dict[str, Any]] = Field(default_factory=list)
    base_url: str | None = None


class Catalog(BaseModel):
    endpoints: dict[str, EndpointDefinition]
    lookups: dict[str, LookupDefinition]
    categories: dict[str, str]  # category id -> label


def _endpoint_from_entry(entry: dict[str, Any]) -> EndpointDefinition:
    metadata = EndpointMetadata(
        name=entry.get("name") or entry["id"],
        description=entry.get("description") or None,
        category=entry.get("category", "diger"),
        category_label=entry.get("category_label", "Diğer"),
        service=entry.get("service", "electricity"),
        kind=entry.get("kind", "data"),
        base_url=entry.get("base_url"),
        is_date_partitioned=entry.get("is_date_partitioned", False),
        paginated=entry.get("paginated", False),
        supported_charts=entry.get("supported_charts", []),
        params=[ParamDef(**p) for p in entry.get("params", [])],
        columns=entry.get("columns", []),
    )
    return EndpointDefinition(
        id=entry["id"], path=entry["path"], method=entry.get("method", "POST"), metadata=metadata
    )


@lru_cache(maxsize=1)
def load_catalog() -> Catalog:
    endpoints: dict[str, EndpointDefinition] = {}
    lookups: dict[str, LookupDefinition] = {}
    categories: dict[str, str] = {}

    for path in sorted(CATALOG_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        categories.update(raw.get("categories", {}))
        for entry in raw.get("datasets", []):
            endpoints[entry["id"]] = _endpoint_from_entry(entry)
        for entry in raw.get("lookups", []):
            lookups[entry["id"]] = LookupDefinition(
                id=entry["id"], path=entry["path"], method=entry.get("method", "GET"),
                name=entry.get("name", ""), columns=entry.get("columns", []),
                base_url=entry.get("base_url"),
            )

    return Catalog(endpoints=endpoints, lookups=lookups, categories=categories)
