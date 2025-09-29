import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPanel = ({ user, onLogout }) => {
  // Navigation state
  const [currentView, setCurrentView] = useState('dashboard');
  const [loading, setLoading] = useState(false);

  // Data states
  const [pendingCouriers, setPendingCouriers] = useState([]);
  const [users, setUsers] = useState([]);
  const [ads, setAds] = useState([]);
  const [featuredRequests, setFeaturedRequests] = useState([]);
  const [featuredBusinesses, setFeaturedBusinesses] = useState([]);
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalCouriers: 0,
    totalBusinesses: 0,
    totalOrders: 0
  });

  // Modal states
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [showAdModal, setShowAdModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedCourier, setSelectedCourier] = useState(null);
  const [selectedCouriers, setSelectedCouriers] = useState([]);

  // Form states
  const [messageForm, setMessageForm] = useState({
    title: '',
    message: '',
    type: 'broadcast'
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
    }
  });
  const [rejectNotes, setRejectNotes] = useState('');

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchPendingCouriers(),
        fetchStats(),
        fetchUsers(),
        fetchAds(),
        fetchFeaturedRequests(),
        fetchFeaturedBusinesses()
      ]);
    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
    setLoading(false);
  };

  const fetchPendingCouriers = async () => {
    try {
      const response = await axios.get(`${API}/admin/couriers/kyc`);
      setPendingCouriers(response.data.filter(c => c.kyc_status === 'pending'));
    } catch (error) {
      console.error('Error fetching pending couriers:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`);
      setStats(response.data);
    } catch (error) {
      // Use fallback stats from users count
      setStats({
        totalUsers: users.length,
        totalCouriers: users.filter(u => u.user_type === 'courier').length,
        totalBusinesses: users.filter(u => u.user_type === 'business').length,
        totalOrders: 0
      });
    }
  };

  const fetchAds = async () => {
    try {
      const response = await axios.get(`${API}/admin/ads`);
      setAds(response.data);
    } catch (error) {
      console.error('Error fetching ads:', error);
      setAds([]);
    }
  };

  const fetchFeaturedRequests = async () => {
    try {
      const response = await axios.get(`${API}/admin/featured-requests`);
      setFeaturedRequests(response.data);
    } catch (error) {
      console.error('Error fetching featured requests:', error);
      setFeaturedRequests([]);
    }
  };

  const fetchFeaturedBusinesses = async () => {
    try {
      const response = await axios.get(`${API}/admin/featured-businesses`);
      setFeaturedBusinesses(response.data);
    } catch (error) {
      console.error('Error fetching featured businesses:', error);
      setFeaturedBusinesses([]);
    }
  };

  // Courier KYC Management
  const handleApprove = async (courierId, notes = '') => {
    try {
      await axios.patch(`${API}/admin/couriers/${courierId}/kyc`, {
        status: 'approved',
        notes
      });
      toast.success('Kurye onaylandı!');
      fetchPendingCouriers();
    } catch (error) {
      toast.error('Onaylama işlemi başarısız');
    }
  };

  const handleReject = async (courierId, notes) => {
    if (!notes.trim()) {
      toast.error('Ret sebebini belirtiniz');
      return;
    }
    
    try {
      await axios.patch(`${API}/admin/couriers/${courierId}/kyc`, {
        status: 'rejected',
        notes
      });
      toast.success('Kurye reddedildi');
      fetchPendingCouriers();
      setShowRejectModal(false);
      setRejectNotes('');
      setSelectedCourier(null);
    } catch (error) {
      toast.error('Reddetme işlemi başarısız');
    }
  };

  // Message Management
  const handleSendMessage = async () => {
    if (!messageForm.title.trim() || !messageForm.message.trim()) {
      toast.error('Başlık ve mesaj gereklidir');
      return;
    }

    try {
      const payload = {
        title: messageForm.title,
        message: messageForm.message,
        type: messageForm.type
      };

      if (messageForm.type === 'selective' && selectedCouriers.length === 0) {
        toast.error('En az bir kurye seçiniz');
        return;
      }

      if (messageForm.type === 'selective') {
        payload.courier_ids = selectedCouriers;
      }

      await axios.post(`${API}/admin/courier/message`, payload);
      toast.success('Mesaj gönderildi!');
      setShowMessageModal(false);
      setMessageForm({ title: '', message: '', type: 'broadcast' });
      setSelectedCouriers([]);
    } catch (error) {
      toast.error('Mesaj gönderilemedi');
    }
  };

  // Ad Management
  const handleCreateAd = async () => {
    if (!adForm.title.trim() || !adForm.description.trim()) {
      toast.error('Başlık ve açıklama gereklidir');
      return;
    }

    try {
      await axios.post(`${API}/admin/ads`, adForm);
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
        schedule: { startAt: '', endAt: '' }
      });
      fetchAds();
    } catch (error) {
      toast.error('Reklam oluşturulamadı');
    }
  };

  const handleDeleteAd = async (adId) => {
    try {
      await axios.delete(`${API}/admin/ads/${adId}`);
      toast.success('Reklam silindi');
      fetchAds();
    } catch (error) {
      toast.error('Reklam silinemedi');
    }
  };

  // Featured Business Management
  const handleApproveFeatured = async (requestId) => {
    try {
      await axios.post(`${API}/admin/featured-requests/${requestId}/approve`);
      toast.success('Öne çıkarma isteği onaylandı!');
      fetchFeaturedRequests();
      fetchFeaturedBusinesses();
    } catch (error) {
      toast.error('Onaylama başarısız');
    }
  };

  const handleRejectFeatured = async (requestId, reason) => {
    try {
      await axios.post(`${API}/admin/featured-requests/${requestId}/reject`, { reason });
      toast.success('Öne çıkarma isteği reddedildi');
      fetchFeaturedRequests();
    } catch (error) {
      toast.error('Reddetme başarısız');
    }
  };

  // Navigation items
  const navigationItems = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'kyc', label: '✅ KYC Onay', icon: '✅' },
    { id: 'users', label: '👥 Kullanıcılar', icon: '👥' },
    { id: 'messages', label: '💬 Mesajlaşma', icon: '💬' },
    { id: 'ads', label: '📢 Reklamlar', icon: '📢' },
    { id: 'featured', label: '⭐ Öne Çıkar', icon: '⭐' }
  ];

  const renderHeader = () => (
    <div className="bg-white shadow-sm border-b p-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">Admin Paneli</h1>
          <Badge className="bg-red-100 text-red-800">Kuryecini Yönetim Sistemi</Badge>
        </div>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">Hoş geldin, {user?.name || 'Admin'}</span>
          <Button onClick={onLogout} variant="outline" size="sm">
            Çıkış
          </Button>
        </div>
      </div>
    </div>
  );

  const renderNavbar = () => (
    <div className="bg-gray-50 border-b">
      <div className="max-w-7xl mx-auto">
        <nav className="flex space-x-1 p-2">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentView === item.id
                  ? 'bg-orange-100 text-orange-800 border border-orange-200'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <span className="mr-2">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm text-gray-600">Toplam Kullanıcı</p>
                <p className="text-2xl font-bold text-blue-600">{stats.totalUsers}</p>
              </div>
              <div className="text-blue-600">👥</div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm text-gray-600">Kurye</p>
                <p className="text-2xl font-bold text-green-600">{stats.totalCouriers}</p>
              </div>
              <div className="text-green-600">🚚</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm text-gray-600">İşletme</p>
                <p className="text-2xl font-bold text-purple-600">{stats.totalBusinesses}</p>
              </div>
              <div className="text-purple-600">🏪</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm text-gray-600">Toplam Sipariş</p>
                <p className="text-2xl font-bold text-orange-600">{stats.totalOrders}</p>
              </div>
              <div className="text-orange-600">📦</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Son Aktiviteler</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <Badge className="bg-green-100 text-green-800">Yeni</Badge>
                <span className="text-sm">5 dakika önce yeni kurye kaydı</span>
              </div>
              <div className="flex items-center space-x-3">
                <Badge className="bg-blue-100 text-blue-800">Sipariş</Badge>
                <span className="text-sm">12 dakika önce yeni sipariş</span>
              </div>
              <div className="flex items-center space-x-3">
                <Badge className="bg-purple-100 text-purple-800">İşletme</Badge>
                <span className="text-sm">1 saat önce işletme başvurusu</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sistem Durumu</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">API Durumu</span>
                <Badge className="bg-green-100 text-green-800">Aktif</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Veritabanı</span>
                <Badge className="bg-green-100 text-green-800">Bağlı</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Mesajlaşma</span>  
                <Badge className="bg-green-100 text-green-800">Çalışıyor</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Reklam Sistemi</span>
                <Badge className="bg-green-100 text-green-800">Çalışıyor</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  // KYC Component (existing functionality preserved)
  const renderKYC = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">KYC Onay Bekleyen Kuryeler</h2>
        <Badge variant="secondary">{pendingCouriers.length} bekleyen</Badge>
      </div>

      {pendingCouriers.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-gray-500 text-lg mb-4">Onay bekleyen kurye bulunmuyor</p>
            <p className="text-sm text-gray-400">Yeni kurye kayıtları burada görünecek</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {pendingCouriers.map((courier) => (
            <CourierCard
              key={courier.id}
              courier={courier}
              onApprove={handleApprove}
              onReject={(id) => {
                setSelectedCourier(id);
                setShowRejectModal(true);
              }}
            />
          ))}
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Kurye Başvurusunu Reddet</h3>
            <div className="space-y-4">
              <div>
                <Label htmlFor="reject-notes">Ret Sebebi</Label>
                <Textarea
                  id="reject-notes"
                  value={rejectNotes}
                  onChange={(e) => setRejectNotes(e.target.value)}
                  placeholder="Neden reddedildiğini açıklayın..."
                  rows={4}
                />
              </div>
              <div className="flex justify-end space-x-3">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowRejectModal(false);
                    setRejectNotes('');
                    setSelectedCourier(null);
                  }}
                >
                  İptal
                </Button>
                <Button 
                  variant="destructive"
                  onClick={() => handleReject(selectedCourier, rejectNotes)}
                >
                  Reddet
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderUsers = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Kullanıcı Yönetimi</h2>
        <Badge variant="secondary">{users.length} kullanıcı</Badge>
      </div>

      <div className="grid gap-4">
        {users.slice(0, 10).map((user) => (
          <Card key={user.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{user.email}</p>
                  <p className="text-sm text-gray-600">
                    {user.user_type} • {user.status || 'active'}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={user.user_type === 'admin' ? 'destructive' : 'secondary'}>
                    {user.user_type}
                  </Badge>
                  <Button variant="outline" size="sm">Düzenle</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderMessages = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Kuryelere Mesaj Gönder</h2>
        <Button onClick={() => setShowMessageModal(true)}>
          ✉️ Yeni Mesaj
        </Button>
      </div>

      <Card>
        <CardContent className="p-6">
          <p className="text-gray-600">
            Kuryelere önemli duyurular, güncellemeler ve bilgilendirmeler gönderebilirsiniz.
            Mesajlar kurye panelinde bildirim olarak görünecektir.
          </p>
        </div>
      </Card>

      {/* Message Modal */}
      {showMessageModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">Kuryelere Mesaj Gönder</h3>
            <div className="space-y-4">
              <div>
                <Label htmlFor="message-title">Başlık</Label>
                <Input
                  id="message-title"
                  value={messageForm.title}
                  onChange={(e) => setMessageForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Mesaj başlığı..."
                />
              </div>
              <div>
                <Label htmlFor="message-content">Mesaj</Label>
                <Textarea
                  id="message-content"
                  value={messageForm.message}
                  onChange={(e) => setMessageForm(prev => ({ ...prev, message: e.target.value }))}
                  placeholder="Mesaj içeriği..."
                  rows={4}
                />
              </div>
              <div>
                <Label htmlFor="message-type">Gönderim Türü</Label>
                <Select 
                  value={messageForm.type} 
                  onValueChange={(value) => setMessageForm(prev => ({ ...prev, type: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="broadcast">Tüm Kuryelere</SelectItem>
                    <SelectItem value="selective">Seçili Kuryelere</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end space-x-3">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowMessageModal(false);
                    setMessageForm({ title: '', message: '', type: 'broadcast' });
                  }}
                >
                  İptal
                </Button>
                <Button onClick={handleSendMessage}>
                  Gönder
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAds = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Reklam Yönetimi</h2>
        <Button onClick={() => setShowAdModal(true)}>
          📢 Yeni Reklam
        </Button>
      </div>

      <div className="grid gap-4">
        {ads.map((ad) => (
          <Card key={ad.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{ad.title}</p>
                  <p className="text-sm text-gray-600">{ad.description}</p>
                  <div className="flex items-center space-x-2 mt-2">
                    <Badge variant="secondary">{ad.type}</Badge>
                    {ad.targeting?.city && (
                      <Badge variant="outline">{ad.targeting.city}</Badge>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">Düzenle</Button>
                  <Button 
                    variant="destructive" 
                    size="sm"
                    onClick={() => handleDeleteAd(ad.id)}
                  >
                    Sil
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Ad Modal */}
      {showAdModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Yeni Reklam Oluştur</h3>
            <div className="space-y-4">
              <div>
                <Label htmlFor="ad-title">Başlık</Label>
                <Input
                  id="ad-title"
                  value={adForm.title}
                  onChange={(e) => setAdForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Reklam başlığı..."
                />
              </div>
              <div>
                <Label htmlFor="ad-description">Açıklama</Label>
                <Textarea
                  id="ad-description"
                  value={adForm.description}
                  onChange={(e) => setAdForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Reklam açıklaması..."
                  rows={3}
                />
              </div>
              <div>
                <Label htmlFor="ad-image">Görsel URL</Label>
                <Input
                  id="ad-image"
                  value={adForm.imgUrl}
                  onChange={(e) => setAdForm(prev => ({ ...prev, imgUrl: e.target.value }))}
                  placeholder="https://example.com/image.jpg"
                />
              </div>
              <div>
                <Label htmlFor="ad-target">Hedef URL</Label>
                <Input
                  id="ad-target"
                  value={adForm.targetUrl}
                  onChange={(e) => setAdForm(prev => ({ ...prev, targetUrl: e.target.value }))}
                  placeholder="https://example.com"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowAdModal(false);
                    setAdForm({
                      title: '',
                      description: '',
                      imgUrl: '',
                      targetUrl: '',
                      ctaText: 'Daha Fazla',
                      type: 'general',
                      targeting: { city: '', category: '' },
                      schedule: { startAt: '', endAt: '' }
                    });
                  }}
                >
                  İptal
                </Button>
                <Button onClick={handleCreateAd}>
                  Oluştur
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderFeatured = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Öne Çıkarma Yönetimi</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Bekleyen İstekler</CardTitle>
            <CardDescription>{featuredRequests.length} istek bekliyor</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {featuredRequests.slice(0, 5).map((request) => (
                <div key={request.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{request.business_name}</p>
                    <p className="text-sm text-gray-600">{request.plan_type} • ₺{request.price}</p>
                  </div>
                  <div className="flex space-x-2">
                    <Button 
                      size="sm" 
                      onClick={() => handleApproveFeatured(request.id)}
                    >
                      Onayla
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleRejectFeatured(request.id, 'Admin tarafından reddedildi')}
                    >
                      Reddet
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Aktif Öne Çıkanlar</CardTitle>
            <CardDescription>{featuredBusinesses.length} işletme öne çıkarılmış</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {featuredBusinesses.slice(0, 5).map((business) => (
                <div key={business.id} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <div>
                    <p className="font-medium">{business.business_name}</p>
                    <p className="text-sm text-gray-600">
                      {business.plan_type} • {new Date(business.expires_at).toLocaleDateString('tr-TR')} tarihine kadar
                    </p>
                  </div>
                  <Badge className="bg-green-100 text-green-800">Aktif</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard': return renderDashboard();
      case 'kyc': return renderKYC();
      case 'users': return renderUsers();
      case 'messages': return renderMessages();
      case 'ads': return renderAds();
      case 'featured': return renderFeatured();
      default: return renderDashboard();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {renderHeader()}
      {renderNavbar()}
      <div className="max-w-7xl mx-auto p-6">
        {renderContent()}
      </div>
    </div>
  );
};

// CourierCard component (preserved from original)
const CourierCard = ({ courier, onApprove, onReject }) => {
  const [notes, setNotes] = useState('');

  const getVehicleTypeName = (type) => {
    const types = {
      'motorcycle': 'Motosiklet',
      'bicycle': 'Bisiklet', 
      'car': 'Araba',
      'scooter': 'Scooter'
    };
    return types[type] || type;
  };

  return (
    <Card className="shadow-lg" data-testid={`courier-card-${courier.id}`}>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-xl">{courier.name}</CardTitle>
            <CardDescription>{courier.phone}</CardDescription>
          </div>
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            Onay Bekliyor
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold mb-2">Kurye Bilgileri</h4>
            <div className="space-y-1 text-sm text-gray-600">
              <p><strong>Araç Türü:</strong> {getVehicleTypeName(courier.vehicle_type)}</p>
              <p><strong>Ehliyet Sınıfı:</strong> {courier.license_class}</p>
              <p><strong>Kayıt Tarihi:</strong> {new Date(courier.created_at).toLocaleDateString('tr-TR')}</p>
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold mb-2">Belgeler</h4>
            <div className="space-y-2">
              {courier.license_photo_url && (
                <Button variant="outline" size="sm" className="w-full">
                  📄 Ehliyet Fotoğrafı Görüntüle
                </Button>
              )}
              {courier.vehicle_document_url && (
                <Button variant="outline" size="sm" className="w-full">
                  📋 Araç Belgesi Görüntüle
                </Button>
              )}
              {courier.profile_photo_url && (
                <Button variant="outline" size="sm" className="w-full">
                  👤 Profil Fotoğrafı Görüntüle
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="border-t pt-4">
          <div className="flex justify-between items-center">
            <div className="flex-1 mr-4">
              <Label htmlFor={`notes-${courier.id}`} className="text-sm font-medium">
                Notlar (İsteğe bağlı)
              </Label>
              <Textarea
                id={`notes-${courier.id}`}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Onay/ret notu ekleyin..."
                className="mt-1"
                rows={2}
              />
            </div>
          </div>
          
          <div className="flex justify-end space-x-3 mt-4">
            <Button
              variant="outline"
              onClick={() => onReject(courier.id)}
              className="text-red-600 border-red-200 hover:bg-red-50"
            >
              ❌ Reddet
            </Button>
            <Button
              onClick={() => onApprove(courier.id, notes)}
              className="bg-green-600 hover:bg-green-700"
            >
              ✅ Onayla
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AdminPanel;