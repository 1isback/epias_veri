"""Export ilk KGUP, son KGUP and gerceklesen (realtime) toplam uretim for
R3-KARAMAN-1 RES, from 2026-01-01 onward, to a standalone xlsx workbook.
"""

from __future__ import annotations

import time as sleep_time
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

import requests
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "r3_karaman1_kgup_urt_2026.xlsx"
BASE_URL = "https://seffaflik.epias.com.tr/electricity-service/v1"
START_DATE = date(2026, 1, 1)
END_DATE = date.today()
REGION = "TR1"
UEVCB_ID = 5012962
POWERPLANT_ID = 3164
PLANT_NAME = "R3-KARAMAN-1 RES"


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
    for attempt in range(6):
        try:
            response = session.post(f"{BASE_URL}{path}", headers=headers, json=body, timeout=60)
            if response.status_code == 400:
                return {"items": []}
            if response.status_code == 429:
                sleep_time.sleep(5 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt == 5:
                raise
            sleep_time.sleep(3 * (attempt + 1))
    return {"items": []}


def add_months(value: date, months: int) -> date:
    index = value.month - 1 + months
    year, month = value.year + index // 12, index % 12 + 1
    return value.replace(year=year, month=month, day=min(value.day, monthrange(year, month)[1]))


def quarter_chunks(start: date, end: date):
    current = start
    while current <= end:
        next_start = add_months(current, 3)
        chunk_end = min(end, next_start - timedelta(days=1))
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


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

    kgup_first: dict[tuple[str, str], float] = {}
    kgup_last: dict[tuple[str, str], float] = {}
    for start, end in quarter_chunks(START_DATE, END_DATE):
        body = {
            "startDate": f"{start:%Y-%m-%d}T00:00:00+03:00",
            "endDate": f"{end:%Y-%m-%d}T23:59:59+03:00",
            "region": REGION,
            "uevcbId": UEVCB_ID,
        }
        first = post_with_retry(session, headers, "/generation/data/dpp-first-version", body)
        last = post_with_retry(session, headers, "/generation/data/dpp", body)
        for item in first.get("items", []):
            kgup_first[(item["date"][:10], item["time"])] = item.get("toplam")
        for item in last.get("items", []):
            kgup_last[(item["date"][:10], item["time"])] = item.get("toplam")
        print(f"KGUP chunk {start}..{end}: ilk={len(first.get('items', []))} son={len(last.get('items', []))}")
        sleep_time.sleep(0.2)

    urt: dict[tuple[str, str], float] = {}
    day = START_DATE
    while day <= END_DATE:
        body = {"date": f"{day:%Y-%m-%d}T00:00:00+03:00", "powerPlantIds": [POWERPLANT_ID]}
        result = post_with_retry(session, headers, "/generation/data/realtime-generation-bulk", body)
        for item in result.get("items", []):
            urt[(item["date"][:10], item["hour"])] = item.get("total")
        if day.day == 1:
            print(f"Realtime uretim fetched through {day}")
        sleep_time.sleep(0.6)
        day += timedelta(days=1)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = PLANT_NAME[:31]
    sheet.append(["Tarih", "Saat", "Ilk KGUP (MWh)", "Son KGUP (MWh)", "Toplam Uretim - Gercek Zamanli (MWh)"])
    hours = [f"{h:02d}:00" for h in range(24)]
    current = START_DATE
    while current <= END_DATE:
        date_str = f"{current:%Y-%m-%d}"
        for hour in hours:
            key = (date_str, hour)
            sheet.append([date_str, hour, kgup_first.get(key), kgup_last.get(key), urt.get(key)])
        current += timedelta(days=1)

    workbook.save(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
