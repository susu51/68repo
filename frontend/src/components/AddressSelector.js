import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card.jsx';
import { Button } from './ui/button.jsx';
import { Input } from './ui/input.jsx';
import { Label } from './ui/label.jsx';
import { MapPin, Plus, Trash2, Edit2, Check } from 'lucide-react';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://food-dash-87.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const AddressSelector = ({ selectedAddress, onAddressSelect }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  const [formData, setFormData] = useState({
    label: '',
    full: '',
    city: '',
    district: '',
    lat: 0,
    lng: 0
  });

  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/customer/addresses`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setAddresses(data.addresses || []);
        
        if (!data.addresses || data.addresses.length === 0) {
          setShowAddForm(true);
        }
      }
    } catch (error) {
      console.error('Adres yükleme hatası:', error);
      toast.error('Adresler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAddress = async () => {
    try {
      if (!formData.label || !formData.full || !formData.city) {
        toast.error('Lütfen tüm alanları doldurun');
        return;
      }

      const method = editingId ? 'PUT' : 'POST';
      const url = editingId ? `${API}/customer/addresses/${editingId}` : `${API}/customer/addresses`;

      const response = await fetch(url, {
        method,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        toast.success(editingId ? 'Adres güncellendi' : 'Adres eklendi');
        setFormData({ label: '', full: '', city: '', district: '', lat: 0, lng: 0 });
        setShowAddForm(false);
        setEditingId(null);
        fetchAddresses();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Adres kaydedilemedi');
      }
    } catch (error) {
      console.error('Adres kaydetme hatası:', error);
      toast.error('Bir hata oluştu');
    }
  };

  const handleDeleteAddress = async (id) => {
    if (!window.confirm('Bu adresi silmek istediğinizden emin misiniz?')) return;

    try {
      const response = await fetch(`${API}/customer/addresses/${id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success('Adres silindi');
        fetchAddresses();
      }
    } catch (error) {
      console.error('Adres silme hatası:', error);
      toast.error('Adres silinemedi');
    }
  };

  const handleEditAddress = (address) => {
    setFormData({
      label: address.label || '',
      full: address.full || '',
      city: address.city || '',
      district: address.district || '',
      lat: address.location?.coordinates?.[1] || 0,
      lng: address.location?.coordinates?.[0] || 0
    });
    setEditingId(address._id);
    setShowAddForm(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Teslimat Adresi Seç</h2>
        {!showAddForm && (
          <Button variant="outline" size="sm" onClick={() => setShowAddForm(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Yeni Adres
          </Button>
        )}
      </div>

      {showAddForm && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-lg">
              {editingId ? 'Adresi Düzenle' : 'Yeni Adres Ekle'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label htmlFor="label">Adres Başlığı</Label>
              <Input id="label" placeholder="Ev, İş, vb." value={formData.label}
                onChange={(e) => setFormData({ ...formData, label: e.target.value })} />
            </div>
            <div>
              <Label htmlFor="full">Tam Adres</Label>
              <textarea id="full" placeholder="Sokak, mahalle, bina no..." value={formData.full}
                onChange={(e) => setFormData({ ...formData, full: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" rows={3} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="city">Şehir</Label>
                <Input id="city" placeholder="İstanbul" value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })} />
              </div>
              <div>
                <Label htmlFor="district">İlçe</Label>
                <Input id="district" placeholder="Kadıköy" value={formData.district}
                  onChange={(e) => setFormData({ ...formData, district: e.target.value })} />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSaveAddress} className="flex-1">
                <Check className="h-4 w-4 mr-2" />
                Kaydet
              </Button>
              <Button variant="outline" onClick={() => {
                setShowAddForm(false);
                setEditingId(null);
                setFormData({ label: '', full: '', city: '', district: '', lat: 0, lng: 0 });
              }}>İptal</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {addresses.length === 0 && !showAddForm && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <MapPin className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Henüz kayıtlı adresiniz yok</p>
            <p className="text-sm mt-2">Lütfen bir adres ekleyin</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-3">
        {addresses.map((address) => (
          <Card key={address._id} className={`cursor-pointer transition-all ${
              selectedAddress?._id === address._id ? 'border-green-500 bg-green-50' : 'hover:border-gray-400'
            }`} onClick={() => onAddressSelect(address)}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <MapPin className="h-4 w-4 text-gray-500" />
                    <h3 className="font-semibold">{address.label}</h3>
                    {selectedAddress?._id === address._id && <Check className="h-5 w-5 text-green-600" />}
                  </div>
                  <p className="text-sm text-gray-600">{address.full}</p>
                  <p className="text-xs text-gray-500 mt-1">{address.district}, {address.city}</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={(e) => {
                    e.stopPropagation();
                    handleEditAddress(address);
                  }}>
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteAddress(address._id);
                  }}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};