import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { MapPin, Navigation, Package, Store, Clock, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://quickship-49.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierReadyOrdersMap = () => {
  const [readyOrders, setReadyOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [courierCity, setCourierCity] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchReadyOrders();

    // Set up auto-refresh every 10 seconds
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        fetchReadyOrders();
      }, 10000);
    }

    return () => {
      // Cleanup interval on unmount or when autoRefresh changes
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [autoRefresh]); // Only depend on autoRefresh to avoid infinite loops

  const fetchReadyOrders = async () => {
    try {
      setLoading(true);
      
      let url = `${API}/courier/orders/ready`;
      if (courierCity) {
        url += `?city=${courierCity}`;
      }

      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include'
      });

      if (response.ok) {
        const orders = await response.json();
        setReadyOrders(orders);
      }
    } catch (error) {
      console.error('Hazır siparişler yükleme hatası:', error);
    } finally {
      setLoading(false);
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
