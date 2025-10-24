import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card.jsx';
import { Button } from './ui/button.jsx';
import { Input } from './ui/input.jsx';
import { Label } from './ui/label.jsx';
import { User, Phone, Mail, Save } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CustomerProfile = ({ user }) => {
  const [profile, setProfile] = useState({
    name: '',
    surname: '',
    email: '',
    phone: ''
  });
  
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Initialize from user data
    if (user) {
      setProfile({
        name: user.first_name || '',
        surname: user.last_name || '',
        email: user.email || '',
        phone: user.phone || ''
      });
    }
  }, [user]);

  const handleInputChange = (field, value) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSaveProfile = async () => {
    try {
      setSaving(true);

      const response = await fetch(`${API}/customer/profile`, {
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
          email: data.profile.email || '',
          phone: data.profile.phone || ''
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
    <div className="max-w-2xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Profil Bilgileri
          </CardTitle>
          <CardDescription>
            Kişisel bilgilerinizi görüntüleyin ve güncelleyin
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

          {/* Email */}
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

          {/* Phone */}
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
    </div>
  );
};
