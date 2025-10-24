import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { MapPin, Navigation, Package, Store, RefreshCw, ShoppingBag } from 'lucide-react';
import { toast } from 'sonner';
import OpenStreetMap from './OpenStreetMap';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

export const CourierMapWithBusinesses = () => {
  const [nearbyBusinesses, setNearbyBusinesses] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [claimingOrderId, setClaimingOrderId] = useState(null);
  const [courierLocation, setCourierLocation] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Get courier location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCourierLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.error('Location error:', error);
          // Default location (Ankara)
          setCourierLocation({ lat: 39.9334, lng: 32.8597 });
        }
      );
    } else {
      setCourierLocation({ lat: 39.9334, lng: 32.8597 });
    }
  }, []);

  useEffect(() => {
    if (courierLocation) {
      fetchNearbyBusinesses();
      const interval = setInterval(fetchNearbyBusinesses, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [courierLocation]);

  const fetchNearbyBusinesses = async () => {
    if (!courierLocation) return;
    
    try {
      setLoading(true);
      const response = await fetch(
        `${API}/courier/tasks/nearby-businesses?lat=${courierLocation.lat}&lng=${courierLocation.lng}&radius_m=50000`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );

      if (response.ok) {
        const data = await response.json();
        setNearbyBusinesses(data);
        console.log('📍 Nearby businesses:', data);
      }
    } catch (error) {
      console.error('❌ Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBusinessClick = async (business) => {
    setSelectedBusiness(business);
    setSelectedOrder(null);
    
    // Fetch available orders for this business
    try {
      const response = await fetch(
        `${API}/courier/tasks/businesses/${business.business_id}/available-orders`,
        {
          method: 'GET',
          credentials: 'include'
        }
      );

      if (response.ok) {
        const orders = await response.json();
        setAvailableOrders(orders);
      }
    } catch (error) {
      console.error('❌ Orders fetch error:', error);
    }
  };

  const handleOrderClick = (order) => {
    setSelectedOrder(order);
  };

  const handleClaimOrder = async (orderId) => {
    try {
      setClaimingOrderId(orderId);
      const response = await fetch(
        `${API}/courier/tasks/orders/${orderId}/claim`,
        {
          method: 'POST',
          credentials: 'include'
        }
      );

      if (response.ok) {
        toast.success('✅ Sipariş başarıyla alındı!');
        await fetchNearbyBusinesses();
        setSelectedBusiness(null);
        setSelectedOrder(null);
        setAvailableOrders([]);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Sipariş alınamadı');
      }
    } catch (error) {
      console.error('❌ Claim error:', error);
      toast.error('Bir hata oluştu');
    } finally {
      setClaimingOrderId(null);
    }
  };

  const openInMaps = (lat, lng, label) => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
      const appleMapsUrl = `maps://maps.apple.com/?daddr=${lat},${lng}&q=${encodeURIComponent(label)}`;
      const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
      
      window.location.href = appleMapsUrl;
      setTimeout(() => {
        window.open(googleMapsUrl, '_blank');
      }, 500);
    } else {
      const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
      window.open(url, '_blank');
    }
  };

  // Convert businesses to map markers
  const mapMarkers = nearbyBusinesses.map(business => {
    const coords = business.location?.coordinates || [business.lng || 0, business.lat || 0];
    return {
      lat: coords[1] || business.lat,
      lng: coords[0] || business.lng,
      type: 'business',
      label: `${business.name} (${business.pending_ready_count} sipariş)`,
      count: business.pending_ready_count,
      businessId: business.business_id,
      popup: `<strong>${business.name}</strong><br/>${business.pending_ready_count} hazır sipariş`
    };
  });

  // Add courier location marker
  if (courierLocation) {
    mapMarkers.push({
      lat: courierLocation.lat,
      lng: courierLocation.lng,
      type: 'courier',
      label: 'Benim Konumum',
      popup: '<strong>📍 Konumunuz</strong>'
    });
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Hazır Siparişler Haritası</h2>
          <p className="text-muted-foreground">
            {nearbyBusinesses.length} işletmede {nearbyBusinesses.reduce((sum, b) => sum + b.pending_ready_count, 0)} hazır sipariş
          </p>
        </div>
        <Button onClick={fetchNearbyBusinesses} disabled={loading} size="sm">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Yenile
        </Button>
      </div>

      {/* Map */}
      <Card>
        <CardContent className="p-0">
          <OpenStreetMap
            center={courierLocation ? [courierLocation.lat, courierLocation.lng] : [39.9334, 32.8597]}
            zoom={13}
            height="500px"
            markers={mapMarkers}
            courierLocation={courierLocation}
            onMarkerClick={(marker) => {
              if (marker.type === 'business') {
                const business = nearbyBusinesses.find(b => b.business_id === marker.businessId);
                if (business) {
                  handleBusinessClick(business);
                }
              }
            }}
          />
        </CardContent>
      </Card>

      {/* Selected Business Orders */}
      {selectedBusiness && availableOrders.length > 0 && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Store className="h-5 w-5" />
                  {selectedBusiness.name}
                </CardTitle>
                <CardDescription>
                  {availableOrders.length} hazır sipariş mevcut
                </CardDescription>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => {
                  setSelectedBusiness(null);
                  setSelectedOrder(null);
                  setAvailableOrders([]);
                }}
              >
                ✕
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {availableOrders.map((order) => (
                <div 
                  key={order.order_id}
                  className={`p-4 bg-white rounded-lg border-2 cursor-pointer transition-all ${
                    selectedOrder?.order_id === order.order_id 
                      ? 'border-green-500 shadow-md' 
                      : 'border-gray-200 hover:border-green-300'
                  }`}
                  onClick={() => handleOrderClick(order)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h5 className="font-semibold text-sm flex items-center gap-2">
                        <Package className="h-4 w-4" />
                        Sipariş #{order.order_code}
                      </h5>
                      <p className="text-xs text-muted-foreground mt-1">
                        👤 {order.customer_name}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        📦 {order.items_count} ürün
                      </p>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        📍 {typeof order.delivery_address === 'string' 
                          ? order.delivery_address 
                          : order.delivery_address?.address || 'Adres bilgisi yok'}
                      </p>
                    </div>
                    <div className="text-right ml-3">
                      <p className="font-bold text-green-600">
                        ₺{order.grand_total?.toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        (₺{order.delivery_fee?.toFixed(2)} teslimat)
                      </p>
                    </div>
                  </div>

                  {/* Order Details (shown when selected) */}
                  {selectedOrder?.order_id === order.order_id && (
                    <div className="mt-3 pt-3 border-t space-y-2">
                      {order.notes && (
                        <p className="text-xs text-yellow-600">
                          💬 Not: {order.notes}
                        </p>
                      )}
                      <div className="flex gap-2">
                        <Button
                          className="flex-1 bg-green-600 hover:bg-green-700"
                          size="sm"
                          onClick={() => handleClaimOrder(order.order_id)}
                          disabled={claimingOrderId === order.order_id}
                        >
                          {claimingOrderId === order.order_id ? (
                            <>🔄 Alınıyor...</>
                          ) : (
                            <>
                              <ShoppingBag className="h-4 w-4 mr-2" />
                              Siparişi Al
                            </>
                          )}
                        </Button>
                        {order.delivery_location?.lat && order.delivery_location?.lng && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openInMaps(
                              order.delivery_location.lat,
                              order.delivery_location.lng,
                              'Teslimat Adresi'
                            )}
                          >
                            <Navigation className="h-4 w-4 mr-2" />
                            Yol Tarifi
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CourierMapWithBusinesses;
