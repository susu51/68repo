import React, { useState, useEffect } from 'react';
import { get, post, patch, del } from '../api/http';
import { toast } from 'react-hot-toast';
import { Plus, Edit2, Trash2, Eye, EyeOff, X } from 'lucide-react';

const CATEGORIES = ['Yemek', 'Kahvaltı', 'İçecek', 'Atıştırmalık'];
const VAT_RATES = [
  { value: 0, label: 'KDV Yok (0%)' },
  { value: 0.08, label: 'İndirdirilmiş KDV (%8)' },
  { value: 0.10, label: 'Genel KDV (%10)' },
  { value: 0.18, label: 'Standart KDV (%18)' }
];

export const BusinessMenuManager = ({ onMenuItemsChange }) => {
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    currency: 'TRY',
    category: 'Yemek',
    tags: '',
    image_url: '',
    is_available: true,
    vat_rate: 0.10,
    preparation_time: 15,
    options: []
  });

  const [optionForm, setOptionForm] = useState({ name: '', price: '' });

  useEffect(() => {
    fetchMenuItems();
  }, []);

  const fetchMenuItems = async () => {
    try {
      setLoading(true);
      const result = await get('/business/menu');
      console.log('📡 Raw API response:', result);
      
      // Handle both {data: [...]} and direct array responses
      const items = result.data || result || [];
      const menuArray = Array.isArray(items) ? items : [];
      
      setMenuItems(menuArray);
      console.log('✅ Menu items loaded:', menuArray.length, menuArray);
      
      // Notify parent component about menu items change
      if (onMenuItemsChange) {
        onMenuItemsChange(menuArray);
      }
    } catch (error) {
      console.error('❌ Error loading menu:', error);
      toast.error('Menü yüklenirken hata oluştu: ' + (error.message || 'Bilinmeyen hata'));
      setMenuItems([]);
      
      // Notify parent component about empty menu
      if (onMenuItemsChange) {
        onMenuItemsChange([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      
      // Prepare data
      const data = {
        ...formData,
        price: parseFloat(formData.price),
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
        vat_rate: parseFloat(formData.vat_rate),
        preparation_time: parseInt(formData.preparation_time) || 15
      };

      if (editingItem) {
        // Update existing item
        const result = await patch(`/business/menu/${editingItem.id}`, data);
        console.log('✅ Update response:', result);
        toast.success('Menü ürünü güncellendi!');
      } else {
        // Create new item
        const result = await post('/business/menu', data);
        console.log('✅ Create response:', result);
        toast.success('Menü ürünü eklendi!');
      }

      // Reload menu items
      await fetchMenuItems();
      
      // Small delay to ensure state update
      setTimeout(() => {
        handleCloseModal();
      }, 100);
    } catch (error) {
      console.error('Error saving menu item:', error);
      const errorMsg = error.message || error.response?.data?.detail || error.detail || 'Kaydetme hatası';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (itemId, itemName) => {
    if (!window.confirm(`"${itemName}" ürününü silmek istediğinize emin misiniz?`)) {
      return;
    }

    try {
      setLoading(true);
      // Soft delete by default
      await del(`/business/menu/${itemId}?soft_delete=true`);
      toast.success('Ürün devre dışı bırakıldı');
      await fetchMenuItems();
    } catch (error) {
      console.error('Error deleting menu item:', error);
      const errorMsg = error.message || error.detail || 'Silme hatası';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAvailability = async (item) => {
    try {
      setLoading(true);
      await patch(`/business/menu/${item.id}`, {
        is_available: !item.is_available
      });
      toast.success(item.is_available ? 'Ürün devre dışı' : 'Ürün aktif');
      await fetchMenuItems();
    } catch (error) {
      console.error('Error toggling availability:', error);
      const errorMsg = error.message || error.detail || 'Güncelleme hatası';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      description: item.description,
      price: item.price.toString(),
      currency: item.currency || 'TRY',
      category: item.category,
      tags: Array.isArray(item.tags) ? item.tags.join(', ') : '',
      image_url: item.image_url || '',
      is_available: item.is_available,
      vat_rate: item.vat_rate,
      preparation_time: item.preparation_time || 15,
      options: item.options || []
    });
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingItem(null);
    setFormData({
      name: '',
      description: '',
      price: '',
      currency: 'TRY',
      category: 'Yemek',
      tags: '',
      image_url: '',
      is_available: true,
      vat_rate: 0.10,
      preparation_time: 15,
      options: []
    });
    setOptionForm({ name: '', price: '' });
  };

  const handleAddOption = () => {
    if (!optionForm.name || !optionForm.price) {
      toast.error('Opsiyon adı ve fiyatı gerekli');
      return;
    }

    setFormData(prev => ({
      ...prev,
      options: [...prev.options, {
        name: optionForm.name,
        price: parseFloat(optionForm.price)
      }]
    }));

    setOptionForm({ name: '', price: '' });
    toast.success('Opsiyon eklendi');
  };

  const handleRemoveOption = (index) => {
    setFormData(prev => ({
      ...prev,
      options: prev.options.filter((_, i) => i !== index)
    }));
  };

  const filteredItems = selectedCategory === 'all' 
    ? menuItems 
    : menuItems.filter(item => item.category === selectedCategory);

  const categoryStats = CATEGORIES.reduce((acc, cat) => {
    acc[cat] = menuItems.filter(item => item.category === cat).length;
    return acc;
  }, {});

  return (
    <div className="p-4 md:p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Menü Yönetimi</h1>
          <p className="text-sm md:text-base text-gray-600 mt-1">Ürünlerinizi ekleyin, düzenleyin ve yönetin</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center justify-center gap-2 bg-orange-500 text-white px-4 md:px-6 py-3 rounded-lg hover:bg-orange-600 transition-colors font-semibold shadow-md w-full md:w-auto"
        >
          <Plus size={20} />
          Yeni Ürün Ekle
        </button>
      </div>

      {/* Category Filter */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedCategory === 'all'
                ? 'bg-orange-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Tümü ({menuItems.length})
          </button>
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                selectedCategory === cat
                  ? 'bg-orange-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat} ({categoryStats[cat] || 0})
            </button>
          ))}
        </div>
      </div>

      {/* Menu Items Grid */}
      {loading && menuItems.length === 0 ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Yükleniyor...</p>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-600 text-lg">
            {selectedCategory === 'all' 
              ? 'Henüz menü ürünü eklenmemiş' 
              : `${selectedCategory} kategorisinde ürün bulunamadı`}
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="mt-4 text-orange-500 hover:text-orange-600 font-medium"
          >
            İlk ürününüzü ekleyin
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredItems.map(item => (
            <div key={item.id} className={`bg-white rounded-lg shadow-md overflow-hidden transition-all hover:shadow-lg ${!item.is_available ? 'opacity-60' : ''}`}>
              {/* Image */}
              <div className="relative h-48 bg-gray-200">
                {item.image_url ? (
                  <img src={item.image_url} alt={item.name} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <span>Resim yok</span>
                  </div>
                )}
                {!item.is_available && (
                  <div className="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
                    Devre Dışı
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{item.name}</h3>
                  <span className="text-orange-600 font-bold text-lg">
                    {item.price.toFixed(2)} {item.currency}
                  </span>
                </div>

                <p className="text-gray-600 text-sm mb-3 line-clamp-2">{item.description}</p>

                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                    {item.category}
                  </span>
                  {item.tags && item.tags.length > 0 && item.tags.map((tag, idx) => (
                    <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                      #{tag}
                    </span>
                  ))}
                </div>

                <div className="flex gap-1 text-xs text-gray-500 mb-3">
                  <span>⏱️ {item.preparation_time} dk</span>
                  <span className="mx-2">•</span>
                  <span>KDV: %{(item.vat_rate * 100).toFixed(0)}</span>
                </div>

                {item.options && item.options.length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs text-gray-500 font-medium mb-1">Opsiyonlar:</p>
                    {item.options.map((opt, idx) => (
                      <span key={idx} className="text-xs text-gray-600 mr-2">
                        {opt.name} (+{opt.price} TL)
                      </span>
                    ))}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => handleEdit(item)}
                    className="flex-1 flex items-center justify-center gap-1 bg-blue-500 text-white px-3 py-2 rounded hover:bg-blue-600 transition-colors text-sm"
                  >
                    <Edit2 size={14} />
                    Düzenle
                  </button>
                  <button
                    onClick={() => handleToggleAvailability(item)}
                    className={`flex items-center justify-center gap-1 px-3 py-2 rounded transition-colors text-sm ${
                      item.is_available
                        ? 'bg-yellow-500 text-white hover:bg-yellow-600'
                        : 'bg-green-500 text-white hover:bg-green-600'
                    }`}
                  >
                    {item.is_available ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                  <button
                    onClick={() => handleDelete(item.id, item.name)}
                    className="flex items-center justify-center gap-1 bg-red-500 text-white px-3 py-2 rounded hover:bg-red-600 transition-colors text-sm"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingItem ? 'Ürün Düzenle' : 'Yeni Ürün Ekle'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Ürün Adı *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="Örn: Margarita Pizza"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Açıklama
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="Ürün açıklaması..."
                />
              </div>

              {/* Price and Category */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fiyat (TL) *
                  </label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Kategori *
                  </label>
                  <select
                    required
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    {CATEGORIES.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* VAT Rate and Prep Time */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    KDV Oranı *
                  </label>
                  <select
                    required
                    value={formData.vat_rate}
                    onChange={(e) => setFormData({ ...formData, vat_rate: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    {VAT_RATES.map(vat => (
                      <option key={vat.value} value={vat.value}>{vat.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Hazırlık Süresi (dakika)
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={formData.preparation_time}
                    onChange={(e) => setFormData({ ...formData, preparation_time: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Etiketler (virgülle ayırın)
                </label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="Örn: vegan, acılı, gluten-free"
                />
              </div>

              {/* Image URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Görsel URL
                </label>
                <input
                  type="url"
                  value={formData.image_url}
                  onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                  placeholder="https://..."
                />
              </div>

              {/* Options Section */}
              <div className="border-t pt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Opsiyonlar (Ekstra seçenekler)
                </label>
                
                {/* Existing Options */}
                {formData.options.length > 0 && (
                  <div className="mb-3 space-y-2">
                    {formData.options.map((opt, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-gray-50 p-2 rounded">
                        <span className="flex-1 text-sm">{opt.name}</span>
                        <span className="text-sm font-medium">+{opt.price} TL</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveOption(idx)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add Option Form */}
                <div className="grid grid-cols-3 gap-2">
                  <input
                    type="text"
                    placeholder="Opsiyon adı"
                    value={optionForm.name}
                    onChange={(e) => setOptionForm({ ...optionForm, name: e.target.value })}
                    className="col-span-2 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
                  />
                  <input
                    type="number"
                    placeholder="Fiyat"
                    min="0"
                    step="0.01"
                    value={optionForm.price}
                    onChange={(e) => setOptionForm({ ...optionForm, price: e.target.value })}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 text-sm"
                  />
                  <button
                    type="button"
                    onClick={handleAddOption}
                    className="col-span-3 bg-gray-200 text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
                  >
                    + Opsiyon Ekle
                  </button>
                </div>
              </div>

              {/* Available Toggle */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_available"
                  checked={formData.is_available}
                  onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                  className="w-4 h-4 text-orange-500 rounded focus:ring-orange-500"
                />
                <label htmlFor="is_available" className="text-sm font-medium text-gray-700">
                  Ürün aktif (Müşterilere göster)
                </label>
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Kaydediliyor...' : editingItem ? 'Güncelle' : 'Ekle'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessMenuManager;
