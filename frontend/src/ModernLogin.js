import React, { useState, useEffect } from 'react';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { KuryeciniLogo, KuryeciniTextLogo } from "./components/KuryeciniLogo";
import PhoneAuth from "./PhoneAuth";
import toast from 'react-hot-toast';
import { api } from './api/http';  // Use cookie-aware API client

export const ModernLogin = ({ onLogin, onRegisterClick, onClose }) => {
  const [loginMethod, setLoginMethod] = useState('email');
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
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

  // Handle email/password login - SIMPLIFIED WORKING VERSION
  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Direct fetch call - bypass API wrapper issues
      const response = await fetch('http://localhost:8001/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        })
      });
      
      console.log('🎯 Login response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('🎯 Login result:', result);
        
        if (result.success) {
          // Store token for development
          if (result.access_token) {
            localStorage.setItem('access_token', result.access_token);
          }
          
          // Success actions
          onLogin && onLogin({ success: true, ...result });
          onClose && onClose();
          toast.success('✅ Giriş başarılı!');
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Giriş başarısız');
      }
    } catch (error) {
      console.error('❌ Login error:', error);
      toast.error(`Giriş hatası: ${error.message}`);
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

  return (
    <div className={`min-h-screen ${backgroundClass} flex items-center justify-center p-4 relative overflow-hidden`}>
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

          {/* Email Login Form */}
          {!loading && loginMethod === 'email' && (
            <form onSubmit={handleEmailLogin} className="space-y-4">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <KuryeciniLogo size="small" />
                  <span className="text-sm font-medium text-gray-700">E-posta ile Giriş</span>
                </div>
                <Input
                  type="email"
                  placeholder="ornek@email.com"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                  className={`${theme === 'dark' ? 'bg-gray-700/50 border-gray-600 text-white' : 'bg-white/80'} backdrop-blur-sm`}
                />
              </div>
              <div>
                <Input
                  type="password"
                  placeholder="Şifreniz"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  required
                  className={`${theme === 'dark' ? 'bg-gray-700/50 border-gray-600 text-white' : 'bg-white/80'} backdrop-blur-sm`}
                />
              </div>
              
              <button 
                type="submit" 
                disabled={loading}
                className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-semibold py-3 rounded-lg shadow-lg transform transition-all duration-200 hover:scale-105 disabled:opacity-50"
              >
                <div className="flex items-center justify-center space-x-2">
                  <KuryeciniLogo size="small" className="opacity-90" />
                  <span>Kuryecini'ye Giriş Yap</span>
                </div>
              </button>
              
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => window.showForgotPassword && window.showForgotPassword()}
                  className="text-sm text-orange-600 hover:text-orange-800 hover:underline transition-colors"
                >
                  Şifremi Unuttum?
                </button>
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

          {/* Register Link */}
          {!loading && (
            <div className="text-center pt-4 border-t border-gray-200/50 dark:border-gray-700/50">
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-600'}`}>
                Hesabınız yok mu?{' '}
                <button
                  onClick={onRegisterClick}
                  className="text-orange-600 hover:text-orange-700 font-medium underline transition-colors"
                >
                  Kayıt Ol
                </button>
              </p>
            </div>
          )}

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