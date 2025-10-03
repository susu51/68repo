import React, { useState } from 'react';
import { ModernLogin } from '../ModernLogin';
import ForgotPassword from '../pages/Auth/ForgotPassword';
import ResetPassword from '../pages/Auth/ResetPassword';

const AuthWrapper = ({ children, user, onLogin }) => {
  const [authMode, setAuthMode] = useState('login'); // 'login', 'forgot', 'reset'

  // Expose forgot password function to window for ModernLogin
  React.useEffect(() => {
    window.showForgotPassword = () => setAuthMode('forgot');
    
    // Cleanup
    return () => {
      delete window.showForgotPassword;
    };
  }, []);

  // Check if we're on reset password route
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    
    if (token && window.location.pathname === '/reset-password') {
      setAuthMode('reset');
    }
  }, []);

  // If user is logged in, show main app
  if (user) {
    return children;
  }

  // Show appropriate auth page
  switch (authMode) {
    case 'forgot':
      return (
        <ForgotPassword 
          onBackToLogin={() => setAuthMode('login')}
        />
      );
    case 'reset':
      return (
        <ResetPassword 
          onBackToLogin={() => {
            setAuthMode('login');
            // Clear URL params
            window.history.replaceState({}, document.title, '/');
          }}
        />
      );
    default:
      return (
        <ModernLogin 
          onLogin={onLogin}
          onRegisterClick={() => console.log('Register clicked')}
          onClose={() => console.log('Close clicked')}
        />
      );
  }
};

export default AuthWrapper;