"""Export ilk KGUP, son KGUP and gerceklesen (realtime) toplam uretim for a fixed
list of power plants, from 2026-09-01 onward, to an xlsx workbook (one sheet per plant).
"""

from __future__ import annotations

import time as sleep_time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "santral_kgup_urt_eylul2026.xlsx"
BASE_URL = "https://seffaflik.epias.com.tr/electricity-service/v1"
START_DATE = date(2026, 9, 1)
END_DATE = date.today()
REGION = "TR1"

# name -> (uevcbId for dpp/dpp-first-version, powerPlantId for realtime-generation-bulk)
PLANTS: dict[str, tuple[int, int]] = {
    "BIRKAPILI HES": (268, 1100),
    "DAGPAZARI RES": (100467, 1215),
    "KARAMAN RES": (3217251, 3058),
    "SERTAVUL RES": (3213751, 2629),
    "TEKSIN GES": (3212790, 2572),
    "R3-KARAMAN-1 RES": (5012962, 3164),
    "AKYEL-1 RES": (3213030, 2591),
    "AKYEL-2 RES": (3213031, 2616),
}


def credentials() -> dict[str, str]:
    text = (ROOT / "backend/.env").read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return {"username": values["EPIAS_USERNAME"], "password": values["EPIAS_PASSWORD"]}


def post_with_retry(session: requests.Session, headers: dict, path: str, body: dict) -> dict:
    for attempt in range(3):
        try:
            response = session.post(f"{BASE_URL}{path}", headers=headers, json=body, timeout=60)
            if response.status_code == 400:
                return {"items": []}
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt == 2:
                raise
            sleep_time.sleep(3 * (attempt + 1))
    return {"items": []}


def main() -> None:
    session = requests.Session()
    auth = session.post(
        "https://giris.epias.com.tr/cas/v1/tickets",
        data=credentials(),
        headers={"Accept": "text/plain"},
        timeout=30,
    )
    auth.raise_for_status()
    headers = {"TGT": auth.text.strip(), "Accept": "application/json", "Content-Type": "application/json"}

    # ilk / son KGUP, per plant, single call covering the whole range
    kgup_first: dict[str, dict[tuple[str, str], float]] = {}
    kgup_last: dict[str, dict[tuple[str, str], float]] = {}
    range_body_base = {
        "startDate": f"{START_DATE:%Y-%m-%d}T00:00:00+03:00",
        "endDate": f"{END_DATE:%Y-%m-%d}T23:59:59+03:00",
        "region": REGION,
    }
    for name, (uevcb_id, _) in PLANTS.items():
        body = {**range_body_base, "uevcbId": uevcb_id}
        first = post_with_retry(session, headers, "/generation/data/dpp-first-version", body)
        last = post_with_retry(session, headers, "/generation/data/dpp", body)
        kgup_first[name] = {(item["date"][:10], item["time"]): item.get("toplam") for item in first.get("items", [])}
        kgup_last[name] = {(item["date"][:10], item["time"]): item.get("toplam") for item in last.get("items", [])}
        print(f"KGUP fetched for {name}: ilk={len(kgup_first[name])} son={len(kgup_last[name])}")
        sleep_time.sleep(0.2)

    # realtime (gerceklesen) toplam uretim, one call per day for all plants at once
    urt: dict[str, dict[tuple[str, str], float]] = {name: {} for name in PLANTS}
    powerplant_id_to_name = {ppid: name for name, (_, ppid) in PLANTS.items()}
    day = START_DATE
    while day <= END_DATE:
        body = {"date": f"{day:%Y-%m-%d}T00:00:00+03:00", "powerPlantIds": list(powerplant_id_to_name.keys())}
        result = post_with_retry(session, headers, "/generation/data/realtime-generation-bulk", body)
        for item in result.get("items", []):
            plant_id = int(item["powerPlantName"].rsplit("-", 1)[-1])
            name = powerplant_id_to_name.get(plant_id)
            if name:
                urt[name][(item["date"][:10], item["hour"])] = item.get("total")
        print(f"Realtime uretim fetched for {day}: {len(result.get('items', []))} rows")
        sleep_time.sleep(0.2)
        day += timedelta(days=1)

    workbook = Workbook()
    workbook.remove(workbook.active)
    hours = [f"{h:02d}:00" for h in range(24)]
    for name in PLANTS:
        sheet = workbook.create_sheet(name[:31])
        sheet.append(["Tarih", "Saat", "Ilk KGUP (MWh)", "Son KGUP (MWh)", "Toplam Uretim - Gercek Zamanli (MWh)"])
        current = START_DATE
        while current <= END_DATE:
            date_str = f"{current:%Y-%m-%d}"
            for hour in hours:
                key = (date_str, hour)
                sheet.append(
                    [
                        date_str,
                        hour,
                        kgup_first[name].get(key),
                        kgup_last[name].get(key),
                        urt[name].get(key),
                    ]
                )
            current += timedelta(days=1)

    workbook.save(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
