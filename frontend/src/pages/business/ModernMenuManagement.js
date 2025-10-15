import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Plus, Edit, Trash2, Eye, EyeOff, Search, Filter, X, Package } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { get, post, patch, del } from '../../api/http';

const CATEGORIES = [
  'Yemek',
  'Kahvaltı',
  'İçecek',
  'Atıştırmalık'
];

const VAT_RATES = [
  { value: 0, label: 'KDV Yok (0%)' },
  { value: 0.08, label: 'İndirdirilmiş (%8)' },
  { value: 0.10, label: 'Genel (%10)' },
  { value: 0.18, label: 'Standart (%18)' }
];

export const ModernMenuManagement = ({ businessId, onStatsUpdate }) => {
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
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
    preparation_time: 15
  });

  useEffect(() => {
    fetchMenuItems();
  }, []);

  const fetchMenuItems = async () => {
    try {
      setLoading(true);
      console.log('🔄 Fetching menu items...');
      const response = await get('/business/menu');
      console.log('📦 Response status:', response.status, response.ok);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const items = await response.json();
      console.log('📦 Parsed JSON items:', items, 'Length:', items?.length);
      
      const menuArray = Array.isArray(items) ? items : [];
      console.log('📦 Final menu array:', menuArray.length, 'items');
      
      setMenuItems(menuArray);
      console.log('✅ Menu loaded successfully!', menuArray.length, 'items');
      
      // Also trigger stats update if callback provided
      if (onStatsUpdate) {
        console.log('🔄 Triggering stats update...');
        onStatsUpdate();
      }
    } catch (error) {
      console.error('❌ Menu loading error:', error);
      toast.error('Menü yüklenemedi: ' + error.message);
      setMenuItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!formData.name || !formData.price) {
      toast.error('Ürün adı ve fiyat zorunludur');
      return;
    }

    try {
      setLoading(true);

      const data = {
        ...formData,
        price: parseFloat(formData.price),
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
        vat_rate: parseFloat(formData.vat_rate),
        preparation_time: parseInt(formData.preparation_time) || 15
      };

      let response;
      if (editingItem) {
        response = await patch(`/business/menu/${editingItem.id}`, data);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        toast.success('Ürün güncellendi!');
      } else {
        response = await post('/business/menu', data);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        toast.success('Ürün eklendi!');
      }

      await fetchMenuItems();
      handleCloseModal();
    } catch (error) {
      console.error('Save error:', error);
      toast.error(error.response?.data?.detail || 'Kaydetme hatası');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name || '',
      description: item.description || '',
      price: item.price?.toString() || '',
      currency: item.currency || 'TRY',
      category: item.category || 'Ana Yemekler',
      tags: Array.isArray(item.tags) ? item.tags.join(', ') : '',
      image_url: item.image_url || '',
      is_available: item.is_available !== false,
      vat_rate: item.vat_rate || 0.10,
      preparation_time: item.preparation_time || 15
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bu ürünü silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const response = await del(`/business/menu/${id}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      toast.success('Ürün silindi');
      await fetchMenuItems();
    } catch (error) {
      toast.error('Silme hatası: ' + error.message);
    }
  };

  const handleToggleAvailability = async (item) => {
    try {
      const response = await patch(`/business/menu/${item.id}`, {
        ...item,
        is_available: !item.is_available
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      toast.success(item.is_available ? 'Ürün stokta yok olarak işaretlendi' : 'Ürün tekrar stokta');
      await fetchMenuItems();
    } catch (error) {
      toast.error('Güncelleme hatası: ' + error.message);
    }
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
      preparation_time: 15
    });
  };

  // Filter menu items
  const filteredItems = menuItems.filter(item => {
    const matchesSearch = !searchQuery || 
      item.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.description?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  // Group by category
  const groupedItems = {};
  filteredItems.forEach(item => {
    const cat = item.category || 'Diğer';
    if (!groupedItems[cat]) groupedItems[cat] = [];
    groupedItems[cat].push(item);
  });

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Menü Yönetimi</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {menuItems.length} ürün • {filteredItems.length} gösteriliyor
          </p>
        </div>
        <Button
          onClick={() => {
            setEditingItem(null);
            setShowModal(true);
          }}
          className="bg-primary hover:bg-primary-hover"
        >
          <Plus className="h-4 w-4 mr-2" />
          Yeni Ürün
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Ürün ara..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Category Filter */}
            <div className="sm:w-64">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full h-10 px-3 border border-border rounded-md bg-background text-foreground"
              >
                <option value="all">Tüm Kategoriler</option>
                {CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Menu Items by Category - All states always rendered */}
      
      {/* Loading State */}
      <div style={{ display: loading ? 'flex' : 'none' }} className="justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>

      {/* Empty State */}
      <Card style={{ display: !loading && Object.keys(groupedItems).length === 0 ? 'block' : 'none' }}>
        <CardContent className="text-center py-12">
          <Package className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Henüz ürün eklemediniz</h3>
          <p className="text-muted-foreground mb-6">
            İlk ürününüzü ekleyerek başlayın
          </p>
          <Button onClick={() => setShowModal(true)} className="bg-primary hover:bg-primary-hover">
            <Plus className="h-4 w-4 mr-2" />
            İlk Ürünü Ekle
          </Button>
        </CardContent>
      </Card>

      {/* Menu Items List */}
      <div style={{ display: !loading && Object.keys(groupedItems).length > 0 ? 'block' : 'none' }} className="space-y-6">
          {Object.entries(groupedItems).map(([category, items]) => (
            <div key={category}>
              <h2 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                <div className="h-1 w-12 bg-primary rounded-full"></div>
                {category}
                <span className="text-sm font-normal text-muted-foreground">({items.length})</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {items.map((item) => (
                  <Card key={item.id} className={`card-hover-lift ${!item.is_available ? 'opacity-60' : ''}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-semibold text-foreground mb-1">{item.name}</h3>
                          {item.description && (
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {item.description}
                            </p>
                          )}
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                          item.is_available
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        }`}>
                          {item.is_available ? 'Stokta' : 'Stok Yok'}
                        </div>
                      </div>

                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-bold text-primary">
                            ₺{item.price?.toFixed(2)}
                          </span>
                          {item.vat_rate > 0 && (
                            <span className="text-xs text-muted-foreground">
                              +KDV %{(item.vat_rate * 100).toFixed(0)}
                            </span>
                          )}
                        </div>
                        {item.preparation_time && (
                          <span className="text-xs text-muted-foreground">
                            ⏱️ {item.preparation_time} dk
                          </span>
                        )}
                      </div>

                      {item.tags && item.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-3">
                          {item.tags.slice(0, 3).map((tag, idx) => (
                            <span key={idx} className="px-2 py-0.5 bg-secondary text-xs rounded-full">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="flex gap-2">
                        <Button
                          onClick={() => handleEdit(item)}
                          variant="outline"
                          size="sm"
                          className="flex-1"
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          Düzenle
                        </Button>
                        <Button
                          onClick={() => handleToggleAvailability(item)}
                          variant="outline"
                          size="sm"
                        >
                          {item.is_available ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                        <Button
                          onClick={() => handleDelete(item.id)}
                          variant="outline"
                          size="sm"
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal */}
      <div 
        style={{ display: showModal ? 'flex' : 'none' }}
        className="fixed inset-0 bg-black/50 items-center justify-center z-50 p-4"
      >
        {showModal && (
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>
                  {editingItem ? 'Ürün Düzenle' : 'Yeni Ürün Ekle'}
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={handleCloseModal}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Name */}
                <div>
                  <Label htmlFor="name">Ürün Adı *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Örn: Margherita Pizza"
                    required
                  />
                </div>

                {/* Description */}
                <div>
                  <Label htmlFor="description">Açıklama</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Ürün açıklaması..."
                    rows={3}
                  />
                </div>

                {/* Price & Category */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="price">Fiyat (₺) *</Label>
                    <Input
                      id="price"
                      type="number"
                      step="0.01"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                      placeholder="99.90"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="category">Kategori</Label>
                    <select
                      id="category"
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      className="w-full h-10 px-3 border border-border rounded-md bg-background"
                    >
                      {CATEGORIES.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* VAT & Prep Time */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="vat_rate">KDV Oranı</Label>
                    <select
                      id="vat_rate"
                      value={formData.vat_rate}
                      onChange={(e) => setFormData({ ...formData, vat_rate: e.target.value })}
                      className="w-full h-10 px-3 border border-border rounded-md bg-background"
                    >
                      {VAT_RATES.map(rate => (
                        <option key={rate.value} value={rate.value}>{rate.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="prep_time">Hazırlık Süresi (dk)</Label>
                    <Input
                      id="prep_time"
                      type="number"
                      value={formData.preparation_time}
                      onChange={(e) => setFormData({ ...formData, preparation_time: e.target.value })}
                      placeholder="15"
                    />
                  </div>
                </div>

                {/* Tags */}
                <div>
                  <Label htmlFor="tags">Etiketler</Label>
                  <Input
                    id="tags"
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                    placeholder="vegan, acı, popüler (virgülle ayırın)"
                  />
                </div>

                {/* Image URL */}
                <div>
                  <Label htmlFor="image_url">Görsel URL</Label>
                  <Input
                    id="image_url"
                    value={formData.image_url}
                    onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                    placeholder="https://..."
                  />
                </div>

                {/* Available */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_available"
                    checked={formData.is_available}
                    onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  <Label htmlFor="is_available" className="cursor-pointer">
                    Stokta mevcut
                  </Label>
                </div>

                {/* Buttons */}
                <div className="flex gap-3 pt-4">
                  <Button
                    type="submit"
                    className="flex-1 bg-primary hover:bg-primary-hover"
                    disabled={loading}
                  >
                    {loading ? 'Kaydediliyor...' : editingItem ? 'Güncelle' : 'Ekle'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCloseModal}
                    disabled={loading}
                  >
                    İptal
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
