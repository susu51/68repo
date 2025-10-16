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

                      {/* Details Grid */}
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                        <div>
                          <div className="text-xs text-gray-500">Telefon</div>
                          <div className="text-sm font-medium text-gray-900">{request.phone}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500">Şehir</div>
                          <div className="text-sm font-medium text-gray-900">{request.city}</div>
                        </div>
                        {request.district && (
                          <div>
                            <div className="text-xs text-gray-500">İlçe</div>
                            <div className="text-sm font-medium text-gray-900">{request.district}</div>
                          </div>
                        )}
                        {request.vehicle_type && (
                          <div>
                            <div className="text-xs text-gray-500">Araç Tipi</div>
                            <div className="text-sm font-medium text-gray-900">{request.vehicle_type}</div>
                          </div>
                        )}
                        {request.business_name && (
                          <div>
                            <div className="text-xs text-gray-500">İşletme Adı</div>
                            <div className="text-sm font-medium text-gray-900">{request.business_name}</div>
                          </div>
                        )}
                        {request.business_tax_id && (
                          <div>
                            <div className="text-xs text-gray-500">Vergi No</div>
                            <div className="text-sm font-medium text-gray-900">{request.business_tax_id}</div>
                          </div>
                        )}
                      </div>

                      {/* Documents */}
                      {request.kyc_documents && request.kyc_documents.length > 0 && (
                        <div className="mb-4">
                          <div className="text-xs text-gray-500 mb-2">Yüklenen Belgeler</div>
                          <div className="flex flex-wrap gap-2">
                            {request.kyc_documents.map((doc, index) => (
                              <a
                                key={index}
                                href={`${process.env.REACT_APP_BACKEND_URL || ''}${doc.path}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center space-x-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
                              >
                                <span>📄</span>
                                <span className="text-sm">{doc.type === 'license' ? 'Ehliyet' : doc.type === 'id_card' ? 'Kimlik' : doc.type === 'vehicle_registration' ? 'Ruhsat' : 'İşletme Fotoğrafı'}</span>
                              </a>
                            ))}
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
