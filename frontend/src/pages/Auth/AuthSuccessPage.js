import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import KuryeciniLogo from '../../components/KuryeciniLogo';

const AuthSuccessPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to dashboard after 2 seconds
    const timer = setTimeout(() => {
      navigate('/dashboard');
    }, 2000);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div 
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
      }}
    >
      <div
        style={{
          background: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          borderRadius: '24px',
          padding: '60px 40px',
          maxWidth: '480px',
          width: '100%',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          textAlign: 'center'
        }}
      >
        <div
          style={{
            display: 'inline-block',
            background: 'rgba(255, 255, 255, 0.9)',
            borderRadius: '16px',
            padding: '15px',
            marginBottom: '30px'
          }}
        >
          <KuryeciniLogo width={80} height={80} />
        </div>
        
        <div style={{ fontSize: '64px', marginBottom: '20px' }}>✅</div>
        
        <h1 style={{ 
          fontSize: '32px', 
          fontWeight: '700', 
          color: '#ffffff',
          marginBottom: '15px'
        }}>
          Giriş Başarılı!
        </h1>
        
        <p style={{ 
          fontSize: '18px', 
          color: '#e2e8f0',
          marginBottom: '30px'
        }}>
          Anasayfaya yönlendiriliyorsunuz...
        </p>
        
        <div style={{
          width: '60px',
          height: '60px',
          border: '4px solid rgba(255, 255, 255, 0.3)',
          borderTop: '4px solid #ffffff',
          borderRadius: '50%',
          margin: '0 auto',
          animation: 'spin 1s linear infinite'
        }} />
        
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
};

export default AuthSuccessPage;
