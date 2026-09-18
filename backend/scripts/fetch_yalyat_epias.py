"""Fetch the EPİAŞ Şeffaflık series for the YAL-YAT forecast dataset and merge them
into ``yalyat/birlesik_veriseti.xlsx``.

Scope was fixed with the user (2026-09-10): "çekirdek + opsiyonel" seri seti,
zaman aralığı olabildiğince eskiye (2017-01-01, DST-öncesi karmaşadan kaçınmak için).

What it does
------------
1. ``fetch``  – hits ~20 transparency endpoints in 90-day chunks, caches every raw
   response under ``yalyat/raw/<endpoint>/<start>.json`` so runs resume.
2. ``build``  – normalises every cached series to an hourly (Europe/Istanbul, naive)
   index, writes ``yalyat/epias_series_2017_now.csv`` (all fetched columns) and then
   merges onto the existing ``veriseti`` sheet:
     * existing rows keep their existing column values (NetTalimat, Tuketim,
       Tahmin_Tuketim, *_ilk_kgup, *_son_kgup, *_urt) untouched;
     * ``gunes_ilk_kgup`` nulls are filled from ``dpp-first-version`` (genuinely ~0
       before 2025 – see the data inventory artifact);
     * pre-2023 rows get NetTalimat / Tuketim / Tahmin_Tuketim / *_ilk_kgup /
       *_son_kgup from the API (``*_urt`` stays blank – that column uses the user's
       own recipe);
     * ~75 new columns (ptf, smf, sistem yönü, YAL/YAT kırılımı, dengesizlik,
       aFRR/FCR, nomine kapasite, RES üretim+tahmin, YEKDEM, rt_ üretim, EAK, KUDÜP).
   Output: ``yalyat/birlesik_veriseti_enriched.xlsx`` (+ ``.csv``).

Usage
-----
    python backend/scripts/fetch_yalyat_epias.py fetch
    python backend/scripts/fetch_yalyat_epias.py build
    python backend/scripts/fetch_yalyat_epias.py all
    python backend/scripts/fetch_yalyat_epias.py fetch --start 2023-01-01   # slice
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
ENV = ROOT / "backend" / ".env"
YALYAT = ROOT / "yalyat"
RAW = YALYAT / "raw"
SRC_XLSX = YALYAT / "birlesik_veriseti.xlsx"
OUT_XLSX = YALYAT / "birlesik_veriseti_enriched.xlsx"
OUT_CSV = YALYAT / "birlesik_veriseti_enriched.csv"
SERIES_CSV = YALYAT / "epias_series_2017_now.csv"

AUTH_URL = "https://giris.epias.com.tr/cas/v1/tickets"
BASE = "https://seffaflik.epias.com.tr/electricity-service/v1"

DEFAULT_START = date(2017, 1, 1)
# 28 days keeps every endpoint happy: some (YEKDEM licensed-realtime-generation)
# reject ranges > 1 calendar month (a 30-day window that straddles February trips it),
# and it keeps row counts well under a page.
CHUNK_DAYS = 28
PAGE_SIZE = 10000

# 14 KGÜP/üretim kaynak alanları – EPİAŞ dpp/dpp-first-version/sbfgp/aic ortak şeması
KGUP_FIELDS = [
    "toplam", "dogalgaz", "ruzgar", "linyit", "tasKomur", "ithalKomur", "fuelOil",
    "jeotermal", "barajli", "nafta", "biokutle", "akarsu", "gunes", "diger",
]

# ---------------------------------------------------------------------------
# endpoint table:  key -> (path, needs_region, is_subhourly)
# ---------------------------------------------------------------------------
ENDPOINTS: dict[str, tuple[str, bool, bool]] = {
    "yal":            ("/markets/bpm/data/order-summary-up", False, False),
    "yat":            ("/markets/bpm/data/order-summary-down", False, False),
    "system_dir":     ("/markets/bpm/data/system-direction", False, False),
    "smf":            ("/markets/bpm/data/system-marginal-price", False, False),
    "ptf":            ("/markets/dam/data/mcp", False, False),
    "gip_wap":        ("/markets/idm/data/weighted-average-price", False, False),
    "imb_qty":        ("/markets/imbalance/data/imbalance-quantity", False, False),
    "imb_amt":        ("/markets/imbalance/data/imbalance-amount", False, False),
    "afrr":           ("/markets/ancillary-services/data/secondary-frequency-capacity-amount", False, False),
    "fcr":            ("/markets/ancillary-services/data/primary-frequency-capacity-amount", False, False),
    "nom_cap":        ("/transmission/data/nominal-capacity", False, False),
    "res_fc":         ("/renewables/data/res-generation-and-forecast", False, True),
    "yekdem":         ("/renewables/data/licensed-realtime-generation", False, False),
    "eak":            ("/generation/data/aic", True, False),
    "kudup":          ("/generation/data/sbfgp", True, False),
    "kgup_ilk":       ("/generation/data/dpp-first-version", True, False),
    "kgup_son":       ("/generation/data/dpp", True, False),
    "rt_gen":         ("/generation/data/realtime-generation", False, False),
    "consumption":    ("/consumption/data/realtime-consumption", False, False),
    "lep":            ("/consumption/data/load-estimation-plan", False, False),
}


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------
def credentials() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("EPIAS_USERNAME="):
            out["username"] = line.split("=", 1)[1].strip()
        elif line.startswith("EPIAS_PASSWORD="):
            out["password"] = line.split("=", 1)[1].strip()
    if "username" not in out or "password" not in out:
        raise SystemExit("EPIAS_USERNAME / EPIAS_PASSWORD not found in backend/.env")
    return out


def get_tgt(session: requests.Session) -> str:
    resp = session.post(AUTH_URL, data=credentials(), headers={"Accept": "text/plain"}, timeout=30)
    resp.raise_for_status()
    return resp.text.strip()


def chunks(start: date, end: date):
    cur = start
    while cur <= end:
        nxt = min(end, cur + timedelta(days=CHUNK_DAYS - 1))
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def _post(session, headers, path, body):
    note = ""
    for attempt in range(8):
        try:
            resp = session.post(f"{BASE}{path}", headers=headers, json=body, timeout=180)
            if resp.status_code == 200:
                return resp.json()
            note = f"HTTP {resp.status_code}: {resp.text[:200]}"
            if resp.status_code == 401:
                headers["TGT"] = get_tgt(session)
            if resp.status_code == 400:  # bad request = genuinely no data for range
                return {"items": [], "_note": note}
            if resp.status_code == 429:  # throttled – back off hard
                time.sleep(45)
                continue
        except requests.RequestException as exc:
            note = f"{type(exc).__name__}: {exc}"
        wait = min(60, 4 * (attempt + 1))
        print(f"    retry {attempt + 1}/8 ({note}); sleep {wait}s", flush=True)
        time.sleep(wait)
    raise RuntimeError(f"{path} failed for {body.get('startDate')}: {note}")


def fetch_chunk(session, headers, path, needs_region, s: date, e: date) -> list[dict]:
    body = {
        "startDate": f"{s:%Y-%m-%d}T00:00:00+03:00",
        "endDate": f"{e:%Y-%m-%d}T23:59:59+03:00",
    }
    if needs_region:
        body["region"] = "TR1"

    first = _post(session, headers, path, {**body, "page": {"number": 1, "size": PAGE_SIZE}})
    items = list(first.get("items") or [])
    page = first.get("page") or {}
    total = page.get("total")
    if total and len(items) < total:
        pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
        for n in range(2, pages + 1):
            nxt = _post(session, headers, path, {**body, "page": {"number": n, "size": PAGE_SIZE}})
            items.extend(nxt.get("items") or [])
            time.sleep(0.15)
    return items


def cmd_fetch(start: date) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    # some endpoints (SMF, YEKDEM) reject an endDate that is not fully in the past
    end = date.today() - timedelta(days=1)
    session = requests.Session()
    headers = {"TGT": get_tgt(session), "Accept": "application/json", "Content-Type": "application/json"}
    chunk_list = list(chunks(start, end))
    print(f"range {start} .. {end}  ({len(chunk_list)} chunks x {len(ENDPOINTS)} endpoints)")

    for key, (path, needs_region, _sub) in ENDPOINTS.items():
        outdir = RAW / key
        outdir.mkdir(exist_ok=True)
        for s, e in chunk_list:
            cache = outdir / f"{s:%Y%m%d}.json"
            if cache.exists():
                continue
            items = fetch_chunk(session, headers, path, needs_region, s, e)
            cache.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            print(f"  {key:12} {s:%Y-%m-%d}  rows={len(items)}", flush=True)
            time.sleep(0.9)
    print("fetch complete")


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def _hour_index(row: dict) -> pd.Timestamp | None:
    """Best-effort hourly Europe/Istanbul (naive) timestamp from an EPİAŞ row."""
    d = row.get("date") or row.get("period")
    if not d:
        return None
    day = pd.Timestamp(str(d)).tz_localize(None).normalize()
    hv = row.get("hour")
    if hv is None:
        hv = row.get("time")
    if hv is None:
        return day
    if isinstance(hv, (int, float)):
        h, m = int(hv), 0
    else:
        s = str(hv)
        if "T" in s:
            t = pd.Timestamp(s)
            h, m = t.hour, t.minute
        else:
            parts = s.split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
    if h >= 24:
        return day + pd.Timedelta(hours=h, minutes=m)
    return day + pd.Timedelta(hours=h, minutes=m)


def _load_raw(key: str) -> pd.DataFrame:
    rows: list[dict] = []
    d = RAW / key
    if not d.exists():
        return pd.DataFrame()
    for f in sorted(d.glob("*.json")):
        rows.extend(json.loads(f.read_text(encoding="utf-8")))
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["ts"] = [_hour_index(r) for r in rows]
    df = df.dropna(subset=["ts"])
    return df


def _hourly(df: pd.DataFrame, cols: dict[str, str], subhourly: bool = False) -> pd.DataFrame:
    """Pick/rename ``cols`` (src->dst), collapse to one row per hour."""
    keep = [c for c in cols if c in df.columns]
    out = df[["ts", *keep]].copy()
    out["ts"] = out["ts"].dt.floor("h")  # collapse any sub-hourly stamps
    for c in keep:
        if out[c].dtype == object:
            conv = pd.to_numeric(out[c], errors="coerce")
            if conv.notna().sum() >= out[c].notna().sum():  # genuinely numeric
                out[c] = conv
    agg = "mean" if subhourly else "last"
    num = out.select_dtypes("number").columns
    gb = out.groupby("ts")
    res = gb[list(num)].agg(agg)
    for c in keep:
        if c not in num:
            res[c] = gb[c].last()
    res = res.rename(columns={s: d for s, d in cols.items() if s in res.columns})
    return res


def build_series() -> pd.DataFrame:
    parts: list[pd.DataFrame] = []

    # --- prices & direction -------------------------------------------------
    df = _load_raw("ptf")
    if not df.empty:
        parts.append(_hourly(df, {"price": "ptf", "priceUsd": "ptf_usd", "priceEur": "ptf_eur"}))
    df = _load_raw("smf")
    if not df.empty:
        parts.append(_hourly(df, {"systemMarginalPrice": "smf"}))
    df = _load_raw("gip_wap")
    if not df.empty:
        col = "weightedAveragePrice" if "weightedAveragePrice" in df.columns else "wap"
        parts.append(_hourly(df, {col: "gip_aof"}))
    df = _load_raw("system_dir")
    if not df.empty:
        parts.append(_hourly(df, {"systemDirection": "sistem_yonu", "smpDirectionId": "sistem_yonu_id"}))

    # --- YAL / YAT --------------------------------------------------------
    df = _load_raw("yal")
    if not df.empty:
        parts.append(_hourly(df, {
            "upRegulationZeroCoded": "yal_0", "upRegulationOneCoded": "yal_1",
            "upRegulationTwoCoded": "yal_2", "upRegulationDelivered": "yal_teslim",
            "net": "yal_net",
        }))
    df = _load_raw("yat")
    if not df.empty:
        parts.append(_hourly(df, {
            "downRegulationZeroCoded": "yat_0", "downRegulationOneCoded": "yat_1",
            "downRegulationTwoCoded": "yat_2", "downRegulationDelivered": "yat_teslim",
            "net": "yat_net",
        }))

    # --- imbalance (lagged) ----------------------------------------------
    df = _load_raw("imb_qty")
    if not df.empty:
        parts.append(_hourly(df, {"positiveImbalance": "dengesizlik_poz_mwh",
                                  "negativeImbalance": "dengesizlik_neg_mwh"}))
    df = _load_raw("imb_amt")
    if not df.empty:
        parts.append(_hourly(df, {"positiveImbalance": "dengesizlik_poz_tl",
                                  "negativeImbalance": "dengesizlik_neg_tl"}))

    # --- reserves -------------------------------------------------------
    df = _load_raw("afrr")
    if not df.empty:
        parts.append(_hourly(df, {"amount": "afrr_mw"}))
    df = _load_raw("fcr")
    if not df.empty:
        parts.append(_hourly(df, {"amount": "fcr_mw"}))

    # --- transmission --------------------------------------------------
    df = _load_raw("nom_cap")
    if not df.empty:
        parts.append(_hourly(df, {"bidQuantity": "nomine_ihracat_mw",
                                  "offerQuantity": "nomine_ithalat_mw"}))

    # --- RES üretim + tahmin (sub-hourly -> hourly mean) --------------
    df = _load_raw("res_fc")
    if not df.empty:
        parts.append(_hourly(df, {"generation": "res_gercek_mw", "forecast": "res_tahmin_mw"},
                             subhourly=True))

    # --- YEKDEM GZ üretim -------------------------------------------
    df = _load_raw("yekdem")
    if not df.empty:
        parts.append(_hourly(df, {
            "toplam": "yekdem_toplam", "ruzgar": "yekdem_ruzgar", "gunes": "yekdem_gunes",
            "jeotermal": "yekdem_jeotermal", "rezervuarli": "yekdem_rezervuarli",
            "nehirTipi": "yekdem_nehirtipi", "kanalTipi": "yekdem_kanaltipi",
            "biyokutle": "yekdem_biyokutle", "copGazi": "yekdem_copgazi",
            "biyogaz": "yekdem_biyogaz", "diger": "yekdem_diger",
        }))

    # --- realtime generation (canonical, rt_ prefix) --------------
    df = _load_raw("rt_gen")
    if not df.empty:
        parts.append(_hourly(df, {
            "total": "rt_toplam", "naturalGas": "rt_dogalgaz", "dammedHydro": "rt_barajli",
            "lignite": "rt_linyit", "river": "rt_akarsu", "importCoal": "rt_ithalkomur",
            "wind": "rt_ruzgar", "sun": "rt_gunes", "fueloil": "rt_fueloil",
            "geothermal": "rt_jeotermal", "asphaltiteCoal": "rt_asfaltit",
            "blackCoal": "rt_taskomur", "biomass": "rt_biokutle", "naphta": "rt_nafta",
            "lng": "rt_lng", "importExport": "rt_ithalat_ihracat", "wasteheat": "rt_atikisi",
        }))

    # --- EAK / KUDÜP per source ---------------------------------
    df = _load_raw("eak")
    if not df.empty:
        parts.append(_hourly(df, {f: f"eak_{f.lower()}" for f in KGUP_FIELDS}))
    df = _load_raw("kudup")
    if not df.empty:
        parts.append(_hourly(df, {f: f"kudup_{f.lower()}" for f in KGUP_FIELDS}))

    # --- API copies of the existing columns (for pre-2023 fill) --
    df = _load_raw("kgup_ilk")
    if not df.empty:
        parts.append(_hourly(df, {f: f"api_{f}_ilk_kgup" for f in KGUP_FIELDS}))
    df = _load_raw("kgup_son")
    if not df.empty:
        parts.append(_hourly(df, {f: f"api_{f}_son_kgup" for f in KGUP_FIELDS}))
    df = _load_raw("consumption")
    if not df.empty:
        parts.append(_hourly(df, {"consumption": "api_Tuketim"}))
    df = _load_raw("lep")
    if not df.empty:
        parts.append(_hourly(df, {"lep": "api_Tahmin_Tuketim"}))

    wide = pd.concat(parts, axis=1)
    wide = wide[~wide.index.duplicated(keep="first")].sort_index()
    full = pd.date_range(wide.index.min(), wide.index.max(), freq="h")
    wide = wide.reindex(full)
    wide.index.name = "DatetimeSaat"
    return wide


def cmd_build() -> None:
    wide = build_series()
    wide.to_csv(SERIES_CSV, encoding="utf-8-sig")
    print(f"raw series -> {SERIES_CSV}  shape={wide.shape}")

    # existing dataset -------------------------------------------------
    old = pd.read_excel(SRC_XLSX, sheet_name="veriseti")
    old["DatetimeSaat"] = pd.to_datetime(old["DatetimeSaat"])
    old = old.set_index("DatetimeSaat").sort_index()
    old_cols = list(old.columns)

    # master hourly index: union of both, continuous
    lo = min(old.index.min(), wide.index.min())
    hi = max(old.index.max(), wide.index.max())
    idx = pd.date_range(lo, hi, freq="h")
    merged = old.reindex(idx)
    merged.index.name = "DatetimeSaat"

    # 1) new columns straight from the API series
    api_cols = [c for c in wide.columns if not c.startswith("api_")]
    for c in api_cols:
        merged[c] = wide[c].reindex(idx)

    # 2) fill the existing "core" columns only where they are missing
    fill_map = {
        "NetTalimat": "yal_net",
        "Tuketim": "api_Tuketim",
        "Tahmin_Tuketim": "api_Tahmin_Tuketim",
    }
    for f in KGUP_FIELDS:
        fill_map[f"{f}_ilk_kgup"] = f"api_{f}_ilk_kgup"
        fill_map[f"{f}_son_kgup"] = f"api_{f}_son_kgup"

    filled_report: dict[str, int] = {}
    for dst, src in fill_map.items():
        if dst not in merged.columns:
            continue
        srcser = wide[src].reindex(idx) if src in wide.columns else pd.Series(index=idx, dtype=float)
        before = merged[dst].isna().sum()
        merged[dst] = merged[dst].where(merged[dst].notna(), srcser)
        filled_report[dst] = int(before - merged[dst].isna().sum())

    # drop the trailing rows past the last real observation (only forward LEP
    # forecast lands there), keeping the set aligned to the target column
    last_real = merged["NetTalimat"].last_valid_index()
    if last_real is not None:
        merged = merged.loc[:last_real]

    # Tarih / Saat helper columns for the whole (extended) range
    merged["Tarih"] = merged.index.strftime("%d-%b-%y")
    merged["Saat"] = merged.index.hour

    # column order: original layout first, then the new blocks
    new_cols = [c for c in merged.columns if c not in old_cols]
    merged = merged[[*old_cols, *new_cols]].reset_index()

    # --- write outputs (memory-frugal: CSV first, then stream to xlsx) ---
    n_rows = len(merged)
    d_min, d_max = merged["DatetimeSaat"].min(), merged["DatetimeSaat"].max()
    merged.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"csv -> {OUT_CSV}  ({n_rows:,} satır)")

    dd = _data_dictionary(old_cols, new_cols)
    miss = (
        merged.drop(columns=["DatetimeSaat", "Tarih", "Saat"])
        .isna().sum().rename("eksik_adet").to_frame()
    )
    miss["eksik_yuzde"] = (100 * miss["eksik_adet"] / n_rows).round(2)
    miss = miss.reset_index().rename(columns={"index": "kolon"})

    del merged, old, wide
    import gc
    gc.collect()

    _stream_to_xlsx(OUT_CSV, OUT_XLSX, {"kolon_sozlugu": dd, "eksik_ozet": miss})

    print(f"\nxlsx  -> {OUT_XLSX}")
    print(f"        satır {n_rows:,}   ({d_min} .. {d_max})")
    print(f"        kolon {len(old_cols)} -> {len(old_cols) + len(new_cols)}   (+{len(new_cols)} yeni)")
    print("\ndoldurulan mevcut kolonlar (yalnızca boş hücreler):")
    for k, v in filled_report.items():
        if v:
            print(f"   {k:22} +{v:,}")


def _stream_to_xlsx(csv_path: Path, xlsx_path: Path, extra_sheets: dict[str, pd.DataFrame]) -> None:
    """Write a large CSV to xlsx without loading it all into memory."""
    from openpyxl import Workbook

    wb = Workbook(write_only=True)
    ws = wb.create_sheet("veriseti")
    header_done = False
    for chunk in pd.read_csv(csv_path, chunksize=8000, low_memory=False,
                             parse_dates=["DatetimeSaat"]):
        if not header_done:
            ws.append(list(chunk.columns))
            header_done = True
        chunk["DatetimeSaat"] = chunk["DatetimeSaat"].astype("datetime64[us]").astype(object)
        chunk = chunk.astype(object).where(chunk.notna(), None)
        for row in chunk.itertuples(index=False, name=None):
            ws.append(list(row))
    for name, dfx in extra_sheets.items():
        wsx = wb.create_sheet(name)
        wsx.append(list(dfx.columns))
        for row in dfx.astype(object).where(dfx.notna(), None).itertuples(index=False, name=None):
            wsx.append(list(row))
    wb.save(xlsx_path)


def _data_dictionary(old_cols, new_cols) -> pd.DataFrame:
    notes = {
        "ptf": "Piyasa Takas Fiyatı – markets/dam/data/mcp .price (TL/MWh)",
        "ptf_usd": "PTF USD/MWh", "ptf_eur": "PTF EUR/MWh",
        "smf": "Sistem Marjinal Fiyatı – bpm/system-marginal-price (TL/MWh)",
        "gip_aof": "GİP Ağırlıklı Ortalama Fiyat – idm/weighted-average-price (TL/MWh)",
        "sistem_yonu": "Sistem yönü metni (Enerji Açığı/Fazlası/Dengede) – 4s gecikmeli",
        "sistem_yonu_id": "smpDirectionId (1=Açık,2=Dengede,3=Fazla)",
        "yal_0": "YAL 0 kodlu talimat (MWh)", "yal_1": "YAL 1 kodlu (kısıt) (MWh)",
        "yal_2": "YAL 2 kodlu (MWh)", "yal_teslim": "Teslim edilen toplam YAL (MWh)",
        "yal_net": "Net talimat (=NetTalimat, doğrulama)",
        "yat_0": "YAT 0 kodlu (MWh)", "yat_1": "YAT 1 kodlu (kısıt) (MWh)",
        "yat_2": "YAT 2 kodlu (MWh)", "yat_teslim": "Teslim edilen toplam YAT (negatif) (MWh)",
        "yat_net": "Net talimat (YAL-YAT), yal_net ile aynı",
        "dengesizlik_poz_mwh": "Pozitif dengesizlik miktarı (MWh) – ~1 ay uzlaştırma gecikmeli",
        "dengesizlik_neg_mwh": "Negatif dengesizlik miktarı (MWh) – gecikmeli",
        "dengesizlik_poz_tl": "Pozitif dengesizlik tutarı (TL) – gecikmeli",
        "dengesizlik_neg_tl": "Negatif dengesizlik tutarı (TL) – gecikmeli",
        "afrr_mw": "Sekonder frekans (aFRR) rezerv miktarı (MW) – 2019+",
        "fcr_mw": "Primer frekans (FCR) rezerv miktarı (MW) – 2019+",
        "nomine_ihracat_mw": "Nomine kapasite alış/ihracat (MW)",
        "nomine_ithalat_mw": "Nomine kapasite satış/ithalat (MW)",
        "res_gercek_mw": "Türkiye RES gerçekleşen üretim (MW) – 2020+, saatlik ort.",
        "res_tahmin_mw": "Türkiye RES üretim tahmini (MW) – 2020+, saatlik ort., ileriye dönük",
    }
    rows = []
    for c in old_cols:
        rows.append((c, "mevcut", "Orijinal birlesik_veriseti kolonu (değiştirilmedi; yalnızca boş hücreler API'den dolduruldu)"))
    for c in new_cols:
        if c in ("Tarih", "Saat"):
            continue
        n = notes.get(c)
        if n is None:
            if c.startswith("yekdem_"):
                n = f"YEKDEM lisanslı GZ üretim – {c[7:]} (MWh) – renewables/licensed-realtime-generation"
            elif c.startswith("rt_"):
                n = f"Gerçekleşen üretim (kanonik) – {c[3:]} (MWh) – generation/realtime-generation"
            elif c.startswith("eak_"):
                n = f"Emre Amade Kapasite – {c[4:]} (MW) – generation/aic, region=TR1"
            elif c.startswith("kudup_"):
                n = f"KUDÜP (GİP sonrası revize plan) – {c[6:]} (MW) – generation/sbfgp, region=TR1"
            else:
                n = ""
        rows.append((c, "yeni", n))
    return pd.DataFrame(rows, columns=["kolon", "tip", "aciklama"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["fetch", "build", "all"])
    ap.add_argument("--start", type=lambda s: datetime.strptime(s, "%Y-%m-%d").date(), default=DEFAULT_START)
    args = ap.parse_args()
    if args.command in ("fetch", "all"):
        cmd_fetch(args.start)
    if args.command in ("build", "all"):
        cmd_build()


if __name__ == "__main__":
    main()
