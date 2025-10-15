import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Home, Briefcase, MapPin, Navigation, Loader2, Map } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://express-track-2.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const SimpleAddressFormWithMap = ({ address, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    adres_basligi: address?.adres_basligi || address?.label || '',
    alici_adsoyad: address?.alici_adsoyad || '',
    telefon: address?.telefon || '',
    acik_adres: address?.acik_adres || address?.full || '',
    il: address?.il || address?.city || '',
    ilce: address?.ilce || address?.district || '',
    mahalle: address?.mahalle || '',
    posta_kodu: address?.posta_kodu || '',
    kat_daire: address?.kat_daire || '',
    lat: address?.lat || 39.9334, // Turkey center default
    lng: address?.lng || 32.8597,
    is_default: address?.is_default || false
  });

  const [reverseGeocoding, setReverseGeocoding] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleReverseGeocode = async () => {
    if (!formData.lat || !formData.lng) {
      toast.error('Önce GPS konumunuzu alın');
      return;
    }

    setReverseGeocoding(true);
    try {
      const response = await fetch(`${API}/geocode/reverse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: formData.lat, lng: formData.lng })
      });

      if (response.ok) {
        const data = await response.json();
        setFormData(prev => ({
          ...prev,
          il: data.il || prev.il,
          ilce: data.ilce || prev.ilce,
          mahalle: data.mahalle || prev.mahalle,
          posta_kodu: data.posta_kodu || prev.posta_kodu,
          acik_adres: data.formatted_address || prev.acik_adres
        }));
        toast.success('Konum bilgileri güncellendi');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Konum bilgisi alınamadı');
      }
    } catch (error) {
      console.error('Reverse geocoding error:', error);
      toast.error('Konum bilgisi alınırken hata oluştu');
    } finally {
      setReverseGeocoding(false);
    }
  };

  const getUserLocation = () => {
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
          toast.success('GPS konumu alındı!');
          
          // Auto reverse geocode
          setTimeout(() => {
            handleReverseGeocode();
          }, 500);
        },
        (error) => {
          toast.dismiss();
          toast.error('Konum alınamadı. Lütfen manuel girin.');
          console.error('Geolocation error:', error);
        }
      );
    } else {
      toast.error('Tarayıcınız konum servislerini desteklemiyor');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!formData.adres_basligi || !formData.alici_adsoyad || !formData.telefon) {
      toast.error('Adres başlığı, alıcı adı ve telefon zorunludur');
      return;
    }

    if (!formData.il || !formData.ilce || !formData.mahalle) {
      toast.error('İl, ilçe ve mahalle zorunludur');
      return;
    }

    if (!formData.acik_adres) {
      toast.error('Açık adres zorunludur');
      return;
    }

    try {
      setSaving(true);
      await onSave(formData);
    } catch (error) {
      console.error('Save error:', error);
      toast.error('Adres kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // OpenStreetMap static image URL
  const getStaticMapUrl = () => {
    const { lat, lng } = formData;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${lng-0.01},${lat-0.01},${lng+0.01},${lat+0.01}&layer=mapnik&marker=${lat},${lng}`;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            {address ? 'Adresi Düzenle' : 'Yeni Adres Ekle'}
          </CardTitle>
          <CardDescription>
            GPS konumunuzu alın veya manuel olarak adres bilgilerini girin
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Static Map Preview */}
          <div className="mb-6 rounded-lg overflow-hidden border-2 border-border bg-gray-100 dark:bg-gray-800" style={{ height: '300px' }}>
            {formData.lat && formData.lng ? (
              <iframe
                width="100%"
                height="100%"
                frameBorder="0"
                scrolling="no"
                marginHeight="0"
                marginWidth="0"
                src={getStaticMapUrl()}
                title="Adres Haritası"
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Map className="h-16 w-16 mb-4" />
                <p>GPS konumunuzu alın veya manuel koordinat girin</p>
              </div>
            )}
          </div>

          {/* GPS Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            <Button
              type="button"
              onClick={getUserLocation}
              variant="outline"
              className="w-full"
              disabled={reverseGeocoding}
            >
              <Navigation className="h-4 w-4 mr-2" />
              GPS Konumumu Al
            </Button>
            
            <Button
              type="button"
              onClick={handleReverseGeocode}
              variant="outline"
              className="w-full"
              disabled={reverseGeocoding || !formData.lat || !formData.lng}
            >
              {reverseGeocoding ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <MapPin className="h-4 w-4 mr-2" />
              )}
              Adres Bilgilerini Getir
            </Button>
          </div>

          {/* Coordinates Display */}
          <div className="mb-6 p-3 bg-secondary rounded-lg">
            <p className="text-xs text-muted-foreground mb-1">Koordinatlar</p>
            <p className="text-sm font-mono">
              {formData.lat.toFixed(6)}, {formData.lng.toFixed(6)}
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Quick Label Buttons */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Adres Başlığı *</Label>
              <div className="flex gap-2 mb-2">
                <Button
                  type="button"
                  variant={formData.adres_basligi === 'Ev' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleInputChange('adres_basligi', 'Ev')}
                  className={formData.adres_basligi === 'Ev' ? 'bg-primary' : ''}
                >
                  <Home className="h-4 w-4 mr-1" />
                  Ev
                </Button>
                <Button
                  type="button"
                  variant={formData.adres_basligi === 'İş' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleInputChange('adres_basligi', 'İş')}
                  className={formData.adres_basligi === 'İş' ? 'bg-primary' : ''}
                >
                  <Briefcase className="h-4 w-4 mr-1" />
                  İş
                </Button>
                <Button
                  type="button"
                  variant={formData.adres_basligi && !['Ev', 'İş'].includes(formData.adres_basligi) ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleInputChange('adres_basligi', 'Diğer')}
                >
                  Diğer
                </Button>
              </div>
              <Input
                value={formData.adres_basligi}
                onChange={(e) => handleInputChange('adres_basligi', e.target.value)}
                placeholder="Örn: Evim, İşyerim"
                required
              />
            </div>

            {/* Recipient Info */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="alici_adsoyad">Alıcı Ad Soyad *</Label>
                <Input
                  id="alici_adsoyad"
                  value={formData.alici_adsoyad}
                  onChange={(e) => handleInputChange('alici_adsoyad', e.target.value)}
                  placeholder="Suayip Başer"
                  required
                />
              </div>
              <div>
                <Label htmlFor="telefon">Telefon *</Label>
                <Input
                  id="telefon"
                  value={formData.telefon}
                  onChange={(e) => handleInputChange('telefon', e.target.value)}
                  placeholder="+90 555 123 4567"
                  required
                />
              </div>
            </div>

            {/* Address Details */}
            <div>
              <Label htmlFor="acik_adres">Açık Adres *</Label>
              <Input
                id="acik_adres"
                value={formData.acik_adres}
                onChange={(e) => handleInputChange('acik_adres', e.target.value)}
                placeholder="Mahalle, Sokak, No"
                required
              />
            </div>

            {/* City/District/Neighborhood */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="il">İl *</Label>
                <Input
                  id="il"
                  value={formData.il}
                  onChange={(e) => handleInputChange('il', e.target.value)}
                  placeholder="Niğde"
                  required
                />
              </div>
              <div>
                <Label htmlFor="ilce">İlçe *</Label>
                <Input
                  id="ilce"
                  value={formData.ilce}
                  onChange={(e) => handleInputChange('ilce', e.target.value)}
                  placeholder="Merkez"
                  required
                />
              </div>
              <div>
                <Label htmlFor="mahalle">Mahalle *</Label>
                <Input
                  id="mahalle"
                  value={formData.mahalle}
                  onChange={(e) => handleInputChange('mahalle', e.target.value)}
                  placeholder="Fertek"
                  required
                />
              </div>
            </div>

            {/* Optional Fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="posta_kodu">Posta Kodu</Label>
                <Input
                  id="posta_kodu"
                  value={formData.posta_kodu || ''}
                  onChange={(e) => handleInputChange('posta_kodu', e.target.value)}
                  placeholder="51000"
                />
              </div>
              <div>
                <Label htmlFor="kat_daire">Kat / Daire</Label>
                <Input
                  id="kat_daire"
                  value={formData.kat_daire || ''}
                  onChange={(e) => handleInputChange('kat_daire', e.target.value)}
                  placeholder="Kat 5, Daire 12"
                />
              </div>
            </div>

            {/* Default Checkbox */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_default"
                checked={formData.is_default}
                onChange={(e) => handleInputChange('is_default', e.target.checked)}
                className="rounded border-gray-300 text-primary focus:ring-primary"
              />
              <Label htmlFor="is_default" className="cursor-pointer">
                Varsayılan adres olarak ayarla
              </Label>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                type="submit"
                className="flex-1 bg-primary hover:bg-primary-hover"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Kaydediliyor...
                  </>
                ) : (
                  'Adresi Kaydet'
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                disabled={saving}
              >
                İptal
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
