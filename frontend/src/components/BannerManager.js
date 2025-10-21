import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://ai-order-debug.preview.emergentagent.com/api';

export const BannerManager = () => {
  const [banners, setBanners] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    image_url: '',
    link_url: '',
    order: 0
  });

  useEffect(() => {
    fetchBanners();
  }, []);

  const fetchBanners = async () => {
    try {
      // Mock data
      setBanners([]);
    } catch (error) {
      console.error('Banners fetch error:', error);
    }
  };

  const handleCreate = async () => {
    try {
      // Create banner
      setBanners([...banners, { ...formData, id: Date.now() }]);
      toast.success('Reklam banner oluşturuldu');
      setShowForm(false);
      setFormData({ title: '', description: '', image_url: '', link_url: '', order: 0 });
    } catch (error) {
      toast.error('Banner oluşturulamadı');
    }
  };

  const handleDelete = (id) => {
    if (window.confirm('Bu banner\'ı silmek istediğinizden emin misiniz?')) {
      setBanners(banners.filter(b => b.id !== id));
      toast.success('Banner silindi');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">🎨 Anasayfa Reklam Yönetimi</h2>
        <Button onClick={() => setShowForm(!showForm)} className="bg-indigo-600">
          {showForm ? '❌ İptal' : '➕ Yeni Banner'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Yeni Reklam Banner Oluştur</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <input
                placeholder="Başlık"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <textarea
                placeholder="Açıklama"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                rows="3"
              />
              <input
                placeholder="Görsel URL"
                value={formData.image_url}
                onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <input
                placeholder="Link URL (opsiyonel)"
                value={formData.link_url}
                onChange={(e) => setFormData({ ...formData, link_url: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <input
                type="number"
                placeholder="Sıralama"
                value={formData.order}
                onChange={(e) => setFormData({ ...formData, order: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <Button onClick={handleCreate} className="bg-indigo-600">
                ✅ Banner Oluştur
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {banners.map((banner) => (
          <Card key={banner.id}>
            <CardContent className="p-4">
              {banner.image_url && (
                <img src={banner.image_url} alt={banner.title} className="w-full h-48 object-cover rounded-lg mb-3" />
              )}
              <h3 className="text-xl font-bold mb-2">{banner.title}</h3>
              <p className="text-gray-600 text-sm mb-3">{banner.description}</p>
              <div className="flex gap-2">
                <Button onClick={() => handleDelete(banner.id)} className="bg-red-500 flex-1">
                  🗑️ Sil
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {banners.length === 0 && (
        <Card className="bg-yellow-50">
          <CardContent className="p-8 text-center">
            <p className="text-5xl mb-4">🎨</p>
            <p className="text-gray-700">Henüz reklam banner yok. Slide gösterimi için banner ekleyin.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default BannerManager;