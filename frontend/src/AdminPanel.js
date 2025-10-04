import React, { useState, useEffect } from 'react';

const AdminPanel = ({ user, onLogout }) => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [pendingBusinesses, setPendingBusinesses] = useState([]);
  const [pendingCouriers, setPendingCouriers] = useState([]);
  const [loading, setLoading] = useState(false);
  
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
              { id: 'courier-kyc', label: '🚴 Kurye KYC' },
              { id: 'business-kyc', label: '🏪 İşletme KYC' },
              { id: 'users', label: '👥 Kullanıcılar' },
              { id: 'businesses', label: '🏪 İşletmeler' },
              { id: 'ads', label: '📢 Reklamlar' },
              { id: 'featured', label: '⭐ Öne Çıkar' }
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

        {currentView === 'kyc' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">🏪 İşletme KYC Onayları</h2>
            
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold text-gray-900">Test İşletmesi</h3>
                    <p className="text-sm text-gray-600">test@example.com • Aksaray</p>
                    <span className="inline-block mt-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                      Onay Bekliyor
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
                <p className="text-gray-500">Bu basit KYC sistemi çalışıyor!</p>
                <p className="text-sm text-gray-400 mt-2">
                  Backend endpoints: /admin/users/ID/approve
                </p>
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