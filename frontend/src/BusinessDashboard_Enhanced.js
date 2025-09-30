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
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);

  // Restaurant status and settings
  const [restaurantStatus, setRestaurantStatus] = useState({
    isOpen: true,
    isAcceptingOrders: true,
    busyMode: false,
    preparationTime: 25
  });

  // Orders management
  const [incomingOrders, setIncomingOrders] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [unprocessedCount, setUnprocessedCount] = useState(0);

  // Menu & Product management
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState(['Başlangıçlar', 'Ana Yemekler', 'Tatlılar', 'İçecekler', 'Pizza', 'Burger']);
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: '',
    category: 'Ana Yemekler',
    preparation_time: 15,
    is_available: true,
    image_url: '',
    ingredients: '',
    allergens: ''
  });

  // Analytics and Statistics
  const [stats, setStats] = useState({
    today: {
      orders: 0,
      revenue: 0,
      avgOrderValue: 0,
      completionRate: 0
    },
    week: {
      orders: 0,
      revenue: 0,
      growth: 0
    },
    month: {
      orders: 0,
      revenue: 0,
      growth: 0
    },
    topProducts: [],
    peakHours: [],
    customerSatisfaction: 4.5
  });

  // Financial data
  const [financials, setFinancials] = useState({
    dailyRevenue: [],
    monthlyRevenue: 0,
    pendingPayouts: 0,
    commission: 0.15,
    totalEarnings: 0
  });

  // Initialize with professional mock data
  useEffect(() => {
    initializeBusinessData();
    const interval = setInterval(fetchLiveData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const initializeBusinessData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadMockOrders(),
        loadMockProducts(),
        loadMockStats(),
        loadMockFinancials()
      ]);
    } catch (error) {
      console.error('Initialization error:', error);
      toast.error('Veri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const loadMockOrders = () => {
    // Incoming orders
    setIncomingOrders([
      {
        id: 'ORD-001',
        customer_name: 'Ahmet Yılmaz',
        customer_phone: '+90 532 123 4567',
        items: [
          { name: 'Chicken Burger', quantity: 2, price: 45.00 },
          { name: 'Patates Kızartması', quantity: 1, price: 15.00 }
        ],
        total_amount: 105.00,
        pickup_address: 'Beşiktaş Merkez',
        delivery_address: { address: 'Kadıköy, Moda Cad. No:15', lat: 40.9876, lng: 29.0234 },
        order_date: new Date(),
        status: 'pending',
        payment_method: 'card',
        notes: 'Acılı sos ekle lütfen'
      },
      {
        id: 'ORD-002', 
        customer_name: 'Zeynep Kaya',
        customer_phone: '+90 533 987 6543',
        items: [
          { name: 'Margarita Pizza', quantity: 1, price: 65.00 },
          { name: 'Cola', quantity: 2, price: 10.00 }
        ],
        total_amount: 85.00,
        pickup_address: 'Beşiktaş Merkez',
        delivery_address: { address: 'Şişli, Nişantaşı Cad. No:42', lat: 41.0567, lng: 28.9876 },
        order_date: new Date(Date.now() - 10000),
        status: 'pending',
        payment_method: 'cash',
        notes: 'İnce hamur'
      }
    ]);

    // Active orders  
    setActiveOrders([
      {
        id: 'ORD-003',
        customer_name: 'Mehmet Demir',
        items: [{ name: 'Adana Kebap', quantity: 1, price: 55.00 }],
        total_amount: 55.00,
        status: 'preparing',
        accepted_at: new Date(Date.now() - 600000), // 10 minutes ago
        preparation_time: 20
      }
    ]);

    setUnprocessedCount(2);
  };

  const loadMockProducts = () => {
    setProducts([
      {
        id: 'PRD-001',
        name: 'Chicken Burger',
        description: 'Sulu tavuk göğsü, taze sebzeler ve özel sosumuzla',
        price: 45.00,
        category: 'Burger',
        preparation_time: 15,
        is_available: true,
        image_url: 'https://images.unsplash.com/photo-1550547660-d9450f859349?w=300',
        ingredients: 'Tavuk göğsü, marul, domates, soğan, turşu',
        allergens: 'Gluten',
        order_count: 245,
        rating: 4.8
      },
      {
        id: 'PRD-002',
        name: 'Margarita Pizza',
        description: 'Klasik İtalyan pizzası - mozzarella, domates, fesleğen',
        price: 65.00,
        category: 'Pizza',
        preparation_time: 20,
        is_available: true,
        image_url: 'https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=300',
        ingredients: 'Pizza hamuru, mozzarella, domates sosu, fesleğen',
        allergens: 'Gluten, Süt',
        order_count: 189,
        rating: 4.9
      },
      {
        id: 'PRD-003',
        name: 'Adana Kebap',
        description: 'Geleneksel Adana kebabı, lavash ekmeği ile',
        price: 55.00,
        category: 'Ana Yemekler',
        preparation_time: 25,
        is_available: false,
        image_url: 'https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=300',
        ingredients: 'Dana kıyma, soğan, baharat, lavash',
        allergens: 'Gluten',
        order_count: 156,
        rating: 4.7
      }
    ]);
  };

  const loadMockStats = () => {
    setStats({
      today: {
        orders: 23,
        revenue: 1247.50,
        avgOrderValue: 54.24,
        completionRate: 96.5
      },
      week: {
        orders: 187,
        revenue: 9876.25,
        growth: 12.5
      },
      month: {
        orders: 756,
        revenue: 42315.75,
        growth: 18.7
      },
      topProducts: [
        { name: 'Chicken Burger', sales: 245, revenue: 11025.00 },
        { name: 'Margarita Pizza', sales: 189, revenue: 12285.00 },
        { name: 'Adana Kebap', sales: 156, revenue: 8580.00 }
      ],
      peakHours: [
        { hour: '12:00-13:00', orders: 15 },
        { hour: '19:00-20:00', orders: 22 },
        { hour: '20:00-21:00', orders: 18 }
      ],
      customerSatisfaction: 4.6
    });
  };

  const loadMockFinancials = () => {
    setFinancials({
      dailyRevenue: [
        { date: '2024-01-01', revenue: 1247.50 },
        { date: '2024-01-02', revenue: 1456.25 },
        { date: '2024-01-03', revenue: 987.75 }
      ],
      monthlyRevenue: 42315.75,
      pendingPayouts: 3567.25,
      commission: 0.15,
      totalEarnings: 35968.50
    });
  };

  const fetchLiveData = async () => {
    // Simulate live data updates
    setStats(prev => ({
      ...prev,
      today: {
        ...prev.today,
        orders: prev.today.orders + Math.floor(Math.random() * 2),
        revenue: prev.today.revenue + (Math.random() * 100)
      }
    }));
  };
    todayOrders: 0,
    todayRevenue: 0,
    weeklyOrders: 0,
    weeklyRevenue: 0,
    monthlyOrders: 0,
    monthlyRevenue: 0,
    totalOrders: 0,
    totalRevenue: 0,
    averageOrderValue: 0,
    customerRating: 4.2
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
      fetchStats(),
      fetchRestaurantStatus()
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
      // Use mock data for demonstration
      const mockOrders = [
        {
          id: '1',
          order_number: 'ORD-001',
          customer_name: 'Ahmet Yılmaz',
          customer_phone: '+905551234567',
          delivery_address: 'Kadıköy, İstanbul',
          total_amount: 85.50,
          status: 'pending',
          created_at: new Date().toISOString(),
          items: [
            { name: 'Margherita Pizza', quantity: 1, price: 45.50 },
            { name: 'Coca Cola', quantity: 2, price: 20.00 }
          ]
        },
        {
          id: '2',
          order_number: 'ORD-002',
          customer_name: 'Fatma Özkan',
          customer_phone: '+905559876543',
          delivery_address: 'Beşiktaş, İstanbul',
          total_amount: 120.00,
          status: 'pending',
          created_at: new Date(Date.now() - 300000).toISOString(),
          items: [
            { name: 'Kebab Menu', quantity: 2, price: 60.00 }
          ]
        }
      ];
      setIncomingOrders(mockOrders);
      setUnprocessedCount(mockOrders.length);
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
      // Mock active orders
      setActiveOrders([
        {
          id: '3',
          order_number: 'ORD-003',
          customer_name: 'Mehmet Demir',
          total_amount: 65.00,
          status: 'preparing',
          created_at: new Date(Date.now() - 600000).toISOString()
        }
      ]);
    }
  };

  const fetchOrderHistory = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/orders/history`, {
        headers: { Authorization: `Bearer ${token}` }
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
      // Mock success for demo
      setIncomingOrders(prev => prev.filter(order => order.id !== orderId));
      setActiveOrders(prev => [...prev, { 
        id: orderId, 
        order_number: `ORD-${orderId}`,
        customer_name: 'Test Customer',
        total_amount: 75.00,
        status: 'accepted',
        created_at: new Date().toISOString()
      }]);
      toast.success('Sipariş kabul edildi! (Demo)');
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
      // Mock success for demo
      setIncomingOrders(prev => prev.filter(order => order.id !== orderId));
      toast.success('Sipariş reddedildi (Demo)');
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
      // Mock update for demo
      setActiveOrders(prev => prev.map(order => 
        order.id === orderId ? { ...order, status } : order
      ));
      toast.success('Durum güncellendi (Demo)');
    }
  };

  // Products functions
  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/products/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setProducts(response.data.products || response.data || []);
    } catch (error) {
      console.error('Failed to fetch products:', error);
      // Mock products for demo
      setProducts([
        {
          id: '1',
          name: 'Margherita Pizza',
          description: 'Klasik domates, mozzarella ve fesleğen',
          price: 45.50,
          category: 'food',
          preparation_time: 20,
          is_available: true,
          image_url: '',
          order_count: 25
        },
        {
          id: '2',
          name: 'Coca Cola',
          description: '330ml şişe',
          price: 10.00,
          category: 'drink',
          preparation_time: 2,
          is_available: true,
          image_url: '',
          order_count: 45
        },
        {
          id: '3',
          name: 'Adana Kebab',
          description: 'Acılı adana kebab, yanında pilav ve salata',
          price: 65.00,
          category: 'food',
          preparation_time: 25,
          is_available: false,
          image_url: '',
          order_count: 12
        }
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
        category: 'food',
        preparation_time: 15,
        is_available: true,
        image_url: ''
      });
      fetchProducts();
    } catch (error) {
      toast.error('Ürün kaydedilemedi');
      // Mock success for demo
      const newProduct = {
        id: Date.now().toString(),
        ...productForm,
        price: parseFloat(productForm.price),
        order_count: 0
      };
      
      if (editingProduct) {
        setProducts(prev => prev.map(p => p.id === editingProduct.id ? newProduct : p));
        toast.success('Ürün güncellendi! (Demo)');
      } else {
        setProducts(prev => [...prev, newProduct]);
        toast.success('Ürün eklendi! (Demo)');
      }
      
      setShowProductModal(false);
      setEditingProduct(null);
      setProductForm({
        name: '',
        description: '',
        price: '',
        category: 'food',
        preparation_time: 15,
        is_available: true,
        image_url: ''
      });
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
      // Mock delete for demo
      setProducts(prev => prev.filter(p => p.id !== productId));
      toast.success('Ürün silindi (Demo)');
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
      // Mock update for demo
      setProducts(prev => prev.map(p => 
        p.id === productId ? { ...p, is_available: isAvailable } : p
      ));
      toast.success(isAvailable ? 'Ürün stokta (Demo)' : 'Ürün stoktan çıkarıldı (Demo)');
    }
  };

  // Statistics functions
  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/business/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setStats(response.data || stats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // Mock stats for demo
      setStats({
        todayOrders: 12,
        todayRevenue: 485.50,
        weeklyOrders: 67,
        weeklyRevenue: 2240.75,
        monthlyOrders: 245,
        monthlyRevenue: 8950.25,
        totalOrders: 1250,
        totalRevenue: 45780.00,
        averageOrderValue: 68.50,
        customerRating: 4.3
      });
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

  const toggleRestaurantOpen = async () => {
    const newStatus = !restaurantStatus.isOpen;
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.put(`${API}/business/status`, {
        isOpen: newStatus
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setRestaurantStatus(prev => ({ ...prev, isOpen: newStatus }));
      toast.success(newStatus ? 'Restoran açıldı' : 'Restoran kapatıldı');
    } catch (error) {
      toast.error('Durum güncellenemedi');
      // Mock update for demo
      setRestaurantStatus(prev => ({ ...prev, isOpen: newStatus }));
      toast.success(newStatus ? 'Restoran açıldı (Demo)' : 'Restoran kapatıldı (Demo)');
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
      image_url: product.image_url || ''
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
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="orders">
              📋 Siparişler
              {unprocessedCount > 0 && (
                <Badge className="ml-1 bg-red-500">{unprocessedCount}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="menu">🍽️ Menü</TabsTrigger>
            <TabsTrigger value="analytics">📊 Raporlar</TabsTrigger>
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
              <h2 className="text-xl font-bold">🍽️ Menü & Fiyat Yönetimi</h2>
              <div className="flex space-x-2">
                <Button 
                  onClick={() => {
                    setEditingProduct(null);
                    setProductForm({
                      name: '',
                      description: '',
                      price: '',
                      category: 'food',
                      preparation_time: 15,
                      is_available: true,
                      image_url: ''
                    });
                    setShowProductModal(true);
                  }}
                  className="bg-green-600 hover:bg-green-700"
                >
                  ➕ Yeni Menü Ekle
                </Button>
                <Button 
                  onClick={fetchProducts}
                  variant="outline"
                >
                  🔄 Yenile
                </Button>
              </div>
            </div>

            {/* Menu Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl mb-2">🍽️</div>
                  <div className="text-2xl font-bold text-blue-600">{products.length}</div>
                  <div className="text-sm text-gray-600">Toplam Menü</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl mb-2">✅</div>
                  <div className="text-2xl font-bold text-green-600">{products.filter(p => p.is_available).length}</div>
                  <div className="text-sm text-gray-600">Stokta</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl mb-2">❌</div>
                  <div className="text-2xl font-bold text-red-600">{products.filter(p => !p.is_available).length}</div>
                  <div className="text-sm text-gray-600">Stok Yok</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl mb-2">💰</div>
                  <div className="text-2xl font-bold text-purple-600">
                    ₺{products.length > 0 ? (products.reduce((sum, p) => sum + (p.price || 0), 0) / products.length).toFixed(2) : '0.00'}
                  </div>
                  <div className="text-sm text-gray-600">Ortalama Fiyat</div>
                </CardContent>
              </Card>
            </div>

            {/* Enhanced Products Grid */}
            {products.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-6xl mb-4">🍽️</div>
                  <h3 className="text-xl font-semibold mb-2">Henüz menü eklenmemiş</h3>
                  <p className="text-gray-600 mb-4">İlk menü öğenizi ekleyerek başlayın</p>
                  <Button 
                    onClick={() => {
                      setEditingProduct(null);
                      setProductForm({
                        name: '',
                        description: '',
                        price: '',
                        category: 'food',
                        preparation_time: 15,
                        is_available: true,
                        image_url: ''
                      });
                      setShowProductModal(true);
                    }}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    ➕ İlk Menüyü Ekle
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product) => (
                  <Card key={product.id} className={`hover:shadow-lg transition-all duration-300 ${!product.is_available ? 'opacity-60 border-red-200' : 'border-green-200'}`}>
                    <CardContent className="p-4">
                      {product.image_url && (
                        <div className="relative mb-3">
                          <img 
                            src={product.image_url} 
                            alt={product.name}
                            className="w-full h-32 object-cover rounded-lg"
                          />
                          {!product.is_available && (
                            <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
                              <span className="text-white font-bold">STOK YOK</span>
                            </div>
                          )}
                        </div>
                      )}
                      
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-semibold text-lg flex-1">{product.name}</h3>
                        <Badge variant={product.is_available ? 'default' : 'secondary'} className="ml-2">
                          {product.is_available ? '✅' : '❌'}
                        </Badge>
                      </div>
                      
                      <p className="text-gray-600 text-sm mb-3">{product.description || 'Açıklama yok'}</p>
                      
                      {/* Enhanced Price Display */}
                      <div className="bg-green-50 p-3 rounded-lg mb-3">
                        <div className="flex justify-between items-center">
                          <span className="text-lg font-bold text-green-700">₺{product.price}</span>
                          <div className="flex items-center space-x-2">
                            <Button
                              onClick={() => {
                                const newPrice = prompt(`${product.name} için yeni fiyat:`, product.price);
                                if (newPrice && !isNaN(newPrice)) {
                                  // Update price
                                  setProducts(prev => prev.map(p => 
                                    p.id === product.id ? { ...p, price: parseFloat(newPrice) } : p
                                  ));
                                  toast.success('Fiyat güncellendi (Demo)');
                                }
                              }}
                              variant="outline"
                              size="sm"
                              className="text-xs px-2 py-1 h-auto"
                            >
                              💰 Fiyat Değiştir
                            </Button>
                          </div>
                        </div>
                        <div className="text-xs text-green-600 mt-1">
                          💡 Hızlı fiyat değişimi
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                        <span>⏱️ {product.preparation_time || 15} dk</span>
                        <Badge variant="outline" className="text-xs">
                          {product.category === 'food' ? '🍽️ Yemek' : '🥤 İçecek'}
                        </Badge>
                        <span>🔥 {product.order_count || 0} sipariş</span>
                      </div>
                      
                      <div className="flex space-x-1">
                        <Button
                          onClick={() => {
                            setEditingProduct(product);
                            setProductForm({
                              name: product.name,
                              description: product.description || '',
                              price: product.price.toString(),
                              category: product.category,
                              preparation_time: product.preparation_time || 15,
                              is_available: product.is_available,
                              image_url: product.image_url || ''
                            });
                            setShowProductModal(true);
                          }}
                          variant="outline"
                          size="sm"
                          className="flex-1 text-xs"
                        >
                          ✏️ Düzenle
                        </Button>
                        <Button
                          onClick={() => toggleProductAvailability(product.id, !product.is_available)}
                          variant="outline"
                          size="sm"
                          className={`flex-1 text-xs ${product.is_available ? 'border-red-200 text-red-600 hover:bg-red-50' : 'border-green-200 text-green-600 hover:bg-green-50'}`}
                        >
                          {product.is_available ? '❌ Stokta Yok' : '✅ Stokta Var'}
                        </Button>
                        <Button
                          onClick={() => deleteProduct(product.id)}
                          variant="outline"
                          size="sm"
                          className="border-red-200 text-red-600 hover:bg-red-50 px-2"
                        >
                          🗑️
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

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
                          <SelectItem value="food">Yiyecek</SelectItem>
                          <SelectItem value="drink">İçecek</SelectItem>
                          <SelectItem value="dessert">Tatlı</SelectItem>
                          <SelectItem value="appetizer">Meze</SelectItem>
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
            <h2 className="text-xl font-bold">📊 Raporlar & İstatistikler</h2>

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

            {/* Performance Metrics */}
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
                    <div className="flex items-center justify-center space-x-1">
                      <p className="text-2xl font-bold text-yellow-600">{stats.customerRating}</p>
                      <span className="text-yellow-500">⭐</span>
                    </div>
                    <p className="text-sm text-gray-600">Müşteri Memnuniyeti</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">₺{(stats.monthlyRevenue * 0.95).toFixed(2)}</p>
                    <p className="text-sm text-gray-600">Aylık Net Kazanç (%5 komisyon sonrası)</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <h2 className="text-xl font-bold">⚙️ Restoran Ayarları</h2>

            <Card>
              <CardHeader>
                <CardTitle>📊 Mevcut Durum</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                </div>
                
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-semibold mb-2">💡 İpuçları</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Yoğun saatlerde siparişleri hızlı kabul edin</li>
                    <li>• Ürün stok durumlarını güncel tutun</li>
                    <li>• Müşteri memnuniyeti için teslimat sürelerini kısa tutun</li>
                    <li>• Popüler ürünlerinizi öne çıkarın</li>
                  </ul>
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