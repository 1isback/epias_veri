"""Small hand-curated overlay on top of the generated catalog.

`FEATURED_DATASET_IDS` surfaces the datasets people ask for most at the top of
the Explorer. `LEGACY_ALIASES` keeps the short ids the codebase used before the
catalog existed (``ptf``, ``smf`` …) pointing at their catalog entries so
`dashboard.py`, `data.py` and `sync_service.py` keep working unchanged.
"""

# Ordered: the Explorer renders them in this order under "Öne çıkanlar".
FEATURED_DATASET_IDS: list[str] = [
    "mcp-data",                 # Piyasa Takas Fiyatı (PTF)
    "system-marginal-price",    # Sistem Marjinal Fiyatı (SMF)
    "weighted-average-price",   # GİP Ağırlıklı Ortalama Fiyat
    "injection-quantity",       # UEVM
    "realtime-generation",      # Gerçek Zamanlı Üretim
    "realtime-consumption",     # Gerçek Zamanlı Tüketim
    "load-estimation-plan",     # Yük Tahmin Planı
    "consumption-quantity",     # Tüketim Miktarları
]

# legacy id -> catalog id
LEGACY_ALIASES: dict[str, str] = {
    "ptf": "mcp-data",
    "smf": "system-marginal-price",
    "injection_quantity": "injection-quantity",
    "injection_quantity_powerplant_list": "injection-quantity-powerplant-list",
}
