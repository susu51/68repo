"""
Content & Media Seeder for Kuryecini Platform
Phase 2: Content Blocks and Media Assets Database Seeding
"""

import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/kuryecini')

async def seed_content_blocks():
    """Seed content_blocks collection with predefined content"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    # Content blocks data as specified in user requirements
    content_blocks = [
        {
            "_id": "home_admin",
            "title": "Yönetici Kontrol Merkezi",
            "sections": [
                {
                    "type": "stat_grid", 
                    "items": [
                        {"label": "Aktif Kurye", "value": 0},
                        {"label": "Aktif İşletme", "value": 0},
                        {"label": "Bugünkü Sipariş", "value": 0},
                        {"label": "Toplam Gelir", "value": 0}
                    ]
                },
                {
                    "type": "popular_products", 
                    "source": "db", 
                    "limit": 8,
                    "title": "Popüler Ürünler"
                },
                {
                    "type": "ad_boards", 
                    "items": [
                        {
                            "title": "Kampanya", 
                            "subtitle": "Yeni müşterilere özel %20 indirim",
                            "image": "/assets/campaigns/campaign1.jpg",
                            "cta": {
                                "text": "Detaylar", 
                                "href": "/admin/campaigns"
                            }
                        },
                        {
                            "title": "Kurye Alımı", 
                            "subtitle": "Hemen başvurun, hemen kazanmaya başlayın",
                            "image": "/assets/campaigns/courier-recruitment.jpg",
                            "cta": {
                                "text": "Başvuru Yap", 
                                "href": "/admin/couriers"
                            }
                        }
                    ]
                }
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "register_courier",
            "title": "Kurye Olun - Özgürce Kazanın",
            "subtitle": "Esnek çalışma saatleri, günlük ödeme, kendi patronunuz olun",
            "benefits": [
                "Günlük ödeme alın",
                "Esnek çalışma saatleri", 
                "Kendi rotanızı belirleyin",
                "Bonus ve teşviklerden yararlanın"
            ],
            "steps": [
                {"title": "Kayıt Olun", "description": "Bilgilerinizi girin ve hesap oluşturun"},
                {"title": "Kimlik Doğrulama", "description": "Belgelerinizi yükleyin ve onay bekleyin"},
                {"title": "Kazanmaya Başlayın", "description": "Siparişleri alın ve para kazanın"}
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "register_business", 
            "title": "İşletmenizi Büyütün",
            "subtitle": "Binlerce müşteriye ulaşın, satışlarınızı artırın",
            "benefits": [
                "Geniş müşteri kitlesi",
                "Kolay menü yönetimi",
                "Anlık sipariş bildirimleri", 
                "Detaylı satış raporları"
            ],
            "steps": [
                {"title": "Hesap Oluşturun", "description": "İşletme bilgilerinizi girin"},
                {"title": "Menüyü Hazırlayın", "description": "Ürünlerinizi ve fiyatlarını ekleyin"},
                {"title": "Satış Yapın", "description": "Siparişleri alın ve müşterilerinizi mutlu edin"}
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "register_customer",
            "title": "Kuryecini'ye Hoş Geldiniz",
            "subtitle": "En sevdiğiniz yemekleri kapınıza kadar getiriyoruz",
            "benefits": [
                "Hızlı teslimat",
                "Güvenli ödeme",
                "Binlerce restoran seçeneği",
                "7/24 müşteri desteği"
            ],
            "steps": [
                {"title": "Keşfedin", "description": "Yakınızdaki restoranları inceleyin"},
                {"title": "Sipariş Verin", "description": "Favorilerinizi seçin ve sepete ekleyin"},
                {"title": "Tadını Çıkarın", "description": "Siparişiniz kapınızda"}
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "customer_landing",
            "title": "Türkiye'nin En Hızlı Teslimat Platformu",
            "hero_text": "15 Dakikada Kapınızda!",
            "description": "Binlerce restoran, market ve mağazadan istediğinizi sipariş edin. Güvenli, hızlı ve uygun fiyatla!",
            "features": [
                {
                    "icon": "🚀",
                    "title": "Hızlı Teslimat",
                    "description": "Ortalama 15 dakikada teslimat"
                },
                {
                    "icon": "🔒", 
                    "title": "Güvenli Ödeme",
                    "description": "256-bit SSL şifreleme ile korumalı"
                },
                {
                    "icon": "📱",
                    "title": "Kolay Kullanım", 
                    "description": "Sezgisel arayüz ve tek tık sipariş"
                },
                {
                    "icon": "🎯",
                    "title": "Doğru Adres",
                    "description": "GPS destekli hassas konum belirleme"
                }
            ],
            "cta": {
                "primary": "Hemen Sipariş Ver",
                "secondary": "Yakındaki Restoranları Keşfet"
            },
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Clear existing content blocks
    await db.content_blocks.delete_many({})
    
    # Insert new content blocks
    result = await db.content_blocks.insert_many(content_blocks)
    print(f"✅ Inserted {len(result.inserted_ids)} content blocks")
    
    client.close()
    return len(result.inserted_ids)

async def seed_media_assets():
    """Seed media_assets collection with predefined media galleries"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.kuryecini
    
    # Media assets data as specified in user requirements
    media_assets = [
        {
            "_id": "courier_gallery",
            "title": "Kurye Galerisi",
            "description": "Kurye kayıt sayfası için görseller",
            "images": [
                "/assets/courier/c1.jpg",
                "/assets/courier/c2.jpg", 
                "/assets/courier/c3.jpg",
                "/assets/courier/delivery-bike.jpg",
                "/assets/courier/happy-courier.jpg"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "business_gallery", 
            "title": "İşletme Galerisi",
            "description": "İşletme kayıt sayfası için görseller",
            "images": [
                "/assets/business/r1.jpg",
                "/assets/business/r2.jpg",
                "/assets/business/restaurant-kitchen.jpg", 
                "/assets/business/chef-cooking.jpg",
                "/assets/business/food-preparation.jpg"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "customer_steps",
            "title": "Müşteri Adımları",
            "description": "Müşteri kayıt ve kullanım adımları görselleri", 
            "images": [
                "/assets/customer/step1.jpg",
                "/assets/customer/step2.jpg",
                "/assets/customer/step3.jpg",
                "/assets/customer/order-process.jpg",
                "/assets/customer/delivery-tracking.jpg"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "admin_assets",
            "title": "Yönetici Paneli Görselleri",
            "description": "Admin paneli için ikonlar ve görseller",
            "images": [
                "/assets/admin/dashboard-icon.svg",
                "/assets/admin/analytics-chart.jpg",
                "/assets/admin/user-management.jpg",
                "/assets/admin/settings-gear.svg"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "_id": "placeholder_images",
            "title": "Placeholder Görselleri", 
            "description": "Genel placeholder ve varsayılan görseller",
            "images": [
                "/assets/placeholder.jpg",
                "/assets/food-placeholder.jpg",
                "/assets/restaurant-placeholder.jpg",
                "/assets/user-avatar-placeholder.svg",
                "/assets/logo-placeholder.png"
            ],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Clear existing media assets
    await db.media_assets.delete_many({})
    
    # Insert new media assets
    result = await db.media_assets.insert_many(media_assets)
    print(f"✅ Inserted {len(result.inserted_ids)} media asset collections")
    
    client.close()
    return len(result.inserted_ids)

async def main():
    """Main seeding function"""
    print("🌱 Starting Content & Media Seeding...")
    
    try:
        # Seed content blocks
        content_count = await seed_content_blocks()
        print(f"📝 Content Blocks: {content_count} collections created")
        
        # Seed media assets  
        media_count = await seed_media_assets()
        print(f"🖼️ Media Assets: {media_count} galleries created")
        
        print(f"✅ Phase 2 Seeding Complete!")
        print(f"Total: {content_count + media_count} collections seeded")
        
    except Exception as e:
        print(f"❌ Seeding failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())