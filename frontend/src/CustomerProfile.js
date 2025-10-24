import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Label } from "./components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Customer Profile Management Component
export const CustomerProfile = ({ user, onClose }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [loyaltyPoints, setLoyaltyPoints] = useState({ total_points: 0, lifetime_points: 0, tier_level: 'Bronze' });
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [profileForm, setProfileForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    birth_date: '',
    gender: '',
    preferred_language: 'tr',
    theme_preference: 'light',
    notification_preferences: {
      email_notifications: true,
      sms_notifications: true,
      push_notifications: true,
      marketing_emails: false
    }
  });
  const [addressForm, setAddressForm] = useState({
    title: '',
    address_line: '',
    district: '',
    city: '',
    postal_code: '',
    is_default: false
  });

  const turkishCities = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", 
    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", 
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", 
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", 
    "Giresun", "Gümüşhane", "Hakkâri", "Hatay", "Isparta", "Mersin", "İstanbul", 
    "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", 
    "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", 
    "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", 
    "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", 
    "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", 
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", 
    "Karabük", "Kilis", "Osmaniye", "Düzce"
  ];

  // Fetch user profile
  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile/me`);
      const profileData = response.data;
      setProfile(profileData);
      
      // Update form with profile data
      setProfileForm({
        first_name: profileData.first_name || '',
        last_name: profileData.last_name || '',
        email: profileData.email || '',
        birth_date: profileData.birth_date ? profileData.birth_date.split('T')[0] : '',
        gender: profileData.gender || '',
        preferred_language: profileData.preferred_language || 'tr',
        theme_preference: profileData.theme_preference || 'light',
        notification_preferences: profileData.notification_preferences || {
          email_notifications: true,
          sms_notifications: true,
          push_notifications: true,
          marketing_emails: false
        }
      });
    } catch (error) {
      console.error('Profile fetch error:', error);
      toast.error('Profil bilgileri yüklenemedi');
    }
  };

  // Fetch user addresses
  const fetchAddresses = async () => {
    try {
      const response = await axios.get(`${API}/addresses`);
      setAddresses(response.data);
    } catch (error) {
      console.error('Addresses fetch error:', error);
      toast.error('Adresler yüklenemedi');
    }
  };

  // Fetch order history
  const fetchOrderHistory = async () => {
    try {
      const response = await axios.get(`${API}/orders/history?page=1&limit=10`);
      setOrderHistory(response.data.orders || []);
    } catch (error) {
      console.error('Order history fetch error:', error);
      toast.error('Sipariş geçmişi yüklenemedi');
    }
  };

  // Fetch loyalty points
  const fetchLoyaltyPoints = async () => {
    try {
      const response = await axios.get(`${API}/loyalty/points`);
      setLoyaltyPoints(response.data);
    } catch (error) {
      console.error('Loyalty points fetch error:', error);
    }
  };

  useEffect(() => {
    if (user && user.role === 'customer') {
      fetchProfile();
      fetchAddresses();
      fetchOrderHistory();
      fetchLoyaltyPoints();
    }
  }, [user]);

  // Update profile
  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.put(`${API}/profile/me`, profileForm);
      toast.success('Profil başarıyla güncellendi!');
      fetchProfile();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Profil güncellenemedi');
    }
    setLoading(false);
  };

  // Handle address operations
  const handleAddressSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (editingAddress) {
        await axios.put(`${API}/addresses/${editingAddress.id}`, addressForm);
        toast.success('Adres güncellendi!');
      } else {
        await axios.post(`${API}/addresses`, addressForm);
        toast.success('Adres eklendi!');
      }
      
      setShowAddressForm(false);
      setEditingAddress(null);
      setAddressForm({
        title: '',
        address_line: '',
        district: '',
        city: '',
        postal_code: '',
        is_default: false
      });
      fetchAddresses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Adres işlemi başarısız');
    }
    setLoading(false);
  };

  const handleDeleteAddress = async (addressId) => {
    if (!window.confirm('Bu adresi silmek istediğinizden emin misiniz?')) return;

    try {
      await axios.delete(`${API}/addresses/${addressId}`);
      toast.success('Adres silindi!');
      fetchAddresses();
    } catch (error) {
      toast.error('Adres silinemedi');
    }
  };

  const handleSetDefaultAddress = async (addressId) => {
    try {
      await axios.post(`${API}/addresses/${addressId}/set-default`);
      toast.success('Varsayılan adres güncellendi!');
      fetchAddresses();
    } catch (error) {
      toast.error('Varsayılan adres ayarlanamadı');
    }
  };

  const handleReorder = async (orderId) => {
    try {
      const response = await axios.post(`${API}/orders/${orderId}/reorder`);
      const reorderData = response.data;
      
      if (reorderData.available_items.length > 0) {
        toast.success(`${reorderData.available_items.length} ürün sepete eklendi!`);
        // Here you would normally add items to cart
      } else {
        toast.error('Bu siparişten hiçbir ürün tekrar sipariş edilemez');
      }
    } catch (error) {
      toast.error('Tekrar sipariş verilemedi');
    }
  };

  if (!user || user.role !== 'customer') {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Bu sayfaya sadece müşteriler erişebilir.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white/70 backdrop-blur-lg border-b border-gray-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="text-2xl">👤</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Profilim</h1>
                <p className="text-sm text-gray-600">Hesap ayarlarınızı yönetin</p>
              </div>
            </div>
            <Button onClick={onClose} variant="outline">
              Geri Dön
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="profile">👤 Profil</TabsTrigger>
            <TabsTrigger value="addresses">📍 Adreslerim</TabsTrigger>
            <TabsTrigger value="orders">📦 Siparişlerim</TabsTrigger>
            <TabsTrigger value="loyalty">⭐ Puanlarım</TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Kişisel Bilgiler</CardTitle>
                <CardDescription>
                  Profil bilgilerinizi güncelleyebilirsiniz
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProfileUpdate} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="first_name">Ad</Label>
                      <Input
                        id="first_name"
                        value={profileForm.first_name}
                        onChange={(e) => setProfileForm({...profileForm, first_name: e.target.value})}
                        placeholder="Adınız"
                      />
                    </div>
                    <div>
                      <Label htmlFor="last_name">Soyad</Label>
                      <Input
                        id="last_name"
                        value={profileForm.last_name}
                        onChange={(e) => setProfileForm({...profileForm, last_name: e.target.value})}
                        placeholder="Soyadınız"
                      />
                    </div>
                    <div>
                      <Label htmlFor="email">E-posta</Label>
                      <Input
                        id="email"
                        type="email"
                        value={profileForm.email}
                        onChange={(e) => setProfileForm({...profileForm, email: e.target.value})}
                        placeholder="ornek@email.com"
                      />
                    </div>
                    <div>
                      <Label htmlFor="birth_date">Doğum Tarihi</Label>
                      <Input
                        id="birth_date"
                        type="date"
                        value={profileForm.birth_date}
                        onChange={(e) => setProfileForm({...profileForm, birth_date: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="gender">Cinsiyet</Label>
                      <Select value={profileForm.gender} onValueChange={(value) => setProfileForm({...profileForm, gender: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Cinsiyet seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="male">Erkek</SelectItem>
                          <SelectItem value="female">Kadın</SelectItem>
                          <SelectItem value="other">Diğer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="theme">Tema Tercihi</Label>
                      <Select value={profileForm.theme_preference} onValueChange={(value) => setProfileForm({...profileForm, theme_preference: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Tema seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="light">Açık Tema</SelectItem>
                          <SelectItem value="dark">Koyu Tema</SelectItem>
                          <SelectItem value="auto">Otomatik</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Notification Preferences */}
                  <div className="space-y-3">
                    <Label>Bildirim Tercihleri</Label>
                    <div className="space-y-2">
                      {[
                        { key: 'email_notifications', label: 'E-posta bildirimleri' },
                        { key: 'sms_notifications', label: 'SMS bildirimleri' },
                        { key: 'push_notifications', label: 'Anlık bildirimler' },
                        { key: 'marketing_emails', label: 'Pazarlama e-postaları' }
                      ].map((pref) => (
                        <div key={pref.key} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={pref.key}
                            checked={profileForm.notification_preferences[pref.key]}
                            onChange={(e) => setProfileForm({
                              ...profileForm,
                              notification_preferences: {
                                ...profileForm.notification_preferences,
                                [pref.key]: e.target.checked
                              }
                            })}
                            className="rounded border-gray-300"
                          />
                          <Label htmlFor={pref.key} className="text-sm">{pref.label}</Label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? 'Güncelleniyor...' : 'Profili Güncelle'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Addresses Tab */}
          <TabsContent value="addresses" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Adreslerim</h2>
              <Button onClick={() => setShowAddressForm(true)}>
                ➕ Yeni Adres Ekle
              </Button>
            </div>

            {/* Address Form */}
            {showAddressForm && (
              <Card>
                <CardHeader>
                  <CardTitle>{editingAddress ? 'Adresi Düzenle' : 'Yeni Adres Ekle'}</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleAddressSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="title">Adres Başlığı</Label>
                        <Input
                          id="title"
                          value={addressForm.title}
                          onChange={(e) => setAddressForm({...addressForm, title: e.target.value})}
                          placeholder="Ev, İş, Diğer..."
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="city">Şehir</Label>
                        <Select value={addressForm.city} onValueChange={(value) => setAddressForm({...addressForm, city: value})} required>
                          <SelectTrigger>
                            <SelectValue placeholder="Şehir seçin" />
                          </SelectTrigger>
                          <SelectContent>
                            {turkishCities.map((city) => (
                              <SelectItem key={city} value={city}>{city}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="md:col-span-2">
                        <Label htmlFor="address_line">Adres</Label>
                        <Textarea
                          id="address_line"
                          value={addressForm.address_line}
                          onChange={(e) => setAddressForm({...addressForm, address_line: e.target.value})}
                          placeholder="Mahalle, sokak, bina no, daire no..."
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="district">İlçe</Label>
                        <Input
                          id="district"
                          value={addressForm.district}
                          onChange={(e) => setAddressForm({...addressForm, district: e.target.value})}
                          placeholder="İlçe"
                        />
                      </div>
                      <div>
                        <Label htmlFor="postal_code">Posta Kodu</Label>
                        <Input
                          id="postal_code"
                          value={addressForm.postal_code}
                          onChange={(e) => setAddressForm({...addressForm, postal_code: e.target.value})}
                          placeholder="34000"
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="is_default"
                        checked={addressForm.is_default}
                        onChange={(e) => setAddressForm({...addressForm, is_default: e.target.checked})}
                        className="rounded border-gray-300"
                      />
                      <Label htmlFor="is_default">Varsayılan adres olarak ayarla</Label>
                    </div>

                    <div className="flex space-x-2">
                      <Button type="submit" disabled={loading}>
                        {loading ? 'Kaydediliyor...' : (editingAddress ? 'Güncelle' : 'Ekle')}
                      </Button>
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={() => {
                          setShowAddressForm(false);
                          setEditingAddress(null);
                          setAddressForm({
                            title: '', address_line: '', district: '', city: '', postal_code: '', is_default: false
                          });
                        }}
                      >
                        İptal
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Address List */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {addresses.map((address) => (
                <Card key={address.id} className={address.is_default ? 'border-green-500 bg-green-50' : ''}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold flex items-center">
                        {address.title}
                        {address.is_default && (
                          <Badge variant="secondary" className="ml-2 bg-green-100 text-green-800">
                            Varsayılan
                          </Badge>
                        )}
                      </h3>
                      <div className="flex space-x-1">
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={() => {
                            setEditingAddress(address);
                            setAddressForm({
                              title: address.title,
                              address_line: address.address_line,
                              district: address.district || '',
                              city: address.city,
                              postal_code: address.postal_code || '',
                              is_default: address.is_default
                            });
                            setShowAddressForm(true);
                          }}
                        >
                          ✏️
                        </Button>
                        {!address.is_default && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleSetDefaultAddress(address.id)}
                          >
                            ⭐
                          </Button>
                        )}
                        <Button 
                          size="sm" 
                          variant="ghost"
                          onClick={() => handleDeleteAddress(address.id)}
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">
                      {address.address_line}
                    </p>
                    <p className="text-sm text-gray-500">
                      {address.district && `${address.district}, `}{address.city}
                      {address.postal_code && ` - ${address.postal_code}`}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {addresses.length === 0 && (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-4xl mb-4">📍</div>
                  <h3 className="text-lg font-semibold mb-2">Henüz adres eklenmemiş</h3>
                  <p className="text-gray-600 mb-4">Hızlı teslimat için adreslerinizi ekleyin</p>
                  <Button onClick={() => setShowAddressForm(true)}>
                    İlk Adresimi Ekle
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-6">
            <h2 className="text-2xl font-bold">Sipariş Geçmişim</h2>
            
            <div className="space-y-4">
              {orderHistory.map((order) => (
                <Card key={order.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="font-semibold text-lg">{order.business_name}</h3>
                        <p className="text-sm text-gray-600">
                          Sipariş #{order.id.slice(-8)} • {new Date(order.created_at).toLocaleDateString('tr-TR')}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-green-600">₺{order.total_amount}</div>
                        <Badge variant={
                          order.status === 'delivered' ? 'default' :
                          order.status === 'cancelled' ? 'destructive' :
                          'secondary'
                        }>
                          {order.status === 'delivered' ? 'Teslim Edildi' :
                           order.status === 'cancelled' ? 'İptal Edildi' :
                           order.status === 'pending' ? 'Beklemede' :
                           order.status === 'preparing' ? 'Hazırlanıyor' : 'Yolda'}
                        </Badge>
                      </div>
                    </div>

                    {/* Order Items */}
                    <div className="mb-4">
                      <h4 className="font-medium mb-2">Siparişiniz:</h4>
                      <div className="space-y-1">
                        {order.items.map((item, index) => (
                          <div key={index} className="flex justify-between text-sm">
                            <span>{item.quantity}x {item.product_name}</span>
                            <span>₺{item.total}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex space-x-2">
                      {order.can_reorder && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleReorder(order.id)}
                        >
                          🔄 Tekrar Sipariş Ver
                        </Button>
                      )}
                      {order.can_rate && (
                        <Button size="sm" variant="outline">
                          ⭐ Değerlendir
                        </Button>
                      )}
                      {order.rating_given && (
                        <Badge variant="secondary">✅ Değerlendirildi</Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {orderHistory.length === 0 && (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-4xl mb-4">📦</div>
                  <h3 className="text-lg font-semibold mb-2">Henüz sipariş yok</h3>
                  <p className="text-gray-600">İlk siparişinizi vererek başlayın!</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Loyalty Tab */}
          <TabsContent value="loyalty" className="space-y-6">
            <Card className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold mb-2">🏆 Sadakat Puanlarınız</h3>
                    <div className="flex items-center space-x-6">
                      <div>
                        <div className="text-3xl font-bold">{loyaltyPoints.total_points}</div>
                        <div className="text-sm opacity-90">Aktif Puan</div>
                      </div>
                      <div>
                        <div className="text-xl font-semibold">{loyaltyPoints.tier_level}</div>
                        <div className="text-sm opacity-90">Seviye</div>
                      </div>
                      <div>
                        <div className="text-xl font-semibold">{loyaltyPoints.lifetime_points}</div>
                        <div className="text-sm opacity-90">Toplam Kazanılan</div>
                      </div>
                    </div>
                  </div>
                  <div className="text-6xl opacity-20">⭐</div>
                </div>
                <div className="mt-4 text-sm opacity-90">
                  💡 Her 10₺'lik siparişe 1 puan kazanın! 100 puan = 10₺ indirim
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Puan Durumu</CardTitle>
                <CardDescription>
                  Sadakat puanlarınızı nasıl kullanabileceğinizi öğrenin
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                        💰
                      </div>
                      <div>
                        <div className="font-medium">Kullanılabilir Puan</div>
                        <div className="text-sm text-gray-600">Sipariş sırasında kullanabilirsiniz</div>
                      </div>
                    </div>
                    <div className="text-xl font-bold text-green-600">
                      {loyaltyPoints.total_points}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl mb-2">🥉</div>
                      <div className="font-medium">Bronze</div>
                      <div className="text-sm text-gray-600">0-999 puan</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl mb-2">🥈</div>
                      <div className="font-medium">Silver</div>
                      <div className="text-sm text-gray-600">1000-2999 puan</div>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <div className="text-2xl mb-2">🥇</div>
                      <div className="font-medium">Gold</div>
                      <div className="text-sm text-gray-600">3000+ puan</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default CustomerProfile;