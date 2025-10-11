import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import toast from 'react-hot-toast';

// Use new VITE environment variable
const API_BASE = import.meta.env.VITE_API_BASE_URL;

export const CourierDashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('orders');
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
      setUnreadCount(response.data.unread_count || 0);
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

  // Toggle online status
  const toggleOnlineStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/courier/status/toggle`);
      setIsOnline(response.data.is_online);
      toast.success(response.data.message);
      
      if (response.data.is_online) {
        fetchAvailableOrders();
      }
    } catch (error) {
      toast.error('Durum değiştirilemedi');
    }
    setLoading(false);
  };

  // Accept order
  const acceptOrder = async (orderId) => {
    try {
      setLoading(true);
      await axios.post(`${API}/courier/orders/${orderId}/accept`);
      toast.success('Sipariş kabul edildi!');
      
      // Find the accepted order and set as current
      const acceptedOrder = availableOrders.find(order => order.id === orderId);
      if (acceptedOrder) {
        setCurrentOrder({ ...acceptedOrder, status: 'accepted' });
      }
      
      fetchAvailableOrders();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sipariş kabul edilemedi');
    }
    setLoading(false);
  };

  // Update order status
  const updateOrderStatus = async (orderId, status, notes = '') => {
    try {
      setLoading(true);
      await axios.post(`${API}/courier/orders/${orderId}/update-status`, {
        status,
        notes,
        location: null // Could add GPS coordinates here
      });
      
      const statusMessages = {
        'picked_up': 'Sipariş alındı!',
        'delivered': 'Sipariş teslim edildi!'
      };
      
      toast.success(statusMessages[status]);
      
      if (status === 'delivered') {
        setCurrentOrder(null);
      } else {
        setCurrentOrder(prev => ({ ...prev, status }));
      }
      
      fetchOrderHistory();
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
    setLoading(false);
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

  // Auto-refresh data
  useEffect(() => {
    if (isOnline) {
      fetchAvailableOrders();
    }
    fetchOrderHistory();
    fetchNotifications(); 
    fetchMessages();

    // Set up intervals for real-time updates
    const intervals = [];
    
    if (isOnline) {
      intervals.push(setInterval(fetchAvailableOrders, 30000)); // Every 30 seconds
    }
    
    intervals.push(setInterval(fetchNotifications, 60000)); // Every minute
    intervals.push(setInterval(fetchMessages, 120000)); // Every 2 minutes

    return () => {
      intervals.forEach(interval => clearInterval(interval));
    };
  }, [isOnline, historyFilter]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <div className="bg-white/70 backdrop-blur-lg border-b border-gray-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="text-2xl">🚚</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Kurye Paneli</h1>
                <p className="text-sm text-gray-600">
                  Hoş geldin, {user?.first_name} {user?.last_name}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Online/Offline Toggle */}
              <div className="flex items-center space-x-2">
                <Button
                  onClick={toggleOnlineStatus}
                  disabled={loading}
                  className={`${isOnline 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-gray-600 hover:bg-gray-700'
                  } text-white`}
                >
                  {isOnline ? '🟢 Çevrimiçi' : '🔴 Çevrimdışı'}
                </Button>
              </div>
              
              {/* Notifications Badge */}
              <div className="relative">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setActiveTab('notifications')}
                >
                  🔔
                  {unreadCount > 0 && (
                    <Badge className="absolute -top-2 -right-2 bg-red-500 text-white min-w-5 h-5 flex items-center justify-center text-xs">
                      {unreadCount}
                    </Badge>
                  )}
                </Button>
              </div>
              
              <Button onClick={onLogout} variant="outline">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Current Order Status */}
        {currentOrder && (
          <Card className="mb-6 border-blue-200 bg-blue-50">
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

        {/* Tabs Navigation */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="orders">📋 Siparişler</TabsTrigger>
            <TabsTrigger value="history">📊 Geçmiş</TabsTrigger>
            <TabsTrigger value="notifications">
              🔔 Bildirimler
              {unreadCount > 0 && (
                <Badge className="ml-1 bg-red-500">{unreadCount}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="messages">💬 Mesajlar</TabsTrigger>
            <TabsTrigger value="stats">📈 İstatistikler</TabsTrigger>
          </TabsList>

          {/* Available Orders Tab */}
          <TabsContent value="orders" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Mevcut Siparişler</h2>
              <Button onClick={fetchAvailableOrders} variant="outline">
                🔄 Yenile
              </Button>
            </div>

            {!isOnline ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-4xl mb-4">🔴</div>
                  <h3 className="text-lg font-semibold mb-2">Çevrimdışı Durumdasınız</h3>
                  <p className="text-gray-600 mb-4">
                    Sipariş almak için çevrimiçi olmanız gerekiyor.
                  </p>
                  <Button onClick={toggleOnlineStatus} className="bg-green-600 hover:bg-green-700">
                    🟢 Çevrimiçi Ol
                  </Button>
                </CardContent>
              </Card>
            ) : availableOrders.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-4xl mb-4">📭</div>
                  <h3 className="text-lg font-semibold mb-2">Şu An Sipariş Yok</h3>
                  <p className="text-gray-600">
                    Yeni siparişler geldiğinde burada görünecek.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {availableOrders.map((order) => (
                  <Card key={order.id} className="hover:shadow-lg transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="font-semibold">{order.business_name}</h4>
                          <p className="text-sm text-gray-600">{order.business_address}</p>
                        </div>
                        <Badge className="bg-green-100 text-green-800">
                          ₺{order.commission} komisyon
                        </Badge>
                      </div>
                      
                      <div className="space-y-2 text-sm">
                        <p><strong>Teslimat:</strong> {order.delivery_address}</p>
                        <p><strong>Tutar:</strong> ₺{order.total_amount}</p>
                        <p><strong>Mesafe:</strong> {order.estimated_distance}</p>
                        <p><strong>Hazırlık:</strong> ~{order.estimated_prep_time} dk</p>
                      </div>
                      
                      <Button 
                        onClick={() => acceptOrder(order.id)}
                        disabled={loading}
                        className="w-full mt-4 bg-blue-600 hover:bg-blue-700"
                      >
                        ✅ Siparişi Kabul Et
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Order History Tab */}
          <TabsContent value="history" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Sipariş Geçmişi</h2>
              <div className="flex space-x-2">
                <Select 
                  value={historyFilter.status} 
                  onValueChange={(value) => setHistoryFilter({...historyFilter, status: value})}
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
                  onValueChange={(value) => setHistoryFilter({...historyFilter, date: value})}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tüm Zamanlar</SelectItem>
                    <SelectItem value="today">Bugün</SelectItem>
                    <SelectItem value="week">Bu Hafta</SelectItem>
                    <SelectItem value="month">Bu Ay</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-4">
              {orderHistory.map((order) => (
                <Card key={order.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <h4 className="font-semibold">{order.business_name}</h4>
                          <Badge variant={order.status === 'delivered' ? 'default' : 'secondary'}>
                            {order.status === 'delivered' ? 'Teslim Edildi' : order.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {new Date(order.created_at).toLocaleDateString('tr-TR')} • 
                          {order.delivery_address}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-green-600">₺{order.commission}</div>
                        <div className="text-sm text-gray-500">₺{order.total_amount} sipariş</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-4">
            <h2 className="text-2xl font-bold">Bildirimler</h2>
            
            <div className="space-y-3">
              {notifications.map((notification) => (
                <Card 
                  key={notification.id}
                  className={`cursor-pointer hover:shadow-md transition-shadow ${
                    !notification.read ? 'border-blue-200 bg-blue-50' : ''
                  }`}
                  onClick={() => markNotificationRead(notification.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <div className="text-2xl">
                        {notification.type === 'admin_message' ? '💬' : 
                         notification.type === 'new_order' ? '📋' : '🔔'}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold">{notification.title}</h4>
                        <p className="text-sm text-gray-600">{notification.message}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(notification.created_at).toLocaleString('tr-TR')}
                        </p>
                      </div>
                      {!notification.read && (
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Messages Tab */}
          <TabsContent value="messages" className="space-y-4">
            <h2 className="text-2xl font-bold">Admin Mesajları</h2>
            
            <div className="space-y-4">
              {messages.map((message) => (
                <Card key={message.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <div className="text-2xl">👨‍💼</div>
                      <div className="flex-1">
                        <h4 className="font-semibold">{message.title}</h4>
                        <p className="text-gray-700 mt-2">{message.message}</p>
                        <p className="text-xs text-gray-400 mt-2">
                          {new Date(message.created_at).toLocaleString('tr-TR')}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Statistics Tab */}
          <TabsContent value="stats" className="space-y-4">
            <h2 className="text-2xl font-bold">İstatistiklerim</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="text-3xl mb-2">📦</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {orderHistory.filter(o => o.status === 'delivered').length}
                  </div>
                  <div className="text-sm text-gray-600">Teslim Edilen Sipariş</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="text-3xl mb-2">💰</div>
                  <div className="text-2xl font-bold text-green-600">
                    ₺{orderHistory.reduce((sum, order) => sum + order.commission, 0).toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600">Toplam Kazanç</div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="text-3xl mb-2">⭐</div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {user?.average_rating || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Ortalama Puan</div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default CourierDashboard;