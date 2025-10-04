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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Toplam Kullanıcılar</h3>
              <p className="text-3xl font-bold text-blue-600">150</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Aktif İşletmeler</h3>
              <p className="text-3xl font-bold text-green-600">45</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Bekleyen KYC</h3>
              <p className="text-3xl font-bold text-yellow-600">12</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Günlük Siparişler</h3>
              <p className="text-3xl font-bold text-purple-600">89</p>
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
            <h2 className="text-xl font-semibold text-gray-900 mb-6">🏪 İşletme Yönetimi</h2>
            <p className="text-gray-600">İşletme listesi burada görünecek.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminPanel;