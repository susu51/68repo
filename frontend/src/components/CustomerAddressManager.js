import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-ai.preview.emergentagent.com';

export const CustomerAddressManager = () => {
  const [addresses, setAddresses] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    street: '',
    building: '',
    floor: '',
    apartment: '',
    city: '',
    district: '',
    postal_code: '',
    lat: 0,
    lng: 0,
    is_default: false
  });

  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    try {
      const response = await axios.get(`${API_BASE}/customer/addresses`, {
        withCredentials: true
      });
      setAddresses(response.data.addresses || []);
    } catch (error) {
      console.error('Addresses fetch error:', error);
      toast.error('Adresler yüklenemedi');
    }
  };

  const handleAdd = async () => {
    if (!formData.title || !formData.street || !formData.city) {
      toast.error('Lütfen zorunlu alanları doldurun');
      return;
    }

    try {
      await axios.post(`${API_BASE}/customer/addresses`, formData, {
        withCredentials: true
      });
      toast.success('Adres eklendi');
      setShowForm(false);
      setFormData({
        title: '',
        street: '',
        building: '',
        floor: '',
        apartment: '',
        city: '',
        district: '',
        postal_code: '',
        lat: 0,
        lng: 0,
        is_default: false
      });
      fetchAddresses();
    } catch (error) {
      toast.error('Adres eklenemedi');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Bu adresi silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`${API_BASE}/customer/addresses/${id}`, {
          withCredentials: true
        });
        toast.success('Adres silindi');
        fetchAddresses();
      } catch (error) {
        toast.error('Adres silinemedi');
      }
    }
  };

  const getGPSForAddress = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setFormData({
            ...formData,
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
          toast.success('GPS konumu alındı');
        },
        () => toast.error('GPS konumu alınamadı')
      );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">📍 Adreslerim</h2>
        <Button onClick={() => setShowForm(!showForm)} className="bg-blue-600">
          {showForm ? '❌ İptal' : '➕ Yeni Adres'}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Yeni Adres Ekle</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <input
                placeholder="Adres Başlığı (Ev, İş, vb.)"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="Şehir"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="px-3 py-2 border rounded-lg"
                />
                <input
                  placeholder="İlçe"
                  value={formData.district}
                  onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                  className="px-3 py-2 border rounded-lg"
                />
              </div>
              <textarea
                placeholder="Sokak/Mahalle"
                value={formData.street}
                onChange={(e) => setFormData({ ...formData, street: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                rows="2"
              />
              <div className="grid grid-cols-3 gap-4">
                <input
                  placeholder="Bina No"
                  value={formData.building}
                  onChange={(e) => setFormData({ ...formData, building: e.target.value })}
                  className="px-3 py-2 border rounded-lg"
                />
                <input
                  placeholder="Kat"
                  value={formData.floor}
                  onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                  className="px-3 py-2 border rounded-lg"
                />
                <input
                  placeholder="Daire"
                  value={formData.apartment}
                  onChange={(e) => setFormData({ ...formData, apartment: e.target.value })}
                  className="px-3 py-2 border rounded-lg"
                />
              </div>
              <div className="flex gap-4">
                <Button onClick={getGPSForAddress} className="bg-purple-600">
                  📍 GPS Konumu Al
                </Button>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  />
                  <span>Varsayılan adres olarak ayarla</span>
                </label>
              </div>
              <Button onClick={handleAdd} className="w-full bg-blue-600">
                ✔️ Adresi Kaydet
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {addresses.map((addr) => (
          <Card key={addr.id} className={addr.is_default ? 'border-2 border-blue-500' : ''}>
            <CardContent className="p-4">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-bold">{addr.title}</h3>
                {addr.is_default && (
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">Varsayılan</span>
                )}
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <p>{addr.street}</p>
                <p>Bina: {addr.building}, Kat: {addr.floor}, Daire: {addr.apartment}</p>
                <p>{addr.district}, {addr.city}</p>
                {addr.postal_code && <p>Posta Kodu: {addr.postal_code}</p>}
              </div>
              <Button
                onClick={() => handleDelete(addr.id)}
                className="w-full mt-3 bg-red-500"
              >
                🗑️ Sil
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {addresses.length === 0 && (
        <Card className="bg-yellow-50">
          <CardContent className="p-12 text-center">
            <p className="text-5xl mb-4">📍</p>
            <p className="text-gray-700">Henüz kayıtlı adresiniz yok</p>
            <p className="text-sm text-gray-600 mt-2">Yeni bir adres ekleyin</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CustomerAddressManager;