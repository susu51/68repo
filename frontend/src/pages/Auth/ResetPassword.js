import React, { useState, useEffect } from 'react';
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { KuryeciniLogo } from "../../components/KuryeciniLogo";
import toast from 'react-hot-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

export const ResetPassword = ({ onBackToLogin }) => {
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [token, setToken] = useState('');
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [validationErrors, setValidationErrors] = useState({});

  useEffect(() => {
    // Get token from URL params
    const urlParams = new URLSearchParams(window.location.search);
    const tokenParam = urlParams.get('token');
    
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      toast.error('Geçersiz sıfırlama bağlantısı');
    }
  }, []);

  const validatePassword = (password) => {
    const errors = {};
    
    if (password.length < 8) {
      errors.password = 'Parola en az 8 karakter olmalıdır';
    } else if (!/\d/.test(password)) {
      errors.password = 'Parola en az bir rakam içermelidir';
    } else if (!/[a-zA-Z]/.test(password)) {
      errors.password = 'Parola en az bir harf içermelidir';
    }
    
    return errors;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear validation errors when user types
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate passwords
    const passwordErrors = validatePassword(formData.password);
    if (formData.password !== formData.confirmPassword) {
      passwordErrors.confirmPassword = 'Parolalar eşleşmiyor';
    }
    
    if (Object.keys(passwordErrors).length > 0) {
      setValidationErrors(passwordErrors);
      return;
    }
    
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/reset`, {
        token: token,
        password: formData.password
      });
      
      if (response.data.success) {
        setCompleted(true);
        toast.success('Parola başarıyla sıfırlandı!');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Parola sıfırlama hatası';
      toast.error(errorMessage);
      
      // Handle specific error cases
      if (errorMessage.includes('Token')) {
        setTimeout(() => onBackToLogin(), 3000);
      }
    }
    setLoading(false);
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-4">
            <KuryeciniLogo size="lg" />
            <CardTitle className="text-2xl font-bold text-red-600">Geçersiz Bağlantı</CardTitle>
            <CardDescription>
              Parola sıfırlama bağlantısı geçersiz veya eksik.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={onBackToLogin}
              className="w-full bg-orange-500 hover:bg-orange-600"
            >
              Giriş Sayfasına Dön
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (completed) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-4">
            <KuryeciniLogo size="lg" />
            <CardTitle className="text-2xl font-bold text-green-600">Parola Sıfırlandı</CardTitle>
            <CardDescription>
              Parolanız başarıyla güncellendi. Artık yeni parolanızla giriş yapabilirsiniz.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  ✅ Parola başarıyla güncellendi
                </p>
              </div>
              
              <Button 
                onClick={onBackToLogin}
                className="w-full bg-orange-500 hover:bg-orange-600"
              >
                Giriş Yap
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <KuryeciniLogo size="lg" />
          <CardTitle className="text-2xl font-bold">Yeni Parola Belirle</CardTitle>
          <CardDescription>
            Hesabınız için güvenli bir parola oluşturun.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Yeni Parola
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="En az 8 karakter, rakam ve harf içermeli"
                required
                className="w-full"
              />
              {validationErrors.password && (
                <p className="text-sm text-red-600 mt-1">{validationErrors.password}</p>
              )}
            </div>
            
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                Parola Tekrar
              </label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                placeholder="Parolayı tekrar girin"
                required
                className="w-full"
              />
              {validationErrors.confirmPassword && (
                <p className="text-sm text-red-600 mt-1">{validationErrors.confirmPassword}</p>
              )}
            </div>
            
            <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
              <p className="font-medium mb-1">Güvenli parola kriterleri:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>En az 8 karakter</li>
                <li>En az bir rakam</li>
                <li>En az bir harf</li>
              </ul>
            </div>
            
            <Button 
              type="submit" 
              disabled={loading || !formData.password || !formData.confirmPassword}
              className="w-full bg-orange-500 hover:bg-orange-600"
            >
              {loading ? 'Güncelleniyor...' : 'Parolayı Güncelle'}
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <Button 
              variant="ghost" 
              onClick={onBackToLogin}
              className="text-sm"
            >
              ← Giriş Sayfasına Dön
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResetPassword;