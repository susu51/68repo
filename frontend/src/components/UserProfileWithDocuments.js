import React, { useState, useEffect } from 'react';
import { api } from '../api/http';
import toast from 'react-hot-toast';

const UserProfileWithDocuments = ({ user, onClose }) => {
  const [userDetails, setUserDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserDetails();
  }, []);

  const fetchUserDetails = async () => {
    try {
      const response = await api('/me');
      const data = await response.json();
      setUserDetails(data);
    } catch (error) {
      console.error('Error fetching user details:', error);
      toast.error('Profil bilgileri yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto"></div>
          <p className="text-center mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  const getRoleIcon = (role) => {
    switch(role) {
      case 'customer': return '🛒';
      case 'courier': return '🏍️';
      case 'business': return '🏪';
      case 'admin': return '👑';
      default: return '👤';
    }
  };

  const getRoleName = (role) => {
    switch(role) {
      case 'customer': return 'Müşteri';
      case 'courier': return 'Kurye';
      case 'business': return 'İşletme';
      case 'admin': return 'Admin';
      default: return 'Kullanıcı';
    }
  };

  const getKYCStatusBadge = (status) => {
    const badges = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '⏳ Onay Bekliyor' },
      approved: { bg: 'bg-green-100', text: 'text-green-800', label: '✅ Onaylandı' },
      rejected: { bg: 'bg-red-100', text: 'text-red-800', label: '❌ Reddedildi' }
    };
    const badge = badges[status] || { bg: 'bg-gray-100', text: 'text-gray-800', label: status };
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-3xl w-full my-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 p-6 rounded-t-2xl">
          <div className="flex items-center justify-between text-white">
            <div className="flex items-center space-x-4">
              <div className="text-5xl">{getRoleIcon(userDetails?.role)}</div>
              <div>
                <h2 className="text-2xl font-bold">{userDetails?.name || 'Kullanıcı'}</h2>
                <p className="text-orange-100">{getRoleName(userDetails?.role)}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* KYC Status */}
          {userDetails?.kyc_status && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-blue-900 mb-1">KYC Onay Durumu</h3>
                  <p className="text-sm text-blue-700">
                    {userDetails.kyc_status === 'pending' && 'Başvurunuz inceleniyor. Onay sonrası tüm özelliklere erişebileceksiniz.'}
                    {userDetails.kyc_status === 'approved' && 'Hesabınız onaylandı! Tüm özellikleri kullanabilirsiniz.'}
                    {userDetails.kyc_status === 'rejected' && 'Başvurunuz reddedildi. Lütfen destek ile iletişime geçin.'}
                  </p>
                </div>
                {getKYCStatusBadge(userDetails.kyc_status)}
              </div>
            </div>
          )}

          {/* Personal Info */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Kişisel Bilgiler</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Ad Soyad</div>
                <div className="font-medium text-gray-900">{userDetails?.name || '-'}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">E-posta</div>
                <div className="font-medium text-gray-900">{userDetails?.email || '-'}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Telefon</div>
                <div className="font-medium text-gray-900">{userDetails?.phone || '-'}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Şehir</div>
                <div className="font-medium text-gray-900">{userDetails?.city || '-'}</div>
              </div>
              {userDetails?.district && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600">İlçe</div>
                  <div className="font-medium text-gray-900">{userDetails.district}</div>
                </div>
              )}
              {userDetails?.neighborhood && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600">Mahalle/Köy</div>
                  <div className="font-medium text-gray-900">{userDetails.neighborhood}</div>
                </div>
              )}
            </div>
          </div>

          {/* Role Specific Info */}
          {userDetails?.role === 'courier' && userDetails?.vehicle_type && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Kurye Bilgileri</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Araç Tipi</div>
                <div className="font-medium text-gray-900">
                  {userDetails.vehicle_type === 'bicycle' && '🚲 Bisiklet'}
                  {userDetails.vehicle_type === 'motorbike' && '🏍️ Motosiklet'}
                  {userDetails.vehicle_type === 'car' && '🚗 Araba'}
                  {userDetails.vehicle_type === 'van' && '🚚 Minivan'}
                </div>
              </div>
            </div>
          )}

          {userDetails?.role === 'business' && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">İşletme Bilgileri</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {userDetails.business_name && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600">İşletme Adı</div>
                    <div className="font-medium text-gray-900">{userDetails.business_name}</div>
                  </div>
                )}
                {userDetails.business_tax_id && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600">Vergi Numarası</div>
                    <div className="font-medium text-gray-900">{userDetails.business_tax_id}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* KYC Documents */}
          {userDetails?.kyc_documents && userDetails.kyc_documents.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Yüklenen Belgeler</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {userDetails.kyc_documents.map((doc, index) => (
                  <a
                    key={index}
                    href={`${process.env.REACT_APP_BACKEND_URL || ''}${doc.path}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-3 p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200"
                  >
                    <div className="text-3xl">
                      {doc.type === 'license' && '🪪'}
                      {doc.type === 'id_card' && '👤'}
                      {doc.type === 'vehicle_registration' && '📋'}
                      {doc.type === 'business_photo' && '🏪'}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-blue-900">
                        {doc.type === 'license' && 'Ehliyet'}
                        {doc.type === 'id_card' && 'Kimlik'}
                        {doc.type === 'vehicle_registration' && 'Araç Ruhsatı'}
                        {doc.type === 'business_photo' && 'İşletme Fotoğrafı'}
                      </div>
                      <div className="text-sm text-blue-600">{doc.filename}</div>
                    </div>
                    <div className="text-blue-600">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </div>
                  </a>
                ))}
              </div>
              <p className="text-sm text-gray-500 mt-3">
                💡 Belgeleri görüntülemek için tıklayın
              </p>
            </div>
          )}

          {/* No Documents Message */}
          {(!userDetails?.kyc_documents || userDetails.kyc_documents.length === 0) && 
           (userDetails?.role === 'courier' || userDetails?.role === 'business') && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <span className="text-xl">⚠️</span>
                <div className="text-sm text-yellow-800">
                  <p className="font-medium">Belge Yüklemesi Eksik</p>
                  <p>Kayıt sırasında belge yüklemeniz gerekmekteydi. Lütfen destek ile iletişime geçin.</p>
                </div>
              </div>
            </div>
          )}

          {/* Account Info */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Hesap Bilgileri</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">Hesap Durumu</div>
                <div className="font-medium text-gray-900">
                  {userDetails?.is_active ? '✅ Aktif' : '❌ Pasif'}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-600">E-posta Doğrulama</div>
                <div className="font-medium text-gray-900">
                  {userDetails?.is_verified ? '✅ Doğrulandı' : '⏳ Bekliyor'}
                </div>
              </div>
              {userDetails?.created_at && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600">Kayıt Tarihi</div>
                  <div className="font-medium text-gray-900">
                    {new Date(userDetails.created_at).toLocaleDateString('tr-TR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 p-6 bg-gray-50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors font-medium"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserProfileWithDocuments;
