import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { toast } from 'react-hot-toast';
import { apiClient } from '../../utils/apiClient';

const ProfilePage = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || ''
  });

  // Profile tab data
  const [coupons, setCoupons] = useState([]);
  const [discounts, setDiscounts] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  
  // Modal states
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showAddressModal, setShowAddressModal] = useState(false);
  
  // Password change states
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  
  // Payment method states
  const [newPaymentMethod, setNewPaymentMethod] = useState({
    provider: 'stripe',
    card_number: '',
    expiry_month: '',
    expiry_year: '',
    cvv: '',
    cardholder_name: ''
  });
  
  // Address management states
  const [userAddresses, setUserAddresses] = useState([]);
  const [editingAddress, setEditingAddress] = useState(null);
  const [newAddress, setNewAddress] = useState({
    title: 'Ev',
    full_address: '',
    district: '',
    city: '',
    building_no: '',
    apartment_no: '',
    floor: '',
    instructions: '',
    phone: '',
    lat: null,
    lng: null,
    is_default: false
  });
  
  // Notification settings states
  const [notificationSettings, setNotificationSettings] = useState({
    push_notifications: true,
    email_notifications: true,
    order_updates: true,
    promotions: false
  });

  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Address management functions
  const handleSaveAddress = async () => {
    try {
      setLoading(true);
      
      const addressData = {
        ...newAddress,
        lat: newAddress.lat ? parseFloat(newAddress.lat) : null,
        lng: newAddress.lng ? parseFloat(newAddress.lng) : null
      };
      
      if (editingAddress) {
        // Update existing address
        await apiClient.put(`/customer/addresses/${editingAddress.id}`, addressData);
        toast.success('Adres başarıyla güncellendi');
      } else {
        // Create new address
        await apiClient.post('/customer/addresses', addressData);
        toast.success('Adres başarıyla eklendi');
      }
      
      // Reset form and reload addresses
      setNewAddress({
        title: 'Ev',
        full_address: '',
        district: '',
        city: '',
        building_no: '',
        apartment_no: '',
        floor: '',
        instructions: '',
        phone: '',
        lat: null,
        lng: null,
        is_default: false
      });
      setEditingAddress(null);
      setShowAddressModal(false);
      
      // Reload addresses
      loadTabData('addresses');
      
    } catch (error) {
      console.error('Address save error:', error);
      toast.error(editingAddress ? 'Adres güncellenirken hata oluştu' : 'Adres eklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleEditAddress = (address) => {
    setEditingAddress(address);
    setNewAddress({
      title: address.title || 'Ev',
      full_address: address.full_address || '',
      district: address.district || '',
      city: address.city || '',
      building_no: address.building_no || '',
      apartment_no: address.apartment_no || '',
      floor: address.floor || '',
      instructions: address.instructions || '',
      phone: address.phone || '',
      lat: address.lat || null,
      lng: address.lng || null,
      is_default: address.is_default || false
    });
    setShowAddressModal(true);
  };

  const handleDeleteAddress = async (addressId) => {
    if (!confirm('Bu adresi silmek istediğinizden emin misiniz?')) return;
    
    try {
      setLoading(true);
      await apiClient.delete(`/customer/addresses/${addressId}`);
      toast.success('Adres başarıyla silindi');
      loadTabData('addresses');
    } catch (error) {
      console.error('Address delete error:', error);
      toast.error('Adres silinirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefaultAddress = async (addressId) => {
    try {
      setLoading(true);
      await apiClient.patch(`/customer/addresses/${addressId}/default`);
      toast.success('Varsayılan adres güncellendi');
      loadTabData('addresses');
    } catch (error) {
      console.error('Default address error:', error);
      toast.error('Varsayılan adres güncellenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', name: 'Bilgilerim', icon: '👤' },
    { id: 'addresses', name: 'Adreslerim', icon: '📍' },
    { id: 'coupons', name: 'Kuponlarım', icon: '🎟️' },
    { id: 'discounts', name: 'İndirimlerim', icon: '💸' },
    { id: 'campaigns', name: 'Kampanyalar', icon: '🎉' },
    { id: 'payment_methods', name: 'Ödeme Yöntemlerim', icon: '💳' },
    { id: 'notifications', name: 'Bildirimler', icon: '🔔' }
  ];

  useEffect(() => {
    if (activeTab !== 'profile') {
      loadTabData(activeTab);
    }
  }, [activeTab]);

  const loadTabData = async (tab) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('kuryecini_access_token');

      if (!token) {
        // No token - show empty data instead of mock
        console.log('No authentication token - showing empty data');
        return;
      }

      const headers = { 'Authorization': `Bearer ${token}` };

      switch (tab) {
        case 'addresses':
          const addressesRes = await apiClient.get('/customer/addresses');
          setUserAddresses(addressesRes.data || []);
          break;
        case 'coupons':
          const couponsRes = await axios.get(`${API}/api/profile/coupons`, { headers });
          setCoupons(couponsRes.data || []);
          break;
        case 'discounts':
          const discountsRes = await axios.get(`${API}/api/profile/discounts`, { headers });
          setDiscounts(discountsRes.data || []);
          break;
        case 'campaigns':
          const campaignsRes = await axios.get(`${API}/api/campaigns`);
          setCampaigns(campaignsRes.data || []);
          break;
        case 'payment_methods':
          const paymentRes = await axios.get(`${API}/api/payment-methods`, { headers });
          setPaymentMethods(paymentRes.data || []);
          break;
      }
    } catch (error) {
      console.error(`Error loading ${tab}:`, error);
      // Don't load mock data - show empty state instead
    } finally {
      setLoading(false);
    }
  };

  const loadMockData = (tab) => {
    switch (tab) {
      case 'coupons':
        setCoupons(mockCoupons);
        break;
      case 'discounts':
        setDiscounts(mockDiscounts);
        break;
      case 'campaigns':
        setCampaigns(mockCampaigns);
        break;
      case 'payment_methods':
        setPaymentMethods(mockPaymentMethods);
        break;
    }
    setLoading(false);
  };

  const handleSaveProfile = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('kuryecini_access_token');

      if (!token) {
        toast.success('Profil bilgileri kaydedildi!');
        setIsEditing(false);
        return;
      }

      await axios.put(`${API}/api/profile`, profileData, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      toast.success('Profil bilgileri güncellendi!');
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error('Güncelleme sırasında hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    try {
      if (passwordData.newPassword !== passwordData.confirmPassword) {
        toast.error('Yeni şifreler eşleşmiyor');
        return;
      }

      if (passwordData.newPassword.length < 6) {
        toast.error('Yeni şifre en az 6 karakter olmalıdır');
        return;
      }

      setLoading(true);
      const token = localStorage.getItem('kuryecini_access_token');

      await axios.post(`${API}/api/auth/change-password`, {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      toast.success('Şifre başarıyla değiştirildi!');
      setShowPasswordModal(false);
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      });
    } catch (error) {
      console.error('Error changing password:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Şifre değiştirirken hata oluştu');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddPaymentMethod = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('kuryecini_access_token');

      await axios.post(`${API}/api/payment-methods`, newPaymentMethod, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      toast.success('Ödeme yöntemi başarıyla eklendi!');
      setShowPaymentModal(false);
      setNewPaymentMethod({
        provider: 'stripe',
        card_number: '',
        expiry_month: '',
        expiry_year: '',
        cvv: '',
        cardholder_name: ''
      });
      
      // Refresh payment methods
      loadTabData('payment_methods');
    } catch (error) {
      console.error('Error adding payment method:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Ödeme yöntemi eklerken hata oluştu');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddAddress = async () => {
    try {
      if (!newAddress.label || !newAddress.description || !newAddress.city) {
        toast.error('Lütfen tüm zorunlu alanları doldurun');
        return;
      }

      setLoading(true);

      await apiClient.post('/user/addresses', newAddress);

      toast.success('Adres başarıyla eklendi!');
      setShowAddressModal(false);
      setNewAddress({
        label: '',
        description: '',
        city: '',
        district: '',
        lat: 0,
        lng: 0
      });
      
      // Refresh addresses
      loadTabData('addresses');
    } catch (error) {
      console.error('Error adding address:', error);
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('Adres eklerken hata oluştu');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateNotificationSettings = async (newSettings) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');

      await axios.patch(`${API}/api/user/notification-settings`, newSettings, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      setNotificationSettings(newSettings);
      toast.success('Bildirim ayarları güncellendi!');
    } catch (error) {
      console.error('Error updating notification settings:', error);
      toast.error('Ayarlar güncellenirken hata oluştu');
    }
  };

  const handleUseCoupon = (coupon) => {
    toast.success(`${coupon.code} kuponu sepete eklendi!`);
    // Navigate to cart or discover page
  };

  const handleDeletePaymentMethod = (methodId) => {
    if (window.confirm('Bu ödeme yöntemini silmek istediğinize emin misiniz?')) {
      setPaymentMethods(paymentMethods.filter(pm => pm.id !== methodId));
      toast.success('Ödeme yöntemi silindi');
    }
  };

  // Duplicate functions removed - using the updated versions above

  // Duplicate function removed

  // Mock data
  const mockCoupons = [
    {
      id: 'coupon-1',
      code: 'WELCOME20',
      title: 'Hoş Geldin İndirimi',
      description: 'İlk siparişinizde %20 indirim',
      discount: 20,
      discountType: 'PERCENT',
      minAmount: 50,
      expiryDate: '31 Ocak 2024',
      status: 'active'
    },
    {
      id: 'coupon-2',
      code: 'PIZZA15',
      title: 'Pizza İndirimi',
      description: 'Pizza siparişlerinde ₺15 indirim',
      discount: 15,
      discountType: 'AMOUNT',
      minAmount: 75,
      expiryDate: '15 Şubat 2024',
      status: 'active'
    }
  ];

  const mockDiscounts = [
    {
      id: 'discount-1',
      title: 'VIP Müşteri İndirimi',
      description: 'Tüm siparişlerinizde geçerli',
      discount: 15,
      type: 'PERCENT',
      validUntil: '31 Aralık 2024'
    }
  ];

  const mockCampaigns = [
    {
      id: 'campaign-1',
      title: 'Pizza Festivali',
      description: 'Tüm pizzalarda %30 indirim',
      discount: 30,
      discountType: 'PERCENT',
      validUntil: '28 Şubat 2024',
      imageUrl: null
    },
    {
      id: 'campaign-2',
      title: 'Sağlıklı Yaşam',
      description: 'Salata siparişlerinde %25 indirim',
      discount: 25,
      discountType: 'PERCENT',
      validUntil: '31 Mart 2024',
      imageUrl: null
    }
  ];

  const mockPaymentMethods = [
    {
      id: 'pm-1',
      brand: 'VISA',
      lastFour: '4242',
      expiryMonth: '12',
      expiryYear: '26',
      provider: 'stripe',
      createdAt: '2024-01-01T00:00:00Z'
    }
  ];

  const renderTabContent = () => {
    if (loading) {
      return (
        <div className="text-center py-16">
          <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      );
    }

    switch (activeTab) {
      case 'addresses':
        return renderAddresses();
      case 'coupons':
        return renderCoupons();
      case 'discounts':
        return renderDiscounts();
      case 'campaigns':
        return renderCampaigns();
      case 'payment_methods':
        return renderPaymentMethods();
      case 'notifications':
        return renderNotifications();
      default:
        return renderProfileInfo();
    }
  };

  const renderProfileInfo = () => (
    <div className="space-y-6">
      {/* Profile Information Card */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">👤 Kişisel Bilgiler</h3>
            <Button
              onClick={() => setIsEditing(!isEditing)}
              variant={isEditing ? "outline" : "default"}
            >
              {isEditing ? '❌ İptal' : '✏️ Düzenle'}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Ad</Label>
              {isEditing ? (
                <Input
                  value={profileData.first_name}
                  onChange={(e) => setProfileData({...profileData, first_name: e.target.value})}
                />
              ) : (
                <p className="p-2 bg-gray-50 rounded">{profileData.first_name}</p>
              )}
            </div>
            
            <div>
              <Label>Soyad</Label>
              {isEditing ? (
                <Input
                  value={profileData.last_name}
                  onChange={(e) => setProfileData({...profileData, last_name: e.target.value})}
                />
              ) : (
                <p className="p-2 bg-gray-50 rounded">{profileData.last_name}</p>
              )}
            </div>
          </div>

          <div>
            <Label>E-posta</Label>
            <p className="p-2 bg-gray-50 rounded text-gray-500">
              {profileData.email} (Değiştirilemez)
            </p>
          </div>

          <div>
            <Label>Telefon</Label>
            {isEditing ? (
              <Input
                value={profileData.phone}
                onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                placeholder="0555 123 4567"
              />
            ) : (
              <p className="p-2 bg-gray-50 rounded">{profileData.phone || 'Belirtilmemiş'}</p>
            )}
          </div>

          {isEditing && (
            <div className="flex gap-3 pt-4">
              <Button
                onClick={() => setIsEditing(false)}
                variant="outline"
                className="flex-1"
              >
                İptal
              </Button>
              <Button
                onClick={handleSaveProfile}
                disabled={loading}
                className="flex-1"
              >
                {loading ? 'Kaydediliyor...' : '✅ Kaydet'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Account Actions */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">⚙️ Hesap Ayarları</h3>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button 
            variant="outline" 
            className="w-full justify-start"
            onClick={() => setShowPasswordModal(true)}
          >
            🔒 Şifre Değiştir
          </Button>
          <Button 
            variant="outline" 
            className="w-full justify-start"
            onClick={() => setActiveTab('notifications')}
          >
            🔔 Bildirim Ayarları
          </Button>
          <Button 
            variant="outline" 
            className="w-full justify-start"
            onClick={() => setActiveTab('addresses')}
          >
            📍 Adres Yönetimi
          </Button>
          
          <hr className="my-4" />
          
          <Button 
            onClick={onLogout}
            className="w-full bg-red-500 hover:bg-red-600 text-white"
          >
            🚪 Çıkış Yap
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  const renderCoupons = () => (
    <div className="space-y-4">
      {coupons.length === 0 ? (
        <div className="text-center py-16">
          <span className="text-6xl mb-4 block">🎟️</span>
          <h3 className="text-xl font-bold mb-2">Henüz kuponunuz yok</h3>
          <p className="text-gray-600">Kampanyaları takip ederek kupon kazanın</p>
        </div>
      ) : (
        coupons.map(coupon => (
          <Card key={coupon.id} className="border-l-4 border-l-orange-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-2xl">🎟️</span>
                    <span className="font-mono bg-gray-100 px-2 py-1 rounded text-sm font-bold">
                      {coupon.code}
                    </span>
                  </div>
                  <h4 className="font-semibold text-gray-800">{coupon.title}</h4>
                  <p className="text-sm text-gray-600">{coupon.description}</p>
                  <div className="text-xs text-gray-500 mt-2 space-y-1">
                    <div>Minimum: ₺{coupon.minAmount}</div>
                    <div>Son tarih: {coupon.expiryDate}</div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-2xl font-bold text-orange-600 mb-2">
                    {coupon.discountType === 'PERCENT' ? `%${coupon.discount}` : `₺${coupon.discount}`}
                  </div>
                  <Button
                    onClick={() => handleUseCoupon(coupon)}
                    size="sm"
                    className="bg-orange-500 hover:bg-orange-600"
                  >
                    Kullan
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );

  const renderDiscounts = () => (
    <div className="space-y-4">
      {discounts.length === 0 ? (
        <div className="text-center py-16">
          <span className="text-6xl mb-4 block">💸</span>
          <h3 className="text-xl font-bold mb-2">Henüz özel indiriminiz yok</h3>
          <p className="text-gray-600">VIP müşteri olarak özel indirimler kazanın</p>
        </div>
      ) : (
        discounts.map(discount => (
          <Card key={discount.id} className="border-l-4 border-l-green-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-2xl">💸</span>
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-semibold">
                      Özel İndirim
                    </span>
                  </div>
                  <h4 className="font-semibold text-gray-800">{discount.title}</h4>
                  <p className="text-sm text-gray-600">{discount.description}</p>
                  <p className="text-xs text-gray-500 mt-2">
                    Geçerli: {discount.validUntil}
                  </p>
                </div>
                
                <div className="text-2xl font-bold text-green-600">
                  {discount.type === 'PERCENT' ? `%${discount.discount}` : `₺${discount.discount}`}
                </div>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );

  const renderCampaigns = () => (
    <div className="space-y-4">
      {campaigns.map(campaign => (
        <Card key={campaign.id} className="overflow-hidden">
          <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-lg">{campaign.title}</h4>
                <p className="opacity-90">{campaign.description}</p>
              </div>
              <div className="text-3xl">🎉</div>
            </div>
          </div>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Son tarih: {campaign.validUntil}</p>
                <p className="text-lg font-bold text-purple-600">
                  %{campaign.discount} İndirim
                </p>
              </div>
              <Button className="bg-purple-500 hover:bg-purple-600">
                Kampanyayı Gör
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}

      {campaigns.length === 0 && (
        <div className="text-center py-16">
          <span className="text-6xl mb-4 block">🎉</span>
          <h3 className="text-xl font-bold mb-2">Aktif kampanya yok</h3>
          <p className="text-gray-600">Yeni kampanyalar için takipte kalın</p>
        </div>
      )}
    </div>
  );

  const renderAddresses = () => (
    <div className="space-y-4">
      {/* Add Address Button */}
      <Card className="border-dashed border-2">
        <CardContent className="p-6 text-center">
          <Button 
            onClick={() => {
              setEditingAddress(null);
              setNewAddress({
                title: 'Ev',
                full_address: '',
                district: '',
                city: '',
                building_no: '',
                apartment_no: '',
                floor: '',
                instructions: '',
                phone: '',
                lat: null,
                lng: null,
                is_default: false
              });
              setShowAddressModal(true);
            }}
            className="bg-orange-500 hover:bg-orange-600 text-white"
          >
            ➕ Yeni Adres Ekle
          </Button>
          <p className="text-sm text-gray-600 mt-2">
            Teslimat adresinizi ekleyin
          </p>
        </CardContent>
      </Card>

      {/* Existing Addresses */}
      {userAddresses.map(address => (
        <Card key={address.id}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  📍
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <p className="font-semibold">{address.title}</p>
                    {address.is_default && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        Varsayılan
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{address.full_address}</p>
                  <p className="text-xs text-gray-500">
                    {address.district && `${address.district}, `}{address.city}
                  </p>
                  {address.building_no && (
                    <p className="text-xs text-gray-400">
                      Bina: {address.building_no} 
                      {address.apartment_no && `, Daire: ${address.apartment_no}`}
                      {address.floor && `, Kat: ${address.floor}`}
                    </p>
                  )}
                  {address.phone && (
                    <p className="text-xs text-gray-400">Tel: {address.phone}</p>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleEditAddress(address)}
                  disabled={loading}
                >
                  ✏️
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-red-500"
                  onClick={() => handleDeleteAddress(address.id)}
                  disabled={loading}
                >
                  🗑️
                </Button>
                {!address.is_default && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-green-600 border-green-300"
                    onClick={() => handleSetDefaultAddress(address.id)}
                    disabled={loading}
                  >
                    📌 Varsayılan Yap
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      {userAddresses.length === 0 && (
        <div className="text-center py-16">
          <span className="text-6xl mb-4 block">📍</span>
          <h3 className="text-xl font-bold mb-2">Henüz adresiniz yok</h3>
          <p className="text-gray-600">İlk adresinizi ekleyin</p>
        </div>
      )}
    </div>
  );

  const renderNotifications = () => (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">🔔 Bildirim Ayarları</h2>
        <p className="text-gray-600">Hangi bildirimleri almak istediğinizi seçin</p>
      </div>

      {/* Push Notifications */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold">📱 Push Bildirimleri</h4>
              <p className="text-sm text-gray-600">Mobil cihazınıza anında bildirim gönderir</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.push_notifications}
                onChange={(e) => handleUpdateNotificationSettings({
                  ...notificationSettings,
                  push_notifications: e.target.checked
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Email Notifications */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold">📧 E-posta Bildirimleri</h4>
              <p className="text-sm text-gray-600">E-posta adresinize bildirim gönderir</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.email_notifications}
                onChange={(e) => handleUpdateNotificationSettings({
                  ...notificationSettings,
                  email_notifications: e.target.checked
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Order Updates */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold">📦 Sipariş Güncellemeleri</h4>
              <p className="text-sm text-gray-600">Sipariş durumu değişikliklerinde bildirim alın</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.order_updates}
                onChange={(e) => handleUpdateNotificationSettings({
                  ...notificationSettings,
                  order_updates: e.target.checked
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Promotions */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold">🎉 Promosyon Bildirimleri</h4>
              <p className="text-sm text-gray-600">Kampanya ve indirimler hakkında bilgi alın</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.promotions}
                onChange={(e) => handleUpdateNotificationSettings({
                  ...notificationSettings,
                  promotions: e.target.checked
                })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-orange-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-orange-600"></div>
            </label>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderPaymentMethods = () => (
    <div className="space-y-4">
      {/* Add Payment Method Button */}
      <Card className="border-dashed border-2">
        <CardContent className="p-6 text-center">
          <Button 
            onClick={() => setShowPaymentModal(true)}
            className="bg-orange-500 hover:bg-orange-600 text-white"
          >
            ➕ Yeni Ödeme Yöntemi Ekle
          </Button>
          <p className="text-sm text-gray-600 mt-2">
            Kredi kartı veya banka kartı ekleyin
          </p>
        </CardContent>
      </Card>

      {/* Existing Payment Methods */}
      {paymentMethods.map(method => (
        <Card key={method.id}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  💳
                </div>
                <div>
                  <p className="font-semibold">**** **** **** {method.lastFour}</p>
                  <p className="text-sm text-gray-600">
                    {method.brand.toUpperCase()} • {method.expiryMonth}/{method.expiryYear}
                  </p>
                  <p className="text-xs text-gray-500">
                    Eklenme: {new Date(method.createdAt).toLocaleDateString('tr-TR')}
                  </p>
                </div>
              </div>
              
              <Button
                onClick={() => handleDeletePaymentMethod(method.id)}
                variant="outline"
                size="sm"
                className="text-red-500 hover:text-red-700"
              >
                🗑️
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}

      {paymentMethods.length === 0 && (
        <div className="text-center py-16">
          <span className="text-6xl mb-4 block">💳</span>
          <h3 className="text-xl font-bold mb-2">Kayıtlı ödeme yönteminiz yok</h3>
          <p className="text-gray-600">Hızlı ödeme için kart ekleyin</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-40">
        <div className="p-4">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-xl">👤</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">
                {profileData.first_name} {profileData.last_name}
              </h1>
              <p className="text-sm text-gray-600">{profileData.email}</p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-4 pb-4">
          <div className="flex space-x-2 overflow-x-auto">
            {tabs.map(tab => (
              <Button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                variant={activeTab === tab.id ? "default" : "outline"}
                size="sm"
                className="min-w-fit"
              >
                {tab.icon} {tab.name}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {renderTabContent()}
      </div>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">🔒 Şifre Değiştir</h3>
              
              <div className="space-y-4">
                <div>
                  <Label>Mevcut Şifre</Label>
                  <Input
                    type="password"
                    value={passwordData.currentPassword}
                    onChange={(e) => setPasswordData({...passwordData, currentPassword: e.target.value})}
                    placeholder="Mevcut şifrenizi girin"
                  />
                </div>
                
                <div>
                  <Label>Yeni Şifre</Label>
                  <Input
                    type="password"
                    value={passwordData.newPassword}
                    onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})}
                    placeholder="Yeni şifrenizi girin"
                  />
                </div>
                
                <div>
                  <Label>Yeni Şifre (Tekrar)</Label>
                  <Input
                    type="password"
                    value={passwordData.confirmPassword}
                    onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                    placeholder="Yeni şifrenizi tekrar girin"
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <Button
                  onClick={() => setShowPasswordModal(false)}
                  variant="outline"
                  className="flex-1"
                >
                  İptal
                </Button>
                <Button
                  onClick={handlePasswordChange}
                  disabled={loading}
                  className="flex-1 bg-orange-500 hover:bg-orange-600 text-white"
                >
                  {loading ? 'Değiştiriliyor...' : 'Şifreyi Değiştir'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Address Modal */}
      {showAddressModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                📍 {editingAddress ? 'Adres Düzenle' : 'Yeni Adres Ekle'}
              </h3>
              
              <div className="space-y-4 max-h-96 overflow-y-auto">
                <div>
                  <Label>Adres Etiketi</Label>
                  <select
                    value={newAddress.title}
                    onChange={(e) => setNewAddress({...newAddress, title: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg p-2"
                  >
                    <option value="Ev">🏠 Ev</option>
                    <option value="İş">🏢 İş</option>
                    <option value="Diğer">📍 Diğer</option>
                  </select>
                </div>
                
                <div>
                  <Label>Tam Adres *</Label>
                  <textarea
                    value={newAddress.full_address}
                    onChange={(e) => setNewAddress({...newAddress, full_address: e.target.value})}
                    placeholder="Mahalle, cadde, sokak adı..."
                    className="w-full border border-gray-300 rounded-lg p-3 text-sm h-20"
                    required
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Şehir *</Label>
                    <select
                      value={newAddress.city}
                      onChange={(e) => setNewAddress({...newAddress, city: e.target.value})}
                      className="w-full border border-gray-300 rounded-lg p-2"
                      required
                    >
                      <option value="">Şehir Seçin</option>
                      <option value="İstanbul">İstanbul</option>
                      <option value="Ankara">Ankara</option>
                      <option value="İzmir">İzmir</option>
                      <option value="Aksaray">Aksaray</option>
                      <option value="Bursa">Bursa</option>
                      <option value="Antalya">Antalya</option>
                    </select>
                  </div>
                  <div>
                    <Label>İlçe</Label>
                    <Input
                      type="text"
                      value={newAddress.district}
                      onChange={(e) => setNewAddress({...newAddress, district: e.target.value})}
                      placeholder="İlçe adı"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <Label>Bina No</Label>
                    <Input
                      type="text"
                      value={newAddress.building_no}
                      onChange={(e) => setNewAddress({...newAddress, building_no: e.target.value})}
                      placeholder="123"
                    />
                  </div>
                  <div>
                    <Label>Daire No</Label>
                    <Input
                      type="text"
                      value={newAddress.apartment_no}
                      onChange={(e) => setNewAddress({...newAddress, apartment_no: e.target.value})}
                      placeholder="5"
                    />
                  </div>
                  <div>
                    <Label>Kat</Label>
                    <Input
                      type="text"
                      value={newAddress.floor}
                      onChange={(e) => setNewAddress({...newAddress, floor: e.target.value})}
                      placeholder="2"
                    />
                  </div>
                </div>
                
                <div>
                  <Label>Telefon</Label>
                  <Input
                    type="tel"
                    value={newAddress.phone}
                    onChange={(e) => setNewAddress({...newAddress, phone: e.target.value})}
                    placeholder="0532 123 45 67"
                  />
                </div>
                
                <div>
                  <Label>Teslimat Talimatları</Label>
                  <textarea
                    value={newAddress.instructions}
                    onChange={(e) => setNewAddress({...newAddress, instructions: e.target.value})}
                    placeholder="Zil çalın, kapıya bırakın vb..."
                    className="w-full border border-gray-300 rounded-lg p-3 text-sm h-16"
                  />
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="default_address"
                    checked={newAddress.is_default}
                    onChange={(e) => setNewAddress({...newAddress, is_default: e.target.checked})}
                    className="rounded"
                  />
                  <Label htmlFor="default_address" className="text-sm">Varsayılan adres olarak ayarla</Label>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-blue-700 text-sm">
                    📍 Konum bilgisi otomatik olarak belirlenecektir.
                  </p>
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <Button
                  onClick={() => {
                    setShowAddressModal(false);
                    setEditingAddress(null);
                    setNewAddress({
                      title: 'Ev',
                      full_address: '',
                      district: '',
                      city: '',
                      building_no: '',
                      apartment_no: '',
                      floor: '',
                      instructions: '',
                      phone: '',
                      lat: null,
                      lng: null,
                      is_default: false
                    });
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  İptal
                </Button>
                <Button
                  onClick={handleSaveAddress}
                  disabled={loading || !newAddress.full_address || !newAddress.city}
                  className="flex-1 bg-orange-500 hover:bg-orange-600 text-white"
                >
                  {loading ? (editingAddress ? 'Güncelleniyor...' : 'Ekleniyor...') : 
                           (editingAddress ? 'Adresi Güncelle' : 'Adresi Ekle')}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Method Modal */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">💳 Ödeme Yöntemi Ekle</h3>
              
              <div className="space-y-4">
                <div>
                  <Label>Sağlayıcı</Label>
                  <select
                    value={newPaymentMethod.provider}
                    onChange={(e) => setNewPaymentMethod({...newPaymentMethod, provider: e.target.value})}
                    className="w-full border border-gray-300 rounded-lg p-2"
                  >
                    <option value="stripe">Stripe</option>
                    <option value="iyzico">İyzico</option>
                  </select>
                </div>
                
                <div>
                  <Label>Kart Numarası</Label>
                  <Input
                    type="text"
                    value={newPaymentMethod.card_number}
                    onChange={(e) => setNewPaymentMethod({...newPaymentMethod, card_number: e.target.value})}
                    placeholder="1234 5678 9012 3456"
                    maxLength={19}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Ay</Label>
                    <Input
                      type="text"
                      value={newPaymentMethod.expiry_month}
                      onChange={(e) => setNewPaymentMethod({...newPaymentMethod, expiry_month: e.target.value})}
                      placeholder="MM"
                      maxLength={2}
                    />
                  </div>
                  <div>
                    <Label>Yıl</Label>
                    <Input
                      type="text"
                      value={newPaymentMethod.expiry_year}
                      onChange={(e) => setNewPaymentMethod({...newPaymentMethod, expiry_year: e.target.value})}
                      placeholder="YY"
                      maxLength={2}
                    />
                  </div>
                </div>
                
                <div>
                  <Label>CVV</Label>
                  <Input
                    type="text"
                    value={newPaymentMethod.cvv}
                    onChange={(e) => setNewPaymentMethod({...newPaymentMethod, cvv: e.target.value})}
                    placeholder="123"
                    maxLength={4}
                  />
                </div>
                
                <div>
                  <Label>Kart Sahibi Adı</Label>
                  <Input
                    type="text"
                    value={newPaymentMethod.cardholder_name}
                    onChange={(e) => setNewPaymentMethod({...newPaymentMethod, cardholder_name: e.target.value})}
                    placeholder="Ad Soyad"
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <Button
                  onClick={() => setShowPaymentModal(false)}
                  variant="outline"
                  className="flex-1"
                >
                  İptal
                </Button>
                <Button
                  onClick={handleAddPaymentMethod}
                  disabled={loading}
                  className="flex-1 bg-orange-500 hover:bg-orange-600 text-white"
                >
                  {loading ? 'Ekleniyor...' : 'Kartı Ekle'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;