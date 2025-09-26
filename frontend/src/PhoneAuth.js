import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Checkbox } from './components/ui/checkbox';
import { Badge } from './components/ui/badge';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Phone Input Component with Turkish formatting
const PhoneInput = ({ value, onChange, error, disabled }) => {
  const [displayValue, setDisplayValue] = useState(value || '');

  const formatTurkishPhone = (input) => {
    // Remove all non-digit characters
    const cleaned = input.replace(/\D/g, '');
    
    // Handle different cases
    if (cleaned.length === 0) return '';
    
    // If starts with 90, add + 
    if (cleaned.startsWith('90')) {
      const rest = cleaned.substring(2);
      if (rest.length <= 3) return `+90 ${rest}`;
      if (rest.length <= 6) return `+90 ${rest.substring(0, 3)} ${rest.substring(3)}`;
      if (rest.length <= 8) return `+90 ${rest.substring(0, 3)} ${rest.substring(3, 6)} ${rest.substring(6)}`;
      return `+90 ${rest.substring(0, 3)} ${rest.substring(3, 6)} ${rest.substring(6, 8)} ${rest.substring(8, 10)}`;
    }
    
    // If starts with 0, remove it and add +90
    if (cleaned.startsWith('0')) {
      const withoutZero = cleaned.substring(1);
      if (withoutZero.length <= 3) return `+90 ${withoutZero}`;
      if (withoutZero.length <= 6) return `+90 ${withoutZero.substring(0, 3)} ${withoutZero.substring(3)}`;
      if (withoutZero.length <= 8) return `+90 ${withoutZero.substring(0, 3)} ${withoutZero.substring(3, 6)} ${withoutZero.substring(6)}`;
      return `+90 ${withoutZero.substring(0, 3)} ${withoutZero.substring(3, 6)} ${withoutZero.substring(6, 8)} ${withoutZero.substring(8, 10)}`;
    }
    
    // If starts with 5, add +90
    if (cleaned.startsWith('5')) {
      if (cleaned.length <= 3) return `+90 ${cleaned}`;
      if (cleaned.length <= 6) return `+90 ${cleaned.substring(0, 3)} ${cleaned.substring(3)}`;
      if (cleaned.length <= 8) return `+90 ${cleaned.substring(0, 3)} ${cleaned.substring(3, 6)} ${cleaned.substring(6)}`;
      return `+90 ${cleaned.substring(0, 3)} ${cleaned.substring(3, 6)} ${cleaned.substring(6, 8)} ${cleaned.substring(8, 10)}`;
    }
    
    return input;
  };

  const handleChange = (e) => {
    const input = e.target.value;
    const formatted = formatTurkishPhone(input);
    setDisplayValue(formatted);
    
    // Extract clean phone number for API
    const cleanPhone = formatted.replace(/\D/g, '');
    let apiPhone = '';
    
    if (cleanPhone.startsWith('90') && cleanPhone.length >= 12) {
      apiPhone = '+' + cleanPhone.substring(0, 12);
    } else if (cleanPhone.length >= 10) {
      apiPhone = '+90' + cleanPhone.substring(cleanPhone.length - 10);
    }
    
    onChange(apiPhone);
  };

  return (
    <div>
      <Input
        type="tel"
        placeholder="+90 5XX XXX XX XX"
        value={displayValue}
        onChange={handleChange}
        disabled={disabled}
        className={error ? 'border-red-500' : ''}
        data-testid="phone-input"
      />
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
      <p className="text-xs text-gray-500 mt-1">
        Türk cep telefonu numaranızı girin
      </p>
    </div>
  );
};

// OTP Input Component
const OTPInput = ({ value, onChange, error, disabled }) => {
  const handleChange = (e) => {
    const input = e.target.value.replace(/\D/g, ''); // Only digits
    if (input.length <= 6) {
      onChange(input);
    }
  };

  return (
    <div>
      <Input
        type="text"
        placeholder="123456"
        value={value}
        onChange={handleChange}
        disabled={disabled}
        className={`text-center text-lg tracking-wider ${error ? 'border-red-500' : ''}`}
        maxLength={6}
        data-testid="otp-input"
      />
      {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
    </div>
  );
};

// Main Phone Authentication Component
const PhoneAuth = ({ onLoginSuccess }) => {
  const [step, setStep] = useState('phone'); // 'phone' | 'otp' | 'role_selection'
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpData, setOtpData] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [kvkkAccepted, setKvkkAccepted] = useState(false);
  const [errors, setErrors] = useState({});

  // KVKK countdown
  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [countdown]);

  // Mock OTP display for development
  const [mockOtp, setMockOtp] = useState(null);

  const validatePhone = (phoneNumber) => {
    if (!phoneNumber) return 'Telefon numarası gerekli';
    if (!phoneNumber.startsWith('+90')) return 'Geçersiz Türk telefon numarası';
    if (phoneNumber.length !== 13) return 'Telefon numarası 11 haneli olmalı';
    return null;
  };

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    const phoneError = validatePhone(phone);
    if (phoneError) {
      setErrors({ phone: phoneError });
      return;
    }

    if (!kvkkAccepted) {
      setErrors({ kvkk: 'KVKK metnini onaylamanız gerekli' });
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/otp/request`, {
        phone: phone,
        device_id: navigator.userAgent // Simple device ID
      });

      if (response.data.success) {
        setOtpData(response.data);
        setStep('otp');
        setCountdown(120); // 2 minutes countdown
        
        // Show mock OTP in development
        if (response.data.mock_otp) {
          setMockOtp(response.data.mock_otp);
          toast.info(`Geliştirici modu: OTP ${response.data.mock_otp}`);
        }
        
        toast.success('SMS gönderildi');
      } else {
        setErrors({ phone: response.data.message });
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'SMS gönderimi başarısız';
      setErrors({ phone: errorMsg });
      toast.error(errorMsg);
    }
    
    setLoading(false);
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    
    if (!otp || otp.length !== 6) {
      setErrors({ otp: 'OTP 6 haneli olmalı' });
      return;
    }

    setErrors({});
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/otp/verify`, {
        phone: phone,
        otp: otp
      });

      if (response.data.access_token) {
        // Login successful
        onLoginSuccess({
          access_token: response.data.access_token,
          refresh_token: response.data.refresh_token,
          user_data: response.data.user_data,
          user_type: response.data.user_type
        });
        toast.success('Giriş başarılı!');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'OTP doğrulama başarısız';
      setErrors({ otp: errorMsg });
      toast.error(errorMsg);
    }
    
    setLoading(false);
  };

  const handleResendOTP = async () => {
    if (countdown > 0) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/otp/request`, {
        phone: phone,
        device_id: navigator.userAgent
      });

      if (response.data.success) {
        setCountdown(120);
        if (response.data.mock_otp) {
          setMockOtp(response.data.mock_otp);
          toast.info(`Geliştirici modu: OTP ${response.data.mock_otp}`);
        }
        toast.success('SMS yeniden gönderildi');
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error('SMS gönderimi başarısız');
    }
    setLoading(false);
  };

  const formatCountdown = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (step === 'phone') {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-orange-600">Telefon Doğrulama</CardTitle>
          <CardDescription>
            Telefon numaranıza SMS ile kod gönderelim
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePhoneSubmit} className="space-y-4">
            <div>
              <Label htmlFor="phone">Telefon Numarası</Label>
              <PhoneInput
                value={phone}
                onChange={setPhone}
                error={errors.phone}
                disabled={loading}
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="kvkk"
                  checked={kvkkAccepted}
                  onCheckedChange={setKvkkAccepted}
                  disabled={loading}
                  data-testid="kvkk-checkbox"
                />
                <Label htmlFor="kvkk" className="text-sm">
                  <a 
                    href="#" 
                    className="text-orange-600 hover:text-orange-700"
                    onClick={(e) => {
                      e.preventDefault();
                      toast.info('KVKK metni: Kişisel verileriniz kanun kapsamında korunmaktadır.');
                    }}
                  >
                    KVKK metnini
                  </a> okudum ve kabul ediyorum
                </Label>
              </div>
              {errors.kvkk && <p className="text-sm text-red-500">{errors.kvkk}</p>}
            </div>

            <Button
              type="submit"
              disabled={loading || !phone || !kvkkAccepted}
              className="w-full bg-orange-600 hover:bg-orange-700"
              data-testid="send-otp-btn"
            >
              {loading ? 'Gönderiliyor...' : 'SMS Kodu Gönder'}
            </Button>
          </form>
        </CardContent>
      </Card>
    );
  }

  if (step === 'otp') {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-orange-600">SMS Doğrulama</CardTitle>
          <CardDescription>
            <div className="space-y-2">
              <p>{phone} numarasına gönderilen kodu girin</p>
              {countdown > 0 && (
                <Badge variant="secondary">
                  Kod {formatCountdown(countdown)} içinde geçersiz olacak
                </Badge>
              )}
            </div>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleOtpSubmit} className="space-y-4">
            <div>
              <Label htmlFor="otp">SMS Kodu</Label>
              <OTPInput
                value={otp}
                onChange={setOtp}
                error={errors.otp}
                disabled={loading}
              />
            </div>

            {mockOtp && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Geliştirici Modu:</strong> OTP Kodu: <code className="font-mono">{mockOtp}</code>
                </p>
              </div>
            )}

            <Button
              type="submit"
              disabled={loading || otp.length !== 6}
              className="w-full bg-orange-600 hover:bg-orange-700"
              data-testid="verify-otp-btn"
            >
              {loading ? 'Doğrulanıyor...' : 'Doğrula ve Giriş Yap'}
            </Button>

            <div className="flex justify-between items-center">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setStep('phone')}
                disabled={loading}
                data-testid="back-to-phone-btn"
              >
                ← Geri Dön
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={handleResendOTP}
                disabled={loading || countdown > 0}
                data-testid="resend-otp-btn"
              >
                {countdown > 0 ? formatCountdown(countdown) : 'Tekrar Gönder'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    );
  }

  return null;
};

export default PhoneAuth;