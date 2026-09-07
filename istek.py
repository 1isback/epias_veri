import requests
import pandas as pd
from datetime import datetime

# URL ve Header bilgileri
url = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "tgt": "TGT-4711776-swQdl5hDGuVoX85ckGl7hP77ZzCx0oiIZRtTm1sGIJ-XERRYcKuIh8jKq8q2Qzh2-xw-cas-675f69769c-g2cm9"
    }

# 1. Bugünü otomatik al
bugun = datetime.now().strftime('%Y-%m-%d')

# 2. İstek gövdesini bugünün tarihine göre oluştur
body = {
    "startDate": f"{bugun}T00:00:00+03:00",
    "endDate": f"{bugun}T23:59:59+03:00"
}

# İsteği gönder
response = requests.post(url, headers=headers, json=body)

if response.status_code == 200:
    data = response.json()

    # "items" verisini tabloya çevir
    if "items" in data:
        df = pd.DataFrame(data["items"])

        # Sadece ilgili sütunları göstermek isterseniz burayı özelleştirebilirsiniz
        # Örn: df = df[['date', 'mcp', 'mcpUsd']]

        print(f"\n--- {bugun} TARİHLİ PTF TABLOSU ---")
        print(df.to_string(index=False))
    else:
        print("Veri bulunamadı. Gelen mesaj:", data)
else:
    print(f"Hata! Durum Kodu: {response.status_code}")
    print("Hata Detayı:", response.text)