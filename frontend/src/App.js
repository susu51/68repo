import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import "./App.css";

// Components
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('delivertr_token');
    const userData = localStorage.getItem('delivertr_user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const login = (token, userData) => {
    localStorage.setItem('delivertr_token', token);
    localStorage.setItem('delivertr_user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('delivertr_token');
    localStorage.removeItem('delivertr_user');
    setUser(null);
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

// Phone Verification Component
const PhoneVerification = ({ onVerified, onBack }) => {
  const [phone, setPhone] = useState('+90');
  const [code, setCode] = useState('');
  const [verificationId, setVerificationId] = useState('');
  const [step, setStep] = useState(1); // 1: phone, 2: code
  const [loading, setLoading] = useState(false);

  const sendCode = async () => {
    if (phone.length < 13) {
      toast.error('Geçerli telefon numarası giriniz');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/send-code`, { phone });
      setVerificationId(response.data.verification_id);
      setStep(2);
      toast.success('Doğrulama kodu gönderildi');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Hata oluştu');
    }
    setLoading(false);
  };

  const verifyCode = async () => {
    if (code.length !== 6) {
      toast.error('6 haneli doğrulama kodunu giriniz');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/verify-code`, {
        phone,
        code,
        verification_id: verificationId
      });

      if (response.data.is_new_user) {
        onVerified({ phone, isNewUser: true });
      } else {
        onVerified({ 
          phone, 
          isNewUser: false, 
          loginData: response.data 
        });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Doğrulama başarısız');
    }
    setLoading(false);
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-orange-600">
          {step === 1 ? 'Telefon Doğrulama' : 'Doğrulama Kodu'}
        </CardTitle>
        <CardDescription>
          {step === 1 
            ? 'Telefon numaranızı girin'
            : `${phone} numarasına gönderilen 6 haneli kodu girin`
          }
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {step === 1 ? (
          <>
            <Input
              type="tel"
              placeholder="+90 5XX XXX XX XX"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              maxLength={14}
              data-testid="phone-input"
            />
            <Button 
              onClick={sendCode} 
              disabled={loading} 
              className="w-full bg-orange-600 hover:bg-orange-700"
              data-testid="send-code-btn"
            >
              {loading ? 'Gönderiliyor...' : 'Doğrulama Kodu Gönder'}
            </Button>
          </>
        ) : (
          <>
            <Input
              type="text"
              placeholder="6 haneli kod"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').substring(0, 6))}
              maxLength={6}
              className="text-center text-2xl tracking-wider"
              data-testid="verification-code-input"
            />
            <Button 
              onClick={verifyCode} 
              disabled={loading} 
              className="w-full bg-orange-600 hover:bg-orange-700"
              data-testid="verify-code-btn"
            >
              {loading ? 'Doğrulanıyor...' : 'Doğrula'}
            </Button>
            <Button 
              onClick={() => setStep(1)} 
              variant="ghost" 
              className="w-full"
              data-testid="back-to-phone-btn"
            >
              ← Telefon numarasını değiştir
            </Button>
          </>
        )}
        
        {onBack && (
          <Button onClick={onBack} variant="outline" className="w-full" data-testid="back-btn">
            ← Ana Sayfa
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

// Registration Components
const CourierRegistration = ({ phone, onComplete }) => {
  const [formData, setFormData] = useState({
    phone,
    first_name: '',
    last_name: '',
    iban: '',
    vehicle_type: '',
    license_class: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/register/courier`, formData);
      onComplete(response.data);
      toast.success('Kurye kaydınız tamamlandı! Onay bekliyor.');
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
            <Input
              placeholder="Adınız"
              value={formData.first_name}
              onChange={(e) => setFormData({...formData, first_name: e.target.value})}
              required
              data-testid="courier-first-name"
            />
            <Input
              placeholder="Soyadınız"
              value={formData.last_name}
              onChange={(e) => setFormData({...formData, last_name: e.target.value})}
              required
              data-testid="courier-last-name"
            />
          </div>
          
          <Input
            placeholder="IBAN (TR ile başlayan)"
            value={formData.iban}
            onChange={(e) => setFormData({...formData, iban: e.target.value})}
            required
            data-testid="courier-iban"
          />
          
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
          
          <Input
            placeholder="Ehliyet sınıfı (A, A1, A2, B, vb.)"
            value={formData.license_class}
            onChange={(e) => setFormData({...formData, license_class: e.target.value})}
            required
            data-testid="courier-license-class"
          />
          
          <Button 
            type="submit" 
            disabled={loading}
            className="w-full bg-orange-600 hover:bg-orange-700"
            data-testid="courier-register-btn"
          >
            {loading ? 'Kaydediliyor...' : 'Kurye Kaydını Tamamla'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

const BusinessRegistration = ({ phone, onComplete }) => {
  const [formData, setFormData] = useState({
    phone,
    business_name: '',
    tax_number: '',
    address: '',
    business_type: ''
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
          <Input
            placeholder="İşletme adı"
            value={formData.business_name}
            onChange={(e) => setFormData({...formData, business_name: e.target.value})}
            required
            data-testid="business-name"
          />
          
          <Input
            placeholder="Vergi numarası"
            value={formData.tax_number}
            onChange={(e) => setFormData({...formData, tax_number: e.target.value})}
            required
            data-testid="business-tax-number"
          />
          
          <Textarea
            placeholder="İşletme adresi"
            value={formData.address}
            onChange={(e) => setFormData({...formData, address: e.target.value})}
            required
            data-testid="business-address"
          />
          
          <Select onValueChange={(value) => setFormData({...formData, business_type: value})} required>
            <SelectTrigger data-testid="business-type-select">
              <SelectValue placeholder="İşletme türü" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="restaurant">Restoran</SelectItem>
              <SelectItem value="market">Market</SelectItem>
              <SelectItem value="store">Mağaza</SelectItem>
            </SelectContent>
          </Select>
          
          <Button 
            type="submit" 
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700"
            data-testid="business-register-btn"
          >
            {loading ? 'Kaydediliyor...' : 'İşletme Kaydını Tamamla'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

const CustomerRegistration = ({ phone, onComplete }) => {
  const [formData, setFormData] = useState({
    phone,
    first_name: '',
    last_name: '',
    email: ''
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
            <Input
              placeholder="Adınız"
              value={formData.first_name}
              onChange={(e) => setFormData({...formData, first_name: e.target.value})}
              required
              data-testid="customer-first-name"
            />
            <Input
              placeholder="Soyadınız"
              value={formData.last_name}
              onChange={(e) => setFormData({...formData, last_name: e.target.value})}
              required
              data-testid="customer-last-name"
            />
          </div>
          
          <Input
            type="email"
            placeholder="E-posta (opsiyonel)"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            data-testid="customer-email"
          />
          
          <Button 
            type="submit" 
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700"
            data-testid="customer-register-btn"
          >
            {loading ? 'Kaydediliyor...' : 'Müşteri Kaydını Tamamla'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

// Dashboard Components
const CourierDashboard = ({ user }) => {
  const { logout } = useAuth();

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
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Kurye Paneli</h1>
          <Button onClick={logout} variant="outline" data-testid="logout-btn">
            Çıkış Yap
          </Button>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>KYC Durumu</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {getKYCStatusBadge(user.kyc_status)}
                <p className="text-sm text-gray-600">
                  {user.kyc_status === 'pending' && 'Belgeleriniz inceleniyor...'}
                  {user.kyc_status === 'approved' && 'Çalışmaya başlayabilirsiniz!'}
                  {user.kyc_status === 'rejected' && 'Belgelerinizi yeniden gönderiniz.'}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Çalışma Durumu</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant={user.kyc_status === 'approved' ? "default" : "secondary"}>
                {user.kyc_status === 'approved' ? 'Çevrimdışı' : 'Beklemede'}
              </Badge>
              <p className="text-sm text-gray-600 mt-2">
                {user.kyc_status === 'approved' 
                  ? 'Çevrimiçi olarak sipariş alabilirsiniz'
                  : 'Onay sonrası aktif olacak'
                }
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Günlük Kazanç</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">₺0.00</p>
              <p className="text-sm text-gray-600">Bugün</p>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Yakındaki Siparişler</CardTitle>
            <CardDescription>Size yakın teslimat işleri</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500">
              {user.kyc_status === 'approved' 
                ? 'Şu anda yakınınızda sipariş bulunmuyor'
                : 'Onay sonrası siparişler görünecek'
              }
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

const BusinessDashboard = ({ user }) => {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 p-4" data-testid="business-dashboard">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">İşletme Paneli</h1>
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
              <p className="text-2xl font-bold text-blue-600">0</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Günlük Ciro</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">₺0.00</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Aktif Ürünler</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-purple-600">0</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">İşletme Durumu</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge variant="secondary">Kapalı</Badge>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="orders" className="space-y-4">
          <TabsList>
            <TabsTrigger value="orders">Siparişler</TabsTrigger>
            <TabsTrigger value="menu">Menü</TabsTrigger>
            <TabsTrigger value="settings">Ayarlar</TabsTrigger>
          </TabsList>
          
          <TabsContent value="orders">
            <Card>
              <CardHeader>
                <CardTitle>Gelen Siparişler</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  Henüz sipariş bulunmuyor
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="menu">
            <Card>
              <CardHeader>
                <CardTitle>Ürün/Menü Yönetimi</CardTitle>
                <CardDescription>Ürünlerinizi ekleyin ve yönetin</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Button className="bg-blue-600 hover:bg-blue-700" data-testid="add-product-btn">
                    + İlk Ürününüzü Ekleyin
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="settings">
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
                  <label className="block text-sm font-medium mb-2">Çalışma Saatleri</label>
                  <div className="grid grid-cols-2 gap-4">
                    <Input placeholder="Açılış (09:00)" />
                    <Input placeholder="Kapanış (22:00)" />
                  </div>
                </div>
                <Button className="bg-blue-600 hover:bg-blue-700" data-testid="save-settings-btn">
                  Ayarları Kaydet
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

const CustomerDashboard = ({ user }) => {
  const { logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 p-4" data-testid="customer-dashboard">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Hoş Geldin, {user.name}</h1>
          <Button onClick={logout} variant="outline" data-testid="logout-btn">
            Çıkış Yap
          </Button>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Yakın Restoranlar</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4">
                <p className="text-gray-500">Yakınınızdaki restoranları keşfedin</p>
                <Button className="mt-2 bg-green-600 hover:bg-green-700" data-testid="browse-restaurants-btn">
                  Restoranlara Göz At
                </Button>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Market Alışverişi</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4">
                <p className="text-gray-500">Günlük ihtiyaçlarınızı sipariş edin</p>
                <Button className="mt-2 bg-blue-600 hover:bg-blue-700" data-testid="browse-markets-btn">
                  Marketlere Göz At
                </Button>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Kargo Gönder</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-4">
                <p className="text-gray-500">Paket göndermeniz için kurye</p>
                <Button className="mt-2 bg-orange-600 hover:bg-orange-700" data-testid="send-package-btn">
                  Kargo İsteği Oluştur
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Son Siparişleriniz</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-gray-500">
              Henüz sipariş vermemişsiniz
            </div>
          </CardContent>
        </Card>
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
                Restoranın, marketin veya mağazan var mı? 
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
  const [step, setStep] = useState('phone'); // phone, register
  const [userType, setUserType] = useState('');
  const [phoneData, setPhoneData] = useState(null);

  const handleVerified = (data) => {
    setPhoneData(data);
    
    if (!data.isNewUser) {
      // Existing user - login
      login(data.loginData.access_token, {
        phone: data.phone,
        user_type: data.loginData.user_type,
        ...data.loginData.user_data
      });
    } else {
      // New user - show registration options
      setStep('register');
    }
  };

  const handleRegistrationComplete = (loginData) => {
    login(loginData.access_token, {
      phone: phoneData.phone,
      user_type: loginData.user_type,
      ...loginData.user_data
    });
  };

  if (step === 'phone') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-blue-50 flex items-center justify-center p-4">
        <PhoneVerification onVerified={handleVerified} onBack={onBack} />
      </div>
    );
  }

  if (step === 'register') {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-4xl mx-auto py-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Hangi rolde katılmak istiyorsun?
            </h1>
            <p className="text-gray-600">
              Telefon: <strong>{phoneData?.phone}</strong>
            </p>
          </div>

          {!userType ? (
            <div className="grid md:grid-cols-3 gap-6">
              <Card 
                className="cursor-pointer hover:shadow-lg transition-all duration-300 border-2 hover:border-orange-500"
                onClick={() => setUserType('courier')}
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
                onClick={() => setUserType('business')}
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
                onClick={() => setUserType('customer')}
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
          ) : (
            <div>
              <Button 
                onClick={() => setUserType('')} 
                variant="ghost" 
                className="mb-4"
                data-testid="back-to-role-selection"
              >
                ← Rol seçimine geri dön
              </Button>
              
              {userType === 'courier' && (
                <CourierRegistration 
                  phone={phoneData.phone} 
                  onComplete={handleRegistrationComplete}
                />
              )}
              {userType === 'business' && (
                <BusinessRegistration 
                  phone={phoneData.phone} 
                  onComplete={handleRegistrationComplete}
                />
              )}
              {userType === 'customer' && (
                <CustomerRegistration 
                  phone={phoneData.phone} 
                  onComplete={handleRegistrationComplete}
                />
              )}
            </div>
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