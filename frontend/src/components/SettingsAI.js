/**
 * AI Settings Page Component
 * Admin → Ayarlar → Entegrasyonlar → AI Ayarları
 * 
 * Allows admins to:
 * - Configure OpenAI API key (optional, overrides Emergent LLM Key)
 * - Toggle Emergent LLM Key usage
 * - Configure redaction rules for PII
 * - Set default time windows and rate limits
 * - Test OpenAI connection
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import toast from 'react-hot-toast';
import { getAISettings, putAISettings, testAISettings, selftestAI } from '../api/aiSettings';

export const SettingsAI = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null); // {ok, provider, model, latency_ms}
  
  const [settings, setSettings] = useState({
    openai_api_key: '',
    use_emergent_key: true,
    default_model: 'gpt-4o-mini',
    default_time_window_minutes: 60,
    rate_limit_per_min: 6,
    redact_rules: []
  });
  
  const [openaiKeyConfigured, setOpenaiKeyConfigured] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await getAISettings();
      
      setSettings({
        openai_api_key: '', // Never expose the actual key
        use_emergent_key: data.use_emergent_key,
        default_model: data.default_model,
        default_time_window_minutes: data.default_time_window_minutes,
        rate_limit_per_min: data.rate_limit_per_min,
        redact_rules: data.redact_rules || []
      });
      
      setOpenaiKeyConfigured(data.openai_api_key_configured);
    } catch (error) {
      console.error('Failed to load AI settings:', error);
      // Keep default values if loading fails
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Prepare update payload (only send changed fields)
      const updatePayload = {
        use_emergent_key: settings.use_emergent_key,
        default_time_window_minutes: settings.default_time_window_minutes,
        rate_limit_per_min: settings.rate_limit_per_min,
        redact_rules: settings.redact_rules
      };
      
      // Only include openai_api_key if user entered something
      if (settings.openai_api_key && settings.openai_api_key.trim()) {
        updatePayload.openai_api_key = settings.openai_api_key.trim();
      }
      
      const updatedSettings = await putAISettings(updatePayload);
      
      toast.success('✅ Ayarlar kaydedildi.', {
        duration: 3000,
        icon: '✅'
      });
      
      // Reload to get updated values
      await loadSettings();
      
      // Clear the password field
      setSettings(prev => ({ ...prev, openai_api_key: '' }));
      
    } catch (error) {
      console.error('Failed to save AI settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      
      const result = await testAISettings();
      
      if (result.success) {
        toast.success(`✅ Bağlantı başarılı! Model: ${result.model}, Kaynak: ${result.key_source === 'emergent' ? 'Emergent LLM Key' : 'Özel Anahtar'}`, {
          duration: 5000,
          icon: '✅'
        });
      } else {
        toast.error('Bağlantı testi başarısız.');
      }
      
    } catch (error) {
      console.error('Failed to test AI settings:', error);
    } finally {
      setTesting(false);
    }
  };

  const handleRedactRuleToggle = (ruleType) => {
    setSettings(prev => ({
      ...prev,
      redact_rules: prev.redact_rules.map(rule =>
        rule.type === ruleType
          ? { ...rule, enabled: !rule.enabled }
          : rule
      )
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Ayarlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <span>✨</span>
            <span>AI Ayarları</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* OpenAI API Key */}
          <div>
            <label htmlFor="openai-key" className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI Anahtarı
              {openaiKeyConfigured && (
                <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                  ✓ Yapılandırılmış
                </span>
              )}
            </label>
            <input
              id="openai-key"
              type="password"
              value={settings.openai_api_key}
              onChange={(e) => setSettings({ ...settings, openai_api_key: e.target.value })}
              placeholder={openaiKeyConfigured ? "••••••••••••••••••••" : "sk-..."}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              data-testid="ai-settings-openai-key"
            />
            <p className="text-xs text-gray-500 mt-1">
              Boş bırakırsanız Emergent LLM Key kullanılır. Özel anahtar girerseniz override eder.
            </p>
          </div>

          {/* Use Emergent Key Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Emergent LLM Key Kullan
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Varsayılan olarak açık. Universal key ile OpenAI/Anthropic/Google modellerine erişim sağlar.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSettings({ ...settings, use_emergent_key: !settings.use_emergent_key })}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.use_emergent_key ? 'bg-blue-600' : 'bg-gray-200'
              }`}
              data-testid="ai-settings-emergent-toggle"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.use_emergent_key ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Default Time Window */}
          <div>
            <label htmlFor="time-window" className="block text-sm font-medium text-gray-700 mb-2">
              Varsayılan Zaman Aralığı (dakika)
            </label>
            <input
              id="time-window"
              type="number"
              min="1"
              max="1440"
              value={settings.default_time_window_minutes}
              onChange={(e) => setSettings({ ...settings, default_time_window_minutes: parseInt(e.target.value) || 60 })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              data-testid="ai-settings-time-window"
            />
            <p className="text-xs text-gray-500 mt-1">
              AI sorgularında varsayılan zaman penceresi (15 dk, 1 saat, 24 saat)
            </p>
          </div>

          {/* Rate Limit */}
          <div>
            <label htmlFor="rate-limit" className="block text-sm font-medium text-gray-700 mb-2">
              Dakikada AI İstek Limiti
            </label>
            <input
              id="rate-limit"
              type="number"
              min="1"
              max="60"
              value={settings.rate_limit_per_min}
              onChange={(e) => setSettings({ ...settings, rate_limit_per_min: parseInt(e.target.value) || 6 })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              data-testid="ai-settings-rate-limit"
            />
            <p className="text-xs text-gray-500 mt-1">
              Her admin kullanıcısının dakikada yapabileceği AI sorgu sayısı
            </p>
          </div>

          {/* Redaction Rules */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Redaksiyon Kuralları (PII)
            </label>
            <div className="space-y-2">
              {settings.redact_rules.map((rule) => (
                <div key={rule.type} className="flex items-center">
                  <input
                    type="checkbox"
                    id={`redact-${rule.type}`}
                    checked={rule.enabled}
                    onChange={() => handleRedactRuleToggle(rule.type)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    data-testid={`ai-settings-redact-${rule.type}`}
                  />
                  <label
                    htmlFor={`redact-${rule.type}`}
                    className="ml-2 block text-sm text-gray-700 capitalize"
                  >
                    {rule.type === 'phone' && '📞 Telefon'}
                    {rule.type === 'email' && '📧 E-posta'}
                    {rule.type === 'iban' && '🏦 IBAN'}
                    {rule.type === 'jwt' && '🔑 JWT/Authorization'}
                    {rule.type === 'card' && '💳 Kart Numarası'}
                    {rule.type === 'address' && '📍 Adres'}
                  </label>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Seçili kurallar, AI'ya gönderilen loglardan hassas bilgileri otomatik maskeleyecek.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4 border-t">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              data-testid="ai-settings-save"
            >
              {saving ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Kaydediliyor...
                </span>
              ) : (
                '💾 Kaydet'
              )}
            </button>
            
            <button
              onClick={handleTest}
              disabled={testing}
              className="flex-1 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              data-testid="ai-settings-test"
            >
              {testing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Test ediliyor...
                </span>
              ) : (
                '🔌 Bağlantıyı Test Et'
              )}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Feature Flag Info */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">ℹ️</span>
            <div className="flex-1">
              <h4 className="font-medium text-blue-900 mb-1">Panel-Aware AI Assistant</h4>
              <p className="text-sm text-blue-700">
                Bu ayarlar, Admin panelindeki AI asistanı için kullanılır. AI asistanı, seçilen panele (customer/business/courier) 
                göre bağlamsal sorular yanıtlar ve PII redaction ile güvenlik sağlar.
              </p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                <span className="bg-blue-200 text-blue-800 px-2 py-1 rounded">
                  Emergent LLM Key: OpenAI/Anthropic/Google
                </span>
                <span className="bg-green-200 text-green-800 px-2 py-1 rounded">
                  Varsayılan Model: gpt-4o-mini
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsAI;
