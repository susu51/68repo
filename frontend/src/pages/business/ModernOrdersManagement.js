import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { 
  ShoppingBag, 
  Clock, 
  CheckCircle, 
  XCircle, 
  ChefHat,
  Package,
  Truck,
  Phone,
  MapPin,
  Eye,
  RefreshCw,
  CheckCheck,
  AlertCircle,
  Wifi,
  WifiOff
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { get, patch } from '../../api/http';
import { useOrderNotifications } from '../../hooks/useOrderNotifications';

export const ModernOrdersManagement = ({ businessId }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [stats, setStats] = useState({
    pending: 0,
    preparing: 0,
    ready: 0,
    delivered: 0
  });

  // WebSocket for real-time notifications
  const { isConnected, reconnect } = useOrderNotifications(
    businessId,
    (event) => {
      console.log('🔔 New order event received:', event);
      // Refresh orders when new order arrives
      fetchOrders();
    }
  );

  useEffect(() => {
    fetchOrders();
    // Auto-refresh every 30 seconds as fallback
    const interval = setInterval(fetchOrders, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      
      // Fetch both incoming and active orders
      const [incomingResult, activeResult] = await Promise.all([
        get('/business/orders/incoming').catch(() => ({ data: { orders: [] } })),
        get('/business/orders/active').catch(() => ({ data: { orders: [] } }))
      ]);
      
      // Handle response format - check if data has 'orders' property or is array directly
      const incomingOrders = Array.isArray(incomingResult?.data) 
        ? incomingResult.data 
        : (incomingResult?.data?.orders || []);
      const activeOrders = Array.isArray(activeResult?.data) 
        ? activeResult.data 
        : (activeResult?.data?.orders || []);
      
      const allOrders = [...incomingOrders, ...activeOrders];
      setOrders(allOrders);
      
      // Calculate stats
      const newStats = {
        pending: allOrders.filter(o => ['created', 'pending', 'placed'].includes(o.status)).length,
        preparing: allOrders.filter(o => o.status === 'preparing').length,
        ready: allOrders.filter(o => o.status === 'ready').length,
        confirmed: allOrders.filter(o => o.status === 'confirmed').length
      };
      setStats(newStats);
      
      console.log('✅ Orders loaded:', allOrders.length);
    } catch (error) {
      console.error('❌ Orders loading error:', error);
      toast.error('Siparişler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      await patch(`/business/orders/${orderId}/status`, { status: newStatus });
      toast.success(`Sipariş durumu güncellendi: ${getStatusLabel(newStatus)}`);
      await fetchOrders();
    } catch (error) {
      console.error('❌ Status update error:', error);
      toast.error(error.response?.data?.detail || 'Durum güncellenemedi');
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      'pending': 'Bekliyor',
      'placed': 'Bekliyor',
      'confirmed': 'Onaylandı',
      'preparing': 'Hazırlanıyor',
      'ready': 'Hazır',
      'picked_up': 'Kuryede',
      'delivering': 'Yolda',
      'delivered': 'Teslim Edildi',
      'cancelled': 'İptal'
    };
    return labels[status] || status;
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-orange-100 text-orange-800 dark:bg-orange-900/20',
      'placed': 'bg-orange-100 text-orange-800 dark:bg-orange-900/20',
      'confirmed': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20',
      'preparing': 'bg-purple-100 text-purple-800 dark:bg-purple-900/20',
      'ready': 'bg-green-100 text-green-800 dark:bg-green-900/20',
      'picked_up': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20',
      'delivering': 'bg-teal-100 text-teal-800 dark:bg-teal-900/20',
      'delivered': 'bg-green-100 text-green-800 dark:bg-green-900/20',
      'cancelled': 'bg-red-100 text-red-800 dark:bg-red-900/20'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getNextAction = (status) => {
    if (status === 'pending' || status === 'placed') {
      return { label: 'Onayla', nextStatus: 'confirmed', icon: CheckCheck, color: 'bg-blue-600' };
    }
    if (status === 'confirmed') {
      return { label: 'Hazırlanmaya Başla', nextStatus: 'preparing', icon: ChefHat, color: 'bg-purple-600' };
    }
    if (status === 'preparing') {
      return { label: 'Hazır', nextStatus: 'ready', icon: Package, color: 'bg-green-600' };
    }
    return null;
  };

  const filteredOrders = statusFilter === 'all' 
    ? orders 
    : orders.filter(order => {
        if (statusFilter === 'pending') return ['pending', 'placed'].includes(order.status);
        return order.status === statusFilter;
      });

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground flex items-center gap-2">
            Sipariş Yönetimi
            {/* WebSocket Status Indicator */}
            {isConnected ? (
              <Wifi className="h-5 w-5 text-green-500" title="Canlı bildirimler aktif" />
            ) : (
              <WifiOff className="h-5 w-5 text-gray-400" title="Canlı bildirimler bağlı değil" />
            )}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Siparişlerinizi yönetin ve durumlarını güncelleyin
            {isConnected && <span className="text-green-600 ml-2">• Canlı bildirimler aktif</span>}
          </p>
        </div>
        <div className="flex gap-2">
          {!isConnected && (
            <Button
              onClick={reconnect}
              variant="outline"
              size="sm"
              className="text-orange-600"
            >
              <Wifi className="h-4 w-4 mr-2" />
              Bağlan
            </Button>
          )}
          <Button
            onClick={fetchOrders}
            variant="outline"
            size="sm"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Yenile
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card className={`cursor-pointer transition-all ${statusFilter === 'pending' ? 'ring-2 ring-orange-500' : ''}`}
              onClick={() => setStatusFilter(statusFilter === 'pending' ? 'all' : 'pending')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Bekleyen</p>
                <p className="text-2xl font-bold text-orange-600">{stats.pending}</p>
              </div>
              <div className="p-3 rounded-xl bg-orange-100 dark:bg-orange-900/20">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className={`cursor-pointer transition-all ${statusFilter === 'preparing' ? 'ring-2 ring-purple-500' : ''}`}
              onClick={() => setStatusFilter(statusFilter === 'preparing' ? 'all' : 'preparing')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Hazırlanıyor</p>
                <p className="text-2xl font-bold text-purple-600">{stats.preparing}</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-100 dark:bg-purple-900/20">
                <ChefHat className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className={`cursor-pointer transition-all ${statusFilter === 'ready' ? 'ring-2 ring-green-500' : ''}`}
              onClick={() => setStatusFilter(statusFilter === 'ready' ? 'all' : 'ready')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Hazır</p>
                <p className="text-2xl font-bold text-green-600">{stats.ready}</p>
              </div>
              <div className="p-3 rounded-xl bg-green-100 dark:bg-green-900/20">
                <Package className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className={`cursor-pointer transition-all ${statusFilter === 'confirmed' ? 'ring-2 ring-blue-500' : ''}`}
              onClick={() => setStatusFilter(statusFilter === 'confirmed' ? 'all' : 'confirmed')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Onaylı</p>
                <p className="text-2xl font-bold text-blue-600">{stats.confirmed}</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/20">
                <CheckCircle className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter Pills */}
      <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
        <Button
          variant={statusFilter === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setStatusFilter('all')}
        >
          Tümü ({orders.length})
        </Button>
        <Button
          variant={statusFilter === 'pending' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setStatusFilter('pending')}
        >
          🕐 Bekleyen ({stats.pending})
        </Button>
        <Button
          variant={statusFilter === 'confirmed' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setStatusFilter('confirmed')}
        >
          ✅ Onaylı ({stats.confirmed})
        </Button>
        <Button
          variant={statusFilter === 'preparing' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setStatusFilter('preparing')}
        >
          👨‍🍳 Hazırlanıyor ({stats.preparing})
        </Button>
        <Button
          variant={statusFilter === 'ready' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setStatusFilter('ready')}
        >
          📦 Hazır ({stats.ready})
        </Button>
      </div>

      {/* Orders List */}
      {loading && orders.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Siparişler yükleniyor...</p>
          </CardContent>
        </Card>
      ) : filteredOrders.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <ShoppingBag className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {statusFilter === 'all' ? 'Henüz sipariş yok' : 'Bu kategoride sipariş yok'}
            </h3>
            <p className="text-muted-foreground">
              Yeni siparişler geldiğinde burada görünecek
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredOrders.map((order) => {
            const nextAction = getNextAction(order.status);
            
            return (
              <Card key={order.id} className="card-hover-lift">
                <CardContent className="p-4 sm:p-6">
                  <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                    {/* Left: Order Info */}
                    <div className="flex-1 space-y-3">
                      {/* Customer & Time */}
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-foreground">
                              {order.customer_name || 'Müşteri'}
                            </h3>
                            <Badge className={getStatusColor(order.status)}>
                              {getStatusLabel(order.status)}
                            </Badge>
                          </div>
                          {order.customer_phone && (
                            <div className="flex items-center gap-1 text-sm text-muted-foreground">
                              <Phone className="h-3 w-3" />
                              {order.customer_phone}
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-foreground">
                            ₺{order.total_amount?.toFixed(2)}
                          </p>
                          {order.order_date && (
                            <p className="text-xs text-muted-foreground">
                              {new Date(order.order_date).toLocaleTimeString('tr-TR', {
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Items */}
                      <div className="bg-secondary/50 rounded-lg p-3">
                        <p className="text-xs font-medium text-muted-foreground mb-2">Ürünler:</p>
                        <div className="space-y-1">
                          {order.items?.map((item, idx) => (
                            <div key={idx} className="flex justify-between text-sm">
                              <span>{item.quantity}x {item.product_name || item.name}</span>
                              <span className="font-medium">₺{item.subtotal?.toFixed(2)}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Delivery Address */}
                      {order.delivery_address && (
                        <div className="flex items-start gap-2 text-sm">
                          <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                          <span className="text-muted-foreground">
                            {typeof order.delivery_address === 'string' 
                              ? order.delivery_address 
                              : order.delivery_address.address}
                          </span>
                        </div>
                      )}

                      {/* Notes */}
                      {order.notes && (
                        <div className="flex items-start gap-2 text-sm bg-yellow-50 dark:bg-yellow-900/10 border border-yellow-200 dark:border-yellow-800 rounded-lg p-2">
                          <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                          <span className="text-yellow-800 dark:text-yellow-200">
                            <strong>Not:</strong> {order.notes}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Right: Action Buttons */}
                    <div className="flex flex-col gap-2 lg:w-64">
                      {/* Bekleyen siparişler için onay UI */}
                      {['created', 'pending', 'placed'].includes(order.status) && (
                        <div className="space-y-2">
                          <div>
                            <label className="text-xs font-medium text-muted-foreground mb-1 block">
                              Paket Başı Fiyat (₺)
                            </label>
                            <input
                              type="number"
                              data-testid="unit-fee-input"
                              placeholder="10.00"
                              step="0.50"
                              min="0"
                              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:outline-none"
                              id={`unit-fee-${order.id}`}
                            />
                          </div>
                          <Button
                            data-testid="approve-order-btn"
                            onClick={() => confirmOrder(order.id)}
                            className="w-full bg-green-600 hover:bg-green-700 text-white"
                            size="lg"
                          >
                            <CheckCheck className="h-4 w-4 mr-2" />
                            Onayla
                          </Button>
                        </div>
                      )}
                      
                      {/* Diğer durumlar için normal aksiyon */}
                      {nextAction && !['created', 'pending', 'placed'].includes(order.status) && (
                        <Button
                          onClick={() => updateOrderStatus(order.id, nextAction.nextStatus)}
                          className={`${nextAction.color} hover:opacity-90 text-white`}
                          size="lg"
                        >
                          {React.createElement(nextAction.icon, { className: 'h-4 w-4 mr-2' })}
                          {nextAction.label}
                        </Button>
                      )}
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedOrder(order)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Detay
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Order Details Modal - Always rendered but hidden */}
      <div 
        style={{ display: selectedOrder ? 'flex' : 'none' }}
        className="fixed inset-0 bg-black/50 items-center justify-center p-4 z-50"
        onClick={() => setSelectedOrder(null)}
      >
        {selectedOrder && (
          <Card 
            className="max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Sipariş Detayları</span>
                <Button variant="ghost" size="sm" onClick={() => setSelectedOrder(null)}>✕</Button>
              </CardTitle>
              <CardDescription>
                Sipariş #{selectedOrder.id?.slice(-8)}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Müşteri</p>
                  <p className="font-semibold">{selectedOrder.customer_name}</p>
                  {selectedOrder.customer_phone && (
                    <p className="text-sm text-muted-foreground">{selectedOrder.customer_phone}</p>
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Durum</p>
                  <Badge className={getStatusColor(selectedOrder.status)}>
                    {getStatusLabel(selectedOrder.status)}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Toplam Tutar</p>
                  <p className="text-xl font-bold">₺{selectedOrder.total_amount?.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Ödeme</p>
                  <p className="font-semibold">{selectedOrder.payment_method || 'Nakit'}</p>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Ürünler</p>
                <div className="space-y-2">
                  {selectedOrder.items?.map((item, idx) => (
                    <div key={idx} className="flex justify-between bg-secondary/50 p-3 rounded-lg">
                      <div>
                        <p className="font-medium">{item.product_name || item.name}</p>
                        <p className="text-sm text-muted-foreground">Adet: {item.quantity}</p>
                      </div>
                      <p className="font-semibold">₺{item.subtotal?.toFixed(2)}</p>
                    </div>
                  ))}
                </div>
              </div>

              {selectedOrder.delivery_address && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Teslimat Adresi</p>
                  <div className="bg-secondary/50 p-3 rounded-lg">
                    <p>
                      {typeof selectedOrder.delivery_address === 'string' 
                        ? selectedOrder.delivery_address 
                        : selectedOrder.delivery_address.address}
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};