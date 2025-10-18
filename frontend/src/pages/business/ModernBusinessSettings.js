import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { 
  Settings, 
  Clock, 
  MapPin, 
  Phone, 
  Mail, 
  Save, 
  Store,
  DollarSign,
  Radius,
  FileText,
  RefreshCw
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { get, patch } from '../../api/http';

export const ModernBusinessSettings = ({ businessInfo, onUpdate }) => {
  const [settings, setSettings] = useState({
    first_name: '',
    last_name: '',
    business_name: '',
    phone: '',
    address: '',
    city: '',
    district: '',
    description: '',
    opening_hours: '09:00-23:00',
    delivery_radius_km: 10,
    min_order_amount: 0,
    delivery_fee: 0
  });
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);
  
  const loadProfile = async () => {
    try {
      setLoading(true);
      const result = await get('/business/profile');
      const profile = result.data || result;
      
      setSettings({
        first_name: profile.first_name || '',
        last_name: profile.last_name || '',
        business_name: profile.business_name || '',
        phone: profile.phone || '',
        address: profile.address || '',
        city: profile.city || '',
        district: profile.district || '',
        description: profile.description || '',
        opening_hours: profile.opening_hours || '09:00-23:00',
        delivery_radius_km: profile.delivery_radius_km || 10,
        min_order_amount: profile.min_order_amount || 0,
        delivery_fee: profile.delivery_fee || 0
      });
      
      console.log('✅ Profile loaded');
    } catch (error) {
      console.error('❌ Profile loading error:', error);
      toast.error('Profil bilgileri yüklenemedi');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSave = async () => {
    try {
      setSaving(true);
      
      const result = await patch('/business/profile', settings);
      toast.success('Ayarlar başarıyla kaydedildi!');
      
      // Update parent component if callback provided
      if (onUpdate && result.data?.profile) {
        onUpdate(result.data.profile);
      }
      
      console.log('✅ Settings saved');
    } catch (error) {
      console.error('❌ Save error:', error);
      toast.error(error.response?.data?.detail || 'Ayarlar kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-4 sm:p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">İşletme Ayarları</h1>
          <p className="text-sm text-muted-foreground mt-1">
            İşletmenizin bilgilerini ve çalışma koşullarını yönetin
          </p>
        </div>
        <Button
          onClick={loadProfile}
          variant="outline"
          size="sm"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Yenile
        </Button>
      </div>
      
      <div className="space-y-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Store className="h-5 w-5 text-primary" />
              Temel Bilgiler
            </CardTitle>
            <CardDescription>İşletmenizin genel bilgileri</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Yetkili Kişi Bilgileri */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="first_name">Yetkili Adı *</Label>
                <Input
                  id="first_name"
                  value={settings.first_name}
                  onChange={(e) => setSettings({...settings, first_name: e.target.value})}
                  placeholder="Ahmet"
                />
              </div>
              
              <div>
                <Label htmlFor="last_name">Yetkili Soyadı *</Label>
                <Input
                  id="last_name"
                  value={settings.last_name}
                  onChange={(e) => setSettings({...settings, last_name: e.target.value})}
                  placeholder="Yılmaz"
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="business_name">İşletme Adı *</Label>
              <Input
                id="business_name"
                value={settings.business_name}
                onChange={(e) => setSettings({...settings, business_name: e.target.value})}
                placeholder="Restoranım"
              />
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="phone" className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Telefon
                </Label>
                <Input
                  id="phone"
                  value={settings.phone}
                  onChange={(e) => setSettings({...settings, phone: e.target.value})}
                  placeholder="+90 555 000 0000"
                />
              </div>
              
              <div>
                <Label htmlFor="city" className="flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  Şehir
                </Label>
                <Input
                  id="city"
                  value={settings.city}
                  onChange={(e) => setSettings({...settings, city: e.target.value})}
                  placeholder="Ankara"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="district">İlçe</Label>
                <Input
                  id="district"
                  value={settings.district}
                  onChange={(e) => setSettings({...settings, district: e.target.value})}
                  placeholder="Çankaya"
                />
              </div>
              
              <div>
                <Label htmlFor="address">Adres</Label>
                <Input
                  id="address"
                  value={settings.address}
                  onChange={(e) => setSettings({...settings, address: e.target.value})}
                  placeholder="Mahalle, Sokak No:1"
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="description" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Açıklama
              </Label>
              <Textarea
                id="description"
                value={settings.description}
                onChange={(e) => setSettings({...settings, description: e.target.value})}
                placeholder="İşletmeniz hakkında kısa bir açıklama..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>
        
        {/* Working Hours */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Çalışma Saatleri
            </CardTitle>
            <CardDescription>İşletmenizin açık olduğu saatler</CardDescription>
          </CardHeader>
          <CardContent>
            <div>
              <Label htmlFor="opening_hours">Çalışma Saatleri</Label>
              <Input
                id="opening_hours"
                value={settings.opening_hours}
                onChange={(e) => setSettings({...settings, opening_hours: e.target.value})}
                placeholder="09:00-23:00"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Format: 09:00-23:00 veya 09:00-14:00, 17:00-23:00
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Delivery Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Radius className="h-5 w-5 text-primary" />
              Teslimat Ayarları
            </CardTitle>
            <CardDescription>Teslimat bölgesi ve ücretleri</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="delivery_radius_km">Teslimat Yarıçapı (km)</Label>
                <Input
                  id="delivery_radius_km"
                  type="number"
                  min="1"
                  max="50"
                  value={settings.delivery_radius_km}
                  onChange={(e) => setSettings({...settings, delivery_radius_km: parseInt(e.target.value) || 10})}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Teslimat yapabileceğiniz maksimum mesafe
                </p>
              </div>
              
              <div>
                <Label htmlFor="min_order_amount" className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Minimum Sipariş (₺)
                </Label>
                <Input
                  id="min_order_amount"
                  type="number"
                  min="0"
                  step="0.5"
                  value={settings.min_order_amount}
                  onChange={(e) => setSettings({...settings, min_order_amount: parseFloat(e.target.value) || 0})}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Minimum sipariş tutarı
                </p>
              </div>
              
              <div>
                <Label htmlFor="delivery_fee">Teslimat Ücreti (₺)</Label>
                <Input
                  id="delivery_fee"
                  type="number"
                  min="0"
                  step="0.5"
                  value={settings.delivery_fee}
                  onChange={(e) => setSettings({...settings, delivery_fee: parseFloat(e.target.value) || 0})}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Sabit teslimat ücreti
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Save Button */}
        <div className="flex justify-end gap-3">
          <Button
            onClick={loadProfile}
            variant="outline"
            disabled={saving}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Sıfırla
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || !settings.business_name}
            className="bg-primary hover:bg-primary-hover min-w-[200px]"
            size="lg"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Kaydediliyor...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Ayarları Kaydet
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};