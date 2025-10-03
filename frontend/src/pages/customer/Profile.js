import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { toast } from 'react-hot-toast';
import axios from 'axios';

const Profile = ({ user, onBack, onLogout }) => {
  const [activeTab, setActiveTab] = useState('profile'); // 'profile' | 'coupons' | 'discounts' | 'campaigns' | 'payment_methods'
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    birthDate: user?.birthDate || '',
    gender: user?.gender || ''
  });
  const [isUpdating, setIsUpdating] = useState(false);
  
  // New state for enhanced features
  const [coupons, setCoupons] = useState([]);
  const [discounts, setDiscounts] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [loading, setLoading] = useState(false);

  const API = process.env.REACT_APP_BACKEND_URL;

  const tabs = [
    { id: 'profile', name: 'Bilgilerim', icon: '👤' },
    { id: 'coupons', name: 'Kuponlarım', icon: '🎟️' },
    { id: 'discounts', name: 'İndirimlerim', icon: '💸' },
    { id: 'campaigns', name: 'Kampanyalar', icon: '🎉' },
    { id: 'payment_methods', name: 'Ödeme Yöntemlerim', icon: '💳' }
  ];

  // Load data for active tab
  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab]);

  const loadTabData = async (tab) => {
    if (tab === 'profile') return; // Profile data already loaded
    
    setLoading(true);
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      switch (tab) {
        case 'coupons':
          // Mock data for now - will be replaced with real API
          setCoupons([
            {
              id: 1,
              code: 'YENI20',
              description: '%20 İndirim - Yeni müşterilere özel',
              discountType: 'PERCENT',
              discountValue: 20,
              validUntil: '2025-02-28',
              minAmount: 50
            },
            {
              id: 2,
              code: 'SPRING15',
              description: '₺15 İndirim - Bahar kampanyası',
              discountType: 'AMOUNT',
              discountValue: 15,
              validUntil: '2025-03-31',
              minAmount: 75
            }
          ]);
          break;
          
        case 'discounts':
          setDiscounts([
            {
              id: 1,
              title: 'Sadık Müşteri İndirimi',
              description: '10+ sipariş verenlere özel %15 indirim',
              discountType: 'PERCENT',
              discountValue: 15,
              validUntil: '2025-06-30'
            },
            {
              id: 2,
              title: 'Hafta Sonu Özel',
              description: 'Hafta sonları ₺10 ekstra indirim',
              discountType: 'AMOUNT',
              discountValue: 10,
              validUntil: '2025-12-31'
            }
          ]);
          break;
          
        case 'campaigns':
          setCampaigns([
            {
              id: 1,
              title: 'Yaz Kampanyası',
              description: 'Tüm pizzalarda %25 indirim! Sıcak günlerde serin lezzetler.',
              discountType: 'PERCENT',
              discountValue: 25,
              validUntil: '2025-08-31',
              imageUrl: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400'
            },
            {
              id: 2,
              title: 'Hızlı Teslimat Garantisi',
              description: '30 dakikada kapınızda! Geç kalırsak ücretsiz.',
              validUntil: '2025-12-31',
              imageUrl: 'https://images.unsplash.com/photo-1526367790999-0150786686a2?w=400'
            }
          ]);
          break;
          
        case 'payment_methods':
          setPaymentMethods([
            {
              id: 1,
              provider: 'iyzico',
              brand: 'VISA',
              last4: '4242',
              token: 'pm_test_1234',
              createdAt: '2025-01-01'
            },
            {
              id: 2,
              provider: 'stripe',
              brand: 'MASTERCARD',
              last4: '5678',
              token: 'pm_test_5678',
              createdAt: '2024-12-15'
            }
          ]);
          break;
      }
    } catch (error) {
      console.error(`Error loading ${tab}:`, error);
      toast.error('Veri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setIsUpdating(true);
    
    try {
      // Mock API call - gerçek profil güncelleme API'si
      console.log('Updating profile:', profileData);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      toast.success('✅ Profiliniz güncellendi!');
      setIsEditing(false);
      
    } catch (error) {
      console.error('Profile update error:', error);
      toast.error('❌ Profil güncellenemedi. Tekrar deneyin.');
    } finally {
      setIsUpdating(false);
    }
  };

  const orderHistory = [
    {
      id: 1,
      restaurant: 'Pizzacı Ahmet',
      date: '2025-01-02',
      total: 67.50,
      status: 'Teslim Edildi',
      items: ['Margherita Pizza', 'Cola']
    },
    {
      id: 2,
      restaurant: 'Burger Palace',
      date: '2024-12-28',
      total: 45.00,
      status: 'Teslim Edildi',
      items: ['Cheeseburger', 'Patates']
    },
    {
      id: 3,
      restaurant: 'Sushi World',
      date: '2024-12-25',
      total: 89.00,
      status: 'İptal Edildi',
      items: ['California Roll', 'Miso Soup']
    }
  ];

  const renderTabContent = () => {
    if (loading) {
      return (
        <div className="text-center py-16">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Yükleniyor...</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'coupons':
        return renderCoupons();
      case 'discounts':
        return renderDiscounts();
      case 'campaigns':
        return renderCampaigns();
      case 'payment_methods':
        return renderPaymentMethods();
      default:
        return renderProfileInfo();
    }
  };

  const renderProfileInfo = () => (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Profile Information */}
      <Card className="border-0 shadow-lg rounded-2xl">
            <CardHeader>
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-800">👤 Kişisel Bilgiler</h2>
                <Button
                  onClick={() => isEditing ? setIsEditing(false) : setIsEditing(true)}
                  className={`${isEditing ? 'bg-gray-500 hover:bg-gray-600' : 'bg-blue-500 hover:bg-blue-600'} text-white rounded-lg`}
                >
                  {isEditing ? '❌ İptal' : '✏️ Düzenle'}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-semibold text-gray-700">Ad</Label>
                  {isEditing ? (
                    <Input
                      value={profileData.first_name}
                      onChange={(e) => setProfileData({...profileData, first_name: e.target.value})}
                      className="mt-1 rounded-xl border-gray-200"
                    />
                  ) : (
                    <p className="mt-1 p-3 bg-gray-50 rounded-xl font-medium">{profileData.first_name}</p>
                  )}
                </div>
                
                <div>
                  <Label className="text-sm font-semibold text-gray-700">Soyad</Label>
                  {isEditing ? (
                    <Input
                      value={profileData.last_name}
                      onChange={(e) => setProfileData({...profileData, last_name: e.target.value})}
                      className="mt-1 rounded-xl border-gray-200"
                    />
                  ) : (
                    <p className="mt-1 p-3 bg-gray-50 rounded-xl font-medium">{profileData.last_name}</p>
                  )}
                </div>
              </div>

              <div>
                <Label className="text-sm font-semibold text-gray-700">E-posta</Label>
                <p className="mt-1 p-3 bg-gray-50 rounded-xl font-medium text-gray-500">{profileData.email} (Değiştirilemez)</p>
              </div>

              <div>
                <Label className="text-sm font-semibold text-gray-700">Telefon</Label>
                {isEditing ? (
                  <Input
                    value={profileData.phone}
                    onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                    className="mt-1 rounded-xl border-gray-200"
                    placeholder="0555 123 4567"
                  />
                ) : (
                  <p className="mt-1 p-3 bg-gray-50 rounded-xl font-medium">{profileData.phone || 'Belirtilmemiş'}</p>
                )}
              </div>

              {isEditing && (
                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={() => setIsEditing(false)}
                    className="flex-1 bg-gray-500 hover:bg-gray-600 text-white rounded-xl"
                  >
                    İptal
                  </Button>
                  <Button
                    onClick={handleSaveProfile}
                    disabled={isUpdating}
                    className="flex-1 bg-green-500 hover:bg-green-600 text-white rounded-xl disabled:opacity-50"
                  >
                    {isUpdating ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        Kaydediliyor...
                      </>
                    ) : (
                      '✅ Kaydet'
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Account Actions */}
          <Card className="border-0 shadow-lg rounded-2xl">
            <CardHeader>
              <h2 className="text-xl font-bold text-gray-800">⚙️ Hesap Ayarları</h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button className="w-full justify-start bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-xl p-4 h-auto">
                <div className="flex items-center">
                  <span className="text-2xl mr-4">🔒</span>
                  <div className="text-left">
                    <div className="font-semibold">Şifre Değiştir</div>
                    <div className="text-sm opacity-70">Hesabınızın güvenliği için şifrenizi güncelleyin</div>
                  </div>
                </div>
              </Button>

              <Button className="w-full justify-start bg-green-50 hover:bg-green-100 text-green-700 border border-green-200 rounded-xl p-4 h-auto">
                <div className="flex items-center">
                  <span className="text-2xl mr-4">🔔</span>
                  <div className="text-left">
                    <div className="font-semibold">Bildirim Ayarları</div>
                    <div className="text-sm opacity-70">Sipariş durumu ve promosyon bildirimlerini yönetin</div>
                  </div>
                </div>
              </Button>

              <Button className="w-full justify-start bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-xl p-4 h-auto">
                <div className="flex items-center">
                  <span className="text-2xl mr-4">💳</span>
                  <div className="text-left">
                    <div className="font-semibold">Ödeme Yöntemleri</div>
                    <div className="text-sm opacity-70">Kredi kartı ve diğer ödeme seçeneklerini yönetin</div>
                  </div>
                </div>
              </Button>

              <hr className="my-4" />

              <Button 
                onClick={onLogout}
                className="w-full bg-red-500 hover:bg-red-600 text-white rounded-xl p-4 font-semibold"
              >
                🚪 Çıkış Yap
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Order History */}
        <Card className="mt-6 border-0 shadow-lg rounded-2xl">
          <CardHeader>
            <h2 className="text-xl font-bold text-gray-800">📋 Sipariş Geçmişi</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {orderHistory.map(order => (
                <div key={order.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mr-4">
                      <span className="text-xl">🍽️</span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-800">{order.restaurant}</h3>
                      <p className="text-sm text-gray-600">{order.items.join(', ')}</p>
                      <p className="text-xs text-gray-500">{order.date}</p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className="text-lg font-bold text-gray-800">₺{order.total.toFixed(2)}</p>
                    <p className={`text-sm font-medium ${
                      order.status === 'Teslim Edildi' ? 'text-green-600' :
                      order.status === 'İptal Edildi' ? 'text-red-600' :
                      'text-orange-600'
                    }`}>
                      {order.status}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderCoupons = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">🎟️ Kuponlarım</h2>
        <p className="text-gray-600">Mevcut kuponlarınızı görüntüleyin ve yönetin</p>
      </div>
      
      {coupons.length === 0 ? (
        <Card className="text-center py-16 border-0 shadow-lg rounded-2xl">
          <CardContent>
            <div className="text-6xl mb-4">🎟️</div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Henüz kuponunuz yok</h3>
            <p className="text-gray-600 mb-6">Yemek siparişlerinizde kullanabileceğiniz kuponlar burada görünecek</p>
            <Button className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-xl px-8">
              🎯 Kampanyaları İncele
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {coupons.map(coupon => (
            <Card key={coupon.id} className="border-0 shadow-lg rounded-2xl overflow-hidden bg-gradient-to-br from-orange-50 to-red-50">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-3xl">{coupon.icon}</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    coupon.status === 'active' ? 'bg-green-100 text-green-800' :
                    coupon.status === 'used' ? 'bg-gray-100 text-gray-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {coupon.status === 'active' ? 'Aktif' : 
                     coupon.status === 'used' ? 'Kullanıldı' : 'Süresi Doldu'}
                  </span>
                </div>
                
                <h3 className="font-bold text-lg text-gray-800 mb-2">{coupon.title}</h3>
                <p className="text-gray-600 text-sm mb-4">{coupon.description}</p>
                
                <div className="bg-white rounded-xl p-4 mb-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">%{coupon.discount}</div>
                    <div className="text-sm text-gray-500">İndirim</div>
                  </div>
                </div>
                
                <div className="text-xs text-gray-500 space-y-1">
                  <div>Minimum: ₺{coupon.minAmount}</div>
                  <div>Geçerlilik: {coupon.expiryDate}</div>
                  <div>Kod: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{coupon.code}</span></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const renderDiscounts = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">💸 İndirimlerim</h2>
        <p className="text-gray-600">Size özel indirimlerinizi kullanın</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {discounts.map(discount => (
          <Card key={discount.id} className="border-0 shadow-lg rounded-2xl">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">💸</span>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-500">
                    {discount.discountType === 'PERCENT' ? `%${discount.discountValue}` : `₺${discount.discountValue}`}
                  </div>
                  <div className="text-sm text-gray-500">İndirim</div>
                </div>
              </div>
              
              <h3 className="text-lg font-bold text-gray-800 mb-2">{discount.title}</h3>
              <p className="text-gray-600 text-sm mb-4">{discount.description}</p>
              
              <div className="flex justify-between text-sm text-gray-500">
                <span>Geçerlilik: {new Date(discount.validUntil).toLocaleDateString('tr-TR')}</span>
                <span className="text-green-600 font-medium">Aktif</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderCampaigns = () => (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">🎉 Kampanyalar</h2>
        <p className="text-gray-600">Güncel kampanya ve fırsatları kaçırmayın</p>
      </div>

      <div className="grid gap-6">
        {campaigns.map(campaign => (
          <Card key={campaign.id} className="border-0 shadow-lg rounded-2xl overflow-hidden">
            <div className="md:flex">
              {campaign.imageUrl && (
                <div className="md:w-1/3">
                  <img 
                    src={campaign.imageUrl} 
                    alt={campaign.title}
                    className="w-full h-48 md:h-full object-cover"
                  />
                </div>
              )}
              <CardContent className="p-6 md:w-2/3">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-gray-800">{campaign.title}</h3>
                  {campaign.discountValue && (
                    <div className="bg-red-500 text-white px-3 py-1 rounded-lg text-sm font-bold">
                      {campaign.discountType === 'PERCENT' ? `%${campaign.discountValue}` : `₺${campaign.discountValue}`} İndirim
                    </div>
                  )}
                </div>
                
                <p className="text-gray-600 mb-4">{campaign.description}</p>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    Son tarih: {new Date(campaign.validUntil).toLocaleDateString('tr-TR')}
                  </span>
                  <Button className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white rounded-xl">
                    🛍️ Kampanyaya Git
                  </Button>
                </div>
              </CardContent>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderPaymentMethods = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">💳 Ödeme Yöntemlerim</h2>
          <p className="text-gray-600">Kayıtlı ödeme yöntemlerinizi yönetin</p>
        </div>
        
        <Button 
          onClick={() => {
            toast.info('Yeni ödeme yöntemi ekleme özelliği yakında!');
          }}
          className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-xl"
        >
          ➕ Yeni Yöntem Ekle
        </Button>
      </div>

      {paymentMethods.length === 0 ? (
        <Card className="text-center py-16 border-0 shadow-lg rounded-2xl">
          <CardContent>
            <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">💳</span>
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">Henüz ödeme yönteminiz yok</h3>
            <p className="text-gray-600 mb-6">Hızlı ödeme için kart bilgilerinizi güvenle kaydedin</p>
            <Button className="bg-blue-500 hover:bg-blue-600 text-white rounded-xl">
              ➕ İlk Kartımı Ekle
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {paymentMethods.map(method => (
            <Card key={method.id} className="border-0 shadow-lg rounded-2xl">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mr-4 ${
                      method.brand === 'VISA' ? 'bg-blue-100' : 
                      method.brand === 'MASTERCARD' ? 'bg-red-100' : 'bg-gray-100'
                    }`}>
                      <span className="text-2xl">
                        {method.brand === 'VISA' ? '💳' : 
                         method.brand === 'MASTERCARD' ? '💳' : '💳'}
                      </span>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-gray-800">{method.brand}</div>
                      <div className="text-sm text-gray-500">**** **** **** {method.last4}</div>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={() => {
                      if (window.confirm('Bu ödeme yöntemini silmek istediğinize emin misiniz?')) {
                        setPaymentMethods(paymentMethods.filter(pm => pm.id !== method.id));
                        toast.success('Ödeme yöntemi silindi');
                      }
                    }}
                    className="bg-red-500 hover:bg-red-600 text-white w-10 h-10 rounded-full p-0"
                  >
                    🗑️
                  </Button>
                </div>
                
                <div className="text-xs text-gray-500 mb-2">
                  Sağlayıcı: {method.provider.charAt(0).toUpperCase() + method.provider.slice(1)}
                </div>
                <div className="text-xs text-gray-500">
                  Eklenme: {new Date(method.createdAt).toLocaleDateString('tr-TR')}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-red-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <Card className="mb-6 border-0 shadow-xl rounded-3xl bg-gradient-to-r from-purple-500 via-pink-500 to-red-500 text-white overflow-hidden">
          <CardContent className="p-8 relative">
            <div className="absolute inset-0 bg-white/10 opacity-40">
              <div className="absolute top-0 right-0 w-48 h-48 bg-white/20 rounded-full -mr-24 -mt-24"></div>
              <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/15 rounded-full -ml-16 -mb-16"></div>
            </div>
            
            <div className="relative z-10 flex items-center justify-between">
              <div className="flex items-center">
                <Button
                  onClick={onBack}
                  className="bg-white/20 hover:bg-white/30 text-white rounded-full w-12 h-12 p-0 mr-4 backdrop-blur-sm"
                >
                  ←
                </Button>
                
                <div>
                  <h1 className="text-3xl font-bold">👤 Profil</h1>
                  <p className="text-white/90 text-lg">Hesap ayarlarınızı yönetin</p>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-2xl font-bold">{profileData.first_name} {profileData.last_name}</div>
                <div className="text-white/80 text-sm">{profileData.email}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tab Navigation */}
        <Card className="mb-6 border-0 shadow-lg rounded-2xl">
          <CardContent className="p-6">
            <div className="flex gap-2 overflow-x-auto">
              {tabs.map(tab => (
                <Button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`min-w-fit rounded-xl px-6 py-3 font-semibold transition-all duration-300 ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {tab.icon} {tab.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Tab Content */}
        {renderTabContent()}

      </div>
    </div>
  );
};

export default Profile;