import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { MapPin, Plus, Edit, Trash2, Home, Briefcase, CheckCircle } from 'lucide-react';
import { SimpleAddressFormWithMap } from '../../components/SimpleAddressFormWithMap';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

export const AddressManagementPage = ({ onBack }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);

  useEffect(() => {
    loadAddresses();
  }, []);

  const loadAddresses = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/me/addresses`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setAddresses(data || []);
      } else {
        toast.error('Adresler yüklenemedi');
      }
    } catch (error) {
      console.error('Load addresses error:', error);
      toast.error('Bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAddress = async (formData) => {
    try {
      const url = editingAddress
        ? `${API}/me/addresses/${editingAddress.id}`
        : `${API}/me/addresses`;
      
      const method = editingAddress ? 'PATCH' : 'POST';

      const response = await fetch(url, {
        method,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        toast.success(editingAddress ? 'Adres güncellendi' : 'Adres eklendi');
        setShowForm(false);
        setEditingAddress(null);
        loadAddresses();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Adres kaydedilemedi');
      }
    } catch (error) {
      console.error('Save address error:', error);
      throw error;
    }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!window.confirm('Bu adresi silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const response = await fetch(`${API}/me/addresses/${addressId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success('Adres silindi');
        loadAddresses();
      } else {
        toast.error('Adres silinemedi');
      }
    } catch (error) {
      console.error('Delete address error:', error);
      toast.error('Bir hata oluştu');
    }
  };

  const handleSetDefault = async (addressId) => {
    try {
      const response = await fetch(`${API}/me/addresses/${addressId}/default`, {
        method: 'PATCH',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success('Varsayılan adres güncellendi');
        loadAddresses();
      } else {
        toast.error('Varsayılan adres ayarlanamadı');
      }
    } catch (error) {
      console.error('Set default error:', error);
      toast.error('Bir hata oluştu');
    }
  };

  const getAddressIcon = (label) => {
    const lower = label?.toLowerCase() || '';
    if (lower.includes('ev')) return Home;
    if (lower.includes('iş') || lower.includes('ofis')) return Briefcase;
    return MapPin;
  };

  if (showForm) {
    return (
      <SimpleAddressFormWithMap
        address={editingAddress}
        onSave={handleSaveAddress}
        onCancel={() => {
          setShowForm(false);
          setEditingAddress(null);
        }}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          {onBack && (
            <Button onClick={onBack} variant="outline" size="sm">
              ← Geri
            </Button>
          )}
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground flex items-center gap-2">
            <MapPin className="h-6 w-6 text-primary" />
            Adreslerim
          </h1>
        </div>
        <Button
          onClick={() => {
            setEditingAddress(null);
            setShowForm(true);
          }}
          className="bg-primary hover:bg-primary-hover"
        >
          <Plus className="h-4 w-4 mr-2" />
          Yeni Adres
        </Button>
      </div>

      {/* Address List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : addresses.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <MapPin className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Henüz adres eklemediniz</h3>
            <p className="text-muted-foreground mb-6">
              Sipariş vermek için adres eklemeniz gerekiyor
            </p>
            <Button
              onClick={() => setShowForm(true)}
              className="bg-primary hover:bg-primary-hover"
            >
              <Plus className="h-4 w-4 mr-2" />
              İlk Adresini Ekle
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {addresses.map((address) => {
            const Icon = getAddressIcon(address.adres_basligi || address.label);
            
            return (
              <Card key={address.id} className="card-hover-lift">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className="flex-shrink-0 p-3 rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-6 w-6" />
                    </div>

                    {/* Address Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-bold text-foreground">
                          {address.adres_basligi || address.label}
                        </h3>
                        {address.is_default && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 text-xs font-medium rounded-full">
                            <CheckCircle className="h-3 w-3" />
                            Varsayılan
                          </span>
                        )}
                      </div>

                      {address.alici_adsoyad && (
                        <p className="text-sm font-medium text-foreground mb-1">
                          {address.alici_adsoyad}
                        </p>
                      )}

                      {address.telefon && (
                        <p className="text-sm text-muted-foreground mb-2">
                          📞 {address.telefon}
                        </p>
                      )}

                      <p className="text-sm text-muted-foreground mb-2">
                        {address.acik_adres || address.full}
                      </p>

                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                        {address.mahalle && (
                          <span className="px-2 py-1 bg-secondary rounded">
                            {address.mahalle}
                          </span>
                        )}
                        {address.ilce && (
                          <span className="px-2 py-1 bg-secondary rounded">
                            {address.ilce || address.district}
                          </span>
                        )}
                        {address.il && (
                          <span className="px-2 py-1 bg-secondary rounded font-semibold">
                            {address.il || address.city}
                          </span>
                        )}
                        {address.posta_kodu && (
                          <span className="px-2 py-1 bg-secondary rounded">
                            {address.posta_kodu}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2 flex-shrink-0">
                      <Button
                        onClick={() => {
                          setEditingAddress(address);
                          setShowForm(true);
                        }}
                        variant="outline"
                        size="sm"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      
                      {!address.is_default && (
                        <Button
                          onClick={() => handleSetDefault(address.id)}
                          variant="outline"
                          size="sm"
                          title="Varsayılan yap"
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      )}
                      
                      <Button
                        onClick={() => handleDeleteAddress(address.id)}
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
