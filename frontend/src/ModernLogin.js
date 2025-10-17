import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { KuryeciniLogo, KuryeciniTextLogo } from "./components/KuryeciniLogo";
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
          <div className="flex justify-center mb-4">
            <KuryeciniTextLogo className="h-12" />
          </div>
          <CardTitle className="text-2xl text-center">Hoş Geldiniz! 👋</CardTitle>
          
          {/* Login Method Tabs */}
          <div className="flex gap-2">
            <Button
              variant={loginMethod === 'email' ? 'default' : 'outline'}
              onClick={() => setLoginMethod('email')}
              className="flex-1"
            >
              📧 E-posta
            </Button>
            <Button
              variant={loginMethod === 'phone' ? 'default' : 'outline'}
              onClick={() => setLoginMethod('phone')}
              className="flex-1"
            >
              📱 Telefon
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {loginMethod === 'email' ? (
            <form onSubmit={handleEmailLogin} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium">E-posta</label>
                <Input
                  type="email"
                  placeholder="ornek@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="h-12"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Şifre</label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="h-12"
                />
              </div>

              <Button
                type="submit"
                className="w-full h-12 text-base"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="animate-spin mr-2">⏳</span>
                    Giriş yapılıyor...
                  </>
                ) : (
                  '🚀 Giriş Yap'
                )}
              </Button>
            </form>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 text-center">
                Telefon ile giriş yakında aktif olacak! 📱
              </p>
              <Button
                variant="outline"
                onClick={() => setLoginMethod('email')}
                className="w-full"
              >
                ← E-posta ile Giriş Yap
              </Button>
            </div>
          )}

          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Hesabınız yok mu?{' '}
              <button
                onClick={() => {
                  if (onClose) onClose();
                  navigate('/register');
                }}
                className="text-orange-600 font-semibold hover:text-orange-700 hover:underline"
              >
                Kayıt Ol
              </button>
            </p>
          </div>

          {/* Demo Credentials */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className="text-xs text-blue-800 font-medium mb-2">💡 Demo Hesaplar:</p>
            <div className="text-xs text-blue-700 space-y-1">
              <p>👤 Müşteri: customer@test.com / test123</p>
              <p>🏪 İşletme: business@test.com / test123</p>
              <p>🏍️ Kurye: courier@test.com / test123</p>
              <p>👨‍💼 Admin: admin@kuryecini.com / admin123</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModernLogin;
