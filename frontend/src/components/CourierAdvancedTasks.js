import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  MapPin, 
  Navigation, 
  Package, 
  Store, 
  RefreshCw, 
  List,
  Map,
  Phone,
  CreditCard,
  User,
  Clock,
  DollarSign,
  Home,
  ShoppingBag
} from 'lucide-react';
import { toast } from 'sonner';
import { SimpleLeafletMap } from './SimpleLeafletMap';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-hub.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierAdvancedTasks = () => {
  // Removed viewMode - only map view
  const [nearbyBusinesses, setNearbyBusinesses] = useState([]);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [businessOrders, setBusinessOrders] = useState([]);
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
          setCourierLocation({ lat: 39.9334, lng: 32.8597 });
        }
      );
    } else {
      setCourierLocation({ lat: 39.9334, lng: 32.8597 });
    }
  }, []);

  useEffect(() => {
    if (courierLocation) {
      fetchData();
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [courierLocation]);

  const fetchData = async () => {
    if (!courierLocation) return;
    
    try {
      setLoading(true);
      
      // Fetch nearby businesses with ready orders
      const businessResponse = await fetch(
        `${API}/courier/tasks/nearby-businesses?lat=${courierLocation.lat}&lng=${courierLocation.lng}&radius_m=50000`,
        { method: 'GET', credentials: 'include' }
      );

      if (businessResponse.ok) {
        const businesses = await businessResponse.json();
        setNearbyBusinesses(businesses);
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
    
    try {
      const response = await fetch(
        `${API}/courier/tasks/businesses/${business.business_id}/available-orders`,
        { method: 'GET', credentials: 'include' }
      );

      if (response.ok) {
        const orders = await response.json();
        setBusinessOrders(orders);
      }
    } catch (error) {
      console.error('❌ Orders fetch error:', error);
    }
  };

  const handleClaimOrder = async (orderId) => {
    try {
      setClaimingOrderId(orderId);
      const response = await fetch(
        `${API}/courier/tasks/orders/${orderId}/claim`,
        { method: 'POST', credentials: 'include' }
      );

      if (response.ok) {
        toast.success('✅ Sipariş başarıyla alındı! "Siparişler" sekmesine gidin.');
        await fetchData();
        setSelectedOrder(null);
        setSelectedBusiness(null);
        setBusinessOrders([]);
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
      window.location.href = appleMapsUrl;
      setTimeout(() => {
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
      }, 500);
    } else {
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
    }
  };

  // Map markers - show BUSINESS locations with PACKAGE count (not delivery locations!)
  const mapMarkers = [];
  
  // Add business markers with package icons
  nearbyBusinesses.forEach(business => {
    const coords = business.location?.coordinates || [business.lng || 0, business.lat || 0];
    if (coords[1] && coords[0] && business.pending_ready_count > 0) {
      mapMarkers.push({
        lat: coords[1],
        lng: coords[0],
        type: 'business',
        businessId: business.business_id,
        label: `📦 ${business.name}`,
        count: business.pending_ready_count,
        popup: `<strong>📦 ${business.name}</strong><br/>${business.pending_ready_count} hazır paket`
      });
    }
  });

  // Add courier location
  if (courierLocation) {
    mapMarkers.push({
      lat: courierLocation.lat,
      lng: courierLocation.lng,
      type: 'courier',
      label: '📍 Benim Konumum',
      popup: '<strong>📍 Konumunuz</strong>'
    });
  }

  const formatAddress = (address) => {
    if (typeof address === 'string') return address;
    return address?.label || address?.address || 'Adres bilgisi yok';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Paket Havuzu - Hazır Siparişler</h2>
          <p className="text-muted-foreground">
            {nearbyBusinesses.reduce((sum, b) => sum + b.pending_ready_count, 0)} hazır paket • {nearbyBusinesses.length} işletme
          </p>
        </div>
        <Button onClick={fetchData} disabled={loading} size="sm" variant="outline">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''} mr-2`} />
          Yenile
        </Button>
      </div>

      {/* Simple Leaflet Map */}
      <SimpleLeafletMap
        onBusinessClick={async (business) => {
          const formattedBusiness = {
            business_id: business.id,
            name: business.name,
            pending_ready_count: business.active_order_count,
            location: business.location
          };
          await handleBusinessClick(formattedBusiness);
        }}
      />

      {/* Selected Business Orders */}
      {selectedBusiness && businessOrders.length > 0 && (
        <Card className="border-2 border-green-500 bg-green-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Store className="h-5 w-5" />
                  {selectedBusiness.name}
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  📦 {businessOrders.length} hazır paket
                </p>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => {
                  setSelectedBusiness(null);
                  setBusinessOrders([]);
                  setSelectedOrder(null);
                }}
              >
                ✕
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              {businessOrders.map((order) => (
                <Card 
                  key={order.order_id}
                  className={`cursor-pointer transition-all ${
                    selectedOrder?.order_id === order.order_id 
                      ? 'border-2 border-green-600 bg-white shadow-md' 
                      : 'bg-white hover:border-green-300'
                  }`}
                  onClick={() => setSelectedOrder(selectedOrder?.order_id === order.order_id ? null : order)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h5 className="font-semibold flex items-center gap-2">
                          <Package className="h-4 w-4" />
                          Sipariş #{order.order_code}
                        </h5>
                        <p className="text-xs text-muted-foreground mt-1">
                          👤 {order.customer_name}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          📦 {order.items_count} ürün
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-green-600">
                          ₺{order.grand_total?.toFixed(2)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          (₺{order.delivery_fee?.toFixed(2)} teslimat)
                        </p>
                      </div>
                    </div>

                    {/* Expand when selected */}
                    {selectedOrder?.order_id === order.order_id && (
                      <div className="mt-3 pt-3 border-t space-y-2">
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          📍 {formatAddress(order.delivery_address)}
                        </p>
                        {order.notes && (
                          <p className="text-xs text-yellow-600">
                            💬 {order.notes}
                          </p>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Order Details Panel */}
      {selectedOrder && (
        <Card className="border-2 border-green-500 bg-green-50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <ShoppingBag className="h-5 w-5" />
                Sipariş Detayları #{selectedOrder.order_code}
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setSelectedOrder(null)}
              >
                ✕
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Business Info */}
            <Card className="bg-orange-50 border-orange-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Store className="h-4 w-4" />
                  Alınacak Yer (İşletme)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div>
                  <p className="text-xs text-muted-foreground">İşletme Adı</p>
                  <p className="font-semibold">{selectedOrder.business_name}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Adres</p>
                  <p className="text-sm">{formatAddress(selectedOrder.business_address)}</p>
                </div>
                {selectedOrder.business_location?.lat && selectedOrder.business_location?.lng && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full bg-orange-100 hover:bg-orange-200"
                    onClick={() => openInMaps(
                      selectedOrder.business_location.lat,
                      selectedOrder.business_location.lng,
                      'İşletme - Alış Noktası'
                    )}
                  >
                    <Navigation className="h-4 w-4 mr-2" />
                    İşletmeye Git (Maps)
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Customer Info */}
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Müşteri Bilgileri
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div>
                  <p className="text-xs text-muted-foreground">Ad Soyad</p>
                  <p className="font-semibold">{selectedOrder.customer_name}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Teslimat Adresi</p>
                  <p className="text-sm">{formatAddress(selectedOrder.delivery_address)}</p>
                </div>
                {selectedOrder.customer_phone && (
                  <div>
                    <p className="text-xs text-muted-foreground">İletişim</p>
                    <a 
                      href={`tel:${selectedOrder.customer_phone}`}
                      className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:underline"
                    >
                      <Phone className="h-4 w-4" />
                      {selectedOrder.customer_phone}
                    </a>
                  </div>
                )}
                {selectedOrder.delivery_location?.lat && selectedOrder.delivery_location?.lng && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full bg-blue-100 hover:bg-blue-200"
                    onClick={() => openInMaps(
                      selectedOrder.delivery_location.lat,
                      selectedOrder.delivery_location.lng,
                      'Müşteri - Teslimat Noktası'
                    )}
                  >
                    <Navigation className="h-4 w-4 mr-2" />
                    Müşteriye Git (Maps)
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Order Details */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Sipariş İçeriği
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Ürün Sayısı:</span>
                  <span className="font-medium">{selectedOrder.items_count} ürün</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Sipariş Tutarı:</span>
                  <span className="font-medium">₺{selectedOrder.total_amount?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Teslimat Ücreti:</span>
                  <span className="font-medium text-green-600">₺{selectedOrder.delivery_fee?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold pt-2 border-t">
                  <span>Toplam:</span>
                  <span className="text-green-600">₺{selectedOrder.grand_total?.toFixed(2)}</span>
                </div>
              </CardContent>
            </Card>

            {/* Payment Info */}
            <Card className="bg-yellow-50 border-yellow-200">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Ödeme Bilgisi
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-yellow-600" />
                  <div>
                    <p className="font-semibold">
                      {selectedOrder.payment_method === 'cash' ? 'Kapıda Nakit Ödeme' : 
                       selectedOrder.payment_method === 'card' ? 'Kredi Kartı (Ödendi)' : 
                       'Ödeme Bilgisi Yok'}
                    </p>
                    {selectedOrder.payment_method === 'cash' && (
                      <p className="text-xs text-yellow-700">
                        ⚠️ Müşteriden ₺{selectedOrder.grand_total?.toFixed(2)} tahsil edilecek
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Notes */}
            {selectedOrder.notes && (
              <Card className="bg-purple-50 border-purple-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">📝 Notlar</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">{selectedOrder.notes}</p>
                </CardContent>
              </Card>
            )}

            {/* Action Button */}
            <Button
              className="w-full bg-green-600 hover:bg-green-700 text-lg py-6"
              onClick={() => handleClaimOrder(selectedOrder.order_id)}
              disabled={claimingOrderId === selectedOrder.order_id}
            >
              {claimingOrderId === selectedOrder.order_id ? (
                <>🔄 Sipariş Alınıyor...</>
              ) : (
                <>
                  <ShoppingBag className="h-5 w-5 mr-2" />
                  Siparişi Al ve Teslimata Başla
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CourierAdvancedTasks;
