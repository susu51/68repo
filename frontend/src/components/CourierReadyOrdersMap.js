import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { MapPin, Navigation, Package, Store, Clock, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://courier-connect-14.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierReadyOrdersMap = () => {
  const [readyOrders, setReadyOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [courierCity, setCourierCity] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchNearbyBusinesses();
    
    const interval = setInterval(() => {
      fetchNearbyBusinesses();
    }, 15000); // 15 saniye
    
    return () => clearInterval(interval);
  }, []);

  const [nearbyBusinesses, setNearbyBusinesses] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [claimingOrderId, setClaimingOrderId] = useState(null);
  
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

  const openInMaps = (lat, lng, address) => {
    // Open in Google Maps
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
    window.open(url, '_blank');
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
                onClick={fetchReadyOrders}
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
                  key={location.business_id || index}
                  className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-purple-200 dark:border-purple-800 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-semibold text-sm flex items-center gap-2">
                        <Store className="h-4 w-4 text-purple-600" />
                        {location.business_name}
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {location.address}
                      </p>
                    </div>
                    <Badge variant="secondary" className="bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">
                      {location.task_count} sipariş
                    </Badge>
                  </div>
                  
                  {location.location && location.location.lat && location.location.lng && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full mt-2"
                      onClick={() => openInMaps(location.location.lat, location.location.lng, location.address)}
                    >
                      <Navigation className="h-3 w-3 mr-2" />
                      Haritada Göster
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Ready Orders List */}
      {readyOrders.length === 0 ? (
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
