"""Generate the EPİAŞ dataset catalog from the transparency platform's own Swagger spec.

EPİAŞ publishes a full Swagger 2.0 document per service, e.g.
    https://seffaflik.epias.com.tr/electricity-service/technical/tr/swagger.json

This script downloads it (or reads a local copy), resolves ``$ref`` schemas and
writes ``app/integrations/epias/catalog/<service>.json`` — a data-driven catalog
the backend loads at import time. Adding a new dataset then only means
regenerating this file, not editing Python.

Usage:
    python scripts/generate_catalog.py                # fetch electricity live
    python scripts/generate_catalog.py --from-file el.json
    python scripts/generate_catalog.py --service electricity --service natural_gas
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

import httpx

CATALOG_DIR = Path(__file__).resolve().parents[1] / "app" / "integrations" / "epias" / "catalog"

SERVICES: dict[str, dict[str, str]] = {
    "electricity": {
        "swagger": "https://seffaflik.epias.com.tr/electricity-service/technical/tr/swagger.json",
        # base_url is None -> the loader uses settings.EPIAS_BASE_URL (…/electricity-service/v1)
        "base_url": "",
    },
    # Wired but out of scope for the first release; enable with --service natural_gas.
    "natural_gas": {
        "swagger": "https://seffaflik.epias.com.tr/natural-gas-service/technical/tr/swagger.json",
        "base_url": "https://seffaflik.epias.com.tr/natural-gas-service/v1",
    },
}

# tag (Swagger "controller") -> human friendly Turkish category label
CATEGORY_LABELS: dict[str, str] = {
    "consumption-data-controller": "Tüketim",
    "generation-data-controller": "Üretim",
    "renewables-data-controller": "Yenilenebilir (YEK)",
    "transmission-data-controller": "İletim",
    "markets-gop-data-controller": "Gün Öncesi Piyasası (GÖP)",
    "markets-gip-data-controller": "Gün İçi Piyasası (GİP)",
    "markets-dgp-data-controller": "Dengeleme Güç Piyasası (DGP)",
    "markets-dams-data-controller": "Vadeli Elektrik Piyasası (VEP/DAMS)",
    "markets-vep-data-controller": "Vadeli Elektrik Piyasası (VEP)",
    "markets-yekg-data-controller": "YEK-G Piyasası",
    "markets-gddk-data-controller": "GDDK",
    "markets-ancillary-services-data-controller": "Yan Hizmetler",
    "markets-imbalance-data-controller": "Dengesizlik",
    "markets-bilateral-contracts-data-controller": "İkili Anlaşmalar",
    "markets-general-data-data-controller": "Piyasa Genel Veriler",
    "markets-data-controller": "Piyasalar",
    "dashboard-data-controller": "Özet Gösterge Paneli",
    "main-data-controller": "Genel / Referans Listeler",
    "menu-controller": "Menü",
}

# Request-body param name -> lookup dataset id that supplies its option list.
PARAM_LOOKUPS: dict[str, str] = {
    "provinceId": "province-list",
    "powerPlantId": "powerplant-list",
    "powerplantId": "powerplant-list",
    "powerPlantIds": "powerplant-list",
    "region": "region-list",
    "regionId": "umm-region-list",
    "distributionId": "distribution-region",
    "mesajTipId": "umm-message-type-list",
    "basinName": "basin-list",
    "damName": "dam-list",
}

# Per-dataset overrides: some endpoints need an id from a *specific* list, not the
# generic one PARAM_LOOKUPS would pick. Keyed by dataset id -> param -> lookup id.
DATASET_PARAM_LOOKUPS: dict[str, dict[str, str]] = {
    "injection-quantity": {"powerplantId": "injection-quantity-powerplant-list"},
}

# Curated labels for params whose Swagger "description" is copy-paste noise.
PARAM_LABELS: dict[str, str] = {
    "startDate": "Başlangıç tarihi",
    "endDate": "Bitiş tarihi",
    "date": "Tarih",
    "period": "Dönem",
    "periodStartDate": "Dönem başlangıcı",
    "periodEndDate": "Dönem bitişi",
    "versionStartDate": "Versiyon başlangıcı",
    "versionEndDate": "Versiyon bitişi",
    "year": "Yıl",
    "region": "Bölge",
    "regionId": "Bölge",
    "organizationId": "Organizasyon",
    "organizationIds": "Organizasyonlar",
    "uevcbId": "UEVÇB",
    "uevcbIds": "UEVÇB listesi",
    "uevcbName": "UEVÇB adı",
    "powerPlantId": "Santral",
    "powerplantId": "Santral",
    "powerPlantIds": "Santraller",
    "provinceId": "İl",
    "districtName": "İlçe",
    "basinName": "Havza",
    "damName": "Baraj",
    "distributionId": "Dağıtım bölgesi",
    "loadType": "Yük tipi",
    "orderType": "Talimat tipi",
    "priceType": "Fiyat tipi",
    "direction": "Yön",
    "deliveryPeriod": "Teslimat dönemi",
    "mesajTipId": "Mesaj tipi",
}

DATE_DESC_NOISE = "formatında tarih bilgisi"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_spec(service: str, from_file: str | None) -> dict[str, Any]:
    if from_file:
        return json.loads(Path(from_file).read_text(encoding="utf-8"))
    url = SERVICES[service]["swagger"]
    print(f"  fetching {url}")
    resp = httpx.get(url, timeout=60.0)
    resp.raise_for_status()
    return resp.json()


class Resolver:
    def __init__(self, definitions: dict[str, Any]):
        self.definitions = definitions

    def resolve(self, schema: dict[str, Any] | None) -> dict[str, Any]:
        if not schema:
            return {}
        ref = schema.get("$ref")
        if ref:
            return self.resolve(self.definitions.get(ref.split("/")[-1], {}))
        return schema

    def properties(self, schema: dict[str, Any] | None) -> dict[str, Any]:
        return self.resolve(schema).get("properties") or {}


def clean_desc(value: str | None) -> str:
    if not value or DATE_DESC_NOISE in value:
        return ""
    return value.strip()


def build_param(name: str, prop: dict[str, Any], required: set[str]) -> dict[str, Any]:
    param: dict[str, Any] = {
        "name": name,
        "type": prop.get("type", "string"),
        "required": name in required,
        "label": PARAM_LABELS.get(name) or clean_desc(prop.get("description")) or name,
    }
    if prop.get("format"):
        param["format"] = prop["format"]
    if prop.get("enum"):
        param["enum"] = prop["enum"]
    desc = clean_desc(prop.get("description"))
    if desc and desc != param["label"]:
        param["description"] = desc
    if name in PARAM_LOOKUPS:
        param["lookup_id"] = PARAM_LOOKUPS[name]
    return param


def build_columns(resolver: Resolver, response_schema: dict[str, Any]) -> list[dict[str, Any]]:
    resolved = resolver.resolve(response_schema)
    props = resolved.get("properties") or {}
    items = props.get("items")
    if not items:
        return []
    row_props = resolver.properties(items.get("items"))
    columns = []
    for field, prop in row_props.items():
        column = {"field": field, "type": prop.get("type", "string"),
                  "label": clean_desc(prop.get("description")) or field}
        if prop.get("format"):
            column["format"] = prop["format"]
        columns.append(column)
    return columns


def is_export_operation(path: str, operation: dict[str, Any], request_props: dict[str, Any]) -> bool:
    if "exportType" in request_props:
        return True
    if any("export" in tag for tag in operation.get("tags", [])):
        return True
    return path.rstrip("/").endswith("-export") or path.endswith("/export")


LOOKUP_HINT = re.compile(r"(-list|-filter-list|-direction|region$|list$)")


def parse_service(service: str, spec: dict[str, Any]) -> dict[str, Any]:
    resolver = Resolver(spec.get("definitions", {}))
    base_url = SERVICES[service]["base_url"] or None
    datasets: list[dict[str, Any]] = []
    lookups: list[dict[str, Any]] = []
    categories: dict[str, str] = {}
    used_ids: set[str] = set()

    for raw_path, methods in sorted(spec.get("paths", {}).items()):
        clean_path = raw_path[len("/v1"):] if raw_path.startswith("/v1/") else raw_path
        for method, operation in methods.items():
            method = method.upper()
            if method not in ("GET", "POST"):
                continue

            body_params = [p for p in operation.get("parameters", []) if p.get("in") == "body"]
            request_schema = body_params[0].get("schema") if body_params else None
            request_props = resolver.properties(request_schema)
            required = set(resolver.resolve(request_schema).get("required", []))

            if is_export_operation(raw_path, operation, request_props):
                continue

            op_id = operation.get("operationId") or ""
            dataset_id = slugify(op_id) or slugify(clean_path.split("/")[-1])
            base_id = dataset_id
            counter = 2
            while dataset_id in used_ids:
                dataset_id = f"{base_id}-{counter}"
                counter += 1
            used_ids.add(dataset_id)

            tag = (operation.get("tags") or ["diger"])[0]
            category_label = CATEGORY_LABELS.get(tag, tag.replace("-data-controller", "").replace("-", " ").title())
            categories[tag] = category_label

            params = [
                build_param(name, prop, required)
                for name, prop in request_props.items()
                if name != "page"
            ]
            for param in params:
                override = DATASET_PARAM_LOOKUPS.get(dataset_id, {}).get(param["name"])
                if override:
                    param["lookup_id"] = override
            response_schema = operation.get("responses", {}).get("200", {}).get("schema", {})
            columns = build_columns(resolver, response_schema)

            is_lookup = method == "GET" or bool(LOOKUP_HINT.search(clean_path.split("/")[-1]))

            entry = {
                "id": dataset_id,
                "path": clean_path,
                "method": method,
                "service": service,
                "name": operation.get("summary") or op_id or dataset_id,
                "description": clean_desc(operation.get("description")),
                "category": tag,
                "category_label": category_label,
                "is_date_partitioned": "startDate" in request_props and "endDate" in request_props,
                "paginated": "page" in request_props,
                "params": params,
                "columns": columns,
                "kind": "lookup" if is_lookup else "data",
            }
            if base_url:
                entry["base_url"] = base_url

            datasets.append(entry)
            if is_lookup:
                lookups.append({
                    "id": dataset_id,
                    "path": clean_path,
                    "method": method,
                    "name": entry["name"],
                    "columns": columns,
                    **({"base_url": base_url} if base_url else {}),
                })

    return {
        "service": service,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": SERVICES[service]["swagger"],
        "spec_version": spec.get("info", {}).get("version"),
        "categories": dict(sorted(categories.items(), key=lambda kv: kv[1])),
        "datasets": datasets,
        "lookups": lookups,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", action="append", choices=list(SERVICES), help="defaults to electricity")
    parser.add_argument("--from-file", help="read the swagger json from a local file (single service only)")
    args = parser.parse_args()

    services = args.service or ["electricity"]
    if args.from_file and len(services) != 1:
        parser.error("--from-file requires exactly one --service")

    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    for service in services:
        print(f"[{service}]")
        spec = load_spec(service, args.from_file)
        catalog = parse_service(service, spec)
        out = CATALOG_DIR / f"{service}.json"
        out.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        data_count = sum(1 for d in catalog["datasets"] if d["kind"] == "data")
        print(f"  wrote {out.relative_to(CATALOG_DIR.parents[3])}: "
              f"{data_count} datasets, {len(catalog['lookups'])} lookups, "
              f"{len(catalog['categories'])} categories")


if __name__ == "__main__":
    sys.exit(main())
