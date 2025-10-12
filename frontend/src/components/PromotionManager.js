import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import api from '../api/http';

const PromotionManager = () => {
  const [promotions, setPromotions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    title: '',
    description: '',
    discount_pct: 0,
    discount_amount: null,
    target: 'all',
    target_id: null,
    min_order: 0,
    usage_limit: null,
    usage_per_user: 1,
    start_date: '',
    end_date: '',
    is_active: true
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchPromotions();
  }, []);

  const fetchPromotions = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/promotions');
      const data = await response.json();
      setPromotions(data);
    } catch (error) {
      console.error('Error fetching promotions:', error);
      alert('Promosyonlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      
      const url = editingId ? `/admin/promotions/${editingId}` : '/admin/promotions';
      const method = editingId ? 'PATCH' : 'POST';
      
      const response = await api(url, {
        method,
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        alert(editingId ? 'Promosyon güncellendi!' : 'Promosyon oluşturuldu!');
        setShowForm(false);
        setEditingId(null);
        resetForm();
        fetchPromotions();
      } else {
        const error = await response.json();
        alert(error.detail || 'Hata oluştu');
      }
    } catch (error) {
      console.error('Error saving promotion:', error);
      alert('Kaydetme hatası');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      code: '',
      title: '',
      description: '',
      discount_pct: 0,
      discount_amount: null,
      target: 'all',
      target_id: null,
      min_order: 0,
      usage_limit: null,
      usage_per_user: 1,
      start_date: '',
      end_date: '',
      is_active: true
    });
  };

  const handleEdit = (promo) => {
    setEditingId(promo.id);
    setFormData({
      code: promo.code,
      title: promo.title,
      description: promo.description,
      discount_pct: promo.discount_pct || 0,
      discount_amount: promo.discount_amount,
      target: promo.target,
      target_id: promo.target_id,
      min_order: promo.min_order,
      usage_limit: promo.usage_limit,
      usage_per_user: promo.usage_per_user,
      start_date: promo.start_date ? promo.start_date.split('T')[0] : '',
      end_date: promo.end_date ? promo.end_date.split('T')[0] : '',
      is_active: promo.is_active
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bu promosyonu silmek istediğinizden emin misiniz?')) return;
    
    try {
      setLoading(true);
      const response = await api(`/admin/promotions/${id}`, { method: 'DELETE' });
      
      if (response.ok) {
        alert('Promosyon silindi');
        fetchPromotions();
      } else {
        alert('Silme hatası');
      }
    } catch (error) {
      console.error('Error deleting promotion:', error);
      alert('Silme hatası');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">🎁 Promosyon Yönetimi</h2>
        <Button onClick={() => {
          setShowForm(!showForm);
          setEditingId(null);
          resetForm();
        }}>
          {showForm ? 'İptal' : '+ Yeni Promosyon Ekle'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? 'Promosyonu Düzenle' : 'Yeni Promosyon Ekle'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Kupon Kodu *</Label>
                  <Input
                    value={formData.code}
                    onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase()})}
                    placeholder="KUPON10"
                    required
                    disabled={editingId}
                  />
                </div>
                <div>
                  <Label>Başlık *</Label>
                  <Input
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    required
                  />
                </div>
              </div>

              <div>
                <Label>Açıklama *</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>İndirim % (0-100)</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.discount_pct}
                    onChange={(e) => setFormData({...formData, discount_pct: parseFloat(e.target.value)})}
                  />
                </div>
                <div>
                  <Label>Minimum Sipariş Tutarı (TL)</Label>
                  <Input
                    type="number"
                    min="0"
                    value={formData.min_order}
                    onChange={(e) => setFormData({...formData, min_order: parseFloat(e.target.value)})}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Toplam Kullanım Limiti</Label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.usage_limit || ''}
                    onChange={(e) => setFormData({...formData, usage_limit: e.target.value ? parseInt(e.target.value) : null})}
                    placeholder="Sınırsız"
                  />
                </div>
                <div>
                  <Label>Kullanıcı Başına Limit</Label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.usage_per_user}
                    onChange={(e) => setFormData({...formData, usage_per_user: parseInt(e.target.value)})}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Başlangıç Tarihi *</Label>
                  <Input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>Bitiş Tarihi *</Label>
                  <Input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                    required
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="w-4 h-4"
                />
                <Label>Aktif</Label>
              </div>

              <Button type="submit" disabled={loading}>
                {loading ? 'Kaydediliyor...' : 'Kaydet'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4">
        {promotions.map((promo) => (
          <Card key={promo.id} className={promo.is_active ? '' : 'opacity-50'}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl font-bold text-orange-600">{promo.code}</span>
                    <span className={`px-2 py-1 rounded text-xs ${promo.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                      {promo.is_active ? 'Aktif' : 'Pasif'}
                    </span>
                  </div>
                  <h3 className="font-bold text-lg mt-1">{promo.title}</h3>
                  <p className="text-sm text-gray-600">{promo.description}</p>
                  
                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">İndirim:</span>
                      <span className="ml-1 font-semibold">%{promo.discount_pct}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Min. Tutar:</span>
                      <span className="ml-1 font-semibold">{promo.min_order} TL</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Kullanım:</span>
                      <span className="ml-1 font-semibold">{promo.used_count} / {promo.usage_limit || '∞'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Bitiş:</span>
                      <span className="ml-1 font-semibold">{new Date(promo.end_date).toLocaleDateString('tr-TR')}</span>
                    </div>
                  </div>
                </div>

                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleEdit(promo)}
                  >
                    Düzenle
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => handleDelete(promo.id)}
                  >
                    Sil
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {promotions.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          Henüz promosyon eklenmemiş. Yukarıdan yeni promosyon ekleyebilirsiniz.
        </div>
      )}
    </div>
  );
};

export default PromotionManager;
