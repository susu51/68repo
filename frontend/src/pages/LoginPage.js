import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useCookieAuth } from './contexts/CookieAuthContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useCookieAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(formData.email, formData.password);
      
      if (result && result.success) {
        toast.success('✅ Giriş başarılı!');
        // CookieAuthContext will handle navigation
      } else {
        toast.error(result?.error || 'Giriş başarısız');
      }
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Bağlantı hatası');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-orange-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-orange-600 mb-2">🚀 Kuryecini</h1>
          <p className="text-gray-600">Hızlı ve Güvenli Teslimat</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Giriş Yap</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                E-posta
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="ornek@email.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Şifre
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-orange-600 text-white py-3 rounded-lg hover:bg-orange-700 disabled:opacity-50 font-medium transition-colors"
            >
              {loading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
            </button>
          </form>

          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              Hesabınız yok mu?{' '}
              <button
                onClick={() => navigate('/register')}
                className="text-orange-600 font-medium hover:text-orange-700"
              >
                Kayıt Ol
              </button>
            </p>
          </div>

          {/* Back to Home */}
          <div className="mt-4 text-center">
            <button
              onClick={() => navigate('/')}
              className="text-gray-500 hover:text-gray-700 text-sm"
            >
              ← Ana Sayfaya Dön
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
