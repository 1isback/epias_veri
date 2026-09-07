from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.api.deps import get_current_user
from app.models.user import User
from app.operations.sync_manager import sync_manager
from app.core.metrics import metrics
from app.integrations.epias.client import EpiasClient
from datetime import datetime
import pytz

router = APIRouter()

@router.get("/status")
async def get_dashboard_status(current_user: User = Depends(get_current_user)):
    return {
        "active_syncs": list(sync_manager.active_syncs),
        "total_api_requests": metrics.api_request_count,
        "failed_imports": metrics.failed_imports
    }

@router.get("/overview")
async def get_dashboard_overview(current_user: User = Depends(get_current_user)):
    # Fetch today's data from EpiasClient
    istanbul_tz = pytz.timezone('Europe/Istanbul')
    today_str = datetime.now(istanbul_tz).strftime("%Y-%m-%d")
    
    try:
        raw_data = await EpiasClient.fetch_data("ptf", today_str, today_str)
    except Exception as e:
        # Fallback to empty if api fails
        print(f"Error fetching PTF: {e}")
        raw_data = []

    # Calculate KPIs
    tl_prices = [item['price'] for item in raw_data if 'price' in item]
    usd_prices = [item['priceUsd'] for item in raw_data if 'priceUsd' in item]
    eur_prices = [item['priceEur'] for item in raw_data if 'priceEur' in item]
    
    avg_ptf = sum(tl_prices) / len(tl_prices) if tl_prices else 0
    max_ptf = max(tl_prices) if tl_prices else 0
    min_ptf = min(tl_prices) if tl_prices else 0

    avg_usd = sum(usd_prices) / len(usd_prices) if usd_prices else 0
    avg_eur = sum(eur_prices) / len(eur_prices) if eur_prices else 0

    kpis = [
        {
            "id": "kpi_ptf_avg",
            "title": "Ortalama PTF",
            "value": f"{avg_ptf:,.2f}",
            "unit": "TL/MWh",
            "trend": {"value": 0, "isPositive": True},
            "sparklineData": [{"time": str(i), "value": p} for i, p in enumerate(tl_prices)]
        },
        {
            "id": "kpi_ptf_max",
            "title": "Maksimum PTF",
            "value": f"{max_ptf:,.2f}",
            "unit": "TL/MWh",
            "trend": {"value": 0, "isPositive": True},
            "sparklineData": [{"time": str(i), "value": p} for i, p in enumerate(tl_prices)]
        },
        {
            "id": "kpi_ptf_min",
            "title": "Minimum PTF",
            "value": f"{min_ptf:,.2f}",
            "unit": "TL/MWh",
            "trend": {"value": 0, "isPositive": False},
            "sparklineData": [{"time": str(i), "value": p} for i, p in enumerate(tl_prices)]
        }
    ]

    # Format chart data
    chart_data = []
    for item in raw_data:
        try:
            # item['date'] format is usually "2023-01-01T00:00:00+0300"
            date_str = item.get('date', '')
            if 'T' in date_str:
                time_str = date_str.split('T')[1][:5] # Get "00:00"
            else:
                time_str = date_str
                
            chart_data.append({
                "time": time_str,
                "mcp": item.get('price', 0),
                "mcpUsd": item.get('priceUsd', 0),
                "mcpEur": item.get('priceEur', 0)
            })
        except Exception:
            pass

    alerts = []
    if max_ptf > 3000:
        alerts.append({
            "id": "alert_1",
            "type": "Fiyat",
            "message": "PTF 3000 TL/MWh sınırını aştı",
            "location": "Piyasa",
            "timestamp": "Bugün",
            "severity": "warning",
            "value": f"{max_ptf:,.2f} TL"
        })

    assets = [] # No actual asset data available yet
    interconnectors = [] # No interconnector data available yet

    return {
        "kpis": kpis,
        "chartData": chart_data,
        "alerts": alerts,
        "assets": assets,
        "interconnectors": interconnectors
    }
