import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import "./App.css";
import { CreateOrderForm, OrdersList, NearbyOrdersForCourier, OrderStatusBadge } from "./OrderSystem";
import { MenuManagement, MenuDisplay } from "./MenuManagement";
import { CreatePackageOrder, PackageOrderHistory } from "./PackageOrder";
import CourierBalance from "./CourierBalance";
import FileUpload from "./FileUpload";
import LeafletMap from "./LeafletMap";
import { ProfessionalFoodOrderSystem } from "./FoodOrderSystem";

// Components
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { Label } from "./components/ui/label";
import toast from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

// Console log for debugging
console.log('Frontend connecting to:', API);

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isMounted, setIsMounted] = useState(true);

  useEffect(() => {
    setIsMounted(true);
    
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const userData = localStorage.getItem('kuryecini_user');
      
      if (token && userData && isMounted) {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        // Set axios default authorization header
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      // Clear corrupted data
      localStorage.removeItem('kuryecini_access_token');
      localStorage.removeItem('kuryecini_user');
    }
    
    if (isMounted) {
      setLoading(false);
    }

    // Cleanup
    return () => {
      setIsMounted(false);
    };
  }, []);

  const login = (authData) => {
    if (!isMounted) return;
    
    try {
      localStorage.setItem('kuryecini_access_token', authData.access_token);
      localStorage.setItem('kuryecini_user', JSON.stringify(authData.user_data));
      setUser(authData.user_data);
      
      // Set axios default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${authData.access_token}`;
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const logout = () => {
    if (!isMounted) return;
    
    try {
      localStorage.removeItem('kuryecini_access_token');
      localStorage.removeItem('kuryecini_user');
      setUser(null);
      delete axios.defaults.headers.common['Authorization'];
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Login Component - Email/Password Authentication + Admin Login
const LoginForm = ({ onRegisterClick }) => {
  const { login } = useAuth();
  const [loginType, setLoginType] = useState('user'); // 'user' or 'admin'
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    adminPassword: ''
  });
  const [loading, setLoading] = useState(false);

  const handleUserSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: formData.email,
        password: formData.password
      });
      login(response.data);
      toast.success('Başarıyla giriş yaptınız!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Giriş başarısız');
    }
    setLoading(false);
  };

  const handleAdminSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Manual validation
    if (!formData.adminPassword || formData.adminPassword.trim() === '') {
      toast.error('Lütfen admin şifresini girin');
      setLoading(false);
      return;
    }

    try {
      const response = await axios.post(`${API}/auth/admin`, {
        password: formData.adminPassword
      });
      
      login(response.data);
      toast.success('Admin girişi başarılı!');
    } catch (error) {
      console.error('Admin login error:', error);
      toast.error(error.response?.data?.detail || 'Admin giriş hatası');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-orange-600">
          {loginType === 'user' ? 'Giriş Yap' : 'Admin Girişi'}
        </CardTitle>
        <CardDescription>
          {loginType === 'user' ? 'DeliverTR hesabınıza giriş yapın' : 'Admin paneline erişim'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Login Type Selector */}
        <Tabs value={loginType} onValueChange={setLoginType} className="mb-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="user" data-testid="user-login-tab">Kullanıcı Girişi</TabsTrigger>
            <TabsTrigger value="admin" data-testid="admin-login-tab">Admin Girişi</TabsTrigger>
          </TabsList>
          
          <TabsContent value="user">
            <form onSubmit={handleUserSubmit} className="space-y-4">
              <div>
                <Label htmlFor="email">E-posta</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="ornek@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                  data-testid="login-email"
                />
              </div>
              
              <div>
                <Label htmlFor="password">Şifre</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Şifrenizi girin"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  data-testid="login-password"
                />
              </div>
              
              <Button 
                type="submit" 
                disabled={loading}
                className="w-full bg-orange-600 hover:bg-orange-700"
                data-testid="login-submit-btn"
              >
                {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
              </Button>
            </form>
          </TabsContent>
          
          <TabsContent value="admin">
            <form onSubmit={handleAdminSubmit} className="space-y-4">
              <div>
                <Label htmlFor="adminPassword">Admin Şifresi</Label>
                <Input
                  id="adminPassword"
                  type="password"
                  placeholder="Admin şifresini girin (6851)"
                  value={formData.adminPassword}
                  onChange={(e) => setFormData({...formData, adminPassword: e.target.value})}
                  data-testid="admin-password"
                />
              </div>
              
              <Button 
                onClick={handleAdminSubmit}
                disabled={loading}
                className="w-full bg-red-600 hover:bg-red-700"
                data-testid="admin-login-btn"
              >
                {loading ? 'Giriş yapılıyor...' : 'Admin Girişi'}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
        
        {loginType === 'user' && (
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              Hesabınız yok mu?{' '}
              <button
                onClick={onRegisterClick}
                className="text-orange-600 hover:text-orange-700 font-medium"
                data-testid="go-to-register-btn"
              >
                Kayıt Ol
              </button>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// City selector component
const CitySelector = ({ value, onChange, required = false }) => {
  const cities = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", 
    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", 
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", 
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", 
    "Giresun", "Gümüşhane", "Hakkâri", "Hatay", "Isparta", "Mersin", "İstanbul", 
    "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", 
    "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", 
    "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", 
    "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", 
    "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", 
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", 
    "Karabük", "Kilis", "Osmaniye", "Düzce"
  ];

  return (
    <Select value={value} onValueChange={onChange} required={required}>
      <SelectTrigger data-testid="city-select">
        <SelectValue placeholder="Şehir seçin" />
      </SelectTrigger>
      <SelectContent>
        {cities.map((city) => (
          <SelectItem key={city} value={city}>
            {city}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
};

// Admin Dashboard - System Management
const AdminDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [couriers, setCouriers] = useState([]);
  const [kycFilter, setKycFilter] = useState('pending'); // pending, approved, rejected, all
  const [loading, setLoading] = useState(false);
  const [selectedCourier, setSelectedCourier] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectDialog, setShowRejectDialog] = useState(false);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`);
      setUsers(response.data || []);
    } catch (error) {
      console.error('Users fetch error:', error);
      setUsers([]);
      if (error.response?.status !== 403) {
        toast.error('Kullanıcılar yüklenemedi');
      }
    }
  };

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/admin/products`);
      setProducts(response.data || []);
    } catch (error) {
      console.error('Products fetch error:', error);
      setProducts([]);
      if (error.response?.status !== 403) {
        toast.error('Ürünler yüklenemedi');
      }
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/admin/orders`);
      setOrders(response.data || []);
    } catch (error) {
      console.error('Orders fetch error:', error);
      setOrders([]);
      if (error.response?.status !== 403) {
        toast.error('Siparişler yüklenemedi');
      }
    }
  };

  const fetchCouriers = async () => {
    try {
      const response = await axios.get(`${API}/admin/couriers/kyc`);
      setCouriers(response.data || []);
    } catch (error) {
      console.error('Couriers fetch error:', error);
      setCouriers([]);
      if (error.response?.status !== 403) {
        toast.error('Kurye bilgileri yüklenemedi');
      }
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        await Promise.allSettled([
          fetchUsers(),
          fetchProducts(), 
          fetchOrders(),
          fetchCouriers()
        ]);
      } catch (error) {
        console.error('Data fetch error:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      await axios.patch(`${API}/orders/${orderId}/status?new_status=${newStatus}`);
      toast.success('Sipariş durumu güncellendi');
      fetchOrders();
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
  };

  const updateCourierKYC = async (courierId, kycStatus, notes = '') => {
    try {
      setLoading(true);
      await axios.patch(`${API}/admin/couriers/${courierId}/kyc?kyc_status=${kycStatus}`, 
        notes ? { notes } : {},
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      toast.success(`Kurye KYC durumu ${kycStatus === 'approved' ? 'onaylandı' : 'reddedildi'}`);
      
      // Refresh couriers list to update UI immediately
      await fetchCouriers();
      
      // Close dialog if open
      setShowRejectDialog(false);
      setRejectReason('');
      setSelectedCourier(null);
    } catch (error) {
      console.error('KYC Update Error:', error);
      toast.error('KYC durumu güncellenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = (courier) => {
    setSelectedCourier(courier);
    setShowRejectDialog(true);
  };

  const confirmReject = async () => {
    if (!rejectReason.trim()) {
      toast.error('Lütfen reddetme sebebini yazın');
      return;
    }
    await updateCourierKYC(selectedCourier.id, 'rejected', rejectReason);
  };

  const getRoleColor = (role) => {
    if (!role) return 'bg-gray-100 text-gray-800';
    
    switch (role.toLowerCase()) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'courier': return 'bg-orange-100 text-orange-800';
      case 'business': return 'bg-green-100 text-green-800';
      case 'customer': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getKYCStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 flex items-center space-x-3">
            <div className="w-6 h-6 border-3 border-red-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-gray-700">Admin paneli yükleniyor...</span>
          </div>
        </div>
      )}
      
      {/* Mobile-Responsive Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8">
          <div className="flex justify-between h-14 sm:h-16">
            <div className="flex items-center">
              <h1 className="text-sm sm:text-xl font-semibold text-red-600">
                🛡️ <span className="hidden sm:inline">Admin Panel - </span>DeliverTR
              </h1>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <Badge variant="outline" className="bg-red-50 border-red-200 text-red-800 text-xs">
                Admin
              </Badge>
              <Button onClick={logout} variant="outline" size="sm">
                <span className="hidden sm:inline">Çıkış</span>
                <span className="sm:hidden">🚪</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8 py-4 sm:py-8">
        {/* Mobile-Responsive Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-lg sm:text-2xl">👥</div>
                </div>
                <div className="ml-2 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">
                      Kullanıcı
                    </dt>
                    <dd className="text-sm sm:text-lg font-medium text-gray-900">
                      {users.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-lg sm:text-2xl">🍽️</div>
                </div>
                <div className="ml-2 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">
                      Ürün
                    </dt>
                    <dd className="text-sm sm:text-lg font-medium text-gray-900">
                      {products.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-lg sm:text-2xl">📦</div>
                </div>
                <div className="ml-2 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">
                      Sipariş
                    </dt>
                    <dd className="text-sm sm:text-lg font-medium text-gray-900">
                      {orders.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="text-lg sm:text-2xl">💰</div>
                </div>
                <div className="ml-2 sm:ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-xs sm:text-sm font-medium text-gray-500 truncate">
                      Ciro
                    </dt>
                    <dd className="text-xs sm:text-lg font-medium text-gray-900">
                      ₺{orders.reduce((sum, order) => sum + order.total_amount, 0).toFixed(2)}
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Mobile-Responsive Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5 text-xs sm:text-sm">
            <TabsTrigger value="users" className="px-1 sm:px-3">
              <span className="hidden sm:inline">Kullanıcılar</span>
              <span className="sm:hidden">👥</span>
            </TabsTrigger>
            <TabsTrigger value="kyc" className="px-1 sm:px-3">
              <span className="hidden sm:inline">KYC Onay</span>
              <span className="sm:hidden">📋</span>
            </TabsTrigger>
            <TabsTrigger value="products" className="px-1 sm:px-3">
              <span className="hidden sm:inline">Ürünler</span>
              <span className="sm:hidden">🍽️</span>
            </TabsTrigger>
            <TabsTrigger value="orders" className="px-1 sm:px-3">
              <span className="hidden sm:inline">Siparişler</span>
              <span className="sm:hidden">📦</span>
            </TabsTrigger>
            <TabsTrigger value="map" className="px-1 sm:px-3">
              <span className="hidden sm:inline">Harita</span>
              <span className="sm:hidden">🗺️</span>
            </TabsTrigger>
          </TabsList>

          {/* KYC Tab */}
          <TabsContent value="kyc" className="space-y-4 sm:space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm sm:text-base">
                  Kurye KYC Onayları ({couriers.filter(c => kycFilter === 'all' || c.kyc_status === kycFilter).length})
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Kurye belgelerini inceleyin ve onaylayın
                </CardDescription>
                
                {/* KYC Filter Buttons */}
                <div className="flex flex-wrap gap-2 pt-4">
                  <Button
                    size="sm"
                    variant={kycFilter === 'pending' ? 'default' : 'outline'}
                    onClick={() => setKycFilter('pending')}
                    className="text-xs"
                  >
                    ⏳ Bekleyen ({couriers.filter(c => c.kyc_status === 'pending').length})
                  </Button>
                  <Button
                    size="sm"
                    variant={kycFilter === 'approved' ? 'default' : 'outline'}
                    onClick={() => setKycFilter('approved')}
                    className="text-xs"
                  >
                    ✅ Onaylı ({couriers.filter(c => c.kyc_status === 'approved').length})
                  </Button>
                  <Button
                    size="sm"
                    variant={kycFilter === 'rejected' ? 'default' : 'outline'}
                    onClick={() => setKycFilter('rejected')}
                    className="text-xs"
                  >
                    ❌ Reddedilen ({couriers.filter(c => c.kyc_status === 'rejected').length})
                  </Button>
                  <Button
                    size="sm"
                    variant={kycFilter === 'all' ? 'default' : 'outline'}
                    onClick={() => setKycFilter('all')}
                    className="text-xs"
                  >
                    📋 Tümü ({couriers.length})
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {couriers.filter(courier => kycFilter === 'all' || courier.kyc_status === kycFilter).length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500 text-sm">
                      {kycFilter === 'pending' ? 'Bekleyen KYC bulunamadı' :
                       kycFilter === 'approved' ? 'Onaylı KYC bulunamadı' :
                       kycFilter === 'rejected' ? 'Reddedilen KYC bulunamadı' :
                       'Kurye bulunamadı'}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {couriers.filter(courier => kycFilter === 'all' || courier.kyc_status === kycFilter).map((courier) => (
                      <Card key={courier.id} className="overflow-hidden">
                        <CardContent className="p-3 sm:p-4">
                          <div className="space-y-4">
                            {/* Courier Info */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                              <div>
                                <h3 className="font-semibold text-sm sm:text-base">
                                  {courier.first_name} {courier.last_name}
                                </h3>
                                <p className="text-xs sm:text-sm text-gray-600">{courier.email}</p>
                                <p className="text-xs text-gray-500">
                                  📍 {courier.city} • 🚗 {courier.vehicle_type}
                                </p>
                              </div>
                              <Badge className={getKYCStatusColor(courier.kyc_status)} size="sm">
                                {courier.kyc_status === 'approved' ? '✅ Onaylı' :
                                 courier.kyc_status === 'rejected' ? '❌ Reddedildi' : '⏳ Bekliyor'}
                              </Badge>
                            </div>

                            {/* Vehicle & License Details */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs sm:text-sm bg-gray-50 p-3 rounded-lg">
                              <div className="space-y-1">
                                <p><strong>Araç Modeli:</strong> {courier.vehicle_model}</p>
                                <p><strong>Ehliyet Sınıfı:</strong> {courier.license_class}</p>
                              </div>
                              <div className="space-y-1">
                                <p><strong>Ehliyet No:</strong> {courier.license_number}</p>
                                <p><strong>IBAN:</strong> {courier.iban?.slice(-4).padStart(courier.iban?.length || 0, '*')}</p>
                              </div>
                            </div>

                            {/* Documents */}
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              {/* License Photo */}
                              <div className="space-y-2">
                                <Label className="text-xs font-semibold">Ehliyet Fotoğrafı</Label>
                                {courier.license_photo_url ? (
                                  <div className="relative group">
                                    <img
                                      src={`${BACKEND_URL}${courier.license_photo_url}`}
                                      alt="Ehliyet"
                                      className="w-full h-24 sm:h-32 object-cover rounded border cursor-pointer hover:opacity-75 transition-opacity"
                                      onClick={() => window.open(`${BACKEND_URL}${courier.license_photo_url}`, '_blank')}
                                    />
                                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded transition-all flex items-center justify-center">
                                      <span className="text-white opacity-0 group-hover:opacity-100 text-xs font-semibold">
                                        🔍 Büyült
                                      </span>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="w-full h-24 sm:h-32 bg-gray-100 rounded border flex items-center justify-center text-gray-500 text-xs">
                                    📄 Yok
                                  </div>
                                )}
                              </div>

                              {/* Vehicle Photo */}
                              <div className="space-y-2">
                                <Label className="text-xs font-semibold">Araç Fotoğrafı</Label>
                                {courier.vehicle_photo_url ? (
                                  <div className="relative group">
                                    <img
                                      src={`${BACKEND_URL}${courier.vehicle_photo_url}`}
                                      alt="Araç"
                                      className="w-full h-24 sm:h-32 object-cover rounded border cursor-pointer hover:opacity-75 transition-opacity"
                                      onClick={() => window.open(`${BACKEND_URL}${courier.vehicle_photo_url}`, '_blank')}
                                    />
                                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded transition-all flex items-center justify-center">
                                      <span className="text-white opacity-0 group-hover:opacity-100 text-xs font-semibold">
                                        🔍 Büyült
                                      </span>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="w-full h-24 sm:h-32 bg-gray-100 rounded border flex items-center justify-center text-gray-500 text-xs">
                                    🚗 Yok
                                  </div>
                                )}
                              </div>

                              {/* Profile Photo */}
                              <div className="space-y-2">
                                <Label className="text-xs font-semibold">Profil Fotoğrafı</Label>
                                {courier.profile_photo_url ? (
                                  <div className="relative group">
                                    <img
                                      src={`${BACKEND_URL}${courier.profile_photo_url}`}
                                      alt="Profil"
                                      className="w-full h-24 sm:h-32 object-cover rounded border cursor-pointer hover:opacity-75 transition-opacity"
                                      onClick={() => window.open(`${BACKEND_URL}${courier.profile_photo_url}`, '_blank')}
                                    />
                                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded transition-all flex items-center justify-center">
                                      <span className="text-white opacity-0 group-hover:opacity-100 text-xs font-semibold">
                                        🔍 Büyült
                                      </span>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="w-full h-24 sm:h-32 bg-gray-100 rounded border flex items-center justify-center text-gray-500 text-xs">
                                    👤 Yok
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Action Buttons */}
                            {courier.kyc_status === 'pending' && (
                              <div className="flex flex-col sm:flex-row gap-2 pt-3 border-t">
                                <Button
                                  onClick={() => updateCourierKYC(courier.id, 'approved')}
                                  className="bg-green-600 hover:bg-green-700 text-xs sm:text-sm flex-1"
                                  size="sm"
                                  disabled={loading}
                                >
                                  {loading ? '⏳ İşleniyor...' : '✅ Onayla'}
                                </Button>
                                <Button
                                  onClick={() => handleReject(courier)}
                                  variant="destructive"
                                  className="text-xs sm:text-sm flex-1"
                                  size="sm"
                                  disabled={loading}
                                >
                                  ❌ Reddet
                                </Button>
                              </div>
                            )}

                            {/* Review History */}
                            {(courier.kyc_reviewed_at || courier.kyc_notes) && (
                              <div className="text-xs text-gray-500 pt-2 border-t bg-gray-50 p-2 rounded">
                                {courier.kyc_reviewed_at && (
                                  <p>📅 İnceleme: {new Date(courier.kyc_reviewed_at).toLocaleDateString('tr-TR')}</p>
                                )}
                                {courier.kyc_notes && (
                                  <p>📝 Not: {courier.kyc_notes}</p>
                                )}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Tab - Mobile Responsive */}
          <TabsContent value="users" className="space-y-4 sm:space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm sm:text-base">Kullanıcı Yönetimi ({users.length})</CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Tüm kullanıcıları görüntüleyin ve yönetin
                </CardDescription>
              </CardHeader>
              <CardContent>
                {users.length === 0 ? (
                  <p className="text-gray-500 text-center py-8 text-sm">Kullanıcı bulunamadı</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Kullanıcı
                          </th>
                          <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Rol
                          </th>
                          <th className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Şehir
                          </th>
                          <th className="hidden lg:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Kayıt Tarihi
                          </th>
                          <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Durum
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((user) => (
                          <tr key={user.id}>
                            <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="flex-shrink-0 h-8 w-8 sm:h-10 sm:w-10">
                                  <div className="h-8 w-8 sm:h-10 sm:w-10 rounded-full bg-gray-200 flex items-center justify-center text-xs sm:text-base">
                                    {user.role === 'courier' ? '🚴' : 
                                     user.role === 'business' ? '🏪' :
                                     user.role === 'customer' ? '👤' : '👑'}
                                  </div>
                                </div>
                                <div className="ml-2 sm:ml-4">
                                  <div className="text-xs sm:text-sm font-medium text-gray-900">
                                    {user.first_name && user.last_name ? 
                                      `${user.first_name} ${user.last_name}` :
                                      user.business_name || user.email || 'İsimsiz Kullanıcı'
                                    }
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    {user.email || 'E-posta yok'}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                              <Badge className={getRoleColor(user.role)} size="sm">
                                {user.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'Unknown'}
                              </Badge>
                            </td>
                            <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {user.city || '-'}
                            </td>
                            <td className="hidden lg:table-cell px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(user.created_at).toLocaleDateString('tr-TR')}
                            </td>
                            <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                              <Badge variant={user.is_active ? "default" : "secondary"} size="sm">
                                {user.is_active ? 'Aktif' : 'Pasif'}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Ürün Yönetimi ({products.length})</CardTitle>
                <CardDescription>
                  Tüm ürünleri görüntüleyin ve yönetin
                </CardDescription>
              </CardHeader>
              <CardContent>
                {products.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Ürün bulunamadı</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {products.map((product) => (
                      <Card key={product.id} className="overflow-hidden">
                        {product.photo_url && (
                          <div className="h-32 overflow-hidden">
                            <img 
                              src={`${BACKEND_URL}${product.photo_url}`} 
                              alt={product.name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        )}
                        <CardContent className="p-4">
                          <h3 className="font-semibold">{product.name}</h3>
                          <p className="text-sm text-gray-600 mb-2">{product.description}</p>
                          <p className="text-xs text-gray-500 mb-2">İşletme: {product.business_name}</p>
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-green-600">₺{product.price}</span>
                            <Badge variant={product.is_available ? "default" : "secondary"}>
                              {product.is_available ? 'Mevcut' : 'Stokta Yok'}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Sipariş Yönetimi ({orders.length})</CardTitle>
                <CardDescription>
                  Tüm siparişleri görüntüleyin ve yönetin
                </CardDescription>
              </CardHeader>
              <CardContent>
                {orders.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Sipariş bulunamadı</p>
                ) : (
                  <div className="space-y-4">
                    {orders.map((order) => (
                      <Card key={order.id}>
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <h3 className="font-semibold">Sipariş #{order.id.slice(-8)}</h3>
                              <p className="text-sm text-gray-600">
                                {order.customer_name} → {order.business_name}
                              </p>
                              <p className="text-xs text-gray-500">{order.delivery_address}</p>
                              {order.courier_name && (
                                <p className="text-xs text-gray-500">Kurye: {order.courier_name}</p>
                              )}
                            </div>
                            <div className="text-right">
                              <p className="font-bold text-lg">₺{order.total_amount}</p>
                              <p className="text-sm text-gray-500">
                                Komisyon: ₺{order.commission_amount?.toFixed(2)}
                              </p>
                              <OrderStatusBadge status={order.status} />
                            </div>
                          </div>

                          <div className="mb-3">
                            <h4 className="font-medium mb-1">Siparişler:</h4>
                            {order.items.map((item, index) => (
                              <div key={index} className="text-sm text-gray-600">
                                {item.quantity}x {item.product_name} - ₺{item.subtotal}
                              </div>
                            ))}
                          </div>

                          <div className="flex justify-between items-center">
                            <p className="text-xs text-gray-500">
                              {new Date(order.created_at).toLocaleString('tr-TR')}
                            </p>
                            
                            {order.status !== 'delivered' && order.status !== 'cancelled' && (
                              <div className="space-x-2">
                                {order.status === 'created' && (
                                  <Button 
                                    size="sm"
                                    onClick={() => updateOrderStatus(order.id, 'assigned')}
                                  >
                                    Kuryeye Ata
                                  </Button>
                                )}
                                {order.status === 'assigned' && (
                                  <Button 
                                    size="sm"
                                    onClick={() => updateOrderStatus(order.id, 'on_route')}
                                  >
                                    Yolda Olarak İşaretle
                                  </Button>
                                )}
                                {order.status === 'on_route' && (
                                  <Button 
                                    size="sm"
                                    onClick={() => updateOrderStatus(order.id, 'delivered')}
                                  >
                                    Teslim Edildi
                                  </Button>
                                )}
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Map Tab */}
          <TabsContent value="map">
            <Card>
              <CardHeader>
                <CardTitle>Sistem Haritası</CardTitle>
              </CardHeader>
              <CardContent>
                <LeafletMap
                  center={[39.925533, 32.866287]}
                  zoom={10}
                  height="600px"
                  markers={orders.filter(order => order.delivery_lat && order.delivery_lng).map(order => ({
                    lat: order.delivery_lat,
                    lng: order.delivery_lng,
                    type: 'delivery',
                    popup: true,
                    title: `Sipariş #${order.id.slice(-8)}`,
                    description: `${order.customer_name} - ${order.status}`,
                    address: order.delivery_address
                  }))}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* KYC Reject Dialog */}
        {showRejectDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">KYC Reddetme Sebebi</h3>
              <p className="text-sm text-gray-600 mb-4">
                {selectedCourier?.first_name} {selectedCourier?.last_name} adlı kurye için reddetme sebebini belirtin:
              </p>
              <textarea
                className="w-full p-3 border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                rows="4"
                placeholder="Örn: Ehliyet fotoğrafı net değil, araç ruhsatı eksik, vs..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
              <div className="flex justify-end space-x-3 mt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowRejectDialog(false);
                    setRejectReason('');
                    setSelectedCourier(null);
                  }}
                  disabled={loading}
                >
                  İptal
                </Button>
                <Button
                  variant="destructive"
                  onClick={confirmReject}
                  disabled={loading || !rejectReason.trim()}
                >
                  {loading ? '⏳ Reddediliyor...' : '❌ Reddet'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
const CourierRegistration = ({ onComplete, onBack }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    iban: '',
    vehicle_type: '',
    vehicle_model: '',
    license_class: '',
    license_number: '',
    city: ''
  });
  const [licensePhotoUrl, setLicensePhotoUrl] = useState('');
  const [vehiclePhotoUrl, setVehiclePhotoUrl] = useState('');
  const [profilePhotoUrl, setProfilePhotoUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Add photo URLs to form data
      const registrationData = {
        ...formData,
        license_photo_url: licensePhotoUrl,
        vehicle_photo_url: vehiclePhotoUrl,
        profile_photo_url: profilePhotoUrl
      };

      const response = await axios.post(`${API}/register/courier`, registrationData);
      
      onComplete(response.data);
      toast.success('Kurye kaydınız tamamlandı! KYC onayı bekliyor.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Kayıt başarısız');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-orange-600">Kurye Kaydı</CardTitle>
        <CardDescription>Kurye olarak çalışmak için bilgilerinizi doldurun</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Email ve Şifre */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>E-posta *</Label>
              <Input
                type="email"
                placeholder="ornek@email.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                data-testid="courier-email"
              />
            </div>
            <div>
              <Label>Şifre *</Label>
              <Input
                type="password"
                placeholder="Güvenli şifre"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                data-testid="courier-password"
              />
            </div>
          </div>

          {/* Kişisel Bilgiler */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Ad *</Label>
              <Input
                placeholder="Adınız"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                required
                data-testid="courier-first-name"
              />
            </div>
            <div>
              <Label>Soyad *</Label>
              <Input
                placeholder="Soyadınız"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                required
                data-testid="courier-last-name"
              />
            </div>
          </div>

          {/* Şehir ve IBAN */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Şehir *</Label>
              <Select onValueChange={(value) => setFormData({...formData, city: value})} required>
                <SelectTrigger data-testid="courier-city-select">
                  <SelectValue placeholder="Şehir seçin" />
                </SelectTrigger>
                <SelectContent className="max-h-60 overflow-y-auto">
                  <SelectItem value="Adana">🌾 Adana</SelectItem>
                  <SelectItem value="Adiyaman">🏔️ Adıyaman</SelectItem>
                  <SelectItem value="Afyonkarahisar">🌸 Afyonkarahisar</SelectItem>
                  <SelectItem value="Agri">⛰️ Ağrı</SelectItem>
                  <SelectItem value="Aksaray">🏛️ Aksaray</SelectItem>
                  <SelectItem value="Amasya">🍎 Amasya</SelectItem>
                  <SelectItem value="Ankara">🏛️ Ankara</SelectItem>
                  <SelectItem value="Antalya">🏖️ Antalya</SelectItem>
                  <SelectItem value="Ardahan">❄️ Ardahan</SelectItem>
                  <SelectItem value="Artvin">🌲 Artvin</SelectItem>
                  <SelectItem value="Aydin">🫒 Aydın</SelectItem>
                  <SelectItem value="Balikesir">🐟 Balıkesir</SelectItem>
                  <SelectItem value="Bartin">⚓ Bartın</SelectItem>
                  <SelectItem value="Batman">🛢️ Batman</SelectItem>
                  <SelectItem value="Bayburt">🏔️ Bayburt</SelectItem>
                  <SelectItem value="Bilecik">🏺 Bilecik</SelectItem>
                  <SelectItem value="Bingol">🏞️ Bingöl</SelectItem>
                  <SelectItem value="Bitlis">🏔️ Bitlis</SelectItem>
                  <SelectItem value="Bolu">🌲 Bolu</SelectItem>
                  <SelectItem value="Burdur">🌊 Burdur</SelectItem>
                  <SelectItem value="Bursa">🌳 Bursa</SelectItem>
                  <SelectItem value="Canakkale">⚔️ Çanakkale</SelectItem>
                  <SelectItem value="Cankiri">🏞️ Çankırı</SelectItem>
                  <SelectItem value="Corum">🌾 Çorum</SelectItem>
                  <SelectItem value="Denizli">🏔️ Denizli</SelectItem>
                  <SelectItem value="Diyarbakir">🏛️ Diyarbakır</SelectItem>
                  <SelectItem value="Duzce">🌲 Düzce</SelectItem>
                  <SelectItem value="Edirne">🏰 Edirne</SelectItem>
                  <SelectItem value="Elazig">🏔️ Elazığ</SelectItem>
                  <SelectItem value="Erzincan">⛰️ Erzincan</SelectItem>
                  <SelectItem value="Erzurum">🏔️ Erzurum</SelectItem>
                  <SelectItem value="Eskisehir">🎓 Eskişehir</SelectItem>
                  <SelectItem value="Gaziantep">🍯 Gaziantep</SelectItem>
                  <SelectItem value="Giresun">🌰 Giresun</SelectItem>
                  <SelectItem value="Gumushane">⛏️ Gümüşhane</SelectItem>
                  <SelectItem value="Hakkari">🏔️ Hakkâri</SelectItem>
                  <SelectItem value="Hatay">🌶️ Hatay</SelectItem>
                  <SelectItem value="Igdir">🏔️ Iğdır</SelectItem>
                  <SelectItem value="Isparta">🌹 Isparta</SelectItem>
                  <SelectItem value="Istanbul">🏙️ İstanbul</SelectItem>
                  <SelectItem value="Izmir">🌊 İzmir</SelectItem>
                  <SelectItem value="Kahramanmaras">🍦 Kahramanmaraş</SelectItem>
                  <SelectItem value="Karabuk">🔥 Karabük</SelectItem>
                  <SelectItem value="Karaman">🏛️ Karaman</SelectItem>
                  <SelectItem value="Kars">❄️ Kars</SelectItem>
                  <SelectItem value="Kastamonu">🌰 Kastamonu</SelectItem>
                  <SelectItem value="Kayseri">⛰️ Kayseri</SelectItem>
                  <SelectItem value="Kirikkale">🏭 Kırıkkale</SelectItem>
                  <SelectItem value="Kirklareli">🌾 Kırklareli</SelectItem>
                  <SelectItem value="Kirsehir">🏛️ Kırşehir</SelectItem>
                  <SelectItem value="Kilis">🏛️ Kilis</SelectItem>
                  <SelectItem value="Kocaeli">🏭 Kocaeli</SelectItem>
                  <SelectItem value="Konya">🕌 Konya</SelectItem>
                  <SelectItem value="Kutahya">🏺 Kütahya</SelectItem>
                  <SelectItem value="Malatya">🍑 Malatya</SelectItem>
                  <SelectItem value="Manisa">🍇 Manisa</SelectItem>
                  <SelectItem value="Mardin">🏛️ Mardin</SelectItem>
                  <SelectItem value="Mersin">🚢 Mersin</SelectItem>
                  <SelectItem value="Mugla">🏖️ Muğla</SelectItem>
                  <SelectItem value="Mus">🏔️ Muş</SelectItem>
                  <SelectItem value="Nevsehir">🎈 Nevşehir</SelectItem>
                  <SelectItem value="Nigde">🍒 Niğde</SelectItem>
                  <SelectItem value="Ordu">🌰 Ordu</SelectItem>
                  <SelectItem value="Osmaniye">🌾 Osmaniye</SelectItem>
                  <SelectItem value="Rize">🫖 Rize</SelectItem>
                  <SelectItem value="Sakarya">🏭 Sakarya</SelectItem>
                  <SelectItem value="Samsun">⚓ Samsun</SelectItem>
                  <SelectItem value="Sanliurfa">🏛️ Şanlıurfa</SelectItem>
                  <SelectItem value="Siirt">🏔️ Siirt</SelectItem>
                  <SelectItem value="Sinop">⚓ Sinop</SelectItem>
                  <SelectItem value="Sirnak">🏔️ Şırnak</SelectItem>
                  <SelectItem value="Sivas">🏛️ Sivas</SelectItem>
                  <SelectItem value="Tekirdag">🌾 Tekirdağ</SelectItem>
                  <SelectItem value="Tokat">🌾 Tokat</SelectItem>
                  <SelectItem value="Trabzon">🏔️ Trabzon</SelectItem>
                  <SelectItem value="Tunceli">🏞️ Tunceli</SelectItem>
                  <SelectItem value="Usak">🏺 Uşak</SelectItem>
                  <SelectItem value="Van">🌊 Van</SelectItem>
                  <SelectItem value="Yalova">🌊 Yalova</SelectItem>
                  <SelectItem value="Yozgat">🌾 Yozgat</SelectItem>
                  <SelectItem value="Zonguldak">⚫ Zonguldak</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>IBAN *</Label>
              <Input
                placeholder="TR00 0000 0000 0000 0000 0000 00"
                value={formData.iban}
                onChange={(e) => setFormData({...formData, iban: e.target.value})}
                required
                data-testid="courier-iban"
              />
            </div>
          </div>

          {/* Ehliyet Bilgileri */}
          <div className="space-y-4 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-800">Ehliyet Bilgileri</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Ehliyet Sınıfı *</Label>
                <Select onValueChange={(value) => setFormData({...formData, license_class: value})}>
                  <SelectTrigger data-testid="courier-license-class">
                    <SelectValue placeholder="Seçiniz" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="A">A (Motosiklet)</SelectItem>
                    <SelectItem value="A1">A1 (Hafif Motosiklet)</SelectItem>
                    <SelectItem value="A2">A2 (Orta Motosiklet)</SelectItem>
                    <SelectItem value="B">B (Otomobil)</SelectItem>
                    <SelectItem value="C">C (Kamyon)</SelectItem>
                    <SelectItem value="D">D (Otobüs)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Ehliyet Numarası *</Label>
                <Input
                  placeholder="00000000"
                  value={formData.license_number}
                  onChange={(e) => setFormData({...formData, license_number: e.target.value})}
                  required
                  data-testid="courier-license-number"
                />
              </div>
            </div>
            
            {/* Ehliyet Fotoğrafı */}
            <FileUpload
              label="Ehliyet Fotoğrafı"
              accept="image/*"
              onFileUploaded={setLicensePhotoUrl}
              required={true}
            />
          </div>

          {/* Araç Bilgileri */}
          <div className="space-y-4 p-4 bg-green-50 rounded-lg">
            <h3 className="font-semibold text-green-800">Araç Bilgileri</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Araç Tipi *</Label>
                <Select onValueChange={(value) => setFormData({...formData, vehicle_type: value})}>
                  <SelectTrigger data-testid="courier-vehicle-type">
                    <SelectValue placeholder="Seçiniz" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="araba">Araba</SelectItem>
                    <SelectItem value="motor">Motosiklet</SelectItem>
                    <SelectItem value="elektrikli_motor">Elektrikli Motosiklet</SelectItem>
                    <SelectItem value="bisiklet">Bisiklet</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Araç Modeli *</Label>
                <Input
                  placeholder="Honda PCX 150"
                  value={formData.vehicle_model}
                  onChange={(e) => setFormData({...formData, vehicle_model: e.target.value})}
                  required
                  data-testid="courier-vehicle-model"
                />
              </div>
            </div>

            {/* Araç Fotoğrafı */}
            <FileUpload
              label="Araç Fotoğrafı"
              accept="image/*"
              onFileUploaded={setVehiclePhotoUrl}
              required={true}
            />
          </div>

          {/* Profil Fotoğrafı */}
          <div className="space-y-4 p-4 bg-orange-50 rounded-lg">
            <h3 className="font-semibold text-orange-800">Profil Fotoğrafı</h3>
            <FileUpload
              label="Profil Fotoğrafınız"
              accept="image/*"
              onFileUploaded={setProfilePhotoUrl}
              required={true}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Adınız</Label>
              <Input
                placeholder="Adınız"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                required
                data-testid="courier-first-name"
              />
            </div>
            <div>
              <Label>Soyadınız</Label>
              <Input
                placeholder="Soyadınız"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                required
                data-testid="courier-last-name"
              />
            </div>
          </div>
          
          <div>
            <Label>IBAN</Label>
            <Input
              placeholder="TR ile başlayan IBAN numarası"
              value={formData.iban}
              onChange={(e) => setFormData({...formData, iban: e.target.value})}
              required
              data-testid="courier-iban"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Araç Türü</Label>
              <Select onValueChange={(value) => setFormData({...formData, vehicle_type: value})} required>
                <SelectTrigger data-testid="courier-vehicle-select">
                  <SelectValue placeholder="Araç türünüz" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="araba">Araba</SelectItem>
                  <SelectItem value="motor">Motor</SelectItem>
                  <SelectItem value="elektrikli_motor">Elektrikli Motor</SelectItem>
                  <SelectItem value="bisiklet">Bisiklet</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Araç Modeli</Label>
              <Input
                placeholder="Örn: Honda Civic, Yamaha R25"
                value={formData.vehicle_model}
                onChange={(e) => setFormData({...formData, vehicle_model: e.target.value})}
                required
                data-testid="courier-vehicle-model"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Ehliyet Sınıfı</Label>
              <Input
                placeholder="A, A1, A2, B, C, D"
                value={formData.license_class}
                onChange={(e) => setFormData({...formData, license_class: e.target.value})}
                required
                data-testid="courier-license-class"
              />
            </div>
            <div>
              <Label>Şehir</Label>
              <CitySelector 
                value={formData.city}
                onChange={(value) => setFormData({...formData, city: value})}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FileUpload
              label="Ehliyet Fotoğrafı"
              onFileUploaded={setLicensePhotoUrl}
              accept="image/*"
            />
            <FileUpload
              label="Araç Fotoğrafı"
              onFileUploaded={setVehiclePhotoUrl}
              accept="image/*"
            />
          </div>
          
          <div className="flex gap-4">
            <Button 
              type="submit" 
              disabled={loading}
              className="flex-1 bg-orange-600 hover:bg-orange-700"
              data-testid="courier-register-btn"
            >
              {loading ? 'Kaydediliyor...' : 'Kurye Kaydını Tamamla'}
            </Button>
            <Button onClick={onBack} variant="outline" className="flex-1">
              ← Geri Dön
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

const BusinessRegistration = ({ onComplete, onBack }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    business_name: '',
    tax_number: '',
    address: '',
    city: '',
    business_category: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/register/business`, formData);
      onComplete(response.data);
      toast.success('İşletme kaydınız tamamlandı!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Kayıt başarısız');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-blue-600">İşletme Kaydı</CardTitle>
        <CardDescription>İşletmenizi platforma kaydedin</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>E-posta *</Label>
              <Input
                type="email"
                placeholder="isletme@email.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                data-testid="business-email"
              />
            </div>
            <div>
              <Label>Şifre *</Label>
              <Input
                type="password"
                placeholder="Güvenli şifre"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                data-testid="business-password"
              />
            </div>
          </div>

          <div>
            <Label>İşletme Adı</Label>
            <Input
              placeholder="İşletme adı"
              value={formData.business_name}
              onChange={(e) => setFormData({...formData, business_name: e.target.value})}
              required
              data-testid="business-name"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Vergi Numarası</Label>
              <Input
                placeholder="Vergi numarası"
                value={formData.tax_number}
                onChange={(e) => setFormData({...formData, tax_number: e.target.value})}
                required
                data-testid="business-tax-number"
              />
            </div>
            <div>
              <Label>Şehir</Label>
              <Select onValueChange={(value) => setFormData({...formData, city: value})} required>
                <SelectTrigger data-testid="business-city-select">
                  <SelectValue placeholder="Şehir seçin" />
                </SelectTrigger>
                <SelectContent className="max-h-60 overflow-y-auto">
                  <SelectItem value="Adana">🌾 Adana</SelectItem>
                  <SelectItem value="Adiyaman">🏔️ Adıyaman</SelectItem>
                  <SelectItem value="Afyonkarahisar">🌸 Afyonkarahisar</SelectItem>
                  <SelectItem value="Agri">⛰️ Ağrı</SelectItem>
                  <SelectItem value="Aksaray">🏛️ Aksaray</SelectItem>
                  <SelectItem value="Amasya">🍎 Amasya</SelectItem>
                  <SelectItem value="Ankara">🏛️ Ankara</SelectItem>
                  <SelectItem value="Antalya">🏖️ Antalya</SelectItem>
                  <SelectItem value="Ardahan">❄️ Ardahan</SelectItem>
                  <SelectItem value="Artvin">🌲 Artvin</SelectItem>
                  <SelectItem value="Aydin">🫒 Aydın</SelectItem>
                  <SelectItem value="Balikesir">🐟 Balıkesir</SelectItem>
                  <SelectItem value="Bartin">⚓ Bartın</SelectItem>
                  <SelectItem value="Batman">🛢️ Batman</SelectItem>
                  <SelectItem value="Bayburt">🏔️ Bayburt</SelectItem>
                  <SelectItem value="Bilecik">🏺 Bilecik</SelectItem>
                  <SelectItem value="Bingol">🏞️ Bingöl</SelectItem>
                  <SelectItem value="Bitlis">🏔️ Bitlis</SelectItem>
                  <SelectItem value="Bolu">🌲 Bolu</SelectItem>
                  <SelectItem value="Burdur">🌊 Burdur</SelectItem>
                  <SelectItem value="Bursa">🌳 Bursa</SelectItem>
                  <SelectItem value="Canakkale">⚔️ Çanakkale</SelectItem>
                  <SelectItem value="Cankiri">🏞️ Çankırı</SelectItem>
                  <SelectItem value="Corum">🌾 Çorum</SelectItem>
                  <SelectItem value="Denizli">🏔️ Denizli</SelectItem>
                  <SelectItem value="Diyarbakir">🏛️ Diyarbakır</SelectItem>
                  <SelectItem value="Duzce">🌲 Düzce</SelectItem>
                  <SelectItem value="Edirne">🏰 Edirne</SelectItem>
                  <SelectItem value="Elazig">🏔️ Elazığ</SelectItem>
                  <SelectItem value="Erzincan">⛰️ Erzincan</SelectItem>
                  <SelectItem value="Erzurum">🏔️ Erzurum</SelectItem>
                  <SelectItem value="Eskisehir">🎓 Eskişehir</SelectItem>
                  <SelectItem value="Gaziantep">🍯 Gaziantep</SelectItem>
                  <SelectItem value="Giresun">🌰 Giresun</SelectItem>
                  <SelectItem value="Gumushane">⛏️ Gümüşhane</SelectItem>
                  <SelectItem value="Hakkari">🏔️ Hakkâri</SelectItem>
                  <SelectItem value="Hatay">🌶️ Hatay</SelectItem>
                  <SelectItem value="Igdir">🏔️ Iğdır</SelectItem>
                  <SelectItem value="Isparta">🌹 Isparta</SelectItem>
                  <SelectItem value="Istanbul">🏙️ İstanbul</SelectItem>
                  <SelectItem value="Izmir">🌊 İzmir</SelectItem>
                  <SelectItem value="Kahramanmaras">🍦 Kahramanmaraş</SelectItem>
                  <SelectItem value="Karabuk">🔥 Karabük</SelectItem>
                  <SelectItem value="Karaman">🏛️ Karaman</SelectItem>
                  <SelectItem value="Kars">❄️ Kars</SelectItem>
                  <SelectItem value="Kastamonu">🌰 Kastamonu</SelectItem>
                  <SelectItem value="Kayseri">⛰️ Kayseri</SelectItem>
                  <SelectItem value="Kirikkale">🏭 Kırıkkale</SelectItem>
                  <SelectItem value="Kirklareli">🌾 Kırklareli</SelectItem>
                  <SelectItem value="Kirsehir">🏛️ Kırşehir</SelectItem>
                  <SelectItem value="Kilis">🏛️ Kilis</SelectItem>
                  <SelectItem value="Kocaeli">🏭 Kocaeli</SelectItem>
                  <SelectItem value="Konya">🕌 Konya</SelectItem>
                  <SelectItem value="Kutahya">🏺 Kütahya</SelectItem>
                  <SelectItem value="Malatya">🍑 Malatya</SelectItem>
                  <SelectItem value="Manisa">🍇 Manisa</SelectItem>
                  <SelectItem value="Mardin">🏛️ Mardin</SelectItem>
                  <SelectItem value="Mersin">🚢 Mersin</SelectItem>
                  <SelectItem value="Mugla">🏖️ Muğla</SelectItem>
                  <SelectItem value="Mus">🏔️ Muş</SelectItem>
                  <SelectItem value="Nevsehir">🎈 Nevşehir</SelectItem>
                  <SelectItem value="Nigde">🍒 Niğde</SelectItem>
                  <SelectItem value="Ordu">🌰 Ordu</SelectItem>
                  <SelectItem value="Osmaniye">🌾 Osmaniye</SelectItem>
                  <SelectItem value="Rize">🫖 Rize</SelectItem>
                  <SelectItem value="Sakarya">🏭 Sakarya</SelectItem>
                  <SelectItem value="Samsun">⚓ Samsun</SelectItem>
                  <SelectItem value="Sanliurfa">🏛️ Şanlıurfa</SelectItem>
                  <SelectItem value="Siirt">🏔️ Siirt</SelectItem>
                  <SelectItem value="Sinop">⚓ Sinop</SelectItem>
                  <SelectItem value="Sirnak">🏔️ Şırnak</SelectItem>
                  <SelectItem value="Sivas">🏛️ Sivas</SelectItem>
                  <SelectItem value="Tekirdag">🌾 Tekirdağ</SelectItem>
                  <SelectItem value="Tokat">🌾 Tokat</SelectItem>
                  <SelectItem value="Trabzon">🏔️ Trabzon</SelectItem>
                  <SelectItem value="Tunceli">🏞️ Tunceli</SelectItem>
                  <SelectItem value="Usak">🏺 Uşak</SelectItem>
                  <SelectItem value="Van">🌊 Van</SelectItem>
                  <SelectItem value="Yalova">🌊 Yalova</SelectItem>
                  <SelectItem value="Yozgat">🌾 Yozgat</SelectItem>
                  <SelectItem value="Zonguldak">⚫ Zonguldak</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div>
            <Label>İşletme Adresi</Label>
            <Textarea
              placeholder="İşletme adresi"
              value={formData.address}
              onChange={(e) => setFormData({...formData, address: e.target.value})}
              required
              data-testid="business-address"
            />
          </div>
          
          <div>
            <Label>Ne satıyorsunuz?</Label>
            <Select onValueChange={(value) => setFormData({...formData, business_category: value})} required>
              <SelectTrigger data-testid="business-category-select">
                <SelectValue placeholder="Kategori seçin" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="gida">🍔 Gıda (Restoran, Cafe, Pastane)</SelectItem>
                <SelectItem value="nakliye">📦 Nakliye (Kargo, Paket Teslimat)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>İşletme Açıklaması (Opsiyonel)</Label>
            <Textarea
              placeholder="İşletmeniz hakkında kısa bilgi..."
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              data-testid="business-description"
            />
          </div>
          
          <div className="flex gap-4">
            <Button 
              type="submit" 
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              data-testid="business-register-btn"
            >
              {loading ? 'Kaydediliyor...' : 'İşletme Kaydını Tamamla'}
            </Button>
            <Button onClick={onBack} variant="outline" className="flex-1">
              ← Geri Dön
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

const CustomerRegistration = ({ onComplete, onBack }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    city: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/register/customer`, formData);
      onComplete(response.data);
      toast.success('Müşteri kaydınız tamamlandı!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Kayıt başarısız');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-green-600">Müşteri Kaydı</CardTitle>
        <CardDescription>Sipariş vermek için kaydolun</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>E-posta *</Label>
              <Input
                type="email"
                placeholder="ornek@email.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
                data-testid="customer-email"
              />
            </div>
            <div>
              <Label>Şifre *</Label>
              <Input
                type="password"
                placeholder="Güvenli şifre"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                data-testid="customer-password"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Adınız</Label>
              <Input
                placeholder="Adınız"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                required
                data-testid="customer-first-name"
              />
            </div>
            <div>
              <Label>Soyadınız</Label>
              <Input
                placeholder="Soyadınız"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                required
                data-testid="customer-last-name"
              />
            </div>
          </div>

          <div>
            <Label>Şehir</Label>
            <CitySelector 
              value={formData.city}
              onChange={(value) => setFormData({...formData, city: value})}
              required
            />
          </div>
          
          <div className="flex gap-4">
            <Button 
              type="submit" 
              disabled={loading}
              className="flex-1 bg-green-600 hover:bg-green-700"
              data-testid="customer-register-btn"
            >
              {loading ? 'Kaydediliyor...' : 'Müşteri Kaydını Tamamla'}
            </Button>
            <Button onClick={onBack} variant="outline" className="flex-1">
              ← Geri Dön
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

// Dashboard Components  
const CourierDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [isOnline, setIsOnline] = useState(user.is_online || false);
  const [currentView, setCurrentView] = useState('nearby');
  const [myOrders, setMyOrders] = useState([]);
  const [nearbyOrders, setNearbyOrders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [courierLocation, setCourierLocation] = useState(null);
  const [routePolyline, setRoutePolyline] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);

  // KYC Status Check
  const isKYCApproved = user.kyc_status === 'approved';

  useEffect(() => {
    if (currentView === 'orders') {
      fetchMyOrders();
    } else if (currentView === 'nearby' && isKYCApproved) {
      fetchNearbyOrders();
    }
  }, [currentView, isKYCApproved]);

  const fetchMyOrders = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/orders`);
      setMyOrders(response.data);
    } catch (error) {
      console.error('Siparişler alınamadı:', error);
    }
    setLoading(false);
  };

  const fetchNearbyOrders = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/orders/nearby`);
      setNearbyOrders(response.data || []);
    } catch (error) {
      console.error('Yakındaki siparişler alınamadı:', error);
      setNearbyOrders([]);
    }
    setLoading(false);
  };

  // Location update handler
  const handleLocationUpdate = (location) => {
    setCourierLocation(location);
    // Update nearby orders distances
    if (nearbyOrders.length > 0) {
      updateOrderDistances(location);
    }
  };

  const updateOrderDistances = (currentLocation) => {
    const updatedOrders = nearbyOrders.map(order => {
      // Calculate distance using Haversine formula (simplified)
      const distance = calculateDistance(
        currentLocation.lat,
        currentLocation.lng,
        order.pickup_address?.lat || 41.0082, // Default Istanbul coords
        order.pickup_address?.lng || 28.9784
      );
      
      return {
        ...order,
        distance_km: distance.toFixed(1),
        estimated_duration: `${Math.round(distance * 3)} dk` // Rough estimate: 3 min per km
      };
    });
    
    setNearbyOrders(updatedOrders);
  };

  // Simple distance calculation (Haversine formula)
  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  // Get route to order location
  const getRouteToOrder = async (order) => {
    if (!courierLocation) {
      toast.error('Konum bilginiz alınamadı, lütfen konumunuzu açın');
      return;
    }

    setSelectedOrder(order);
    
    // Demo route calculation - in real app would use routing service
    const pickupLat = order.pickup_address?.lat || 41.0082;
    const pickupLng = order.pickup_address?.lng || 28.9784;
    const deliveryLat = order.delivery_address?.lat || 41.0122;
    const deliveryLng = order.delivery_address?.lng || 28.9824;
    
    // Create a simple route polyline
    const route = [
      [courierLocation.lat, courierLocation.lng], // Current location
      [pickupLat, pickupLng], // Pickup location
      [deliveryLat, deliveryLng] // Delivery location
    ];
    
    setRoutePolyline(route);
    
    toast.success(`🧭 ${order.business_name || 'Sipariş'} için yol tarifi hazırlandı!`);
    
    // Open external navigation app
    const googleMapsUrl = `https://www.google.com/maps/dir/${courierLocation.lat},${courierLocation.lng}/${pickupLat},${pickupLng}`;
    window.open(googleMapsUrl, '_blank');
  };

  // Generate map markers for nearby orders
  const getMapMarkers = () => {
    const markers = [];
    
    // Add nearby orders as markers
    nearbyOrders.forEach((order, index) => {
      // Pickup location (business)
      markers.push({
        lat: order.pickup_address?.lat || (41.0082 + (index * 0.01)),
        lng: order.pickup_address?.lng || (28.9784 + (index * 0.01)),
        type: 'pickup',
        popup: true,
        title: `🏪 ${order.business_name || 'İşletme'}`,
        description: 'Paket alım noktası',
        address: order.pickup_address?.address || 'Adres bilgisi yok',
        distance: order.distance_km ? `${order.distance_km} km` : null,
        estimatedTime: order.estimated_duration || null,
        orderValue: `₺${order.total_amount} (Komisyon: ₺${order.commission_amount})`,
        onNavigate: () => getRouteToOrder(order)
      });
      
      // Delivery location (customer)
      markers.push({
        lat: order.delivery_address?.lat || (41.0122 + (index * 0.01)),
        lng: order.delivery_address?.lng || (28.9824 + (index * 0.01)),
        type: 'package',
        popup: true,
        title: `📦 ${order.customer_name || 'Müşteri'}`,
        description: 'Paket teslim noktası',
        address: order.delivery_address?.address || 'Teslimat adresi',
        distance: order.distance_km ? `${order.distance_km} km` : null,
        estimatedTime: order.estimated_duration || null,
        orderValue: `₺${order.total_amount}`,
        onNavigate: () => getRouteToOrder(order)
      });
    });
    
    return markers;
  };

  const getKYCStatusBadge = (status) => {
    const statusConfig = {
      pending: { text: "⏳ KYC Onay Bekliyor", className: "bg-yellow-100 text-yellow-800" },
      approved: { text: "✅ KYC Onaylandı", className: "bg-green-100 text-green-800" },
      rejected: { text: "❌ KYC Reddedildi", className: "bg-red-100 text-red-800" }
    };
    
    const config = statusConfig[status] || statusConfig.pending;
    return <Badge className={config.className} data-testid="kyc-status-badge">{config.text}</Badge>;
  };

  // KYC Warning Component
  const KYCWarning = () => (
    <Card className="border-yellow-200 bg-yellow-50">
      <CardContent className="p-4">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">⚠️</div>
          <div className="flex-1">
            <h3 className="font-semibold text-yellow-800">KYC Onayı Gerekli</h3>
            <p className="text-sm text-yellow-700">
              {user.kyc_status === 'pending' ? 
                'Belgeleriniz inceleniyor. Onaylandıktan sonra sipariş alabilirsiniz.' :
                'Belgeleriniz reddedildi. Lütfen yeni belgeler yükleyip tekrar başvurun.'
              }
            </p>
            {getKYCStatusBadge(user.kyc_status)}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-2 sm:p-4" data-testid="courier-dashboard">
      {/* Mobile-Responsive Header */}
      <div className="bg-white shadow-lg rounded-lg mb-4 sm:mb-6">
        <div className="p-3 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h1 className="text-lg sm:text-2xl font-bold text-gray-900">
                Kurye Panel - {user.first_name} {user.last_name}
              </h1>
              <p className="text-sm text-gray-600">
                {user.city} • {user.vehicle_type} • {user.vehicle_model}
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
              {getKYCStatusBadge(user.kyc_status)}
              {isKYCApproved && (
                <Badge 
                  className={isOnline ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}
                  data-testid="online-status"
                >
                  {isOnline ? "🟢 Çevrimiçi" : "⚫ Çevrimdışı"}
                </Badge>
              )}
              <Button onClick={logout} variant="outline" size="sm">
                <span className="hidden sm:inline">Çıkış</span>
                <span className="sm:hidden">🚪</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* KYC Warning */}
      {!isKYCApproved && (
        <div className="mb-4 sm:mb-6">
          <KYCWarning />
        </div>
      )}

      {/* Main Content - Only show if KYC approved */}
      {isKYCApproved ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Left Column - Orders & Map */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg">Yakındaki Siparişler</CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Size yakın siparişleri görüntüleyin ve kabul edin
                </CardDescription>
              </CardHeader>
              <CardContent>
                <NearbyOrdersForCourier />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  🗺️ Kurye Haritası
                  {courierLocation && (
                    <Badge variant="outline" className="bg-green-50 border-green-200 text-green-800 text-xs">
                      📍 Konum Aktif
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Canlı konumunuz ve yakındaki siparişler
                  {selectedOrder && (
                    <span className="block text-blue-600 mt-1">
                      🧭 {selectedOrder.business_name} için yol tarifi aktif
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <LeafletMap
                  center={courierLocation ? [courierLocation.lat, courierLocation.lng] : [41.0082, 28.9784]}
                  zoom={courierLocation ? 14 : 12}
                  height="400px"
                  markers={getMapMarkers()}
                  showLocationButton={true}
                  courierMode={true}
                  onLocationUpdate={handleLocationUpdate}
                  routePolyline={routePolyline}
                />
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Stats & Profile */}
          <div className="space-y-4 sm:space-y-6">
            {/* Balance Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg">Bakiye</CardTitle>
              </CardHeader>
              <CardContent>
                <CourierBalance />
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg">Hızlı İşlemler</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  onClick={() => setIsOnline(!isOnline)}
                  className={`w-full ${isOnline ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}`}
                  size="sm"
                >
                  {isOnline ? '⏸️ Çevrimdışı Ol' : '▶️ Çevrimiçi Ol'}
                </Button>
                
                <Button
                  onClick={() => setCurrentView('orders')}
                  variant="outline"
                  className="w-full"
                  size="sm"
                >
                  📦 Siparişlerim
                </Button>
              </CardContent>
            </Card>

            {/* Profile Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg">Profil Özeti</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-xs sm:text-sm space-y-1">
                  <p><strong>Ehliyet:</strong> {user.license_class} - {user.license_number}</p>
                  <p><strong>IBAN:</strong> {user.iban?.slice(-4).padStart(user.iban?.length || 0, '*')}</p>
                  <p><strong>Bakiye:</strong> ₺{user.balance || '0.00'}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        // Show message when KYC not approved
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📋</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">KYC Onayı Bekleniyor</h2>
          <p className="text-gray-600">
            Belgeleriniz admin tarafından incelendikten sonra sipariş almaya başlayabilirsiniz.
          </p>
        </div>
      )}
    </div>
  );
};

// Business Dashboard - Enhanced with Product Management
const BusinessDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  // Product form state
  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    preparation_time_minutes: 30,
    photo_url: '',
    is_available: true
  });

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/products/my`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setProducts(response.data);
    } catch (error) {
      console.error('Product fetch error:', error);
      toast.error('Ürünler yüklenemedi');
    }
    setLoading(false);
  };

  const fetchOrders = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      const response = await axios.get(`${API}/orders`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setOrders(response.data);
    } catch (error) {
      console.error('Orders fetch error:', error);
      toast.error('Siparişler yüklenemedi');
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchOrders();
  }, []);

  const handleProductSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const productData = {
        ...productForm,
        price: parseFloat(productForm.price),
        preparation_time_minutes: parseInt(productForm.preparation_time_minutes)
      };

      const token = localStorage.getItem('kuryecini_access_token');
      await axios.post(`${API}/products`, productData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      toast.success('Ürün başarıyla eklendi!');
      setProductForm({
        name: '',
        description: '',
        price: '',
        category: '',
        preparation_time_minutes: 30,
        photo_url: '',
        is_available: true
      });
      fetchProducts();
    } catch (error) {
      console.error('Product creation error:', error);
      toast.error(error.response?.data?.detail || 'Ürün eklenemedi');
    }
    setLoading(false);
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      await axios.patch(`${API}/orders/${orderId}/status?new_status=${newStatus}`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      toast.success('Sipariş durumu güncellendi');
      fetchOrders();
    } catch (error) {
      console.error('Order status update error:', error);
      toast.error('Durum güncellenemedi');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      {/* Mobile-Responsive Header */}
      <div className="bg-white/70 backdrop-blur-lg border-b border-gray-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-16">
            <div className="flex items-center space-x-2 sm:space-x-4">
              <div className="text-xl sm:text-2xl">🏪</div>
              <div>
                <h1 className="text-sm sm:text-xl font-semibold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                  <span className="hidden sm:inline">{user.business_name || 'İşletme'} - </span>Yönetim
                </h1>
                <p className="text-xs text-gray-600 hidden sm:block">
                  Kuryecini İşletme Yönetim Paneli
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4">
              <Badge variant="outline" className="bg-green-50 border-green-200 text-green-800 text-xs">
                İşletme
              </Badge>
              <Button onClick={logout} variant="outline" size="sm">
                <span className="hidden sm:inline">Çıkış</span>
                <span className="sm:hidden">🚪</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3 mb-6 bg-white/60 backdrop-blur-lg">
            <TabsTrigger value="products" className="text-xs sm:text-sm">
              <span className="mr-1 sm:mr-2">📦</span>
              <span className="hidden sm:inline">Ürünler</span>
              <span className="sm:hidden">Ürün</span>
            </TabsTrigger>
            <TabsTrigger value="orders" className="text-xs sm:text-sm">
              <span className="mr-1 sm:mr-2">🧾</span>
              <span className="hidden sm:inline">Siparişler</span>
              <span className="sm:hidden">Sipariş</span>
            </TabsTrigger>
            <TabsTrigger value="map" className="text-xs sm:text-sm">
              <span className="mr-1 sm:mr-2">🗺️</span>
              Harita
            </TabsTrigger>
          </TabsList>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-4 sm:space-y-6">
            {/* Add Product Form */}
            <Card className="border-0 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50">
                <CardTitle className="flex items-center text-sm sm:text-lg">
                  <span className="mr-2">➕</span>
                  Yeni Ürün Ekle
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Müşterileriniz için yeni ürün ekleyin
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                <form onSubmit={handleProductSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs sm:text-sm font-semibold">Ürün Adı *</Label>
                      <Input
                        value={productForm.name}
                        onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                        placeholder="Margherita Pizza"
                        className="mt-1"
                        required
                      />
                    </div>
                    <div>
                      <Label className="text-xs sm:text-sm font-semibold">Fiyat (₺) *</Label>
                      <Input
                        type="number"
                        step="0.01"
                        min="0"
                        value={productForm.price}
                        onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                        placeholder="25.50"
                        className="mt-1"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-xs sm:text-sm font-semibold">Açıklama *</Label>
                    <Textarea
                      value={productForm.description}
                      onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                      placeholder="Ürün açıklaması... (Malzemeler, özellikler vs.)"
                      className="mt-1 resize-none"
                      rows="3"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs sm:text-sm font-semibold">Kategori *</Label>
                      <Select onValueChange={(value) => setProductForm({...productForm, category: value})} required>
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Kategori seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="pizza">🍕 Pizza</SelectItem>
                          <SelectItem value="burger">🍔 Burger</SelectItem>
                          <SelectItem value="kebab">🥙 Kebab</SelectItem>
                          <SelectItem value="pasta">🍝 Pasta</SelectItem>
                          <SelectItem value="salad">🥗 Salata</SelectItem>
                          <SelectItem value="soup">🍲 Çorba</SelectItem>
                          <SelectItem value="dessert">🍰 Tatlı</SelectItem>
                          <SelectItem value="drink">🥤 İçecek</SelectItem>
                          <SelectItem value="other">📦 Diğer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label className="text-xs sm:text-sm font-semibold">Hazırlanma Süresi (dk)</Label>
                      <Input
                        type="number"
                        min="5"
                        max="120"
                        value={productForm.preparation_time_minutes}
                        onChange={(e) => setProductForm({...productForm, preparation_time_minutes: parseInt(e.target.value)})}
                        className="mt-1"
                      />
                    </div>
                  </div>

                  <div>
                    <Label className="text-xs sm:text-sm font-semibold">Ürün Fotoğrafı</Label>
                    <FileUpload
                      label="Ürün Fotoğrafı"
                      onFileUploaded={(url) => setProductForm({...productForm, photo_url: url})}
                      accept="image/*"
                    />
                    {productForm.photo_url && (
                      <div className="mt-2">
                        <img 
                          src={`${BACKEND_URL}${productForm.photo_url}`} 
                          alt="Ürün fotoğrafı" 
                          className="w-20 h-20 object-cover rounded-lg border"
                        />
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="is_available"
                      checked={productForm.is_available}
                      onChange={(e) => setProductForm({...productForm, is_available: e.target.checked})}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor="is_available" className="text-xs sm:text-sm">
                      ✅ Ürün şu anda mevcut
                    </Label>
                  </div>

                  <Button 
                    type="submit" 
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-sm sm:text-base"
                  >
                    {loading ? '⏳ Ekleniyor...' : '➕ Ürün Ekle'}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Products List */}
            <Card className="border-0 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50">
                <CardTitle className="flex items-center text-sm sm:text-lg">
                  <span className="mr-2">📦</span>
                  Mevcut Ürünler ({products.length})
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Ürünlerinizi yönetin ve düzenleyin
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                {products.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-4xl sm:text-6xl mb-4">📦</div>
                    <p className="text-gray-500 text-sm sm:text-base">Henüz ürününüz yok</p>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">Yukarıdaki formdan yeni ürün ekleyin</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
                    {products.map((product) => (
                      <Card key={product.id} className="overflow-hidden hover:shadow-lg transition-shadow border-0 shadow-md">
                        {product.photo_url && (
                          <div className="h-28 sm:h-32 overflow-hidden relative">
                            <img 
                              src={`${BACKEND_URL}${product.photo_url}`} 
                              alt={product.name}
                              className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                            />
                            <Badge 
                              variant={product.is_available ? "default" : "secondary"}
                              className={`absolute top-2 right-2 text-xs ${
                                product.is_available ? 'bg-green-500 text-white' : 'bg-gray-500 text-white'
                              }`}
                            >
                              {product.is_available ? '✅ Mevcut' : '❌ Stokta Yok'}
                            </Badge>
                          </div>
                        )}
                        <CardContent className="p-3 sm:p-4">
                          <h3 className="font-semibold text-sm sm:text-base text-gray-900 mb-1">
                            {product.name}
                          </h3>
                          <p className="text-xs sm:text-sm text-gray-600 mb-3 line-clamp-2">
                            {product.description}
                          </p>
                          <div className="space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                                ₺{product.price}
                              </span>
                              <Badge variant="outline" className="text-xs">
                                📂 {product.category}
                              </Badge>
                            </div>
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              <span>⏱️ {product.preparation_time_minutes} dk</span>
                              <span>{product.is_available ? '🟢 Aktif' : '🔴 Pasif'}</span>
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

          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-4 sm:space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50">
                <CardTitle className="flex items-center text-sm sm:text-lg">
                  <span className="mr-2">🧾</span>
                  Gelen Siparişler ({orders.length})
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm">
                  Müşteri siparişlerini yönetin ve takip edin
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                {orders.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-4xl sm:text-6xl mb-4">🧾</div>
                    <p className="text-gray-500 text-sm sm:text-base">Henüz siparişiniz yok</p>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">Müşteriler sipariş vermeye başladığında burada göreceksiniz</p>
                  </div>
                ) : (
                  <div className="space-y-3 sm:space-y-4">
                    {orders.map((order) => (
                      <Card key={order.id} className="overflow-hidden border-0 shadow-md hover:shadow-lg transition-shadow">
                        <CardContent className="p-3 sm:p-4">
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                <h3 className="font-semibold text-sm sm:text-base">
                                  Sipariş #{order.id.slice(-8)}
                                </h3>
                                <OrderStatusBadge status={order.status} />
                              </div>
                              <div className="space-y-1 text-xs sm:text-sm text-gray-600">
                                <p className="flex items-center">
                                  <span className="mr-1">👤</span>
                                  {order.customer_name}
                                </p>
                                <p className="flex items-center">
                                  <span className="mr-1">📍</span>
                                  <span className="truncate">{order.delivery_address}</span>
                                </p>
                                <p className="flex items-center">
                                  <span className="mr-1">🕐</span>
                                  {new Date(order.created_at).toLocaleString('tr-TR')}
                                </p>
                              </div>
                            </div>
                            
                            <div className="text-left sm:text-right">
                              <p className="text-lg sm:text-xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                                ₺{order.total_amount}
                              </p>
                              <p className="text-xs sm:text-sm text-gray-500">
                                Komisyon: ₺{order.commission_amount?.toFixed(2) || '0.00'}
                              </p>
                            </div>
                          </div>

                          <div className="mt-3 pt-3 border-t border-gray-100">
                            <h4 className="font-medium mb-2 text-xs sm:text-sm text-gray-800">📋 Sipariş Detayları:</h4>
                            <div className="space-y-1">
                              {order.items.map((item, index) => (
                                <div key={index} className="flex justify-between items-center text-xs sm:text-sm">
                                  <span className="text-gray-600">
                                    {item.quantity}x {item.product_name}
                                  </span>
                                  <span className="font-medium text-gray-800">₺{item.subtotal}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {order.status === 'created' && (
                            <div className="mt-4 pt-3 border-t border-gray-100">
                              <Button 
                                onClick={() => updateOrderStatus(order.id, 'assigned')}
                                className="w-full bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 text-xs sm:text-sm"
                                size="sm"
                              >
                                ✅ Siparişi Onayla ve Hazırlamaya Başla
                              </Button>
                            </div>
                          )}
                          
                          {order.status === 'assigned' && (
                            <div className="mt-4 pt-3 border-t border-gray-100">
                              <Button 
                                onClick={() => updateOrderStatus(order.id, 'on_route')}
                                className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-xs sm:text-sm"
                                size="sm"
                              >
                                🚚 Kurye Teslim Edildi (Yola Çıktı)
                              </Button>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Map Tab */}
          <TabsContent value="map">
            <Card>
              <CardHeader>
                <CardTitle>Teslimat Haritası</CardTitle>
              </CardHeader>
              <CardContent>
                <LeafletMap
                  center={[39.925533, 32.866287]}
                  zoom={12}
                  height="500px"
                  markers={orders.filter(order => order.delivery_lat && order.delivery_lng).map(order => ({
                    lat: order.delivery_lat,
                    lng: order.delivery_lng,
                    type: 'delivery',
                    popup: true,
                    title: `Sipariş #${order.id.slice(-8)}`,
                    description: order.customer_name,
                    address: order.delivery_address
                  }))}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Customer Dashboard - Modern Tech Design
const CustomerDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [mapCenter, setMapCenter] = useState([39.925533, 32.866287]); // Default to Turkey center
  const [isMounted, setIsMounted] = useState(true); // Track component mount status
  const [orderForm, setOrderForm] = useState({
    delivery_address: '',
    delivery_lat: null,
    delivery_lng: null,
    notes: ''
  });

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (error) {
      toast.error('Ürünler yüklenemedi');
    }
    setLoading(false);
  };

  const fetchMyOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
      toast.error('Siparişler yüklenemedi');
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchMyOrders();
  }, []);

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.product_id === product.id);
    
    if (existingItem) {
      setCart(cart.map(item => 
        item.product_id === product.id 
          ? { ...item, quantity: item.quantity + 1, subtotal: (item.quantity + 1) * item.product_price }
          : item
      ));
    } else {
      setCart([...cart, {
        product_id: product.id,
        product_name: product.name,
        product_price: product.price,
        quantity: 1,
        subtotal: product.price
      }]);
    }
    
    toast.success(`${product.name} sepete eklendi! ✨`);
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
  };

  const updateCartQuantity = (productId, newQuantity) => {
    if (newQuantity === 0) {
      removeFromCart(productId);
      return;
    }
    
    setCart(cart.map(item => 
      item.product_id === productId 
        ? { ...item, quantity: newQuantity, subtotal: newQuantity * item.product_price }
        : item
    ));
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + item.subtotal, 0);
  };

  const handleOrderSubmit = async (e) => {
    e.preventDefault();
    
    if (cart.length === 0) {
      toast.error('Sepetiniz boş! 🛒');
      return;
    }
    
    if (!orderForm.delivery_address) {
      toast.error('Teslimat adresini girin! 📍');
      return;
    }

    setLoading(true);

    try {
      const orderData = {
        delivery_address: orderForm.delivery_address,
        delivery_lat: orderForm.delivery_lat,
        delivery_lng: orderForm.delivery_lng,
        items: cart,
        total_amount: getCartTotal(),
        notes: orderForm.notes
      };

      await axios.post(`${API}/orders`, orderData);
      
      toast.success('Sipariş başarıyla oluşturuldu! 🎉');
      setCart([]);
      setOrderForm({
        delivery_address: '',
        delivery_lat: null,
        delivery_lng: null,
        notes: ''
      });
      fetchMyOrders();
      setActiveTab('orders');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sipariş oluşturulamadı');
    }
    setLoading(false);
  };

  // Location Management Functions
  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      if (isMounted) {
        setLocationError('Tarayıcınız konum hizmetlerini desteklemiyor');
      }
      return;
    }

    setLocationError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (isMounted) {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setUserLocation(location);
          setMapCenter([location.lat, location.lng]);
          setLocationError(null);
          toast.success('Konumunuz güncellendi! 📍');
          
          // Update order form with new location
          setOrderForm(prev => ({
            ...prev,
            delivery_lat: location.lat,
            delivery_lng: location.lng
          }));
        }
      },
      (error) => {
        if (isMounted) {
          console.error('Konum alınamadı:', error);
          let errorMessage = 'Konum alınamadı';
          switch(error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = 'Konum erişimi reddedildi. Lütfen tarayıcı ayarlarından konum izni verin.';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = 'Konum bilgisi mevcut değil.';
              break;
            case error.TIMEOUT:
              errorMessage = 'Konum alma işlemi zaman aşımına uğradı.';
              break;
          }
          setLocationError(errorMessage);
          toast.error(errorMessage);
        }
      },
      { 
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 300000  // 5 minutes cache
      }
    );
  };

  // Get location on component mount
  useEffect(() => {
    setIsMounted(true);
    getCurrentLocation();
    
    // Cleanup function
    return () => {
      setIsMounted(false);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Modern Header with Glass Effect */}
      <div className="bg-white/70 backdrop-blur-lg border-b border-gray-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 sm:h-20">
            <div className="flex items-center space-x-4">
              <div className="text-2xl sm:text-3xl">🍽️</div>
              <div>
                <h1 className="text-lg sm:text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  DeliverTR
                </h1>
                <p className="text-xs sm:text-sm text-gray-600">
                  Merhaba, {user.first_name || 'Kullanıcı'}! 👋
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              {/* Cart Badge with Animation */}
              {cart.length > 0 && (
                <div className="relative">
                  <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-semibold flex items-center space-x-1 shadow-lg">
                    <span>🛒</span>
                    <span className="hidden sm:inline">Sepet:</span>
                    <span>{cart.length}</span>
                  </div>
                </div>
              )}
              
              <Button 
                onClick={logout} 
                variant="outline" 
                size="sm"
                className="bg-white/50 border-gray-300 hover:bg-white/80"
              >
                <span className="hidden sm:inline">Çıkış</span>
                <span className="sm:hidden">🚪</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-6 sm:py-8">
        {/* Modern Tab Navigation */}
        <div className="mb-8">
          <div className="flex space-x-2 sm:space-x-4 p-2 bg-white/60 backdrop-blur-lg rounded-2xl shadow-lg border border-gray-200/50">
            {[
              { id: 'products', icon: '🍽️', label: 'Keşfet', count: products.length },
              { id: 'cart', icon: '🛒', label: 'Sepet', count: cart.length },
              { id: 'orders', icon: '📦', label: 'Siparişler', count: orders.length },
              { id: 'map', icon: '🗺️', label: 'Harita', count: null }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center space-x-2 px-3 sm:px-6 py-3 rounded-xl transition-all duration-300 text-sm sm:text-base font-medium
                  ${activeTab === tab.id 
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg transform scale-105' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'
                  }
                `}
              >
                <span className="text-lg sm:text-xl">{tab.icon}</span>
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.count !== null && tab.count > 0 && (
                  <span className={`
                    text-xs px-2 py-1 rounded-full font-semibold
                    ${activeTab === tab.id ? 'bg-white/20' : 'bg-indigo-100 text-indigo-600'}
                  `}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* Products Tab - Professional Food Order System */}
          {activeTab === 'products' && (
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              <ProfessionalFoodOrderSystem />
            </div>
          )}

          {/* Cart Tab */}
          {activeTab === 'cart' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Cart Items */}
                <div className="lg:col-span-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>Sepetim ({cart.length} ürün)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {cart.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">Sepetiniz boş</p>
                      ) : (
                        <div className="space-y-4">
                          {cart.map((item) => (
                            <div key={item.product_id} className="flex items-center justify-between p-4 border rounded-lg">
                              <div className="flex-1">
                                <h4 className="font-medium">{item.product_name}</h4>
                                <p className="text-sm text-gray-600">₺{item.product_price} x {item.quantity}</p>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => updateCartQuantity(item.product_id, item.quantity - 1)}
                                >
                                  -
                                </Button>
                                <span className="w-8 text-center">{item.quantity}</span>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => updateCartQuantity(item.product_id, item.quantity + 1)}
                                >
                                  +
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => removeFromCart(item.product_id)}
                                >
                                  🗑️
                                </Button>
                              </div>
                              <div className="text-right ml-4">
                                <p className="font-bold">₺{item.subtotal.toFixed(2)}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Order Summary & Checkout */}
                <div>
                  <Card>
                    <CardHeader>
                      <CardTitle>Sipariş Özeti</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleOrderSubmit} className="space-y-4">
                        <div>
                          <Label>Teslimat Adresi *</Label>
                          <Textarea
                            value={orderForm.delivery_address}
                            onChange={(e) => setOrderForm({...orderForm, delivery_address: e.target.value})}
                            placeholder="Tam adresinizi yazın..."
                            required
                          />
                        </div>
                        
                        <div>
                          <Label>Sipariş Notu (Opsiyonel)</Label>
                          <Textarea
                            value={orderForm.notes}
                            onChange={(e) => setOrderForm({...orderForm, notes: e.target.value})}
                            placeholder="Özel istekleriniz..."
                          />
                        </div>
                        
                        <div className="border-t pt-4">
                          <div className="flex justify-between items-center mb-2">
                            <span>Ara Toplam:</span>
                            <span>₺{getCartTotal().toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between items-center mb-2">
                            <span>Teslimat:</span>
                            <span>Ücretsiz</span>
                          </div>
                          <div className="flex justify-between items-center font-bold text-lg border-t pt-2">
                            <span>Toplam:</span>
                            <span>₺{getCartTotal().toFixed(2)}</span>
                          </div>
                        </div>
                        
                        <Button 
                          type="submit" 
                          disabled={loading || cart.length === 0}
                          className="w-full bg-green-600 hover:bg-green-700"
                        >
                          {loading ? 'Sipariş Oluşturuluyor...' : 'Siparişi Tamamla'}
                        </Button>
                      </form>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          )}

          {/* Orders Tab */}
          {activeTab === 'orders' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Siparişlerim ({orders.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  {orders.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">Henüz siparişiniz yok</p>
                  ) : (
                    <div className="space-y-4">
                      {orders.map((order) => (
                        <Card key={order.id}>
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div>
                                <h3 className="font-semibold">Sipariş #{order.id.slice(-8)}</h3>
                                <p className="text-sm text-gray-600">{order.business_name}</p>
                                <p className="text-xs text-gray-500">{order.delivery_address}</p>
                              </div>
                              <div className="text-right">
                                <p className="font-bold text-lg">₺{order.total_amount}</p>
                                <OrderStatusBadge status={order.status} />
                              </div>
                            </div>

                            <div className="mb-3">
                              <h4 className="font-medium mb-1">Siparişler:</h4>
                              {order.items.map((item, index) => (
                                <div key={index} className="text-sm text-gray-600">
                                  {item.quantity}x {item.product_name} - ₺{item.subtotal}
                                </div>
                              ))}
                            </div>

                            <p className="text-xs text-gray-500">
                              Sipariş Tarihi: {new Date(order.created_at).toLocaleString('tr-TR')}
                            </p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Map Tab */}
          {activeTab === 'map' && (
            <div className="space-y-6">
              {/* Location Status Card */}
              <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-2xl">📍</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-800">Konum Durumu</h3>
                        {userLocation ? (
                          <p className="text-sm text-green-600">
                            ✅ Konumunuz aktif • {userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}
                          </p>
                        ) : locationError ? (
                          <p className="text-sm text-red-600">❌ {locationError}</p>
                        ) : (
                          <p className="text-sm text-yellow-600">🔄 Konum alınıyor...</p>
                        )}
                      </div>
                    </div>
                    <Button 
                      onClick={getCurrentLocation}
                      className="bg-blue-600 hover:bg-blue-700"
                      disabled={!navigator.geolocation}
                    >
                      📍 Şu Anki Konumum
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Map Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <span>🗺️</span>
                    <span>Sipariş Takip Haritası</span>
                  </CardTitle>
                  <p className="text-sm text-gray-600">
                    Aktif siparişlerinizi ve konumunuzu haritada görüntüleyin
                  </p>
                </CardHeader>
                <CardContent>
                  <LeafletMap
                    center={mapCenter}
                    zoom={userLocation ? 14 : 6}
                    height="500px"
                    markers={[
                      // User location marker
                      ...(userLocation ? [{
                        lat: userLocation.lat,
                        lng: userLocation.lng,
                        type: 'user',
                        popup: true,
                        title: '📍 Benim Konumum',
                        description: `${user.first_name || 'Müşteri'}`,
                        address: 'Şu anki konumunuz'
                      }] : []),
                      // Order markers
                      ...orders.filter(order => order.delivery_lat && order.delivery_lng).map(order => ({
                        lat: order.delivery_lat,
                        lng: order.delivery_lng,
                        type: 'delivery',
                        popup: true,
                        title: `Sipariş #${order.id.slice(-8)}`,
                        description: `Durum: ${order.status}`,
                        address: order.delivery_address
                      }))
                    ]}
                  />
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main Pages
const HomePage = ({ onAuthStart }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-blue-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6" key="logo-container">
            <div 
              key="logo-icon"
              className="w-16 h-16 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center shadow-lg mr-4"
            >
              <span className="text-white text-2xl font-bold">K</span>
            </div>
            <h1 
              key="logo-text"
              className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-orange-600 to-blue-600 bg-clip-text text-transparent"
            >
              Kuryecini
            </h1>
          </div>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Türkiye'nin en hızlı teslimat platformu. Herkes kurye olabilir, 
            her işletme satabilir, herkes sipariş verebilir.
          </p>
          <Button 
            onClick={onAuthStart}
            className="bg-orange-600 hover:bg-orange-700 text-white px-8 py-4 text-lg rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
            data-testid="get-started-btn"
          >
            Hemen Başla →
          </Button>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-8 mt-16">
          <Card key="courier-card" className="text-center hover:shadow-lg transition-shadow duration-300">
            <CardHeader>
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🚗</span>
              </div>
              <CardTitle className="text-orange-600">Kurye Ol</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Araç türü serbest! Araba, motor, bisiklet veya elektrikli araçla 
                para kazanmaya başla.
              </p>
            </CardContent>
          </Card>

          <Card key="business-card" className="text-center hover:shadow-lg transition-shadow duration-300">
            <CardHeader>
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🏪</span>
              </div>
              <CardTitle className="text-blue-600">İşletme Aç</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Restoranın, marketin veya nakliye şirketin var mı? 
                Hemen kayıt ol, satışa başla.
              </p>
            </CardContent>
          </Card>

          <Card key="customer-card" className="text-center hover:shadow-lg transition-shadow duration-300">
            <CardHeader>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📱</span>
              </div>
              <CardTitle className="text-green-600">Sipariş Ver</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Yemek, market alışverişi veya kargo gönderimi - 
                her ihtiyacın için hızlı teslimat.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Stats */}
        <div className="mt-16 bg-white rounded-2xl shadow-lg p-8">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <h3 className="text-3xl font-bold text-orange-600">%3</h3>
              <p className="text-gray-600">Düşük Komisyon</p>
            </div>
            <div>
              <h3 className="text-3xl font-bold text-blue-600">24/7</h3>
              <p className="text-gray-600">Hızlı Teslimat</p>
            </div>
            <div>
              <h3 className="text-3xl font-bold text-green-600">∞</h3>
              <p className="text-gray-600">Sınırsız Araç</p>
            </div>
            <div>
              <h3 className="text-3xl font-bold text-purple-600">🇹🇷</h3>
              <p className="text-gray-600">Türkiye Geneli</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const AuthPage = ({ onBack }) => {
  const { login } = useAuth();
  const [step, setStep] = useState('login'); // login, register, user_type_selection, registration_form
  const [userType, setUserType] = useState('');

  const handleRegistrationComplete = (loginData) => {
    login(loginData);
  };

  if (step === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-blue-50 flex items-center justify-center p-4">
        <LoginForm onRegisterClick={() => setStep('user_type_selection')} />
      </div>
    );
  }

  if (step === 'user_type_selection') {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-4xl mx-auto py-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Hangi rolde katılmak istiyorsunuz?
            </h1>
            <p className="text-gray-600">
              DeliverTR ailesine katılmak için rolünüzü seçin
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <Card 
              className="cursor-pointer hover:shadow-lg transition-all duration-300 border-2 hover:border-orange-500"
              onClick={() => {
                setUserType('courier');
                setStep('registration_form');
              }}
              data-testid="select-courier-type"
            >
              <CardHeader className="text-center">
                <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">🚗</span>
                </div>
                <CardTitle className="text-orange-600">Kurye</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-center text-gray-600">
                  Teslimat yaparak para kazan
                </p>
              </CardContent>
            </Card>

            <Card 
              className="cursor-pointer hover:shadow-lg transition-all duration-300 border-2 hover:border-blue-500"
              onClick={() => {
                setUserType('business');
                setStep('registration_form');
              }}
              data-testid="select-business-type"
            >
              <CardHeader className="text-center">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">🏪</span>
                </div>
                <CardTitle className="text-blue-600">İşletme</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-center text-gray-600">
                  Ürünlerini sat, sipariş al
                </p>
              </CardContent>
            </Card>

            <Card 
              className="cursor-pointer hover:shadow-lg transition-all duration-300 border-2 hover:border-green-500"
              onClick={() => {
                setUserType('customer');
                setStep('registration_form');
              }}
              data-testid="select-customer-type"
            >
              <CardHeader className="text-center">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">📱</span>
                </div>
                <CardTitle className="text-green-600">Müşteri</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-center text-gray-600">
                  Sipariş ver, hızlı teslimat al
                </p>
              </CardContent>
            </Card>
          </div>

          <div className="text-center mt-8">
            <Button 
              onClick={() => setStep('login')} 
              variant="outline"
              data-testid="back-to-login"
            >
              ← Giriş Sayfasına Dön
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'registration_form') {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-4xl mx-auto py-8">
          {userType === 'courier' && (
            <CourierRegistration 
              onComplete={handleRegistrationComplete}
              onBack={() => setStep('user_type_selection')}
            />
          )}
          {userType === 'business' && (
            <BusinessRegistration 
              onComplete={handleRegistrationComplete}
              onBack={() => setStep('user_type_selection')}
            />
          )}
          {userType === 'customer' && (
            <CustomerRegistration 
              onComplete={handleRegistrationComplete}
              onBack={() => setStep('user_type_selection')}
            />
          )}
        </div>
      </div>
    );
  }

  return null;
};

// Main App Component
function App() {
  const [showAuth, setShowAuth] = useState(false);
  
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <AuthRouter showAuth={showAuth} setShowAuth={setShowAuth} />
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

const AuthRouter = ({ showAuth, setShowAuth }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  // If user is authenticated, show appropriate dashboard
  if (user) {
    return (
      <Routes>
        <Route path="/" element={
          user.role === 'admin' ? <AdminDashboard user={user} /> :
          user.role === 'courier' ? <CourierDashboard user={user} /> :
          user.role === 'business' ? <BusinessDashboard user={user} /> :
          <CustomerDashboard user={user} />
        } />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    );
  }

  // Not authenticated
  if (showAuth) {
    return <AuthPage onBack={() => setShowAuth(false)} />;
  }

  return (
    <Routes>
      <Route path="/" element={<HomePage onAuthStart={() => setShowAuth(true)} />} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

export default App;