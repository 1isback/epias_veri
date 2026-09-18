"""Backfill pre-2019 hourly generation for the SANKO hydro plants in
``resources/uevm-final.xlsx``.

UEVM (injection-quantity) data on EPİAŞ only starts 2019-01-01. This script pulls the
per-plant "Gerçek Zamanlı Üretim" (real-time generation) ``total`` for 2013-2018 from

    https://seffaflik.epias.com.tr/electricity/electricity-generation/ex-post-generation/real-time-generation

and prepends it to the existing sheet as a proxy for the missing UEVM history.

Notes
-----
* Burç Bendi HES has no per-plant real-time series on EPİAŞ, so its column stays blank
  before 2019.
* Real-time metering and UEVM settlement are different series; pre-2019 values are an
  approximation, not settled quantities.

Usage
-----
    python scripts/backfill_pre2019_realtime.py fetch     # hit the API, write the cache
    python scripts/backfill_pre2019_realtime.py merge      # merge cache into the xlsx
    python scripts/backfill_pre2019_realtime.py all        # fetch + merge
    python scripts/backfill_pre2019_realtime.py fetch --start 2018-12-01   # dry-run slice
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "resources" / "uevm-final.xlsx"
CACHE = ROOT / "resources" / "_pre2019_realtime_cache.json"
AUTH_URL = "https://giris.epias.com.tr/cas/v1/tickets"
BASE = "https://seffaflik.epias.com.tr/electricity-service/v1"
RT_PATH = "/generation/data/realtime-generation"
DATE_FMT = "yyyy\\-mm\\-dd\\ h:mm:ss"

# Column order in resources/uevm-final.xlsx -> real-time-generation powerPlantId,
# matched by EIC against the real-time powerplant-list. None = no real-time series.
PLANTS: list[tuple[str, int | None]] = [
    ("Uluabat", 652),
    ("Bulam", 1011),
    ("Burçbendi", None),
    ("Feke1", 1217),
    ("Feke2", 1189),
    ("Gökkaya", 1798),
    ("Himmetli", 1797),
]

DEFAULT_START = date(2013, 1, 1)
END = date(2018, 12, 31)


def credentials() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (ROOT / "backend" / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("EPIAS_USERNAME="):
            out["username"] = line.split("=", 1)[1].strip()
        elif line.startswith("EPIAS_PASSWORD="):
            out["password"] = line.split("=", 1)[1].strip()
    if "username" not in out or "password" not in out:
        raise SystemExit("EPIAS_USERNAME / EPIAS_PASSWORD not found in backend/.env")
    return out


def month_chunks(start: date, end: date):
    cur = start
    while cur <= end:
        nxt = date(cur.year + 1, 1, 1) if cur.month == 12 else date(cur.year, cur.month + 1, 1)
        yield cur, min(end, nxt - timedelta(days=1))
        cur = nxt


def get_tgt(session: requests.Session) -> str:
    resp = session.post(AUTH_URL, data=credentials(), headers={"Accept": "text/plain"}, timeout=30)
    resp.raise_for_status()
    return resp.text.strip()


def fetch_month(session: requests.Session, headers: dict, pid: int, start: date, end: date) -> list[dict]:
    body = {
        "startDate": f"{start:%Y-%m-%d}T00:00:00+03:00",
        "endDate": f"{end:%Y-%m-%d}T23:59:59+03:00",
        "powerPlantId": pid,
    }
    note = ""
    for attempt in range(8):
        try:
            resp = session.post(f"{BASE}{RT_PATH}", headers=headers, json=body, timeout=120)
            if resp.status_code == 200:
                return resp.json().get("items", [])
            note = f"HTTP {resp.status_code}: {resp.text[:160]}"
            if resp.status_code == 401:
                headers["TGT"] = get_tgt(session)
        except requests.RequestException as exc:  # noqa: PERF203
            note = f"{type(exc).__name__}: {exc}"
        wait = min(60, 4 * (attempt + 1))
        print(f"  retry {attempt + 1}/8 for {pid} {start:%Y-%m} ({note}); sleep {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"realtime-generation failed for plant {pid} {start}..{end}: {note}")


def cmd_fetch(start: date) -> None:
    session = requests.Session()
    headers = {"TGT": get_tgt(session), "Accept": "application/json", "Content-Type": "application/json"}
    chunks = list(month_chunks(start, END))
    data: dict[str, dict[str, float | None]] = {}
    if CACHE.exists():
        data = json.loads(CACHE.read_text(encoding="utf-8"))
    for name, pid in PLANTS:
        if pid is None:
            continue
        plant = data.setdefault(name, {})
        done_months = {k.rsplit("-", 1)[0][:7] for k in plant}
        for chunk_start, chunk_end in chunks:
            if f"{chunk_start:%Y-%m}" in done_months:
                print(f"{name:10} {chunk_start:%Y-%m}  cached, skip", flush=True)
                continue
            items = fetch_month(session, headers, pid, chunk_start, chunk_end)
            kept = 0
            for item in items:
                day = str(item.get("date"))[:10]
                if not ("2013-01-01" <= day <= "2018-12-31"):
                    continue
                raw_hour = str(item.get("hour") or "")
                try:
                    hour = int(raw_hour.split(":")[0])
                except ValueError:
                    continue
                plant[f"{day}|{hour}"] = item.get("total")
                kept += 1
            print(f"{name:10} {chunk_start:%Y-%m}  api={len(items):4d}  kept={kept:4d}  total={len(plant)}", flush=True)
            CACHE.write_text(json.dumps(data), encoding="utf-8")
            time.sleep(0.25)
    print(f"\ncache written -> {CACHE}")


def cmd_merge() -> None:
    data: dict[str, dict[str, float | None]] = json.loads(CACHE.read_text(encoding="utf-8"))

    wb = load_workbook(FINAL)
    ws = wb.active
    header = [c.value for c in ws[1]]
    n_plants = len(header) - 2
    if n_plants != len(PLANTS):
        raise SystemExit(f"sheet has {n_plants} plant columns, script expects {len(PLANTS)}")
    existing = list(ws.iter_rows(min_row=2, values_only=True))
    existing_min = min(r[0] for r in existing if r[0] is not None)

    plant_maps = [data.get(name, {}) for name, _ in PLANTS]
    all_days = sorted({key.split("|")[0] for m in plant_maps for key in m})
    if not all_days:
        raise SystemExit("cache is empty; run fetch first")
    first_day = datetime.strptime(all_days[0], "%Y-%m-%d")
    last_day = datetime(2018, 12, 31)
    if existing_min <= last_day:
        raise SystemExit(f"existing data already starts at {existing_min}; refusing to overlap")

    new_rows: list[tuple] = []
    cursor = first_day
    while cursor <= last_day:
        day_str = cursor.strftime("%Y-%m-%d")
        for hour in range(24):
            cells = [
                pmap.get(f"{day_str}|{hour}") if pmap else None
                for pmap in plant_maps
            ]
            new_rows.append((cursor, hour, *cells))
        cursor += timedelta(days=1)

    filled = sum(1 for r in new_rows for v in r[2:] if v is not None)
    print(f"new rows: {len(new_rows)}  ({first_day:%Y-%m-%d} .. 2018-12-31)")
    print(f"filled cells: {filled}")
    for (name, _), pmap in zip(PLANTS, plant_maps):
        print(f"  {name:10} {len(pmap):6d} hourly values")

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = FINAL.with_name(f"uevm-final.backup-{stamp}.xlsx")
    shutil.copy2(FINAL, backup)
    print(f"backup -> {backup}")

    out = Workbook()
    sheet = out.active
    sheet.title = ws.title
    sheet.append(header)
    for row in new_rows:
        sheet.append(row)
    for row in existing:
        sheet.append(row)
    for (cell,) in sheet.iter_rows(min_row=2, min_col=1, max_col=1):
        cell.number_format = DATE_FMT
    out.save(FINAL)
    print(f"saved -> {FINAL}  (rows: {sheet.max_row})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["fetch", "merge", "all"])
    parser.add_argument("--start", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(), default=DEFAULT_START)
    args = parser.parse_args()
    if args.command in ("fetch", "all"):
        cmd_fetch(args.start)
    if args.command in ("merge", "all"):
        cmd_merge()


if __name__ == "__main__":
    main()
