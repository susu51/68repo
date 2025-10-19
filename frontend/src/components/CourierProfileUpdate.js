import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { User, Phone, Mail, CreditCard, Car, Save } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://food-dash-87.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierProfileUpdate = ({ user }) => {
  const [profile, setProfile] = useState({
    name: '',
    surname: '',
    phone: '',
    email: '',
    iban: '',
    vehicleType: '',
    plate: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Initialize from user data
    if (user) {
      setProfile({
        name: user.first_name || '',
        surname: user.last_name || '',
        phone: user.phone || '',
        email: user.email || '',
        iban: user.iban || '',
        vehicleType: user.vehicle_type || '',
        plate: user.license_plate || ''
      });
    }
  }, [user]);

  const handleInputChange = (field, value) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validateIBAN = (iban) => {
    // Remove spaces
    const cleanIBAN = iban.replace(/\s/g, '');
    
    // Check if starts with TR
    if (!cleanIBAN.startsWith('TR') && !cleanIBAN.startsWith('tr')) {
      return 'IBAN must start with TR';
    }
    
    // Check length (TR + 24 digits = 26 total)
    if (cleanIBAN.length !== 26) {
      return 'Turkish IBAN must be 26 characters (TR + 24 digits)';
    }
    
    return null;
  };

  const handleSaveProfile = async () => {
    try {
      setSaving(true);

      // Validate IBAN if provided
      if (profile.iban) {
        const ibanError = validateIBAN(profile.iban);
        if (ibanError) {
          toast.error(ibanError);
          return;
        }
      }

      const response = await fetch(`${API}/courier/profile`, {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profile)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Profil güncellenemedi');
      }

      const data = await response.json();
      
      // Optimistic UI update
      if (data.success && data.profile) {
        setProfile({
          name: data.profile.name || '',
          surname: data.profile.surname || '',
          phone: data.profile.phone || '',
          email: data.profile.email || '',
          iban: data.profile.iban || '',
          vehicleType: data.profile.vehicleType || '',
          plate: data.profile.plate || ''
        });
      }

      toast.success('Profil başarıyla güncellendi!');
    } catch (error) {
      console.error('Profil güncelleme hatası:', error);
      toast.error('Profil güncellenemedi: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          Profil Bilgileri
        </CardTitle>
        <CardDescription>
          Kişisel bilgilerinizi güncelleyin
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Name and Surname */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">
              <User className="h-4 w-4 inline mr-1" />
              Ad
            </Label>
            <Input
              id="name"
              value={profile.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Adınız"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="surname">
              <User className="h-4 w-4 inline mr-1" />
              Soyad
            </Label>
            <Input
              id="surname"
              value={profile.surname}
              onChange={(e) => handleInputChange('surname', e.target.value)}
              placeholder="Soyadınız"
            />
          </div>
        </div>

        {/* Phone and Email */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="phone">
              <Phone className="h-4 w-4 inline mr-1" />
              Telefon
            </Label>
            <Input
              id="phone"
              type="tel"
              value={profile.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
              placeholder="+90 555 123 4567"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="email">
              <Mail className="h-4 w-4 inline mr-1" />
              E-posta
            </Label>
            <Input
              id="email"
              type="email"
              value={profile.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="email@example.com"
            />
          </div>
        </div>

        {/* IBAN */}
        <div className="space-y-2">
          <Label htmlFor="iban">
            <CreditCard className="h-4 w-4 inline mr-1" />
            IBAN (TR ile başlamalı)
          </Label>
          <Input
            id="iban"
            value={profile.iban}
            onChange={(e) => handleInputChange('iban', e.target.value.toUpperCase())}
            placeholder="TR330006100519786457841326"
            maxLength={26}
          />
          <p className="text-xs text-muted-foreground">
            TR + 24 hane (toplam 26 karakter)
          </p>
        </div>

        {/* Vehicle Type and Plate */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="vehicleType">
              <Car className="h-4 w-4 inline mr-1" />
              Araç Tipi
            </Label>
            <select
              id="vehicleType"
              value={profile.vehicleType}
              onChange={(e) => handleInputChange('vehicleType', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Seçiniz</option>
              <option value="Motosiklet">Motosiklet</option>
              <option value="Scooter">Scooter</option>
              <option value="Bisiklet">Bisiklet</option>
              <option value="Araba">Araba</option>
            </select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="plate">
              <Car className="h-4 w-4 inline mr-1" />
              Plaka
            </Label>
            <Input
              id="plate"
              value={profile.plate}
              onChange={(e) => handleInputChange('plate', e.target.value.toUpperCase())}
              placeholder="34 ABC 123"
              maxLength={15}
            />
          </div>
        </div>

        {/* Save Button */}
        <Button
          className="w-full"
          onClick={handleSaveProfile}
          disabled={saving}
        >
          {saving ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Kaydediliyor...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Profili Kaydet
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
};
