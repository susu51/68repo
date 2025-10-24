import React, { useState } from 'react';
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { KuryeciniLogo } from "../../components/KuryeciniLogo";
import toast from 'react-hot-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ForgotPassword = ({ onBackToLogin }) => {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [email, setEmail] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/forgot`, { email });
      
      if (response.data.success) {
        setSubmitted(true);
        toast.success('E-posta gönderildi! Gelen kutunuzu kontrol edin.');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Bir hata oluştu');
    }
    setLoading(false);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center space-y-4">
            <KuryeciniLogo size="lg" />
            <CardTitle className="text-2xl font-bold">E-posta Gönderildi</CardTitle>
            <CardDescription>
              Parola sıfırlama talimatları e-posta adresinize gönderildi. 
              Eğer hesabınız mevcutsa, birkaç dakika içinde bir e-posta alacaksınız.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  📧 E-posta gönderildi: <strong>{email}</strong>
                </p>
              </div>
              
              <div className="text-sm text-gray-600 space-y-2">
                <p>E-posta gelmedi mi?</p>
                <ul className="list-disc list-inside space-y-1 text-left">
                  <li>Spam klasörünü kontrol edin</li>
                  <li>E-posta adresinizi doğru yazdığınızdan emin olun</li>
                  <li>Birkaç dakika bekleyin</li>
                </ul>
              </div>
              
              <Button 
                variant="outline" 
                onClick={onBackToLogin}
                className="w-full"
              >
                ← Giriş Sayfasına Dön
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
          <CardTitle className="text-2xl font-bold">Şifremi Unuttum</CardTitle>
          <CardDescription>
            E-posta adresinizi girin, parola sıfırlama bağlantısını size gönderelim.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                E-posta Adresi
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ornek@email.com"
                required
                className="w-full"
              />
            </div>
            
            <Button 
              type="submit" 
              disabled={loading || !email}
              className="w-full bg-orange-500 hover:bg-orange-600"
            >
              {loading ? 'Gönderiliyor...' : 'Parola Sıfırlama Bağlantısı Gönder'}
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

export default ForgotPassword;