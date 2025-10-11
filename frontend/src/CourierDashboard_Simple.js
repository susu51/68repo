import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import toast from 'react-hot-toast';

// Use new VITE environment variable  
const API_BASE = import.meta.env.VITE_API_BASE_URL;

export const CourierDashboard = ({ user, onLogout }) => {
  // Navigation state
  const [currentView, setCurrentView] = useState('orders');
  const [loading, setLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(user?.is_online || false);
  
  // Orders states
  const [availableOrders, setAvailableOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [currentOrder, setCurrentOrder] = useState(null);
  
  // Notifications and messages
  const [notifications, setNotifications] = useState([]);
  const [messages, setMessages] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Filters
  const [historyFilter, setHistoryFilter] = useState({
    status: 'all',
    date: 'all'
  });

  // Stats
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalEarnings: 0,
    monthlyOrders: 0,
    monthlyEarnings: 0
  });

  useEffect(() => {
    fetchInitialData();
    const interval = setInterval(fetchAvailableOrders, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchInitialData = async () => {
    await Promise.all([
      fetchAvailableOrders(),
      fetchOrderHistory(),
      fetchNotifications(),
      fetchMessages(),
      fetchStats()
    ]);
  };

  // Fetch available orders
  const fetchAvailableOrders = async () => {
    try {
      const response = await axios.get(`${API}/courier/orders/available`);
      setAvailableOrders(response.data.orders || []);
    } catch (error) {
      console.error('Failed to fetch available orders:', error);
    }
  };

  // Fetch order history
  const fetchOrderHistory = async () => {
    try {
      const params = {};
      if (historyFilter.status !== 'all') params.status_filter = historyFilter.status;
      if (historyFilter.date !== 'all') params.date_filter = historyFilter.date;
      
      const response = await axios.get(`${API}/courier/orders/history`, { params });
      setOrderHistory(response.data.orders || []);
    } catch (error) {
      console.error('Failed to fetch order history:', error);
    }
  };

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/courier/notifications`);
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.notifications?.filter(n => !n.read).length || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  };

  // Fetch messages
  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/courier/messages`);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/courier/stats`);
      setStats(response.data || {
        totalOrders: 0,
        totalEarnings: 0,
        monthlyOrders: 0,
        monthlyEarnings: 0
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // Accept order
  const acceptOrder = async (orderId) => {
    setLoading(true);
    try {
      await axios.post(`${API}/courier/orders/${orderId}/accept`);
      toast.success('Sipariş kabul edildi!');
      fetchAvailableOrders();
      setCurrentOrder(availableOrders.find(o => o.id === orderId));
    } catch (error) {
      toast.error('Sipariş kabul edilemedi');
    }
    setLoading(false);
  };

  // Update order status
  const updateOrderStatus = async (orderId, newStatus) => {
    setLoading(true);
    try {
      await axios.post(`${API}/courier/orders/${orderId}/update-status`, {
        status: newStatus
      });
      
      const statusMessages = {
        'picked_up': 'Sipariş alındı olarak işaretlendi',
        'delivered': 'Sipariş teslim edildi!'
      };
      
      toast.success(statusMessages[newStatus] || 'Durum güncellendi');
      
      if (newStatus === 'delivered') {
        setCurrentOrder(null);
      } else {
        setCurrentOrder(prev => ({ ...prev, status: newStatus }));
      }
      
      fetchOrderHistory();
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
    setLoading(false);
  };

  // Toggle online status
  const toggleOnlineStatus = async () => {
    try {
      const response = await axios.post(`${API}/courier/status/toggle`);
      setIsOnline(response.data.is_online);
      toast.success(response.data.message || 'Durum güncellendi');
    } catch (error) {
      toast.error('Durum değiştirilemedi');
    }
  };

  // Mark notification as read
  const markNotificationRead = async (notificationId) => {
    try {
      await axios.post(`${API}/courier/notifications/${notificationId}/read`);
      fetchNotifications();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Generate monthly report
  const generateMonthlyReport = async () => {
    try {
      const response = await axios.get(`${API}/courier/monthly-report`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `kurye-rapor-${new Date().getMonth() + 1}-${new Date().getFullYear()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Aylık rapor indirildi');
    } catch (error) {
      toast.error('Rapor oluşturulamadı');
    }
  };

  // Navigation items
  const navigationItems = [
    { id: 'orders', label: '📋 Siparişler', icon: '📋' },
    { id: 'history', label: '📊 Geçmiş', icon: '📊' },
    { id: 'notifications', label: '🔔 Bildirimler', icon: '🔔', badge: unreadCount },
    { id: 'messages', label: '💬 Mesajlar', icon: '💬' },
    { id: 'stats', label: '📈 İstatistikler', icon: '📈' }
  ];

  const renderHeader = () => (
    <div className="bg-white shadow-sm border-b p-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-900">Kurye Paneli</h1>
          <Badge className="bg-orange-100 text-orange-800">
            {user?.name || 'Kurye'}
          </Badge>
        </div>
        <div className="flex items-center space-x-4">
          {/* Online/Offline Toggle */}
          <Button
            onClick={toggleOnlineStatus}
            disabled={loading}
            className={`${isOnline 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-gray-600 hover:bg-gray-700'
            } text-white`}
            size="sm"
          >
            {isOnline ? '🟢 Çevrimiçi' : '🔴 Çevrimdışı'}
          </Button>
          
          {/* Notifications Badge */}
          <div className="relative">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setCurrentView('notifications')}
            >
              🔔
              {unreadCount > 0 && (
                <Badge className="absolute -top-2 -right-2 bg-red-500 text-white min-w-5 h-5 flex items-center justify-center text-xs">
                  {unreadCount}
                </Badge>
              )}
            </Button>
          </div>
          
          <Button onClick={onLogout} variant="outline" size="sm">
            Çıkış
          </Button>
        </div>
      </div>
    </div>
  );

  const renderNavbar = () => (
    <div className="bg-gray-50 border-b">
      <div className="max-w-7xl mx-auto">
        <nav className="flex space-x-1 p-2">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors relative ${
                currentView === item.id
                  ? 'bg-orange-100 text-orange-800 border border-orange-200'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <span className="mr-2">{item.icon}</span>
              {item.label}
              {item.badge > 0 && (
                <Badge className="ml-2 bg-red-500 text-white text-xs">
                  {item.badge}
                </Badge>
              )}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );

  const renderOrders = () => (
    <div className="space-y-6">
      {/* Current Order Status */}
      {currentOrder && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <span>📦</span>
              <span>Mevcut Sipariş</span>
              <Badge variant="secondary">{currentOrder.status}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p><strong>İşletme:</strong> {currentOrder.business_name}</p>
                <p><strong>Teslimat Adresi:</strong> {currentOrder.delivery_address}</p>
                <p><strong>Tutar:</strong> ₺{currentOrder.total_amount}</p>
                <p><strong>Komisyon:</strong> ₺{currentOrder.commission}</p>
              </div>
              <div className="flex flex-col space-y-2">
                {currentOrder.status === 'accepted' && (
                  <Button 
                    onClick={() => updateOrderStatus(currentOrder.id, 'picked_up')}
                    className="bg-orange-600 hover:bg-orange-700"
                    disabled={loading}
                  >
                    📤 Siparişi Aldım
                  </Button>
                )}
                {currentOrder.status === 'picked_up' && (
                  <Button 
                    onClick={() => updateOrderStatus(currentOrder.id, 'delivered')}
                    className="bg-green-600 hover:bg-green-700"
                    disabled={loading}
                  >
                    ✅ Teslim Ettim
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Mevcut Siparişler</h2>
        <Button onClick={fetchAvailableOrders} variant="outline" size="sm">
          🔄 Yenile
        </Button>
      </div>

      {availableOrders.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-gray-500 text-lg mb-4">Şu anda mevcut sipariş bulunmuyor</p>
            <p className="text-sm text-gray-400">
              {isOnline ? 'Yeni siparişler geldiğinde burada görünecek' : 'Sipariş almak için çevrimiçi olmalısınız'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {availableOrders.map((order) => (
            <Card key={order.id}>
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="font-semibold text-lg">{order.business_name}</h3>
                      <Badge variant="secondary">₺{order.total_amount}</Badge>
                    </div>
                    <p className="text-gray-600 mb-2">📍 {order.delivery_address}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>📏 {order.distance || 'Hesaplanıyor'}km</span>
                      <span>⏱️ ~{order.estimated_time || '20'} dk</span>
                      <span>💰 Komisyon: ₺{order.commission}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <Button 
                      onClick={() => acceptOrder(order.id)}
                      disabled={loading}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      ✅ Kabul Et
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const renderHistory = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Sipariş Geçmişi</h2>
        <div className="flex space-x-2">
          <Select 
            value={historyFilter.status} 
            onValueChange={(value) => setHistoryFilter(prev => ({ ...prev, status: value }))}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tüm Durumlar</SelectItem>
              <SelectItem value="delivered">Teslim Edildi</SelectItem>
              <SelectItem value="cancelled">İptal Edildi</SelectItem>
            </SelectContent>
          </Select>
          <Select 
            value={historyFilter.date} 
            onValueChange={(value) => setHistoryFilter(prev => ({ ...prev, date: value }))}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tüm Zamanlar</SelectItem>
              <SelectItem value="today">Bugün</SelectItem>
              <SelectItem value="week">Bu Hafta</SelectItem>
              <SelectItem value="month">Bu Ay</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchOrderHistory} variant="outline" size="sm">
            🔍 Filtrele
          </Button>
        </div>
      </div>

      <div className="grid gap-4">
        {orderHistory.map((order) => (
          <Card key={order.id}>
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-medium">{order.business_name}</span>
                    <Badge 
                      variant={order.status === 'delivered' ? 'default' : 'secondary'}
                      className={order.status === 'delivered' ? 'bg-green-100 text-green-800' : ''}
                    >
                      {order.status === 'delivered' ? 'Teslim Edildi' : order.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600">
                    {new Date(order.created_at).toLocaleDateString('tr-TR')} • 
                    ₺{order.total_amount} • Komisyon: ₺{order.commission}
                  </p>
                </div>
                <Button variant="outline" size="sm">
                  Detay
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderNotifications = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Bildirimler</h2>
      
      {notifications.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-gray-500">Henüz bildiriminiz bulunmuyor</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <Card 
              key={notification.id} 
              className={notification.read ? 'bg-gray-50' : 'bg-blue-50 border-blue-200'}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-medium">{notification.title}</h3>
                    <p className="text-gray-600 mt-1">{notification.message}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {new Date(notification.created_at).toLocaleString('tr-TR')}
                    </p>
                  </div>
                  {!notification.read && (
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => markNotificationRead(notification.id)}
                    >
                      Okundu
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const renderMessages = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Admin Mesajları</h2>
      
      {messages.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-gray-500">Henüz mesajınız bulunmuyor</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {messages.map((message) => (
            <Card key={message.id}>
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="bg-orange-100 p-2 rounded-full">
                    <span className="text-orange-600">📢</span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium">{message.title}</h3>
                    <p className="text-gray-600 mt-1">{message.message}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      Admin • {new Date(message.created_at).toLocaleString('tr-TR')}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const renderStats = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">İstatistikler & Raporlar</h2>
        <Button onClick={generateMonthlyReport} variant="outline">
          📄 Aylık Rapor İndir
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Toplam İstatistikler</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Toplam Sipariş</span>
              <Badge variant="secondary">{stats.totalOrders}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Toplam Kazanç</span>
              <Badge className="bg-green-100 text-green-800">₺{stats.totalEarnings}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Ortalama Sipariş</span>
              <Badge variant="secondary">
                ₺{stats.totalOrders > 0 ? (stats.totalEarnings / stats.totalOrders).toFixed(2) : '0.00'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Bu Ay</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Aylık Sipariş</span>
              <Badge variant="secondary">{stats.monthlyOrders}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Aylık Kazanç</span>
              <Badge className="bg-green-100 text-green-800">₺{stats.monthlyEarnings}</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Net Kazanç (%5 komisyon)</span>
              <Badge className="bg-blue-100 text-blue-800">
                ₺{(stats.monthlyEarnings * 0.95).toFixed(2)}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Komisyon Bilgisi</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">
              • Her siparişten %5 komisyon alınır
            </p>
            <p className="text-sm text-gray-600 mb-2">
              • Kazançlar haftalık olarak hesabınıza aktarılır
            </p>
            <p className="text-sm text-gray-600">
              • Detaylı rapor için "Aylık Rapor İndir" butonunu kullanın
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderContent = () => {
    switch (currentView) {
      case 'orders': return renderOrders();
      case 'history': return renderHistory();
      case 'notifications': return renderNotifications();
      case 'messages': return renderMessages();
      case 'stats': return renderStats();
      default: return renderOrders();
    }
  };

  if (loading && currentView === 'orders') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {renderHeader()}
      {renderNavbar()}
      <div className="max-w-7xl mx-auto p-6">
        {renderContent()}
      </div>
    </div>
  );
};

export default CourierDashboard;