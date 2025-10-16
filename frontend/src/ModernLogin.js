import React, { useState, useEffect } from 'react';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { KuryeciniLogo, KuryeciniTextLogo } from "./components/KuryeciniLogo";
import PhoneAuth from "./PhoneAuth";
import ModernRegister from './components/ModernRegister';
import toast from 'react-hot-toast';
import { api } from './api/http';  // Use cookie-aware API client
import { useCookieAuth } from './contexts/CookieAuthContext';  // Use auth context

// Türkiye şehirleri
const TURKISH_CITIES = [
  'Adana', 'Adıyaman', 'Afyonkarahisar', 'Ağrı', 'Amasya', 'Ankara', 'Antalya', 'Artvin',
  'Aydın', 'Balıkesir', 'Bilecik', 'Bingöl', 'Bitlis', 'Bolu', 'Burdur', 'Bursa',
  'Çanakkale', 'Çankırı', 'Çorum', 'Denizli', 'Diyarbakır', 'Edirne', 'Elazığ', 'Erzincan',
  'Erzurum', 'Eskişehir', 'Gaziantep', 'Giresun', 'Gümüşhane', 'Hakkâri', 'Hatay', 'Isparta',
  'Mersin', 'İstanbul', 'İzmir', 'Kars', 'Kastamonu', 'Kayseri', 'Kırklareli', 'Kırşehir',
  'Kocaeli', 'Konya', 'Kütahya', 'Malatya', 'Manisa', 'Kahramanmaraş', 'Mardin', 'Muğla',
  'Muş', 'Nevşehir', 'Niğde', 'Ordu', 'Rize', 'Sakarya', 'Samsun', 'Siirt',
  'Sinop', 'Sivas', 'Tekirdağ', 'Tokat', 'Trabzon', 'Tunceli', 'Şanlıurfa', 'Uşak',
  'Van', 'Yozgat', 'Zonguldak', 'Aksaray', 'Bayburt', 'Karaman', 'Kırıkkale', 'Batman',
  'Şırnak', 'Bartın', 'Ardahan', 'Iğdır', 'Yalova', 'Karabük', 'Kilis', 'Osmaniye', 'Düzce'
];

export const ModernLogin = ({ onLogin, onRegisterClick, onClose }) => {
  const { login: contextLogin, register: contextRegister, checkAuthStatus } = useCookieAuth();
  const [loginMethod, setLoginMethod] = useState('email');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRegisterWizard, setShowRegisterWizard] = useState(false);  // Show modern register wizard
  const [isRegisterMode, setIsRegisterMode] = useState(false);  // Track if showing register flow
  const [registerStep, setRegisterStep] = useState('role-selection');  // 'role-selection' or 'form'
  const [selectedRole, setSelectedRole] = useState(null);  // 'customer', 'courier', 'business'
  const [formData, setFormData] = useState({
    // Genel alanlar
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'customer',
    phone: '',
    city: '',
    district: '',
    
    // Kurye için
    vehicle_type: '',
    license_photo: null,
    id_photo: null,
    vehicle_photo: null,
    
    // İşletme için
    business_name: '',
    business_tax_id: '',
    business_photo: null,
    address: ''
  });
  const [theme, setTheme] = useState('light');

  // Theme toggle (no localStorage - use system default)
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  useEffect(() => {
    // Use system preference instead of localStorage
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(prefersDark ? 'dark' : 'light');
  }, []);

  // Handle email/password login - USE CONTEXT METHOD
  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(''); // Clear previous errors

    try {
      console.log('🎯 Attempting login via context...', { email: formData.email, contextLogin: !!contextLogin });
      
      if (!contextLogin) {
        throw new Error('Context login function not available');
      }
      
      // Use context's login method - this properly updates auth state
      const result = await contextLogin(formData.email, formData.password);
      
      console.log('🎯 Context login result:', result);
      
      if (result && result.success) {
        // Success!
        setError('');
        console.log('✅ About to call callbacks...');
        
        // Call onLogin callback if provided
        if (onLogin) {
          console.log('✅ Calling onLogin callback...');
          onLogin(result);
        }
        
        // Close modal - React will handle routing based on updated auth state
        if (onClose) {
          console.log('✅ Calling onClose callback...');
          onClose();
        } else {
          console.log('❌ onClose callback not provided!');
        }
        
        // No need for redirect - context updates user state and React re-renders
        console.log('✅ Login successful, context updated');
      } else {
        // Handle error from context
        const errorMsg = result?.error || 'Giriş başarısız';
        setError(errorMsg);
        console.log('❌ Login failed:', errorMsg, result);
        toast.error(`❌ ${errorMsg}`);
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      
      // Better error messages for common issues
      let errorMsg = 'Bağlantı hatası. Lütfen tekrar deneyin.';
      
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        errorMsg = 'Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin veya daha sonra tekrar deneyin.';
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      setError(errorMsg);
      toast.error(`❌ ${errorMsg}`);
    }
    setLoading(false);
  };

  // Handle role selection
  const handleRoleSelect = (role) => {
    setSelectedRole(role);
    setFormData({ ...formData, role });
    setRegisterStep('form');
  };

  // Handle registration
  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Basic validation
    if (!formData.email || !formData.password) {
      setError('E-posta ve şifre zorunludur');
      toast.error('❌ E-posta ve şifre zorunludur');
      setLoading(false);
      return;
    }

    // Role-specific validation
    if (selectedRole === 'customer') {
      if (!formData.first_name || !formData.last_name || !formData.phone || !formData.city) {
        setError('Tüm alanları doldurun');
        toast.error('❌ Tüm alanları doldurun');
        setLoading(false);
        return;
      }
    }

    if (selectedRole === 'courier') {
      if (!formData.first_name || !formData.last_name || !formData.phone || !formData.city || !formData.district || !formData.vehicle_type) {
        setError('Tüm alanları doldurun');
        toast.error('❌ Tüm alanları doldurun');
        setLoading(false);
        return;
      }
      if (!formData.license_photo || !formData.id_photo || !formData.vehicle_photo) {
        setError('Tüm fotoğrafları yükleyin');
        toast.error('❌ Ehliyet, kimlik ve araç ruhsat fotoğraflarını yükleyin');
        setLoading(false);
        return;
      }
    }

    if (selectedRole === 'business') {
      if (!formData.business_name || !formData.business_tax_id || !formData.first_name || !formData.last_name || !formData.phone) {
        setError('Tüm alanları doldurun');
        toast.error('❌ Tüm alanları doldurun');
        setLoading(false);
        return;
      }
      if (!formData.business_photo) {
        setError('İşletme fotoğrafı yükleyin');
        toast.error('❌ İşletme fotoğrafını yükleyin');
        setLoading(false);
        return;
      }
    }

    try {
      // FormData ile dosya yükleme için
      const formDataToSend = new FormData();
      formDataToSend.append('email', formData.email);
      formDataToSend.append('password', formData.password);
      formDataToSend.append('first_name', formData.first_name || '');
      formDataToSend.append('last_name', formData.last_name || '');
      formDataToSend.append('role', selectedRole);
      formDataToSend.append('phone', formData.phone || '');
      formDataToSend.append('city', formData.city || '');

      // Role-specific data
      if (selectedRole === 'courier') {
        formDataToSend.append('district', formData.district);
        formDataToSend.append('vehicle_type', formData.vehicle_type);
        if (formData.license_photo) formDataToSend.append('license_photo', formData.license_photo);
        if (formData.id_photo) formDataToSend.append('id_photo', formData.id_photo);
        if (formData.vehicle_photo) formDataToSend.append('vehicle_photo', formData.vehicle_photo);
      }

      if (selectedRole === 'business') {
        formDataToSend.append('business_name', formData.business_name);
        formDataToSend.append('business_tax_id', formData.business_tax_id);
        if (formData.business_photo) formDataToSend.append('business_photo', formData.business_photo);
      }

      // API call with FormData
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || ''}/api/auth/register`, {
        method: 'POST',
        body: formDataToSend,
        credentials: 'include' // for cookies
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Kayıt başarısız');
      }

      const result = await response.json();

      if (result?.success) {
        const roleNames = {
          customer: 'Müşteri',
          courier: 'Kurye',
          business: 'İşletme'
        };
        toast.success(`✅ ${roleNames[selectedRole]} kaydı başarılı! ${selectedRole === 'courier' || selectedRole === 'business' ? 'Onay bekliyor.' : 'Hoş geldiniz!'}`);
        
        // Reload to trigger auth check
        await checkAuthStatus();
        
        if (onLogin) {
          onLogin(result);
        }
        
        if (onClose) {
          onClose();
        }
      } else {
        const errorMsg = result?.error || 'Kayıt başarısız';
        setError(errorMsg);
        toast.error(`❌ ${errorMsg}`);
      }
    } catch (error) {
      console.error('❌ Register error:', error);
      const errorMsg = error.message || 'Kayıt hatası';
      setError(errorMsg);
      toast.error(`❌ ${errorMsg}`);
    }
    setLoading(false);
  };

  // Handle Google OAuth
  const handleGoogleLogin = () => {
    setLoading(true);
    
    // Redirect to Emergent Auth
    const redirectUrl = encodeURIComponent(window.location.origin + '/dashboard');
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  // Handle Apple Login (Placeholder)
  const handleAppleLogin = () => {
    toast.error('Apple giriş yakında aktif olacak!');
  };

  // Check for session_id in URL fragment (after Google OAuth redirect)
  useEffect(() => {
    const checkForSessionId = async () => {
      const fragment = window.location.hash.substring(1);
      const params = new URLSearchParams(fragment);
      const sessionId = params.get('session_id');
      
      if (sessionId) {
        setLoading(true);
        
        try {
          // Process session with backend
          const response = await api("/auth/google/session", {
            method: "POST",
            body: JSON.stringify({ session_id: sessionId })
          });
          
          if (response.ok) {
            const result = await response.json();
            if (result.access_token) {
              // Clear URL fragment
              window.history.replaceState({}, document.title, window.location.pathname);
              
              onLogin && onLogin(result);
              onClose && onClose();
              toast.success('Google ile giriş başarılı!');
            }
          }
        } catch (error) {
          console.error('Google OAuth error:', error);
          toast.error('Google giriş başarısız');
        }
        
        setLoading(false);
      }
    };

    checkForSessionId();
  }, [onLogin]);

  const backgroundClass = theme === 'dark' 
    ? 'bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900'
    : 'bg-gradient-to-br from-orange-50 via-red-50 to-yellow-50';

  const cardClass = theme === 'dark'
    ? 'bg-gray-800/70 border-gray-700/50 backdrop-blur-xl'
    : 'bg-white/70 border-white/50 backdrop-blur-xl';

  // Show Modern Register Wizard
  if (showRegisterWizard) {
    return (
      <ModernRegister 
        onSuccess={(data) => {
          setShowRegisterWizard(false);
          if (onLogin) onLogin(data);
          if (onClose) onClose();
        }}
        onBack={() => setShowRegisterWizard(false)}
      />
    );
  }

  return (
    <div className={`${backgroundClass} flex items-center justify-center p-4 relative overflow-hidden max-w-md w-full`} style={{ minHeight: '500px' }}>
      {/* Background Decorations */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-orange-400/20 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-400/20 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-yellow-400/10 rounded-full blur-3xl"></div>
      </div>

      {/* Theme Toggle */}
      <Button
        onClick={toggleTheme}
        variant="ghost"
        size="sm"
        className="absolute top-4 right-4 z-50"
      >
        {theme === 'light' ? '🌙' : '☀️'}
      </Button>

      {/* Close Button */}
      {onClose && (
        <Button
          onClick={onClose}
          variant="ghost"
          size="sm"
          className="absolute top-4 left-4 z-50"
        >
          ← Geri
        </Button>
      )}

      {/* Main Login Card */}
      <Card className={`w-full max-w-md ${cardClass} shadow-2xl border relative z-10`}>
        <CardHeader className="text-center space-y-6">
          {/* Logo */}
          <div className="flex flex-col items-center space-y-4">
            <div className="text-center">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
                Kuryecini
              </h2>
              <p className="text-sm text-gray-500 mb-4">Türkiye'nin En Hızlı Teslimat Platformu</p>
            </div>
            <KuryeciniLogo size="xl" useRealLogo={true} />
          </div>
          
          <div>
            <CardTitle className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
              Hoş Geldiniz! 👋
            </CardTitle>
            <CardDescription className={theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
              Türkiye'nin en hızlı teslimat platformuna giriş yapın
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Login Method Selector */}
          <div className="grid grid-cols-3 gap-2 p-1 bg-gray-100/50 dark:bg-gray-700/50 rounded-lg">
            <Button
              type="button"
              variant={loginMethod === 'email' ? 'default' : 'ghost'}
              onClick={() => setLoginMethod('email')}
              className="text-xs"
            >
              📧 E-posta
            </Button>
            <Button
              type="button"
              variant={loginMethod === 'phone' ? 'default' : 'ghost'}
              onClick={() => setLoginMethod('phone')}
              className="text-xs"
            >
              📱 Telefon
            </Button>
            <Button
              type="button"
              variant={loginMethod === 'oauth' ? 'default' : 'ghost'}
              onClick={() => setLoginMethod('oauth')}
              className="text-xs"
            >
              🔐 OAuth
            </Button>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                Giriş yapılıyor...
              </p>
            </div>
          )}

          {/* Role Selection for Registration */}
          {!loading && loginMethod === 'email' && isRegisterMode && registerStep === 'role-selection' && (
            <div className="space-y-4">
              <div className="text-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Nasıl Kayıt Olmak İstersiniz?</h3>
                <p className="text-sm text-gray-600">Rolünüzü seçin</p>
              </div>

              {/* Role Cards */}
              <div className="grid grid-cols-1 gap-3">
                {/* Customer */}
                <button
                  type="button"
                  onClick={() => handleRoleSelect('customer')}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-all text-left group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-3xl">🛒</div>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 group-hover:text-orange-600">Müşteri</div>
                      <div className="text-xs text-gray-500">Sipariş vermek için kayıt olun</div>
                    </div>
                    <div className="text-orange-500">→</div>
                  </div>
                </button>

                {/* Courier */}
                <button
                  type="button"
                  onClick={() => handleRoleSelect('courier')}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-all text-left group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-3xl">🏍️</div>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 group-hover:text-orange-600">Kurye</div>
                      <div className="text-xs text-gray-500">Teslimat yapmak için kayıt olun</div>
                    </div>
                    <div className="text-orange-500">→</div>
                  </div>
                </button>

                {/* Business */}
                <button
                  type="button"
                  onClick={() => handleRoleSelect('business')}
                  className="p-4 border-2 border-gray-200 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-all text-left group"
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-3xl">🏪</div>
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 group-hover:text-orange-600">İşletme</div>
                      <div className="text-xs text-gray-500">Restoran/İşletme olarak kayıt olun</div>
                    </div>
                    <div className="text-orange-500">→</div>
                  </div>
                </button>
              </div>

              {/* Back to Login */}
              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsRegisterMode(false);
                    setRegisterStep('role-selection');
                    setSelectedRole(null);
                  }}
                  className="text-sm text-gray-600 hover:text-gray-800"
                >
                  ← Giriş Yap
                </button>
              </div>
            </div>
          )}

          {/* Email Login/Register Form */}
          {!loading && loginMethod === 'email' && (!isRegisterMode || (isRegisterMode && registerStep === 'form')) && (
            <form onSubmit={isRegisterMode ? handleRegister : handleEmailLogin} className="space-y-4">
              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start space-x-2">
                  <span className="text-red-600 text-lg">⚠️</span>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-800">{isRegisterMode ? 'Kayıt Hatası' : 'Giriş Hatası'}</p>
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                </div>
              )}
              
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <KuryeciniLogo size="small" />
                  <span className="text-sm font-medium text-gray-700">
                    {isRegisterMode ? 'E-posta ile Kayıt Ol' : 'E-posta ile Giriş'}
                  </span>
                </div>
                
                {/* Register Mode: Role-specific forms */}
                {isRegisterMode && (
                  <>
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-2 mb-3 flex items-center space-x-2">
                      <span className="text-xl">
                        {selectedRole === 'customer' && '🛒'}
                        {selectedRole === 'courier' && '🏍️'}
                        {selectedRole === 'business' && '🏪'}
                      </span>
                      <span className="text-sm font-medium text-orange-800">
                        {selectedRole === 'customer' && 'Müşteri Kaydı'}
                        {selectedRole === 'courier' && 'Kurye Kaydı'}
                        {selectedRole === 'business' && 'İşletme Kaydı'}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          setRegisterStep('role-selection');
                          setSelectedRole(null);
                        }}
                        className="ml-auto text-xs text-orange-600 hover:text-orange-800"
                      >
                        Değiştir
                      </button>
                    </div>

                    {/* MÜŞTERI FORMU */}
                    {selectedRole === 'customer' && (
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            type="text"
                            placeholder="Adınız"
                            value={formData.first_name}
                            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                            required
                            className="bg-white/80 backdrop-blur-sm"
                          />
                          <Input
                            type="text"
                            placeholder="Soyadınız"
                            value={formData.last_name}
                            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                            required
                            className="bg-white/80 backdrop-blur-sm"
                          />
                        </div>
                        <Input
                          type="tel"
                          placeholder="Telefon Numarası (05XX XXX XX XX)"
                          value={formData.phone}
                          onChange={(e) => setFormData({...formData, phone: e.target.value})}
                          required
                          className="bg-white/80 backdrop-blur-sm"
                        />
                        <select
                          value={formData.city}
                          onChange={(e) => setFormData({...formData, city: e.target.value})}
                          required
                          className="w-full px-3 py-2 border rounded-lg bg-white/80"
                        >
                          <option value="">Şehir Seçin</option>
                          {TURKISH_CITIES.map(city => (
                            <option key={city} value={city}>{city}</option>
                          ))}
                        </select>
                      </div>
                    )}

                    {/* KURYE FORMU */}
                    {selectedRole === 'courier' && (
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            type="text"
                            placeholder="Adınız"
                            value={formData.first_name}
                            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                            required
                            className="bg-white/80 backdrop-blur-sm"
                          />
                          <Input
                            type="text"
                            placeholder="Soyadınız"
                            value={formData.last_name}
                            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                            required
                            className="bg-white/80 backdrop-blur-sm"
                          />
                        </div>
                        
                        <Input
                          type="tel"
                          placeholder="Telefon Numarası"
                          value={formData.phone}
                          onChange={(e) => setFormData({...formData, phone: e.target.value})}
                          required
                          className="bg-white/80 backdrop-blur-sm"
                        />
                        
                        <div className="grid grid-cols-2 gap-2">
                          <select
                            value={formData.city}
                            onChange={(e) => setFormData({...formData, city: e.target.value})}
                            required
                            className="w-full px-3 py-2 border rounded-lg bg-white/80"
                          >
                            <option value="">Şehir</option>
                            {TURKISH_CITIES.map(city => (
                              <option key={city} value={city}>{city}</option>
                            ))}
                          </select>
                          <Input
                            type="text"
                            placeholder="İlçe"
                            value={formData.district}
                            onChange={(e) => setFormData({...formData, district: e.target.value})}
                            required
                            className="bg-white/80 backdrop-blur-sm"
                          />
                        </div>

                        <select
                          value={formData.vehicle_type}
                          onChange={(e) => setFormData({...formData, vehicle_type: e.target.value})}
                          required
                          className="w-full px-3 py-2 border rounded-lg bg-white/80"
                        >
                          <option value="">Araç Tipi Seçin</option>
                          <option value="bicycle">🚲 Bisiklet</option>
                          <option value="motorbike">🏍️ Motosiklet</option>
                          <option value="car">🚗 Araba</option>
                          <option value="van">🚚 Minivan</option>
                        </select>

                        {/* Dosya Yüklemeleri */}
                        <div className="space-y-2">
                          <div>
                            <label className="block text-xs text-gray-600 mb-1">📄 Ehliyet Fotoğrafı</label>
                            <input
                              type="file"
                              accept="image/*"
                              onChange={(e) => setFormData({...formData, license_photo: e.target.files[0]})}
                              required
                              className="w-full text-sm"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-gray-600 mb-1">🪪 Kimlik Fotoğrafı</label>
                            <input
                              type="file"
                              accept="image/*"
                              onChange={(e) => setFormData({...formData, id_photo: e.target.files[0]})}
                              required
                              className="w-full text-sm"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-gray-600 mb-1">🚗 Araç Ruhsat Fotoğrafı</label>
                            <input
                              type="file"
                              accept="image/*"
                              onChange={(e) => setFormData({...formData, vehicle_photo: e.target.files[0]})}
                              required
                              className="w-full text-sm"
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    {/* İŞLETME FORMU */}
                    {selectedRole === 'business' && (
                      <div className="space-y-3">
                        <Input
                          type="text"
                          placeholder="İşletme/Restoran Adı"
                          value={formData.business_name}
                          onChange={(e) => setFormData({...formData, business_name: e.target.value})}
                          required
                          className="bg-white/80 backdrop-blur-sm"
                        />
                        
                        <Input
                          type="text"
                          placeholder="Vergi Numarası"
                          value={formData.business_tax_id}
                          onChange={(e) => setFormData({...formData, business_tax_id: e.target.value})}
                          required
                          className="bg-white/80 backdrop-blur-sm"
                        />

                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            type="text"
                            placeholder="Yetkili Adı"
                            value={formData.first_name}
                            onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                            required
                            className="bg-white/80 backdrop-blur-sm"
                          />
                          <Input
                            type="text"
                            placeholder="Yetkili Soyadı"
                            value={formData.last_name}
                            onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                            required
                            className="bg-white/80 backdrop-blur-sm"
                          />
                        </div>

                        <Input
                          type="tel"
                          placeholder="Telefon Numarası"
                          value={formData.phone}
                          onChange={(e) => setFormData({...formData, phone: e.target.value})}
                          required
                          className="bg-white/80 backdrop-blur-sm"
                        />

                        <div>
                          <label className="block text-xs text-gray-600 mb-1">🏪 İşletme Fotoğrafı</label>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={(e) => setFormData({...formData, business_photo: e.target.files[0]})}
                            required
                            className="w-full text-sm"
                          />
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Email ve Şifre - Tüm roller için (Müşteri için ekstra, diğerleri için ana) */}
                {!isRegisterMode && (
                  <Input
                    type="email"
                    placeholder="ornek@email.com"
                    value={formData.email}
                    onChange={(e) => {
                      setFormData({...formData, email: e.target.value});
                      setError('');
                    }}
                    required
                    className={`${theme === 'dark' ? 'bg-gray-700/50 border-gray-600 text-white' : 'bg-white/80'} backdrop-blur-sm ${error ? 'border-red-300' : ''}`}
                  />
                )}
                
                {isRegisterMode && selectedRole !== 'customer' && (
                  <div className="space-y-2 mt-3 pt-3 border-t border-gray-200">
                    <Input
                      type="email"
                      placeholder="E-posta"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      required
                      className="bg-white/80 backdrop-blur-sm"
                    />
                    <Input
                      type="password"
                      placeholder="Şifre"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      required
                      className="bg-white/80 backdrop-blur-sm"
                    />
                  </div>
                )}

                {isRegisterMode && selectedRole === 'customer' && (
                  <div className="space-y-2 mt-3 pt-3 border-t border-gray-200">
                    <Input
                      type="email"
                      placeholder="E-posta"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                      required
                      className="bg-white/80 backdrop-blur-sm"
                    />
                    <Input
                      type="password"
                      placeholder="Şifre"
                      value={formData.password}
                      onChange={(e) => setFormData({...formData, password: e.target.value})}
                      required
                      className="bg-white/80 backdrop-blur-sm"
                    />
                  </div>
                )}
              </div>
              
              {!isRegisterMode && (
                <div>
                  <Input
                    type="password"
                    placeholder="Şifreniz"
                    value={formData.password}
                    onChange={(e) => {
                      setFormData({...formData, password: e.target.value});
                      setError('');
                    }}
                    required
                    className={`${theme === 'dark' ? 'bg-gray-700/50 border-gray-600 text-white' : 'bg-white/80'} backdrop-blur-sm ${error ? 'border-red-300' : ''}`}
                  />
                </div>
              )}
              
              <button 
                type="submit" 
                disabled={loading}
                className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-semibold py-3 rounded-lg shadow-lg transform transition-all duration-200 hover:scale-105 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <KuryeciniLogo size="small" className="opacity-90" />
                <span>{isRegisterMode ? "Kuryecini'ye Kayıt Ol" : "Kuryecini'ye Giriş Yap"}</span>
              </button>
              
              <div className="text-center space-y-2">
                {!isRegisterMode && (
                  <button
                    type="button"
                    onClick={() => window.showForgotPassword && window.showForgotPassword()}
                    className="text-sm text-orange-600 hover:text-orange-800 hover:underline transition-colors block w-full"
                  >
                    Şifremi Unuttum?
                  </button>
                )}
                
                {!isRegisterMode && (
                  <button
                    type="button"
                    onClick={() => {
                      setShowRegisterWizard(true);
                    }}
                    className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    Hesabınız yok mu? Kayıt Ol →
                  </button>
                )}
                
                {isRegisterMode && registerStep === 'form' && (
                  <button
                    type="button"
                    onClick={() => {
                      setRegisterStep('role-selection');
                      setSelectedRole(null);
                    }}
                    className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    ← Rol Seçimine Dön
                  </button>
                )}
              </div>
            </form>
          )}

          {/* Phone Login */}
          {!loading && loginMethod === 'phone' && (
            <div className="space-y-4">
              <PhoneAuth 
                onLogin={onLogin}
                onBack={() => setLoginMethod('email')}
              />
            </div>
          )}

          {/* OAuth Login Options */}
          {!loading && loginMethod === 'oauth' && (
            <div className="space-y-3">
              {/* Google Login */}
              <Button
                onClick={handleGoogleLogin}
                variant="outline"
                className={`w-full py-3 ${theme === 'dark' ? 'bg-gray-700/50 border-gray-600 text-white hover:bg-gray-600' : 'bg-white/80 hover:bg-white'} backdrop-blur-sm flex items-center justify-center space-x-3 transition-all duration-200 hover:scale-105`}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span className="font-medium">Google ile Devam Et</span>
              </Button>

              {/* Apple Login */}
              <Button
                onClick={handleAppleLogin}
                variant="outline"
                className={`w-full py-3 ${theme === 'dark' ? 'bg-gray-900/80 border-gray-600 text-white hover:bg-gray-800' : 'bg-black/80 text-white hover:bg-black'} backdrop-blur-sm flex items-center justify-center space-x-3 transition-all duration-200 hover:scale-105`}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/>
                </svg>
                <span className="font-medium">Apple ile Devam Et</span>
                <Badge variant="secondary" className="text-xs">Yakında</Badge>
              </Button>

              {/* Divider */}
              <div className="flex items-center space-x-4">
                <div className={`flex-1 h-px ${theme === 'dark' ? 'bg-gray-600' : 'bg-gray-300'}`}></div>
                <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                  veya
                </span>
                <div className={`flex-1 h-px ${theme === 'dark' ? 'bg-gray-600' : 'bg-gray-300'}`}></div>
              </div>

              <Button
                onClick={() => setLoginMethod('email')}
                variant="ghost"
                className="w-full"
              >
                📧 E-posta ile giriş yap
              </Button>
            </div>
          )}

          {/* Register Link removed - now handled in email form toggle */}

          {/* Features */}
          <div className="grid grid-cols-3 gap-4 pt-4">
            <div className="text-center">
              <div className="text-2xl mb-1">⚡</div>
              <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Hızlı Teslimat
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">🔒</div>
              <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Güvenli Ödeme
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl mb-1">📱</div>
              <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
                Kolay Kullanım
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModernLogin;