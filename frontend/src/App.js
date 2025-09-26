import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import "./App.css";
import AdminPanel from "./AdminPanel";
import MapComponent from "./MapComponent";
import { CreateOrderForm, OrdersList, NearbyOrdersForCourier, OrderStatusBadge } from "./OrderSystem";
import { MenuManagement, MenuDisplay } from "./MenuManagement";
import { CreatePackageOrder, PackageOrderHistory } from "./PackageOrder";
import CourierBalance from "./CourierBalance";
import PhoneAuth from "./PhoneAuth";

// Components
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { Label } from "./components/ui/label";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('delivertr_access_token');
    const refreshToken = localStorage.getItem('delivertr_refresh_token');
    const userData = localStorage.getItem('delivertr_user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    } else if (refreshToken) {
      // Try to refresh token
      refreshAccessToken(refreshToken);
    }
    setLoading(false);
  }, []);

  const refreshAccessToken = async (refreshToken) => {
    try {
      const response = await axios.post(`${API}/auth/refresh`, {
        refresh_token: refreshToken
      });
      
      localStorage.setItem('delivertr_access_token', response.data.access_token);
      // User data remains the same, just refresh the token
      
    } catch (error) {
      // Refresh failed, clear everything
      logout();
    }
  };

  const login = (authData) => {
    localStorage.setItem('delivertr_access_token', authData.access_token);
    localStorage.setItem('delivertr_refresh_token', authData.refresh_token);
    localStorage.setItem('delivertr_user', JSON.stringify(authData.user_data));
    setUser(authData.user_data);
    
    // Set axios default authorization header
    axios.defaults.headers.common['Authorization'] = `Bearer ${authData.access_token}`;
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('delivertr_refresh_token');
      if (refreshToken) {
        await axios.post(`${API}/auth/logout`, {
          refresh_token: refreshToken
        });
      }
    } catch (error) {
      console.log('Logout error:', error);
    } finally {
      localStorage.removeItem('delivertr_access_token');
      localStorage.removeItem('delivertr_refresh_token');  
      localStorage.removeItem('delivertr_user');
      setUser(null);
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  // Set authorization header on app start
  useEffect(() => {
    const token = localStorage.getItem('delivertr_access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

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

// Login Component
const LoginForm = ({ onRegisterClick }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, formData);
      login(response.data.access_token, {
        email: formData.email,
        user_type: response.data.user_type,
        ...response.data.user_data
      });
      toast.success('Başarıyla giriş yaptınız!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Giriş başarısız');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-orange-600">Giriş Yap</CardTitle>
        <CardDescription>DeliverTR hesabınıza giriş yapın</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
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

// File Upload Component
const FileUpload = ({ label, onFileSelect, accept = "image/*", testId }) => {
  const [uploading, setUploading] = useState(false);
  const [fileUrl, setFileUrl] = useState('');

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setFileUrl(response.data.file_url);
      onFileSelect(response.data.file_url);
      toast.success('Dosya başarıyla yüklendi');
    } catch (error) {
      toast.error('Dosya yükleme başarısız');
    }
    setUploading(false);
  };

  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
        <input
          type="file"
          accept={accept}
          onChange={handleFileChange}
          className="hidden"
          id={testId}
        />
        <label htmlFor={testId} className="cursor-pointer">
          {uploading ? (
            <div className="text-blue-600">Yükleniyor...</div>
          ) : fileUrl ? (
            <div className="space-y-2">
              <img src={`${BACKEND_URL}${fileUrl}`} alt="Preview" className="mx-auto max-h-20" />
              <p className="text-green-600 text-sm">✓ Dosya yüklendi</p>
            </div>
          ) : (
            <div className="text-gray-500">
              📁 {label} için dosya seçin
            </div>
          )}
        </label>
      </div>
    </div>
  );
};

// Registration Components
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
    city: ''
  });
  const [licensePhotoUrl, setLicensePhotoUrl] = useState('');
  const [vehiclePhotoUrl, setVehiclePhotoUrl] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/register/courier`, formData);
      
      // Update photos if uploaded
      if (licensePhotoUrl || vehiclePhotoUrl) {
        const token = response.data.access_token;
        await axios.put(`${API}/courier/update-photos`, {
          license_photo_url: licensePhotoUrl,
          vehicle_photo_url: vehiclePhotoUrl
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }

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
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>E-posta</Label>
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
              <Label>Şifre</Label>
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
              onFileSelect={setLicensePhotoUrl}
              testId="license-upload"
            />
            <FileUpload
              label="Araç Fotoğrafı"
              onFileSelect={setVehiclePhotoUrl}
              testId="vehicle-upload"
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
              <Label>E-posta</Label>
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
              <Label>Şifre</Label>
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
              <CitySelector 
                value={formData.city}
                onChange={(value) => setFormData({...formData, city: value})}
                required
              />
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
              <Label>E-posta</Label>
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
              <Label>Şifre</Label>
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
  const [currentView, setCurrentView] = useState('nearby'); // nearby, orders, balance, profile
  const [myOrders, setMyOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentView === 'orders') {
      fetchMyOrders();
    }
  }, [currentView]);

  const fetchMyOrders = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('delivertr_token');
      const response = await axios.get(`${API}/orders/my-orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyOrders(response.data.orders);
    } catch (error) {
      console.error('Siparişler alınamadı:', error);
    }
    setLoading(false);
  };

  const toggleOnlineStatus = async () => {
    try {
      const token = localStorage.getItem('delivertr_token');
      const response = await axios.post(`${API}/courier/toggle-online`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsOnline(response.data.is_online);
      toast.success(response.data.is_online ? 'Çevrimiçi oldunuz!' : 'Çevrimdışı oldunuz');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Durum değiştirilemedi');
    }
  };

  const updateLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(async (position) => {
        try {
          const token = localStorage.getItem('delivertr_token');
          await axios.post(`${API}/courier/location/update`, {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            address: `${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}`
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          toast.success('Konum güncellendi');
        } catch (error) {
          toast.error('Konum güncellenemedi');
        }
      });
    }
  };

  const getKYCStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: "secondary", text: "Onay Bekliyor", className: "bg-yellow-100 text-yellow-800" },
      approved: { variant: "default", text: "Onaylandı", className: "bg-green-100 text-green-800" },
      rejected: { variant: "destructive", text: "Reddedildi", className: "bg-red-100 text-red-800" }
    };
    
    const config = statusConfig[status] || statusConfig.pending;
    return <Badge className={config.className} data-testid="kyc-status-badge">{config.text}</Badge>;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4" data-testid="courier-dashboard">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Kurye Paneli</h1>
            <p className="text-gray-600">{user.name} - {user.city}</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={updateLocation} variant="outline" size="sm">
              📍 Konum Güncelle
            </Button>
            <Button onClick={logout} variant="outline" data-testid="logout-btn">
              Çıkış Yap
            </Button>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid md:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">KYC Durumu</CardTitle>
            </CardHeader>
            <CardContent>
              {getKYCStatusBadge(user.kyc_status)}
              <p className="text-xs text-gray-600 mt-2">
                {user.kyc_status === 'pending' && 'Belgeleriniz inceleniyor'}
                {user.kyc_status === 'approved' && 'Çalışabilirsiniz!'}
                {user.kyc_status === 'rejected' && 'Belgeleri güncelleyin'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Çevrimiçi Durum</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Badge className={isOnline ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                  {isOnline ? '🟢 Çevrimiçi' : '⚫ Çevrimdışı'}
                </Badge>
                <Button
                  onClick={toggleOnlineStatus}
                  disabled={user.kyc_status !== 'approved'}
                  size="sm"
                  variant="outline"
                  data-testid="toggle-online-btn"
                >
                  Değiştir
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Mevcut Bakiye</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">₺{user.balance?.toFixed(2) || '0.00'}</p>
              <p className="text-xs text-gray-600">Çekilebilir</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Tamamlanan</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-blue-600">0</p>
              <p className="text-xs text-gray-600">Sipariş</p>
            </CardContent>
          </Card>
        </div>

        {/* Navigation */}
        <div className="mb-6">
          <div className="flex gap-2">
            <Button
              onClick={() => setCurrentView('nearby')}
              variant={currentView === 'nearby' ? 'default' : 'outline'}
              data-testid="nearby-orders-tab"
            >
              🔍 Yakındaki Siparişler
            </Button>
            <Button
              onClick={() => setCurrentView('orders')}
              variant={currentView === 'orders' ? 'default' : 'outline'}
              data-testid="my-orders-tab"
            >
              📋 Siparişlerim
            </Button>
            <Button
              onClick={() => setCurrentView('balance')}
              variant={currentView === 'balance' ? 'default' : 'outline'}
              data-testid="balance-tab"
            >
              💰 Bakiye & Kazançlar
            </Button>
            <Button
              onClick={() => setCurrentView('map')}
              variant={currentView === 'map' ? 'default' : 'outline'}
            >
              🗺️ Harita
            </Button>
          </div>
        </div>

        {/* Content */}
        {currentView === 'nearby' && user.kyc_status === 'approved' && isOnline && (
          <NearbyOrdersForCourier />
        )}

        {currentView === 'nearby' && (user.kyc_status !== 'approved' || !isOnline) && (
          <Card>
            <CardContent className="text-center py-12">
              <div className="text-4xl mb-4">⚠️</div>
              <p className="text-gray-600 mb-2">
                {user.kyc_status !== 'approved' 
                  ? 'KYC onayınız tamamlanmalı' 
                  : 'Sipariş almak için çevrimiçi olun'
                }
              </p>
            </CardContent>
          </Card>
        )}

        {currentView === 'orders' && (
          <div>
            {loading ? (
              <Card>
                <CardContent className="text-center py-12">
                  <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-600">Siparişler yükleniyor...</p>
                </CardContent>
              </Card>
            ) : (
              <OrdersList
                userType="courier"
                orders={myOrders}
                onStatusUpdate={fetchMyOrders}
              />
            )}
          </div>
        )}

        {currentView === 'balance' && (
          <CourierBalance />
        )}

        {currentView === 'map' && (
          <Card>
            <CardHeader>
              <CardTitle>Konum & Harita</CardTitle>
            </CardHeader>
            <CardContent>
              <MapComponent
                showCurrentLocation={true}
                height="500px"
                onLocationSelect={(location) => {
                  console.log('Seçilen konum:', location);
                }}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

const BusinessDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [currentView, setCurrentView] = useState('orders'); // orders, menu, settings
  const [myOrders, setMyOrders] = useState([]);
  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (currentView === 'orders') {
      fetchMyOrders();
    }
  }, [currentView]);

  const fetchMyOrders = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('delivertr_token');
      const response = await axios.get(`${API}/orders/my-orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyOrders(response.data.orders);
    } catch (error) {
      console.error('Siparişler alınamadı:', error);
    }
    setLoading(false);
  };

  const getCategoryName = (category) => {
    return category === 'gida' ? 'Gıda' : 'Nakliye';
  };

  const handleOrderCreated = (orderId) => {
    toast.success('Sipariş oluşturuldu!');
    setShowCreateOrder(false);
    setCurrentView('orders');
    fetchMyOrders();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4" data-testid="business-dashboard">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{user.business_name}</h1>
            <p className="text-gray-600">{getCategoryName(user.category)} • {user.city}</p>
          </div>
          <Button onClick={logout} variant="outline" data-testid="logout-btn">
            Çıkış Yap
          </Button>
        </div>

        <div className="grid md:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Bugünkü Siparişler</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-blue-600">{myOrders.length}</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Günlük Ciro</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">
                ₺{myOrders.reduce((sum, order) => sum + (order.total || 0), 0).toFixed(2)}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Aktif Siparişler</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-purple-600">
                {myOrders.filter(order => !['delivered', 'cancelled'].includes(order.status)).length}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">İşletme Durumu</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="default" className="bg-green-100 text-green-800">Açık</Badge>
            </CardContent>
          </Card>
        </div>

        {/* Navigation */}
        <div className="mb-6">
          <div className="flex gap-2">
            <Button
              onClick={() => setCurrentView('orders')}
              variant={currentView === 'orders' ? 'default' : 'outline'}
              data-testid="orders-tab"
            >
              📋 Siparişler
            </Button>
            <Button
              onClick={() => setCurrentView('menu')}
              variant={currentView === 'menu' ? 'default' : 'outline'}
              data-testid="menu-tab"
            >
              {user.category === 'gida' ? '🍽️ Menü' : '📦 Hizmetler'}
            </Button>
            <Button
              onClick={() => setShowCreateOrder(true)}
              className="bg-green-600 hover:bg-green-700"
              data-testid="create-order-btn"
            >
              + Test Sipariş Oluştur
            </Button>
            <Button
              onClick={() => setCurrentView('settings')}
              variant={currentView === 'settings' ? 'default' : 'outline'}
            >
              ⚙️ Ayarlar
            </Button>
          </div>
        </div>

        {/* Content */}
        {currentView === 'orders' && (
          <div>
            {loading ? (
              <Card>
                <CardContent className="text-center py-12">
                  <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-600">Siparişler yükleniyor...</p>
                </CardContent>
              </Card>
            ) : (
              <OrdersList
                userType="business"
                orders={myOrders}
                onStatusUpdate={fetchMyOrders}
              />
            )}
          </div>
        )}

        {currentView === 'menu' && user.category === 'gida' && (
          <MenuManagement />
        )}

        {currentView === 'menu' && user.category === 'nakliye' && (
          <Card>
            <CardHeader>
              <CardTitle>Nakliye Hizmetleri</CardTitle>
              <CardDescription>Nakliye işletmeleri için özel hizmet yönetimi</CardDescription>
            </CardHeader>
            <CardContent className="text-center py-12">
              <div className="text-4xl mb-4">🚚</div>
              <p className="text-gray-500 mb-4">Nakliye hizmet yönetimi yakında!</p>
              <p className="text-sm text-gray-400">
                Müşteriler size paket siparişi verebilir
              </p>
            </CardContent>
          </Card>
        )}

        {currentView === 'settings' && (
          <Card>
            <CardHeader>
              <CardTitle>İşletme Ayarları</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">İşletme Adı</label>
                <Input value={user.business_name} readOnly />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Kategori</label>
                <Input value={getCategoryName(user.category)} readOnly />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Şehir</label>
                <Input value={user.city} readOnly />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Çalışma Saatleri</label>
                <div className="grid grid-cols-2 gap-4">
                  <Input placeholder="Açılış (09:00)" />
                  <Input placeholder="Kapanış (22:00)" />
                </div>
              </div>
              
              {/* Admin Panel Link */}
              <div className="mt-6 pt-6 border-t">
                <div className="text-center">
                  <a 
                    href="/admin" 
                    className="text-sm text-gray-500 hover:text-blue-600 transition-colors"
                    data-testid="admin-panel-link"
                  >
                    🛠️ Admin Panel (Demo)
                  </a>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Create Order Modal */}
        {showCreateOrder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <CreateOrderForm
                businessId={user.business_id || "demo-business-id"}
                onOrderCreated={handleOrderCreated}
                onCancel={() => setShowCreateOrder(false)}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const CustomerDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [myOrders, setMyOrders] = useState([]);
  const [nearbyBusinesses, setNearbyBusinesses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateOrder, setShowCreateOrder] = useState(false);
  const [showCreatePackage, setShowCreatePackage] = useState(false);
  const [selectedBusiness, setSelectedBusiness] = useState(null);

  useEffect(() => {
    fetchMyOrders();
    // In a real app, we'd fetch nearby businesses based on customer location
    setNearbyBusinesses([
      {
        id: 'demo-restaurant-1',
        name: 'Burger Palace',
        category: 'gida',
        distance: 1.2,
        rating: 4.5,
        delivery_time: 25
      },
      {
        id: 'demo-restaurant-2', 
        name: 'Pizza Corner',
        category: 'gida',
        distance: 0.8,
        rating: 4.8,
        delivery_time: 20
      },
      {
        id: 'demo-cargo-1',
        name: 'Hızlı Kargo',
        category: 'nakliye',
        distance: 2.1,
        rating: 4.3,
        delivery_time: 15
      }
    ]);
  }, []);

  const fetchMyOrders = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('delivertr_token');
      const response = await axios.get(`${API}/orders/my-orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyOrders(response.data.orders);
    } catch (error) {
      console.error('Siparişler alınamadı:', error);
    }
    setLoading(false);
  };

  const handleOrderCreated = (orderId) => {
    toast.success('Sipariş oluşturuldu!');
    setShowCreateOrder(false);
    setShowCreatePackage(false);
    setSelectedBusiness(null);
    fetchMyOrders();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4" data-testid="customer-dashboard">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Hoş Geldin, {user.name}</h1>
            <p className="text-gray-600">{user.city}</p>
          </div>
          <Button onClick={logout} variant="outline" data-testid="logout-btn">
            Çıkış Yap
          </Button>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Actions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Actions */}
            <div className="grid md:grid-cols-3 gap-4">
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="text-center p-6">
                  <div className="text-4xl mb-2">🍔</div>
                  <h3 className="font-semibold mb-2">Yemek Sipariş</h3>
                  <p className="text-sm text-gray-600 mb-3">Restoranlardan sipariş</p>
                  <Button className="bg-red-600 hover:bg-red-700 w-full" data-testid="browse-restaurants-btn">
                    Restoranlara Göz At
                  </Button>
                </CardContent>
              </Card>

              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="text-center p-6">
                  <div className="text-4xl mb-2">🛒</div>
                  <h3 className="font-semibold mb-2">Market</h3>
                  <p className="text-sm text-gray-600 mb-3">Günlük alışveriş</p>
                  <Button className="bg-blue-600 hover:bg-blue-700 w-full" data-testid="browse-markets-btn">
                    Market Alışverişi
                  </Button>
                </CardContent>
              </Card>

              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="text-center p-6">
                  <div className="text-4xl mb-2">📦</div>
                  <h3 className="font-semibold mb-2">Paket Gönder</h3>
                  <p className="text-sm text-gray-600 mb-3">Kargo teslimatı</p>
                  <Button 
                    onClick={() => setShowCreatePackage(true)}
                    className="bg-orange-600 hover:bg-orange-700 w-full" 
                    data-testid="send-package-btn"
                  >
                    Paket Gönder
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Nearby Businesses */}
            <div>
              <h2 className="text-xl font-bold mb-4">Yakındaki İşletmeler</h2>
              
              <div className="grid md:grid-cols-2 gap-4">
                {nearbyBusinesses.map((business) => (
                  <Card key={business.id} className="hover:shadow-md transition-shadow cursor-pointer">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <h3 className="font-semibold">{business.name}</h3>
                          <p className="text-sm text-gray-600">
                            {business.category === 'gida' ? '🍔 Gıda' : '📦 Nakliye'}
                          </p>
                        </div>
                        <Badge variant="outline">
                          ⭐ {business.rating}
                        </Badge>
                      </div>
                      
                      <div className="flex justify-between items-center text-sm text-gray-600 mb-3">
                        <span>📍 {business.distance} km</span>
                        <span>🕒 {business.delivery_time} dk</span>
                      </div>
                      
                      <Button
                        onClick={() => {
                          if (business.category === 'gida') {
                            setSelectedBusiness(business);
                            setShowCreateOrder(true);
                          } else {
                            setShowCreatePackage(true);
                          }
                        }}
                        className="w-full bg-green-600 hover:bg-green-700"
                        data-testid={`order-from-${business.id}`}
                      >
                        {business.category === 'gida' ? 'Sipariş Ver' : 'Kargo Gönder'}
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>

          {/* My Orders Sidebar */}
          <div>
            <h2 className="text-xl font-bold mb-4">Siparişlerim</h2>
            
            {loading ? (
              <Card>
                <CardContent className="text-center py-8">
                  <div className="w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Yükleniyor...</p>
                </CardContent>
              </Card>
            ) : myOrders.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <div className="text-4xl mb-2">📋</div>
                  <p className="text-gray-500 text-sm">Henüz siparişiniz yok</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {myOrders.slice(0, 5).map((order) => (
                  <Card key={order.id} className="hover:shadow-sm transition-shadow">
                    <CardContent className="p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-medium text-sm">
                            {order.order_type === 'food' ? '🍔' : '📦'} #{order.id.substring(0, 8)}
                          </p>
                          <p className="text-xs text-gray-600">
                            {order.business_name || 'Paket Teslimat'}
                          </p>
                        </div>
                        <OrderStatusBadge status={order.status} />
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-gray-600">
                          {new Date(order.created_at).toLocaleDateString('tr-TR')}
                        </span>
                        <span className="font-semibold">₺{order.total?.toFixed(2)}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {myOrders.length > 5 && (
                  <Button variant="outline" className="w-full" size="sm">
                    Tümünü Gör ({myOrders.length})
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Create Order Modal */}
        {showCreateOrder && selectedBusiness && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <CreateOrderForm
                businessId={selectedBusiness.id}
                onOrderCreated={handleOrderCreated}
                onCancel={() => {
                  setShowCreateOrder(false);
                  setSelectedBusiness(null);
                }}
              />
            </div>
          </div>
        )}

        {/* Create Package Order Modal */}
        {showCreatePackage && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <CreatePackageOrder
                onOrderCreated={handleOrderCreated}
                onCancel={() => setShowCreatePackage(false)}
              />
            </div>
          </div>
        )}
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
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-orange-600 to-blue-600 bg-clip-text text-transparent">
            DeliverTR
          </h1>
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
          <Card className="text-center hover:shadow-lg transition-shadow duration-300">
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

          <Card className="text-center hover:shadow-lg transition-shadow duration-300">
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

          <Card className="text-center hover:shadow-lg transition-shadow duration-300">
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
    login(loginData.access_token, {
      email: loginData.user_data.email,
      user_type: loginData.user_type,
      ...loginData.user_data
    });
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
              Hangi rolde katılmak istiyorsun?
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

  if (user) {
    return (
      <Routes>
        <Route path="/" element={
          user.user_type === 'courier' ? <CourierDashboard user={user} /> :
          user.user_type === 'business' ? <BusinessDashboard user={user} /> :
          <CustomerDashboard user={user} />
        } />
        <Route path="/admin" element={<AdminPanel />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    );
  }

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