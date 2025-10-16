import React, { useState, useEffect } from 'react';
import { api } from '../api/http';
import toast from 'react-hot-toast';

const AdminKYC = () => {
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ pending: 0, approved: 0, rejected: 0 });
  const [selectedUser, setSelectedUser] = useState(null);

  useEffect(() => {
    fetchPendingRequests();
    fetchStats();
  }, []);

  const fetchPendingRequests = async () => {
    try {
      const response = await api('/admin/kyc/pending');
      const data = await response.json();
      if (data.success) {
        setPendingRequests(data.pending_requests);
      }
    } catch (error) {
      console.error('Error fetching pending requests:', error);
      toast.error('KYC istekleri yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api('/admin/kyc/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleAction = async (userId, action, reason = null) => {
    try {
      const response = await api('/admin/kyc/action', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, action, reason })
      });

      const data = await response.json();
      if (data.success) {
        toast.success(`KYC ${action === 'approve' ? 'onaylandı' : 'reddedildi'}!`);
        fetchPendingRequests();
        fetchStats();
        setSelectedUser(null);
      }
    } catch (error) {
      console.error('Error processing KYC action:', error);
      toast.error('İşlem başarısız');
    }
  };

  const getRoleIcon = (role) => {
    switch(role) {
      case 'courier': return '🏍️';
      case 'business': return '🏪';
      default: return '👤';
    }
  };

  const getRoleName = (role) => {
    switch(role) {
      case 'courier': return 'Kurye';
      case 'business': return 'İşletme';
      default: return 'Kullanıcı';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">KYC Onay Sistemi</h1>
          <p className="text-gray-600 mt-2">Kurye ve işletme başvurularını inceleyin ve onaylayın</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Bekleyen</div>
            <div className="text-3xl font-bold text-orange-600">{stats.pending}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Onaylanan</div>
            <div className="text-3xl font-bold text-green-600">{stats.approved}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Reddedilen</div>
            <div className="text-3xl font-bold text-red-600">{stats.rejected}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Toplam</div>
            <div className="text-3xl font-bold text-gray-800">{stats.total}</div>
          </div>
        </div>

        {/* Pending Requests List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Bekleyen Başvurular</h2>
          </div>

          {pendingRequests.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-5xl mb-4">✅</div>
              <p>Bekleyen KYC başvurusu yok</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {pendingRequests.map((request) => (
                <div key={request.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* User Info */}
                      <div className="flex items-center space-x-3 mb-3">
                        <span className="text-3xl">{getRoleIcon(request.role)}</span>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="text-lg font-semibold text-gray-900">{request.name}</h3>
                            <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-medium rounded">
                              {getRoleName(request.role)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{request.email}</p>
                        </div>
                      </div>

                      {/* İletişim Bilgileri */}
                      <div className="mb-6">
                        <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
                          <span>📞</span>
                          <span>İletişim Bilgileri</span>
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <div className="text-xs text-gray-500 mb-1">📧 E-posta</div>
                            <div className="text-sm font-medium text-gray-900 break-all">{request.email}</div>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <div className="text-xs text-gray-500 mb-1">📱 Telefon</div>
                            <div className="text-sm font-medium text-gray-900">{request.phone || '-'}</div>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <div className="text-xs text-gray-500 mb-1">👤 Ad Soyad</div>
                            <div className="text-sm font-medium text-gray-900">{request.name}</div>
                          </div>
                        </div>
                      </div>

                      {/* Konum Bilgileri */}
                      <div className="mb-6">
                        <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
                          <span>📍</span>
                          <span>Konum Bilgileri</span>
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <div className="text-xs text-gray-500 mb-1">İl</div>
                            <div className="text-sm font-medium text-gray-900">{request.city || '-'}</div>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <div className="text-xs text-gray-500 mb-1">İlçe</div>
                            <div className="text-sm font-medium text-gray-900">{request.district || '-'}</div>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <div className="text-xs text-gray-500 mb-1">Mahalle/Köy</div>
                            <div className="text-sm font-medium text-gray-900">{request.neighborhood || '-'}</div>
                          </div>
                        </div>
                      </div>

                      {/* Rol Bazlı Bilgiler */}
                      {(request.vehicle_type || request.business_name) && (
                        <div className="mb-6">
                          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
                            <span>{request.role === 'courier' ? '🏍️' : '🏪'}</span>
                            <span>{request.role === 'courier' ? 'Kurye Bilgileri' : 'İşletme Bilgileri'}</span>
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {request.vehicle_type && (
                              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                <div className="text-xs text-gray-500 mb-1">Araç Tipi</div>
                                <div className="text-sm font-medium text-gray-900">
                                  {request.vehicle_type === 'bicycle' && '🚲 Bisiklet'}
                                  {request.vehicle_type === 'motorbike' && '🏍️ Motosiklet'}
                                  {request.vehicle_type === 'car' && '🚗 Araba'}
                                  {request.vehicle_type === 'van' && '🚚 Minivan'}
                                </div>
                              </div>
                            )}
                            {request.business_name && (
                              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                <div className="text-xs text-gray-500 mb-1">İşletme Adı</div>
                                <div className="text-sm font-medium text-gray-900">{request.business_name}</div>
                              </div>
                            )}
                            {request.business_tax_id && (
                              <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                <div className="text-xs text-gray-500 mb-1">Vergi Numarası</div>
                                <div className="text-sm font-medium text-gray-900">{request.business_tax_id}</div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Yüklenen Belgeler - Büyük ve Görsel */}
                      {request.kyc_documents && request.kyc_documents.length > 0 ? (
                        <div className="mb-6">
                          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
                            <span>📄</span>
                            <span>Yüklenen Belgeler ({request.kyc_documents.length})</span>
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {request.kyc_documents.map((doc, index) => (
                              <a
                                key={index}
                                href={`${process.env.REACT_APP_BACKEND_URL || ''}${doc.path}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="group relative bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border-2 border-blue-200 hover:border-blue-400 hover:shadow-lg transition-all duration-200"
                              >
                                <div className="flex flex-col items-center text-center space-y-3">
                                  <div className="text-5xl transform group-hover:scale-110 transition-transform">
                                    {doc.type === 'license' && '🪪'}
                                    {doc.type === 'id_card' && '👤'}
                                    {doc.type === 'vehicle_registration' && '📋'}
                                    {doc.type === 'business_photo' && '🏪'}
                                  </div>
                                  <div className="w-full">
                                    <div className="font-semibold text-gray-900 mb-1">
                                      {doc.type === 'license' && 'Ehliyet'}
                                      {doc.type === 'id_card' && 'Kimlik'}
                                      {doc.type === 'vehicle_registration' && 'Araç Ruhsatı'}
                                      {doc.type === 'business_photo' && 'İşletme Fotoğrafı'}
                                    </div>
                                    <div className="text-xs text-gray-600 break-all">{doc.filename}</div>
                                  </div>
                                  <div className="flex items-center space-x-1 text-blue-600 text-sm font-medium">
                                    <span>Görüntüle</span>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                  </div>
                                </div>
                                <div className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                                  ✓
                                </div>
                              </a>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="mb-6">
                          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center space-x-2">
                            <span>📄</span>
                            <span>Yüklenen Belgeler</span>
                          </h4>
                          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
                            <div className="flex items-start space-x-3">
                              <span className="text-2xl">⚠️</span>
                              <div>
                                <p className="font-semibold text-red-900">Belge Yüklenmemiş!</p>
                                <p className="text-sm text-red-700 mt-1">
                                  Bu kullanıcı kayıt sırasında gerekli belgeleri yüklememiş. Başvuruyu reddetmeyi veya kullanıcıdan belge istemegi düşünün.
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Created Date */}
                      <div className="text-xs text-gray-400">
                        Başvuru: {new Date(request.created_at).toLocaleString('tr-TR')}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col space-y-2 ml-4">
                      <button
                        onClick={() => handleAction(request.id, 'approve')}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                      >
                        <span>✓</span>
                        <span>Onayla</span>
                      </button>
                      <button
                        onClick={() => handleAction(request.id, 'reject')}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
                      >
                        <span>✗</span>
                        <span>Reddet</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminKYC;
