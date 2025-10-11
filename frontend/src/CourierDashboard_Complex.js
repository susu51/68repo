import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Courier Nearby Orders Component (Original from GitHub - City-wide with Notifications)
export const CourierDashboard = ({ user, onLogout }) => {
  const [nearbyOrders, setNearbyOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [courierLocation, setCourierLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [lastNotificationTime, setLastNotificationTime] = useState(0);
  const [isMounted, setIsMounted] = useState(true);

  useEffect(() => {
    setIsMounted(true);
    // First get location, then fetch orders
    startLocationTracking();

    // Fetch orders every 30 seconds, but only after we have location
    const ordersInterval = setInterval(() => {
      if (courierLocation && isMounted) {
        fetchNearbyOrders();
      }
    }, 30000);

    // Update location every 3 minutes
    const locationInterval = setInterval(() => {
      if (isMounted) {
        updateLocation();
      }
    }, 180000);

    return () => {
      setIsMounted(false);
      clearInterval(ordersInterval);
      clearInterval(locationInterval);
    };
  }, []);

  // Fetch orders after location is obtained
  useEffect(() => {
    if (courierLocation && isMounted) {
      fetchNearbyOrders();
    }
  }, [courierLocation, isMounted]);

  const fetchNearbyOrders = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.get(`${API}/orders/nearby`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (isMounted) {
        const orders = response.data || [];
        setNearbyOrders(orders);

        // Check for very close orders and send notifications
        if (courierLocation && orders.length > 0) {
          checkForCloseOrders(orders);
        }
      }

    } catch (error) {
      console.error('Siparişler alınamadı:', error);
      if (isMounted) {
        setNearbyOrders([]);
      }
    }
    if (isMounted) {
      setLoading(false);
    }
  };

  const startLocationTracking = () => {
    if (!navigator.geolocation) {
      if (isMounted) {
        setLocationError('Tarayıcınız konum hizmetlerini desteklemiyor');
        setLoading(false);
      }
      return;
    }

    if (isMounted) {
      setLoading(true);
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (isMounted) {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setCourierLocation(location);
          setLocationError(null);
          console.log('Konum alındı:', location);
        }
      },
      (error) => {
        if (isMounted) {
          console.error('Konum alınamadı:', error);
          setLocationError('Konum erişimi reddedildi veya kullanılamıyor');
          setLoading(false);
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  };

  const updateLocation = () => {
    if (!navigator.geolocation || !isMounted) return;

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (isMounted) {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setCourierLocation(location);

          // Refresh orders when location updates
          if (nearbyOrders.length > 0) {
            checkForCloseOrders(nearbyOrders);
          }
        }
      },
      (error) => {
        if (isMounted) {
          console.error('Konum güncellenemedi:', error);
        }
      },
      { enableHighAccuracy: true, timeout: 5000 }
    );
  };

  // Calculate distance using Haversine formula
  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  // Check for orders within 1km and send audio notification
  const checkForCloseOrders = (orders) => {
    if (!courierLocation) return;

    const now = Date.now();
    // Don't send notifications more than once per 5 minutes
    if (now - lastNotificationTime < 300000) return;

    const closeOrders = orders.filter(order => {
      const pickupLat = order.pickup_address?.lat || 41.0082;
      const pickupLng = order.pickup_address?.lng || 28.9784;
      const distance = calculateDistance(
        courierLocation.lat, courierLocation.lng,
        pickupLat, pickupLng
      );
      return distance <= 1; // Within 1km
    });

    if (closeOrders.length > 0) {
      sendAudioNotification(closeOrders);
      setLastNotificationTime(now);
    }
  };

  // Send audio notification for close orders
  const sendAudioNotification = (closeOrders) => {
    // Browser notification
    if (Notification.permission === 'granted') {
      const orderCount = closeOrders.length;
      const totalValue = closeOrders.reduce((sum, order) => sum + (order.total_amount || 0), 0);

      new Notification('🚚 Yakında Sipariş!', {
        body: `${orderCount} adet sipariş 1km yakınınızda! Toplam: ₺${totalValue.toFixed(2)}`,
        icon: '/favicon.ico',
        tag: 'nearby-order'
      });
    }

    // Audio notification
    try {
      const audio = new Audio();
      // Create beep sound using Web Audio API
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.setValueAtTime(800, audioContext.currentTime); // 800Hz beep
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);

      console.log('🔊 Ses bildirimi gönderildi!');
    } catch (error) {
      console.error('Ses bildirimi gönderilemedi:', error);
    }

    // Visual toast notification
    toast.success(`🚚 ${closeOrders.length} adet sipariş yakınınızda!`);
  };

  // Request notification permission on component mount
  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const acceptOrder = async (orderId) => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies // Fixed token key
      await axios.post(`${API}/orders/${orderId}/accept`, {}, {
        withCredentials: true
      });

      toast.success('Sipariş kabul edildi!');
      fetchNearbyOrders(); // Refresh list
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sipariş kabul edilemedi');
    }
  };

  // Update map markers with order locations
  const updateMapMarkers = (orders) => {
    const markers = orders.map(order => ({
      id: order.id,
      position: [order.pickup_latitude || 39.925533, order.pickup_longitude || 32.866287],
      popup: `
        <div>
          <h3>${order.business_name}</h3>
          <p>Tutar: ₺${order.total_amount}</p>
          <p>Komisyon: ₺${order.commission}</p>
          <p>Mesafe: ${order.distance || 'Hesaplanıyor'}km</p>
        </div>
      `,
      type: 'business'
    }));

    // Add courier location if available
    if (courierLocation) {
      markers.push({
        id: 'courier',
        position: [courierLocation.latitude, courierLocation.longitude],
        popup: 'Sizin Konumunuz',
        type: 'user'
      });
    }

    // Add current order delivery location
    if (currentOrder && currentOrder.delivery_latitude) {
      markers.push({
        id: 'delivery',
        position: [currentOrder.delivery_latitude, currentOrder.delivery_longitude],
        popup: `
          <div>
            <h3>Teslimat Adresi</h3>
            <p>${currentOrder.delivery_address}</p>
          </div>
        `,
        type: 'customer'
      });

      // Create route if courier location is available
      if (courierLocation) {
        setRoutePolyline([
          [courierLocation.latitude, courierLocation.longitude],
          [currentOrder.delivery_latitude, currentOrder.delivery_longitude]
        ]);
      }
    }

    setMapMarkers(markers);
  };

  // Fetch order history
  const fetchOrderHistory = async () => {
    try {
      const params = {};
      if (historyFilter.status !== 'all') params.status_filter = historyFilter.status;
      if (historyFilter.date !== 'all') params.date_filter = historyFilter.date;
      
      const response = await axios.get(`${API}/courier/orders/history`, { params });
      setOrderHistory(response.data.orders || []);
    } catch (error) {
      console.error('Failed to fetch order history:', error);
    }
  };

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/courier/notifications`);
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.notifications?.filter(n => !n.read).length || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  // Fetch messages
  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/courier/messages`);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/courier/stats`);
      setStats(response.data || {
        totalOrders: 0,
        totalEarnings: 0,
        monthlyOrders: 0,
        monthlyEarnings: 0
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // Accept order
  const acceptOrder = async (orderId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/courier/orders/${orderId}/accept`);
      toast.success('Sipariş kabul edildi!');
      fetchAvailableOrders();
      setCurrentOrder(availableOrders.find(o => o.id === orderId));
    } catch (error) {
      toast.error('Sipariş kabul edilemedi');
    }
    setLoading(false);
  };

  // Update order status
  const updateOrderStatus = async (orderId, newStatus) => {
    setLoading(true);
    try {
      await axios.post(`${API}/courier/orders/${orderId}/update-status`, {
        status: newStatus
      });
      
      const statusMessages = {
        'picked_up': 'Sipariş alındı olarak işaretlendi',
        'delivered': 'Sipariş teslim edildi!'
      };
      
      toast.success(statusMessages[newStatus] || 'Durum güncellendi');
      
      if (newStatus === 'delivered') {
        setCurrentOrder(null);
        setRoutePolyline(null);
      } else {
        setCurrentOrder(prev => ({ ...prev, status: newStatus }));
      }
      
      fetchOrderHistory();
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
    setLoading(false);
  };

  // Toggle online status
  const toggleOnlineStatus = async () => {
    try {
      const response = await axios.post(`${API}/courier/status/toggle`);
      setIsOnline(response.data.is_online);
      toast.success(response.data.message || 'Durum güncellendi');
    } catch (error) {
      toast.error('Durum değiştirilemedi');
    }
  };

  // Mark notification as read
  const markNotificationRead = async (notificationId) => {
    try {
      await axios.post(`${API}/courier/notifications/${notificationId}/read`);
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Generate monthly report
  const generateMonthlyReport = async () => {
    try {
      const response = await axios.get(`${API}/courier/monthly-report`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `kurye-rapor-${new Date().getMonth() + 1}-${new Date().getFullYear()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Aylık rapor indirildi');
    } catch (error) {
      toast.error('Rapor oluşturulamadı');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="text-2xl">🚚</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Kurye Paneli</h1>
                <p className="text-sm text-gray-600">
                  {user?.first_name} {user?.last_name}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Online/Offline Toggle */}
              <Button
                onClick={toggleOnlineStatus}
                disabled={loading}
                className={`${isOnline 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-gray-600 hover:bg-gray-700'
                } text-white`}
                size="sm"
              >
                {isOnline ? '🟢 Çevrimiçi' : '🔴 Çevrimdışı'}
              </Button>
              
              {/* Notifications Badge */}
              <div className="relative">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setActiveTab('notifications')}
                >
                  🔔
                  {unreadCount > 0 && (
                    <Badge className="absolute -top-2 -right-2 bg-red-500 text-white min-w-5 h-5 flex items-center justify-center text-xs">
                      {unreadCount}
                    </Badge>
                  )}
                </Button>
              </div>
              
              <Button onClick={onLogout} variant="outline" size="sm">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Current Order Status */}
      {currentOrder && (
        <div className="bg-blue-50 border-b border-blue-200 py-4">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <Card className="border-blue-200">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span>📦</span>
                  <span>Mevcut Sipariş</span>
                  <Badge variant="secondary">{currentOrder.status}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p><strong>İşletme:</strong> {currentOrder.business_name}</p>
                    <p><strong>Teslimat Adresi:</strong> {currentOrder.delivery_address}</p>
                    <p><strong>Tutar:</strong> ₺{currentOrder.total_amount}</p>
                    <p><strong>Komisyon:</strong> ₺{currentOrder.commission}</p>
                  </div>
                  <div className="flex flex-col space-y-2">
                    {currentOrder.status === 'accepted' && (
                      <Button 
                        onClick={() => updateOrderStatus(currentOrder.id, 'picked_up')}
                        className="bg-orange-600 hover:bg-orange-700"
                        disabled={loading}
                      >
                        📤 Siparişi Aldım
                      </Button>
                    )}
                    {currentOrder.status === 'picked_up' && (
                      <Button 
                        onClick={() => updateOrderStatus(currentOrder.id, 'delivered')}
                        className="bg-green-600 hover:bg-green-700"
                        disabled={loading}
                      >
                        ✅ Teslim Ettim
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="orders">📋 Siparişler</TabsTrigger>
            <TabsTrigger value="map">🗺️ Harita</TabsTrigger>
            <TabsTrigger value="history">📊 Geçmiş</TabsTrigger>
            <TabsTrigger value="notifications">
              🔔 Bildirimler
              {unreadCount > 0 && (
                <Badge className="ml-1 bg-red-500">{unreadCount}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="stats">📈 İstatistikler</TabsTrigger>
          </TabsList>

          {/* Available Orders Tab */}
          <TabsContent value="orders" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Mevcut Siparişler</h2>
              <Button onClick={fetchAvailableOrders} variant="outline">
                🔄 Yenile
              </Button>
            </div>

            {availableOrders.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-gray-500 text-lg mb-4">Şu anda mevcut sipariş bulunmuyor</p>
                  <p className="text-sm text-gray-400">
                    {isOnline ? 'Yeni siparişler geldiğinde burada görünecek' : 'Sipariş almak için çevrimiçi olmalısınız'}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {availableOrders.map((order) => (
                  <Card key={order.id}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-semibold text-lg">{order.business_name}</h3>
                            <Badge variant="secondary">₺{order.total_amount}</Badge>
                          </div>
                          <p className="text-gray-600 mb-2">📍 {order.delivery_address}</p>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>📏 {order.distance || 'Hesaplanıyor'}km</span>
                            <span>⏱️ ~{order.estimated_time || '20'} dk</span>
                            <span>💰 Komisyon: ₺{order.commission}</span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <Button 
                            onClick={() => acceptOrder(order.id)}
                            disabled={loading}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            ✅ Kabul Et
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Map Tab */}
          <TabsContent value="map" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Harita Görünümü</h2>
              <div className="flex items-center space-x-2">
                <Badge variant={isOnline ? 'default' : 'secondary'}>
                  {isOnline ? 'Çevrimiçi' : 'Çevrimdışı'}
                </Badge>
                {courierLocation && (
                  <Badge variant="outline">
                    Konum: {courierLocation.latitude.toFixed(4)}, {courierLocation.longitude.toFixed(4)}
                  </Badge>
                )}
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <LeafletMap
                  center={courierLocation ? [courierLocation.latitude, courierLocation.longitude] : [39.925533, 32.866287]}
                  zoom={13}
                  height="500px"
                  markers={mapMarkers}
                  courierMode={true}
                  routePolyline={routePolyline}
                  className="rounded-lg"
                />
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Mevcut Siparişler</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-blue-600">{availableOrders.length}</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Aktif Sipariş</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-green-600">{currentOrder ? 1 : 0}</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Durum</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className={`text-2xl font-bold ${isOnline ? 'text-green-600' : 'text-gray-600'}`}>
                    {isOnline ? 'Aktif' : 'Pasif'}
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Sipariş Geçmişi</h2>
              <div className="flex space-x-2">
                <Select 
                  value={historyFilter.status} 
                  onValueChange={(value) => setHistoryFilter(prev => ({ ...prev, status: value }))}
                >
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tüm Durumlar</SelectItem>
                    <SelectItem value="delivered">Teslim Edildi</SelectItem>
                    <SelectItem value="cancelled">İptal Edildi</SelectItem>
                  </SelectContent>
                </Select>
                <Select 
                  value={historyFilter.date} 
                  onValueChange={(value) => setHistoryFilter(prev => ({ ...prev, date: value }))}
                >
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tüm Zamanlar</SelectItem>
                    <SelectItem value="today">Bugün</SelectItem>
                    <SelectItem value="week">Bu Hafta</SelectItem>
                    <SelectItem value="month">Bu Ay</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={fetchOrderHistory} variant="outline">
                  🔍 Filtrele
                </Button>
              </div>
            </div>

            <div className="grid gap-4">
              {orderHistory.map((order) => (
                <Card key={order.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-medium">{order.business_name}</span>
                          <Badge 
                            variant={order.status === 'delivered' ? 'default' : 'secondary'}
                            className={order.status === 'delivered' ? 'bg-green-100 text-green-800' : ''}
                          >
                            {order.status === 'delivered' ? 'Teslim Edildi' : order.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600">
                          {new Date(order.created_at).toLocaleDateString('tr-TR')} • 
                          ₺{order.total_amount} • Komisyon: ₺{order.commission}
                        </p>
                      </div>
                      <Button variant="outline" size="sm">
                        Detay
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-4">
            <h2 className="text-2xl font-bold">Bildirimler</h2>
            
            {notifications.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-gray-500">Henüz bildiriminiz bulunmuyor</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {notifications.map((notification) => (
                  <Card 
                    key={notification.id} 
                    className={notification.read ? 'bg-gray-50' : 'bg-blue-50 border-blue-200'}
                  >
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="font-medium">{notification.title}</h3>
                          <p className="text-gray-600 mt-1">{notification.message}</p>
                          <p className="text-xs text-gray-500 mt-2">
                            {new Date(notification.created_at).toLocaleString('tr-TR')}
                          </p>
                        </div>
                        {!notification.read && (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => markNotificationRead(notification.id)}
                          >
                            Okundu
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Admin Messages */}
            <div className="mt-8">
              <h3 className="text-xl font-semibold mb-4">Admin Mesajları</h3>
              {messages.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-8">
                    <p className="text-gray-500">Henüz mesajınız bulunmuyor</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <Card key={message.id}>
                      <CardContent className="p-4">
                        <div className="flex items-start space-x-3">
                          <div className="bg-orange-100 p-2 rounded-full">
                            <span className="text-orange-600">📢</span>
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium">{message.title}</h3>
                            <p className="text-gray-600 mt-1">{message.message}</p>
                            <p className="text-xs text-gray-500 mt-2">
                              Admin • {new Date(message.created_at).toLocaleString('tr-TR')}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Stats Tab */}
          <TabsContent value="stats" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">İstatistikler & Raporlar</h2>
              <Button onClick={generateMonthlyReport} variant="outline">
                📄 Aylık Rapor İndir
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Toplam İstatistikler</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>Toplam Sipariş</span>
                    <Badge variant="secondary">{stats.totalOrders}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Toplam Kazanç</span>
                    <Badge className="bg-green-100 text-green-800">₺{stats.totalEarnings}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Ortalama Sipariş</span>
                    <Badge variant="secondary">
                      ₺{stats.totalOrders > 0 ? (stats.totalEarnings / stats.totalOrders).toFixed(2) : '0.00'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Bu Ay</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>Aylık Sipariş</span>
                    <Badge variant="secondary">{stats.monthlyOrders}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Aylık Kazanç</span>
                    <Badge className="bg-green-100 text-green-800">₺{stats.monthlyEarnings}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Net Kazanç (%5 komisyon)</span>
                    <Badge className="bg-blue-100 text-blue-800">
                      ₺{(stats.monthlyEarnings * 0.95).toFixed(2)}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Komisyon Bilgisi</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">
                    • Her siparişten %5 komisyon alınır
                  </p>
                  <p className="text-sm text-gray-600 mb-2">
                    • Kazançlar haftalık olarak hesabınıza aktarılır
                  </p>
                  <p className="text-sm text-gray-600">
                    • Detaylı rapor için "Aylık Rapor İndir" butonunu kullanın
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default CourierDashboard;