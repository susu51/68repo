import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../../components/ui/dialog";
import { Badge } from "../../components/ui/badge";
import { Textarea } from "../../components/ui/textarea";
import { toast } from 'react-hot-toast';
import { apiClient } from '../../utils/apiClient';
import { MapPin, Plus, Edit2, Trash2, Navigation, Star, Clock, Check } from 'lucide-react';

const turkishCities = [
  'Adana', 'Adıyaman', 'Afyonkarahisar', 'Ağrı', 'Aksaray', 'Amasya', 'Ankara', 'Antalya', 
  'Ardahan', 'Artvin', 'Aydın', 'Balıkesir', 'Bartın', 'Batman', 'Bayburt', 'Bilecik', 
  'Bingöl', 'Bitlis', 'Bolu', 'Burdur', 'Bursa', 'Çanakkale', 'Çankırı', 'Çorum', 
  'Denizli', 'Diyarbakır', 'Düzce', 'Edirne', 'Elazığ', 'Erzincan', 'Erzurum', 
  'Eskişehir', 'Gaziantep', 'Giresun', 'Gümüşhane', 'Hakkâri', 'Hatay', 'Iğdır', 
  'Isparta', 'İstanbul', 'İzmir', 'Kahramanmaraş', 'Karabük', 'Karaman', 'Kars', 
  'Kastamonu', 'Kayseri', 'Kırıkkale', 'Kırklareli', 'Kırşehir', 'Kilis', 'Kocaeli', 
  'Konya', 'Kütahya', 'Malatya', 'Manisa', 'Mardin', 'Mersin', 'Muğla', 'Muş', 
  'Nevşehir', 'Niğde', 'Ordu', 'Osmaniye', 'Rize', 'Sakarya', 'Samsun', 'Siirt', 
  'Sinop', 'Sivas', 'Şanlıurfa', 'Şırnak', 'Tekirdağ', 'Tokat', 'Trabzon', 'Tunceli', 
  'Uşak', 'Van', 'Yalova', 'Yozgat', 'Zonguldak'
];

const initialAddressForm = {
  label: '',
  city: '',
  district: '',
  description: '',
  lat: null,
  lng: null
};

const AddressesPageComponent = ({ onSelectAddress, onBack, onAddressAdded }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [addressForm, setAddressForm] = useState(initialAddressForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [gettingLocation, setGettingLocation] = useState(false);

  const resetForm = useCallback(() => {
    setAddressForm(initialAddressForm);
    setEditingAddress(null);
    setCurrentLocation(null);
  }, []);

  const loadAddresses = useCallback(async () => {
    setLoading(true);
    try {
      console.log('🔄 Loading addresses...');
      const response = await apiClient.get('/user/addresses');
      
      if (response && Array.isArray(response)) {
        setAddresses(response);
        console.log(`✅ Loaded ${response.length} addresses`);
      } else {
        setAddresses([]);
        console.log('ℹ️ No addresses found or invalid response format');
      }
    } catch (error) {
      console.error('❌ Error loading addresses:', error);
      setAddresses([]);
      
      if (error.response?.status === 401) {
        toast.error('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
      } else {
        toast.error('Adresler yüklenirken hata oluştu');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAddresses();
  }, [loadAddresses]);

  const getCurrentLocation = () => {
    setGettingLocation(true);
    
    if (!navigator.geolocation) {
      toast.error('Tarayıcınız konum özelliğini desteklemiyor');
      setGettingLocation(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setCurrentLocation({ lat: latitude, lng: longitude });
        setAddressForm(prev => ({
          ...prev,
          lat: latitude,
          lng: longitude
        }));
        toast.success('Mevcut konumunuz alındı!');
        setGettingLocation(false);
      },
      (error) => {
        console.error('Konum alınamadı:', error);
        toast.error('Konum erişimi reddedildi veya alınamadı');
        setGettingLocation(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const validateForm = () => {
    const errors = [];
    
    if (!addressForm.label?.trim()) errors.push('Adres adı');
    if (!addressForm.city?.trim()) errors.push('Şehir');
    if (!addressForm.district?.trim()) errors.push('İlçe');
    if (!addressForm.description?.trim()) errors.push('Adres açıklaması');
    
    if (errors.length > 0) {
      toast.error(`Lütfen şu alanları doldurun: ${errors.join(', ')}`);
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    
    try {
      const addressData = {
        ...addressForm,
        lat: addressForm.lat || 40.7831, // Default Istanbul coordinates if no location
        lng: addressForm.lng || 29.0441
      };

      let response;
      if (editingAddress) {
        // Update existing address
        console.log('🔄 Updating address:', editingAddress.id);
        response = await apiClient.put(`/user/addresses/${editingAddress.id}`, addressData);
        
        setAddresses(prev => 
          prev.map(addr => addr.id === editingAddress.id ? response : addr)
        );
        toast.success('Adres başarıyla güncellendi!');
      } else {
        // Create new address
        console.log('🔄 Creating new address');
        response = await apiClient.post('/user/addresses', addressData);
        
        setAddresses(prev => [...prev, response]);
        toast.success('Adres başarıyla eklendi!');
        
        // Notify parent component
        if (onAddressAdded) {
          onAddressAdded(response);
        }
      }

      // Reset form and close modal
      resetForm();
      setShowAddForm(false);
      
    } catch (error) {
      console.error('❌ Error saving address:', error);
      
      if (error.response?.status === 401) {
        toast.error('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
      } else if (error.response?.status === 422) {
        const detail = error.response?.data?.detail;
        if (typeof detail === 'string') {
          toast.error(`Doğrulama hatası: ${detail}`);
        } else {
          toast.error('Adres bilgileri geçersiz. Lütfen kontrol edin.');
        }
      } else {
        const errorMsg = editingAddress ? 'Adres güncellenirken hata oluştu' : 'Adres eklenirken hata oluştu';
        toast.error(errorMsg);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (address) => {
    setEditingAddress(address);
    setAddressForm({
      label: address.label || '',
      city: address.city || '',
      district: address.district || '',
      description: address.description || '',
      lat: address.lat || null,
      lng: address.lng || null
    });
    setShowAddForm(true);
  };

  const handleDelete = async (addressId) => {
    if (!window.confirm('Bu adresi silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      console.log('🗑️ Deleting address:', addressId);
      await apiClient.delete(`/user/addresses/${addressId}`);
      
      setAddresses(prev => prev.filter(addr => addr.id !== addressId));
      toast.success('Adres başarıyla silindi!');
      
    } catch (error) {
      console.error('❌ Error deleting address:', error);
      
      if (error.response?.status === 404) {
        // Address already deleted, remove from UI
        setAddresses(prev => prev.filter(addr => addr.id !== addressId));
        toast.success('Adres silindi');
      } else if (error.response?.status === 401) {
        toast.error('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
      } else {
        toast.error('Adres silinirken hata oluştu');
      }
    }
  };

  const setDefaultAddress = async (addressId) => {
    try {
      console.log('⭐ Setting default address:', addressId);
      await apiClient.post(`/user/addresses/${addressId}/set-default`);
      
      // Update local state
      setAddresses(prev => 
        prev.map(addr => ({
          ...addr,
          is_default: addr.id === addressId
        }))
      );
      
      toast.success('Varsayılan adres ayarlandı!');
      
    } catch (error) {
      console.error('❌ Error setting default address:', error);
      toast.error('Varsayılan adres ayarlanırken hata oluştu');
    }
  };

  const handleSelectAddress = (address) => {
    if (onSelectAddress) {
      onSelectAddress(address);
    }
  };

  const openAddForm = () => {
    resetForm();
    setShowAddForm(true);
  };

  const closeForm = () => {
    resetForm();
    setShowAddForm(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-2"></div>
          <p className="text-gray-600">Adresleriniz yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="w-5 h-5 text-orange-500" />
              Adres Yönetimi
            </CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              Teslimat adreslerinizi yönetin ve düzenleyin
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={openAddForm} className="bg-orange-500 hover:bg-orange-600">
              <Plus className="w-4 h-4 mr-2" />
              Yeni Adres
            </Button>
            {onBack && (
              <Button variant="outline" onClick={onBack}>
                ← Geri Dön
              </Button>
            )}
          </div>
        </CardHeader>
        
        <CardContent>
          {addresses.length === 0 ? (
            <div className="text-center py-12">
              <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Henüz kayıtlı adresiniz yok
              </h3>
              <p className="text-gray-500 mb-4">
                Sipariş vermek için bir teslimat adresi eklemeniz gerekiyor
              </p>
              <Button onClick={openAddForm} className="bg-orange-500 hover:bg-orange-600">
                <Plus className="w-4 h-4 mr-2" />
                İlk Adresini Ekle
              </Button>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {addresses.map((address) => (
                <Card key={address.id} className="relative border-gray-200 hover:border-orange-200 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium text-gray-900">
                          {address.label}
                        </h3>
                        {address.is_default && (
                          <Badge className="bg-orange-100 text-orange-800 text-xs">
                            <Star className="w-3 h-3 mr-1" />
                            Varsayılan
                          </Badge>
                        )}
                      </div>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(address)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit2 className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(address.id)}
                          className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    <div className="space-y-2 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-gray-400" />
                        <span>{address.city}, {address.district}</span>
                      </div>
                      <p className="text-xs leading-relaxed">
                        {address.description}
                      </p>
                      {address.lat && address.lng && (
                        <div className="text-xs text-gray-400">
                          📍 {address.lat.toFixed(6)}, {address.lng.toFixed(6)}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex gap-2 mt-4">
                      {onSelectAddress && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleSelectAddress(address)}
                          className="flex-1"
                        >
                          <Check className="w-4 h-4 mr-2" />
                          Seç
                        </Button>
                      )}
                      {!address.is_default && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDefaultAddress(address.id)}
                          className="text-orange-600 hover:text-orange-700"
                        >
                          <Star className="w-4 h-4 mr-1" />
                          Varsayılan Yap
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

        {/* Add Address Dialog - Enhanced Card Design with Portal Safety */}
        {showAddForm && (
          <Dialog 
            key="add-address-dialog" 
            open={showAddForm} 
            onOpenChange={(open) => {
              if (isMounted) {
                setShowAddForm(open);
              }
            }}
            modal={true}
            container={document.body}
          >
            <DialogContent key="dialog-content" className="sm:max-w-[700px] p-0 border-0 shadow-2xl rounded-3xl overflow-hidden">
            {/* Header Card */}
            <div className="bg-gradient-to-br from-green-500 via-teal-500 to-cyan-500 p-8 text-white relative overflow-hidden">
              {/* Background Pattern */}
              <div className="absolute inset-0 bg-white/10 opacity-30">
                <div className="absolute top-0 right-0 w-40 h-40 bg-white/20 rounded-full -mr-20 -mt-20"></div>
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/15 rounded-full -ml-16 -mb-16"></div>
              </div>
              
              <DialogHeader className="relative">
                <div className="flex items-center">
                  <div className="w-16 h-16 bg-white/25 backdrop-blur-sm rounded-2xl flex items-center justify-center mr-4 shadow-lg">
                    <span className="text-3xl">📍</span>
                  </div>
                  <div>
                    <DialogTitle className="text-2xl font-bold mb-1">Yeni Adres Ekle</DialogTitle>
                    <p className="text-white/90 text-sm">Restoranları bulmak için adres bilgilerinizi girin</p>
                  </div>
                </div>
              </DialogHeader>
            </div>
            
            {/* Form Card */}
            <div className="p-8 bg-white">
              <div className="space-y-6">
                {/* Address Name & City Card */}
                <Card className="border border-gray-100 shadow-md rounded-2xl">
                  <CardHeader className="pb-4">
                    <h4 className="font-semibold text-gray-800 flex items-center">
                      <span className="mr-2">🏷️</span>
                      Temel Bilgiler
                    </h4>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-semibold text-gray-700">Adres Adı *</Label>
                        <Input
                          className="mt-2 rounded-xl border-gray-200 focus:border-orange-500 h-12"
                          placeholder="Ev, İş, Okul vb."
                          value={newAddress.label}
                          onChange={(e) => {
                            if (isMounted) {
                              setNewAddress({...newAddress, label: e.target.value});
                            }
                          }}
                        />
                      </div>
                      
                      <div>
                        <Label className="text-sm font-semibold text-gray-700">Şehir *</Label>
                        <select 
                          className="mt-2 rounded-xl border-gray-200 focus:border-orange-500 h-12 w-full px-3 py-2 bg-white border-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                          value={newAddress.city}
                          onChange={(e) => {
                            console.log('🏙️ Native select changed:', e.target.value);
                            if (isMounted) {
                              setNewAddress({...newAddress, city: e.target.value});
                              console.log('🏙️ City state updated to:', e.target.value);
                            }
                          }}
                        >
                          <option value="">Şehir Seçin</option>
                          {turkishCities.map(city => (
                            <option key={city} value={city}>{city}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                {/* Address Description Card */}
                <Card className="border border-gray-100 shadow-md rounded-2xl">
                  <CardHeader className="pb-4">
                    <h4 className="font-semibold text-gray-800 flex items-center">
                      <span className="mr-2">🏠</span>
                      Adres Detayı
                    </h4>
                  </CardHeader>
                  <CardContent>
                    <Label className="text-sm font-semibold text-gray-700">Adres Açıklaması *</Label>
                    <Input
                      className="mt-2 rounded-xl border-gray-200 focus:border-orange-500 h-12"
                      placeholder="Mahalle, sokak, bina no, daire no vb."
                      value={newAddress.description}
                      onChange={(e) => {
                        if (isMounted) {
                          setNewAddress({...newAddress, description: e.target.value});
                        }
                      }}
                    />
                  </CardContent>
                </Card>
                
                {/* Location Card */}
                <Card className="border border-gray-100 shadow-md rounded-2xl">
                  <CardHeader className="pb-4">
                    <h4 className="font-semibold text-gray-800 flex items-center">
                      <span className="mr-2">🗺️</span>
                      Konum Bilgisi (Opsiyonel)
                    </h4>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={getCurrentLocation}
                      className="w-full rounded-xl border-2 border-dashed border-blue-300 hover:border-blue-500 h-12 text-blue-600 font-medium"
                    >
                      📍 Mevcut Konumu Otomatik Al
                    </Button>
                    
                    <div className="text-center text-sm text-gray-500 font-medium">veya manuel girin</div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-xs font-semibold text-gray-600">Enlem (Latitude)</Label>
                        <Input
                          className="mt-1 rounded-xl border-gray-200 h-10"
                          placeholder="41.0082"
                          type="number"
                          step="any"
                          value={newAddress.lat || ''}
                          onChange={(e) => {
                            if (isMounted) {
                              setNewAddress({...newAddress, lat: parseFloat(e.target.value) || null});
                            }
                          }}
                        />
                      </div>
                      <div>
                        <Label className="text-xs font-semibold text-gray-600">Boylam (Longitude)</Label>
                        <Input
                          className="mt-1 rounded-xl border-gray-200 h-10"
                          placeholder="28.9784"
                          type="number"
                          step="any"
                          value={newAddress.lng || ''}
                          onChange={(e) => {
                            if (isMounted) {
                              setNewAddress({...newAddress, lng: parseFloat(e.target.value) || null});
                            }
                          }}
                        />
                      </div>
                    </div>
                    
                    {newAddress.lat && newAddress.lng && (
                      <div className="p-3 bg-green-50 border border-green-200 rounded-xl">
                        <p className="text-sm text-green-700 font-medium flex items-center">
                          <span className="mr-2">✅</span>
                          Konum başarıyla alındı: {newAddress.lat.toFixed(4)}, {newAddress.lng.toFixed(4)}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
                
                {/* Action Buttons */}
                <div className="flex gap-4 pt-4">
                  <Button 
                    variant="outline" 
                    onClick={() => {
                      if (isMounted) {
                        setShowAddForm(false);
                      }
                    }}
                    className="flex-1 h-12 rounded-xl border-gray-300 hover:bg-gray-50"
                  >
                    ❌ İptal Et
                  </Button>
                  <Button 
                    onClick={handleAddAddress}
                    className="flex-1 h-12 bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    ✅ Adresi Kaydet
                  </Button>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
        )}
      </div>
    </div>
  );
};

// Memoize component to reduce re-renders that might cause DOM manipulation issues
export const AddressesPage = React.memo(AddressesPageComponent);
export default AddressesPage;