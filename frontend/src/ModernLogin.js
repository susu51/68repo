import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { KuryeciniTextLogo } from "./components/KuryeciniLogo";
import toast from 'react-hot-toast';
import { useCookieAuth } from './contexts/CookieAuthContext';
import { useTheme } from './contexts/ThemeContext';

export const ModernLogin = ({ onClose }) => {
  const navigate = useNavigate();
  const { login } = useCookieAuth();
  const { theme, toggleTheme } = useTheme();
  const [loginMethod, setLoginMethod] = useState('email');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    phone: ''
  });

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await login(formData.email, formData.password);
      
      if (result && result.success) {
        toast.success('✅ Giriş başarılı!');
        if (onClose) onClose();
      } else {
        const errorMsg = result?.error || 'Giriş başarısız';
        setError(errorMsg);
        toast.error(`❌ ${errorMsg}`);
      }
    } catch (error) {
      console.error('Login error:', error);
      const errorMsg = 'Bağlantı hatası. Lütfen tekrar deneyin.';
      setError(errorMsg);
      toast.error(`❌ ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneLogin = async (e) => {
    e.preventDefault();
    toast.info('📱 Telefon doğrulama kodu gönderiliyor...');
    // TODO: Implement phone auth
  };

  const handleOAuthLogin = (provider) => {
    toast.info(`🔑 ${provider} ile giriş yapılıyor...`);
    // TODO: Implement OAuth
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-lg relative shadow-2xl border-2 dark:border-gray-700 dark:bg-gray-800">
        {/* Close & Theme Toggle */}
        <div className="absolute top-4 right-4 flex items-center gap-2 z-10">
          <button
            onClick={toggleTheme}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            title={theme === 'light' ? 'Karanlık Mod' : 'Aydınlık Mod'}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          >
            ×
          </button>
        </div>

        <CardHeader className="space-y-6 pt-8">
          {/* Logo Section */}
          <div className="text-center space-y-3">
            <div className="flex justify-center mb-3">
              <div className="bg-gradient-to-r from-orange-500 to-orange-600 p-4 rounded-2xl shadow-lg">
                <KuryeciniTextLogo className="h-10" />
              </div>
            </div>
            <div className="inline-block px-4 py-1.5 bg-orange-100 dark:bg-orange-900/30 rounded-full">
              <p className="text-sm font-medium text-orange-800 dark:text-orange-300">
                🚀 Türkiye'nin En Hızlı Teslimat Platformu
              </p>
            </div>
          </div>

          <div className="text-center space-y-2">
            <CardTitle className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-orange-500 bg-clip-text text-transparent">
              Hoş Geldiniz!
            </CardTitle>
            <p className="text-gray-600 dark:text-gray-400">
              Hızlı ve güvenli teslimat için giriş yapın
            </p>
          </div>

          {/* Login Method Tabs */}
          <div className="flex gap-2 p-1 bg-gray-100 dark:bg-gray-900 rounded-lg">
            <button
              onClick={() => setLoginMethod('email')}
              className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
                loginMethod === 'email'
                  ? 'bg-white dark:bg-gray-700 text-orange-600 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              📧 E-posta
            </button>
            <button
              onClick={() => setLoginMethod('phone')}
              className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
                loginMethod === 'phone'
                  ? 'bg-white dark:bg-gray-700 text-orange-600 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              📱 Telefon
            </button>
            <button
              onClick={() => setLoginMethod('oauth')}
              className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
                loginMethod === 'oauth'
                  ? 'bg-white dark:bg-gray-700 text-orange-600 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              🔑 OAuth
            </button>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Email Login */}
          {loginMethod === 'email' && (
            <form onSubmit={handleEmailLogin} className="space-y-5">
              {error && (
                <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  E-posta Adresi
                </label>
                <Input
                  type="email"
                  placeholder="ornek@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="h-12 text-base dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">Şifre</label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="h-12 text-base dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <Button
                type="submit"
                className="w-full h-12 text-base font-semibold bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600 shadow-lg"
                disabled={loading}
              >
                {loading ? '⏳ Giriş yapılıyor...' : '🚀 Giriş Yap'}
              </Button>
            </form>
          )}

          {/* Phone Login */}
          {loginMethod === 'phone' && (
            <form onSubmit={handlePhoneLogin} className="space-y-5">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Telefon Numarası
                </label>
                <Input
                  type="tel"
                  placeholder="+90 5XX XXX XX XX"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  required
                  className="h-12 text-base dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              </div>

              <Button
                type="submit"
                className="w-full h-12 text-base font-semibold bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-700 hover:to-orange-600 shadow-lg"
                disabled={loading}
              >
                📱 Doğrulama Kodu Gönder
              </Button>
            </form>
          )}

          {/* OAuth Login */}
          {loginMethod === 'oauth' && (
            <div className="space-y-3">
              <Button
                onClick={() => handleOAuthLogin('Google')}
                variant="outline"
                className="w-full h-12 text-base font-semibold dark:border-gray-600 dark:hover:bg-gray-700"
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google ile Giriş Yap
              </Button>

              <Button
                onClick={() => handleOAuthLogin('Facebook')}
                variant="outline"
                className="w-full h-12 text-base font-semibold dark:border-gray-600 dark:hover:bg-gray-700"
              >
                <svg className="w-5 h-5 mr-2" fill="#1877F2" viewBox="0 0 24 24">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
                Facebook ile Giriş Yap
              </Button>
            </div>
          )}

          {/* Footer */}
          <div className="text-center pt-4 border-t dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Hesabınız yok mu?{' '}
              <button
                onClick={() => navigate('/register')}
                className="text-orange-600 dark:text-orange-400 font-semibold hover:underline"
              >
                Kayıt Ol
              </button>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModernLogin;
