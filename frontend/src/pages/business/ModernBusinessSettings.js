import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Settings, Clock, MapPin, Phone, Mail, Save } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const ModernBusinessSettings = ({ businessInfo, onUpdate }) => {
  const [settings, setSettings] = useState({
    name: businessInfo?.name || '',
    phone: businessInfo?.phone || '',
    email: businessInfo?.email || '',
    address: businessInfo?.address || '',
    opening_hours: businessInfo?.opening_hours || '09:00 - 23:00'
  });
  
  const [saving, setSaving] = useState(false);
  
  const handleSave = async () => {
    setSaving(true);
    // Simulate save
    setTimeout(() => {
      toast.success('Ayarlar kaydedildi');
      setSaving(false);
    }, 1000);
  };
  
  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold text-foreground mb-6">İşletme Ayarları</h1>
      
      <div className="space-y-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              Temel Bilgiler
            </CardTitle>
            <CardDescription>İşletmenizin genel bilgileri</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">İşletme Adı</Label>
              <Input
                id="name"
                value={settings.name}
                onChange={(e) => setSettings({...settings, name: e.target.value})}
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
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  E-posta
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={settings.email}
                  onChange={(e) => setSettings({...settings, email: e.target.value})}
                  placeholder="info@restaurant.com"
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="address" className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Adres
              </Label>
              <Input
                id="address"
                value={settings.address}
                onChange={(e) => setSettings({...settings, address: e.target.value})}
                placeholder="Ankara, Türkiye"
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
              <Label htmlFor="hours">Çalışma Saatleri</Label>
              <Input
                id="hours"
                value={settings.opening_hours}
                onChange={(e) => setSettings({...settings, opening_hours: e.target.value})}
                placeholder="09:00 - 23:00"
              />
            </div>
          </CardContent>
        </Card>
        
        {/* Save Button */}
        <Button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-primary hover:bg-primary-hover"
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
  );
};