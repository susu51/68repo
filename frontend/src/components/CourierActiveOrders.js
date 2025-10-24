import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Package, 
  Navigation, 
  Phone,
  CheckCircle,
  MapPin,
  Store,
  User,
  CreditCard,
  DollarSign,
  Clock
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CourierActiveOrders = () => {
  const [activeOrders, setActiveOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    fetchActiveOrders();
    const interval = setInterval(fetchActiveOrders, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchActiveOrders = async () => {
    try {
      const response = await fetch(`${API}/courier/tasks/my-orders`, {
        method: 'GET',
        credentials: 'include'
      });

      if (response.ok) {
        const orders = await response.json();
        setActiveOrders(orders);
      }
    } catch (error) {
      console.error('❌ Fetch error:', error);
    }
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      setActionLoading(orderId);
      const response = await fetch(`${API}/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ new_status: newStatus })
      });

      if (response.ok) {
        toast.success(
          newStatus === 'picked_up' ? '✅ Paket alındı olarak işaretlendi!' : 
          newStatus === 'delivered' ? '🎉 Sipariş teslim edildi!' : 
          '✅ Durum güncellendi'
        );
        await fetchActiveOrders();
        if (newStatus === 'delivered') {
          setSelectedOrder(null);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Durum güncellenemedi');
      }
    } catch (error) {
      console.error('❌ Status update error:', error);
      toast.error('Bir hata oluştu');
    } finally {
      setActionLoading(null);
    }
  };

  const openInMaps = (lat, lng, label) => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
      window.location.href = `maps://maps.apple.com/?daddr=${lat},${lng}&q=${encodeURIComponent(label)}`;
      setTimeout(() => {
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
      }, 500);
    } else {
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
    }
  };

  const formatAddress = (address) => {
    if (typeof address === 'string') return address;
    return address?.label || address?.address || 'Adres bilgisi yok';
  };

  const getStatusInfo = (status) => {
    switch (status) {
      case 'assigned':
        return { label: 'Atandı', color: 'bg-yellow-100 text-yellow-700', icon: Clock };
      case 'picked_up':
        return { label: 'Alındı', color: 'bg-blue-100 text-blue-700', icon: Package };
      case 'delivering':
        return { label: 'Teslimat Yolda', color: 'bg-purple-100 text-purple-700', icon: Navigation };
      default:
        return { label: status, color: 'bg-gray-100 text-gray-700', icon: Package };
    }
  };

  if (activeOrders.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-muted-foreground">
          <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Şu an aktif teslimatınız bulunmuyor</p>
          <p className="text-sm mt-2">Hazır siparişler sekmesinden sipariş alabilirsiniz</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Aktif Teslimatlarım ({activeOrders.length})</h2>
      </div>

      {/* Orders Grid */}
      <div className="grid gap-4">
        {activeOrders.map((order) => {
          const statusInfo = getStatusInfo(order.status);
          const StatusIcon = statusInfo.icon;
          const isSelected = selectedOrder?.order_id === order.order_id;

          return (
            <Card 
              key={order.order_id}
              className={`cursor-pointer transition-all ${
                isSelected ? 'border-2 border-green-500 shadow-lg' : 'hover:shadow-md'
              }`}
              onClick={() => setSelectedOrder(isSelected ? null : order)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Package className="h-5 w-5" />
                      Sipariş #{order.order_code}
                    </CardTitle>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className={statusInfo.color}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {statusInfo.label}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-green-600">
                      ₺{order.grand_total?.toFixed(2)}
                    </p>
                  </div>
                </div>
              </CardHeader>

              {isSelected && (
                <CardContent className="space-y-4">
                  {/* Pickup Location */}
                  <Card className="bg-orange-50 border-orange-200">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Store className="h-4 w-4" />
                        Alış Noktası (İşletme)
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div>
                        <p className="text-xs text-muted-foreground">İşletme</p>
                        <p className="font-semibold">{order.business_name}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">Adres</p>
                        <p className="text-sm">{formatAddress(order.business_address)}</p>
                      </div>
                      {order.business_location?.lat && order.business_location?.lng && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full bg-orange-100 hover:bg-orange-200"
                          onClick={(e) => {
                            e.stopPropagation();
                            openInMaps(
                              order.business_location.lat,
                              order.business_location.lng,
                              'İşletme - Alış Noktası'
                            );
                          }}
                        >
                          <Navigation className="h-4 w-4 mr-2" />
                          İşletmeye Git
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
                        <p className="font-semibold">{order.customer_name}</p>
                      </div>
                      {order.customer_phone && (
                        <div>
                          <p className="text-xs text-muted-foreground">Telefon</p>
                          <a 
                            href={`tel:${order.customer_phone}`}
                            className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Phone className="h-4 w-4" />
                            {order.customer_phone}
                          </a>
                        </div>
                      )}
                      <div>
                        <p className="text-xs text-muted-foreground">Teslimat Adresi</p>
                        <p className="text-sm">{formatAddress(order.delivery_address)}</p>
                      </div>
                      {order.delivery_location?.lat && order.delivery_location?.lng && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full bg-blue-100 hover:bg-blue-200"
                          onClick={(e) => {
                            e.stopPropagation();
                            openInMaps(
                              order.delivery_location.lat,
                              order.delivery_location.lng,
                              'Müşteri - Teslimat Noktası'
                            );
                          }}
                        >
                          <Navigation className="h-4 w-4 mr-2" />
                          Müşteriye Git
                        </Button>
                      )}
                    </CardContent>
                  </Card>

                  {/* Order Details */}
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Sipariş Detayları</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Ürün Sayısı:</span>
                        <span className="font-medium">{order.items_count} ürün</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Sipariş Tutarı:</span>
                        <span className="font-medium">₺{order.total_amount?.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Teslimat Ücreti:</span>
                        <span className="font-medium text-green-600">₺{order.delivery_fee?.toFixed(2)}</span>
                      </div>
                      {order.notes && (
                        <div className="pt-2 border-t">
                          <p className="text-xs text-muted-foreground">Not:</p>
                          <p className="text-sm">{order.notes}</p>
                        </div>
                      )}
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
                            {order.payment_method === 'cash' ? 'Kapıda Nakit Ödeme' : 
                             order.payment_method === 'card' ? 'Kredi Kartı (Online Ödendi)' : 
                             order.payment_method === 'cash_on_delivery' ? 'Kapıda Nakit' :
                             'Ödeme Bilgisi Yok'}
                          </p>
                          {order.payment_method === 'cash' && (
                            <p className="text-xs text-yellow-700">
                              ⚠️ Müşteriden ₺{order.grand_total?.toFixed(2)} tahsil edilecek
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Action Buttons */}
                  <div className="space-y-2 pt-2">
                    {order.status === 'assigned' && (
                      <Button
                        className="w-full bg-blue-600 hover:bg-blue-700 text-lg py-6"
                        onClick={(e) => {
                          e.stopPropagation();
                          updateOrderStatus(order.order_id, 'picked_up');
                        }}
                        disabled={actionLoading === order.order_id}
                      >
                        {actionLoading === order.order_id ? (
                          <>🔄 Güncelleniyor...</>
                        ) : (
                          <>
                            <Package className="h-5 w-5 mr-2" />
                            Paketi Aldım
                          </>
                        )}
                      </Button>
                    )}

                    {order.status === 'picked_up' && (
                      <Button
                        className="w-full bg-green-600 hover:bg-green-700 text-lg py-6"
                        onClick={(e) => {
                          e.stopPropagation();
                          updateOrderStatus(order.order_id, 'delivered');
                        }}
                        disabled={actionLoading === order.order_id}
                      >
                        {actionLoading === order.order_id ? (
                          <>🔄 Teslim ediliyor...</>
                        ) : (
                          <>
                            <CheckCircle className="h-5 w-5 mr-2" />
                            Teslim Ettim
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default CourierActiveOrders;
