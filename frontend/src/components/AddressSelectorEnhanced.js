import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card.jsx';
import { Button } from './ui/button.jsx';
import { Input } from './ui/input.jsx';
import { Label } from './ui/label.jsx';
import { MapPin, Plus, Check, Home, Briefcase, MapPinned, Navigation } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://food-dash-87.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const AddressSelectorEnhanced = ({ selectedAddress, onAddressSelect }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  
  const [formData, setFormData] = useState({
    label: '',
    full: '',
    city: '',
    district: '',
    lat: 41.0082,
    lng: 28.9784
  });

  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    try {
      setLoading(true);
      // Use the correct endpoint
      const response = await fetch(`${API}/me/addresses`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        const addressList = Array.isArray(data) ? data : (data.addresses || []);
        setAddresses(addressList);
        
        console.log('✅ Loaded addresses:', addressList.length);
        
        // Auto-select first address if none selected
        if (addressList.length > 0 && !selectedAddress) {
          onAddressSelect(addressList[0]);
        }
      } else {
        console.error('Failed to load addresses:', response.status);
        toast.error('Adresler yüklenemedi');
      }
    } catch (error) {
      console.error('Adres yükleme hatası:', error);
      toast.error('Adres yükleme hatası');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAddress = async () => {
    try {
      if (!formData.label || !formData.full || !formData.city) {
        toast.error('Lütfen tüm alanları doldurun');
        return;
      }

      // Use new schema with backward compatibility fields
      const addressData = {
        adres_basligi: formData.label,
        alici_adsoyad: 'Müşteri', // TODO: Get from user profile
        telefon: '05551234567', // TODO: Get from user profile
        acik_adres: formData.full,
        il: formData.city,
        ilce: formData.district || 'Merkez',
        mahalle: formData.district || 'Merkez',
        lat: formData.lat,
        lng: formData.lng,
        is_default: addresses.length === 0,
        // Backward compatibility
        label: formData.label,
        full: formData.full,
        city: formData.city,
        district: formData.district
      };

      const response = await fetch(`${API}/me/addresses`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(addressData)
      });

      if (response.ok) {
        toast.success('Adres eklendi');
        setFormData({ label: '', full: '', city: '', district: '', lat: 41.0082, lng: 28.9784 });
        setShowAddForm(false);
        fetchAddresses();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Adres kaydedilemedi');
      }
    } catch (error) {
      console.error('Adres kaydetme hatası:', error);
      toast.error('Bir hata oluştu');
    }
  };

  const getAddressIcon = (label) => {
    const lower = label?.toLowerCase() || '';
    if (lower.includes('ev')) return Home;
    if (lower.includes('iş') || lower.includes('ofis')) return Briefcase;
    return MapPin;
  };

  const getLocationFromBrowser = () => {
    if (navigator.geolocation) {
      toast.loading('Konumunuz alınıyor...');
      navigator.geolocation.getCurrentPosition(
        (position) => {
          toast.dismiss();
          setFormData(prev => ({
            ...prev,
            lat: position.coords.latitude,
            lng: position.coords.longitude
          }));
          toast.success('Konum alındı!');
        },
        (error) => {
          toast.dismiss();
          toast.error('Konum alınamadı');
          console.error('Geolocation error:', error);
        }
      );
    } else {
      toast.error('Tarayıcınız konum servisleri desteklemiyor');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            Teslimat Adresi
          </CardTitle>
          <CardDescription>
            Siparişinizin teslim edileceği adresi seçin
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Address List */}
          {addresses.length > 0 ? (
            <div className="space-y-3">
              {addresses.map((address) => {
                const Icon = getAddressIcon(address.label);
                const isSelected = selectedAddress?.id === address.id;
                
                return (
                  <div
                    key={address.id}
                    onClick={() => onAddressSelect(address)}
                    className={`p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 ${
                      isSelected
                        ? 'border-primary bg-primary/5 shadow-orange'
                        : 'border-border hover:border-primary/50 hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        isSelected ? 'bg-primary text-primary-foreground' : 'bg-secondary text-foreground'
                      }`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-semibold text-foreground">{address.label}</h4>
                          {address.is_default && (
                            <span className="restaurant-badge-orange text-xs">Varsayılan</span>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {address.full || address.description || `${address.district}, ${address.city}`}
                        </p>
                      </div>

                      {isSelected && (
                        <div className="flex-shrink-0">
                          <div className="bg-primary text-primary-foreground rounded-full p-1">
                            <Check className="h-4 w-4" />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <MapPin className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground mb-4">Kayıtlı adresiniz yok</p>
            </div>
          )}

          {/* Add New Address Button */}
          {!showAddForm && (
            <Button
              onClick={() => setShowAddForm(true)}
              variant="outline"
              className="w-full border-dashed border-2 border-primary text-primary hover:bg-primary/5"
            >
              <Plus className="h-4 w-4 mr-2" />
              Yeni Adres Ekle
            </Button>
          )}

          {/* Add Address Form */}
          {showAddForm && (
            <Card className="border-2 border-primary">
              <CardContent className="p-4 space-y-4">
                <h4 className="font-semibold text-foreground flex items-center gap-2">
                  <MapPinned className="h-4 w-4 text-primary" />
                  Yeni Adres Ekle
                </h4>

                {/* Quick Label Buttons */}
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={formData.label === 'Ev' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFormData(prev => ({ ...prev, label: 'Ev' }))}
                    className={formData.label === 'Ev' ? 'bg-primary' : ''}
                  >
                    <Home className="h-4 w-4 mr-1" />
                    Ev
                  </Button>
                  <Button
                    type="button"
                    variant={formData.label === 'İş' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFormData(prev => ({ ...prev, label: 'İş' }))}
                    className={formData.label === 'İş' ? 'bg-primary' : ''}
                  >
                    <Briefcase className="h-4 w-4 mr-1" />
                    İş
                  </Button>
                  <Button
                    type="button"
                    variant={formData.label && !['Ev', 'İş'].includes(formData.label) ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setFormData(prev => ({ ...prev, label: 'Diğer' }))}
                  >
                    <MapPin className="h-4 w-4 mr-1" />
                    Diğer
                  </Button>
                </div>

                <div className="space-y-3">
                  <div>
                    <Label htmlFor="label" className="text-sm">Adres Başlığı</Label>
                    <Input
                      id="label"
                      value={formData.label}
                      onChange={(e) => setFormData(prev => ({ ...prev, label: e.target.value }))}
                      placeholder="Örn: Evim, İşyerim"
                      className="kuryecini-input"
                    />
                  </div>

                  <div>
                    <Label htmlFor="full" className="text-sm">Adres Detayı</Label>
                    <Input
                      id="full"
                      value={formData.full}
                      onChange={(e) => setFormData(prev => ({ ...prev, full: e.target.value }))}
                      placeholder="Sokak, mahalle, bina no, daire"
                      className="kuryecini-input"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label htmlFor="city" className="text-sm">Şehir</Label>
                      <Input
                        id="city"
                        value={formData.city}
                        onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                        placeholder="İstanbul"
                        className="kuryecini-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="district" className="text-sm">İlçe</Label>
                      <Input
                        id="district"
                        value={formData.district}
                        onChange={(e) => setFormData(prev => ({ ...prev, district: e.target.value }))}
                        placeholder="Kadıköy"
                        className="kuryecini-input"
                      />
                    </div>
                  </div>

                  {/* GPS Location */}
                  <Button
                    type="button"
                    onClick={getLocationFromBrowser}
                    variant="outline"
                    className="w-full"
                    size="sm"
                  >
                    <Navigation className="h-4 w-4 mr-2" />
                    GPS Konumumu Kullan
                  </Button>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleSaveAddress}
                    className="flex-1 bg-primary hover:bg-primary-hover"
                  >
                    Adresi Kaydet
                  </Button>
                  <Button
                    onClick={() => {
                      setShowAddForm(false);
                      setFormData({ label: '', full: '', city: '', district: '', lat: 41.0082, lng: 28.9784 });
                    }}
                    variant="outline"
                  >
                    İptal
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
