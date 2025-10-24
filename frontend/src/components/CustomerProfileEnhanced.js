import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card.jsx';
import { Button } from './ui/button.jsx';
import { Input } from './ui/input.jsx';
import { Label } from './ui/label.jsx';
import { User, Phone, Mail, Save, MapPin, Package, Settings, Bell, CreditCard, LogOut, ChevronRight } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

export const CustomerProfileEnhanced = ({ user, onLogout, onNavigateToAddresses }) => {
  const [activeSection, setActiveSection] = useState('profile'); // profile, addresses, settings
  const [profile, setProfile] = useState({
    name: '',
    surname: '',
    email: '',
    phone: ''
  });
  const [addresses, setAddresses] = useState([]);
  const [saving, setSaving] = useState(false);
  const [loadingAddresses, setLoadingAddresses] = useState(false);

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
    
    // Load addresses
    if (activeSection === 'addresses') {
      loadAddresses();
    }
  }, [user, activeSection]);

  const loadAddresses = async () => {
    try {
      setLoadingAddresses(true);
      const response = await fetch(`${API}/user/addresses`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setAddresses(data || []);
      }
    } catch (error) {
      console.error('Adres yükleme hatası:', error);
    } finally {
      setLoadingAddresses(false);
    }
  };

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

  // Menu items for profile sections
  const menuItems = [
    { id: 'profile', label: 'Profil Bilgileri', icon: User, description: 'Kişisel bilgileriniz' },
    { id: 'addresses', label: 'Adreslerim', icon: MapPin, description: 'Kayıtlı teslimat adresleri', badge: addresses.length },
    { id: 'settings', label: 'Ayarlar', icon: Settings, description: 'Hesap ayarları' }
  ];

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6">
      {/* Profile Header Card - Trendyol Go Style */}
      <Card className="mb-6 shadow-orange">
        <CardContent className="p-6">
          <div className="flex items-center space-x-4">
            <div className="h-16 w-16 rounded-full bg-gradient-orange flex items-center justify-center text-white text-2xl font-bold">
              {(profile.name?.[0] || user?.first_name?.[0] || user?.email?.[0] || 'K').toUpperCase()}
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-foreground">
                {profile.name || profile.surname ? `${profile.name} ${profile.surname}` : 'Kullanıcı'}
              </h2>
              <p className="text-sm text-muted-foreground">{profile.email || user?.email}</p>
            </div>
            <Button variant="outline" onClick={onLogout} className="hidden sm:flex items-center gap-2">
              <LogOut className="h-4 w-4" />
              Çıkış Yap
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar - Menu */}
        <div className="lg:col-span-1">
          <Card>
            <CardContent className="p-4 space-y-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeSection === item.id;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      if (item.id === 'addresses' && onNavigateToAddresses) {
                        onNavigateToAddresses();
                      } else {
                        setActiveSection(item.id);
                      }
                    }}
                    className={`w-full flex items-center justify-between p-3 rounded-lg transition-all duration-200 ${
                      isActive 
                        ? 'bg-primary text-primary-foreground shadow-orange' 
                        : 'hover:bg-secondary text-foreground'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5" />
                      <div className="text-left">
                        <p className="text-sm font-medium">{item.label}</p>
                        <p className={`text-xs ${isActive ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>
                          {item.description}
                        </p>
                      </div>
                    </div>
                    {item.badge !== undefined && (
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                        isActive ? 'bg-white text-primary' : 'bg-primary/10 text-primary'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </CardContent>
          </Card>
        </div>

        {/* Right Content Area */}
        <div className="lg:col-span-3">
          {/* Profile Section */}
          {activeSection === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5 text-primary" />
                  Profil Bilgileri
                </CardTitle>
                <CardDescription>
                  Kişisel bilgilerinizi görüntüleyin ve güncelleyin
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Name and Surname */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-sm font-medium">
                      Ad
                    </Label>
                    <Input
                      id="name"
                      value={profile.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="Adınız"
                      className="kuryecini-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="surname" className="text-sm font-medium">
                      Soyad
                    </Label>
                    <Input
                      id="surname"
                      value={profile.surname}
                      onChange={(e) => handleInputChange('surname', e.target.value)}
                      placeholder="Soyadınız"
                      className="kuryecini-input"
                    />
                  </div>
                </div>

                {/* Email */}
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                    <Mail className="h-4 w-4 text-primary" />
                    E-posta
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    value={profile.email}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="email@example.com"
                    className="kuryecini-input"
                  />
                </div>

                {/* Phone */}
                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-sm font-medium flex items-center gap-2">
                    <Phone className="h-4 w-4 text-primary" />
                    Telefon
                  </Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={profile.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    placeholder="+90 555 123 4567"
                    className="kuryecini-input"
                  />
                </div>

                {/* Save Button */}
                <Button
                  className="w-full bg-primary hover:bg-primary-hover text-primary-foreground shadow-orange"
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
          )}

          {/* Addresses Section */}
          {activeSection === 'addresses' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-primary" />
                  Kayıtlı Adreslerim
                </CardTitle>
                <CardDescription>
                  Teslimat adreslerinizi yönetin
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loadingAddresses ? (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : addresses.length === 0 ? (
                  <div className="text-center py-12">
                    <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground mb-4">Henüz kayıtlı adresiniz yok</p>
                    <Button className="bg-primary hover:bg-primary-hover">
                      <MapPin className="h-4 w-4 mr-2" />
                      Yeni Adres Ekle
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {addresses.map((address) => (
                      <div 
                        key={address.id} 
                        className="p-4 border border-border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="font-semibold text-foreground">{address.label}</span>
                              {address.is_default && (
                                <span className="restaurant-badge-orange text-xs">Varsayılan</span>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {address.full || address.description || address.district}
                            </p>
                          </div>
                          <ChevronRight className="h-5 w-5 text-muted-foreground" />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Settings Section */}
          {activeSection === 'settings' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-primary" />
                  Hesap Ayarları
                </CardTitle>
                <CardDescription>
                  Bildirimler ve tercihlerinizi yönetin
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Notification Settings */}
                <div className="border-b border-border pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Bell className="h-5 w-5 text-primary" />
                      <div>
                        <p className="font-medium text-foreground">Bildirimler</p>
                        <p className="text-sm text-muted-foreground">Sipariş güncellemelerini al</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>
                </div>

                {/* Language (Mock) */}
                <div className="border-b border-border pb-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">Dil</p>
                      <p className="text-sm text-muted-foreground">Türkçe</p>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                  </div>
                </div>

                {/* Logout Button */}
                <Button 
                  onClick={onLogout} 
                  variant="destructive" 
                  className="w-full"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  Çıkış Yap
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
