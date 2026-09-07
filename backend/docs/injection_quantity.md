# UEVM (Uzlaştırma Esas Veriş Miktarı)

Bu entegrasyon, mevcut `AuthenticationManager` üzerinden TGT alır ve aynı HTTP retry/timeout motorunu kullanır. TGT hiçbir API cevabına veya log kaydına yazılmaz.

Kullanılan EPİAŞ servisleri:

- `GET /v1/generation/data/injection-quantity-powerplant-list`
- `POST /v1/generation/data/injection-quantity`

EPİAŞ'ın teknik dokümanındaki UEVM body alanları `startDate`, `endDate`, `powerplantId` ve isteğe bağlı `page` alanlarıdır. Tarihler Europe/Istanbul zaman diliminde ISO-8601 (`+03:00`) biçiminde gönderilir. Cevap `items` altında `date`, `hour`, `total` ve kaynak-bazlı UEVM değerlerini içerir.

Sorgular en fazla üç takvim ayı olacak şekilde, bitişler dahil olacak biçimde parçalanır. Parçalar birbirini takip eder; örneğin `2025-01-01..2025-12-31` dört istek olur. Her chunk sıralı çağrılır. Bir çağrı başarısız olursa hiçbir veritabanı upsert'i yapılmaz; başarılı chunk'lar da yeniden işlenmez.

Tablolar:

- `injection_quantity_powerplants`: EPİAŞ santral referansları ve son senkronizasyon zamanı
- `injection_quantities`: saatlik UEVM satırları

`injection_quantities` içinde `epias_powerplant_id + interval_start` benzersizdir. PostgreSQL `ON CONFLICT DO UPDATE` ile tekrar senkronizasyonları upsert edilir.

## API

```bash
curl -X POST "http://localhost:8000/api/v1/generation/injection-quantity/powerplants/sync"

curl "http://localhost:8000/api/v1/generation/injection-quantity/powerplants?search=Santral&limit=100&offset=0"

curl -X POST "http://localhost:8000/api/v1/generation/injection-quantity/sync" \
  -H "Content-Type: application/json" \
  -d '{"powerplant_id":123,"start_date":"2026-01-01","end_date":"2026-12-31","force_refresh":false}'

curl "http://localhost:8000/api/v1/generation/injection-quantity?powerplant_id=123&start_date=2026-01-01&end_date=2026-01-31&limit=1000&offset=0"
```

## Migration ve test

```bash
cd backend
alembic upgrade head
python -m pytest tests -q
```

Migration öncesinde üretim veritabanının yedeğini alın. Dış EPİAŞ çağrıları testlerde mocklanmalıdır.
