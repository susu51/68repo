import React, { useState, useEffect, useCallback } from 'react';
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
  WifiOff,
  Printer
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { get, patch } from '../../api/http';
import { useOrderNotifications } from '../../hooks/useOrderNotifications';

export const ModernOrdersManagement = ({ businessId }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(0);
  const [stats, setStats] = useState({
    pending: 0,
    preparing: 0,
    ready: 0,
    delivered: 0
  });

  // Define fetchOrders early so it can be used in callbacks
  const fetchOrders = useCallback(async () => {
    // Debounce: Don't fetch if called within last 2 seconds
    const now = Date.now();
    if (now - lastFetchTime < 2000) {
      console.log('⏭️ Skipping fetch - too soon since last fetch');
      return;
    }
    
    try {
      setLoading(true);
      setLastFetchTime(now);
      
      console.log('🔄 Fetching ALL orders from business API...');
      
      // Fetch incoming orders (pending/placed)
      const incomingResponse = await get('/business/orders/incoming');
      console.log('📡 Incoming orders response:', incomingResponse);
      
      // Try to fetch active orders (confirmed, preparing, ready) - if fails, continue with incoming only
      let activeResponse = null;
      try {
        activeResponse = await get('/business/orders/active');
        console.log('📡 Active orders response:', activeResponse);
      } catch (activeError) {
        console.warn('⚠️ Could not fetch active orders, using incoming only:', activeError.message);
      }
      
      // Parse response - backend returns array directly
      let incomingOrders = [];
      if (incomingResponse) {
        if (Array.isArray(incomingResponse)) {
          incomingOrders = incomingResponse;
        } else if (Array.isArray(incomingResponse.data)) {
          incomingOrders = incomingResponse.data;
        } else if (incomingResponse.data?.orders) {
          incomingOrders = incomingResponse.data.orders;
        }
      }
      
      // Parse active orders
      let activeOrders = [];
      if (activeResponse) {
        if (Array.isArray(activeResponse)) {
          activeOrders = activeResponse;
        } else if (Array.isArray(activeResponse.data)) {
          activeOrders = activeResponse.data;
        } else if (activeResponse.data?.orders) {
          activeOrders = activeResponse.data.orders;
        }
      }
      
      console.log(`✅ Found ${incomingOrders.length} incoming + ${activeOrders.length} active orders`);
      
      // Merge and deduplicate orders
      const allOrders = [...incomingOrders, ...activeOrders];
      const uniqueOrders = Array.from(new Map(allOrders.map(o => [o.id, o])).values());
      
      // Set orders
      setOrders(uniqueOrders);
      
      // Calculate stats from unique orders
      const newStats = {
        pending: uniqueOrders.filter(o => ['created', 'pending', 'placed'].includes(o.status)).length,
        preparing: uniqueOrders.filter(o => o.status === 'preparing').length,
        ready: uniqueOrders.filter(o => o.status === 'ready').length,
        confirmed: uniqueOrders.filter(o => o.status === 'confirmed').length,
        delivered: uniqueOrders.filter(o => o.status === 'delivered').length
      };
      setStats(newStats);
      
      console.log('✅ Orders loaded:', uniqueOrders.length, 'Stats:', newStats);
    } catch (error) {
      console.error('❌ Orders loading error:', error);
      toast.error('Siparişler yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, []); // Empty deps - fetchOrders doesn't depend on any props/state

  // WebSocket callback - memoized to prevent infinite re-renders
  const handleNewOrder = useCallback((event) => {
    console.log('🔔 New order event received:', event);
    
    // Play notification sound
    try {
      import('../../utils/notificationSound').then(module => {
        module.default();
      });
    } catch (e) {
      console.log('Audio notification failed:', e);
    }
    
    // Show toast
    toast.success('🆕 Yeni Sipariş Alındı!', {
      duration: 5000,
      icon: '🔔'
    });
    
    // Refresh orders when new order arrives
    fetchOrders();
  }, [fetchOrders]);

  // WebSocket for real-time notifications (enabled only when businessId exists)
  const { isConnected, reconnect } = useOrderNotifications(
    businessId,
    handleNewOrder,
    !!businessId  // enabled: only when businessId exists
  );

  useEffect(() => {
    fetchOrders();
    // Auto-refresh every 50 seconds - background update without page reload
    const interval = setInterval(fetchOrders, 50000);
    return () => clearInterval(interval);
  }, [fetchOrders]);

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      console.log(`🔄 Updating order ${orderId} to status: ${newStatus}`);
      
      // Simple status update - no courier task creation
      await patch(`/orders/${orderId}/status`, { to: newStatus });
      
      // Custom messages
      if (newStatus === 'ready') {
        toast.success('Sipariş HAZIR durumuna geçti! Kuryelere açıldı.', {
          duration: 3000,
          icon: '✅'
        });
      } else {
        toast.success(`Sipariş durumu güncellendi: ${getStatusLabel(newStatus)}`);
      }
      
      await fetchOrders();
    } catch (error) {
      console.error('❌ Status update error:', error);
      toast.error('Durum güncellenemedi');
    }
  };

  const confirmOrder = async (orderId) => {
    try {
      console.log('🎯 Confirming order (just status, no courier yet):', orderId);
      
      // Simply update status to 'confirmed'
      await patch(`/orders/${orderId}/status`, { to: 'confirmed' });
      
      toast.success('Sipariş onaylandı! Hazırlanmaya başlayabilirsiniz.', {
        duration: 3000,
        icon: '✅'
      });
      
      // Refresh orders
      await fetchOrders();
    } catch (error) {
      console.error('❌ Confirm order error:', error);
      toast.error('Sipariş onaylanamadı');
    }
  };

  const printReceipt = (order) => {
    try {
      // Create a hidden iframe for printing
      const printFrame = document.createElement('iframe');
      printFrame.style.position = 'fixed';
      printFrame.style.right = '0';
      printFrame.style.bottom = '0';
      printFrame.style.width = '0';
      printFrame.style.height = '0';
      printFrame.style.border = 'none';
      document.body.appendChild(printFrame);
      
      const doc = printFrame.contentWindow.document;
      
      // Generate receipt HTML
      const receiptHTML = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Sipariş Fişi #${order.id?.slice(-8)}</title>
          <style>
            @media print {
              @page { margin: 0.5cm; size: 80mm auto; }
              body { margin: 0; }
            }
            body {
              font-family: 'Courier New', monospace;
              font-size: 12px;
              line-height: 1.4;
              max-width: 80mm;
              margin: 0 auto;
              padding: 10px;
            }
            h1 { font-size: 18px; text-align: center; margin: 10px 0; font-weight: bold; }
            h2 { font-size: 14px; margin: 10px 0; font-weight: bold; border-bottom: 2px dashed #000; padding-bottom: 5px; }
            .header { text-align: center; margin-bottom: 15px; border-bottom: 2px solid #000; padding-bottom: 10px; }
            .info { margin: 8px 0; }
            .label { font-weight: bold; }
            .items { margin: 10px 0; }
            .item { display: flex; justify-content: space-between; margin: 5px 0; padding: 3px 0; }
            .item-name { flex: 1; }
            .item-qty { width: 40px; text-align: center; }
            .item-price { width: 60px; text-align: right; }
            .total { border-top: 2px solid #000; border-bottom: 2px solid #000; padding: 8px 0; margin: 10px 0; font-size: 14px; font-weight: bold; }
            .footer { text-align: center; margin-top: 15px; font-size: 10px; border-top: 2px dashed #000; padding-top: 10px; }
            .divider { border-bottom: 1px dashed #000; margin: 8px 0; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>🍽️ SİPARİŞ FİŞİ</h1>
            <div style="font-size: 10px;">Sipariş #${order.id?.slice(-8) || 'N/A'}</div>
            <div style="font-size: 10px;">${new Date(order.order_date || Date.now()).toLocaleString('tr-TR')}</div>
          </div>

          <div class="info">
            <div><span class="label">Müşteri:</span> ${order.customer_name || 'Müşteri'}</div>
            ${order.customer_phone ? `<div><span class="label">Telefon:</span> ${order.customer_phone}</div>` : ''}
            ${order.delivery_address ? `<div><span class="label">Adres:</span> ${typeof order.delivery_address === 'string' ? order.delivery_address : order.delivery_address.address}</div>` : ''}
            <div><span class="label">Ödeme:</span> ${order.payment_method === 'card' ? 'Kart' : 'Nakit'}</div>
            <div><span class="label">Durum:</span> ${getStatusLabel(order.status)}</div>
          </div>

          <div class="divider"></div>

          <h2>ÜRÜNLER</h2>
          <div class="items">
            ${order.items?.map(item => `
              <div class="item">
                <span class="item-name">${item.product_name || item.name}</span>
                <span class="item-qty">${item.quantity}x</span>
                <span class="item-price">₺${item.subtotal?.toFixed(2)}</span>
              </div>
            `).join('') || '<div>Ürün bulunamadı</div>'}
          </div>

          <div class="divider"></div>

          ${order.notes ? `
            <div class="info">
              <div><span class="label">Not:</span> ${order.notes}</div>
            </div>
            <div class="divider"></div>
          ` : ''}

          <div class="total">
            <div style="display: flex; justify-content: space-between;">
              <span>TOPLAM:</span>
              <span>₺${order.total_amount?.toFixed(2)}</span>
            </div>
          </div>

          <div class="footer">
            <div>Afiyet olsun! 🙏</div>
            <div style="margin-top: 5px;">Kuryecini - Hızlı Teslimat</div>
          </div>
        </body>
        </html>
      `;
      
      doc.open();
      doc.write(receiptHTML);
      doc.close();
      
      // Wait for content to load then print
      printFrame.contentWindow.onload = () => {
        setTimeout(() => {
          printFrame.contentWindow.print();
          setTimeout(() => {
            document.body.removeChild(printFrame);
          }, 100);
        }, 250);
      };
      
      toast.success('Fiş yazdırılıyor...');
    } catch (error) {
      console.error('❌ Print error:', error);
      toast.error('Yazdırma hatası');
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
        if (statusFilter === 'pending') return ['pending', 'placed', 'created'].includes(order.status);
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

      {/* Stats Cards - Order: Bekleyen → Onaylı → Hazır (preparing kaldırıldı) */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {/* 1. Bekleyen */}
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
        
        {/* 2. Onaylı */}
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
        
        {/* 3. Hazır */}
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
                      {/* Bekleyen siparişler için onay butonu (sadece durum değişir) */}
                      {['created', 'pending', 'placed'].includes(order.status) && (
                        <Button
                          data-testid="approve-order-btn"
                          onClick={() => confirmOrder(order.id)}
                          className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                          size="lg"
                        >
                          <CheckCheck className="h-4 w-4 mr-2" />
                          Onayla
                        </Button>
                      )}
                      
                      {/* Onaylı siparişler için hazırlanmaya başla - direkt READY olur */}
                      {order.status === 'confirmed' && (
                        <Button
                          data-testid="start-preparing-btn"
                          onClick={() => updateOrderStatus(order.id, 'ready')}
                          className="w-full bg-green-600 hover:bg-green-700 text-white"
                          size="lg"
                        >
                          <Package className="h-4 w-4 mr-2" />
                          Hazırlanmaya Başla
                        </Button>
                      )}
                      
                      {/* Ready durumunda bilgi mesajı */}
                      {order.status === 'ready' && (
                        <div className="w-full p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                          <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                            <CheckCircle className="h-5 w-5" />
                            <span className="text-sm font-medium">Sipariş hazır - Kurye bekleyebilir</span>
                          </div>
                        </div>
                      )}
                      
                      <div className="grid grid-cols-2 gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedOrder(order)}
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          Detay
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => printReceipt(order)}
                        >
                          <Printer className="h-4 w-4 mr-1" />
                          Yazdır
                        </Button>
                      </div>
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
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>Sipariş Detayları</CardTitle>
                  <CardDescription>Sipariş #{selectedOrder.id?.slice(-8)}</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => printReceipt(selectedOrder)}
                    className="gap-2"
                  >
                    <Printer className="h-4 w-4" />
                    Yazdır
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setSelectedOrder(null)}>✕</Button>
                </div>
              </div>
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

// Wrap with React.memo to prevent unnecessary re-renders
export default React.memo(ModernOrdersManagement);