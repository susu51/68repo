import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://food-dash-87.preview.emergentagent.com/api';

export const PlatformSettings = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/admin/settings`, {
        withCredentials: true
      });
      setSettings(response.data);
    } catch (error) {
      console.error('Settings fetch error:', error);
      toast.error('Ayarlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await axios.patch(`${API_BASE}/admin/settings`, settings, {
        withCredentials: true
      });
      toast.success('Ayarlar başarıyla kaydedildi');
    } catch (error) {
      console.error('Settings save error:', error);
      toast.error('Ayarlar kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Ayarlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  if (!settings) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Platform Ayarları</h2>
          <p className="text-gray-600 mt-1">Platform genelindeki ayarları yönetin</p>
        </div>
        <Button 
          onClick={handleSave}
          disabled={saving}
          className="bg-orange-600 hover:bg-orange-700"
        >
          {saving ? '💾 Kaydediliyor...' : '💾 Kaydet'}
        </Button>
      </div>

      {/* Platform Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🏢 Platform Ayarları
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Uygulama Adı
              </label>
              <input
                type="text"
                value={settings.platform.app_name}
                onChange={(e) => updateSetting('platform', 'app_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Versiyon
              </label>
              <input
                type="text"
                value={settings.platform.app_version}
                onChange={(e) => updateSetting('platform', 'app_version', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Platform Komisyon Oranı (%)
              </label>
              <input
                type="number"
                value={settings.platform.platform_commission_rate}
                onChange={(e) => updateSetting('platform', 'platform_commission_rate', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Kurye Komisyon Oranı (%)
              </label>
              <input
                type="number"
                value={settings.platform.courier_commission_rate}
                onChange={(e) => updateSetting('platform', 'courier_commission_rate', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Varsayılan Teslimat Ücreti (₺)
              </label>
              <input
                type="number"
                value={settings.platform.default_delivery_fee}
                onChange={(e) => updateSetting('platform', 'default_delivery_fee', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maksimum Teslimat Yarıçapı (km)
              </label>
              <input
                type="number"
                value={settings.platform.max_delivery_radius_km}
                onChange={(e) => updateSetting('platform', 'max_delivery_radius_km', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.platform.maintenance_mode}
                onChange={(e) => updateSetting('platform', 'maintenance_mode', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Bakım Modu</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.platform.new_registrations_enabled}
                onChange={(e) => updateSetting('platform', 'new_registrations_enabled', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Yeni Kayıtlar Aktif</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Payment Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            💳 Ödeme Ayarları
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Sipariş Tutarı (₺)
            </label>
            <input
              type="number"
              value={settings.payment.minimum_order_amount}
              onChange={(e) => updateSetting('payment', 'minimum_order_amount', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.payment.cash_on_delivery}
                onChange={(e) => updateSetting('payment', 'cash_on_delivery', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Kapıda Ödeme</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.payment.online_payment}
                onChange={(e) => updateSetting('payment', 'online_payment', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Online Ödeme</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.payment.pos_payment}
                onChange={(e) => updateSetting('payment', 'pos_payment', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">POS ile Ödeme</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Business Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🏪 İşletme Ayarları
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.business.auto_approve_businesses}
                onChange={(e) => updateSetting('business', 'auto_approve_businesses', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">İşletmeleri Otomatik Onayla</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.business.require_business_documents}
                onChange={(e) => updateSetting('business', 'require_business_documents', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">İşletme Belgeleri Zorunlu</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.business.business_verification_required}
                onChange={(e) => updateSetting('business', 'business_verification_required', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">İşletme Doğrulaması Gerekli</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Courier Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🏍️ Kurye Ayarları
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.courier.auto_approve_couriers}
                onChange={(e) => updateSetting('courier', 'auto_approve_couriers', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Kuryeleri Otomatik Onayla</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.courier.require_vehicle_documents}
                onChange={(e) => updateSetting('courier', 'require_vehicle_documents', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Araç Belgeleri Zorunlu</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.courier.courier_background_check}
                onChange={(e) => updateSetting('courier', 'courier_background_check', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Kurye Geçmiş Kontrolü</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔔 Bildirim Ayarları
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notifications.email_enabled}
                onChange={(e) => updateSetting('notifications', 'email_enabled', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Email Bildirimleri</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notifications.sms_enabled}
                onChange={(e) => updateSetting('notifications', 'sms_enabled', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">SMS Bildirimleri</span>
            </label>

            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notifications.push_enabled}
                onChange={(e) => updateSetting('notifications', 'push_enabled', e.target.checked)}
                className="w-5 h-5 text-orange-600 rounded focus:ring-orange-500"
              />
              <span className="text-sm font-medium text-gray-700">Push Bildirimleri</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* Save Button (Bottom) */}
      <div className="flex justify-end">
        <Button 
          onClick={handleSave}
          disabled={saving}
          className="bg-orange-600 hover:bg-orange-700 px-8"
        >
          {saving ? '💾 Kaydediliyor...' : '💾 Tüm Ayarları Kaydet'}
        </Button>
      </div>
    </div>
  );
};

export default PlatformSettings;
