import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const BusinessDashboard = ({ user, onLogout }) => {
  // Navigation state
  const [activeTab, setActiveTab] = useState('orders');
  const [loading, setLoading] = useState(true);

  // Restaurant status
  const [restaurantStatus, setRestaurantStatus] = useState({
    isOpen: true,
    openingTime: '09:00',
    closingTime: '23:00',
    workingDays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
    deliveryRadius: 5,
    estimatedDeliveryTime: 30,
    isAcceptingOrders: true
  });

  // Orders management
  const [incomingOrders, setIncomingOrders] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [unprocessedCount, setUnprocessedCount] = useState(0);

  // Menu & Product management
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    preparation_time: 15,
    is_available: true,
    image_url: '',
    tags: []
  });

  // Statistics & Reports
  const [stats, setStats] = useState({
    todayOrders: 0,
    todayRevenue: 0,
    weeklyOrders: 0,
    weeklyRevenue: 0,
    monthlyOrders: 0,
    monthlyRevenue: 0,
    totalOrders: 0,
    totalRevenue: 0,
    averageOrderValue: 0,
    customerRating: 4.2,
    totalCustomers: 0
  });

  // Popular products
  const [popularProducts, setPopularProducts] = useState([]);
  const [customerReviews, setCustomerReviews] = useState([]);

  // Featured promotion
  const [featuredStatus, setFeaturedStatus] = useState(null);
  const [promotionPlans, setPromotionPlans] = useState([
    { id: 'basic', name: 'Temel Paket', price: 99, duration: 7, features: ['Listelerde üstte gösterim', 'Özel rozet'] },
    { id: 'premium', name: 'Premium Paket', price: 199, duration: 15, features: ['Listelerde üstte gösterim', 'Özel rozet', 'Ana sayfada öne çıkarma'] },
    { id: 'ultimate', name: 'Ultimate Paket', price: 399, duration: 30, features: ['Listelerde üstte gösterim', 'Özel rozet', 'Ana sayfada öne çıkarma', 'Reklam banner\'ında yer alma'] }
  ]);

  // Filters
  const [orderFilter, setOrderFilter] = useState({
    status: 'all',
    dateRange: 'today',
    sortBy: 'newest'
  });

  const [reportFilter, setReportFilter] = useState({
    period: 'daily',
    startDate: new Date().toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchInitialData();
    
    // Auto refresh for incoming orders
    const ordersInterval = setInterval(() => {
      if (activeTab === 'orders') {
        fetchIncomingOrders();
      }
    }, 30000);

    return () => clearInterval(ordersInterval);
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    await Promise.all([
      fetchIncomingOrders(),
      fetchActiveOrders(),
      fetchOrderHistory(),
      fetchProducts(),
      fetchCategories(),
      fetchStats(),
      fetchPopularProducts(),
      fetchCustomerReviews(),
      fetchRestaurantStatus(),
      fetchFeaturedStatus()
    ]);
    setLoading(false);
  };

  // Orders functions
  const fetchIncomingOrders = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/orders/incoming`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const orders = response.data.orders || [];
      setIncomingOrders(orders);
      setUnprocessedCount(orders.filter(order => order.status === 'pending').length);
    } catch (error) {
      console.error('Failed to fetch incoming orders:', error);
    }
  };

  const fetchActiveOrders = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/orders/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setActiveOrders(response.data.orders || []);
    } catch (error) {
      console.error('Failed to fetch active orders:', error);
    }
  };

  const fetchOrderHistory = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const params = {};
      
      if (orderFilter.status !== 'all') params.status = orderFilter.status;
      if (orderFilter.dateRange !== 'all') params.date_range = orderFilter.dateRange;
      params.sort_by = orderFilter.sortBy;

      const response = await axios.get(`${API}/business/orders/history`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      
      setOrderHistory(response.data.orders || []);
    } catch (error) {
      console.error('Failed to fetch order history:', error);
    }
  };

  const acceptOrder = async (orderId) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.post(`${API}/business/orders/${orderId}/accept`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Sipariş kabul edildi!');
      fetchIncomingOrders();
      fetchActiveOrders();
    } catch (error) {
      toast.error('Sipariş kabul edilemedi');
    }
  };

  const rejectOrder = async (orderId, reason) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.post(`${API}/business/orders/${orderId}/reject`, {
        reason: reason || 'İşletme tarafından reddedildi'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Sipariş reddedildi');
      fetchIncomingOrders();
    } catch (error) {
      toast.error('Sipariş reddedilemedi');
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.post(`${API}/business/orders/${orderId}/status`, {
        status,
        timestamp: new Date().toISOString()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const statusMessages = {
        'preparing': 'Sipariş hazırlanıyor',
        'ready': 'Sipariş hazır',
        'picked_up': 'Kurye aldı',
        'delivered': 'Teslim edildi',
        'cancelled': 'Sipariş iptal edildi'
      };

      toast.success(statusMessages[status] || 'Durum güncellendi');
      fetchActiveOrders();
      fetchOrderHistory();
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
  };

  // Products functions
  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/products/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setProducts(response.data.products || []);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/categories`);
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      setCategories([
        { id: 'food', name: 'Yiyecek' },
        { id: 'drink', name: 'İçecek' },
        { id: 'dessert', name: 'Tatlı' },
        { id: 'appetizer', name: 'Meze' }
      ]);
    }
  };

  const saveProduct = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const url = editingProduct 
        ? `${API}/products/${editingProduct.id}` 
        : `${API}/products`;
      
      const method = editingProduct ? 'put' : 'post';
      
      await axios[method](url, productForm, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(editingProduct ? 'Ürün güncellendi!' : 'Ürün eklendi!');
      setShowProductModal(false);
      setEditingProduct(null);
      setProductForm({
        name: '',
        description: '',
        price: '',
        category: '',
        preparation_time: 15,
        is_available: true,
        image_url: '',
        tags: []
      });
      fetchProducts();
    } catch (error) {
      toast.error('Ürün kaydedilemedi');
    }
  };

  const deleteProduct = async (productId) => {
    if (!window.confirm('Bu ürünü silmek istediğinizden emin misiniz?')) return;

    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.delete(`${API}/products/${productId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Ürün silindi');
      fetchProducts();
    } catch (error) {
      toast.error('Ürün silinemedi');
    }
  };

  const toggleProductAvailability = async (productId, isAvailable) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.patch(`${API}/products/${productId}/availability`, {
        is_available: isAvailable
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(isAvailable ? 'Ürün stokta' : 'Ürün stoktan çıkarıldı');
      fetchProducts();
    } catch (error) {
      toast.error('Stok durumu güncellenemedi');
    }
  };

  // Statistics functions
  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setStats(response.data || {
        todayOrders: 0,
        todayRevenue: 0,
        weeklyOrders: 0,
        weeklyRevenue: 0,
        monthlyOrders: 0,
        monthlyRevenue: 0,
        totalOrders: 0,
        totalRevenue: 0,
        averageOrderValue: 0,
        customerRating: 4.2,
        totalCustomers: 0
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchPopularProducts = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/popular-products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setPopularProducts(response.data.products || []);
    } catch (error) {
      console.error('Failed to fetch popular products:', error);
    }
  };

  const fetchCustomerReviews = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/reviews`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCustomerReviews(response.data.reviews || []);
    } catch (error) {
      console.error('Failed to fetch reviews:', error);
    }
  };

  // Restaurant status functions
  const fetchRestaurantStatus = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setRestaurantStatus(prev => ({ ...prev, ...response.data }));
    } catch (error) {
      console.error('Failed to fetch restaurant status:', error);
    }
  };

  const updateRestaurantStatus = async (updates) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.put(`${API}/business/status`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setRestaurantStatus(prev => ({ ...prev, ...updates }));
      toast.success('Restoran durumu güncellendi');
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
  };

  const toggleRestaurantOpen = async () => {
    const newStatus = !restaurantStatus.isOpen;
    await updateRestaurantStatus({ isOpen: newStatus });
    toast.success(newStatus ? 'Restoran açıldı' : 'Restoran kapatıldı');
  };

  // Featured promotion functions
  const fetchFeaturedStatus = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/featured-status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setFeaturedStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch featured status:', error);
    }
  };

  const requestFeatured = async (planId) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const plan = promotionPlans.find(p => p.id === planId);
      
      await axios.post(`${API}/business/featured-request`, {
        plan_type: planId,
        duration_days: plan.duration,
        price: plan.price
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Öne çıkarma isteği gönderildi! Admin onayı bekleniyor.');
      fetchFeaturedStatus();
    } catch (error) {
      toast.error('İstek gönderilemedi');
    }
  };

  // Report generation
  const generateReport = async (type = 'daily') => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/report/${type}`, {
        headers: { Authorization: `Bearer ${token}` },
        params: reportFilter,
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `restoran-rapor-${type}-${new Date().toISOString().slice(0, 10)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Rapor indirildi');
    } catch (error) {
      toast.error('Rapor oluşturulamadı');
    }
  };

  const openEditProduct = (product) => {
    setEditingProduct(product);
    setProductForm({
      name: product.name,
      description: product.description,
      price: product.price.toString(),
      category: product.category,
      preparation_time: product.preparation_time || 15,
      is_available: product.is_available,
      image_url: product.image_url || '',
      tags: product.tags || []
    });
    setShowProductModal(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center py-12">
            <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">İşletme paneli yükleniyor...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="text-2xl">🏪</div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">İşletme Paneli</h1>
                <p className="text-sm text-gray-600">
                  {user?.business_name || 'Restoranım'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Restaurant Status Toggle */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={toggleRestaurantOpen}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    restaurantStatus.isOpen ? 'bg-green-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                      restaurantStatus.isOpen ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`text-sm font-medium ${restaurantStatus.isOpen ? 'text-green-600' : 'text-gray-500'}`}>
                  {restaurantStatus.isOpen ? '🟢 Açık' : '🔴 Kapalı'}
                </span>
              </div>

              {/* Unprocessed Orders Indicator */}
              {unprocessedCount > 0 && (
                <Badge className="bg-red-600 animate-pulse">
                  {unprocessedCount} Yeni Sipariş
                </Badge>
              )}

              {/* Featured Status */}
              {featuredStatus && featuredStatus.is_active && (
                <Badge className="bg-gold-600 text-white">
                  ⭐ Öne Çıkarılmış
                </Badge>
              )}

              <Button onClick={onLogout} variant="outline" size="sm">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="orders">
              📋 Siparişler
              {unprocessedCount > 0 && (
                <Badge className="ml-1 bg-red-500">{unprocessedCount}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="menu">🍽️ Menü</TabsTrigger>
            <TabsTrigger value="analytics">📊 Raporlar</TabsTrigger>
            <TabsTrigger value="featured">⭐ Öne Çıkar</TabsTrigger>
            <TabsTrigger value="settings">⚙️ Ayarlar</TabsTrigger>
          </TabsList>

          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">Sipariş Yönetimi</h2>
              <Button onClick={fetchIncomingOrders} variant="outline" size="sm">
                🔄 Yenile
              </Button>
            </div>

            {!restaurantStatus.isOpen && (
              <Card className="border-orange-200 bg-orange-50">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2">
                    <div className="text-orange-600">⚠️</div>
                    <div>
                      <p className="font-semibold text-orange-800">Restoran Kapalı</p>
                      <p className="text-orange-600">Yeni sipariş alamazsınız. Restoranı açmak için yukarıdaki butonu kullanın.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Incoming Orders */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <span>🔔 Gelen Siparişler</span>
                  {unprocessedCount > 0 && (
                    <Badge className="bg-red-600">{unprocessedCount} Bekliyor</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {incomingOrders.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Şu anda bekleyen sipariş yok</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {incomingOrders.map((order) => (
                      <Card key={order.id} className="border-blue-200 bg-blue-50">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <h3 className="font-semibold">Sipariş #{order.order_number}</h3>
                                <Badge variant="secondary">{order.status}</Badge>
                                <Badge className="bg-green-600">₺{order.total_amount}</Badge>
                              </div>
                              
                              <p className="text-sm text-gray-600 mb-2">
                                👤 {order.customer_name} • 📞 {order.customer_phone}
                              </p>
                              
                              <p className="text-sm text-gray-600 mb-3">
                                📍 {order.delivery_address}
                              </p>
                              
                              <div className="space-y-1">
                                {order.items?.map((item, index) => (
                                  <div key={index} className="flex justify-between text-sm">
                                    <span>{item.quantity}x {item.name}</span>
                                    <span>₺{(item.price * item.quantity).toFixed(2)}</span>
                                  </div>
                                ))}
                              </div>
                              
                              <p className="text-xs text-gray-500 mt-2">
                                🕐 {new Date(order.created_at).toLocaleString('tr-TR')}
                              </p>
                            </div>
                            
                            <div className="ml-4 space-y-2">
                              <Button
                                onClick={() => acceptOrder(order.id)}
                                className="w-full bg-green-600 hover:bg-green-700"
                                size="sm"
                              >
                                ✅ Kabul Et
                              </Button>
                              <Button
                                onClick={() => rejectOrder(order.id)}
                                variant="outline"
                                className="w-full border-red-200 text-red-600 hover:bg-red-50"
                                size="sm"
                              >
                                ❌ Reddet
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Active Orders */}
            <Card>
              <CardHeader>
                <CardTitle>🔥 Aktif Siparişler</CardTitle>
              </CardHeader>
              <CardContent>
                {activeOrders.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Şu anda aktif sipariş yok</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {activeOrders.map((order) => (
                      <Card key={order.id} className="border-green-200 bg-green-50">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <h3 className="font-semibold">Sipariş #{order.order_number}</h3>
                                <Badge variant={
                                  order.status === 'preparing' ? 'default' :
                                  order.status === 'ready' ? 'secondary' :
                                  'outline'
                                }>
                                  {order.status === 'preparing' ? '👨‍🍳 Hazırlanıyor' :
                                   order.status === 'ready' ? '✅ Hazır' :
                                   order.status === 'picked_up' ? '🚚 Kuryede' : order.status}
                                </Badge>
                              </div>
                              
                              <p className="text-sm text-gray-600">
                                👤 {order.customer_name} • ₺{order.total_amount}
                              </p>
                              
                              <p className="text-xs text-gray-500 mt-1">
                                ⏱️ {Math.floor((Date.now() - new Date(order.created_at)) / 60000)} dakika önce
                              </p>
                            </div>
                            
                            <div className="ml-4 space-y-2">
                              {order.status === 'accepted' && (
                                <Button
                                  onClick={() => updateOrderStatus(order.id, 'preparing')}
                                  className="w-full bg-orange-600 hover:bg-orange-700"
                                  size="sm"
                                >
                                  👨‍🍳 Hazırla
                                </Button>
                              )}
                              {order.status === 'preparing' && (
                                <Button
                                  onClick={() => updateOrderStatus(order.id, 'ready')}
                                  className="w-full bg-green-600 hover:bg-green-700"
                                  size="sm"
                                >
                                  ✅ Hazır
                                </Button>
                              )}
                              {order.status === 'ready' && (
                                <div className="text-center">
                                  <Badge className="bg-blue-600">🚚 Kurye Bekleniyor</Badge>
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Menu Tab */}
          <TabsContent value="menu" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">Menü Yönetimi</h2>
              <Button 
                onClick={() => {
                  setEditingProduct(null);
                  setProductForm({
                    name: '',
                    description: '',
                    price: '',
                    category: '',
                    preparation_time: 15,
                    is_available: true,
                    image_url: '',
                    tags: []
                  });
                  setShowProductModal(true);
                }}
                className="bg-green-600 hover:bg-green-700"
              >
                ➕ Yeni Ürün Ekle
              </Button>
            </div>

            {/* Products Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => (
                <Card key={product.id} className={`hover:shadow-lg transition-shadow ${!product.is_available ? 'opacity-60' : ''}`}>
                  <CardContent className="p-4">
                    {product.image_url && (
                      <img 
                        src={product.image_url} 
                        alt={product.name}
                        className="w-full h-32 object-cover rounded-lg mb-3"
                      />
                    )}
                    
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-lg">{product.name}</h3>
                      <Badge variant={product.is_available ? 'default' : 'secondary'}>
                        {product.is_available ? '✅ Stokta' : '❌ Tükendi'}
                      </Badge>
                    </div>
                    
                    <p className="text-gray-600 text-sm mb-2">{product.description}</p>
                    
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-lg font-bold text-green-600">₺{product.price}</span>
                      <Badge variant="outline">{product.category}</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                      <span>⏱️ {product.preparation_time || 15} dk</span>
                      <span>🔥 {product.order_count || 0} sipariş</span>
                    </div>
                    
                    <div className="flex space-x-2">
                      <Button
                        onClick={() => openEditProduct(product)}
                        variant="outline"
                        size="sm"
                        className="flex-1"
                      >
                        ✏️ Düzenle
                      </Button>
                      <Button
                        onClick={() => toggleProductAvailability(product.id, !product.is_available)}
                        variant="outline"
                        size="sm"
                        className={`flex-1 ${product.is_available ? 'border-red-200 text-red-600' : 'border-green-200 text-green-600'}`}
                      >
                        {product.is_available ? '❌ Stoktan Çıkar' : '✅ Stoka Ekle'}
                      </Button>
                      <Button
                        onClick={() => deleteProduct(product.id)}
                        variant="outline"
                        size="sm"
                        className="border-red-200 text-red-600 hover:bg-red-50"
                      >
                        🗑️
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Product Modal */}
            {showProductModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
                  <h3 className="text-lg font-semibold mb-4">
                    {editingProduct ? 'Ürün Düzenle' : 'Yeni Ürün Ekle'}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="product-name">Ürün Adı</Label>
                      <Input
                        id="product-name"
                        value={productForm.name}
                        onChange={(e) => setProductForm(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Örn: Margherita Pizza"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="product-description">Açıklama</Label>
                      <Textarea
                        id="product-description"
                        value={productForm.description}
                        onChange={(e) => setProductForm(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Ürün açıklaması..."
                        rows={3}
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="product-price">Fiyat (₺)</Label>
                        <Input
                          id="product-price"
                          type="number"
                          value={productForm.price}
                          onChange={(e) => setProductForm(prev => ({ ...prev, price: e.target.value }))}
                          placeholder="0.00"
                          min="0"
                          step="0.01"
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="product-prep-time">Hazırlık Süresi (dk)</Label>
                        <Input
                          id="product-prep-time"
                          type="number"
                          value={productForm.preparation_time}
                          onChange={(e) => setProductForm(prev => ({ ...prev, preparation_time: parseInt(e.target.value) }))}
                          min="1"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="product-category">Kategori</Label>
                      <Select 
                        value={productForm.category} 
                        onValueChange={(value) => setProductForm(prev => ({ ...prev, category: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Kategori seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map((category) => (
                            <SelectItem key={category.id} value={category.id}>
                              {category.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="product-image">Görsel URL</Label>
                      <Input
                        id="product-image"
                        value={productForm.image_url}
                        onChange={(e) => setProductForm(prev => ({ ...prev, image_url: e.target.value }))}
                        placeholder="https://example.com/image.jpg"
                      />
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="product-available"
                        checked={productForm.is_available}
                        onChange={(e) => setProductForm(prev => ({ ...prev, is_available: e.target.checked }))}
                        className="rounded border-gray-300"
                      />
                      <Label htmlFor="product-available">Stokta mevcut</Label>
                    </div>
                  </div>
                  
                  <div className="flex justify-end space-x-3 mt-6">
                    <Button 
                      variant="outline" 
                      onClick={() => {
                        setShowProductModal(false);
                        setEditingProduct(null);
                      }}
                    >
                      İptal
                    </Button>
                    <Button onClick={saveProduct}>
                      {editingProduct ? '💾 Güncelle' : '➕ Ekle'}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">Raporlar & İstatistikler</h2>
              
              <div className="flex space-x-2">
                <Button onClick={() => generateReport('daily')} variant="outline" size="sm">
                  📄 Günlük Rapor
                </Button>
                <Button onClick={() => generateReport('weekly')} variant="outline" size="sm">
                  📄 Haftalık Rapor
                </Button>
                <Button onClick={() => generateReport('monthly')} variant="outline" size="sm">
                  📄 Aylık Rapor
                </Button>
              </div>
            </div>

            {/* Revenue Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{stats.todayRevenue.toFixed(2)}</p>
                  <p className="text-green-100">Bugün</p>
                  <p className="text-xs text-green-200 mt-1">
                    {stats.todayOrders} sipariş
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{stats.weeklyRevenue.toFixed(2)}</p>
                  <p className="text-blue-100">Bu Hafta</p>
                  <p className="text-xs text-blue-200 mt-1">
                    {stats.weeklyOrders} sipariş
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{stats.monthlyRevenue.toFixed(2)}</p>
                  <p className="text-purple-100">Bu Ay</p>
                  <p className="text-xs text-purple-200 mt-1">
                    {stats.monthlyOrders} sipariş
                  </p>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
                <CardContent className="p-6 text-center">
                  <p className="text-3xl font-bold mb-2">₺{stats.totalRevenue.toFixed(2)}</p>
                  <p className="text-orange-100">Toplam</p>
                  <p className="text-xs text-orange-200 mt-1">
                    {stats.totalOrders} sipariş
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Popular Products & Reviews */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>🔥 En Popüler Ürünler</CardTitle>
                </CardHeader>
                <CardContent>
                  {popularProducts.length === 0 ? (
                    <p className="text-center text-gray-500 py-4">Henüz popüler ürün verisi yok</p>
                  ) : (
                    <div className="space-y-3">
                      {popularProducts.slice(0, 5).map((product, index) => (
                        <div key={product.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <Badge className="w-6 h-6 rounded-full bg-orange-600 text-white text-xs flex items-center justify-center">
                              {index + 1}
                            </Badge>
                            <div>
                              <p className="font-medium">{product.name}</p>
                              <p className="text-sm text-gray-600">₺{product.price}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-green-600">{product.order_count} sipariş</p>
                            <p className="text-xs text-gray-500">₺{(product.order_count * product.price).toFixed(2)} gelir</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <span>⭐ Müşteri Değerlendirmeleri</span>
                    <Badge className="bg-yellow-100 text-yellow-800">
                      {stats.customerRating}/5
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {customerReviews.length === 0 ? (
                    <p className="text-center text-gray-500 py-4">Henüz değerlendirme yok</p>
                  ) : (
                    <div className="space-y-4">
                      {customerReviews.slice(0, 3).map((review) => (
                        <div key={review.id} className="p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <p className="font-medium">{review.customer_name}</p>
                            <div className="flex items-center space-x-1">
                              {[...Array(5)].map((_, i) => (
                                <span 
                                  key={i} 
                                  className={`text-sm ${i < review.rating ? 'text-yellow-500' : 'text-gray-300'}`}
                                >
                                  ⭐
                                </span>
                              ))}
                            </div>
                          </div>
                          <p className="text-sm text-gray-600">{review.comment}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(review.created_at).toLocaleDateString('tr-TR')}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Business Performance */}
            <Card>
              <CardHeader>
                <CardTitle>📈 İşletme Performansı</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">₺{stats.averageOrderValue.toFixed(2)}</p>
                    <p className="text-sm text-gray-600">Ortalama Sipariş Tutarı</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">{stats.totalCustomers}</p>
                    <p className="text-sm text-gray-600">Toplam Müşteri</p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center space-x-1">
                      <p className="text-2xl font-bold text-yellow-600">{stats.customerRating}</p>
                      <span className="text-yellow-500">⭐</span>
                    </div>
                    <p className="text-sm text-gray-600">Müşteri Memnuniyeti</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Featured Tab */}
          <TabsContent value="featured" className="space-y-6">
            <h2 className="text-xl font-bold">⭐ Öne Çıkarma Paketleri</h2>
            
            {featuredStatus && featuredStatus.is_active && (
              <Card className="border-yellow-400 bg-yellow-50">
                <CardContent className="p-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <span className="text-2xl">⭐</span>
                    <div>
                      <h3 className="text-lg font-semibold text-yellow-800">Öne Çıkarma Aktif!</h3>
                      <p className="text-yellow-600">
                        {featuredStatus.plan_type} paketi • 
                        {new Date(featuredStatus.expires_at).toLocaleDateString('tr-TR')} tarihine kadar
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-yellow-700">
                    Restoranınız şu anda listelerde öne çıkarılmış durumda ve daha fazla görünürlük sağlıyor.
                  </p>
                </CardContent>
              </Card>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {promotionPlans.map((plan) => (
                <Card key={plan.id} className={`hover:shadow-lg transition-shadow ${plan.id === 'premium' ? 'border-blue-400 bg-blue-50' : ''}`}>
                  <CardContent className="p-6">
                    <div className="text-center">
                      <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                      <div className="text-3xl font-bold text-green-600 mb-2">₺{plan.price}</div>
                      <p className="text-gray-600 mb-4">{plan.duration} gün süreyle</p>
                      
                      <div className="space-y-2 mb-6">
                        {plan.features.map((feature, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <span className="text-green-600">✅</span>
                            <span className="text-sm">{feature}</span>
                          </div>
                        ))}
                      </div>
                      
                      <Button 
                        onClick={() => requestFeatured(plan.id)}
                        disabled={featuredStatus?.is_active}
                        className="w-full"
                        variant={plan.id === 'premium' ? 'default' : 'outline'}
                      >
                        {featuredStatus?.is_active ? '✅ Aktif Paket Var' : '🚀 Paketi Seç'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card>
              <CardHeader>
                <CardTitle>💡 Öne Çıkarma Hakkında</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm text-gray-600">
                  <p>• Öne çıkarma paketleri restoranınızın daha fazla müşteriye ulaşmasını sağlar</p>
                  <p>• Listelerde üst sıralarda görünür ve özel rozetle işaretlenir</p>
                  <p>• Premium paketler ana sayfada da öne çıkarılır</p>
                  <p>• Ultimate paket ile reklam banner'larında yer alabilirsiniz</p>
                  <p>• Ödemeler admin onayından sonra etkinleşir</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <h2 className="text-xl font-bold">⚙️ Restoran Ayarları</h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Operating Hours */}
              <Card>
                <CardHeader>
                  <CardTitle>🕐 Çalışma Saatleri</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="opening-time">Açılış Saati</Label>
                      <Input
                        id="opening-time"
                        type="time"
                        value={restaurantStatus.openingTime}
                        onChange={(e) => setRestaurantStatus(prev => ({ ...prev, openingTime: e.target.value }))}
                      />
                    </div>
                    <div>
                      <Label htmlFor="closing-time">Kapanış Saati</Label>
                      <Input
                        id="closing-time"
                        type="time"
                        value={restaurantStatus.closingTime}
                        onChange={(e) => setRestaurantStatus(prev => ({ ...prev, closingTime: e.target.value }))}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label>Çalışma Günleri</Label>
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {[
                        { key: 'monday', label: 'Pazartesi' },
                        { key: 'tuesday', label: 'Salı' },
                        { key: 'wednesday', label: 'Çarşamba' },
                        { key: 'thursday', label: 'Perşembe' },
                        { key: 'friday', label: 'Cuma' },
                        { key: 'saturday', label: 'Cumartesi' },
                        { key: 'sunday', label: 'Pazar' }
                      ].map((day) => (
                        <div key={day.key} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={restaurantStatus.workingDays.includes(day.key)}
                            onChange={(e) => {
                              const checked = e.target.checked;
                              setRestaurantStatus(prev => ({
                                ...prev,
                                workingDays: checked
                                  ? [...prev.workingDays, day.key]
                                  : prev.workingDays.filter(d => d !== day.key)
                              }));
                            }}
                            className="rounded border-gray-300"
                          />
                          <span className="text-sm">{day.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <Button 
                    onClick={() => updateRestaurantStatus(restaurantStatus)}
                    className="w-full"
                  >
                    💾 Saatleri Kaydet
                  </Button>
                </CardContent>
              </Card>

              {/* Delivery Settings */}
              <Card>
                <CardHeader>
                  <CardTitle>🚚 Teslimat Ayarları</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="delivery-radius">Teslimat Yarıçapı (km)</Label>
                    <Input
                      id="delivery-radius"
                      type="number"
                      value={restaurantStatus.deliveryRadius}
                      onChange={(e) => setRestaurantStatus(prev => ({ ...prev, deliveryRadius: parseInt(e.target.value) }))}
                      min="1"
                      max="50"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="delivery-time">Tahmini Teslimat Süresi (dk)</Label>
                    <Input
                      id="delivery-time"
                      type="number"
                      value={restaurantStatus.estimatedDeliveryTime}
                      onChange={(e) => setRestaurantStatus(prev => ({ ...prev, estimatedDeliveryTime: parseInt(e.target.value) }))}
                      min="10"
                      max="120"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Sipariş Kabul Durumu</Label>
                      <p className="text-sm text-gray-600">Yeni sipariş alıp almayacağınızı belirler</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={restaurantStatus.isAcceptingOrders}
                      onChange={(e) => setRestaurantStatus(prev => ({ ...prev, isAcceptingOrders: e.target.checked }))}
                      className="rounded border-gray-300"
                    />
                  </div>
                  
                  <Button 
                    onClick={() => updateRestaurantStatus(restaurantStatus)}
                    className="w-full"
                  >
                    💾 Teslimat Ayarlarını Kaydet
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Restaurant Status Overview */}
            <Card>
              <CardHeader>
                <CardTitle>📊 Mevcut Durum</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className={`text-2xl font-bold ${restaurantStatus.isOpen ? 'text-green-600' : 'text-red-600'}`}>
                      {restaurantStatus.isOpen ? '🟢 Açık' : '🔴 Kapalı'}
                    </p>
                    <p className="text-sm text-gray-600">Restoran Durumu</p>
                  </div>
                  <div className="text-center">
                    <p className={`text-2xl font-bold ${restaurantStatus.isAcceptingOrders ? 'text-green-600' : 'text-orange-600'}`}>
                      {restaurantStatus.isAcceptingOrders ? '✅ Alıyor' : '⏸️ Durdu'}
                    </p>
                    <p className="text-sm text-gray-600">Sipariş Durumu</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">{restaurantStatus.deliveryRadius} km</p>
                    <p className="text-sm text-gray-600">Teslimat Yarıçapı</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-600">{restaurantStatus.estimatedDeliveryTime} dk</p>
                    <p className="text-sm text-gray-600">Teslimat Süresi</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default BusinessDashboard;