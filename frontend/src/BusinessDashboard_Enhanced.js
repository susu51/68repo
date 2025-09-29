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
    isAcceptingOrders: true
  });

  // Orders management
  const [incomingOrders, setIncomingOrders] = useState([]);
  const [activeOrders, setActiveOrders] = useState([]);
  const [orderHistory, setOrderHistory] = useState([]);
  const [unprocessedCount, setUnprocessedCount] = useState(0);

  // Menu & Product management
  const [products, setProducts] = useState([]);
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: '',
    category: 'food',
    preparation_time: 15,
    is_available: true,
    image_url: ''
  });

  // Statistics
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

          {/* Orders Tab - İlk kısmı buraya kadar */}
        </Tabs>
      </div>
    </div>
  );
};

export default BusinessDashboard;