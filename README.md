# Kuryecini - Real-Time Delivery Platform

Modern kurye ve yemek teslimat platformu. **Gerçek MongoDB veritabanı** kullanır, mock data yoktur.

## 🚀 Özellikler

- **Gerçek Zamanlı Konum Takibi** (5 saniye güncellemeler)
- **Geospatial Sorgu Sistemi** (MongoDB 2dsphere)
- **JWT + RBAC Güvenlik** (customer, business, courier, admin)
- **Sipariş Durum Yönetimi** (CAS locking ile atomik)
- **Kazanç Hesaplama Sistemi** (admin ayarları ile)
- **Harita & Rota Sistemi** (OSRM + fallback polylines)

## 📋 Kurulum

### 1. Environment Setup

```bash
# Backend .env dosyasını kopyala
cp /app/backend/.env.example /app/backend/.env

# Gerekli değişkenleri ayarla:
MONGO_URL=mongodb://localhost:27017/kuryecini
JWT_SECRET=your_secure_secret_here
```

### 2. Database Initialize

```bash
cd /app/backend
python db_init.py
```

### 3. Servisleri Başlat

```bash
sudo supervisorctl restart all
```

## 🔧 API Endpoints

### Health Check
```bash
curl http://localhost:8001/api/health
```

### Test Authentication
```bash
# Admin Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@kuryecini.com","password":"KuryeciniAdmin2024!"}'
```

## 📊 Database Schema

### Collections
- **businesses** - İşletme bilgileri (2dsphere index)
- **menu_items** - Menü ürünleri
- **orders** - Siparişler (durum geçişleri)
- **courier_locations** - Kurye konumları (son 100 nokta)
- **earnings** - Kazanç kayıtları
- **settings** - Global platform ayarları

### Indexes
- `businesses.location` → 2dsphere (geospatial)
- `orders.status` → Durum sorguları için
- `courier_locations.ts` → Zamana göre sıralama

## 🎯 Implementation Phases

### ✅ Phase 1: Temel Altyapı
- MongoDB bağlantısı ve indexler
- JWT + RBAC güvenlik
- Health check endpoint
- Global settings sistemi

### 🔄 Phase 2: İşletme & Müşteri (Devam ediyor)
- Business menü CRUD
- Nearby restaurants (2dsphere)
- Sipariş oluşturma

### 📋 Phase 3: Kurye Sistemi (Planlı)
- Kurye konum tracking
- Sipariş kabul/teslim akışı
- Kazanç sistemi

### 🗺️ Phase 4: Canlı Harita (Planlı)
- WebSocket canlı takip
- OSRM routing entegrasyonu
- Frontend harita bileşenleri

### 🧪 Phase 5: Testing (Planlı)
- Playwright E2E testler
- API validation
- Performance tests

## 🔐 Güvenlik

- **JWT Tokens**: Tüm API endpoints korumalı
- **Role-Based Access**: customer/business/courier/admin
- **Rate Limiting**: IP ve kullanıcı bazlı
- **Input Validation**: Schema validation (Pydantic)
- **CAS Locking**: Atomik durum değişiklikleri

## 🌍 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URL` | - | MongoDB bağlantı URL'si (ZORUNLU) |
| `JWT_SECRET` | - | JWT token secret key (ZORUNLU) |
| `NEARBY_RADIUS_M` | 5000 | Yakın işletme arama yarıçapı (metre) |
| `COURIER_RATE_PER_PACKAGE` | 20 | Kurye paket başı kazanç (TL) |
| `BUSINESS_COMMISSION_PCT` | 5 | İşletme komisyon oranı (%) |
| `COURIER_UPDATE_SEC` | 5 | Kurye konum güncelleme aralığı |
| `COURIER_TIMEOUT_SEC` | 10 | Kurye konum timeout süresi |
| `OSRM_URL` | - | OSRM routing service URL (opsiyonel) |

## 📱 User Roles

### 👥 Customer
- Yakın restoran keşfetme
- Sipariş verme ve takip
- Gerçek zamanlı kurye konum takibi

### 🏪 Business
- Menü yönetimi (CRUD)
- Sipariş durum güncelleme
- Kazanç takibi

### 🚴 Courier
- Uygun siparişleri görme
- Sipariş kabul/teslim
- Konum paylaşımı (5 sn)
- Kazanç hesaplama

### 🛡️ Admin
- Sistem ayarları yönetimi
- Platform istatistikleri
- Kullanıcı yönetimi

## 🚫 Önemli Notlar

- **Mock Data YOK**: Tüm veriler gerçek MongoDB'den
- **localStorage YOK**: Veriler database'de kalıcı
- **Gerçek Geolocation**: 2dsphere indexleri ile
- **Production Ready**: RBAC güvenlik ve rate limiting

## 🔗 Useful Commands

```bash
# Database durumu
curl http://localhost:8001/api/health

# Backend logları
tail -f /var/log/supervisor/backend.*.log

# Frontend restart
sudo supervisorctl restart frontend

# Database reindex
python /app/backend/db_init.py
```