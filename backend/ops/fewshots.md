### FS1: Müşteri paneli — "restoranlar gözükmüyor"
# Hızlı Teşhis
• Durum: Müşteri panelinde restoran listesi boş dönüyor.
• Etki: Keşfet akışı blok.
• Öncelik: P0

# Derin RCA (olasılık matrisi)
| Neden | Panel | Kanıt/İpucu | Olasılık | Nasıl Doğrularım |
|---|---|---|---|---|
| API 200 ama [] | müşteri | /restaurants boş | Yüksek | http_get /restaurants?lat=<>&lng=<> |
| Konum alamıyor | müşteri | permission denied | Orta | console, feature flag |
| DB boş/şehir filtresi | admin | count=0/hardcode | Orta | db_query count/grep |
| 2dsphere yok | müşteri | geoNear fail | Orta | db_query list_indexes |

# Kontrol Komutları (Kopyala-Çalıştır)
```bash
# Backend health check
curl -X GET https://api.kuryecini.com/api/health

# Test restaurant endpoint
curl -X GET "https://api.kuryecini.com/api/restaurants?lat=41.0082&lng=28.9784"

# Check DB collection
db.businesses.countDocuments({ status: "active" })
db.businesses.getIndexes()
```

# Patch (Mini)
```diff
--- a/backend/routes/restaurants.py
+++ b/backend/routes/restaurants.py
@@ -25,7 +25,10 @@
 async def get_restaurants(lat: float, lng: float):
-    restaurants = await db.businesses.find({"status": "active"}).to_list(None)
+    restaurants = await db.businesses.find({
+        "status": "active",
+        "location": {"$near": {"$geometry": {"type": "Point", "coordinates": [lng, lat]}, "$maxDistance": 5000}}
+    }).to_list(100)
     return restaurants
```
**Neden bu değişiklik?** Geo-spatial query yoktu, tüm restoranları çekiyordu. 2dsphere index kullanarak yakındaki restoranları getir.

# Test
```python
# Test 1: Boş sonuç (uzak konum)
async def test_no_restaurants_far_location():
    resp = await client.get("/api/restaurants?lat=50.0&lng=50.0")
    assert resp.status_code == 200
    assert len(resp.json()) == 0

# Test 2: Mutlu yol (İstanbul)
async def test_restaurants_istanbul():
    resp = await client.get("/api/restaurants?lat=41.0082&lng=28.9784")
    assert resp.status_code == 200
    assert len(resp.json()) > 0
```

# İzleme & Alarm
- `restaurant_list_latency_p95 < 200ms` (uyarı ≥ 250ms)
- `restaurant_list_empty_rate < 5%` (uyarı ≥ 10%)
- Sentry: `event.type:error route:/restaurants`

# DoD (Kabul Kriterleri)
- [ ] Testler yeşil
- [ ] p95 < 200ms
- [ ] İstanbul'da en az 10 restoran dönmeli
- [ ] 2dsphere index oluşturuldu

---

### FS2: İşletme paneli — "Sipariş Ver butonu çalışmıyor"
# Hızlı Teşhis
• Durum: Müşteri "Sipariş Ver" butonuna tıkladığında 404 hatası.
• Etki: Sipariş akışı blok.
• Öncelik: P0

# Derin RCA (olasılık matrisi)
| Neden | Panel | Kanıt/İpucu | Olasılık | Nasıl Doğrularım |
|---|---|---|---|---|
| Double API prefix | müşteri | /api/api/orders | Yüksek | Network tab, grep |
| CORS hatası | müşteri | preflight fail | Orta | console log |
| Auth token eksik | müşteri | 401 | Orta | storage, jwt |

# Kontrol Komutları (Kopyala-Çalıştır)
```bash
# Grep "sipariş ver" butonunu
grep -r "Sipariş Ver" frontend/src/

# Grep API call
grep -r "/api/orders" frontend/src/

# Test endpoint
curl -X POST https://api.kuryecini.com/api/orders \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"restaurant_id":"...","items":[...]}'
```

# Patch (Mini)
```diff
--- a/frontend/src/pages/customer/CustomerApp.js
+++ b/frontend/src/pages/customer/CustomerApp.js
@@ -145,7 +145,7 @@
   const placeOrder = async () => {
-    const response = await fetch(`${BACKEND_URL}/api/orders`, {
+    const response = await fetch(`${BACKEND_URL}/orders`, {
       method: "POST",
       headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
       body: JSON.stringify(orderData)
```
**Neden bu değişiklik?** `BACKEND_URL` zaten `/api` içeriyor, double prefix oluşturuyordu.

# Test
```javascript
// Test 1: Sipariş oluşturma
test("Place order successfully", async () => {
  const order = { restaurant_id: "123", items: [{id: "item1", qty: 2}] };
  const resp = await placeOrder(order);
  expect(resp.status).toBe(200);
  expect(resp.data.order_id).toBeDefined();
});

// Test 2: Geçersiz sipariş
test("Reject invalid order", async () => {
  const order = { items: [] };
  const resp = await placeOrder(order);
  expect(resp.status).toBe(400);
});
```

# İzleme & Alarm
- `order_creation_success_rate > 95%` (uyarı ≤ 90%)
- `order_creation_latency_p95 < 500ms` (uyarı ≥ 700ms)
- Sentry: `event.type:error route:/orders method:POST`

# DoD (Kabul Kriterleri)
- [ ] "Sipariş Ver" butonu çalışıyor
- [ ] 200 dönüyor
- [ ] Order ID oluşturuluyor
- [ ] WebSocket notification tetikleniyor

---

### FS3: Kurye paneli — "Görev listesi boş"
# Hızlı Teşhis
• Durum: Kurye panelinde bekleyen görevler gözükmüyor.
• Etki: Kurye görev kabul edemiyor.
• Öncelik: P1

# Derin RCA (olasılık matrisi)
| Neden | Panel | Kanıt/İpucu | Olasılık | Nasıl Doğrularım |
|---|---|---|---|---|
| Status filtresi yanlış | kurye | pending != waiting | Yüksek | db_query, grep |
| Kurye ID null | kurye | courier_id undefined | Orta | console, auth |
| WebSocket koptu | kurye | onClose event | Orta | WS logs |

# Kontrol Komutları (Kopyala-Çalıştır)
```bash
# Check task collection
db.courier_tasks.find({ status: "pending" }).limit(5)
db.courier_tasks.find({ status: "waiting" }).limit(5)

# Grep status enum
grep -r "status.*waiting" backend/

# Test courier endpoint
curl -X GET https://api.kuryecini.com/api/courier/tasks?status=waiting \
  -H "Authorization: Bearer <courier_token>"
```

# Patch (Mini)
```diff
--- a/backend/routes/courier_tasks.py
+++ b/backend/routes/courier_tasks.py
@@ -18,7 +18,7 @@
 async def get_waiting_tasks(courier: dict = Depends(get_current_courier)):
-    tasks = await db.courier_tasks.find({"status": "pending"}).to_list(100)
+    tasks = await db.courier_tasks.find({"status": "waiting"}).to_list(100)
     return tasks
```
**Neden bu değişiklik?** Status enum'ı "waiting" iken query "pending" arıyordu.

# Test
```python
# Test 1: Waiting tasks döndürme
async def test_get_waiting_tasks():
    # Setup: Create waiting task
    await db.courier_tasks.insert_one({"order_id": "123", "status": "waiting"})
    
    resp = await client.get("/api/courier/tasks?status=waiting", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) > 0

# Test 2: Boş liste
async def test_no_waiting_tasks():
    resp = await client.get("/api/courier/tasks?status=waiting", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 0
```

# İzleme & Alarm
- `waiting_tasks_count > 0` (uyarı = 0 for > 10min)
- `task_assignment_latency_p95 < 30s` (uyarı ≥ 60s)
- Sentry: `event.type:error route:/courier/tasks`

# DoD (Kabul Kriterleri)
- [ ] Bekleyen görevler listeleniyor
- [ ] Status "waiting" ile filtreleniyor
- [ ] WebSocket bildirimleri çalışıyor
- [ ] Kurye görev kabul edebiliyor