import React from 'react';
import { useNavigate } from 'react-router-dom';
import ModernRegister from '../components/ModernRegister';
import { useCookieAuth } from '../contexts/CookieAuthContext';

const RegisterPage = () => {
  const navigate = useNavigate();
  const { checkAuthStatus } = useCookieAuth();

  const handleSuccess = async () => {
    // Recheck auth status after successful registration
    await checkAuthStatus();
    navigate('/');
  };

  const handleBack = () => {
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-orange-50">
      <ModernRegister 
        onSuccess={handleSuccess}
        onBack={handleBack}
      />
    </div>
  );
};

export default RegisterPage;
