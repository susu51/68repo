import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from './ui/card.jsx';
import { Button } from './ui/button.jsx';
import { Input } from './ui/input.jsx';
import { toast } from 'react-hot-toast';
import api from '../api/http';

const AdminSettings = () => {
  const [activeTab, setActiveTab] = useState('maintenance');
  const [settings, setSettings] = useState({
    maintenance_mode: false,
    maintenance_message: '',
    maintenance_eta: '',
    contact_email: '',
    contact_phone: '',
    theme_color: '#FF6B35'
  });
  const [backendLogs, setBackendLogs] = useState([]);
  const [frontendLogs, setFrontendLogs] = useState([]);
  const [logFilter, setLogFilter] = useState('all');
  const [testResults, setTestResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSettings();
    captureFrontendLogs();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/admin/settings/system');
      setSettings(response.data);
    } catch (error) {
      console.error('Error loading settings:', error);
      toast.error('Ayarlar yüklenemedi');
    }
  };

  const captureFrontendLogs = () => {
    const logs = [];
    const originalConsole = {
      log: console.log,
      error: console.error,
      warn: console.warn,
      info: console.info
    };

    // Intercept console methods
    console.log = (...args) => {
      logs.push({ level: 'log', message: args.join(' '), timestamp: new Date().toISOString() });
      originalConsole.log(...args);
    };
    console.error = (...args) => {
      logs.push({ level: 'error', message: args.join(' '), timestamp: new Date().toISOString() });
      originalConsole.error(...args);
    };
    console.warn = (...args) => {
      logs.push({ level: 'warn', message: args.join(' '), timestamp: new Date().toISOString() });
      originalConsole.warn(...args);
    };

    setFrontendLogs(logs);
    
    // Update logs every 2 seconds
    const interval = setInterval(() => {
      setFrontendLogs([...logs].slice(-100)); // Keep last 100 logs
    }, 2000);

    return () => clearInterval(interval);
  };

  const toggleMaintenanceMode = async () => {
    try {
      setLoading(true);
      const response = await api.post('/admin/settings/maintenance-mode', {
        enabled: !settings.maintenance_mode,
        message: settings.maintenance_message,
        eta: settings.maintenance_eta
      });
      
      setSettings(prev => ({ ...prev, maintenance_mode: !prev.maintenance_mode }));
      toast.success(response.data.message);
    } catch (error) {
      console.error('Error toggling maintenance mode:', error);
      toast.error('Bakım modu değiştirilemedi');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setLoading(true);
      await api.post('/admin/settings/system', settings);
      toast.success('Ayarlar kaydedildi');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Ayarlar kaydedilemedi');
    } finally {
      setLoading(false);
    }
  };

  const loadBackendLogs = async () => {
    try {
      const response = await api.get(`/admin/logs/backend?lines=100&level=${logFilter}`);
      setBackendLogs(response.data.logs);
      toast.success(`${response.data.total_lines} log yüklendi`);
    } catch (error) {
      console.error('Error loading backend logs:', error);
      toast.error('Backend logları yüklenemedi');
    }
  };

  const runButtonTests = async (buttonType = 'all') => {
    try {
      setLoading(true);
      const response = await api.post('/admin/test-buttons', { button_type: buttonType });
      setTestResults(response.data.test_results);
      
      const status = response.data.overall_status;
      if (status === 'success') {
        toast.success('Tüm testler başarılı!');
      } else {
        toast.warning('Bazı testler başarısız');
      }
    } catch (error) {
      console.error('Error running tests:', error);
      toast.error('Testler çalıştırılamadı');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">⚙️ Sistem Ayarları</h1>
          <p className="text-gray-600 mt-2">Bakım modu, loglar, testler ve görüntüleme ayarları</p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-2 mb-6 border-b border-gray-200">
          {[
            { id: 'maintenance', label: '🔧 Bakım Modu', icon: '🔧' },
            { id: 'logs', label: '📋 Console & Loglar', icon: '📋' },
            { id: 'tests', label: '🧪 Buton Testleri', icon: '🧪' },
            { id: 'display', label: '🎨 Görüntüleme', icon: '🎨' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-orange-500 text-orange-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Maintenance Mode Tab */}
        {activeTab === 'maintenance' && (
          <div className="space-y-6">
            <Card>
              <CardHeader className="bg-orange-50 border-b">
                <h2 className="text-xl font-bold text-gray-800">🔧 Bakım Modu Yönetimi</h2>
              </CardHeader>
              <CardContent className="p-6">
                {/* Toggle */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg mb-6">
                  <div>
                    <h3 className="font-semibold text-lg">Bakım Modu</h3>
                    <p className="text-sm text-gray-600">
                      {settings.maintenance_mode 
                        ? '🔴 Site bakımda - Tüm kullanıcılar bakım sayfasını görüyor'
                        : '🟢 Site aktif - Normal çalışıyor'}
                    </p>
                  </div>
                  <button
                    onClick={toggleMaintenanceMode}
                    disabled={loading}
                    className={`relative inline-flex h-12 w-24 items-center rounded-full transition-colors ${
                      settings.maintenance_mode ? 'bg-red-500' : 'bg-green-500'
                    } ${loading ? 'opacity-50' : ''}`}
                  >
                    <span
                      className={`inline-block h-10 w-10 transform rounded-full bg-white transition-transform ${
                        settings.maintenance_mode ? 'translate-x-12' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Settings */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Bakım Mesajı
                    </label>
                    <Input
                      value={settings.maintenance_message}
                      onChange={(e) => setSettings(prev => ({ ...prev, maintenance_message: e.target.value }))}
                      placeholder="Sistemimiz bakımda. Kısa süre içinde tekrar hizmetinizdeyiz!"
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tahmini Açılış Süresi
                    </label>
                    <Input
                      type="datetime-local"
                      value={settings.maintenance_eta || ''}
                      onChange={(e) => setSettings(prev => ({ ...prev, maintenance_eta: e.target.value }))}
                      className="w-full"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        İletişim Email
                      </label>
                      <Input
                        type="email"
                        value={settings.contact_email}
                        onChange={(e) => setSettings(prev => ({ ...prev, contact_email: e.target.value }))}
                        placeholder="destek@kuryecini.com"
                        className="w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        İletişim Telefon
                      </label>
                      <Input
                        value={settings.contact_phone}
                        onChange={(e) => setSettings(prev => ({ ...prev, contact_phone: e.target.value }))}
                        placeholder="+90 555 123 45 67"
                        className="w-full"
                      />
                    </div>
                  </div>

                  <Button 
                    onClick={saveSettings} 
                    disabled={loading}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white"
                  >
                    {loading ? 'Kaydediliyor...' : '💾 Ayarları Kaydet'}
                  </Button>
                </div>

                {/* Preview */}
                {settings.maintenance_mode && (
                  <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <h4 className="font-semibold text-yellow-800 mb-2">⚠️ Bakım Modu Aktif</h4>
                    <p className="text-sm text-yellow-700">
                      Tüm kullanıcılar (müşteriler, işletmeler, kuryeler) şu anda bakım sayfasını görüyor.
                      Sadece admin paneli erişilebilir durumda.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="space-y-6">
            <Card>
              <CardHeader className="bg-blue-50 border-b">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold text-gray-800">📋 Console & Log Viewer</h2>
                  <div className="flex space-x-2">
                    <select
                      value={logFilter}
                      onChange={(e) => setLogFilter(e.target.value)}
                      className="px-3 py-1 border rounded"
                    >
                      <option value="all">Tümü</option>
                      <option value="error">Sadece Hatalar</option>
                      <option value="warn">Sadece Uyarılar</option>
                      <option value="info">Sadece Bilgi</option>
                    </select>
                    <Button onClick={loadBackendLogs} size="sm">
                      🔄 Backend Logları Yükle
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                {/* Frontend Logs */}
                <div className="mb-6">
                  <h3 className="font-semibold text-lg mb-3">🌐 Frontend Console Logs</h3>
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                    {frontendLogs.length === 0 ? (
                      <p className="text-gray-500">Henüz log yok...</p>
                    ) : (
                      frontendLogs.slice(-50).map((log, index) => (
                        <div key={index} className={`mb-1 ${
                          log.level === 'error' ? 'text-red-400' :
                          log.level === 'warn' ? 'text-yellow-400' :
                          'text-green-400'
                        }`}>
                          <span className="text-gray-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span> 
                          <span className="ml-2">{log.level.toUpperCase()}:</span> 
                          <span className="ml-2">{log.message}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Backend Logs */}
                <div>
                  <h3 className="font-semibold text-lg mb-3">⚙️ Backend Logs</h3>
                  <div className="bg-gray-900 text-cyan-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                    {backendLogs.length === 0 ? (
                      <p className="text-gray-500">'Backend Logları Yükle' butonuna tıklayın...</p>
                    ) : (
                      backendLogs.map((log, index) => (
                        <div key={index} className="mb-1 text-cyan-300">
                          {log}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tests Tab */}
        {activeTab === 'tests' && (
          <div className="space-y-6">
            <Card>
              <CardHeader className="bg-green-50 border-b">
                <h2 className="text-xl font-bold text-gray-800">🧪 Sistem Buton Testleri</h2>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <Button 
                    onClick={() => runButtonTests('all')}
                    className="bg-blue-500 hover:bg-blue-600 text-white"
                    disabled={loading}
                  >
                    🔍 Tüm Testleri Çalıştır
                  </Button>
                  <Button 
                    onClick={() => runButtonTests('api')}
                    className="bg-purple-500 hover:bg-purple-600 text-white"
                    disabled={loading}
                  >
                    🌐 API Testleri
                  </Button>
                  <Button 
                    onClick={() => runButtonTests('auth')}
                    className="bg-indigo-500 hover:bg-indigo-600 text-white"
                    disabled={loading}
                  >
                    🔐 Auth Testleri
                  </Button>
                  <Button 
                    onClick={() => runButtonTests('orders')}
                    className="bg-orange-500 hover:bg-orange-600 text-white"
                    disabled={loading}
                  >
                    📦 Sipariş Testleri
                  </Button>
                </div>

                {/* Test Results */}
                {testResults.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-lg mb-3">Test Sonuçları:</h3>
                    {testResults.map((result, index) => (
                      <div 
                        key={index}
                        className={`p-4 rounded-lg border-l-4 ${
                          result.status === 'success' ? 'bg-green-50 border-green-500' :
                          result.status === 'warning' ? 'bg-yellow-50 border-yellow-500' :
                          'bg-red-50 border-red-500'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold">{result.test}</h4>
                            <p className="text-sm text-gray-600">{result.message}</p>
                          </div>
                          <span className="text-2xl">
                            {result.status === 'success' ? '✅' : 
                             result.status === 'warning' ? '⚠️' : '❌'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Display Settings Tab */}
        {activeTab === 'display' && (
          <div className="space-y-6">
            <Card>
              <CardHeader className="bg-purple-50 border-b">
                <h2 className="text-xl font-bold text-gray-800">🎨 Görüntüleme Ayarları</h2>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tema Rengi
                    </label>
                    <div className="flex items-center space-x-4">
                      <Input
                        type="color"
                        value={settings.theme_color}
                        onChange={(e) => setSettings(prev => ({ ...prev, theme_color: e.target.value }))}
                        className="w-20 h-12"
                      />
                      <Input
                        value={settings.theme_color}
                        onChange={(e) => setSettings(prev => ({ ...prev, theme_color: e.target.value }))}
                        placeholder="#FF6B35"
                        className="flex-1"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Logo URL
                    </label>
                    <Input
                      value={settings.logo_url || ''}
                      onChange={(e) => setSettings(prev => ({ ...prev, logo_url: e.target.value }))}
                      placeholder="/logo.png"
                      className="w-full"
                    />
                  </div>

                  <Button 
                    onClick={saveSettings} 
                    disabled={loading}
                    className="w-full bg-purple-500 hover:bg-purple-600 text-white"
                  >
                    {loading ? 'Kaydediliyor...' : '💾 Görünüm Ayarlarını Kaydet'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminSettings;
