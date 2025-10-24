// Admin Coupon Management Component
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Plus, Edit, Trash2, Ticket } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const AdminCoupons = () => {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    title: '',
    description: '',
    type: 'percent',
    scope: 'item',
    value: 10,
    min_basket: null,
    valid_from: new Date().toISOString().slice(0, 16),
    valid_to: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    is_active: true
  });

  useEffect(() => {
    fetchCoupons();
  }, []);

  const fetchCoupons = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/admin/coupons`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setCoupons(data);
        console.log('✅ Loaded coupons:', data.length);
      } else {
        console.error('❌ Failed to fetch coupons:', response.status);
      }
    } catch (error) {
      console.error('❌ Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const createCoupon = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/coupons`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          valid_from: new Date(formData.valid_from).toISOString(),
          valid_to: new Date(formData.valid_to).toISOString()
        })
      });

      if (response.ok) {
        toast.success('Kupon oluşturuldu!');
        setShowCreateModal(false);
        fetchCoupons();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Kupon oluşturulamadı');
      }
    } catch (error) {
      console.error('❌ Error:', error);
      toast.error('Bir hata oluştu');
    }
  };

  const deleteCoupon = async (id) => {
    if (!confirm('Bu kuponu silmek istediğinizden emin misiniz?')) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/coupons/${id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success('Kupon silindi');
        fetchCoupons();
      } else {
        toast.error('Kupon silinemedi');
      }
    } catch (error) {
      console.error('❌ Error:', error);
      toast.error('Bir hata oluştu');
    }
  };

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Kupon Yönetimi</h2>
          <p className="text-muted-foreground">İndirim kuponlarını oluşturun ve yönetin</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Yeni Kupon
        </Button>
      </div>

      {/* Coupons List */}
      {loading ? (
        <Card>
          <CardContent className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          </CardContent>
        </Card>
      ) : coupons.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Ticket className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Henüz kupon yok</h3>
            <p className="text-muted-foreground mb-4">İlk kuponunuzu oluşturun</p>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Kupon Oluştur
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {coupons.map((coupon) => (
            <Card key={coupon.id}>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-bold text-lg">{coupon.code}</h3>
                      <p className="text-sm text-muted-foreground">{coupon.title}</p>
                    </div>
                    <Badge variant={coupon.is_active ? 'success' : 'secondary'}>
                      {coupon.is_active ? 'Aktif' : 'Pasif'}
                    </Badge>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{coupon.type === 'percent' ? 'Yüzde' : 'Sabit'}</Badge>
                    <Badge variant="outline">{coupon.scope === 'item' ? 'Ürün' : 'Sepet'}</Badge>
                    <span className="font-bold text-green-600">
                      {coupon.type === 'percent' ? `%${coupon.value}` : `₺${coupon.value}`}
                    </span>
                  </div>

                  <div className="text-xs text-muted-foreground">
                    <p>Geçerlilik: {new Date(coupon.valid_from).toLocaleDateString()} - {new Date(coupon.valid_to).toLocaleDateString()}</p>
                    <p>Kullanım: {coupon.current_uses || 0} / {coupon.global_limit || '∞'}</p>
                  </div>

                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1" disabled>
                      <Edit className="h-3 w-3 mr-1" />
                      Düzenle
                    </Button>
                    <Button 
                      variant="destructive" 
                      size="sm" 
                      onClick={() => deleteCoupon(coupon.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowCreateModal(false)}>
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <CardTitle>Yeni Kupon Oluştur</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-1 block">Kupon Kodu *</label>
                  <input
                    type="text"
                    value={formData.code}
                    onChange={(e) => setFormData({...formData, code: e.target.value.toUpperCase()})}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="YENI10"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">Başlık *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                    placeholder="Yeni Üye İndirimi"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-1 block">Açıklama</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium mb-1 block">Tip</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({...formData, type: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="percent">Yüzde (%)</option>
                    <option value="fixed">Sabit (₺)</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">Kapsam</label>
                  <select
                    value={formData.scope}
                    onChange={(e) => setFormData({...formData, scope: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="item">Ürün Bazlı</option>
                    <option value="cart">Sepet Toplamı</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">Değer *</label>
                  <input
                    type="number"
                    value={formData.value}
                    onChange={(e) => setFormData({...formData, value: parseFloat(e.target.value)})}
                    className="w-full px-3 py-2 border rounded-lg"
                    min="0"
                    step="0.01"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-1 block">Başlangıç Tarihi</label>
                  <input
                    type="datetime-local"
                    value={formData.valid_from}
                    onChange={(e) => setFormData({...formData, valid_from: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">Bitiş Tarihi</label>
                  <input
                    type="datetime-local"
                    value={formData.valid_to}
                    onChange={(e) => setFormData({...formData, valid_to: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={createCoupon} className="flex-1">Oluştur</Button>
                <Button variant="outline" onClick={() => setShowCreateModal(false)}>İptal</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default AdminCoupons;
