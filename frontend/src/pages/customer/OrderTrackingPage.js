import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

const OrderTrackingPage = ({ orderId, onBack, user }) => {
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [courierLocation, setCourierLocation] = useState(null);
  const [locationLoading, setLocationLoading] = useState(false);

  const orderStatuses = {
    'created': { label: 'Sipariş Alındı', icon: '📝', color: 'text-blue-600', bgColor: 'bg-blue-100' },
    'confirmed': { label: 'Sipariş Onaylandı', icon: '✅', color: 'text-green-600', bgColor: 'bg-green-100' },
    'preparing': { label: 'Hazırlanıyor', icon: '👨‍🍳', color: 'text-orange-600', bgColor: 'bg-orange-100' },
    'picked_up': { label: 'Kuryede', icon: '🚴', color: 'text-purple-600', bgColor: 'bg-purple-100' },
    'delivering': { label: 'Yolda', icon: '🚗', color: 'text-blue-600', bgColor: 'bg-blue-100' },
    'delivered': { label: 'Teslim Edildi', icon: '🎉', color: 'text-green-600', bgColor: 'bg-green-100' },
    'cancelled': { label: 'İptal Edildi', icon: '❌', color: 'text-red-600', bgColor: 'bg-red-100' }
  };

  const fetchOrderDetails = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const token = localStorage.getItem('kuryecini_access_token');

      const response = await fetch(`${BACKEND_URL}/api/orders/${orderId}/track`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Sipariş bilgileri alınamadı');
      }

      const orderData = await response.json();
      setOrder(orderData);
      
      // If order has courier and is being delivered, fetch courier location
      if (orderData.courier_id && ['picked_up', 'delivering'].includes(orderData.status)) {
        fetchCourierLocation();
      }
    } catch (error) {
      console.error('Order tracking error:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCourierLocation = async () => {
    try {
      setLocationLoading(true);
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const token = localStorage.getItem('kuryecini_access_token');

      const response = await fetch(`${BACKEND_URL}/api/orders/${orderId}/courier/location`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const locationData = await response.json();
        if (locationData.courier_location) {
          setCourierLocation(locationData.courier_location);
        } else {
          setCourierLocation(null);
        }
      } else {
        setCourierLocation(null);
      }
    } catch (error) {
      console.error('Courier location fetch error:', error);
      setCourierLocation(null);
    } finally {
      setLocationLoading(false);
    }
  };

  useEffect(() => {
    if (orderId) {
      fetchOrderDetails();
      
      // Auto refresh order details every 30 seconds
      const orderInterval = setInterval(fetchOrderDetails, 30000);
      
      // Auto refresh courier location every 5 seconds when courier is delivering
      const locationInterval = setInterval(() => {
        if (order && order.courier_id && ['picked_up', 'delivering'].includes(order.status)) {
          fetchCourierLocation();
        }
      }, 5000);
      
      return () => {
        clearInterval(orderInterval);
        clearInterval(locationInterval);
      };
    }
  }, [orderId, order]);

  const getStatusTimeline = () => {
    if (!order) return [];

    const timeline = [
      { 
        status: 'created', 
        timestamp: order.created_at,
        active: true 
      },
      { 
        status: 'confirmed', 
        timestamp: order.confirmed_at,
        active: ['confirmed', 'preparing', 'picked_up', 'delivering', 'delivered'].includes(order.status)
      },
      { 
        status: 'preparing', 
        timestamp: order.preparing_at,
        active: ['preparing', 'picked_up', 'delivering', 'delivered'].includes(order.status)
      },
      { 
        status: 'picked_up', 
        timestamp: order.picked_up_at,
        active: ['picked_up', 'delivering', 'delivered'].includes(order.status)
      },
      { 
        status: 'delivering', 
        timestamp: order.delivering_at,
        active: ['delivering', 'delivered'].includes(order.status)
      },
      { 
        status: 'delivered', 
        timestamp: order.delivered_at,
        active: order.status === 'delivered'
      }
    ];

    return timeline;
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('tr-TR', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return '';
    }
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString('tr-TR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    } catch {
      return '';
    }
  };

  const getEstimatedDeliveryText = () => {
    if (!order?.estimated_delivery) return '';
    
    try {
      const estimatedTime = new Date(order.estimated_delivery);
      const now = new Date();
      const diffMinutes = Math.max(0, Math.ceil((estimatedTime - now) / (1000 * 60)));
      
      if (diffMinutes <= 0) {
        return 'Çok yakında';
      } else if (diffMinutes <= 60) {
        return `Yaklaşık ${diffMinutes} dakika`;
      } else {
        const hours = Math.ceil(diffMinutes / 60);
        return `Yaklaşık ${hours} saat`;
      }
    } catch {
      return '';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Sipariş bilgileri yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Sipariş bulunamadı'}</p>
          <button 
            onClick={onBack}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg"
          >
            Geri Dön
          </button>
        </div>
      </div>
    );
  }

  const currentStatusInfo = orderStatuses[order.status] || orderStatuses['created'];
  const timeline = getStatusTimeline();

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="flex items-center mb-6">
          <button 
            onClick={onBack}
            className="mr-4 p-2 rounded-full hover:bg-gray-200"
          >
            ←
          </button>
          <h1 className="text-xl font-bold text-gray-900">Sipariş Takip</h1>
        </div>

        {/* Current Status Card */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="text-center">
            <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${currentStatusInfo.bgColor} mb-4`}>
              <span className="text-3xl">{currentStatusInfo.icon}</span>
            </div>
            <h2 className={`text-xl font-bold ${currentStatusInfo.color} mb-2`}>
              {currentStatusInfo.label}
            </h2>
            <p className="text-gray-600 mb-2">
              Sipariş No: #{order.id.slice(-8).toUpperCase()}
            </p>
            {order.estimated_delivery && order.status !== 'delivered' && (
              <p className="text-sm text-blue-600 font-medium">
                Tahmini Teslimat: {getEstimatedDeliveryText()}
              </p>
            )}
          </div>
        </div>

        {/* Restaurant & Items */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center mb-4">
            <span className="text-2xl mr-3">🏪</span>
            <div>
              <p className="font-semibold">{order.business_name}</p>
              <p className="text-sm text-gray-600">{order.items?.length} ürün</p>
            </div>
          </div>

          {/* Order Items */}
          <div className="space-y-2">
            {order.items?.map((item, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <div className="flex-1">
                  <p className="font-medium">{item.product_name}</p>
                  <p className="text-sm text-gray-600">x{item.quantity}</p>
                </div>
                <p className="font-medium">₺{item.subtotal?.toFixed(2)}</p>
              </div>
            ))}
            <div className="flex justify-between items-center font-bold text-lg pt-2">
              <span>Toplam</span>
              <span>₺{order.total_amount?.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Delivery Address */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-start">
            <span className="text-2xl mr-3 mt-1">📍</span>
            <div>
              <p className="font-semibold mb-1">Teslimat Adresi</p>
              <p className="text-gray-600">{order.delivery_address}</p>
            </div>
          </div>
        </div>

        {/* Courier Info */}
        {order.courier_name && (
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-2xl mr-3">🚴</span>
                <div>
                  <p className="font-semibold">Kuryeniz</p>
                  <p className="text-gray-600">{order.courier_name}</p>
                </div>
              </div>
              {order.courier_location && (
                <div className="text-right">
                  <p className="text-sm text-green-600 font-medium">🟢 Aktif</p>
                  <p className="text-xs text-gray-500">
                    Son güncelleme: {formatTime(order.courier_location.last_updated)}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Status Timeline */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Sipariş Durumu</h3>
          
          <div className="space-y-4">
            {timeline.map((step, index) => {
              const statusInfo = orderStatuses[step.status];
              const isActive = step.active;
              const hasTimestamp = step.timestamp;
              
              return (
                <div key={step.status} className="flex items-center">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    isActive ? statusInfo.bgColor : 'bg-gray-100'
                  }`}>
                    <span className={`text-sm ${isActive ? statusInfo.color : 'text-gray-400'}`}>
                      {statusInfo.icon}
                    </span>
                  </div>
                  
                  <div className="ml-3 flex-1">
                    <p className={`font-medium ${isActive ? 'text-gray-900' : 'text-gray-400'}`}>
                      {statusInfo.label}
                    </p>
                    {hasTimestamp && (
                      <p className="text-xs text-gray-500">
                        {formatDate(step.timestamp)} - {formatTime(step.timestamp)}
                      </p>
                    )}
                  </div>
                  
                  {isActive && !hasTimestamp && step.status === order.status && (
                    <div className="text-xs text-blue-600 font-medium">
                      Şu anda
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Payment Info */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-3">💳</span>
              <div>
                <p className="font-semibold">Ödeme Yöntemi</p>
                <p className="text-gray-600 capitalize">
                  {order.payment_method?.replace('_', ' ') || 'Belirtilmemiş'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className={`text-sm font-medium ${
                order.payment_status === 'paid' ? 'text-green-600' : 'text-orange-600'
              }`}>
                {order.payment_status === 'paid' ? '✅ Ödendi' : '⏳ Beklemede'}
              </p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          {order.status === 'delivered' && (
            <button className="w-full bg-green-500 text-white py-3 rounded-lg font-semibold">
              ⭐ Sipariş ve Kurye Değerlendir
            </button>
          )}
          
          {['created', 'confirmed'].includes(order.status) && (
            <button className="w-full bg-red-500 text-white py-3 rounded-lg font-semibold">
              ❌ Siparişi İptal Et
            </button>
          )}
          
          <button 
            onClick={() => window.location.href = `tel:+905551234567`}
            className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold"
          >
            📞 Restoran ile İletişime Geç
          </button>
          
          <button 
            onClick={fetchOrderDetails}
            className="w-full bg-gray-500 text-white py-3 rounded-lg font-semibold"
          >
            🔄 Durumu Yenile
          </button>
        </div>

        {/* Auto Refresh Info */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            📡 Sipariş durumu otomatik olarak güncellenmektedir
          </p>
        </div>
      </div>
    </div>
  );
};

export default OrderTrackingPage;