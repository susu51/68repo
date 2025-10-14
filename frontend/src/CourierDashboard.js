import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import OpenStreetMap from './components/OpenStreetMap';
import { toast } from 'sonner';
import { CourierOrderHistory } from './components/CourierOrderHistory';
import { CourierEarningsReport } from './components/CourierEarningsReport';
import { CourierPDFReports } from './components/CourierPDFReports';
import { CourierProfileUpdate } from './components/CourierProfileUpdate';
import { CourierAvailability } from './components/CourierAvailability';
import { CourierReadyOrdersMap } from './components/CourierReadyOrdersMap';
import { CourierOrderHistoryFiltered } from './components/CourierOrderHistoryFiltered';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://quickship-49.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierDashboard = ({ user, onLogout }) => {
  // Navigation state
  const [activeTab, setActiveTab] = useState('orders');
  const [loading, setLoading] = useState(true);
  
  // Location and orders
  const [nearbyOrders, setNearbyOrders] = useState([]);
  const [courierLocation, setCourierLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [currentOrder, setCurrentOrder] = useState(null);
  const [orderHistory, setOrderHistory] = useState([]);
  const [isOnline, setIsOnline] = useState(true);
  const [lastNotificationTime, setLastNotificationTime] = useState(0);
  const [isMounted, setIsMounted] = useState(true);

  // Earnings and stats
  const [earnings, setEarnings] = useState({
    daily: 0,
    weekly: 0,
    monthly: 0,
    total: 0
  });
  const [stats, setStats] = useState({
    totalOrders: 0,
    completedOrders: 0,
    cancelledOrders: 0,
    avgDeliveryTime: 0,
    rating: 4.5,
    totalDistance: 0
  });

  // Map data
  const [mapMarkers, setMapMarkers] = useState([]);
  const [routePolyline, setRoutePolyline] = useState(null);

  // Profile data
  const [profile, setProfile] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
    phone: user?.phone || '',
    email: user?.email || '',
    profilePhoto: '',
    iban: '',
    workingHours: {
      start: '09:00',
      end: '22:00',
      workDays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    },
    notifications: {
      sound: true,
      push: true,
      email: false
    }
  });

  // Filters
  const [historyFilter, setHistoryFilter] = useState({
    status: 'all',
    dateRange: 'all',
    sortBy: 'date_desc'
  });

  useEffect(() => {
    setIsMounted(true);
    const stopLocationTracking = startLocationTracking();
    fetchInitialData();

    // Auto refresh intervals
    const ordersInterval = setInterval(() => {
      if (courierLocation && isMounted && activeTab === 'orders') {
        fetchNearbyOrders();
      }
    }, 30000);

    const statsInterval = setInterval(() => {
      if (isMounted) {
        fetchEarnings();
        fetchStats();
      }
    }, 300000); // 5 minutes

    return () => {
      setIsMounted(false);
      clearInterval(ordersInterval);
      clearInterval(statsInterval);
      if (stopLocationTracking) {
        stopLocationTracking();
      }
    };
  }, []);

  useEffect(() => {
    if (courierLocation && isMounted) {
      fetchNearbyOrders();
      updateMapData();
    }
  }, [courierLocation, currentOrder]);

  const fetchInitialData = async () => {
    await Promise.all([
      fetchNearbyOrders(),
      fetchOrderHistory(),
      fetchEarnings(),
      fetchStats(),
      fetchProfile()
    ]);
    setLoading(false);
  };

  // Location tracking with watchPosition for continuous updates
  const startLocationTracking = () => {
    if (!navigator.geolocation) {
      if (isMounted) {
        setLocationError('Tarayıcınız konum hizmetlerini desteklemiyor');
        setLoading(false);
      }
      return;
    }

    // Start continuous location tracking with watchPosition
    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        if (isMounted) {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            heading: position.coords.heading,
            speed: position.coords.speed,
            accuracy: position.coords.accuracy,
            ts: Date.now()
          };
          setCourierLocation(location);
          setLocationError(null);
          updateLocationOnServer(location);
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

    // Store watchId for cleanup
    return () => {
      if (watchId) {
        navigator.geolocation.clearWatch(watchId);
      }
    };
  };

  const updateLocationOnServer = React.useCallback(async (location) => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      await axios.post(`${API}/courier/location`, location, {
        withCredentials: true
      });
    } catch (error) {
      console.error('Location update failed:', error);
    }
  }, []);

  // Data fetching functions
  const fetchNearbyOrders = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.get(`${API}/courier/orders/available`, {
        withCredentials: true
      });

      if (isMounted) {
        const orders = response.data?.orders || [];
        setNearbyOrders(orders);
        
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
  };

  const fetchOrderHistory = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const params = {};
      
      if (historyFilter.status !== 'all') params.status = historyFilter.status;
      if (historyFilter.dateRange !== 'all') params.date_range = historyFilter.dateRange;
      params.sort_by = historyFilter.sortBy;

      const response = await axios.get(`${API}/courier/orders/history`, {
        withCredentials: true,
        params
      });

      if (isMounted) {
        setOrderHistory(response.data.orders || []);
      }
    } catch (error) {
      console.error('Sipariş geçmişi alınamadı:', error);
    }
  };

  const fetchEarnings = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.get(`${API}/courier/earnings`, {
        withCredentials: true
      });

      if (isMounted) {
        setEarnings(response.data || {
          daily: 0,
          weekly: 0,
          monthly: 0,
          total: 0
        });
      }
    } catch (error) {
      console.error('Kazanç bilgisi alınamadı:', error);
    }
  };

  const fetchStats = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.get(`${API}/courier/stats`, {
        withCredentials: true
      });

      if (isMounted) {
        setStats(response.data || {
          totalOrders: 0,
          completedOrders: 0,
          cancelledOrders: 0,
          avgDeliveryTime: 0,
          rating: 4.5,
          totalDistance: 0
        });
      }
    } catch (error) {
      console.error('İstatistik bilgisi alınamadı:', error);
    }
  };

  const fetchProfile = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.get(`${API}/courier/profile`, {
        withCredentials: true
      });

      if (isMounted) {
        setProfile(prev => ({
          ...prev,
          ...response.data
        }));
      }
    } catch (error) {
      console.error('Profil bilgisi alınamadı:', error);
    }
  };

  // Distance calculation
  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  // Notification system
  const checkForCloseOrders = (orders) => {
    if (!courierLocation) return;

    const now = Date.now();
    if (now - lastNotificationTime < 300000) return; // 5 minute cooldown

    const closeOrders = orders.filter(order => {
      const pickupLat = order.pickup_address?.lat || 41.0082;
      const pickupLng = order.pickup_address?.lng || 28.9784;
      const distance = calculateDistance(
        courierLocation.lat, courierLocation.lng,
        pickupLat, pickupLng
      );
      return distance <= 1;
    });

    if (closeOrders.length > 0) {
      sendAudioNotification(closeOrders);
      setLastNotificationTime(now);
    }
  };

  const sendAudioNotification = (closeOrders) => {
    if (profile.notifications.push && Notification.permission === 'granted') {
      const orderCount = closeOrders.length;
      const totalValue = closeOrders.reduce((sum, order) => sum + (order.total_amount || 0), 0);

      new Notification('🚚 Yakında Sipariş!', {
        body: `${orderCount} adet sipariş 1km yakınınızda! Toplam: ₺${totalValue.toFixed(2)}`,
        icon: '/favicon.ico',
        tag: 'nearby-order'
      });
    }

    if (profile.notifications.sound) {
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
      } catch (error) {
        console.error('Ses bildirimi gönderilemedi:', error);
      }
    }

    toast.success(`🚚 ${closeOrders.length} adet sipariş yakınınızda!`);
  };

  // Order management
  const acceptOrder = async (orderId) => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.patch(`${API}/courier/orders/${orderId}/pickup`, {}, {
        withCredentials: true
      });

      toast.success('Sipariş alındı! Teslim etmeye başlayabilirsiniz.');
      // Update current order or refresh list
      fetchNearbyOrders();
    } catch (error) {
      console.error('Error picking up order:', error);
      toast.error(error.response?.data?.detail || 'Sipariş alınamadı');
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      await axios.post(`${API}/orders/${orderId}/status`, {
        status,
        location: courierLocation,
        timestamp: new Date().toISOString()
      }, {
        withCredentials: true
      });

      const statusMessages = {
        'picked_up': 'Sipariş alındı!',
        'on_way': 'Yola çıkıldı!',
        'delivered': 'Sipariş teslim edildi!',
        'cancelled': 'Sipariş iptal edildi'
      };

      toast.success(statusMessages[status] || 'Durum güncellendi');
      
      if (status === 'delivered' || status === 'cancelled') {
        setCurrentOrder(null);
        setRoutePolyline(null);
      }
      
      fetchOrderHistory();
      fetchEarnings();
      fetchStats();
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
  };

  const toggleOnlineStatus = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.post(`${API}/courier/status/toggle`, {}, {
        withCredentials: true
      });

      setIsOnline(response.data.is_online);
      toast.success(response.data.is_online ? 'Çevrimiçi oldunuz' : 'Çevrimdışı oldunuz');
    } catch (error) {
      toast.error('Durum değiştirilemedi');
    }
  };

  // Map functions
  const updateMapData = () => {
    const markers = [];
    
    // Add nearby orders
    nearbyOrders.forEach(order => {
      if (order.pickup_address?.lat && order.pickup_address?.lng) {
        markers.push({
          id: `order-${order.id}`,
          lat: order.pickup_address.lat,
          lng: order.pickup_address.lng,
          title: order.business_name,
          description: `₺${order.total_amount}`,
          popup: `
            <div>
              <h3>${order.business_name}</h3>
              <p>₺${order.total_amount}</p>
              <p>Komisyon: ₺${order.commission_amount}</p>
            </div>
          `,
          type: 'business'
        });
      }
    });

    // Add courier location
    if (courierLocation) {
      markers.push({
        id: 'courier',
        lat: courierLocation.lat,
        lng: courierLocation.lng,
        title: 'Sizin Konumunuz',
        description: 'Canlı konum takibi aktif',
        popup: 'Sizin Konumunuz',
        type: 'user'
      });
    }

    // Add current order route
    if (currentOrder && currentOrder.delivery_address?.lat && courierLocation) {
      markers.push({
        id: 'delivery',
        lat: currentOrder.delivery_address.lat,
        lng: currentOrder.delivery_address.lng,
        title: 'Teslimat Adresi',
        description: currentOrder.delivery_address.address,
        popup: `
          <div>
            <h3>Teslimat Adresi</h3>
            <p>${currentOrder.delivery_address.address}</p>
          </div>
        `,
        type: 'customer'
      });

      setRoutePolyline([
        [courierLocation.lat, courierLocation.lng],
        [currentOrder.delivery_address.lat, currentOrder.delivery_address.lng]
      ]);
    }

    setMapMarkers(markers);
  };

  // Profile update
  const updateProfile = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      await axios.put(`${API}/courier/profile`, profile, {
        withCredentials: true
      });

      toast.success('Profil güncellendi!');
    } catch (error) {
      toast.error('Profil güncellenemedi');
    }
  };

  // Generate report
  const generateReport = async (type = 'monthly') => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const response = await axios.get(`${API}/courier/report/${type}`, {
        withCredentials: true,
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `kurye-rapor-${type}-${new Date().toISOString().slice(0, 7)}.pdf`);
      
      // Safe DOM manipulation
      try {
        document.body.appendChild(link);
        link.click();
        
        // Use setTimeout for safe cleanup
        setTimeout(() => {
          try {
            if (link.parentNode) {
              link.remove();
            }
            window.URL.revokeObjectURL(url);
          } catch (removeError) {
            console.warn('Safe cleanup: link already removed');
          }
        }, 100);
      } catch (domError) {
        console.warn('DOM manipulation failed:', domError);
        window.URL.revokeObjectURL(url);
      }

      toast.success('Rapor indirildi');
    } catch (error) {
      toast.error('Rapor oluşturulamadı');
    }
  };

  // Request notification permission
  useEffect(() => {
    if (profile.notifications.push && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, [profile.notifications.push]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center py-12">
            <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Panel yükleniyor...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

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
                  {profile.firstName} {profile.lastName}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Online Status Toggle */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleOnlineStatus}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isOnline ? 'bg-green-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      isOnline ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`text-sm font-medium ${isOnline ? 'text-green-600' : 'text-gray-500'}`}>
                  {isOnline ? '🟢 Çevrimiçi' : '🔴 Çevrimdışı'}
                </span>
              </div>

              {/* Current Order Indicator */}
              {currentOrder && (
                <Badge className="bg-blue-600 animate-pulse">
                  📦 Aktif Sipariş
                </Badge>
              )}

              <Button onClick={onLogout} variant="outline" size="sm">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Current Order Status Bar */}
      {currentOrder && (
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Badge className="bg-white text-blue-600">
                  {currentOrder.status === 'accepted' ? 'Kabul Edildi' :
                   currentOrder.status === 'picked_up' ? 'Alındı' :
                   currentOrder.status === 'on_way' ? 'Yolda' : currentOrder.status}
                </Badge>
                <span className="font-medium">{currentOrder.business_name}</span>
                <span>→</span>
                <span>{currentOrder.customer_name}</span>
              </div>
              
              <div className="flex items-center space-x-2">
                {currentOrder.status === 'accepted' && (
                  <Button
                    onClick={() => updateOrderStatus(currentOrder.id, 'picked_up')}
                    className="bg-orange-600 hover:bg-orange-700"
                    size="sm"
                  >
                    📤 Aldım
                  </Button>
                )}
                {currentOrder.status === 'picked_up' && (
                  <Button
                    onClick={() => updateOrderStatus(currentOrder.id, 'on_way')}
                    className="bg-yellow-600 hover:bg-yellow-700"
                    size="sm"
                  >
                    🚗 Yoldayım
                  </Button>
                )}
                {currentOrder.status === 'on_way' && (
                  <Button
                    onClick={() => updateOrderStatus(currentOrder.id, 'delivered')}
                    className="bg-green-600 hover:bg-green-700"
                    size="sm"
                  >
                    ✅ Teslim Ettim
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Clean Side Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-1 mb-6">
          <div className="flex space-x-1 overflow-x-auto">
              <button
                onClick={() => setActiveTab('orders')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'orders' 
                    ? 'bg-blue-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-blue-500 hover:bg-blue-50'
                }`}
              >
                <span className="text-lg">📋</span>
                <span>Siparişler</span>
                {nearbyOrders.length > 0 && (
                  <span className={`min-w-[20px] h-5 flex items-center justify-center text-xs px-1.5 rounded-full font-bold ${
                    activeTab === 'orders' ? 'bg-white/20 text-white' : 'bg-red-500 text-white'
                  }`}>
                    {nearbyOrders.length}
                  </span>
                )}
              </button>
              
              <button
                onClick={() => setActiveTab('history')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'history' 
                    ? 'bg-green-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-green-500 hover:bg-green-50'
                }`}
              >
                <span className="text-lg">📚</span>
                <span>Geçmiş</span>
              </button>
              
              <button
                onClick={() => setActiveTab('earnings')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'earnings' 
                    ? 'bg-purple-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-purple-500 hover:bg-purple-50'
                }`}
              >
                <span className="text-lg">💰</span>
                <span>Kazanç</span>
              </button>
              
              <button
                onClick={() => setActiveTab('profile')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'profile' 
                    ? 'bg-gray-600 text-white shadow-md' 
                    : 'text-gray-600 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className="text-lg">👤</span>
                <span>Profil</span>
              </button>
              
              <button
                onClick={() => setActiveTab('ready_map')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'ready_map' 
                    ? 'bg-orange-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-orange-500 hover:bg-orange-50'
                }`}
              >
                <span className="text-lg">🗺️</span>
                <span>Hazır Siparişler</span>
              </button>
              
              <button
                onClick={() => setActiveTab('pdf_reports')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'pdf_reports' 
                    ? 'bg-red-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-red-500 hover:bg-red-50'
                }`}
              >
                <span className="text-lg">📄</span>
                <span>PDF Rapor</span>
              </button>
              
              <button
                onClick={() => setActiveTab('availability')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'availability' 
                    ? 'bg-teal-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-teal-500 hover:bg-teal-50'
                }`}
              >
                <span className="text-lg">📅</span>
                <span>Müsaitlik</span>
              </button>
              
              <button
                onClick={() => setActiveTab('history_filtered')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'history_filtered' 
                    ? 'bg-indigo-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-indigo-500 hover:bg-indigo-50'
                }`}
              >
                <span className="text-lg">🔍</span>
                <span>Detaylı Geçmiş</span>
              </button>
              
              <button
                onClick={() => setActiveTab('profile_update')}
                className={`flex items-center space-x-2 px-4 py-3 rounded-md transition-all duration-200 text-sm font-medium whitespace-nowrap ${
                  activeTab === 'profile_update' 
                    ? 'bg-pink-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-pink-500 hover:bg-pink-50'
                }`}
              >
                <span className="text-lg">✏️</span>
                <span>Profil Güncelle</span>
              </button>
            </div>
          </div>

          {/* Orders Content */}
          <div style={{ display: activeTab === 'orders' ? 'block' : 'none' }}>
            <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">🚚 Sipariş Yönetimi</h2>
              <div className="flex space-x-2">
                <Button onClick={fetchNearbyOrders} variant="outline" size="sm">
                  🔄 Yenile
                </Button>
              </div>
            </div>

            {/* Location Status */}
            <Card className={courierLocation ? "border-green-200 bg-green-50" : "border-yellow-200 bg-yellow-50"}>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <div className={courierLocation ? "text-green-600" : "text-yellow-600"}>📍</div>
                  <div className="flex-1">
                    <p className={`font-semibold ${courierLocation ? "text-green-800" : "text-yellow-800"}`}>
                      Konum: {courierLocation ? "AKTİF" : "KAPALI"}
                    </p>
                    {courierLocation ? (
                      <div className="text-green-700 text-sm">
                        <p>Lat: {courierLocation.lat?.toFixed(6)}, Lng: {courierLocation.lng?.toFixed(6)}</p>
                        {courierLocation.accuracy && (
                          <p>Hassasiyet: {courierLocation.accuracy.toFixed(0)}m</p>
                        )}
                      </div>
                    ) : locationError ? (
                      <div>
                        <p className="text-yellow-700 mb-2">{locationError}</p>
                        <Button
                          onClick={() => startLocationTracking()}
                          className="bg-yellow-600 hover:bg-yellow-700"
                          size="sm"
                        >
                          🔄 Konumu Tekrar Dene
                        </Button>
                      </div>
                    ) : (
                      <p className="text-yellow-600">Konum alınıyor...</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Interactive Map with Orders */}
            {courierLocation && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Map Section */}
                <Card>
                  <CardContent className="p-0">
                    <OpenStreetMap
                      center={courierLocation ? [courierLocation.lat, courierLocation.lng] : [41.0082, 28.9784]}
                      zoom={13}
                      height="400px"
                      courierLocation={courierLocation}
                      markers={nearbyOrders.map(order => ({
                        id: order.id,
                        title: `Sipariş #${order.id.slice(-8)}`,
                        type: 'delivery',
                        lat: order.delivery_lat || 41.0082,
                        lng: order.delivery_lng || 28.9784,
                        address: order.delivery_address
                      }))}
                      onMarkerClick={(markerId) => {
                        const order = nearbyOrders.find(o => o.id === markerId);
                        if (order) {
                          toast.success(`📦 Sipariş #${order.id.slice(-8)} - ${order.delivery_address}`);
                        }
                      }}
                    />
                  </CardContent>
                </Card>

                {/* Route Info Panel */}
                {nearbyOrders.length > 0 && courierLocation && (
                  <Card className="border-blue-200 bg-blue-50">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-semibold text-blue-800 flex items-center">
                            <span className="mr-2">🛣️</span>
                            Aktif Rotalar
                          </h3>
                          <p className="text-blue-600 text-sm">
                            {nearbyOrders.length} teslimat noktası • Optimize edilmiş rota
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-blue-700">
                            <div>📍 Toplam mesafe: ~{(nearbyOrders.length * 2.5).toFixed(1)} km</div>
                            <div>⏱️ Tahmini süre: ~{nearbyOrders.length * 12} dk</div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-3 flex items-center space-x-2">
                        <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                        <span className="text-xs text-blue-700">Gerçek zamanlı rota güncellemesi aktif</span>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Orders Control Panel */}
                <div className="space-y-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg flex items-center">
                        <span className="mr-2">🎯</span>
                        Sipariş Kontrol Paneli
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">{nearbyOrders.length}</div>
                          <div className="text-sm text-gray-600">Mevcut Sipariş</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">{currentOrder ? 1 : 0}</div>
                          <div className="text-sm text-gray-600">Aktif Teslimat</div>
                        </div>
                        <div className="text-center">
                          <div className={`text-2xl font-bold ${isOnline ? 'text-green-600' : 'text-gray-400'}`}>
                            {isOnline ? 'Çevrimiçi' : 'Çevrimdışı'}
                          </div>
                          <div className="text-sm text-gray-600">Durum</div>
                        </div>
                      </div>
                      
                      {currentOrder && (
                        <div className="bg-blue-50 p-3 rounded-lg mb-4">
                          <h4 className="font-semibold text-blue-800 mb-2">
                            📦 Aktif Teslimat: {currentOrder.business_name}
                          </h4>
                          <p className="text-sm text-blue-700 mb-2">
                            👤 Müşteri: {currentOrder.customer_name}
                          </p>
                          <div className="flex space-x-2">
                            {currentOrder.status === 'accepted' && (
                              <Button
                                onClick={() => updateOrderStatus(currentOrder.id, 'picked_up')}
                                className="bg-orange-600 hover:bg-orange-700"
                                size="sm"
                              >
                                📤 Teslim Aldım
                              </Button>
                            )}
                            {currentOrder.status === 'picked_up' && (
                              <Button
                                onClick={() => updateOrderStatus(currentOrder.id, 'on_way')}
                                className="bg-yellow-600 hover:bg-yellow-700"
                                size="sm"
                              >
                                🚗 Yola Çıktım
                              </Button>
                            )}
                            {currentOrder.status === 'on_way' && (
                              <Button
                                onClick={() => updateOrderStatus(currentOrder.id, 'delivered')}
                                className="bg-green-600 hover:bg-green-700"
                                size="sm"
                              >
                                ✅ Teslim Ettim
                              </Button>
                            )}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Quick Actions */}
                  <Card>
                    <CardContent className="p-4">
                      <h4 className="font-semibold mb-3">🚀 Hızlı İşlemler</h4>
                      <div className="space-y-2">
                        <Button
                          onClick={() => setActiveTab('history')}
                          variant="outline"
                          className="w-full justify-start"
                        >
                          📚 Teslimat Geçmişi
                        </Button>
                        <Button
                          onClick={() => setActiveTab('earnings')}
                          variant="outline"
                          className="w-full justify-start"
                        >
                          💰 Kazanç Raporu
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}

            {/* Orders List with Map Integration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  📋 Mevcut Siparişler ({nearbyOrders.length} adet)
                </CardTitle>
              </CardHeader>
              <CardContent>
                {nearbyOrders.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-6xl mb-4">📦</div>
                    <p className="text-xl font-semibold mb-2">Şu anda müsait sipariş yok</p>
                    <p className="text-gray-600">Yeni siparişler geldiğinde haritada gösterilecek</p>
                    {courierLocation && isOnline && (
                      <p className="text-xs text-blue-600 mt-2">
                        📍 Konumunuz aktif • Yakın siparişler için bildirim alacaksınız
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {nearbyOrders.map((order) => {
                      const isVeryClose = courierLocation && order.pickup_address &&
                        calculateDistance(
                          courierLocation.lat, courierLocation.lng,
                          order.pickup_address.lat, order.pickup_address.lng
                        ) <= 1;

                      return (
                        <Card
                          key={order.id}
                          className={`hover:shadow-lg transition-all duration-300 cursor-pointer ${
                            isVeryClose ? 'border-green-400 bg-green-50' : 'border-gray-200'
                          }`}
                        >
                          <CardContent className="p-4">
                            {isVeryClose && (
                              <div className="mb-3 p-2 bg-green-100 border border-green-300 rounded-lg">
                                <p className="text-sm font-semibold text-green-800 flex items-center">
                                  🎯 Çok Yakın Sipariş - 1km İçinde!
                                </p>
                              </div>
                            )}

                            <div className="flex justify-between items-start mb-3">
                              <div>
                                <h3 className="font-semibold text-lg flex items-center gap-2">
                                  🏪 {order.business_name}
                                  {order.priority === 'high' && (
                                    <Badge className="bg-red-500 text-white text-xs">🔥 Yüksek Ücret</Badge>
                                  )}
                                </h3>
                                <p className="text-sm text-gray-600">📍 {order.pickup_address?.address}</p>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-green-600 text-lg">₺{order.total_amount}</p>
                                <p className="text-sm text-purple-600 font-medium">
                                  +₺{(order.total_amount * 0.05).toFixed(2)} komisyon
                                </p>
                              </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                              <div>
                                <span className="font-medium">📍 Mesafe:</span>
                                <span className={isVeryClose ? 'text-green-600 font-bold ml-1' : 'ml-1'}>
                                  {courierLocation && order.pickup_address ?
                                    `${calculateDistance(
                                      courierLocation.lat, courierLocation.lng,
                                      order.pickup_address.lat, order.pickup_address.lng
                                    ).toFixed(1)} km` :
                                    <span className="text-orange-600">Konum bekleniyor...</span>}
                                </span>
                              </div>
                              <div>
                                <span className="font-medium">👤 Müşteri:</span>
                                <span className="ml-1">{order.customer_name || 'Müşteri'}</span>
                              </div>
                            </div>

                            <div className="mb-3 p-2 bg-gray-50 rounded">
                              <p className="text-sm">
                                <strong>🏠 Teslimat:</strong> {order.delivery_address?.address || 'Teslimat adresi'}
                              </p>
                            </div>

                            <div className="flex gap-2">
                              <Button
                                onClick={() => acceptOrder(order.id)}
                                disabled={!isOnline}
                                className={`flex-1 ${
                                  isVeryClose ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'
                                }`}
                              >
                                {isVeryClose ? '🎯 Hemen Kabul Et!' : '✅ Kabul Et'}
                              </Button>
                              <Button
                                variant="outline"
                                className="px-3"
                                onClick={() => {
                                  if (order.pickup_address?.lat && order.pickup_address?.lng) {
                                    const mapsUrl = `https://www.google.com/maps/dir/${courierLocation?.lat || 41.0082},${courierLocation?.lng || 28.9784}/${order.pickup_address.lat},${order.pickup_address.lng}`;
                                    window.open(mapsUrl, '_blank');
                                  }
                                }}
                              >
                                🗺️ Yol Tarifi
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Online Status Warning */}
            {!isOnline && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2">
                    <div className="text-red-600">🔴</div>
                    <div>
                      <p className="font-semibold text-red-800">Çevrimdışısınız</p>
                      <p className="text-red-600">Sipariş alabilmek için çevrimiçi olmalısınız.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Orders List */}
            {nearbyOrders.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <div className="text-6xl mb-4">📦</div>
                  <p className="text-xl font-semibold mb-2">Şu anda müsait sipariş yok</p>
                  <p className="text-gray-600">Yeni siparişler geldiğinde burada gösterilecek</p>
                  {courierLocation && isOnline && (
                    <p className="text-xs text-blue-600 mt-2">
                      📍 Konumunuz aktif • Yakın siparişler için bildirim alacaksınız
                    </p>
                  )}
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {/* Notification Status */}
                {courierLocation && isOnline && (
                  <Card className="border-blue-200 bg-blue-50">
                    <CardContent className="p-4">
                      <div className="flex items-center space-x-2">
                        <div className="text-blue-600">🔔</div>
                        <div>
                          <p className="font-semibold text-blue-800">Bildirim Sistemi Aktif</p>
                          <p className="text-blue-600">1km yakınınızdaki siparişler için bildirim alacaksınız</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Orders */}
                {nearbyOrders.map((order) => {
                  const isVeryClose = courierLocation && order.pickup_address &&
                    calculateDistance(
                      courierLocation.lat, courierLocation.lng,
                      order.pickup_address.lat, order.pickup_address.lng
                    ) <= 1;

                  return (
                    <Card
                      key={order.id}
                      className={`hover:shadow-lg transition-shadow ${isVeryClose ? 'border-green-400 bg-green-50' : ''}`}
                    >
                      <CardContent className="p-4">
                        {isVeryClose && (
                          <div className="mb-3 p-2 bg-green-100 border border-green-300 rounded-lg">
                            <p className="text-sm font-semibold text-green-800 flex items-center">
                              🎯 Çok Yakın Sipariş - 1km İçinde!
                            </p>
                          </div>
                        )}

                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                              {order.business_name}
                              {order.priority === 'high' && (
                                <Badge className="bg-red-500 text-white text-xs">🔥 Yüksek Ücret</Badge>
                              )}
                            </h3>
                            <p className="text-sm text-gray-600">{order.pickup_address?.address}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-green-600 text-lg">₺{order.total_amount}</p>
                            <p className="text-sm text-purple-600 font-medium">
                              +₺{(order.total_amount * 0.05).toFixed(2)} komisyon
                            </p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                          <div>
                            <span className="font-medium">📍 Mesafe:</span>
                            <span className={isVeryClose ? 'text-green-600 font-bold ml-1' : 'ml-1'}>
                              {courierLocation && order.pickup_address ?
                                `${calculateDistance(
                                  courierLocation.lat, courierLocation.lng,
                                  order.pickup_address.lat, order.pickup_address.lng
                                ).toFixed(1)} km` :
                                <span className="text-orange-600">Konum bekleniyor...</span>}
                            </span>
                          </div>
                          <div>
                            <span className="font-medium">⏱️ Hazırlık:</span>
                            <span className="ml-1">{order.preparation_time || '15'} dk</span>
                          </div>
                          <div>
                            <span className="font-medium">📦 Ürünler:</span>
                            <span className="ml-1">{order.items?.length || 1} adet</span>
                          </div>
                          <div>
                            <span className="font-medium">👤 Müşteri:</span>
                            <span className="ml-1">{order.customer_name || 'Müşteri'}</span>
                          </div>
                        </div>

                        <div className="mb-3 p-2 bg-gray-50 rounded">
                          <p className="text-sm">
                            <strong>📍 Teslimat:</strong> {order.delivery_address?.address || 'Teslimat adresi'}
                          </p>
                        </div>

                        <div className="flex gap-2">
                          <Button
                            onClick={() => acceptOrder(order.id)}
                            disabled={!isOnline}
                            className={`flex-1 ${isVeryClose ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                          >
                            {isVeryClose ? '🎯 Hemen Kabul Et!' : '✅ Siparişi Kabul Et'}
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => {
                              if (order.delivery_address?.lat && order.delivery_address?.lng) {
                                const mapsUrl = `https://www.google.com/maps/dir/${courierLocation?.lat || 41.0082},${courierLocation?.lng || 28.9784}/${order.delivery_address.lat},${order.delivery_address.lng}`;
                                window.open(mapsUrl, '_blank');
                              }
                            }}
                          >
                            🗺️ Rota
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
            </div>
          </div>

          {/* History Content */}
          <div style={{ display: activeTab === 'history' ? 'block' : 'none' }}>
            <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">Sipariş Geçmişi</h2>
              
              <div className="flex space-x-2">
                <select 
                  value={historyFilter.status} 
                  onChange={(e) => setHistoryFilter(prev => ({ ...prev, status: e.target.value }))}
                  className="w-40 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">Tüm Durumlar</option>
                  <option value="delivered">Teslim Edildi</option>
                  <option value="cancelled">İptal Edildi</option>
                  <option value="on_way">Yolda</option>
                </select>
                
                <select 
                  value={historyFilter.dateRange} 
                  onChange={(e) => setHistoryFilter(prev => ({ ...prev, dateRange: e.target.value }))}
                  className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">Tüm Zamanlar</option>
                  <option value="today">Bugün</option>
                  <option value="week">Bu Hafta</option>
                  <option value="month">Bu Ay</option>
                </select>
                
                <Button onClick={fetchOrderHistory} variant="outline" size="sm">
                  🔍 Filtrele
                </Button>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-blue-600">{stats.totalOrders}</p>
                  <p className="text-sm text-gray-600">Toplam Sipariş</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-green-600">{stats.completedOrders}</p>
                  <p className="text-sm text-gray-600">Teslim Edildi</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <p className="text-2xl font-bold text-orange-600">{stats.avgDeliveryTime}</p>
                  <p className="text-sm text-gray-600">Ort. Teslimat (dk)</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="flex items-center justify-center space-x-1">
                    <p className="text-2xl font-bold text-yellow-600">{stats.rating}</p>
                    <span className="text-yellow-500">⭐</span>
                  </div>
                  <p className="text-sm text-gray-600">Değerlendirme</p>
                </CardContent>
              </Card>
            </div>

            {/* Order History List */}
            <div className="space-y-3">
              {orderHistory.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-8">
                    <p className="text-gray-500">Sipariş geçmişi bulunamadı</p>
                  </CardContent>
                </Card>
              ) : (
                orderHistory.map((order) => (
                  <Card key={order.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="font-medium">{order.business_name}</h3>
                            <Badge variant={
                              order.status === 'delivered' ? 'default' :
                              order.status === 'cancelled' ? 'destructive' :
                              'secondary'
                            }>
                              {order.status === 'delivered' ? '✅ Teslim Edildi' :
                               order.status === 'cancelled' ? '❌ İptal Edildi' :
                               order.status === 'on_way' ? '🚗 Yolda' : order.status}
                            </Badge>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-1">
                            📅 {new Date(order.created_at).toLocaleDateString('tr-TR')} • 
                            🕐 {new Date(order.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                          
                          <p className="text-sm text-gray-600">
                            📍 {order.pickup_address?.address} → {order.delivery_address?.address}
                          </p>
                        </div>
                        
                        <div className="text-right">
                          <p className="font-bold text-green-600">₺{order.total_amount}</p>
                          <p className="text-sm text-purple-600">
                            +₺{(order.commission_amount || order.total_amount * 0.05).toFixed(2)}
                          </p>
                          {order.delivery_time && (
                            <p className="text-xs text-gray-500">
                              ⏱️ {order.delivery_time} dk
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
            </div>
          </div>

          {/* Earnings Content */}
          <div style={{ display: activeTab === 'earnings' ? 'block' : 'none' }}>
            <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">Kazanç Raporu</h2>
              
              <div className="flex space-x-2">
                <Button onClick={() => generateReport('daily')} variant="outline" size="sm">
                  📄 Günlük Rapor
                </Button>
                <Button onClick={() => generateReport('weekly')} variant="outline" size="sm">
                  📄 Haftalık Rapor
                </Button>
                <Button onClick={() => generateReport('monthly')} variant="outline" size="sm">
                  📄 Aylık Rapor
                </Button>
              </div>
            </div>

            {/* Earnings Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{earnings.daily.toFixed(2)}</p>
                  <p className="text-green-100">Bugün</p>
                  <p className="text-xs text-green-200 mt-1">
                    Net kazanç (%5 komisyon sonrası)
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{earnings.weekly.toFixed(2)}</p>
                  <p className="text-blue-100">Bu Hafta</p>
                  <p className="text-xs text-blue-200 mt-1">
                    7 günlük toplam
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{earnings.monthly.toFixed(2)}</p>
                  <p className="text-purple-100">Bu Ay</p>
                  <p className="text-xs text-purple-200 mt-1">
                    30 günlük toplam
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{earnings.total.toFixed(2)}</p>
                  <p className="text-orange-100">Toplam</p>
                  <p className="text-xs text-orange-200 mt-1">
                    Tüm zamanlar
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Earnings Info */}
            <Card>
              <CardHeader>
                <CardTitle>Komisyon Bilgileri</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Komisyon Oranı:</span>
                      <span className="font-medium text-green-600">%5</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Minimum Sipariş Ücreti:</span>
                      <span className="font-medium">₺10</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Ödeme Sıklığı:</span>
                      <span className="font-medium">Haftalık</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Ödeme Günü:</span>
                      <span className="font-medium">Pazartesi</span>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span>Toplam Mesafe:</span>
                      <span className="font-medium">{stats.totalDistance} km</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Km Başına Kazanç:</span>
                      <span className="font-medium text-green-600">
                        ₺{stats.totalDistance > 0 ? (earnings.total / stats.totalDistance).toFixed(2) : '0.00'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Sipariş Başına Ort.:</span>
                      <span className="font-medium text-green-600">
                        ₺{stats.completedOrders > 0 ? (earnings.total / stats.completedOrders).toFixed(2) : '0.00'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>En Yüksek Günlük:</span>
                      <span className="font-medium text-orange-600">₺{earnings.daily.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            </div>
          </div>

          {/* Profile Content */}
          <div style={{ display: activeTab === 'profile' ? 'block' : 'none' }}>
            <div className="space-y-6">
            <h2 className="text-xl font-bold">Profil & Ayarlar</h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Personal Information */}
              <Card>
                <CardHeader>
                  <CardTitle>Kişisel Bilgiler</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="firstName">Ad</Label>
                      <Input
                        id="firstName"
                        value={profile.firstName}
                        onChange={(e) => setProfile(prev => ({ ...prev, firstName: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="lastName">Soyad</Label>
                      <Input
                        id="lastName"
                        value={profile.lastName}
                        onChange={(e) => setProfile(prev => ({ ...prev, lastName: e.target.value }))}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="phone">Telefon</Label>
                    <Input
                      id="phone"
                      value={profile.phone}
                      onChange={(e) => setProfile(prev => ({ ...prev, phone: e.target.value }))}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="email">E-posta</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profile.email}
                      onChange={(e) => setProfile(prev => ({ ...prev, email: e.target.value }))}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="iban">IBAN</Label>
                    <Input
                      id="iban"
                      placeholder="TR00 0000 0000 0000 0000 0000 00"
                      value={profile.iban}
                      onChange={(e) => setProfile(prev => ({ ...prev, iban: e.target.value }))}
                    />
                  </div>
                  
                  <Button onClick={updateProfile} className="w-full">
                    💾 Profili Güncelle
                  </Button>
                </CardContent>
              </Card>

              {/* Working Hours */}
              <Card>
                <CardHeader>
                  <CardTitle>Çalışma Saatleri</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="workStart">Başlangıç Saati</Label>
                      <Input
                        id="workStart"
                        type="time"
                        value={profile.workingHours.start}
                        onChange={(e) => setProfile(prev => ({
                          ...prev,
                          workingHours: { ...prev.workingHours, start: e.target.value }
                        }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="workEnd">Bitiş Saati</Label>
                      <Input
                        id="workEnd"
                        type="time"
                        value={profile.workingHours.end}
                        onChange={(e) => setProfile(prev => ({
                          ...prev,
                          workingHours: { ...prev.workingHours, end: e.target.value }
                        }))}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label>Çalışma Günleri</Label>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {[
                        { key: 'monday', label: 'Pazartesi' },
                        { key: 'tuesday', label: 'Salı' },
                        { key: 'wednesday', label: 'Çarşamba' },
                        { key: 'thursday', label: 'Perşembe' },
                        { key: 'friday', label: 'Cuma' },
                        { key: 'saturday', label: 'Cumartesi' },
                        { key: 'sunday', label: 'Pazar' }
                      ].map((day) => (
                        <div key={day.key} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={profile.workingHours.workDays.includes(day.key)}
                            onChange={(e) => {
                              const checked = e.target.checked;
                              setProfile(prev => ({
                                ...prev,
                                workingHours: {
                                  ...prev.workingHours,
                                  workDays: checked
                                    ? [...prev.workingHours.workDays, day.key]
                                    : prev.workingHours.workDays.filter(d => d !== day.key)
                                }
                              }));
                            }}
                            className="rounded border-gray-300"
                          />
                          <span className="text-sm">{day.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Notification Settings */}
              <Card>
                <CardHeader>
                  <CardTitle>Bildirim Ayarları</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Ses Bildirimleri</Label>
                      <p className="text-sm text-gray-600">Yakın siparişler için ses çal</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={profile.notifications.sound}
                      onChange={(e) => setProfile(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, sound: e.target.checked }
                      }))}
                      className="rounded border-gray-300"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Push Bildirimleri</Label>
                      <p className="text-sm text-gray-600">Tarayıcı bildirimleri</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={profile.notifications.push}
                      onChange={(e) => setProfile(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, push: e.target.checked }
                      }))}
                      className="rounded border-gray-300"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>E-posta Bildirimleri</Label>
                      <p className="text-sm text-gray-600">Önemli güncellemeler</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={profile.notifications.email}
                      onChange={(e) => setProfile(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, email: e.target.checked }
                      }))}
                      className="rounded border-gray-300"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Account Stats */}
              <Card>
                <CardHeader>
                  <CardTitle>Hesap İstatistikleri</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span>Toplam Teslimat:</span>
                    <span className="font-bold text-blue-600">{stats.completedOrders}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Toplam Mesafe:</span>
                    <span className="font-bold text-green-600">{stats.totalDistance} km</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Ortalama Değerlendirme:</span>
                    <div className="flex items-center space-x-1">
                      <span className="font-bold text-yellow-600">{stats.rating}</span>
                      <span className="text-yellow-500">⭐</span>
                    </div>
                  </div>
                  <div className="flex justify-between">
                    <span>Başarı Oranı:</span>
                    <span className="font-bold text-green-600">
                      {stats.totalOrders > 0 ? ((stats.completedOrders / stats.totalOrders) * 100).toFixed(1) : 0}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Üyelik Tarihi:</span>
                    <span className="font-medium">{new Date(user?.created_at || Date.now()).toLocaleDateString('tr-TR')}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
            </div>
          </div>

          {/* Order History Tab */}
          <div style={{ display: activeTab === 'history' ? 'block' : 'none' }}>
            <div className="p-6">
              <CourierOrderHistory />
            </div>
          </div>

          {/* Earnings Report Tab */}
          <div style={{ display: activeTab === 'earnings' ? 'block' : 'none' }}>
            <div className="p-6">
              <CourierEarningsReport />
            </div>
          </div>

          {/* Ready Orders Map Tab - Phase 1 */}
          <div style={{ display: activeTab === 'ready_map' ? 'block' : 'none' }}>
            <React.Fragment>
              <div className="p-6">
                <CourierReadyOrdersMap />
              </div>
            </React.Fragment>
          </div>

          {/* PDF Reports Tab - Phase 1 */}
          <div style={{ display: activeTab === 'pdf_reports' ? 'block' : 'none' }}>
            <React.Fragment>
              <div className="p-6">
                <CourierPDFReports />
              </div>
            </React.Fragment>
          </div>

          {/* Availability Tab - Phase 1 */}
          <div style={{ display: activeTab === 'availability' ? 'block' : 'none' }}>
            <React.Fragment>
              <div className="p-6">
                <CourierAvailability />
              </div>
            </React.Fragment>
          </div>

          {/* Filtered History Tab - Phase 1 */}
          <div style={{ display: activeTab === 'history_filtered' ? 'block' : 'none' }}>
            <React.Fragment>
              <div className="p-6">
                <CourierOrderHistoryFiltered />
              </div>
            </React.Fragment>
          </div>

          {/* Profile Update Tab - Phase 1 */}
          <div style={{ display: activeTab === 'profile_update' ? 'block' : 'none' }}>
            <React.Fragment>
              <div className="p-6">
                <CourierProfileUpdate user={user} />
              </div>
            </React.Fragment>
          </div>
      </div>
    </div>
  );
};

export default React.memo(CourierDashboard);