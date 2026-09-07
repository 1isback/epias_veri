"""Export hourly UEVM data for verified geothermal (JES) power plants."""

import ast
import re
import sys
import time as sleep_time
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

import requests
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "jes_uevm_2019_to_today.xlsx"
LOG = ROOT / "jes_uevm_export.log"
BASE_URL = "https://seffaflik.epias.com.tr/electricity-service/v1"


def credentials() -> dict[str, str]:
    tree = ast.parse((ROOT / "backend/app/core/config.py").read_text(encoding="utf-8"))
    values = {
        node.target.id: ast.literal_eval(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id in {"EPIAS_USERNAME", "EPIAS_PASSWORD"}
    }
    return {"username": values["EPIAS_USERNAME"], "password": values["EPIAS_PASSWORD"]}


def add_months(value: date, months: int) -> date:
    index = value.month - 1 + months
    year, month = value.year + index // 12, index % 12 + 1
    return value.replace(year=year, month=month, day=min(value.day, monthrange(year, month)[1]))


def chunks(start: date, end: date):
    current = start
    while current <= end:
        next_start = add_months(current, 3)
        chunk_end = min(end, next_start - timedelta(days=1))
        yield current, chunk_end
        current = chunk_end + timedelta(days=1)


def sheet_name(name: str, powerplant_id: int, used: set[str]) -> str:
    base = re.sub(r"[\\/*?:\[\]]", "_", name).strip()[:25] or f"JES_{powerplant_id}"
    candidate = base
    suffix = 1
    while candidate in used:
        suffix += 1
        candidate = f"{base[:28]}_{suffix}"
    used.add(candidate)
    return candidate


def main() -> None:
    session = requests.Session()
    auth = session.post("https://giris.epias.com.tr/cas/v1/tickets", data=credentials(), headers={"Accept": "text/plain"}, timeout=30)
    auth.raise_for_status()
    headers = {"TGT": auth.text.strip(), "Accept": "application/json", "Content-Type": "application/json"}
    plants_response = session.get(f"{BASE_URL}/generation/data/injection-quantity-powerplant-list", headers=headers, timeout=60)
    plants_response.raise_for_status()
    candidates = [plant for plant in plants_response.json().get("items", []) if re.search(r"jes|jeotermal", plant.get("name") or "", re.IGNORECASE)]
    workbook = Workbook(write_only=True)
    used_names: set[str] = set()
    total_chunks = len(candidates) * len(list(chunks(date(2019, 1, 1), date.today())))
    completed = 0
    LOG.write_text("", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"Candidates: {len(candidates)}, chunks: {total_chunks}\n")
        for plant in candidates:
            buffered_rows: list[list[object]] = []
            worksheet = None
            for start, end in chunks(date(2019, 1, 1), date.today()):
                body = {"powerplantId": plant["id"], "startDate": f"{start:%Y-%m-%d}T00:00:00+03:00", "endDate": f"{end:%Y-%m-%d}T23:59:59+03:00"}
                for attempt in range(3):
                    try:
                        response = session.post(f"{BASE_URL}/generation/data/injection-quantity", headers=headers, json=body, timeout=90)
                        response.raise_for_status()
                        items = response.json().get("items", [])
                        break
                    except requests.RequestException:
                        if attempt == 2:
                            raise
                        sleep_time.sleep(3 * (attempt + 1))
                rows = [[item.get("date"), item.get("hour"), item.get("total"), item.get("geothermal")] for item in items]
                if worksheet is None:
                    buffered_rows.extend(rows)
                    if any((row[3] or 0) > 0 for row in buffered_rows):
                        worksheet = workbook.create_sheet(sheet_name(plant.get("name") or "JES", plant["id"], used_names))
                        worksheet.append(["Santral ID", plant["id"], "Santral", plant.get("name")])
                        worksheet.append(["Tarih", "Saat", "UEVM Toplam (MWh)", "Jeotermal UEVM (MWh)"])
                        for row in buffered_rows:
                            worksheet.append(row)
                        buffered_rows.clear()
                else:
                    for row in rows:
                        worksheet.append(row)
                completed += 1
                log.write(f"{completed}/{total_chunks}: {plant['id']} {start}..{end}\n")
                log.flush()
                sleep_time.sleep(0.25)
    if not workbook.worksheets:
        raise RuntimeError("No plant with positive geothermal UEVM was found.")
    workbook.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        LOG.write_text(f"FAILED: {type(exc).__name__}: {exc}\n", encoding="utf-8", append=False) if False else None
        print(f"Export failed: {type(exc).__name__}", file=sys.stderr)
        raise
