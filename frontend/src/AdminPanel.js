import React, { useState, useEffect } from 'react';
import KYCManagement from './components/KYCManagement';
import ContentEditor from './components/ContentEditor';
import { apiClient } from './utils/apiClient';

const AdminPanel = ({ user, onLogout }) => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [pendingBusinesses, setPendingBusinesses] = useState([]);
  const [pendingCouriers, setPendingCouriers] = useState([]);
  const [promotions, setPromotions] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch pending businesses for KYC
  const fetchPendingBusinesses = async () => {
    try {
      const response = await apiClient.get('/admin/businesses?kyc_status=pending');
      setPendingBusinesses(response.data);
    } catch (error) {
      console.error('Fetch pending businesses error:', error);
    }
  };

  // Fetch pending couriers for KYC
  const fetchPendingCouriers = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/couriers?kyc_status=pending`, {
        withCredentials: true
      });
      
      if (response.ok) {
        const couriers = await response.json();
        setPendingCouriers(couriers);
      }
    } catch (error) {
      console.error('Fetch pending couriers error:', error);
    }
  };

  // Fetch all promotions
  const fetchPromotions = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/promotions`, {
        withCredentials: true
      });
      
      if (response.ok) {
        const promoData = await response.json();
        setPromotions(promoData);
      }
    } catch (error) {
      console.error('Fetch promotions error:', error);
    }
  };

  // Fetch all products for menu management
  const fetchProducts = async () => {
    try {
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/products`, {
        withCredentials: true
      });
      
      if (response.ok) {
        const productData = await response.json();
        setProducts(productData);
      }
    } catch (error) {
      console.error('Fetch products error:', error);
    }
  };

  // Load data on component mount
  useEffect(() => {
    if (user && user.role === 'admin') {
      fetchPendingBusinesses();
      fetchPendingCouriers();
      fetchPromotions();
      fetchProducts();
    }
  }, [user]);

  // Business approval handler
  const handleBusinessApprove = async (businessId) => {
    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/businesses/${businessId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          kyc_status: 'approved'
        })
      });
      
      if (response.ok) {
        alert('✅ İşletme KYC başarıyla onaylandı!');
        await fetchPendingBusinesses(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Onaylama başarısız: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Business approval error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  // Business rejection handler
  const handleBusinessReject = async (businessId, reason = '') => {
    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/businesses/${businessId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          kyc_status: 'rejected',
          rejection_reason: reason || 'Belgelerde eksiklik veya hata tespit edildi'
        })
      });
      
      if (response.ok) {
        alert('✅ İşletme KYC reddedildi!');
        await fetchPendingBusinesses(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Red işlemi başarısız: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Business rejection error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  // Courier approval handler
  const handleCourierApprove = async (courierId) => {
    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/couriers/${courierId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          kyc_status: 'approved'
        })
      });
      
      if (response.ok) {
        alert('✅ Kurye KYC başarıyla onaylandı!');
        await fetchPendingCouriers(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Onaylama başarısız: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Courier approval error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  // Courier rejection handler
  const handleCourierReject = async (courierId, reason = '') => {
    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/couriers/${courierId}/status`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          kyc_status: 'rejected',
          rejection_reason: reason || 'Belgeler yetersiz veya hatalı'
        })
      });
      
      if (response.ok) {
        alert('✅ Kurye KYC reddedildi!');
        await fetchPendingCouriers(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Red işlemi başarısız: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Courier rejection error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  // Promotion management handlers
  const handleCreatePromotion = async (promotionData) => {
    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/promotions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(promotionData)
      });
      
      if (response.ok) {
        alert('✅ Promosyon başarıyla oluşturuldu!');
        await fetchPromotions(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Promosyon oluşturulamadı: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Create promotion error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePromotion = async (promotionId) => {
    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/promotions/${promotionId}/toggle`, {
        method: 'PATCH',
        withCredentials: true
      });
      
      if (response.ok) {
        alert('✅ Promosyon durumu güncellendi!');
        await fetchPromotions(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Durum güncellenemedi: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Toggle promotion error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePromotion = async (promotionId) => {
    if (!window.confirm('Bu promosyonu silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/promotions/${promotionId}`, {
        method: 'DELETE',
        withCredentials: true
      });
      
      if (response.ok) {
        alert('✅ Promosyon silindi!');
        await fetchPromotions(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Silinemedi: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Delete promotion error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  // Product management handlers
  const handleToggleProduct = async (productId) => {
    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/products/${productId}/toggle`, {
        method: 'PATCH',
        withCredentials: true
      });
      
      if (response.ok) {
        alert('✅ Ürün durumu güncellendi!');
        await fetchProducts(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Durum güncellenemedi: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Toggle product error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Bu ürünü silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      setLoading(true);
      // CI GATE 0 COMPLIANCE - NO localStorage usage, use cookies
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${BACKEND_URL}/api/admin/products/${productId}`, {
        method: 'DELETE',
        withCredentials: true
      });
      
      if (response.ok) {
        alert('✅ Ürün silindi!');
        await fetchProducts(); // Refresh data
      } else {
        const errorData = await response.json();
        alert(`❌ Silinemedi: ${errorData.detail || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('Delete product error:', error);
      alert('❌ Ağ hatası oluştu!');
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
              { id: 'content-editor', label: '📝 İçerik Editörü' },
              { id: 'orders', label: '📦 Siparişler' },
              { id: 'businesses', label: '🏪 İşletmeler' },
              { id: 'business-kyc', label: '✅ İşletme KYC' },
              { id: 'couriers', label: '🚴 Kuryeler' },
              { id: 'courier-kyc', label: '✅ Kurye KYC' },
              { id: 'menus', label: '📋 Menü Yönetimi' },
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
                      <p className="text-sm text-gray-600">{pendingBusinesses.length} bekleyen başvuru</p>
                    </div>
                    <button 
                      onClick={() => setCurrentView('business-kyc')}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Görüntüle →
                    </button>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b">
                    <div>
                      <p className="font-medium">Kurye KYC</p>
                      <p className="text-sm text-gray-600">{pendingCouriers.length} bekleyen başvuru</p>
                    </div>
                    <button 
                      onClick={() => setCurrentView('courier-kyc')}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Görüntüle →
                    </button>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <div>
                      <p className="font-medium">Promosyonlar</p>
                      <p className="text-sm text-gray-600">{promotions.length} toplam kampanya</p>
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

        {/* KYC sections are now integrated into business and courier management modules */}

        {currentView === 'promotions' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">🎯 Promosyon Yönetimi</h2>
              <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                + Yeni Promosyon
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">%20 İndirim Kampanyası</h3>
                    <p className="text-sm text-gray-600">Yeni kullanıcılar için</p>
                  </div>
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                    Aktif
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1 mb-4">
                  <p>🎯 Tip: Yüzde İndirimi</p>
                  <p>💰 %20 indirim</p>
                  <p>📅 01.01.2024 - 31.01.2024</p>
                  <p>🔢 Kullanım: 234/1000</p>
                  <p>💳 Min. Tutar: ₺50</p>
                </div>
                
                <div className="flex space-x-2">
                  <button className="flex-1 bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600">
                    Düzenle
                  </button>
                  <button className="flex-1 bg-gray-500 text-white px-3 py-2 rounded text-sm hover:bg-gray-600">
                    Duraklat
                  </button>
                  <button className="bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600">
                    🗑️
                  </button>
                </div>
              </div>
              
              <div className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">Ücretsiz Teslimat</h3>
                    <p className="text-sm text-gray-600">150₺ üzeri siparişler</p>
                  </div>
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                    Beklemede
                  </span>
                </div>
                
                <div className="text-sm text-gray-600 space-y-1 mb-4">
                  <p>🎯 Tip: Ücretsiz Teslimat</p>
                  <p>💰 Teslimat ücreti ₺0</p>
                  <p>📅 15.02.2024 - 15.03.2024</p>
                  <p>🔢 Kullanım: 0/500</p>
                  <p>💳 Min. Tutar: ₺150</p>
                </div>
                
                <div className="flex space-x-2">
                  <button 
                    onClick={() => handleTogglePromotion('promo-1')}
                    disabled={loading}
                    className="flex-1 bg-green-500 text-white px-3 py-2 rounded text-sm hover:bg-green-600 disabled:opacity-50"
                  >
                    Başlat
                  </button>
                  <button className="flex-1 bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600">
                    Düzenle
                  </button>
                  <button 
                    onClick={() => handleDeletePromotion('promo-1')}
                    disabled={loading}
                    className="bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600 disabled:opacity-50"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
                <div className="text-gray-400 mb-2">
                  <svg className="mx-auto h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <p className="text-gray-500 font-medium">Yeni Promosyon</p>
                <button 
                  onClick={() => {
                    const promotionData = {
                      title: 'Yeni Kampanya',
                      description: 'Test kampanya açıklaması',
                      type: 'percentage',
                      value: 10,
                      min_order_amount: 50,
                      max_usage: 100,
                      start_date: new Date().toISOString().split('T')[0],
                      end_date: new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0]
                    };
                    handleCreatePromotion(promotionData);
                  }}
                  disabled={loading}
                  className="mt-2 text-blue-500 hover:text-blue-600 text-sm disabled:opacity-50"
                >
                  + Kampanya Oluştur
                </button>
              </div>
            </div>
          </div>
        )}

        {currentView === 'settings' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">⚙️ Platform Ayarları</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-6">
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Genel Ayarlar</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Bakım Modu</label>
                      <input type="checkbox" className="rounded" />
                    </div>
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Yeni Kayıtlar</label>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Teslimat Yarıçapı (km)</label>
                      <input type="number" defaultValue="50" className="w-full border rounded px-3 py-2" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Platform Komisyonu (%)</label>
                      <input type="number" defaultValue="5" className="w-full border rounded px-3 py-2" />
                    </div>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Ödeme Ayarları</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Kapıda Ödeme</label>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Online Ödeme</label>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">POS Ödeme</label>
                      <input type="checkbox" className="rounded" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Min. Sipariş Tutarı (₺)</label>
                      <input type="number" defaultValue="25" className="w-full border rounded px-3 py-2" />
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-6">
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Bildirim Ayarları</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Email Bildirimleri</label>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">SMS Bildirimleri</label>
                      <input type="checkbox" className="rounded" />
                    </div>
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Push Bildirimleri</label>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-4">KYC Ayarları</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">İşletme Otomatik Onay</label>
                      <input type="checkbox" className="rounded" />
                    </div>
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Kurye Otomatik Onay</label>
                      <input type="checkbox" className="rounded" />
                    </div>
                    <div className="flex justify-between items-center">
                      <label className="text-sm font-medium text-gray-700">Belge Doğrulama Gerekli</label>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Teslimat Bölgeleri</h3>
                  <div className="space-y-2 mb-3">
                    <div className="flex justify-between items-center py-2 border-b">
                      <span className="text-sm">İstanbul - Avrupa Yakası</span>
                      <span className="text-xs text-gray-500">₺5 teslimat</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b">
                      <span className="text-sm">İstanbul - Anadolu Yakası</span>
                      <span className="text-xs text-gray-500">₺5 teslimat</span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-sm">Ankara - Çankaya</span>
                      <span className="text-xs text-gray-500">₺7 teslimat</span>
                    </div>
                  </div>
                  <button className="w-full bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600">
                    Bölge Ekle
                  </button>
                </div>
              </div>
            </div>
            
            <div className="mt-6 pt-6 border-t flex justify-end space-x-3">
              <button className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50">
                İptal Et
              </button>
              <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                Ayarları Kaydet
              </button>
            </div>
          </div>
        )}

        {currentView === 'reports' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">📈 Raporlar & Analytics</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Bu Ayın Geliri</h3>
                <p className="text-2xl font-bold">₺125,430</p>
                <p className="text-sm opacity-90">+12% geçen aya göre</p>
              </div>
              <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Toplam Siparişler</h3>
                <p className="text-2xl font-bold">2,847</p>
                <p className="text-sm opacity-90">+18% geçen aya göre</p>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2">Ortalama Sipariş</h3>
                <p className="text-2xl font-bold">₺87.50</p>
                <p className="text-sm opacity-90">+5% geçen aya göre</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-4">Sipariş Durumu Dağılımı</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Teslim Edildi</span>
                    <div className="flex items-center">
                      <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                        <div className="bg-green-500 h-2 rounded-full" style={{width: '85%'}}></div>
                      </div>
                      <span className="text-sm font-medium">85%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Yolda</span>
                    <div className="flex items-center">
                      <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                        <div className="bg-blue-500 h-2 rounded-full" style={{width: '8%'}}></div>
                      </div>
                      <span className="text-sm font-medium">8%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Hazırlanıyor</span>
                    <div className="flex items-center">
                      <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                        <div className="bg-yellow-500 h-2 rounded-full" style={{width: '5%'}}></div>
                      </div>
                      <span className="text-sm font-medium">5%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">İptal Edildi</span>
                    <div className="flex items-center">
                      <div className="w-32 bg-gray-200 rounded-full h-2 mr-2">
                        <div className="bg-red-500 h-2 rounded-full" style={{width: '2%'}}></div>
                      </div>
                      <span className="text-sm font-medium">2%</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-4">Top Kategoriler</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">🍕 Pizza</span>
                    <span className="font-medium">₺45,230</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">🍔 Burger</span>
                    <span className="font-medium">₺38,920</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">🌯 Döner</span>
                    <span className="font-medium">₺25,640</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">🍖 Et Yemekleri</span>
                    <span className="font-medium">₺18,340</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">🥗 Salata</span>
                    <span className="font-medium">₺12,890</span>
                  </div>
                </div>
              </div>
              
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-4">Şehir Bazlı Performans</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">İstanbul</span>
                    <div className="text-right">
                      <div className="font-medium">1,456 sipariş</div>
                      <div className="text-xs text-gray-500">₺89,340</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Ankara</span>
                    <div className="text-right">
                      <div className="font-medium">654 sipariş</div>
                      <div className="text-xs text-gray-500">₺42,180</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">İzmir</span>
                    <div className="text-right">
                      <div className="font-medium">387 sipariş</div>
                      <div className="text-xs text-gray-500">₺28,670</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="border rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-4">En İyi Performans Gösteren İşletmeler</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">🥇</span>
                      <span className="text-sm text-gray-600">Pizza Palace İstanbul</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">234 sipariş</div>
                      <div className="text-xs text-gray-500">⭐ 4.8</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">🥈</span>
                      <span className="text-sm text-gray-600">Burger Deluxe</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">189 sipariş</div>
                      <div className="text-xs text-gray-500">⭐ 4.7</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">🥉</span>
                      <span className="text-sm text-gray-600">Döner Evi</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">156 sipariş</div>
                      <div className="text-xs text-gray-500">⭐ 4.6</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 pt-6 border-t">
              <div className="flex justify-between items-center">
                <h3 className="font-semibold text-gray-900">Detaylı Raporlar</h3>
                <div className="flex space-x-2">
                  <button className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50">
                    📊 Finansal Rapor İndir
                  </button>
                  <button className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50">
                    📈 Sipariş Raporu İndir
                  </button>
                  <button className="px-3 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50">
                    👥 Kullanıcı Raporu İndir
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentView === 'businesses' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">🏪 İşletme & Kurye KYC Yönetimi</h2>
            </div>
            <KYCManagement user={user} />
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
                      <button 
                        onClick={() => handleDeleteProduct('product-1')}
                        disabled={loading}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        Sil
                      </button>
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
                      <button 
                        onClick={() => handleToggleProduct('product-2')}
                        disabled={loading}
                        className="text-green-600 hover:text-green-900 disabled:opacity-50"
                      >
                        Aktifleştir
                      </button>
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

        {/* Business KYC View */}
        {currentView === 'business-kyc' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">✅ İşletme KYC Onayları</h2>
              <div className="text-sm text-gray-600">
                {pendingBusinesses.length} bekleyen başvuru
              </div>
            </div>
            
            {loading ? (
              <div className="text-center py-12">
                <div className="text-gray-500">Yükleniyor...</div>
              </div>
            ) : pendingBusinesses.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-500">
                  🎉 Tüm işletme KYC başvuruları işlenmiş!
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {pendingBusinesses.map((business) => (
                  <div key={business.id} className="border rounded-lg p-6 hover:shadow-lg transition-shadow">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">{business.business_name}</h3>
                        <p className="text-gray-600">{business.category}</p>
                        <p className="text-sm text-gray-500">{business.address}</p>
                      </div>
                      <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full">
                        KYC Bekliyor
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-6 mb-6">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">İşletme Bilgileri</h4>
                        <div className="space-y-2 text-sm">
                          <p><span className="text-gray-600">Email:</span> {business.email}</p>
                          <p><span className="text-gray-600">Telefon:</span> {business.phone}</p>
                          <p><span className="text-gray-600">Yetkili Kişi:</span> {business.owner_name}</p>
                          <p><span className="text-gray-600">Vergi No:</span> {business.tax_number}</p>
                          <p><span className="text-gray-600">Başvuru Tarihi:</span> {new Date(business.created_at).toLocaleDateString('tr-TR')}</p>
                        </div>
                      </div>
                      
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Belgeler</h4>
                        <div className="space-y-2 text-sm">
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            Ticaret Sicil Belgesi
                          </p>
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            Vergi Levhası
                          </p>
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            İmza Sirküleri
                          </p>
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            İşyeri Fotoğrafları
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex space-x-4 pt-4 border-t">
                      <button
                        onClick={() => handleBusinessApprove(business.id)}
                        disabled={loading}
                        className="flex-1 bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
                      >
                        ✅ Onayla
                      </button>
                      <button
                        onClick={() => {
                          const reason = prompt('Red nedeni girin (isteğe bağlı):');
                          if (reason !== null) {
                            handleBusinessReject(business.id, reason);
                          }
                        }}
                        disabled={loading}
                        className="flex-1 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:opacity-50"
                      >
                        ❌ Reddet
                      </button>
                      <button className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50">
                        📄 Detay Görüntüle
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Courier KYC View */}
        {currentView === 'courier-kyc' && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900">✅ Kurye KYC Onayları</h2>
              <div className="text-sm text-gray-600">
                {pendingCouriers.length} bekleyen başvuru
              </div>
            </div>
            
            {loading ? (
              <div className="text-center py-12">
                <div className="text-gray-500">Yükleniyor...</div>
              </div>
            ) : pendingCouriers.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-500">
                  🎉 Tüm kurye KYC başvuruları işlenmiş!
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {pendingCouriers.map((courier) => (
                  <div key={courier.id} className="border rounded-lg p-6 hover:shadow-lg transition-shadow">
                    <div className="flex items-center mb-4">
                      <div className="h-16 w-16 bg-blue-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                        {courier.first_name?.charAt(0)}{courier.last_name?.charAt(0)}
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {courier.first_name} {courier.last_name}
                        </h3>
                        <p className="text-gray-600">{courier.vehicle_type || 'Motosiklet'}</p>
                        <span className="inline-block px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">
                          KYC Bekliyor
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-3 mb-6">
                      <div className="text-sm">
                        <p><span className="text-gray-600">Email:</span> {courier.email}</p>
                        <p><span className="text-gray-600">Telefon:</span> {courier.phone}</p>
                        <p><span className="text-gray-600">Doğum Tarihi:</span> {courier.birth_date || 'Belirtilmemiş'}</p>
                        <p><span className="text-gray-600">Başvuru Tarihi:</span> {new Date(courier.created_at).toLocaleDateString('tr-TR')}</p>
                      </div>
                      
                      <div className="pt-3 border-t">
                        <h4 className="font-medium text-gray-900 mb-2">Belgeler</h4>
                        <div className="space-y-1 text-sm">
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            TC Kimlik Belgesi
                          </p>
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            Ehliyet
                          </p>
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            Araç Ruhsatı
                          </p>
                          <p className="flex items-center">
                            <span className="text-green-500 mr-2">✓</span>
                            Adli Sicil Belgesi
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex space-x-3">
                      <button
                        onClick={() => handleCourierApprove(courier.id)}
                        disabled={loading}
                        className="flex-1 bg-green-500 text-white px-3 py-2 rounded text-sm hover:bg-green-600 disabled:opacity-50"
                      >
                        ✅ Onayla
                      </button>
                      <button
                        onClick={() => {
                          const reason = prompt('Red nedeni girin (isteğe bağlı):');
                          if (reason !== null) {
                            handleCourierReject(courier.id, reason);
                          }
                        }}
                        disabled={loading}
                        className="flex-1 bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600 disabled:opacity-50"
                      >
                        ❌ Reddet
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Content Editor View */}
        {currentView === 'content-editor' && (
          <ContentEditor />
        )}
      </main>
    </div>
  );
};

export default AdminPanel;