"""Catalog loader + generic query plumbing."""

import pytest

from app.api.v1.catalog import _normalize_lookup
from app.integrations.epias.catalog.featured import FEATURED_DATASET_IDS, LEGACY_ALIASES
from app.integrations.epias.catalog_loader import load_catalog
from app.integrations.epias.engine import GenericRequestEngine
from app.integrations.epias.registry import get_endpoint_def


def test_catalog_loads_and_has_core_datasets():
    catalog = load_catalog()
    assert len(catalog.endpoints) > 100
    assert len(catalog.lookups) > 10
    for dataset_id in ("mcp-data", "system-marginal-price", "injection-quantity"):
        assert dataset_id in catalog.endpoints


def test_legacy_aliases_resolve():
    assert get_endpoint_def("ptf").path == "/markets/dam/data/mcp"
    assert get_endpoint_def("smf").path == "/markets/bpm/data/system-marginal-price"
    for alias, target in LEGACY_ALIASES.items():
        assert get_endpoint_def(alias) is get_endpoint_def(target)


def test_featured_ids_exist_in_catalog():
    catalog = load_catalog()
    missing = [d for d in FEATURED_DATASET_IDS if d not in catalog.endpoints]
    assert not missing, f"featured ids not in catalog: {missing}"


def test_mcp_metadata_matches_real_epias_fields():
    meta = get_endpoint_def("mcp-data").metadata
    assert meta.is_date_partitioned and meta.paginated
    fields = {c["field"] for c in meta.columns}
    assert {"price", "priceUsd", "priceEur"} <= fields
    assert {p.name for p in meta.params} == {"startDate", "endDate"}


def test_date_param_lookups_are_wired():
    params = {p.name: p for p in get_endpoint_def("injection-quantity").metadata.params}
    # UEVM needs an id from its own powerplant list, not the generic one.
    assert params["powerplantId"].lookup_id == "injection-quantity-powerplant-list"


@pytest.mark.parametrize(
    "rows, expected",
    [
        ([{"id": 10, "name": "ADANA"}], [{"label": "ADANA", "value": 10}]),
        ([[{"id": 1, "name": "X"}]], [{"label": "X", "value": 1}]),  # doubly nested
        ([{"label": "L", "value": "V"}], [{"label": "L", "value": "V"}]),
        ([{"organizationId": 5, "organizationName": "ORG"}], [{"label": "ORG", "value": 5}]),
    ],
)
def test_normalize_lookup(rows, expected):
    assert _normalize_lookup(rows, "organization-list") == expected


def test_region_lookup_uses_short_name_as_value():
    rows = [{"regionId": 1, "regionShortName": "TR1"}]
    assert _normalize_lookup(rows, "region-list") == [{"label": "TR1", "value": "TR1"}]


def test_extract_items_handles_custom_wrapper():
    engine = GenericRequestEngine()
    assert engine._extract_items_from_response({"damList": [{"a": 1}, {"a": 2}]}) == [{"a": 1}, {"a": 2}]
