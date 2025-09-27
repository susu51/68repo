import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Textarea } from './components/ui/textarea';
import { Label } from './components/ui/label';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Order Status Badge Component
export const OrderStatusBadge = ({ status }) => {
  const statusConfig = {
    pending: { color: "bg-yellow-100 text-yellow-800", text: "Beklemede", icon: "⏳" },
    confirmed: { color: "bg-blue-100 text-blue-800", text: "Onaylandı", icon: "✅" },
    preparing: { color: "bg-orange-100 text-orange-800", text: "Hazırlanıyor", icon: "👨‍🍳" },
    ready: { color: "bg-green-100 text-green-800", text: "Hazır", icon: "📦" },
    picked_up: { color: "bg-purple-100 text-purple-800", text: "Alındı", icon: "🚗" },
    delivering: { color: "bg-indigo-100 text-indigo-800", text: "Yolda", icon: "🛣️" },
    delivered: { color: "bg-green-100 text-green-800", text: "Teslim Edildi", icon: "✨" },
    cancelled: { color: "bg-red-100 text-red-800", text: "İptal Edildi", icon: "❌" }
  };

  const config = statusConfig[status] || statusConfig.pending;
  
  return (
    <Badge className={config.color} data-testid={`status-${status}`}>
      {config.icon} {config.text}
    </Badge>
  );
};

// Create Order Component
export const CreateOrderForm = ({ businessId, onOrderCreated, onCancel }) => {
  const [orderItems, setOrderItems] = useState([
    { id: '1', name: '', quantity: 1, unit_price: 0, total_price: 0, notes: '' }
  ]);
  const [deliveryLocation, setDeliveryLocation] = useState(null);
  const [orderNotes, setOrderNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const addItem = () => {
    const newItem = {
      id: Date.now().toString(),
      name: '',
      quantity: 1,
      unit_price: 0,
      total_price: 0,
      notes: ''
    };
    setOrderItems([...orderItems, newItem]);
  };

  const updateItem = (itemId, field, value) => {
    setOrderItems(items => items.map(item => {
      if (item.id === itemId) {
        const updated = { ...item, [field]: value };
        if (field === 'quantity' || field === 'unit_price') {
          updated.total_price = updated.quantity * updated.unit_price;
        }
        return updated;
      }
      return item;
    }));
  };

  const removeItem = (itemId) => {
    setOrderItems(items => items.filter(item => item.id !== itemId));
  };

  const calculateSubtotal = () => {
    return orderItems.reduce((sum, item) => sum + item.total_price, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!deliveryLocation) {
      toast.error('Teslimat adresini seçiniz');
      return;
    }

    const validItems = orderItems.filter(item => item.name && item.quantity > 0 && item.unit_price > 0);
    if (validItems.length === 0) {
      toast.error('En az bir ürün ekleyiniz');
      return;
    }

    setLoading(true);
    try {
      const orderData = {
        business_id: businessId,
        items: validItems,
        delivery_address: {
          lat: deliveryLocation.lat,
          lon: deliveryLocation.lng,
          address: `${deliveryLocation.lat.toFixed(4)}, ${deliveryLocation.lng.toFixed(4)}`,
          city: "İstanbul" // Demo için
        },
        order_notes: orderNotes,
        delivery_fee: 15.0
      };

      const token = localStorage.getItem('delivertr_token');
      const response = await axios.post(`${API}/orders/create`, orderData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Sipariş başarıyla oluşturuldu!');
      if (onOrderCreated) {
        onOrderCreated(response.data.order_id);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sipariş oluşturulamadı');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Yeni Sipariş Oluştur</CardTitle>
        <CardDescription>Sipariş detaylarını doldurun</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Order Items */}
          <div>
            <Label className="text-base font-semibold">Sipariş Kalemleri</Label>
            <div className="space-y-3 mt-2">
              {orderItems.map((item, index) => (
                <div key={item.id} className="grid grid-cols-12 gap-2 p-3 border rounded-lg">
                  <div className="col-span-4">
                    <Input
                      placeholder="Ürün adı"
                      value={item.name}
                      onChange={(e) => updateItem(item.id, 'name', e.target.value)}
                      data-testid={`item-name-${index}`}
                    />
                  </div>
                  <div className="col-span-2">
                    <Input
                      type="number"
                      placeholder="Adet"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateItem(item.id, 'quantity', parseInt(e.target.value) || 0)}
                      data-testid={`item-quantity-${index}`}
                    />
                  </div>
                  <div className="col-span-2">
                    <Input
                      type="number"
                      placeholder="Birim fiyat"
                      min="0"
                      step="0.01"
                      value={item.unit_price}
                      onChange={(e) => updateItem(item.id, 'unit_price', parseFloat(e.target.value) || 0)}
                      data-testid={`item-price-${index}`}
                    />
                  </div>
                  <div className="col-span-2">
                    <Input
                      type="number"
                      placeholder="Toplam"
                      value={item.total_price.toFixed(2)}
                      readOnly
                      className="bg-gray-50"
                    />
                  </div>
                  <div className="col-span-2">
                    <Button
                      type="button"
                      onClick={() => removeItem(item.id)}
                      variant="destructive"
                      size="sm"
                      disabled={orderItems.length === 1}
                    >
                      Sil
                    </Button>
                  </div>
                </div>
              ))}
              
              <Button
                type="button"
                onClick={addItem}
                variant="outline"
                className="w-full"
                data-testid="add-item-btn"
              >
                + Ürün Ekle
              </Button>
            </div>
          </div>

          {/* Delivery Location */}
          <div>
            <Label className="text-base font-semibold">Teslimat Adresi</Label>
            <div className="mt-2">
              <Textarea
                value={deliveryLocation}
                onChange={(e) => setDeliveryLocation(e.target.value)}
                placeholder="Teslimat adresini tam olarak yazın"
                rows="3"
              />
            </div>
          </div>

          {/* Order Notes */}
          <div>
            <Label htmlFor="orderNotes">Sipariş Notları (Opsiyonel)</Label>
            <Textarea
              id="orderNotes"
              placeholder="Sipariş hakkında özel notlarınız..."
              value={orderNotes}
              onChange={(e) => setOrderNotes(e.target.value)}
              data-testid="order-notes"
            />
          </div>

          {/* Order Summary */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold mb-2">Sipariş Özeti</h3>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span>Ara Toplam:</span>
                <span>₺{calculateSubtotal().toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Teslimat Ücreti:</span>
                <span>₺15.00</span>
              </div>
              <div className="border-t pt-1 font-semibold flex justify-between">
                <span>Genel Toplam:</span>
                <span>₺{(calculateSubtotal() + 15).toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              type="submit"
              disabled={loading}
              className="flex-1 bg-green-600 hover:bg-green-700"
              data-testid="create-order-btn"
            >
              {loading ? 'Oluşturuluyor...' : 'Siparişi Oluştur'}
            </Button>
            <Button
              type="button"
              onClick={onCancel}
              variant="outline"
              className="flex-1"
            >
              İptal
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

// Order List Component
export const OrdersList = ({ userType, orders, onStatusUpdate, onOrderSelect }) => {
  const handleStatusUpdate = async (orderId, newStatus) => {
    try {
      const token = localStorage.getItem('delivertr_token');
      await axios.post(`${API}/orders/${orderId}/update-status?status=${newStatus}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Durum güncellendi');
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Durum güncellenemedi');
    }
  };

  const getAvailableActions = (order) => {
    const { status } = order;
    const actions = [];

    if (userType === 'business') {
      if (status === 'pending') actions.push({ key: 'confirmed', label: 'Onayla', color: 'bg-blue-600' });
      if (status === 'confirmed') actions.push({ key: 'preparing', label: 'Hazırlanıyor', color: 'bg-orange-600' });
      if (status === 'preparing') actions.push({ key: 'ready', label: 'Hazır', color: 'bg-green-600' });
      if (['pending', 'confirmed'].includes(status)) actions.push({ key: 'cancelled', label: 'İptal', color: 'bg-red-600' });
    }

    if (userType === 'courier') {
      if (status === 'ready') actions.push({ key: 'picked_up', label: 'Aldım', color: 'bg-purple-600' });
      if (status === 'picked_up') actions.push({ key: 'delivering', label: 'Yoldayım', color: 'bg-indigo-600' });
      if (status === 'delivering') actions.push({ key: 'delivered', label: 'Teslim Ettim', color: 'bg-green-600' });
    }

    if (userType === 'customer') {
      if (['pending', 'confirmed'].includes(status)) actions.push({ key: 'cancelled', label: 'İptal Et', color: 'bg-red-600' });
    }

    return actions;
  };

  if (orders.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <div className="text-4xl mb-4">📋</div>
          <p className="text-gray-500">Henüz sipariş bulunmuyor</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {orders.map((order) => (
        <Card key={order.id} className="hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex justify-between items-start mb-3">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold">Sipariş #{order.id.substring(0, 8)}</h3>
                  <OrderStatusBadge status={order.status} />
                </div>
                <p className="text-sm text-gray-600">
                  {new Date(order.created_at).toLocaleString('tr-TR')}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-lg">₺{order.total?.toFixed(2)}</p>
                <p className="text-sm text-gray-600">{order.items?.length} ürün</p>
              </div>
            </div>

            {/* Order Details */}
            <div className="space-y-2 text-sm">
              {userType !== 'business' && order.business_name && (
                <p><strong>İşletme:</strong> {order.business_name}</p>
              )}
              {userType !== 'customer' && order.customer_name && (
                <p><strong>Müşteri:</strong> {order.customer_name}</p>
              )}
              <p><strong>Teslimat Adresi:</strong> {order.delivery_location?.address}</p>
              {order.order_notes && (
                <p><strong>Notlar:</strong> {order.order_notes}</p>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-2 mt-4">
              {getAvailableActions(order).map((action) => (
                <Button
                  key={action.key}
                  onClick={() => handleStatusUpdate(order.id, action.key)}
                  className={`${action.color} hover:opacity-90`}
                  size="sm"
                  data-testid={`action-${action.key}-${order.id}`}
                >
                  {action.label}
                </Button>
              ))}
              
              <Button
                onClick={() => onOrderSelect && onOrderSelect(order)}
                variant="outline"
                size="sm"
              >
                Detaylar
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Courier Nearby Orders Component (City-wide with Notifications)
export const NearbyOrdersForCourier = () => {
  const [nearbyOrders, setNearbyOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [courierLocation, setCourierLocation] = useState(null);
  const [lastNotificationTime, setLastNotificationTime] = useState(0);

  useEffect(() => {
    fetchNearbyOrders();
    startLocationTracking();
    
    // Fetch orders every 30 seconds
    const ordersInterval = setInterval(fetchNearbyOrders, 30000);
    
    // Update location every 3 minutes 
    const locationInterval = setInterval(updateLocation, 180000); // 3 minutes = 180000ms
    
    return () => {
      clearInterval(ordersInterval);
      clearInterval(locationInterval);
    };
  }, []);

  const fetchNearbyOrders = async () => {
    try {
      const token = localStorage.getItem('delivertr_access_token');
      const response = await axios.get(`${API}/orders/nearby`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const orders = response.data || [];
      setNearbyOrders(orders);
      
      // Check for very close orders and send notifications
      if (courierLocation && orders.length > 0) {
        checkForCloseOrders(orders);
      }
      
    } catch (error) {
      console.error('Siparişler alınamadı:', error);
      setNearbyOrders([]);
    }
    setLoading(false);
  };

  const startLocationTracking = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setCourierLocation(location);
        },
        (error) => console.error('Konum alınamadı:', error),
        { enableHighAccuracy: true }
      );
    }
  };

  const updateLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const newLocation = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setCourierLocation(newLocation);
          
          // Recheck for close orders with new location
          if (nearbyOrders.length > 0) {
            checkForCloseOrders(nearbyOrders);
          }
        },
        (error) => console.error('Konum güncellenemedi:', error),
        { enableHighAccuracy: true }
      );
    }
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
      const token = localStorage.getItem('delivertr_access_token'); // Fixed token key
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
      <Card>
        <CardContent className="text-center py-12">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yakın siparişler yükleniyor...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">Yakındaki Siparişler</h2>
        <Button onClick={fetchNearbyOrders} variant="outline" size="sm">
          🔄 Yenile
        </Button>
      </div>

      {nearbyOrders.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-4xl mb-4">🏙️</div>
            <p className="text-gray-500">Şu anda şehir genelinde sipariş bulunamadı</p>
            <p className="text-sm text-gray-400 mt-2">Yeni siparişler her 30 saniyede güncellenir</p>
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
            // Calculate if order is very close (demo distance calculation)
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
                      <p className="text-sm text-purple-600 font-medium">+₺{order.commission_amount?.toFixed(2)} komisyon</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <span className="font-medium">📍 Mesafe:</span> 
                      <span className={isVeryClose ? 'text-green-600 font-bold' : ''}>
                        {courierLocation && order.pickup_address ? 
                          `${calculateDistance(courierLocation.lat, courierLocation.lng, order.pickup_address.lat, order.pickup_address.lng).toFixed(1)} km` : 
                          'Hesaplanıyor...'}
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
                      className={`flex-1 ${isVeryClose ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}`}
                    >
                      {isVeryClose ? '🎯 Hemen Kabul Et!' : '✅ Siparişi Kabul Et'}
                    </Button>
                    <Button
                      variant="outline"
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
    </div>
  );
};

export default {
  CreateOrderForm,
  OrdersList,
  NearbyOrdersForCourier,
  OrderStatusBadge
};