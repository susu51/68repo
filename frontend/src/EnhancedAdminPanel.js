import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

export const EnhancedAdminPanel = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [users, setUsers] = useState([]);
  const [ads, setAds] = useState([]);
  const [featuredRequests, setFeaturedRequests] = useState([]);
  const [featuredBusinesses, setFeaturedBusinesses] = useState([]);
  const [stats, setStats] = useState({});
  
  // Forms
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [showAdModal, setShowAdModal] = useState(false);
  const [selectedCouriers, setSelectedCouriers] = useState([]);
  const [messageForm, setMessageForm] = useState({
    title: '',
    message: '',
    type: 'broadcast' // 'broadcast' or 'selective'
  });
  const [adForm, setAdForm] = useState({
    title: '',
    description: '',
    imgUrl: '',
    targetUrl: '',
    ctaText: 'Daha Fazla',
    type: 'general',
    targeting: {
      city: '',
      category: ''
    },
    schedule: {
      startAt: '',
      endAt: ''
    },
    active: true,
    order: 0
  });

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      // Get users
      const usersResponse = await axios.get(`${API}/admin/users`);
      setUsers(usersResponse.data || []);
      
      // Calculate stats
      const customerCount = usersResponse.data?.filter(u => u.role === 'customer').length || 0;
      const courierCount = usersResponse.data?.filter(u => u.role === 'courier').length || 0;
      const businessCount = usersResponse.data?.filter(u => u.role === 'business').length || 0;
      
      setStats({
        customers: customerCount,
        couriers: courierCount,
        businesses: businessCount,
        total_users: usersResponse.data?.length || 0
      });
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  // Fetch ads
  const fetchAds = async () => {
    try {
      const response = await axios.get(`${API}/admin/ads`);
      setAds(response.data || []);
    } catch (error) {
      console.error('Failed to fetch ads:', error);
    }
  };

  // Fetch featured requests
  const fetchFeaturedRequests = async () => {
    try {
      const response = await axios.get(`${API}/admin/featured-requests`);
      setFeaturedRequests(response.data.requests || []);
    } catch (error) {
      console.error('Failed to fetch featured requests:', error);
    }
  };

  // Fetch featured businesses
  const fetchFeaturedBusinesses = async () => {
    try {
      const response = await axios.get(`${API}/admin/featured-businesses`);
      setFeaturedBusinesses(response.data.featured_businesses || []);
    } catch (error) {
      console.error('Failed to fetch featured businesses:', error);
    }
  };

  // Generate dummy data
  const generateDummyData = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/admin/generate-dummy-data`);
      toast.success(`Dummy data oluşturuldu: ${JSON.stringify(response.data.created)}`);
      fetchDashboardData();
    } catch (error) {
      toast.error('Dummy data oluşturulamadı');
    }
    setLoading(false);
  };

  // Send message to couriers
  const sendCourierMessage = async () => {
    try {
      setLoading(true);
      
      const messageData = {
        ...messageForm,
        courier_ids: messageForm.type === 'selective' ? selectedCouriers : []
      };
      
      const response = await axios.post(`${API}/admin/courier/message`, messageData);
      toast.success(response.data.message);
      
      setShowMessageModal(false);
      setMessageForm({ title: '', message: '', type: 'broadcast' });
      setSelectedCouriers([]);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Mesaj gönderilemedi');
    }
    setLoading(false);
  };

  // Create advertisement
  const createAd = async () => {
    try {
      setLoading(true);
      
      // Set default dates if not provided
      const now = new Date();
      const adData = {
        ...adForm,
        schedule: {
          startAt: adForm.schedule.startAt || now.toISOString(),
          endAt: adForm.schedule.endAt || new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString()
        }
      };
      
      await axios.post(`${API}/admin/ads`, adData);
      toast.success('Reklam oluşturuldu!');
      
      setShowAdModal(false);
      setAdForm({
        title: '',
        description: '',
        imgUrl: '',
        targetUrl: '',
        ctaText: 'Daha Fazla',
        type: 'general',
        targeting: { city: '', category: '' },
        schedule: { startAt: '', endAt: '' },
        active: true,
        order: 0
      });
      fetchAds();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Reklam oluşturulamadı');
    }
    setLoading(false);
  };

  // Approve featured request
  const approveFeaturedRequest = async (requestId) => {
    try {
      await axios.post(`${API}/admin/featured-requests/${requestId}/approve`);
      toast.success('Öne çıkarma talebi onaylandı!');
      fetchFeaturedRequests();
      fetchFeaturedBusinesses();
    } catch (error) {
      toast.error('Talep onaylanamadı');
    }
  };

  // Reject featured request
  const rejectFeaturedRequest = async (requestId) => {
    const reason = prompt('Red sebebi (opsiyonel):');
    try {
      await axios.post(`${API}/admin/featured-requests/${requestId}/reject`, {
        reason: reason || 'Sebep belirtilmedi'
      });
      toast.success('Öne çıkarma talebi reddedildi');
      fetchFeaturedRequests();
    } catch (error) {
      toast.error('Talep reddedilemedi');
    }
  };

  // Delete ad
  const deleteAd = async (adId) => {
    if (!window.confirm('Bu reklamı silmek istediğinizden emin misiniz?')) return;
    
    try {
      await axios.delete(`${API}/admin/ads/${adId}`);
      toast.success('Reklam silindi!');
      fetchAds();
    } catch (error) {
      toast.error('Reklam silinemedi');
    }
  };

  // Delete user
  const deleteUser = async (userId) => {
    if (!window.confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) return;
    
    try {
      await axios.delete(`${API}/admin/users/${userId}`);
      toast.success('Kullanıcı silindi!');
      fetchDashboardData();
    } catch (error) {
      toast.error('Kullanıcı silinemedi');
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchAds();
    fetchFeaturedRequests();
    fetchFeaturedBusinesses();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white/70 backdrop-blur-lg border-b border-gray-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="text-2xl">👨‍💼</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Admin Paneli</h1>
                <p className="text-sm text-gray-600">
                  Kuryecini Yönetim Sistemi
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button onClick={generateDummyData} variant="outline" disabled={loading}>
                🎲 Test Verisi Oluştur
              </Button>
              <Button onClick={onLogout} variant="outline">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Dashboard Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">👥</div>
              <div className="text-2xl font-bold text-blue-600">
                {stats.customers || 0}
              </div>
              <div className="text-sm text-gray-600">Müşteri</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">🚚</div>
              <div className="text-2xl font-bold text-green-600">
                {stats.couriers || 0}
              </div>
              <div className="text-sm text-gray-600">Kurye</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">🏪</div>
              <div className="text-2xl font-bold text-purple-600">
                {stats.businesses || 0}
              </div>
              <div className="text-sm text-gray-600">İşletme</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-3xl mb-2">📊</div>
              <div className="text-2xl font-bold text-orange-600">
                {stats.total_users || 0}
              </div>
              <div className="text-sm text-gray-600">Toplam Kullanıcı</div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs Navigation */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="dashboard">📊 Dashboard</TabsTrigger>
            <TabsTrigger value="users">👥 Kullanıcılar</TabsTrigger>
            <TabsTrigger value="messaging">💬 Mesajlaşma</TabsTrigger>
            <TabsTrigger value="ads">📢 Reklamlar</TabsTrigger>
            <TabsTrigger value="featured">⭐ Öne Çıkar</TabsTrigger>
            <TabsTrigger value="analytics">📈 Analytics</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Sistem Durumu</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>API Durumu:</span>
                      <Badge className="bg-green-100 text-green-800">🟢 Aktif</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Veritabanı:</span>
                      <Badge className="bg-green-100 text-green-800">🟢 Bağlı</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Mesajlaşma:</span>
                      <Badge className="bg-green-100 text-green-800">🟢 Aktif</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Reklam Sistemi:</span>
                      <Badge className="bg-green-100 text-green-800">🟢 Çalışıyor</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Son Aktiviteler</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div className="flex items-center space-x-2">
                      <span className="text-blue-500">👥</span>
                      <span>Yeni müşteri kaydı</span>
                      <Badge variant="outline">5 dk önce</Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-green-500">🚚</span>
                      <span>Kurye çevrimiçi oldu</span>
                      <Badge variant="outline">12 dk önce</Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-purple-500">🏪</span>
                      <span>Yeni işletme başvurusu</span>
                      <Badge variant="outline">1 sa önce</Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-orange-500">⭐</span>
                      <span>Öne çıkarma talebi</span>
                      <Badge variant="outline">2 sa önce</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Kullanıcı Yönetimi</h2>
              <Button onClick={fetchDashboardData} variant="outline">
                🔄 Yenile
              </Button>
            </div>

            <div className="space-y-4">
              {users.map((user) => (
                <Card key={user.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <div className="text-2xl">
                            {user.role === 'customer' ? '👤' : 
                             user.role === 'courier' ? '🚚' : 
                             user.role === 'business' ? '🏪' : '👨‍💼'}
                          </div>
                          <div>
                            <h4 className="font-semibold">
                              {user.first_name && user.last_name 
                                ? `${user.first_name} ${user.last_name}`
                                : user.business_name || user.email
                              }
                            </h4>
                            <p className="text-sm text-gray-600">{user.email}</p>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge variant={
                                user.role === 'admin' ? 'default' :
                                user.role === 'business' ? 'secondary' :
                                user.role === 'courier' ? 'outline' : 'secondary'
                              }>
                                {user.role}
                              </Badge>
                              <Badge variant={user.is_active ? 'default' : 'destructive'}>
                                {user.is_active ? 'Aktif' : 'Pasif'}
                              </Badge>
                              {user.role === 'courier' && (
                                <Badge variant={user.kyc_approved ? 'default' : 'secondary'}>
                                  {user.kyc_approved ? 'KYC Onaylı' : 'KYC Bekliyor'}
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-500">
                          {user.city || 'Şehir belirtilmemiş'}
                        </span>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => deleteUser(user.id)}
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Messaging Tab */}
          <TabsContent value="messaging" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Kurye Mesajlaşma</h2>
              <Button onClick={() => setShowMessageModal(true)}>
                📝 Yeni Mesaj Gönder
              </Button>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Mesaj Geçmişi</CardTitle>
                <CardDescription>
                  Kuryelerle yapılan mesajlaşma geçmişi
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">💬</div>
                  <p>Henüz mesaj gönderilmemiş</p>
                </div>
              </CardContent>
            </Card>

            {/* Message Modal */}
            {showMessageModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <Card className="w-full max-w-lg">
                  <CardHeader>
                    <CardTitle>Kuryelerle Mesajlaş</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <Label>Mesaj Türü</Label>
                        <Select 
                          value={messageForm.type} 
                          onValueChange={(value) => setMessageForm({...messageForm, type: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="broadcast">📢 Tüm Kuryeler</SelectItem>
                            <SelectItem value="selective">👥 Seçili Kuryeler</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label>Başlık</Label>
                        <Input
                          value={messageForm.title}
                          onChange={(e) => setMessageForm({...messageForm, title: e.target.value})}
                          placeholder="Mesaj başlığı..."
                        />
                      </div>

                      <div>
                        <Label>Mesaj</Label>
                        <Textarea
                          value={messageForm.message}
                          onChange={(e) => setMessageForm({...messageForm, message: e.target.value})}
                          placeholder="Mesaj içeriği..."
                          rows={4}
                        />
                      </div>

                      <div className="flex space-x-2">
                        <Button 
                          onClick={sendCourierMessage}
                          disabled={loading || !messageForm.message}
                          className="flex-1"
                        >
                          {loading ? 'Gönderiliyor...' : '📤 Mesaj Gönder'}
                        </Button>
                        <Button 
                          variant="outline"
                          onClick={() => setShowMessageModal(false)}
                          className="flex-1"
                        >
                          İptal
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Ads Tab */}
          <TabsContent value="ads" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Reklam Yönetimi</h2>
              <Button onClick={() => setShowAdModal(true)}>
                ➕ Yeni Reklam Ekle
              </Button>
            </div>

            <div className="space-y-4">
              {ads.map((ad) => (
                <Card key={ad.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="font-semibold">{ad.title}</h4>
                          <Badge variant={ad.active ? 'default' : 'secondary'}>
                            {ad.active ? 'Aktif' : 'Pasif'}
                          </Badge>
                          <Badge variant="outline">{ad.type}</Badge>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{ad.description}</p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>👁️ {ad.impressions || 0} görüntülenme</span>
                          <span>👆 {ad.clicks || 0} tıklama</span>
                          <span>📅 {new Date(ad.created_at).toLocaleDateString('tr-TR')}</span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => deleteAd(ad.id)}
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Ad Modal */}
            {showAdModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
                <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
                  <CardHeader>
                    <CardTitle>Yeni Reklam Oluştur</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <Label>Başlık</Label>
                        <Input
                          value={adForm.title}
                          onChange={(e) => setAdForm({...adForm, title: e.target.value})}
                          placeholder="Reklam başlığı..."
                        />
                      </div>

                      <div>
                        <Label>Açıklama</Label>
                        <Textarea
                          value={adForm.description}
                          onChange={(e) => setAdForm({...adForm, description: e.target.value})}
                          placeholder="Reklam açıklaması..."
                        />
                      </div>

                      <div>
                        <Label>Hedef URL</Label>
                        <Input
                          value={adForm.targetUrl}
                          onChange={(e) => setAdForm({...adForm, targetUrl: e.target.value})}
                          placeholder="https://example.com"
                        />
                      </div>

                      <div>
                        <Label>CTA Metni</Label>
                        <Input
                          value={adForm.ctaText}
                          onChange={(e) => setAdForm({...adForm, ctaText: e.target.value})}
                          placeholder="Daha Fazla"
                        />
                      </div>

                      <div>
                        <Label>Reklam Türü</Label>
                        <Select 
                          value={adForm.type} 
                          onValueChange={(value) => setAdForm({...adForm, type: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="general">Genel</SelectItem>
                            <SelectItem value="restaurant">Restoran</SelectItem>
                            <SelectItem value="campaign">Kampanya</SelectItem>
                            <SelectItem value="promotion">Promosyon</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id="active"
                          checked={adForm.active}
                          onChange={(e) => setAdForm({...adForm, active: e.target.checked})}
                        />
                        <Label htmlFor="active">Aktif</Label>
                      </div>

                      <div className="flex space-x-2">
                        <Button 
                          onClick={createAd}
                          disabled={loading || !adForm.title}
                          className="flex-1"
                        >
                          {loading ? 'Oluşturuluyor...' : '✅ Reklam Oluştur'}
                        </Button>
                        <Button 
                          variant="outline"
                          onClick={() => setShowAdModal(false)}
                          className="flex-1"
                        >
                          İptal
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* Featured Tab */}
          <TabsContent value="featured" className="space-y-6">
            <h2 className="text-2xl font-bold">Öne Çıkarma Yönetimi</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Featured Requests */}
              <Card>
                <CardHeader>
                  <CardTitle>Bekleyen Talepler</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {featuredRequests.filter(r => r.status === 'pending').map((request) => (
                      <div key={request.id} className="border rounded-lg p-3">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h5 className="font-semibold">{request.business_name}</h5>
                            <p className="text-sm text-gray-600">{request.plan_name} - ₺{request.price}</p>
                          </div>
                          <Badge variant="secondary">Bekliyor</Badge>
                        </div>
                        <div className="flex space-x-2">
                          <Button 
                            size="sm" 
                            onClick={() => approveFeaturedRequest(request.request_id)}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            ✅ Onayla
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => rejectFeaturedRequest(request.request_id)}
                          >
                            ❌ Reddet
                          </Button>
                        </div>
                      </div>
                    ))}
                    
                    {featuredRequests.filter(r => r.status === 'pending').length === 0 && (
                      <p className="text-center text-gray-500 py-4">Bekleyen talep yok</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Active Featured */}
              <Card>
                <CardHeader>
                  <CardTitle>Aktif Öne Çıkanlar</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {featuredBusinesses.map((featured) => (
                      <div key={featured.id} className="border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h5 className="font-semibold">{featured.business_name}</h5>
                            <p className="text-sm text-gray-600">
                              {featured.plan_name} - ₺{featured.price}
                            </p>
                            <p className="text-xs text-gray-500">
                              {featured.remaining_days} gün kaldı
                            </p>
                          </div>
                          <Badge className="bg-yellow-500">⭐ Aktif</Badge>
                        </div>
                      </div>
                    ))}
                    
                    {featuredBusinesses.length === 0 && (
                      <p className="text-center text-gray-500 py-4">Aktif öne çıkan yok</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <h2 className="text-2xl font-bold">Analytics & Raporlar</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Reklam Performansı</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {ads.slice(0, 5).map((ad) => (
                      <div key={ad.id} className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{ad.title}</p>
                          <p className="text-sm text-gray-600">
                            {ad.impressions || 0} görüntülenme, {ad.clicks || 0} tıklama
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">
                            {ad.impressions > 0 ? ((ad.clicks || 0) / ad.impressions * 100).toFixed(1) : 0}%
                          </div>
                          <div className="text-xs text-gray-500">CTR</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Gelir Analizi</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600 mb-2">
                        ₺{featuredBusinesses.reduce((sum, f) => sum + f.price, 0)}
                      </div>
                      <p className="text-gray-600">Toplam Öne Çıkarma Geliri</p>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="font-bold text-blue-600">
                          {featuredRequests.filter(r => r.status === 'pending').length}
                        </div>
                        <p className="text-xs text-gray-600">Bekleyen</p>
                      </div>
                      <div>
                        <div className="font-bold text-green-600">
                          {featuredBusinesses.length}
                        </div>
                        <p className="text-xs text-gray-600">Aktif</p>
                      </div>
                      <div>
                        <div className="font-bold text-gray-600">
                          {featuredRequests.filter(r => r.status === 'approved').length}
                        </div>
                        <p className="text-xs text-gray-600">Toplam Onaylı</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default EnhancedAdminPanel;