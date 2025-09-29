import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Original CourierDashboard from GitHub (NearbyOrdersForCourier)
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
      const token = localStorage.getItem('kuryecini_access_token');
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
      const token = localStorage.getItem('kuryecini_access_token'); // Fixed token key
      await axios.post(`${API}/orders/${orderId}/accept`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Sipariş kabul edildi!');
      fetchNearbyOrders(); // Refresh list
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sipariş kabul edilemedi');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center py-12">
            <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">
              {courierLocation ? 'Siparişler yükleniyor...' : 'Konum alınıyor...'}
            </p>
            {locationError && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-600 text-sm">⚠️ {locationError}</p>
                <Button
                  onClick={startLocationTracking}
                  className="mt-2 bg-red-600 hover:bg-red-700"
                  size="sm"
                >
                  🔄 Konumu Tekrar Dene
                </Button>
              </div>
            )}
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
                  {user?.first_name} {user?.last_name}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button onClick={onLogout} variant="outline" size="sm">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">Yakındaki Siparişler</h2>
            <Button onClick={fetchNearbyOrders} variant="outline" size="sm">
              🔄 Yenile
            </Button>
          </div>

          {/* Location Status Card */}
          {!courierLocation && (
            <Card className="border-yellow-200 bg-yellow-50">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <div className="text-yellow-600">📍</div>
                  <div className="text-sm">
                    <p className="font-semibold text-yellow-800">Konum Durumu</p>
                    {locationError ? (
                      <div>
                        <p className="text-yellow-700 mb-2">{locationError}</p>
                        <Button
                          onClick={startLocationTracking}
                          className="bg-yellow-600 hover:bg-yellow-700"
                          size="sm"
                        >
                          🔄 Konumu Tekrar Dene
                        </Button>
                      </div>
                    ) : (
                      <p className="text-yellow-600">Konum alınıyor... Mesafe hesaplaması için gerekli.</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {nearbyOrders.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <div className="text-6xl mb-4">📦</div>
                <p className="text-xl font-semibold mb-2">Şu anda müsait sipariş yok</p>
                <p className="text-gray-600">Yeni siparişler geldiğinde burada gösterilecek</p>
                {courierLocation && (
                  <p className="text-xs text-blue-600 mt-2">
                    📍 Konumunuz aktif • Yakın siparişler için bildirim alacaksınız
                  </p>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {courierLocation && (
                <Card className="border-blue-200 bg-blue-50">
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2">
                      <div className="text-blue-600">🔔</div>
                      <div className="text-sm">
                        <p className="font-semibold text-blue-800">Bildirim Sistemi Aktif</p>
                        <p className="text-blue-600">1km yakınınızdaki siparişler için sesli bildirim alacaksınız</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {nearbyOrders.map((order) => {
                // Calculate if order is very close only if we have courier location
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
                      {isVeryClose && courierLocation && (
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
                          <p className="text-sm text-purple-600 font-medium">+₺{order.commission_amount?.toFixed(2)} komisyon</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                        <div>
                          <span className="font-medium">📍 Mesafe:</span>
                          <span className={isVeryClose ? 'text-green-600 font-bold' : ''}>
                            {courierLocation && order.pickup_address ?
                              `${calculateDistance(courierLocation.lat, courierLocation.lng, order.pickup_address.lat, order.pickup_address.lng).toFixed(1)} km` :
                              <span className="text-orange-600">Konum bekleniyor...</span>}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">⏱️ Hazırlık:</span> {order.preparation_time}
                        </div>
                        <div>
                          <span className="font-medium">📦 Ürünler:</span> {order.items?.length || 0} adet
                        </div>
                        <div>
                          <span className="font-medium">👤 Müşteri:</span> {order.customer_name}
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
                          className={`flex-1 ${isVeryClose && courierLocation ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                        >
                          {isVeryClose && courierLocation ? '🎯 Hemen Kabul Et!' : '✅ Siparişi Kabul Et'}
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
                          🗺️ Müşteriye Git
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
    </div>
  );
};

export default CourierDashboard;