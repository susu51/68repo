# E2E Testing & Development Guide - Kuryecini

Bu dokümantasyon, Kuryecini platformunun end-to-end (E2E) test ortamını hazırlama ve test senaryolarını çalıştırma rehberidir.

## 📋 Test Kullanıcıları

Platform 4 farklı rol için test kullanıcıları içerir:

| Rol | Email | Şifre | Açıklama |
|-----|-------|-------|----------|
| **Admin** | admin@demo.com | Admin!234 | Platform yöneticisi |
| **İşletme** | business@demo.com | Biz!234 | Niğde Lezzet restoranı |
| **Kurye** | courier@demo.com | Kurye!234 | Motor kuryesi (motorbike) |
| **Müşteri** | customer@demo.com | Musteri!234 | Müşteri (Niğde'de adres) |

## 🗂️ Test Verileri

### Restoran: Niğde Lezzet
- **Konum**: Niğde Merkez (lat: 37.97, lng: 34.68)
- **Durum**: Onaylı (KYC approved)
- **Min. Sipariş**: ₺30
- **Teslimat Ücreti**: ₺10

### Menü (5 Ürün)
1. **Adana Kebap** - ₺85 (20 dk hazırlık)
2. **Mantı** - ₺65 (25 dk hazırlık)
3. **Lahmacun** - ₺25 (15 dk hazırlık)
4. **Ayran** - ₺8 (2 dk hazırlık)
5. **Baklava** - ₺45 (5 dk hazırlık)

### Müşteri Adresi
- **Adres**: Yeni Mahalle, Atatürk Caddesi No:42, Niğde Merkez
- **Konum**: (lat: 37.97, lng: 34.68)
- **Varsayılan**: Evet

## 🚀 Başlangıç

### 1. Veritabanını Seed Etme

```bash
# Backend dizinine git
cd /app/backend

# Seed script'i çalıştır
python seed_e2e_data.py
```

**Çıktı**:
```
✅ E2E database seeding completed successfully!
📋 TEST CREDENTIALS:
Admin:     admin@demo.com / Admin!234
Business:  business@demo.com / Biz!234
Courier:   courier@demo.com / Kurye!234
Customer:  customer@demo.com / Musteri!234
```

### 2. Veritabanını Sıfırlama (Development Only!)

⚠️ **UYARI**: Bu komut tüm verileri siler!

```bash
cd /app/backend
python seed_e2e_data.py --reset
# "RESET" yazıp onaylayın
```

### 3. Servisleri Başlatma

```bash
# Tüm servisleri başlat
sudo supervisorctl restart all

# Backend durumunu kontrol et
sudo supervisorctl status backend

# Frontend durumunu kontrol et
sudo supervisorctl status frontend
```

## 📊 Sipariş Akışı (Order Status Flow)

### Durum Makinesi

```
created 
  ↓ (İşletme: Confirm)
preparing 
  ↓ (İşletme: Ready)
ready_for_pickup
  ↓ (İşletme: Assign Courier)
courier_assigned
  ↓ (Kurye: Accept & Pickup)
picked_up
  ↓ (Kurye: Start Delivery)
delivering
  ↓ (Kurye: Complete)
delivered
```

### Role-Based Permissions

**İşletme (Business)**:
- `created` → `preparing`
- `preparing` → `ready_for_pickup`
- `ready_for_pickup` → `courier_assigned` (atama ile)

**Kurye (Courier)**:
- `courier_assigned` → `picked_up`
- `picked_up` → `delivering`
- `delivering` → `delivered`

## 🧪 E2E Test Senaryoları

### Senaryo 1: Tam Sipariş Akışı

**Amaç**: Müşteri sipariş verir, işletme onaylar, kurye teslim eder

**Adımlar**:
1. **Müşteri** giriş yapar (`customer@demo.com`)
2. Keşfet sayfasında "Niğde Lezzet"i bulur
3. Menüden 2 ürün sepete ekler (Kebap + Ayran)
4. Adres seçer (varsayılan: Niğde Merkez)
5. Ödeme yöntemi seçer (kapıda nakit)
6. Sipariş verir → Status: `created`

7. **İşletme** giriş yapar (`business@demo.com`)
8. "Gelen Siparişler" sayfasında yeni siparişi görür
9. Siparişi onayla → Status: `preparing`
10. Hazır olarak işaretle → Status: `ready_for_pickup`
11. Kurye ata → Status: `courier_assigned`

12. **Kurye** giriş yapar (`courier@demo.com`)
13. Atanan siparişi görür
14. Teslim al → Status: `picked_up`
15. Teslimat başlat → Status: `delivering`
16. Teslim et → Status: `delivered`

17. **Müşteri** siparişlerini kontrol eder
18. Timeline'da tüm durumları görmeli

**Beklenen Sonuç**:
- ✅ Tüm durum geçişleri başarılı
- ✅ Her rol sadece kendi izinli geçişleri yapabiliyor
- ✅ Gerçek zamanlı güncellemeler çalışıyor (WebSocket/SSE)

### Senaryo 2: Adres Değiştirme & Mesafe Filtreleme

**Amaç**: Adres değişince restoran listesi mesafe bazlı güncellenir

**Adımlar**:
1. **Müşteri** giriş yapar
2. "Adreslerim"e yeni adres ekler (farklı il: Ankara)
3. Keşfet sayfasına döner
4. Üst bardan Ankara adresini seçer
5. Restoran listesinin değiştiğini doğrular (Niğde restoranı uzakta/görünmez)
6. Niğde adresine geri döner
7. "Niğde Lezzet" restoranı yakınlarda görünür

**Beklenen Sonuç**:
- ✅ Adres seçimi açıkça görünüyor
- ✅ Mesafe bazlı sıralama çalışıyor
- ✅ Varsayılan İstanbul sapması YOK

### Senaryo 3: Role-Based Access Control (RBAC)

**Amaç**: Roller yalnızca kendi endpoint'lerine erişebilir

**Adımlar**:
1. **Müşteri** token'ı ile `/orders/:id/confirm` PATCH isteği → 403
2. **Kurye** başka kuryenin siparişine `/delivered` PATCH → 403
3. **İşletme** başka işletmenin siparişine erişim → 403

**Beklenen Sonuç**:
- ✅ Unauthorized işlemler 403 dönüyor
- ✅ JWT validation çalışıyor
- ✅ Role guard'lar aktif

### Senaryo 4: İşletme Panel - Ürün CRUD

**Amaç**: İşletme menü yönetimini yapabilir

**Adımlar**:
1. **İşletme** giriş yapar
2. Menü Yönetimi sayfasına gider
3. Yeni ürün ekler (form: ad, açıklama, fiyat, kategori)
4. Ürün listede görünür
5. Ürünü düzenler (fiyat değişikliği)
6. Ürünü siler
7. Silinen ürün listeden kaybolur

**Beklenen Sonuç**:
- ✅ CRUD işlemleri hatasız çalışıyor
- ✅ Loading durumları hiçbir formda asılı kalmıyor
- ✅ Optimistic UI güncellemeleri anında yansıyor
- ✅ Hata durumlarında anlamlı mesajlar gösteriliyor

### Senaryo 5: Gerçek Zamanlılık (Real-time)

**Amaç**: WebSocket/SSE ile canlı güncellemeler

**Adımlar**:
1. **Müşteri** siparişlerini görüntülüyor (timeline açık)
2. Aynı anda **İşletme** siparişi `preparing` yapıyor
3. Müşteri ekranında timeline ANINDA güncellenir (toast bildirimi)
4. **Kurye** `picked_up` yapıyor
5. Müşteri ekranı yine canlı güncellenir

**Beklenen Sonuç**:
- ✅ Event'ler 2 saniye içinde ulaşıyor
- ✅ Toast bildirimleri gösteriliyor
- ✅ Timeline otomatik güncelleniyor
- ✅ Reconnect stratejisi çalışıyor (connection drop test)

## 🔧 API Endpoints

### Sipariş (Orders)

```bash
# Sipariş oluşturma (Customer)
POST /api/orders
Authorization: Bearer {customer_token}
Body: {
  "business_id": "business-e2e-rest-001",
  "items": [{
    "product_id": "product-e2e-001",
    "title": "Adana Kebap",
    "price": 85.0,
    "quantity": 1
  }],
  "delivery_address": {...},
  "payment_method": "cash_on_delivery"
}

# Siparişlerimi getir (Customer)
GET /api/orders/my
Authorization: Bearer {customer_token}

# Sipariş durumu güncelle (Business/Courier)
PATCH /api/orders/{order_id}/status
Authorization: Bearer {business_token}
Body: {
  "from": "created",
  "to": "preparing"
}

# Gelen siparişler (Business)
GET /api/business/orders/incoming
Authorization: Bearer {business_token}

# Atanan siparişler (Courier)
GET /api/courier/orders/assigned
Authorization: Bearer {courier_token}
```

### Gerçek Zamanlılık

```bash
# SSE stream (Order updates)
GET /api/stream/orders?order_id={id}
Authorization: Bearer {token}

# WebSocket (Order tracking)
WS ws://localhost:8001/ws/orders/{order_id}
```

## 📝 Test Komutları (Backend)

```bash
# Login test (Customer)
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer@demo.com","password":"Musteri!234"}'

# Get menu items
curl http://localhost:8001/api/businesses/business-e2e-rest-001/menu

# Create order (token gerekli)
curl -X POST http://localhost:8001/api/orders \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## 🎭 Playwright E2E Tests (TODO)

```bash
# E2E testleri çalıştır
cd /app/frontend
npx playwright test

# Tek senaryo
npx playwright test --grep "Customer places order"

# Debug mode
npx playwright test --debug
```

## 🐛 Troubleshooting

### Sorun: "Restoran bulunamadı"
**Çözüm**: Seed script'i çalıştırın, 2dsphere index kontrolü yapın

### Sorun: "401 Unauthorized"
**Çözüm**: Login yapıp yeni token alın, cookie kontrolü yapın

### Sorun: "Loading asılı kalıyor"
**Çözüm**: Network tab'da API response kontrol edin, finally bloğu var mı?

### Sorun: "WebSocket bağlanamıyor"
**Çözüm**: Backend WebSocket endpoint'i aktif mi? CORS ayarları?

## 📚 Kaynak Dosyalar

- **Seed Script**: `/app/backend/seed_e2e_data.py`
- **Order Routes**: `/app/backend/routes/orders.py`
- **Order Status**: `/app/backend/routes/order_status.py`
- **Business Routes**: `/app/backend/routes/business.py`
- **WebSocket**: `/app/backend/websocket_manager.py`

## 🎯 Kabul Kriterleri

✅ Tüm test kullanıcıları login yapabiliyor
✅ Seed data başarıyla oluşturuluyor
✅ Sipariş akışı tüm durumları geçebiliyor
✅ RBAC guard'lar çalışıyor (403 kontrolü)
✅ Gerçek zamanlı güncellemeler 2 sn içinde ulaşıyor
✅ Adres değişince restoran listesi güncelleniyor (mesafe bazlı)
✅ Loading durumları hiçbir formda asılı kalmıyor
✅ E2E testler CI'da PASS (min 4 senaryo)

## 📞 İletişim & Destek

Bu guide ile ilgili sorularınız için lütfen ekip ile iletişime geçin.

---
**Son Güncelleme**: 2025-01-16
**Versiyon**: 1.0.0
