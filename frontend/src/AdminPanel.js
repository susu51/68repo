import React, { useState, useEffect } from 'react';

const AdminPanel = ({ user, onLogout }) => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [pendingBusinesses, setPendingBusinesses] = useState([]);
  const [pendingCouriers, setPendingCouriers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Business approval handler
  const handleBusinessApprove = async (businessId) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('kuryecini_access_token');
      
      const response = await fetch(`/api/admin/users/${businessId}/approve`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        alert('İşletme başarıyla onaylandı!');
        // Refresh data in real implementation
      } else {
        alert('Onaylama başarısız!');
      }
    } catch (error) {
      console.error('Approval error:', error);
      alert('Hata oluştu!');
    } finally {
      setLoading(false);
    }
  };
  
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Admin Panel</h2>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">🏢 Admin Panel</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Hoş geldin, {user.first_name}</span>
              <button
                onClick={onLogout}
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
              >
                Çıkış Yap
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-8">
            {[
              { id: 'dashboard', label: '📊 Dashboard' },
              { id: 'orders', label: '📦 Siparişler' },
              { id: 'businesses', label: '🏪 İşletmeler' },
              { id: 'menus', label: '📋 Menü Yönetimi' },
              { id: 'couriers', label: '🚴 Kuryeler' },
              { id: 'promotions', label: '🎯 Promosyonlar' },
              { id: 'settings', label: '⚙️ Ayarlar' },
              { id: 'reports', label: '📈 Raporlar' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setCurrentView(tab.id)}
                className={`py-4 px-2 border-b-2 font-medium text-sm ${
                  currentView === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto py-6 px-6">
        {currentView === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Toplam Siparişler</h3>
                <p className="text-3xl font-bold text-blue-600">1,234</p>
                <p className="text-sm text-green-600 mt-1">↗️ +12% bu hafta</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Aktif İşletmeler</h3>
                <p className="text-3xl font-bold text-green-600">89</p>
                <p className="text-sm text-blue-600 mt-1">📈 +5 yeni onay</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Aktif Kuryeler</h3>
                <p className="text-3xl font-bold text-yellow-600">156</p>
                <p className="text-sm text-gray-600 mt-1">🚴 Çevrimiçi: 23</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Günlük Gelir</h3>
                <p className="text-3xl font-bold text-purple-600">₺15,430</p>
                <p className="text-sm text-green-600 mt-1">💰 +8% dün</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Son Siparişler</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b">
                    <div>
                      <p className="font-medium">#ORD-001</p>
                      <p className="text-sm text-gray-600">Pizza Palace - ₺125</p>
                    </div>
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                      Teslim Edildi
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <div>
                      <p className="font-medium">#ORD-002</p>
                      <p className="text-sm text-gray-600">Burger Deluxe - ₺89</p>
                    </div>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                      Yolda
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <div>
                      <p className="font-medium">#ORD-003</p>
                      <p className="text-sm text-gray-600">Döner Evi - ₺65</p>
                    </div>
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                      Hazırlanıyor
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Bekleyen Onaylar</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center py-2 border-b">
                    <div>
                      <p className="font-medium">İşletme KYC</p>
                      <p className="text-sm text-gray-600">3 bekleyen başvuru</p>
                    </div>
                    <button className="text-blue-600 hover:text-blue-800">
                      Görüntüle →
                    </button>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <div>
                      <p className="font-medium">Kurye KYC</p>
                      <p className="text-sm text-gray-600">7 bekleyen başvuru</p>
                    </div>
                    <button className="text-blue-600 hover:text-blue-800">
                      Görüntüle →
                    </button>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <div>
                      <p className="font-medium">Promosyonlar</p>
                      <p className="text-sm text-gray-600">2 aktif kampanya</p>
                    </div>
                    <button className="text-blue-600 hover:text-blue-800">
                      Yönet →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentView === 'orders' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">📦 Sipariş Yönetimi</h2>
              <div className="flex space-x-2">
                <select className="border rounded px-3 py-2">
                  <option>Tüm Durumlar</option>
                  <option>Bekleyen</option>
                  <option>Onaylandı</option>
                  <option>Hazırlanıyor</option>
                  <option>Yolda</option>
                  <option>Teslim Edildi</option>
                  <option>İptal Edildi</option>
                </select>
                <input type="text" placeholder="Sipariş ara..." className="border rounded px-3 py-2" />
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sipariş No
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Müşteri
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşletme
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Kurye
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tutar
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Durum
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşlemler
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #ORD-001
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Ahmet Yılmaz
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Pizza Palace
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Mehmet K.
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ₺125.00
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Teslim Edildi
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Görüntüle</button>
                      <button className="text-red-600 hover:text-red-900">İptal Et</button>
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      #ORD-002
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Fatma Demir
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Burger Deluxe
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Ali S.
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ₺89.50
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        Yolda
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Görüntüle</button>
                      <button className="text-yellow-600 hover:text-yellow-900">Kurye Değiştir</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div className="mt-6 flex justify-between items-center">
              <p className="text-sm text-gray-700">
                Toplam 1,234 sipariş içinden 1-10 arası gösteriliyor
              </p>
              <div className="flex space-x-1">
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Önceki</button>
                <button className="px-3 py-1 bg-blue-500 text-white rounded">1</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">2</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Sonraki</button>
              </div>
            </div>
          </div>
        )}

        {currentView === 'courier-kyc' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">🚴 Kurye KYC Onayları</h2>
            
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold text-gray-900">Test Kurye</h3>
                    <p className="text-sm text-gray-600">courier@example.com • İstanbul</p>
                    <span className="inline-block mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                      KYC Bekliyor
                    </span>
                  </div>
                  <div className="space-x-2">
                    <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                      ✅ Onayla
                    </button>
                    <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                      ❌ Reddet
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="text-center py-8">
                <p className="text-gray-500">Kurye KYC sistemi aktif</p>
                <p className="text-sm text-gray-400 mt-2">
                  Backend: /admin/couriers/ID/kyc
                </p>
              </div>
            </div>
          </div>
        )}

        {currentView === 'business-kyc' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">🏪 İşletme KYC Onayları</h2>
            
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold text-gray-900">başer Restaurant</h3>
                    <p className="text-sm text-gray-600">baser@example.com • Aksaray</p>
                    <span className="inline-block mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                      Onay Bekliyor
                    </span>
                  </div>
                  <div className="space-x-2">
                    <button 
                      onClick={() => handleBusinessApprove('test-business-id')}
                      className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                    >
                      ✅ Onayla
                    </button>
                    <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                      ❌ Reddet
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="text-center py-8">
                <p className="text-gray-500">İşletme KYC sistemi aktif</p>
                <p className="text-sm text-gray-400 mt-2">
                  Backend: /admin/users/ID/approve
                </p>
              </div>
            </div>
          </div>
        )}

        {currentView === 'ads' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">📢 Reklam Yönetimi</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Banner Reklamları</h3>
                <p className="text-sm text-gray-600 mb-4">Ana sayfa banner reklamları</p>
                <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                  Yeni Banner Ekle
                </button>
              </div>
              
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">İşletme Reklamları</h3>
                <p className="text-sm text-gray-600 mb-4">Sponsorlu işletme listeleri</p>
                <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                  Reklam Oluştur
                </button>
              </div>
            </div>
          </div>
        )}

        {currentView === 'featured' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">⭐ Öne Çıkarılanlar</h2>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold">Öne Çıkan İşletmeler</h3>
                <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                  İşletme Ekle
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold">Pizza Palace</h4>
                  <p className="text-sm text-gray-600">İstanbul • ⭐ Öne Çıkan</p>
                  <div className="mt-2 space-x-2">
                    <button className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                      Kaldır
                    </button>
                  </div>
                </div>
                
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                  <p className="text-gray-500">Yeni işletme ekle</p>
                  <button className="mt-2 text-blue-500 hover:text-blue-600">
                    + Ekle
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentView === 'users' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">👥 Kullanıcı Yönetimi</h2>
            <p className="text-gray-600">Kullanıcı listesi burada görünecek.</p>
          </div>
        )}

        {currentView === 'businesses' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">🏪 İşletme Yönetimi</h2>
              <div className="flex space-x-2">
                <select className="border rounded px-3 py-2">
                  <option>Tüm Durumlar</option>
                  <option>Aktif</option>
                  <option>Pasif</option>
                  <option>KYC Bekliyor</option>
                  <option>Onaylandı</option>
                  <option>Reddedildi</option>
                </select>
                <input type="text" placeholder="İşletme ara..." className="border rounded px-3 py-2" />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Pizza Palace İstanbul</h3>
                    <p className="text-sm text-gray-600">Pizza & Fast Food</p>
                    <p className="text-sm text-gray-500">İstanbul, Kadıköy</p>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                    Aktif
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1 mb-4">
                  <p>📧 pizza@example.com</p>
                  <p>📞 +90 212 123 4567</p>
                  <p>⭐ 4.8 (156 değerlendirme)</p>
                  <p>📦 142 sipariş bu ay</p>
                </div>
                
                <div className="flex space-x-2">
                  <button className="flex-1 bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600">
                    Görüntüle
                  </button>
                  <button className="flex-1 bg-gray-500 text-white px-3 py-2 rounded text-sm hover:bg-gray-600">
                    Düzenle
                  </button>
                  <button className="bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600">
                    🚫
                  </button>
                </div>
              </div>
              
              <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Burger Deluxe</h3>
                    <p className="text-sm text-gray-600">Burger & Steakhouse</p>
                    <p className="text-sm text-gray-500">Ankara, Çankaya</p>
                  </div>
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                    KYC Bekliyor
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1 mb-4">
                  <p>📧 burger@example.com</p>
                  <p>📞 +90 312 987 6543</p>
                  <p>⭐ 4.6 (89 değerlendirme)</p>
                  <p>📦 67 sipariş bu ay</p>
                </div>
                
                <div className="flex space-x-2">
                  <button className="flex-1 bg-green-500 text-white px-3 py-2 rounded text-sm hover:bg-green-600">
                    ✅ Onayla
                  </button>
                  <button className="flex-1 bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600">
                    ❌ Reddet
                  </button>
                </div>
              </div>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
                <div className="text-gray-400 mb-2">
                  <svg className="mx-auto h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <p className="text-gray-500 font-medium">Yeni İşletme Ekle</p>
                <button className="mt-2 text-blue-500 hover:text-blue-600 text-sm">
                  + İşletme Oluştur
                </button>
              </div>
            </div>
            
            <div className="mt-6 flex justify-between items-center">
              <p className="text-sm text-gray-700">
                Toplam 89 işletme içinden 1-6 arası gösteriliyor
              </p>
              <div className="flex space-x-1">
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Önceki</button>
                <button className="px-3 py-1 bg-blue-500 text-white rounded">1</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">2</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Sonraki</button>
              </div>
            </div>
          </div>
        )}

        {currentView === 'menus' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">📋 Menü Yönetimi</h2>
              <div className="flex space-x-2">
                <select className="border rounded px-3 py-2">
                  <option>Tüm İşletmeler</option>
                  <option>Pizza Palace</option>
                  <option>Burger Deluxe</option>
                  <option>Döner Evi</option>
                </select>
                <input type="text" placeholder="Ürün ara..." className="border rounded px-3 py-2" />
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ürün
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşletme
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Kategori
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fiyat
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Durum
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşlemler
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 flex-shrink-0">
                          <img className="h-10 w-10 rounded-full object-cover" src="https://via.placeholder.com/40" alt="" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">Margherita Pizza</div>
                          <div className="text-sm text-gray-500">Klasik domates sosu, mozzarella</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Pizza Palace
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Pizza
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₺85.00
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Aktif
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Düzenle</button>
                      <button className="text-red-600 hover:text-red-900">Sil</button>
                    </td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 flex-shrink-0">
                          <img className="h-10 w-10 rounded-full object-cover" src="https://via.placeholder.com/40" alt="" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">Chicken Burger</div>
                          <div className="text-sm text-gray-500">Izgara tavuk, salata, sos</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Burger Deluxe
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Burger
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ₺65.00
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                        Pasif
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button className="text-blue-600 hover:text-blue-900 mr-2">Düzenle</button>
                      <button className="text-green-600 hover:text-green-900">Aktifleştir</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div className="mt-6 flex justify-between items-center">
              <p className="text-sm text-gray-700">
                Toplam 456 ürün içinden 1-10 arası gösteriliyor
              </p>
              <div className="flex space-x-1">
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Önceki</button>
                <button className="px-3 py-1 bg-blue-500 text-white rounded">1</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">2</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Sonraki</button>
              </div>
            </div>
          </div>
        )}

        {currentView === 'couriers' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">🚴 Kurye Yönetimi</h2>
              <div className="flex space-x-2">
                <select className="border rounded px-3 py-2">
                  <option>Tüm Durumlar</option>
                  <option>Çevrimiçi</option>
                  <option>Çevrimdışı</option>
                  <option>Teslimat Yapıyor</option>
                  <option>KYC Bekliyor</option>
                </select>
                <input type="text" placeholder="Kurye ara..." className="border rounded px-3 py-2" />
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center">
                    <div className="h-12 w-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                      MK
                    </div>
                    <div className="ml-3">
                      <h3 className="font-semibold text-gray-900">Mehmet Kaya</h3>
                      <p className="text-sm text-gray-600">Motosiklet</p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-green-400 rounded-full mr-2"></div>
                    <span className="text-sm text-green-600">Çevrimiçi</span>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1 mb-4">
                  <p>📧 mehmet@example.com</p>
                  <p>📞 +90 532 123 4567</p>
                  <p>📍 İstanbul, Kadıköy</p>
                  <p>⭐ 4.9 (234 değerlendirme)</p>
                  <p>📦 43 teslimat bu ay</p>
                  <p>💰 ₺2,340 kazanç</p>
                </div>
                
                <div className="flex space-x-2">
                  <button className="flex-1 bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600">
                    Görüntüle
                  </button>
                  <button className="flex-1 bg-yellow-500 text-white px-3 py-2 rounded text-sm hover:bg-yellow-600">
                    Mesaj
                  </button>
                </div>
              </div>
              
              <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center">
                    <div className="h-12 w-12 bg-green-500 rounded-full flex items-center justify-center text-white font-semibold">
                      AS
                    </div>
                    <div className="ml-3">
                      <h3 className="font-semibold text-gray-900">Ali Şahin</h3>
                      <p className="text-sm text-gray-600">Bisiklet</p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <div className="h-3 w-3 bg-blue-400 rounded-full mr-2"></div>
                    <span className="text-sm text-blue-600">Teslimat Yapıyor</span>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1 mb-4">
                  <p>📧 ali@example.com</p>
                  <p>📞 +90 533 987 6543</p>
                  <p>📍 Ankara, Çankaya</p>
                  <p>⭐ 4.7 (156 değerlendirme)</p>
                  <p>📦 38 teslimat bu ay</p>
                  <p>💰 ₺1,890 kazanç</p>
                </div>
                
                <div className="flex space-x-2">
                  <button className="flex-1 bg-orange-500 text-white px-3 py-2 rounded text-sm hover:bg-orange-600">
                    Takip Et
                  </button>
                  <button className="flex-1 bg-yellow-500 text-white px-3 py-2 rounded text-sm hover:bg-yellow-600">
                    İletişim
                  </button>
                </div>
              </div>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
                <div className="text-gray-400 mb-2">
                  <svg className="mx-auto h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <p className="text-gray-500 font-medium">Yeni Kurye Ekle</p>
                <button className="mt-2 text-blue-500 hover:text-blue-600 text-sm">
                  + Kurye Davet Et
                </button>
              </div>
            </div>
            
            <div className="mt-6 flex justify-between items-center">
              <p className="text-sm text-gray-700">
                Toplam 156 kurye içinden 1-6 arası gösteriliyor
              </p>
              <div className="flex space-x-1">
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Önceki</button>
                <button className="px-3 py-1 bg-blue-500 text-white rounded">1</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">2</button>
                <button className="px-3 py-1 border rounded hover:bg-gray-50">Sonraki</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminPanel;