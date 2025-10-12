import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import api from '../api/http';

const AdBoardManager = () => {
  const [adBoards, setAdBoards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    subtitle: '',
    image: '',
    cta: { text: '', href: '' },
    order: 0,
    is_active: true
  });
  const [editingId, setEditingId] = useState(null);

  useEffect(() => {
    fetchAdBoards();
  }, []);

  const fetchAdBoards = async () => {
    try {
      setLoading(true);
      const response = await api.get('/admin/adboards');
      const data = await response.json();
      setAdBoards(data);
    } catch (error) {
      console.error('Error fetching ad boards:', error);
      alert('Reklam panoları yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      
      const url = editingId ? `/admin/adboards/${editingId}` : '/admin/adboards';
      const method = editingId ? 'PATCH' : 'POST';
      
      const response = await api(url, {
        method,
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        alert(editingId ? 'Reklam güncellendi!' : 'Reklam oluşturuldu!');
        setShowForm(false);
        setEditingId(null);
        setFormData({
          title: '',
          subtitle: '',
          image: '',
          cta: { text: '', href: '' },
          order: 0,
          is_active: true
        });
        fetchAdBoards();
      } else {
        const error = await response.json();
        alert(error.detail || 'Hata oluştu');
      }
    } catch (error) {
      console.error('Error saving ad board:', error);
      alert('Kaydetme hatası');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (board) => {
    setEditingId(board.id);
    setFormData({
      title: board.title,
      subtitle: board.subtitle || '',
      image: board.image,
      cta: board.cta || { text: '', href: '' },
      order: board.order,
      is_active: board.is_active
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Bu reklamı silmek istediğinizden emin misiniz?')) return;
    
    try {
      setLoading(true);
      const response = await api(`/admin/adboards/${id}`, { method: 'DELETE' });
      
      if (response.ok) {
        alert('Reklam silindi');
        fetchAdBoards();
      } else {
        alert('Silme hatası');
      }
    } catch (error) {
      console.error('Error deleting ad board:', error);
      alert('Silme hatası');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">📢 Reklam Panosu Yönetimi</h2>
        <Button onClick={() => {
          setShowForm(!showForm);
          setEditingId(null);
          setFormData({
            title: '',
            subtitle: '',
            image: '',
            cta: { text: '', href: '' },
            order: 0,
            is_active: true
          });
        }}>
          {showForm ? 'İptal' : '+ Yeni Reklam Ekle'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? 'Reklamı Düzenle' : 'Yeni Reklam Ekle'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>Başlık *</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  required
                />
              </div>

              <div>
                <Label>Alt Başlık</Label>
                <Input
                  value={formData.subtitle}
                  onChange={(e) => setFormData({...formData, subtitle: e.target.value})}
                />
              </div>

              <div>
                <Label>Görsel URL *</Label>
                <Input
                  value={formData.image}
                  onChange={(e) => setFormData({...formData, image: e.target.value})}
                  placeholder="/assets/ads/banner.png"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>CTA Metni</Label>
                  <Input
                    value={formData.cta.text}
                    onChange={(e) => setFormData({
                      ...formData,
                      cta: {...formData.cta, text: e.target.value}
                    })}
                    placeholder="Detaylar"
                  />
                </div>
                <div>
                  <Label>CTA Linki</Label>
                  <Input
                    value={formData.cta.href}
                    onChange={(e) => setFormData({
                      ...formData,
                      cta: {...formData.cta, href: e.target.value}
                    })}
                    placeholder="/campaigns"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Sıralama</Label>
                  <Input
                    type="number"
                    value={formData.order}
                    onChange={(e) => setFormData({...formData, order: parseInt(e.target.value)})}
                  />
                </div>
                <div className="flex items-center space-x-2 pt-6">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    className="w-4 h-4"
                  />
                  <Label>Aktif</Label>
                </div>
              </div>

              <Button type="submit" disabled={loading}>
                {loading ? 'Kaydediliyor...' : 'Kaydet'}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {adBoards.map((board) => (
          <Card key={board.id} className={board.is_active ? '' : 'opacity-50'}>
            <CardContent className="p-4">
              <div className="aspect-video bg-gray-100 mb-3 rounded overflow-hidden">
                {board.image && (
                  <img src={board.image} alt={board.title} className="w-full h-full object-cover" />
                )}
              </div>
              
              <h3 className="font-bold text-lg">{board.title}</h3>
              {board.subtitle && <p className="text-sm text-gray-600">{board.subtitle}</p>}
              
              <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
                <span>👁️ {board.impressions} | 👆 {board.clicks}</span>
                <span className={board.is_active ? 'text-green-600' : 'text-red-600'}>
                  {board.is_active ? '✓ Aktif' : '✗ Pasif'}
                </span>
              </div>

              <div className="mt-4 flex space-x-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(board)}
                >
                  Düzenle
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleDelete(board.id)}
                >
                  Sil
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {adBoards.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          Henüz reklam panosu eklenmemiş. Yukarıdan yeni reklam ekleyebilirsiniz.
        </div>
      )}
    </div>
  );
};

export default AdBoardManager;
