/**
 * KYC Management Component - İşletme ve Kurye Onay Sistemi
 * Temizlenmiş ve düzenli KYC yönetim paneli
 */
import React, { useState, useEffect } from 'react';
import { apiClient } from '../utils/apiClient';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';

const KYCManagement = ({ user }) => {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('pending');
  const [businesses, setBusinesses] = useState([]);
  const [couriers, setCouriers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);

  // Fetch businesses by status
  const fetchBusinesses = async (status = 'pending') => {
    try {
      setLoading(true);
      
      if (!isAuthenticated) {
        toast.error('Admin girişi gereklidir');
        return;
      }
      
      const response = await apiClient.get(`/admin/businesses?kyc_status=${status}`);
      const data = response.data;
      
      setBusinesses(data);
      console.log(`✅ Loaded ${data.length} businesses with status: ${status}`);
    } catch (error) {
      console.error('❌ Fetch businesses error:', error);
      setBusinesses([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch couriers by status
  const fetchCouriers = async (status = 'pending') => {
    try {
      setLoading(true);
      
      if (!isAuthenticated) {
        toast.error('Admin girişi gereklidir');
        return;
      }
      
      const response = await apiClient.get(`/admin/couriers?kyc_status=${status}`);
      const data = response.data;
      
      setCouriers(data);
      console.log(`✅ Loaded ${data.length} couriers with status: ${status}`);
    } catch (error) {
      console.error('❌ Fetch couriers error:', error);
      setCouriers([]);
    } finally {
      setLoading(false);
    }
  };

  // KYC Approval
  const approveKYC = async (type, id) => {
    try {
      setLoading(true);
      
      if (!isAuthenticated) {
        toast.error('Admin girişi gereklidir');
        return;
      }
      
      const endpoint = type === 'business' 
        ? `/admin/businesses/${id}/status`
        : `/admin/couriers/${id}/status`;

      const response = await apiClient.patch(endpoint, { kyc_status: 'approved' });
      
      if (response.data.success) {
        toast.success(`✅ ${type === 'business' ? 'İşletme' : 'Kurye'} KYC başarıyla onaylandı!`);
        
        // Refresh both pending and approved lists
        await Promise.all([
          fetchBusinesses('pending'),
          fetchBusinesses('approved'),
          fetchCouriers('pending'),
          fetchCouriers('approved')
        ]);
      } else {
        toast.error(`❌ Onaylama başarısız: ${response.data.message || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('❌ Approval error:', error);
      toast.error('❌ Ağ hatası oluştu! Lütfen tekrar deneyin.');
    } finally {
      setLoading(false);
    }
  };

  // KYC Rejection
  const rejectKYC = async (type, id, reason) => {
    if (!reason) {
      reason = prompt(`${type === 'business' ? 'İşletme' : 'Kurye'} reddetme sebebini girin:`);
      if (!reason) return;
    }

    try {
      setLoading(true);
      
      if (!isAuthenticated) {
        toast.error('Admin girişi gereklidir');
        return;
      }
      
      const endpoint = type === 'business'
        ? `/admin/businesses/${id}/status`
        : `/admin/couriers/${id}/status`;

      const response = await apiClient.patch(endpoint, { 
        kyc_status: 'rejected',
        rejection_reason: reason
      });

      if (response.data.success) {
        toast.success(`✅ ${type === 'business' ? 'İşletme' : 'Kurye'} KYC reddedildi!`);
        
        // Refresh lists
        await Promise.all([
          fetchBusinesses('pending'),
          fetchBusinesses('rejected'),
          fetchCouriers('pending'),
          fetchCouriers('rejected')
        ]);
      } else {
        toast.error(`❌ Reddetme başarısız: ${response.data.message || 'Bilinmeyen hata'}`);
      }
    } catch (error) {
      console.error('❌ Rejection error:', error);
      alert('❌ Ağ hatası oluştu!');
    } finally {
      setLoading(false);
    }
  };

  // View document
  const viewDocument = (documentUrl, title) => {
    setSelectedDocument({ url: documentUrl, title });
  };

  // Load data on tab change
  useEffect(() => {
    fetchBusinesses(activeTab);
    fetchCouriers(activeTab);
  }, [activeTab]);

  const BusinessCard = ({ business }) => (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{business.name}</h3>
          <p className="text-sm text-gray-600">{business.cuisine_type || 'Belirtilmemiş'}</p>
          <p className="text-sm text-gray-500">{business.address}</p>
          <p className="text-sm text-gray-500">📧 {business.email || 'Email yok'}</p>
          <p className="text-sm text-gray-500">📞 {business.phone || 'Telefon yok'}</p>
        </div>
        <div className="flex flex-col items-end space-y-2">
          <span className={`px-2 py-1 text-xs rounded-full ${
            business.kyc_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
            business.kyc_status === 'approved' ? 'bg-green-100 text-green-800' :
            'bg-red-100 text-red-800'
          }`}>
            {business.kyc_status === 'pending' ? 'Bekliyor' :
             business.kyc_status === 'approved' ? 'Onaylandı' : 'Reddedildi'}
          </span>
        </div>
      </div>

      {/* KYC Documents */}
      <div className="mb-3">
        <p className="text-sm font-medium text-gray-700 mb-2">KYC Belgeleri:</p>
        <div className="space-y-1">
          {business.kyc_documents?.business_license && (
            <button 
              className="text-xs text-blue-600 hover:underline block"
              onClick={() => viewDocument(business.kyc_documents.business_license, 'İşletme Ruhsatı')}
            >
              📄 İşletme Ruhsatı
            </button>
          )}
          {business.kyc_documents?.tax_certificate && (
            <button 
              className="text-xs text-blue-600 hover:underline block"
              onClick={() => viewDocument(business.kyc_documents.tax_certificate, 'Vergi Levhası')}
            >
              📄 Vergi Levhası
            </button>
          )}
          {!business.kyc_documents && (
            <p className="text-xs text-gray-500">Belge yüklenmemiş</p>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      {business.kyc_status === 'pending' && (
        <div className="flex space-x-2">
          <button
            className="flex-1 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
            onClick={() => approveKYC('business', business._id || business.id)}
            disabled={loading}
          >
            ✅ Onayla
          </button>
          <button
            className="flex-1 bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700 disabled:opacity-50"
            onClick={() => rejectKYC('business', business._id || business.id)}
            disabled={loading}
          >
            ❌ Reddet
          </button>
        </div>
      )}

      {business.kyc_status === 'rejected' && business.rejection_reason && (
        <div className="mt-2 p-2 bg-red-50 rounded text-sm">
          <p className="text-red-800">Ret Sebebi: {business.rejection_reason}</p>
        </div>
      )}
    </div>
  );

  const CourierCard = ({ courier }) => (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{courier.name || 'İsim Belirtilmemiş'}</h3>
          <p className="text-sm text-gray-600">Kurye</p>
          <p className="text-sm text-gray-500">📧 {courier.email || 'Email yok'}</p>
          <p className="text-sm text-gray-500">📞 {courier.phone || 'Telefon yok'}</p>
          {courier.vehicle_info && (
            <p className="text-sm text-gray-500">🚗 {courier.vehicle_info}</p>
          )}
        </div>
        <span className={`px-2 py-1 text-xs rounded-full ${
          courier.kyc_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
          courier.kyc_status === 'approved' ? 'bg-green-100 text-green-800' :
          'bg-red-100 text-red-800'
        }`}>
          {courier.kyc_status === 'pending' ? 'Bekliyor' :
           courier.kyc_status === 'approved' ? 'Onaylandı' : 'Reddedildi'}
        </span>
      </div>

      {/* KYC Documents */}
      <div className="mb-3">
        <p className="text-sm font-medium text-gray-700 mb-2">KYC Belgeleri:</p>
        <div className="space-y-1">
          {courier.kyc_documents?.id_card && (
            <button 
              className="text-xs text-blue-600 hover:underline block"
              onClick={() => viewDocument(courier.kyc_documents.id_card, 'Kimlik Kartı')}
            >
              🆔 Kimlik Kartı
            </button>
          )}
          {courier.kyc_documents?.driving_license && (
            <button 
              className="text-xs text-blue-600 hover:underline block"
              onClick={() => viewDocument(courier.kyc_documents.driving_license, 'Ehliyet')}
            >
              🚗 Ehliyet
            </button>
          )}
          {!courier.kyc_documents && (
            <p className="text-xs text-gray-500">Belge yüklenmemiş</p>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      {courier.kyc_status === 'pending' && (
        <div className="flex space-x-2">
          <button
            className="flex-1 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
            onClick={() => approveKYC('courier', courier._id || courier.id)}
            disabled={loading}
          >
            ✅ Onayla
          </button>
          <button
            className="flex-1 bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700 disabled:opacity-50"
            onClick={() => rejectKYC('courier', courier._id || courier.id)}
            disabled={loading}
          >
            ❌ Reddet
          </button>
        </div>
      )}

      {courier.kyc_status === 'rejected' && courier.rejection_reason && (
        <div className="mt-2 p-2 bg-red-50 rounded text-sm">
          <p className="text-red-800">Ret Sebebi: {courier.rejection_reason}</p>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Status Tabs */}
      <div className="flex space-x-4 border-b">
        {['pending', 'approved', 'rejected'].map((status) => (
          <button
            key={status}
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === status
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab(status)}
          >
            {status === 'pending' ? '⏳ Bekliyor' :
             status === 'approved' ? '✅ Onaylandı' : '❌ Reddedildi'}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Businesses Section */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          🏪 İşletmeler ({businesses.length})
        </h3>
        {businesses.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {businesses.map((business) => (
              <BusinessCard key={business._id || business.id} business={business} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 py-8 text-center">
            {activeTab === 'pending' ? 'KYC bekleyen işletme yok.' :
             activeTab === 'approved' ? 'Onaylanmış işletme yok.' : 'Reddedilmiş işletme yok.'}
          </p>
        )}
      </div>

      {/* Couriers Section */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          🚚 Kuryeler ({couriers.length})
        </h3>
        {couriers.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {couriers.map((courier) => (
              <CourierCard key={courier._id || courier.id} courier={courier} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 py-8 text-center">
            {activeTab === 'pending' ? 'KYC bekleyen kurye yok.' :
             activeTab === 'approved' ? 'Onaylanmış kurye yok.' : 'Reddedilmiş kurye yok.'}
          </p>
        )}
      </div>

      {/* Document Modal */}
      {selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-3xl max-h-3xl overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">{selectedDocument.title}</h3>
              <button
                className="text-gray-500 hover:text-gray-700"
                onClick={() => setSelectedDocument(null)}
              >
                ✕
              </button>
            </div>
            <img 
              src={selectedDocument.url} 
              alt={selectedDocument.title}
              className="max-w-full h-auto"
              onError={() => alert('Belge yüklenemedi!')}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default KYCManagement;