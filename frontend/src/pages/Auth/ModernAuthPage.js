import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import KuryeciniLogo from '../../components/KuryeciniLogo';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "https://kuryecini-hub.preview.emergentagent.com";

const ModernAuthPage = () => {
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState('email'); // 'email', 'google', 'apple'
  const [isLogin, setIsLogin] = useState(true); // true for login, false for register
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    confirmPassword: '',
    acceptKVKK: false
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  const navigate = useNavigate();
  const location = useLocation();

  // Check for session_id in URL fragment after OAuth redirect
  useEffect(() => {
    const hash = window.location.hash;
    if (hash && hash.includes('session_id=')) {
      const sessionId = hash.split('session_id=')[1].split('&')[0];
      processSessionId(sessionId);
    }
  }, []);

  const processSessionId = async (sessionId) => {
    setLoading(true);
    setMessage('🔄 Google ile giriş yapılıyor...');
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/emergent/session-data`, {
        method: 'GET',
        headers: {
          'X-Session-ID': sessionId,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Oturum doğrulaması başarısız');
      }

      const data = await response.json();
      
      // Set session token in cookie
      document.cookie = `session_token=${data.session_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
      
      // Clean URL
      window.history.replaceState(null, '', window.location.pathname);
      
      // Redirect to dashboard
      setMessage('✅ Giriş başarılı! Yönlendiriliyorsunuz...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
      
    } catch (error) {
      console.error('Session processing error:', error);
      setMessage('❌ Giriş başarısız. Lütfen tekrar deneyin.');
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const redirectUrl = encodeURIComponent(`${window.location.origin}/auth`);
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    setErrors({});
    setMessage('');
    setLoading(true);

    // Validation
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'E-posta adresi gerekli';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Geçerli bir e-posta adresi girin';
    }

    if (!formData.password) {
      newErrors.password = 'Şifre gerekli';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Şifre en az 6 karakter olmalı';
    }

    if (!isLogin) {
      if (!formData.name) {
        newErrors.name = 'Ad Soyad gerekli';
      }
      
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Şifreler eşleşmiyor';
      }
      
      if (!formData.acceptKVKK) {
        newErrors.acceptKVKK = 'KVKK şartlarını kabul etmelisiniz';
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      setLoading(false);
      return;
    }

    try {
      const endpoint = isLogin 
        ? `${BACKEND_URL}/api/auth/login`
        : `${BACKEND_URL}/api/auth/register`;
      
      const payload = isLogin
        ? { email: formData.email, password: formData.password }
        : { 
            email: formData.email, 
            password: formData.password,
            name: formData.name,
            role: 'customer'
          };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'İşlem başarısız');
      }

      setMessage(isLogin ? '✅ Giriş başarılı!' : '✅ Kayıt başarılı! Giriş yapılıyor...');
      
      // Set cookie if token provided
      if (data.access_token) {
        document.cookie = `session_token=${data.access_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
      }

      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);

    } catch (error) {
      console.error('Auth error:', error);
      setMessage(`❌ ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  // Background gradient styles
  const bgGradient = isDarkMode
    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    : 'linear-gradient(135deg, #f6d365 0%, #fda085 100%)';

  const cardBg = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.95)';
  const textColor = isDarkMode ? '#ffffff' : '#1a202c';
  const mutedTextColor = isDarkMode ? '#e2e8f0' : '#4a5568';

  return (
    <div 
      style={{
        minHeight: '100vh',
        background: bgGradient,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        position: 'relative',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
      }}
    >
      {/* Theme Toggle */}
      <button
        onClick={() => setIsDarkMode(!isDarkMode)}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          background: 'rgba(255, 255, 255, 0.2)',
          border: 'none',
          borderRadius: '50%',
          width: '50px',
          height: '50px',
          fontSize: '24px',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}
        onMouseEnter={(e) => {
          e.target.style.transform = 'scale(1.1)';
          e.target.style.background = 'rgba(255, 255, 255, 0.3)';
        }}
        onMouseLeave={(e) => {
          e.target.style.transform = 'scale(1)';
          e.target.style.background = 'rgba(255, 255, 255, 0.2)';
        }}
      >
        {isDarkMode ? '☀️' : '🌙'}
      </button>

      {/* Main Auth Card */}
      <div
        style={{
          background: cardBg,
          backdropFilter: 'blur(20px)',
          borderRadius: '24px',
          padding: '40px',
          maxWidth: '480px',
          width: '100%',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
          border: isDarkMode ? '1px solid rgba(255, 255, 255, 0.2)' : '1px solid rgba(0, 0, 0, 0.1)'
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <div
            style={{
              display: 'inline-block',
              background: 'rgba(255, 255, 255, 0.9)',
              borderRadius: '16px',
              padding: '15px',
              marginBottom: '20px'
            }}
          >
            <KuryeciniLogo width={80} height={80} />
          </div>
          
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: '700', 
            color: textColor,
            margin: '10px 0'
          }}>
            Hoş Geldiniz 👋
          </h1>
          
          <p style={{ 
            fontSize: '16px', 
            color: mutedTextColor,
            margin: '0'
          }}>
            Türkiye'nin en hızlı teslimat platformuna {isLogin ? 'giriş' : 'kayıt'} yapın
          </p>
        </div>

        {/* Tabs */}
        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          marginBottom: '30px',
          borderBottom: `2px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}`,
          paddingBottom: '10px'
        }}>
          <button
            onClick={() => setActiveTab('email')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'email' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'transparent',
              border: 'none',
              borderRadius: '12px',
              color: activeTab === 'email' ? '#fff' : textColor,
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
          >
            📧 E-posta
          </button>
          
          <button
            onClick={() => setActiveTab('google')}
            style={{
              flex: 1,
              padding: '12px',
              background: activeTab === 'google' 
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'transparent',
              border: 'none',
              borderRadius: '12px',
              color: activeTab === 'google' ? '#fff' : textColor,
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s ease'
            }}
          >
            🔑 Google
          </button>
          
          <button
            onClick={() => setActiveTab('apple')}
            disabled
            style={{
              flex: 1,
              padding: '12px',
              background: 'transparent',
              border: 'none',
              borderRadius: '12px',
              color: mutedTextColor,
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'not-allowed',
              opacity: 0.5,
              transition: 'all 0.3s ease'
            }}
          >
             Apple
          </button>
        </div>

        {/* Content */}
        {message && (
          <div style={{
            padding: '12px',
            borderRadius: '12px',
            marginBottom: '20px',
            background: message.includes('❌') 
              ? 'rgba(239, 68, 68, 0.1)'
              : 'rgba(34, 197, 94, 0.1)',
            color: message.includes('❌') ? '#ef4444' : '#22c55e',
            fontSize: '14px',
            textAlign: 'center'
          }}>
            {message}
          </div>
        )}

        {activeTab === 'email' && (
          <form onSubmit={handleEmailAuth}>
            {!isLogin && (
              <div style={{ marginBottom: '20px' }}>
                <label style={{ 
                  display: 'block', 
                  marginBottom: '8px', 
                  fontSize: '14px',
                  fontWeight: '500',
                  color: textColor
                }}>
                  Ad Soyad
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Ad Soyad"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    border: errors.name 
                      ? '2px solid #ef4444' 
                      : `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
                    background: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
                    color: textColor,
                    fontSize: '14px',
                    outline: 'none',
                    transition: 'all 0.3s ease'
                  }}
                />
                {errors.name && (
                  <span style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                    {errors.name}
                  </span>
                )}
              </div>
            )}

            <div style={{ marginBottom: '20px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: '500',
                color: textColor
              }}>
                E-posta
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="ornek@email.com"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: errors.email 
                    ? '2px solid #ef4444' 
                    : `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
                  background: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
                  color: textColor,
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'all 0.3s ease'
                }}
              />
              {errors.email && (
                <span style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                  {errors.email}
                </span>
              )}
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontSize: '14px',
                fontWeight: '500',
                color: textColor
              }}>
                Şifre
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="••••••••"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: errors.password 
                    ? '2px solid #ef4444' 
                    : `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
                  background: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
                  color: textColor,
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'all 0.3s ease'
                }}
              />
              {errors.password && (
                <span style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                  {errors.password}
                </span>
              )}
            </div>

            {!isLogin && (
              <>
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '8px', 
                    fontSize: '14px',
                    fontWeight: '500',
                    color: textColor
                  }}>
                    Şifre Tekrar
                  </label>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    placeholder="••••••••"
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      borderRadius: '12px',
                      border: errors.confirmPassword 
                        ? '2px solid #ef4444' 
                        : `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
                      background: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(255, 255, 255, 0.8)',
                      color: textColor,
                      fontSize: '14px',
                      outline: 'none',
                      transition: 'all 0.3s ease'
                    }}
                  />
                  {errors.confirmPassword && (
                    <span style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                      {errors.confirmPassword}
                    </span>
                  )}
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px',
                    fontSize: '13px',
                    color: textColor,
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      name="acceptKVKK"
                      checked={formData.acceptKVKK}
                      onChange={handleInputChange}
                      style={{ cursor: 'pointer' }}
                    />
                    KVKK ve Kullanım Şartlarını kabul ediyorum
                  </label>
                  {errors.acceptKVKK && (
                    <span style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                      {errors.acceptKVKK}
                    </span>
                  )}
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '14px',
                borderRadius: '12px',
                border: 'none',
                background: 'linear-gradient(135deg, #f97316 0%, #ef4444 100%)',
                color: '#fff',
                fontSize: '16px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                opacity: loading ? 0.7 : 1,
                marginBottom: '16px'
              }}
              onMouseEnter={(e) => {
                if (!loading) e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
              }}
            >
              {loading ? '⏳ İşleniyor...' : `🚀 ${isLogin ? 'Giriş Yap' : 'Kayıt Ol'}`}
            </button>

            {isLogin && (
              <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                <button
                  type="button"
                  onClick={() => alert('Şifre sıfırlama özelliği yakında eklenecek')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: isDarkMode ? '#a78bfa' : '#7c3aed',
                    fontSize: '14px',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  Şifremi Unuttum?
                </button>
              </div>
            )}

            <div style={{ textAlign: 'center' }}>
              <span style={{ fontSize: '14px', color: mutedTextColor }}>
                {isLogin ? 'Hesabın yok mu?' : 'Zaten hesabın var mı?'}
              </span>{' '}
              <button
                type="button"
                onClick={() => setIsLogin(!isLogin)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: isDarkMode ? '#60a5fa' : '#3b82f6',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
              >
                ➡️ {isLogin ? 'Kayıt Ol' : 'Giriş Yap'}
              </button>
            </div>
          </form>
        )}

        {activeTab === 'google' && (
          <div style={{ textAlign: 'center' }}>
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              style={{
                width: '100%',
                padding: '14px',
                borderRadius: '12px',
                border: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
                background: '#fff',
                color: '#1f2937',
                fontSize: '16px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                marginBottom: '16px'
              }}
              onMouseEnter={(e) => {
                if (!loading) e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
              }}
            >
              <svg width="20" height="20" viewBox="0 0 48 48">
                <path fill="#4285F4" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                <path fill="#34A853" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                <path fill="#EA4335" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
              </svg>
              Google ile Devam Et
            </button>

            <p style={{ 
              fontSize: '13px', 
              color: mutedTextColor,
              lineHeight: '1.6'
            }}>
              Google ile giriş yaptığınızda, Google hesabınızla güvenli bir şekilde platform'a erişebilirsiniz.
            </p>
          </div>
        )}

        {activeTab === 'apple' && (
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <p style={{ fontSize: '16px', color: mutedTextColor }}>
               Apple ile giriş özelliği yakında eklenecek...
            </p>
          </div>
        )}

        {/* Trust Badges */}
        <div style={{ 
          marginTop: '40px', 
          paddingTop: '30px',
          borderTop: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}`
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-around',
            gap: '20px'
          }}>
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>⚡</div>
              <div style={{ fontSize: '13px', color: mutedTextColor, fontWeight: '500' }}>
                Hızlı Teslimat
              </div>
            </div>
            
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>🔒</div>
              <div style={{ fontSize: '13px', color: mutedTextColor, fontWeight: '500' }}>
                Güvenli Ödeme
              </div>
            </div>
            
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>📱</div>
              <div style={{ fontSize: '13px', color: mutedTextColor, fontWeight: '500' }}>
                Kolay Kullanım
              </div>
            </div>
          </div>
        </div>

        {/* Payment Icons */}
        <div style={{ 
          marginTop: '30px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '15px',
          opacity: 0.6
        }}>
          <div style={{ 
            fontSize: '11px', 
            color: mutedTextColor,
            fontWeight: '500',
            letterSpacing: '0.5px'
          }}>
            VISA
          </div>
          <div style={{ 
            fontSize: '11px', 
            color: mutedTextColor,
            fontWeight: '500',
            letterSpacing: '0.5px'
          }}>
            MASTERCARD
          </div>
          <div style={{ 
            fontSize: '11px', 
            color: mutedTextColor,
            fontWeight: '500',
            letterSpacing: '0.5px'
          }}>
            3D SECURE
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModernAuthPage;
