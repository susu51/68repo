import React, { useState, useEffect } from 'react';
import { api } from '../api/http';
import toast from 'react-hot-toast';
import { TURKEY_CITIES } from '../data/turkeyLocations';

const AdminAdvertisements = () => {
  const [advertisements, setAdvertisements] = useState([]);
  const [businesses, setBusinesses] = useState([]);
  const [filteredBusinesses, setFilteredBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedAd, setSelectedAd] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    business_id: '',
    business_name: '',
    title: '',
    city: '',
    district: '',
    image: null
  });

  // Get cities list
  const cities = Object.keys(TURKEY_CITIES).sort();

  useEffect(() => {
    fetchAdvertisements();
    fetchBusinesses();
  }, []);

  const fetchAdvertisements = async () => {
    try {
      const response = await api('/admin/advertisements');
      const data = await response.json();
      if (data.success) {
        setAdvertisements(data.advertisements);
      }
    } catch (error) {
      console.error('Error fetching advertisements:', error);
      toast.error('Reklamlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchBusinesses = async () => {
    try {
      const response = await api('/admin/businesses');
      const data = await response.json();
      if (data.success || data.businesses) {
        const businessList = data.businesses || [];
        setBusinesses(businessList);
        setFilteredBusinesses(businessList);
      }
    } catch (error) {
      console.error('Error fetching businesses:', error);
    }
  };

  const handleCityChange = (e) => {
    const selectedCity = e.target.value;
    setFormData({
      ...formData,
      city: selectedCity,
      district: '',
      business_id: '',
      business_name: ''
    });

    // Filter businesses by selected city
    if (selectedCity) {
      const filtered = businesses.filter(b => 
        b.city && b.city.toLowerCase() === selectedCity.toLowerCase()
      );
      setFilteredBusinesses(filtered);
    } else {
      setFilteredBusinesses(businesses);
    }
  };

  const handleDistrictChange = (e) => {
    setFormData({ ...formData, district: e.target.value });
  };

  const handleBusinessChange = (e) => {
    const businessId = e.target.value;
    const business = filteredBusinesses.find(b => b.id === businessId);
    
    setFormData({
      ...formData,
      business_id: businessId,
      business_name: business?.business_name || business?.name || ''
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        toast.error('Lütfen sadece resim dosyası yükleyin');
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Resim boyutu en fazla 5MB olabilir');
        return;
      }
      setFormData({ ...formData, image: file });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.business_id || !formData.city || !formData.image) {
      toast.error('Lütfen tüm zorunlu alanları doldurun');
      return;
    }

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('business_id', formData.business_id);
      formDataToSend.append('business_name', formData.business_name);
      
      // Combine city and district for better targeting
      const locationStr = formData.district 
        ? `${formData.city} - ${formData.district}` 
        : formData.city;
      formDataToSend.append('city', locationStr);
      
      if (formData.title) {
        formDataToSend.append('title', formData.title);
      }
      formDataToSend.append('image', formData.image);

      const response = await api('/admin/advertisements', {
        method: 'POST',
        body: formDataToSend,
        headers: {} // Let browser set Content-Type with boundary
      });

      const data = await response.json();
      if (data.success) {
        toast.success('Reklam başarıyla oluşturuldu!');
        setShowModal(false);
        resetForm();
        fetchAdvertisements();
      } else {
        toast.error(data.message || 'Reklam oluşturulamadı');
      }
    } catch (error) {
      console.error('Error creating advertisement:', error);
      toast.error('Reklam oluşturulurken hata oluştu');
    }
  };

  const handleToggleStatus = async (adId, currentStatus) => {
    try {
      const response = await api(`/admin/advertisements/${adId}/toggle`, {
        method: 'PATCH'
      });

      const data = await response.json();
      if (data.success) {
        toast.success(`Reklam ${data.is_active ? 'aktif' : 'pasif'} edildi`);
        fetchAdvertisements();
      }
    } catch (error) {
      console.error('Error toggling status:', error);
      toast.error('Durum değiştirilemedi');
    }
  };

  const handleDelete = async (adId) => {
    if (!window.confirm('Bu reklamı silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const response = await api(`/admin/advertisements/${adId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        toast.success('Reklam silindi');
        fetchAdvertisements();
      }
    } catch (error) {
      console.error('Error deleting advertisement:', error);
      toast.error('Reklam silinemedi');
    }
  };

  const resetForm = () => {
    setFormData({
      business_id: '',
      business_name: '',
      title: '',
      city: '',
      district: '',
      image: null
    });
    setFilteredBusinesses(businesses);
  };

  const openModal = () => {
    resetForm();
    setShowModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-3 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-4 sm:mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex-1">
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900">Reklam Yönetimi</h1>
            <p className="text-xs sm:text-sm text-gray-600 mt-1 sm:mt-2">Müşteri panelinde gösterilecek restoran reklamlarını yönetin</p>
          </div>
          <button
            onClick={openModal}
            className="w-full sm:w-auto px-4 sm:px-6 py-2 sm:py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center justify-center space-x-2 text-sm sm:text-base"
          >
            <span>➕</span>
            <span>Yeni Reklam</span>
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Toplam Reklam</div>
            <div className="text-3xl font-bold text-gray-800">{advertisements.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Aktif Reklam</div>
            <div className="text-3xl font-bold text-green-600">
              {advertisements.filter(ad => ad.is_active).length}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Pasif Reklam</div>
            <div className="text-3xl font-bold text-red-600">
              {advertisements.filter(ad => !ad.is_active).length}
            </div>
          </div>
        </div>

        {/* Advertisements List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Reklamlar</h2>
          </div>

          {advertisements.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-5xl mb-4">📢</div>
              <p>Henüz reklam eklenmemiş</p>
              <button
                onClick={openModal}
                className="mt-4 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
              >
                İlk Reklamı Oluştur
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {advertisements.map((ad) => (
                <div key={ad.id} className="p-3 sm:p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex flex-col sm:flex-row items-start gap-3 sm:gap-4">
                    {/* Image Preview */}
                    <div className="flex-shrink-0 w-full sm:w-auto">
                      <img
                        src={`${process.env.REACT_APP_BACKEND_URL || ''}${ad.image_url}`}
                        alt={ad.title || ad.business_name}
                        className="w-full sm:w-32 h-32 sm:h-20 object-cover rounded-lg border-2 border-gray-200"
                      />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <h3 className="text-base sm:text-lg font-semibold text-gray-900 break-words">{ad.business_name}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded whitespace-nowrap ${
                          ad.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {ad.is_active ? 'Aktif' : 'Pasif'}
                        </span>
                      </div>
                      {ad.title && (
                        <p className="text-xs sm:text-sm text-gray-600 mb-2 break-words">📝 {ad.title}</p>
                      )}
                      <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-500">
                        <span className="whitespace-nowrap">📍 {ad.city}</span>
                        <span className="break-all text-[10px] sm:text-xs">🆔 {ad.business_id.slice(0, 8)}...</span>
                        <span className="whitespace-nowrap">📅 {new Date(ad.created_at).toLocaleDateString('tr-TR')}</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex sm:flex-col gap-2 w-full sm:w-auto">
                      <button
                        onClick={() => handleToggleStatus(ad.id, ad.is_active)}
                        className={`flex-1 sm:flex-none px-3 sm:px-4 py-2 rounded-lg transition-colors flex items-center justify-center space-x-1 sm:space-x-2 text-xs sm:text-sm ${
                          ad.is_active
                            ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                            : 'bg-green-600 text-white hover:bg-green-700'
                        }`}
                      >
                        <span>{ad.is_active ? '⏸️' : '▶️'}</span>
                        <span className="whitespace-nowrap">{ad.is_active ? 'Pasif' : 'Aktif'}</span>
                      </button>
                      <button
                        onClick={() => handleDelete(ad.id)}
                        className="flex-1 sm:flex-none px-3 sm:px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center space-x-1 sm:space-x-2 text-xs sm:text-sm"
                      >
                        <span>🗑️</span>
                        <span>Sil</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[95vh] sm:max-h-[90vh] overflow-y-auto">
            <div className="p-4 sm:p-6 border-b border-gray-200">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Yeni Reklam Oluştur</h2>
            </div>

            <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-3 sm:space-y-4">
              {/* City Selection */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
                  İl Seçin <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.city}
                  onChange={handleCityChange}
                  className="w-full px-3 sm:px-4 py-2 text-sm sm:text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  required
                >
                  <option value="">-- İl Seçin --</option>
                  {cities.map(city => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>

              {/* District Selection */}
              {formData.city && (
                <div>
                  <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
                    İlçe Seçin (Opsiyonel)
                  </label>
                  <select
                    value={formData.district}
                    onChange={handleDistrictChange}
                    className="w-full px-3 sm:px-4 py-2 text-sm sm:text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="">-- Tüm İlçeler (İl geneli) --</option>
                    {TURKEY_CITIES[formData.city]?.map(district => (
                      <option key={district} value={district}>{district}</option>
                    ))}
                  </select>
                  <p className="text-[10px] sm:text-xs text-gray-500 mt-1">
                    İlçe seçmezseniz il genelinde gösterilir
                  </p>
                </div>
              )}

              {/* Business Selection */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
                  Restoran Seçin <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.business_id}
                  onChange={handleBusinessChange}
                  className="w-full px-3 sm:px-4 py-2 text-sm sm:text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  required
                  disabled={!formData.city}
                >
                  <option value="">
                    {formData.city 
                      ? `-- ${formData.city} İlindeki Restoranlar --` 
                      : '-- Önce İl Seçin --'}
                  </option>
                  {filteredBusinesses.map(business => (
                    <option key={business.id} value={business.id}>
                      {business.business_name || business.name}
                    </option>
                  ))}
                </select>
                {formData.city && filteredBusinesses.length === 0 && (
                  <p className="text-[10px] sm:text-xs text-red-500 mt-1">
                    ⚠️ {formData.city} ilinde kayıtlı restoran bulunamadı
                  </p>
                )}
              </div>

              {/* Title/Slogan */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
                  Reklam Başlığı/Slogan (Opsiyonel)
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 sm:px-4 py-2 text-sm sm:text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  placeholder="Örn: Yılın En İyi Pizzası!"
                />
              </div>

              {/* Image Upload */}
              <div>
                <label className="block text-xs sm:text-sm font-medium text-gray-700 mb-1 sm:mb-2">
                  Reklam Görseli <span className="text-red-500">*</span>
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className="w-full px-3 sm:px-4 py-2 text-xs sm:text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  required
                />
                <p className="text-[10px] sm:text-xs text-gray-500 mt-1">
                  Yatay banner için ideal boyut: 1200x400px (Maksimum 5MB)
                </p>
                {formData.image && (
                  <div className="mt-2">
                    <img
                      src={URL.createObjectURL(formData.image)}
                      alt="Preview"
                      className="w-full h-24 sm:h-32 object-cover rounded-lg border-2 border-gray-200"
                    />
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row justify-end gap-2 sm:gap-3 pt-3 sm:pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="w-full sm:w-auto px-4 py-2 text-sm sm:text-base text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 order-2 sm:order-1"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  className="w-full sm:w-auto px-4 py-2 text-sm sm:text-base bg-orange-600 text-white rounded-lg hover:bg-orange-700 order-1 sm:order-2"
                >
                  Reklam Oluştur
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAdvertisements;
