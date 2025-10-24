import React, { useState, useEffect } from 'react';
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
        body: JSON.stringify({ to: newStatus })
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
        return { 
          label: 'Atandı', 
          bgColor: '#fef3c7', 
          textColor: '#92400e',
          icon: Clock 
        };
      case 'picked_up':
        return { 
          label: 'Alındı', 
          bgColor: '#dbeafe', 
          textColor: '#1e40af',
          icon: Package 
        };
      case 'delivering':
        return { 
          label: 'Teslimat Yolda', 
          bgColor: '#f3e8ff', 
          textColor: '#6b21a8',
          icon: Navigation 
        };
      default:
        return { 
          label: status, 
          bgColor: '#f3f4f6', 
          textColor: '#374151',
          icon: Package 
        };
    }
  };

  if (activeOrders.length === 0) {
    return (
      <div style={{
        border: '1px solid #e5e7eb',
        borderRadius: '0.5rem',
        padding: '3rem',
        textAlign: 'center',
        background: 'white'
      }}>
        <Package size={48} style={{ margin: '0 auto 1rem', opacity: 0.5, color: '#9ca3af' }} />
        <p style={{ fontSize: '1rem', color: '#6b7280', marginBottom: '0.5rem' }}>
          Şu an aktif teslimatınız bulunmuyor
        </p>
        <p style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
          Hazır siparişler sekmesinden sipariş alabilirsiniz
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: 0 }}>
          Aktif Teslimatlarım ({activeOrders.length})
        </h2>
      </div>

      {/* Orders Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {activeOrders.map((order) => {
          const statusInfo = getStatusInfo(order.status);
          const isSelected = selectedOrder?.order_id === order.order_id;

          return (
            <div
              key={order.order_id}
              onClick={() => setSelectedOrder(isSelected ? null : order)}
              style={{
                border: isSelected ? '2px solid #10b981' : '1px solid #e5e7eb',
                borderRadius: '0.5rem',
                padding: '1rem',
                cursor: 'pointer',
                background: 'white',
                boxShadow: isSelected ? '0 4px 6px rgba(0,0,0,0.1)' : 'none',
                transition: 'all 0.2s'
              }}
            >
              {/* Order Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: isSelected ? '1rem' : 0 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <Package size={20} />
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0 }}>
                      Sipariş #{order.order_code}
                    </h3>
                  </div>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    background: statusInfo.bgColor,
                    color: statusInfo.textColor
                  }}>
                    {statusInfo.icon && React.createElement(statusInfo.icon, { size: 12 })}
                    {statusInfo.label}
                  </span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#10b981', margin: 0 }}>
                    ₺{order.grand_total?.toFixed(2)}
                  </p>
                </div>
              </div>
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
