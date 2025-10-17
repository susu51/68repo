// ModernLogin.js - Simple wrapper for backward compatibility
// Now users should use /login and /register routes

import React from 'react';
import { useNavigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';

export const ModernLogin = ({ onClose }) => {
  const navigate = useNavigate();
  
  React.useEffect(() => {
    // Redirect to /login route
    navigate('/login');
  }, [navigate]);

  return <LoginPage />;
};

export default ModernLogin;
