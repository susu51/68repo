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
import FileUpload from "./FileUpload";
import LeafletMap from "./LeafletMap";

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
    const userData = localStorage.getItem('delivertr_user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
      // Set axios default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    setLoading(false);
  }, []);

  const login = (authData) => {
    localStorage.setItem('delivertr_access_token', authData.access_token);
    localStorage.setItem('delivertr_user', JSON.stringify(authData.user_data));
    setUser(authData.user_data);
    
    // Set axios default authorization header
    axios.defaults.headers.common['Authorization'] = `Bearer ${authData.access_token}`;
  };

  const logout = () => {
    localStorage.removeItem('delivertr_access_token');
    localStorage.removeItem('delivertr_user');
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
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

    try {
      const response = await axios.post(`${API}/auth/admin`, {
        password: formData.adminPassword
      });
      login(response.data);
      toast.success('Admin girişi başarılı!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Yanlış admin şifresi');
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
                  placeholder="Admin şifresini girin"
                  value={formData.adminPassword}
                  onChange={(e) => setFormData({...formData, adminPassword: e.target.value})}
                  required
                  data-testid="admin-password"
                />
              </div>
              
              <Button 
                type="submit" 
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

// Registration Components - Email/Password based registration
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
              <Input
                placeholder="İstanbul"
                value={formData.city}
                onChange={(e) => setFormData({...formData, city: e.target.value})}
                required
                data-testid="courier-city"
              />
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
      const token = localStorage.getItem('delivertr_access_token');
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
      const token = localStorage.getItem('delivertr_access_token');
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
          const token = localStorage.getItem('delivertr_access_token');
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
      const response = await axios.get(`${API}/products/my`);
      setProducts(response.data);
    } catch (error) {
      toast.error('Ürünler yüklenemedi');
    }
    setLoading(false);
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/orders`);
      setOrders(response.data);
    } catch (error) {
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

      await axios.post(`${API}/products`, productData);
      
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
      toast.error(error.response?.data?.detail || 'Ürün eklenemedi');
    }
    setLoading(false);
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      await axios.patch(`${API}/orders/${orderId}/status?new_status=${newStatus}`);
      toast.success('Sipariş durumu güncellendi');
      fetchOrders();
    } catch (error) {
      toast.error('Durum güncellenemedi');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold">
                {user.business_name || 'İşletme'} - Yönetim Paneli
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline">İşletme</Badge>
              <Button onClick={logout} variant="outline">Çıkış</Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="products">Ürünler</TabsTrigger>
            <TabsTrigger value="orders">Siparişler</TabsTrigger>
            <TabsTrigger value="map">Harita</TabsTrigger>
          </TabsList>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-6">
            {/* Add Product Form */}
            <Card>
              <CardHeader>
                <CardTitle>Yeni Ürün Ekle</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProductSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Ürün Adı *</Label>
                      <Input
                        value={productForm.name}
                        onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                        placeholder="Margherita Pizza"
                        required
                      />
                    </div>
                    <div>
                      <Label>Fiyat (₺) *</Label>
                      <Input
                        type="number"
                        step="0.01"
                        value={productForm.price}
                        onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                        placeholder="25.50"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label>Açıklama *</Label>
                    <Textarea
                      value={productForm.description}
                      onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                      placeholder="Ürün açıklaması..."
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Kategori *</Label>
                      <Select onValueChange={(value) => setProductForm({...productForm, category: value})}>
                        <SelectTrigger>
                          <SelectValue placeholder="Kategori seçin" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="pizza">Pizza</SelectItem>
                          <SelectItem value="burger">Burger</SelectItem>
                          <SelectItem value="kebap">Kebap</SelectItem>
                          <SelectItem value="döner">Döner</SelectItem>
                          <SelectItem value="tatlı">Tatlı</SelectItem>
                          <SelectItem value="içecek">İçecek</SelectItem>
                          <SelectItem value="diğer">Diğer</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Hazırlık Süresi (dakika)</Label>
                      <Input
                        type="number"
                        value={productForm.preparation_time_minutes}
                        onChange={(e) => setProductForm({...productForm, preparation_time_minutes: e.target.value})}
                        placeholder="30"
                      />
                    </div>
                  </div>

                  {/* Product Photo Upload */}
                  <div>
                    <FileUpload
                      label="Ürün Fotoğrafı"
                      accept="image/*"
                      onFileUploaded={(url) => setProductForm({...productForm, photo_url: url})}
                    />
                  </div>

                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? 'Ekleniyor...' : 'Ürün Ekle'}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Products List */}
            <Card>
              <CardHeader>
                <CardTitle>Mevcut Ürünler ({products.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {products.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Henüz ürün eklenmemiş</p>
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
                          <div className="flex justify-between items-center">
                            <span className="font-bold text-green-600">₺{product.price}</span>
                            <Badge variant={product.is_available ? "default" : "secondary"}>
                              {product.is_available ? 'Mevcut' : 'Stokta Yok'}
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            Hazırlık: {product.preparation_time_minutes} dk
                          </p>
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
                <CardTitle>Gelen Siparişler ({orders.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {orders.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Henüz sipariş yok</p>
                ) : (
                  <div className="space-y-4">
                    {orders.map((order) => (
                      <Card key={order.id}>
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <h3 className="font-semibold">Sipariş #{order.id.slice(-8)}</h3>
                              <p className="text-sm text-gray-600">{order.customer_name}</p>
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

                          {order.status === 'created' && (
                            <Button 
                              onClick={() => updateOrderStatus(order.id, 'assigned')}
                              className="w-full"
                            >
                              Siparişi Onayla
                            </Button>
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

// Customer Dashboard - Enhanced with Product Shopping & Cart
const CustomerDashboard = ({ user }) => {
  const { logout } = useAuth();
  const [activeTab, setActiveTab] = useState('products');
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(false);
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
    
    toast.success(`${product.name} sepete eklendi!`);
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
      toast.error('Sepetiniz boş!');
      return;
    }
    
    if (!orderForm.delivery_address) {
      toast.error('Teslimat adresini girin!');
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
      
      toast.success('Sipariş başarıyla oluşturuldu!');
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold">
                Merhaba, {user.first_name || 'Müşteri'}!
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline">
                🛒 Sepet ({cart.length})
              </Badge>
              <Badge variant="outline">Müşteri</Badge>
              <Button onClick={logout} variant="outline">Çıkış</Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="products">Ürünler</TabsTrigger>
            <TabsTrigger value="cart">Sepet ({cart.length})</TabsTrigger>
            <TabsTrigger value="orders">Siparişlerim</TabsTrigger>
            <TabsTrigger value="map">Harita</TabsTrigger>
          </TabsList>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Mevcut Ürünler ({products.length})</CardTitle>
                <CardDescription>
                  Lezzetli yemekleri sepetinize ekleyin!
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-600">Ürünler yükleniyor...</p>
                  </div>
                ) : products.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Henüz ürün yok</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {products.map((product) => (
                      <Card key={product.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                        {product.photo_url && (
                          <div className="h-48 overflow-hidden">
                            <img 
                              src={`${BACKEND_URL}${product.photo_url}`} 
                              alt={product.name}
                              className="w-full h-full object-cover"
                            />
                          </div>
                        )}
                        <CardContent className="p-4">
                          <div className="mb-3">
                            <h3 className="font-semibold text-lg">{product.name}</h3>
                            <p className="text-sm text-gray-600 mb-2">{product.description}</p>
                            <p className="text-xs text-gray-500">
                              İşletme: {product.business_name} • Hazırlık: {product.preparation_time_minutes} dk
                            </p>
                          </div>
                          
                          <div className="flex justify-between items-center mb-3">
                            <span className="font-bold text-xl text-green-600">₺{product.price}</span>
                            <Badge variant={product.is_available ? "default" : "secondary"}>
                              {product.is_available ? 'Mevcut' : 'Stokta Yok'}
                            </Badge>
                          </div>
                          
                          <Button 
                            onClick={() => addToCart(product)}
                            disabled={!product.is_available}
                            className="w-full"
                          >
                            {product.is_available ? 'Sepete Ekle' : 'Stokta Yok'}
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cart Tab */}
          <TabsContent value="cart" className="space-y-6">
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
          </TabsContent>

          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-6">
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
          </TabsContent>

          {/* Map Tab */}
          <TabsContent value="map">
            <Card>
              <CardHeader>
                <CardTitle>Sipariş Takip Haritası</CardTitle>
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
                    description: `Durum: ${order.status}`,
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
        <Route path="/admin" element={<AdminPanel />} />
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