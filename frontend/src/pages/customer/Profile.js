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
            
            <div className="relative flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-20 h-20 bg-white/25 backdrop-blur-sm rounded-full flex items-center justify-center mr-6 shadow-lg">
                  <span className="text-4xl">👤</span>
                </div>
                <div>
                  <h1 className="text-3xl font-bold mb-2">Profilim</h1>
                  <p className="text-white/90 text-lg">Hesap bilgilerinizi ve avantajlarınızı yönetin</p>
                </div>
              </div>
              
              <Button 
                variant="outline" 
                onClick={onBack}
                className="bg-white/20 border-white/30 text-white hover:bg-white/30 rounded-xl backdrop-blur-sm"
              >
                ← Geri
              </Button>
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
};

export default Profile;