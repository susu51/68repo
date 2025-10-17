import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { KuryeciniTextLogo } from "./components/KuryeciniLogo";
import toast from 'react-hot-toast';
import { useCookieAuth } from './contexts/CookieAuthContext';

export const ModernLogin = ({ onClose }) => {
  const navigate = useNavigate();
  const { login } = useCookieAuth();
  const [loginMethod, setLoginMethod] = useState('email');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: ''
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
      let errorMsg = 'Bağlantı hatası. Lütfen tekrar deneyin.';
      
      if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
        errorMsg = 'Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.';
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      setError(errorMsg);
      toast.error(`❌ ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md relative shadow-2xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 z-10 text-2xl font-bold w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 transition"
        >
          ×
        </button>

        <CardHeader className="space-y-4">
          {/* Logo and Title */}
          <div className="text-center space-y-2">
            <div className="flex justify-center mb-2">
              <KuryeciniTextLogo className="h-10" />
            </div>
            <p className="text-sm text-gray-500">Türkiye'nin En Hızlı Teslimat Platformu</p>
          </div>

          <CardTitle className="text-2xl text-center font-bold">Hoş Geldiniz! 👋</CardTitle>
          <p className="text-sm text-gray-600 text-center">Türkiye'nin en hızlı teslimat platformuna giriş yapın</p>

          {/* Login Method Tabs */}
          <div className="flex gap-2">
            <Button
              variant={loginMethod === 'email' ? 'default' : 'outline'}
              onClick={() => setLoginMethod('email')}
              className="flex-1"
              type="button"
            >
              📧 E-posta
            </Button>
            <Button
              variant={loginMethod === 'phone' ? 'default' : 'outline'}
              onClick={() => setLoginMethod('phone')}
              className="flex-1"
              type="button"
            >
              📱 Telefon
            </Button>
            <Button
              variant={loginMethod === 'oauth' ? 'default' : 'outline'}
              onClick={() => setLoginMethod('oauth')}
              className="flex-1"
              type="button"
            >
              🔑 OAuth
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {loginMethod === 'email' && (
            <form onSubmit={handleEmailLogin} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">E-posta ile Giriş</label>
                <Input
                  type="email"
                  placeholder="ornek@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Input
                  type="password"
                  placeholder="Şifre"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="h-11"
                />
              </div>

              <Button
                type="submit"
                className="w-full h-11 text-base bg-orange-600 hover:bg-orange-700"
                disabled={loading}
              >
                {loading ? "Giriş yapılıyor..." : "Kuryecini'ye Giriş Yap"}
              </Button>

              {/* Register Button */}
              <Button
                type="button"
                onClick={() => {
                  if (onClose) onClose();
                  navigate('/register');
                }}
                variant="outline"
                className="w-full h-11 text-base"
              >
                Kayıt Ol
              </Button>
            </form>
          )}

          {loginMethod === 'phone' && (
            <div className="space-y-4 py-8">
              <p className="text-center text-gray-600">📱 Telefon ile giriş yakında aktif olacak!</p>
              <Button
                variant="outline"
                onClick={() => setLoginMethod('email')}
                className="w-full"
                type="button"
              >
                ← E-posta ile Giriş
              </Button>
            </div>
          )}

          {loginMethod === 'oauth' && (
            <div className="space-y-4 py-8">
              <p className="text-center text-gray-600">🔑 OAuth girişi yakında aktif olacak!</p>
              <Button
                variant="outline"
                onClick={() => setLoginMethod('email')}
                className="w-full"
                type="button"
              >
                ← E-posta ile Giriş
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ModernLogin;
