"""EPİAŞ endpoint registry.

Historically this was a hand-written dict of a handful of endpoints. It is now
loaded from the generated catalog (``catalog/<service>.json`` via
:mod:`app.integrations.epias.catalog_loader`) so every EPİAŞ transparency dataset
is reachable without editing code. A few legacy short ids (``ptf``, ``smf`` …)
are aliased for backwards compatibility.
"""

from __future__ import annotations

from app.integrations.epias.catalog.featured import LEGACY_ALIASES
from app.integrations.epias.catalog_loader import (  # re-exported for callers
    EndpointDefinition,
    EndpointMetadata,
    ParamDef,
    load_catalog,
)

# Kept for callers that still reference these paths directly.
INJECTION_QUANTITY = "/generation/data/injection-quantity"
INJECTION_QUANTITY_POWERPLANT_LIST = "/generation/data/injection-quantity-powerplant-list"

__all__ = [
    "EndpointDefinition",
    "EndpointMetadata",
    "ParamDef",
    "EPIAS_REGISTRY",
    "get_endpoint_def",
    "resolve_endpoint_id",
]


def _build_registry() -> dict[str, EndpointDefinition]:
    catalog = load_catalog()
    registry: dict[str, EndpointDefinition] = dict(catalog.endpoints)
    for alias, target in LEGACY_ALIASES.items():
        if target in registry:
            registry[alias] = registry[target]
    return registry


EPIAS_REGISTRY: dict[str, EndpointDefinition] = _build_registry()


def resolve_endpoint_id(endpoint_id: str) -> str:
    """Map a legacy alias (``ptf``) to its catalog id (``mcp-data``)."""
    return LEGACY_ALIASES.get(endpoint_id, endpoint_id)


def get_endpoint_def(endpoint_id: str) -> EndpointDefinition:
    definition = EPIAS_REGISTRY.get(endpoint_id) or EPIAS_REGISTRY.get(resolve_endpoint_id(endpoint_id))
    if definition is None:
        raise ValueError(f"Endpoint '{endpoint_id}' not found in registry.")
    return definition
