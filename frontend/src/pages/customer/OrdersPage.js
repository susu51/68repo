import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Package, MapPin, Clock, Star, RefreshCw } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { RatingModal } from '../../components/RatingModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://courier-dashboard-3.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

const STATUS_CONFIG = {
  created: { label: 'Oluşturuldu', color: 'bg-gray-500', icon: '📝' },
  confirmed: { label: 'Onaylandı', color: 'bg-blue-500', icon: '✅' },
  preparing: { label: 'Hazırlanıyor', color: 'bg-yellow-500', icon: '👨‍🍳' },
  ready_for_pickup: { label: 'Teslim Alınmayı Bekliyor', color: 'bg-orange-500', icon: '📦' },
  picked_up: { label: 'Kuryede', color: 'bg-purple-500', icon: '🚚' },
  delivering: { label: 'Yolda', color: 'bg-indigo-500', icon: '🛵' },
  delivered: { label: 'Teslim Edildi', color: 'bg-green-500', icon: '✅' },
  cancelled: { label: 'İptal Edildi', color: 'bg-red-500', icon: '❌' }
};

const OrdersPage = ({ user }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showRatingModal, setShowRatingModal] = useState(false);
  const [ratingOrder, setRatingOrder] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchOrders();

    // Auto-refresh every 10 seconds
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchOrders, 10000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${API}/orders/my`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        // Backend returns array directly, not wrapped in {orders: [...]}
        const ordersData = Array.isArray(data) ? data : (data.orders || []);
        console.log('✅ Orders loaded:', ordersData.length, ordersData);
        setOrders(ordersData);
      } else {
        console.error('❌ Orders API error:', response.status, response.statusText);
        toast.error('Siparişler yüklenemedi');
      }
    } catch (error) {
      console.error('❌ Siparişler yüklenemedi:', error);
      toast.error('Siparişler yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleOrderClick = (order) => {
    setSelectedOrder(selectedOrder?._id === order._id ? null : order);
  };

  const handleRateOrder = (order) => {
    setRatingOrder(order);
    setShowRatingModal(true);
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Siparişi iptal etmek istediğinizden emin misiniz?')) return;

    try {
      const response = await fetch(`${API}/orders/${orderId}/cancel`, {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success('Sipariş iptal edildi');
        fetchOrders();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Sipariş iptal edilemedi');
      }
    } catch (error) {
      console.error('İptal hatası:', error);
      toast.error('Bir hata oluştu');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Siparişlerim</h1>
          <p className="text-gray-600">Toplam {orders.length} sipariş</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchOrders}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Yenile
        </Button>
      </div>

      {/* Empty State */}
      {orders.length === 0 && (
        <Card>
          <CardContent className="py-16 text-center">
            <Package className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Henüz siparişiniz yok
            </h3>
            <p className="text-gray-600">
              Restoranları keşfet ve ilk siparişini ver!
            </p>
          </CardContent>
        </Card>
      )}

      {/* Orders List */}
      <div className="space-y-4">
        {orders.map((order) => {
          const statusInfo = STATUS_CONFIG[order.status] || STATUS_CONFIG.created;
          const isExpanded = selectedOrder?._id === order._id;

          return (
            <Card
              key={order._id}
              className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleOrderClick(order)}
            >
              <CardContent className="p-4">
                {/* Order Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">{statusInfo.icon}</span>
                      <Badge className={`${statusInfo.color} text-white`}>
                        {statusInfo.label}
                      </Badge>
                    </div>
                    <h3 className="font-semibold text-lg">
                      {order.business?.name || 'Restoran'}
                    </h3>
                    <p className="text-sm text-gray-600">
                      Sipariş #{order._id?.slice(-6).toUpperCase()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-orange-600">
                      ₺{order.total_amount?.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(order.created_at).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>

                {/* Order Items */}
                <div className="border-t pt-3">
                  <p className="text-sm text-gray-700">
                    {order.items?.length || 0} ürün
                  </p>
                  {isExpanded && (
                    <div className="mt-2 space-y-1">
                      {order.items?.map((item, idx) => (
                        <p key={idx} className="text-sm text-gray-600">
                          • {item.title || item.name} x{item.quantity}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Delivery Address */}
                {isExpanded && order.delivery_address && (
                  <div className="border-t mt-3 pt-3">
                    <div className="flex items-start gap-2">
                      <MapPin className="h-4 w-4 text-gray-500 mt-1" />
                      <div>
                        <p className="text-sm font-medium">Teslimat Adresi</p>
                        <p className="text-sm text-gray-600">
                          {order.delivery_address.address || order.delivery_address.text}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                {isExpanded && (
                  <div className="border-t mt-3 pt-3 flex gap-2">
                    {order.status === 'delivered' && (
                      <Button
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRateOrder(order);
                        }}
                      >
                        <Star className="h-4 w-4 mr-2" />
                        Değerlendir
                      </Button>
                    )}
                    {['created', 'confirmed'].includes(order.status) && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCancelOrder(order._id);
                        }}
                      >
                        İptal Et
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Rating Modal */}
      {showRatingModal && ratingOrder && (
        <RatingModal
          order={ratingOrder}
          onClose={() => {
            setShowRatingModal(false);
            setRatingOrder(null);
            fetchOrders();
          }}
        />
      )}
    </div>
  );
};

export default OrdersPage;
