# Kuryecini Ops Co-Pilot - Kullanım Kılavuzu

## 📋 Genel Bakış

**Kuryecini Ops Co-Pilot**, panel-bazlı (müşteri/işletme/kurye/admin) sistem teşhis ve sorun çözme asistanıdır. Yapılandırılmış 7-blok formatında Türkçe tanılama raporları üretir.

### ✨ Özellikler

- ✅ **7-Blok Yapılandırılmış Yanıt**: Hızlı Teşhis → Derin RCA → Kontrol Komutları → Patch → Test → İzleme & Alarm → DoD
- ✅ **Panel-Aware Context**: Seçilen panele özgü analiz ve çözüm önerileri
- ✅ **Emergent LLM Key Entegrasyonu**: Tek key ile OpenAI modellerine erişim
- ✅ **Manuel Tool Desteği**: http_get, logs_tail, db_query, env_list
- ✅ **Preset Questions**: Yaygın sorunlar için hazır şablonlar
- ✅ **PII Redaction**: Otomatik kişisel veri maskeleme

---

## 🚀 Hızlı Başlangıç

### Backend Endpoint

```http
POST /api/admin/ai/assist
Content-Type: application/json

{
  "panel": "müşteri|işletme|kurye|admin|multi",
  "message": "Sorun tanımı",
  "model": "gpt-4o-mini"  // Optional
}
```

### Response Format

```json
{
  "response": "# Hızlı Teşhis\n• Durum: ...\n• Etki: ...\n• Öncelik: P0|P1|P2\n\n# Derin RCA (olasılık matrisi)\n...",
  "panel": "müşteri"
}
```

---

## 📊 7-Blok Yapısı

### 1️⃣ Hızlı Teşhis
- **Durum**: Sorunun kısa açıklaması
- **Etki**: Hangi kullanıcı/sistem etkileniyor
- **Öncelik**: P0 (Kritik), P1 (Yüksek), P2 (Orta)

### 2️⃣ Derin RCA (Root Cause Analysis)
| Neden | Panel | Kanıt/İpucu | Olasılık | Nasıl Doğrularım |
|---|---|---|---|---|
| ... | ... | ... | Yüksek/Orta/Düşük | ... |

### 3️⃣ Kontrol Komutları (Kopyala-Çalıştır)
```bash
# Bash/cURL/MongoDB komutları
curl -X GET http://localhost:8001/health
```

### 4️⃣ Patch (Mini)
```diff
--- a/backend/routes/orders.py
+++ b/backend/routes/orders.py
@@ -45,7 +45,7 @@
-    city = "Istanbul"  # hardcoded
+    city = request.city  # from request
```
**Neden bu değişiklik?** Açıklama...

### 5️⃣ Test
```python
def test_happy_path():
    # ...

def test_error_case():
    # ...
```

### 6️⃣ İzleme & Alarm
- `latency_p95 < 300ms` (uyarı ≥ 350ms)
- `error_rate < %1` (kritik ≥ %3)

### 7️⃣ DoD (Definition of Done)
- [ ] Testler yeşil
- [ ] Metrik < target
- [ ] Prod'a deploy edildi

---

## 🎯 Panel Seçenekleri

### `müşteri` (Customer)
**Odak**: Restoran keşfi, sepet/checkout, kupon, sipariş takibi

**Dosya Kalıpları**: customer, restaurant, menu, cart, order, checkout

**Örnek Sorular**:
- "restoranlar gözükmüyor, nasıl çözebilirim?"
- "sepet boş görünüyor ama API 200 dönüyor"
- "adresler yüklenmiyor, 403 hatası"

### `işletme` (Business)
**Odak**: Sipariş liste/onay, menü yönetimi, çalışma saatleri, SLA

**Dosya Kalıpları**: business, order_confirm, menu_manager, working_hours

**Örnek Sorular**:
- "yeni siparişler görünmüyor"
- "menü ekleme butonu çalışmıyor"
- "sipariş onaylama 500 hatası veriyor"

### `kurye` (Courier)
**Odak**: Görev kabul, WS bağlantısı, rota/konum, ETA

**Dosya Kalıpları**: courier, task, location, route, delivery

**Örnek Sorular**:
- "bekleyen görevler listesi boş"
- "WebSocket bağlantısı kopuyor"
- "konum güncellemeleri gelmiyor"

### `admin` (Admin)
**Odak**: Sistem ayarları, KYC, analitik, monitoring

**Dosya Kalıpları**: admin, kyc, analytics, settings, monitoring

**Örnek Sorular**:
- "KYC onay süreci çalışmıyor"
- "sistem metrikleri yüklenmiyor"
- "bakım modu aktif etme başarısız"

### `multi` (Cross-Panel)
**Odak**: Paneller arası karşılaştırma, çapraz etki

**Örnek Sorular**:
- "tüm panellerde yavaşlama var"
- "müşteri siparişi işletme paneline düşmüyor"
- "kurye görevi oluşturulmuyor"

---

## 🛠️ Manuel Tool'lar

### 1. `http_get` - HTTP GET ile Endpoint Doğrulama

**Kullanım**:
```bash
POST /api/admin/ai/tools/http_get
{
  "url": "http://localhost:8001/health",
  "headers": {}  // Optional
}
```

**Response**:
```json
{
  "status": 200,
  "text": "{\"status\":\"ok\"}"
}
```

### 2. `logs_tail` - Uygulama Loglarından Son N Satır

**Kullanım**:
```bash
POST /api/admin/ai/tools/logs_tail
{
  "path": "/var/log/supervisor/backend.out.log",
  "limit": 100
}
```

**Response**:
```json
{
  "lines": ["...", "..."]
}
```

### 3. `db_query` - MongoDB Readonly Sorgu

**Kullanım**:
```bash
POST /api/admin/ai/tools/db_query
{
  "collection": "businesses",
  "action": "count",  // count|find_one|list_indexes
  "filter": {"status": "active"}
}
```

**Response**:
```json
{
  "count": 25
}
```

### 4. `env_list` - ENV Değişkenlerini Listele (Maskeli)

**Kullanım**:
```bash
GET /api/admin/ai/tools/env_list?mask=true
```

**Response**:
```json
{
  "MONGO_URL": "***",
  "EMERGENT_LLM_KEY": "***",
  "NODE_ENV": "development"
}
```

---

## 🔐 Authentication & RBAC

**Gerekli Roller**: SuperAdmin, Operasyon

**Authentication Method**: Cookie-based (inherited from admin session)

**Endpoints**:
- `POST /api/admin/ai/assist` - RBAC: Admin only
- `POST /api/admin/ai/tools/*` - RBAC: Admin only

---

## 🎨 Frontend Kullanımı

### 1. Admin Panel → Araçlar → Ops Co-Pilot

![Ops Co-Pilot UI](https://via.placeholder.com/800x400?text=Ops+Co-Pilot+UI)

### 2. Panel Seçimi
- Dropdown'dan panel seçin (müşteri/işletme/kurye/admin/multi)

### 3. Sorun Tanımı
- Textarea'ya sorunu yazın veya preset seçin
- Ctrl+Enter ile gönder

### 4. Yanıt İnceleme
- 7-blok yapılandırılmış yanıt
- Markdown formatında gösterim
- Kopyala butonu ile paylaşma

### 5. Manuel Tool Kullanımı (Opsiyonel)
- Tool butonlarına tıklayın
- Parametreleri girin
- Sonuçlar yanıt alanına eklenir

---

## 📝 Örnek Kullanım Senaryoları

### Senaryo 1: Restoran Listesi Boş (Müşteri Paneli)

**Input**:
```json
{
  "panel": "müşteri",
  "message": "restoranlar gözükmüyor, nasıl çözebilirim?"
}
```

**Output** (7-blok):
```markdown
# Hızlı Teşhis
• Durum: Müşteri panelinde restoran listesi boş dönüyor.
• Etki: Keşfet akışı blok.
• Öncelik: P0

# Derin RCA (olasılık matrisi)
| Neden | Panel | Kanıt/İpucu | Olasılık | Nasıl Doğrularım |
|---|---|---|---|---|
| API 200 ama [] | müşteri | /restaurants boş | Yüksek | http_get /restaurants?lat=<>&lng=<> |
| Konum alamıyor | müşteri | permission denied | Orta | console, feature flag |
| 2dsphere yok | müşteri | geoNear fail | Orta | db_query list_indexes |

# Kontrol Komutları (Kopyala-Çalıştır)
\`\`\`bash
# Backend health check
curl -X GET http://localhost:8001/api/health

# Test restaurant endpoint
curl -X GET "http://localhost:8001/api/restaurants?lat=41.0082&lng=28.9784"

# Check DB collection
db.businesses.countDocuments({ status: "active" })
\`\`\`

# Patch (Mini)
\`\`\`diff
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
\`\`\`
**Neden bu değişiklik?** Geo-spatial query yoktu, tüm restoranları çekiyordu.

# Test
\`\`\`python
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
\`\`\`

# İzleme & Alarm
- `restaurant_list_latency_p95 < 200ms` (uyarı ≥ 250ms)
- `restaurant_list_empty_rate < 5%` (uyarı ≥ 10%)

# DoD (Kabul Kriterleri)
- [ ] Testler yeşil
- [ ] p95 < 200ms
- [ ] İstanbul'da en az 10 restoran dönmeli
- [ ] 2dsphere index oluşturuldu
```

---

## 🔧 Configuration

### Backend Environment Variables

```bash
# AI Diagnostics Panel Settings
EMERGENT_LLM_KEY=sk-emergent-c174948Bc5419E1746
AI_RATE_LIMIT_PER_MIN=6
DEFAULT_TIME_WINDOW_MIN=60

# AI Provider Settings
AI_PROVIDER=emergent
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=  # Optional custom OpenAI key
FEATURE_OPENAI_PROVIDER=true

# Repository Root for AI Dev Tools
REPO_ROOT=/app/backend,/app/frontend
```

### Frontend Feature Flags

```bash
REACT_APP_FEATURE_ADMIN_SETTINGS=true
REACT_APP_FEATURE_AI_SETTINGS=true
REACT_APP_FEATURE_PANEL_AI_ASSISTANT=true
REACT_APP_FEATURE_OPENAI_PROVIDER=true
```

---

## 🚨 Troubleshooting

### Issue 1: "API anahtarı eksik" Hatası

**Çözüm**:
1. Backend `.env` dosyasında `EMERGENT_LLM_KEY` değişkenini kontrol edin
2. Key doğru girildiğinden emin olun
3. Backend'i restart edin: `sudo supervisorctl restart backend`

### Issue 2: 7-Blok Formatı Eksik

**Çözüm**:
1. Master prompt doğru yüklendiğinden emin olun: `/app/backend/ops/system_prompt.md`
2. Few-shot örnekleri kontrol edin: `/app/backend/ops/fewshots.md`
3. Model yanıtını loglarda kontrol edin

### Issue 3: Tool Endpoints 422 Hatası

**Çözüm**:
1. Tool parametrelerini doğru girin (http_get: url required, db_query: collection + action required)
2. Backend logs: `tail -f /var/log/supervisor/backend.err.log`

---

## 📚 API Reference

### POST /api/admin/ai/assist

**Request Body**:
```typescript
{
  panel: "müşteri" | "işletme" | "kurye" | "admin" | "multi";
  message: string;  // max 2000 chars
  model?: string;   // default: "gpt-4o-mini"
}
```

**Response**:
```typescript
{
  response: string;  // 7-block Markdown formatted
  panel: string;
}
```

**Status Codes**:
- `200 OK`: Success
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Not admin
- `422 Validation Error`: Invalid request
- `500 Internal Server Error`: LLM error (with 7-block error response)

---

## 🎓 Best Practices

### 1. Panel Seçimi
- Sorunun hangi panelle ilgili olduğunu doğru belirleyin
- Multi-panel analizler için `multi` seçeneğini kullanın

### 2. Soru Formülasyonu
- Spesifik olun: "Restoran listesi boş" yerine "Müşteri panelinde İstanbul için restoran listesi boş dönüyor"
- Hata mesajlarını ekleyin: "404 hatası alıyorum"
- Hangi işlemden sonra oluştuğunu belirtin: "Sipariş Ver butonuna tıklayınca"

### 3. Yanıt İnceleme
- Kontrol Komutlarını önce çalıştırın
- Patch'i uygulamadan önce test edin
- DoD kriterlerini takip edin

### 4. Tool Kullanımı
- Manuel tool'ları sadece gerektiğinde kullanın
- Tool sonuçlarını LLM'e feedback olarak verin

---

## 🔄 Future Enhancements (Roadmap)

### Phase 2: Automatic Tool Calling
- OpenAI Function Calling entegrasyonu
- LLM'in tool'ları otomatik çağırması
- Multi-step reasoning

### Phase 3: Streaming Response
- SSE ile incremental yanıt
- Real-time progress indicators

### Phase 4: Tool Schema Expansion
- `read_file`: Dosya içeriği okuma
- `grep_code`: Kod içinde arama
- `run_test`: Test çalıştırma
- `deploy_patch`: Otomatik patch uygulama (confirmation required)

---

## 📞 Support

**Issues**: GitHub Issues (varsa)  
**Documentation**: `/app/README_ops_assistant.md`  
**Backend Logs**: `/var/log/supervisor/backend.err.log`  
**Frontend Logs**: Browser Console

---

## 📄 License

© 2025 Kuryecini - All rights reserved
