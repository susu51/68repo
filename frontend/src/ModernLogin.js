import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent } from "./components/ui/card";
import { KuryeciniTextLogo } from "./components/KuryeciniLogo";
import toast from 'react-hot-toast';
import { useCookieAuth } from './contexts/CookieAuthContext';
import { Mail, Lock, X, Chrome, Smartphone } from 'lucide-react';

export const ModernLogin = ({ onLogin, onClose }) => {
  const navigate = useNavigate();
  const { login: contextLogin } = useCookieAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });

  // Handle email/password login
  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('🎯 Attempting login via context...', { email: formData.email });
      
      if (!contextLogin) {
        throw new Error('Context login function not available');
      }
      
      // Use context's login method
      const result = await contextLogin(formData.email, formData.password);
      
      console.log('🎯 Context login result:', result);
      
      if (result && result.success) {
        setError('');
        console.log('✅ Login successful');
        
        toast.success('✅ Giriş başarılı!');
        
        // Call onLogin callback if provided
        if (onLogin) {
          console.log('✅ Calling onLogin callback...');
          onLogin(result);
        }
        
        // Close modal
        if (onClose) {
          console.log('✅ Calling onClose callback...');
          onClose();
        }
      } else {
        // Handle error from context
        const errorMsg = result?.error || 'Giriş başarısız';
        setError(errorMsg);
        console.log('❌ Login failed:', errorMsg, result);
        toast.error(`❌ ${errorMsg}`);
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      
      let errorMsg = 'Bağlantı hatası. Lütfen tekrar deneyin.';
      
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
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

  // Handle OAuth login (placeholder - will be activated later)
  const handleOAuthLogin = (provider) => {
    toast.info(`${provider} ile giriş yakında aktif olacak!`);
    // TODO: Implement OAuth login
  };

  // Handle phone login (placeholder - will be activated later)
  const handlePhoneLogin = () => {
    toast.info('Telefon ile giriş yakında aktif olacak!');
    // TODO: Implement phone login
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="relative w-full max-w-md mx-4 shadow-2xl border-0 overflow-hidden">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-orange-500 via-pink-500 to-purple-600 opacity-90"></div>
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 text-white/80 hover:text-white transition-colors"
        >
          <X className="w-6 h-6" />
        </button>

        <CardContent className="relative z-10 p-8">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4">
              <KuryeciniTextLogo className="h-10 text-white" />
            </div>
          </div>

          {/* Title */}
          <h2 className="text-3xl font-bold text-white text-center mb-2">
            Hoş Geldiniz
          </h2>
          <p className="text-white/80 text-center mb-8">
            Hesabınıza giriş yapın
          </p>

          {/* Email/Password Login Form */}
          <form onSubmit={handleEmailLogin} className="space-y-4">
            {/* Email Input */}
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/60" />
              <Input
                type="email"
                placeholder="E-posta adresiniz"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className="w-full pl-12 pr-4 py-3 bg-white/10 backdrop-blur-md border-white/20 text-white placeholder:text-white/50 focus:border-white/40 focus:ring-2 focus:ring-white/20 rounded-xl"
              />
            </div>

            {/* Password Input */}
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/60" />
              <Input
                type="password"
                placeholder="Şifreniz"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                className="w-full pl-12 pr-4 py-3 bg-white/10 backdrop-blur-md border-white/20 text-white placeholder:text-white/50 focus:border-white/40 focus:ring-2 focus:ring-white/20 rounded-xl"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-500/20 backdrop-blur-sm border border-red-400/30 text-white px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}

            {/* Login Button */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-white text-orange-600 hover:bg-white/90 font-semibold py-3 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-orange-600/30 border-t-orange-600 rounded-full animate-spin"></div>
                  <span>Giriş yapılıyor...</span>
                </div>
              ) : (
                'Giriş Yap'
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/20"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-gradient-to-br from-orange-500/50 via-pink-500/50 to-purple-600/50 backdrop-blur-sm text-white/80 rounded-full">
                veya
              </span>
            </div>
          </div>

          {/* OAuth & Phone Login Options */}
          <div className="space-y-3">
            {/* Google OAuth - Placeholder */}
            <button
              type="button"
              onClick={() => handleOAuthLogin('Google')}
              className="w-full flex items-center justify-center gap-3 bg-white/10 backdrop-blur-md hover:bg-white/20 border border-white/20 text-white font-medium py-3 rounded-xl transition-all duration-200"
            >
              <Chrome className="w-5 h-5" />
              <span>Google ile Giriş Yap</span>
            </button>

            {/* Phone Login - Placeholder */}
            <button
              type="button"
              onClick={handlePhoneLogin}
              className="w-full flex items-center justify-center gap-3 bg-white/10 backdrop-blur-md hover:bg-white/20 border border-white/20 text-white font-medium py-3 rounded-xl transition-all duration-200"
            >
              <Smartphone className="w-5 h-5" />
              <span>Telefon ile Giriş Yap</span>
            </button>
          </div>

          {/* Register Link - Removed as per requirement */}
          {/* Registration is now on separate /register page */}

          {/* Forgot Password */}
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => toast.info('Şifre sıfırlama özelliği yakında eklenecek')}
              className="text-white/80 hover:text-white text-sm underline transition-colors"
            >
              Şifrenizi mi unuttunuz?
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ModernLogin;
