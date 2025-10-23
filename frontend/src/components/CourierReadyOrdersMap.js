import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { MapPin, Navigation, Package, Store, Clock, RefreshCw, ShoppingBag, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://courier-dashboard-3.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierReadyOrdersMap = () => {
  const [readyOrders, setReadyOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [courierCity, setCourierCity] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchNearbyBusinesses();
    fetchMyActiveOrders();
    
    const interval = setInterval(() => {
      fetchNearbyBusinesses();
      fetchMyActiveOrders();
    }, 15000); // 15 saniye
    
    return () => clearInterval(interval);
  }, []);

  const [nearbyBusinesses, setNearbyBusinesses] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [claimingOrderId, setClaimingOrderId] = useState(null);
  const [myActiveOrders, setMyActiveOrders] = useState([]);
  
  const fetchNearbyBusinesses = async () => {
    try {
      setLoading(true);
      
      // Get courier's current location (mock for now - should use geolocation)
      const courierLng = 34.0254; // Aksaray, Ankara
      const courierLat = 38.3687;
      
      // Fetch nearby businesses with ready orders
      const response = await fetch(
        `${API}/courier/tasks/nearby-businesses?lng=${courierLng}&lat=${courierLat}&radius_m=10000`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const businesses = await response.json();
        setNearbyBusinesses(businesses);
        console.log('📍 Nearby businesses:', businesses);
      }
    } catch (error) {
      console.error('❌ Nearby businesses fetch error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchAvailableOrders = async (businessId) => {
    try {
      const response = await fetch(
        `${API}/courier/tasks/businesses/${businessId}/available-orders`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const orders = await response.json();
        setAvailableOrders(orders);
        console.log('📦 Available orders:', orders);
      }
    } catch (error) {
      console.error('❌ Available orders fetch error:', error);
    }
  };
  
  const fetchMyActiveOrders = async () => {
    try {
      const response = await fetch(
        `${API}/courier/tasks/my-orders`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );
      
      if (response.ok) {
        const orders = await response.json();
        setMyActiveOrders(orders);
        console.log('🚚 My active orders:', orders);
      }
    } catch (error) {
      console.error('❌ My active orders fetch error:', error);
    }
  };
  
  const claimOrder = async (orderId) => {
    try {
      setClaimingOrderId(orderId);
      
      const response = await fetch(
        `${API}/courier/tasks/orders/${orderId}/claim`,
        {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        toast.success('✅ Sipariş alındı! Teslimat başlayabilir.');
        
        // Refresh lists
        await fetchNearbyBusinesses();
        await fetchMyActiveOrders();
        setSelectedBusiness(null);
        setAvailableOrders([]);
      } else if (response.status === 409) {
        toast.error('⚠️ Bu sipariş başka bir kurye tarafından alındı');
        // Refresh the list
        if (selectedBusiness) {
          await fetchAvailableOrders(selectedBusiness.business_id);
        }
      } else {
        toast.error('❌ Sipariş alınamadı');
      }
    } catch (error) {
      console.error('❌ Claim error:', error);
      toast.error('Bir hata oluştu');
    } finally {
      setClaimingOrderId(null);
    }
  };

  const handleAcceptOrder = async (orderId) => {
    try {
      const response = await fetch(`${API}/courier/${orderId}/accept`, {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success('Sipariş kabul edildi!');
        // Remove from ready orders
        setReadyOrders(prev => prev.filter(order => order.id !== orderId));
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Sipariş kabul edilemedi');
      }
    } catch (error) {
      console.error('Sipariş kabul hatası:', error);
      toast.error('Sipariş kabul edilemedi');
    }
  };

  const openInMaps = (lat, lng, address, label = 'Teslimat Adresi') => {
    // Convert address to string if it's an object
    const addressStr = typeof address === 'string' 
      ? address 
      : address?.label || address?.address || label;
    
    // Detect device and open appropriate maps app
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isAndroid = /Android/.test(navigator.userAgent);
    
    if (isIOS) {
      // Try Apple Maps first, fallback to Google Maps
      const appleMapsUrl = `maps://maps.apple.com/?daddr=${lat},${lng}&q=${encodeURIComponent(label)}`;
      const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
      
      // Try Apple Maps
      window.location.href = appleMapsUrl;
      
      // Fallback to Google Maps after 500ms
      setTimeout(() => {
        window.open(googleMapsUrl, '_blank');
      }, 500);
    } else {
      // Android or Desktop: Use Google Maps
      const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
      window.open(url, '_blank');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="h-5 w-5" />
                Hazır Siparişler
              </CardTitle>
              <CardDescription>
                Teslim almaya hazır {readyOrders.length} sipariş
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={fetchNearbyBusinesses}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
              <Button
                variant={autoRefresh ? "default" : "outline"}
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? "Otomatik Yenileme: Açık" : "Otomatik Yenileme: Kapalı"}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Nearby Businesses Map - Click to see orders */}
      {nearbyBusinesses.length > 0 && (
        <Card className="border-green-200 bg-green-50 dark:bg-green-900/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-300">
              <Store className="h-5 w-5" />
              Hazır Siparişler - İşletme Haritası ({nearbyBusinesses.length})
            </CardTitle>
            <CardDescription>
              Teslim alınmayı bekleyen siparişler - İşletmeye tıklayın, sipariş seçip alın
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {nearbyBusinesses.map((business, index) => (
                <div 
                  key={business.business_id || index}
                  className={`p-4 bg-white dark:bg-gray-800 rounded-lg border cursor-pointer transition-all ${
                    selectedBusiness?.business_id === business.business_id
                      ? 'border-green-500 ring-2 ring-green-300'
                      : 'border-green-200 dark:border-green-800 hover:shadow-md'
                  }`}
                  onClick={() => {
                    setSelectedBusiness(business);
                    fetchAvailableOrders(business.business_id);
                  }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-semibold text-sm flex items-center gap-2">
                        <Store className="h-4 w-4 text-green-600" />
                        {business.name}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {business.address_short}
                      </p>
                      {business.distance && (
                        <p className="text-xs text-muted-foreground mt-1">
                          📍 {(business.distance / 1000).toFixed(1)} km uzakta
                        </p>
                      )}
                    </div>
                    <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                      {business.pending_ready_count} sipariş
                    </Badge>
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full mt-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedBusiness(business);
                      fetchAvailableOrders(business.business_id);
                    }}
                  >
                    <Package className="h-3 w-3 mr-2" />
                    Siparişleri Gör
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* My Active Orders Panel */}
      {myActiveOrders.length > 0 && (
        <Card className="border-purple-200 bg-purple-50 dark:bg-purple-900/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
              <Package className="h-5 w-5" />
              Aktif Siparişlerim ({myActiveOrders.length})
            </CardTitle>
            <CardDescription>
              Teslim etmekte olduğunuz siparişler
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              {myActiveOrders.map((order) => (
                <div 
                  key={order.order_id}
                  className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-purple-200 dark:border-purple-800"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h5 className="font-semibold text-sm flex items-center gap-2">
                        Sipariş #{order.order_code}
                        {order.status === 'assigned' && (
                          <Badge variant="secondary" className="bg-yellow-100 text-yellow-700">
                            Bekliyor
                          </Badge>
                        )}
                        {order.status === 'picked_up' && (
                          <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                            Alındı
                          </Badge>
                        )}
                        {order.status === 'delivering' && (
                          <Badge variant="secondary" className="bg-green-100 text-green-700">
                            Yolda
                          </Badge>
                        )}
                      </h5>
                      
                      {/* Pickup Info */}
                      <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
                        <p className="text-xs font-semibold text-orange-700 dark:text-orange-300 mb-1">
                          📍 Alınacak Adres:
                        </p>
                        <p className="text-xs font-medium">🏪 {order.business_name}</p>
                        <p className="text-xs text-muted-foreground line-clamp-1">
                          {typeof order.business_address === 'string' 
                            ? order.business_address 
                            : order.business_address?.label || order.business_address?.address || 'Adres bilgisi yok'}
                        </p>
                        {order.business_location?.lat && order.business_location?.lng && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full mt-2 bg-orange-100 hover:bg-orange-200 text-orange-700"
                            onClick={() => openInMaps(
                              order.business_location.lat,
                              order.business_location.lng,
                              order.business_address,
                              'İşletme - Alış Noktası'
                            )}
                          >
                            <Navigation className="h-3 w-3 mr-2" />
                            Alış Noktasına Git (Maps)
                          </Button>
                        )}
                      </div>
                      
                      {/* Delivery Info */}
                      <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                        <p className="text-xs font-semibold text-green-700 dark:text-green-300 mb-1">
                          🚚 Teslim Edilecek Adres:
                        </p>
                        <p className="text-xs font-medium">👤 {order.customer_name}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {typeof order.delivery_address === 'string' 
                            ? order.delivery_address 
                            : order.delivery_address?.label || order.delivery_address?.address || 'Adres bilgisi yok'}
                        </p>
                        {order.delivery_location?.lat && order.delivery_location?.lng && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full mt-2 bg-green-100 hover:bg-green-200 text-green-700"
                            onClick={() => openInMaps(
                              order.delivery_location.lat,
                              order.delivery_location.lng,
                              order.delivery_address,
                              'Müşteri - Teslimat Noktası'
                            )}
                          >
                            <Navigation className="h-3 w-3 mr-2" />
                            Teslimat Noktasına Git (Maps)
                          </Button>
                        )}
                      </div>
                      
                      <p className="text-xs text-muted-foreground mt-2">
                        📦 {order.items_count} ürün
                      </p>
                      {order.notes && (
                        <p className="text-xs text-yellow-600 mt-1">
                          💬 Not: {order.notes}
                        </p>
                      )}
                    </div>
                    <div className="text-right ml-3">
                      <p className="font-bold text-green-600">
                        ₺{order.grand_total.toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        (₺{order.delivery_fee.toFixed(2)} teslimat)
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Available Orders Modal/Panel */}
      {selectedBusiness && (
        <Card className="border-blue-200 bg-blue-50 dark:bg-blue-900/10 mt-4">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
                <ShoppingBag className="h-5 w-5" />
                {selectedBusiness.name} - Siparişler ({availableOrders.length})
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedBusiness(null);
                  setAvailableOrders([]);
                }}
              >
                ✕
              </Button>
            </div>
            <CardDescription>
              Sipariş seçin ve alın - İlk gelen ilk alır!
            </CardDescription>
          </CardHeader>
          <CardContent>
            {availableOrders.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Package className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>Bu işletmede hazır sipariş yok</p>
              </div>
            ) : (
              <div className="grid gap-3">
                {availableOrders.map((order) => (
                  <div 
                    key={order.order_id}
                    className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-blue-200 dark:border-blue-800"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h5 className="font-semibold text-sm">
                          Sipariş #{order.order_code}
                        </h5>
                        <p className="text-xs text-muted-foreground mt-1">
                          👤 {order.customer_name}
                        </p>
                        <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-900 rounded">
                          <p className="text-xs text-muted-foreground line-clamp-2 mb-1">
                            📍 {typeof order.delivery_address === 'string' 
                              ? order.delivery_address 
                              : order.delivery_address?.label || order.delivery_address?.address || 'Adres bilgisi yok'}
                          </p>
                          {order.delivery_location?.lat && order.delivery_location?.lng && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 text-xs p-1"
                              onClick={(e) => {
                                e.stopPropagation();
                                openInMaps(
                                  order.delivery_location.lat,
                                  order.delivery_location.lng,
                                  order.delivery_address,
                                  'Teslimat Adresi'
                                );
                              }}
                            >
                              <Navigation className="h-3 w-3 mr-1" />
                              Maps'te Aç
                            </Button>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          📦 {order.items_count} ürün
                        </p>
                        {order.notes && (
                          <p className="text-xs text-yellow-600 mt-1">
                            💬 {order.notes}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-green-600">
                          ₺{order.grand_total.toFixed(2)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          (₺{order.delivery_fee.toFixed(2)} teslimat)
                        </p>
                      </div>
                    </div>
                    
                    <Button
                      className="w-full bg-green-600 hover:bg-green-700 text-white"
                      size="sm"
                      disabled={claimingOrderId === order.order_id}
                      onClick={() => claimOrder(order.order_id)}
                    >
                      {claimingOrderId === order.order_id ? (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                          Alınıyor...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="h-4 w-4 mr-2" />
                          Siparişi Al
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Ready Orders List (old, keep for now) */}
      {!selectedBusiness && readyOrders.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Şu an hazır sipariş bulunmuyor</p>
              <p className="text-sm mt-2">Yeni siparişler {autoRefresh ? '10 saniyede' : 'manuel yenileme ile'} görünecek</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {readyOrders.map((order) => (
            <Card key={order.id} className="border-green-200 bg-green-50">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Store className="h-5 w-5" />
                      {order.business_name}
                    </CardTitle>
                    <CardDescription className="text-sm">
                      {order.business_address}
                    </CardDescription>
                  </div>
                  <Badge variant="success" className="bg-green-600">
                    Hazır
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Order Info */}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Package className="h-4 w-4" />
                    {order.items_count} ürün
                  </div>
                  <div className="font-medium">
                    ₺{order.total_amount.toFixed(2)}
                  </div>
                </div>

                {/* Delivery Address */}
                <div className="text-sm">
                  <div className="flex items-start gap-2 text-muted-foreground">
                    <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span className="line-clamp-2">
                      {order.delivery_address?.address || 'Adres bilgisi yok'}
                    </span>
                  </div>
                </div>

                {/* Estimated Time */}
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4" />
                  Tahmini: {order.estimated_time}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2">
                  <Button
                    className="flex-1"
                    size="sm"
                    onClick={() => handleAcceptOrder(order.id)}
                  >
                    Kabul Et
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openInMaps(
                      order.business_location.lat,
                      order.business_location.lng,
                      order.business_address
                    )}
                  >
                    <Navigation className="h-4 w-4" />
                  </Button>
                </div>

                {/* Distance info if available */}
                {order.distance && (
                  <div className="text-xs text-muted-foreground text-center pt-1">
                    {(order.distance / 1000).toFixed(1)} km uzaklıkta
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Info */}
      <Card>
        <CardContent className="py-3">
          <p className="text-xs text-muted-foreground text-center">
            💡 Siparişler {autoRefresh ? 'otomatik olarak her 10 saniyede' : 'manuel'} yenilenir. 
            Hazır siparişler yalnızca sizin şehrinizden gösterilir.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
