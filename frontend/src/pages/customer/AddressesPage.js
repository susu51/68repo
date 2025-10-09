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
    // Async Operation Protection
    if (!isMounted) return;
    
    if (onSelectAddress) {
      onSelectAddress(address);
    }
  };

  const getCurrentLocation = () => {
    // Async Operation Protection
    if (!isMounted) return;
    
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          if (isMounted) {
            setNewAddress({
              ...newAddress,
              lat: position.coords.latitude,
              lng: position.coords.longitude
            });
            toast.success('Konum başarıyla alındı!');
          }
        },
        (error) => {
          console.error('Geolocation error:', error);
          if (isMounted) {
            toast.error('Konum alınamadı. Lütfen el ile girin.');
          }
        }
      );
    } else {
      if (isMounted) {
        toast.error('Tarayıcınız konum servisini desteklemiyor.');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Adresler yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-orange-50 to-red-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header Card */}
        <Card className="mb-8 border-0 shadow-xl rounded-3xl bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 text-white overflow-hidden">
          <CardContent className="p-8 relative">
            {/* Background Pattern */}
            <div className="absolute inset-0 bg-white/10 opacity-40">
              <div className="absolute top-0 right-0 w-48 h-48 bg-white/20 rounded-full -mr-24 -mt-24"></div>
              <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/15 rounded-full -ml-16 -mb-16"></div>
            </div>
            
            <div className="relative flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-16 h-16 bg-white/25 backdrop-blur-sm rounded-2xl flex items-center justify-center mr-6 shadow-lg">
                  <span className="text-3xl">📍</span>
                </div>
                <div>
                  <h1 className="text-3xl font-bold mb-2">Kayıtlı Adreslerim</h1>
                  <p className="text-white/90 text-lg">
                    Restoran araması için bir adres seçin. Şehrinize göre en yakın restoranları bulacağız.
                  </p>
                </div>
              </div>
              
              {onBack && (
                <Button 
                  variant="outline" 
                  onClick={onBack}
                  className="bg-white/20 border-white/30 text-white hover:bg-white/30 rounded-xl backdrop-blur-sm"
                >
                  ← Geri
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {addresses.length === 0 ? (
          // Empty state - Enhanced Card Design
          <Card className="text-center py-16 border-0 shadow-2xl rounded-3xl bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 relative overflow-hidden">
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-64 h-64 bg-orange-200 rounded-full -mr-32 -mt-32"></div>
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-pink-200 rounded-full -ml-24 -mb-24"></div>
              <div className="absolute top-1/2 left-1/2 w-32 h-32 bg-red-200 rounded-full -ml-16 -mt-16"></div>
            </div>
            
            <CardContent className="relative z-10">
              <div className="mb-8">
                {/* Animated Icon Container */}
                <div className="w-32 h-32 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl animate-pulse">
                  <span className="text-6xl">📍</span>
                </div>
                
                <h3 className="text-3xl font-bold text-gray-800 mb-4">
                  Henüz kayıtlı adresiniz yok
                </h3>
                <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
                  🍽️ Restoran araması yapmak ve sipariş verebilmek için önce bir adres eklemelisiniz.
                </p>
                
                {/* Feature highlights */}
                <div className="grid md:grid-cols-3 gap-4 mb-8 max-w-2xl mx-auto">
                  <div className="p-4 bg-white/60 backdrop-blur-sm rounded-2xl shadow-lg">
                    <div className="text-2xl mb-2">🏠</div>
                    <p className="text-sm font-medium text-gray-700">Ev, iş, okul adreslerinizi kaydedin</p>
                  </div>
                  <div className="p-4 bg-white/60 backdrop-blur-sm rounded-2xl shadow-lg">
                    <div className="text-2xl mb-2">📍</div>
                    <p className="text-sm font-medium text-gray-700">Konum bazlı restoran önerisi</p>
                  </div>
                  <div className="p-4 bg-white/60 backdrop-blur-sm rounded-2xl shadow-lg">
                    <div className="text-2xl mb-2">⚡</div>
                    <p className="text-sm font-medium text-gray-700">Hızlı teslimat süresi</p>
                  </div>
                </div>
                
                <Button 
                  onClick={() => {
                    if (isMounted) {
                      setShowAddForm(true);
                    }
                  }}
                  className="bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 hover:from-orange-600 hover:via-red-600 hover:to-pink-600 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
                >
                  ➕ İlk Adresimi Ekle
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          // Address list
          <div className="space-y-6">
            {/* Address Count & Add Button Card */}
            <Card className="border-0 shadow-lg rounded-2xl bg-white/80 backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mr-4">
                      <span className="text-white font-bold">{addresses.length}</span>
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-800">Kayıtlı Adresleriniz</h2>
                      <p className="text-sm text-gray-600">Toplam {addresses.length} adet adres</p>
                    </div>
                  </div>
                  <Button 
                    onClick={() => {
                      if (isMounted) {
                        setShowAddForm(true);
                      }
                    }}
                    className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold px-6 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    ➕ Yeni Adres Ekle
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {addresses.map((address, index) => (
                <Card key={`address-card-${address.id || index}`} className="group hover:shadow-2xl hover:scale-105 transition-all duration-500 border-0 shadow-lg bg-white rounded-2xl overflow-hidden">
                  <CardContent className="p-0">
                    {/* Card Header with Icon */}
                    <div className="bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 p-6 text-white relative overflow-hidden">
                      {/* Background Pattern */}
                      <div className="absolute inset-0 bg-white/10 opacity-20">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white/20 rounded-full -mr-16 -mt-16"></div>
                        <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/15 rounded-full -ml-12 -mb-12"></div>
                      </div>
                      
                      <div className="relative flex items-center justify-between">
                        <div className="flex items-center">
                          <div className="w-14 h-14 bg-white/25 backdrop-blur-sm rounded-2xl flex items-center justify-center mr-4 shadow-lg">
                            <span className="text-2xl">📍</span>
                          </div>
                          <div>
                            <h3 className="text-xl font-bold mb-1">
                              {address.label || 'Adres'}
                            </h3>
                            <p className="text-white/90 text-sm font-medium">
                              Kayıtlı Adres
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Card Body */}
                    <div className="p-6">
                      <div className="space-y-4">
                        {/* City */}
                        <div className="flex items-center p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border border-blue-100 shadow-sm">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                            <span className="text-blue-600">🏙️</span>
                          </div>
                          <div>
                            <p className="text-xs text-blue-600 font-semibold uppercase tracking-wider">Şehir</p>
                            <p className="font-bold text-gray-800 text-lg">
                              {address.city || 'Şehir bilgisi yok'}
                            </p>
                          </div>
                        </div>
                        
                        {/* Address Description */}
                        <div className="flex items-start p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-100 shadow-sm">
                          <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mr-3 mt-1">
                            <span className="text-purple-600">🏠</span>
                          </div>
                          <div className="flex-1">
                            <p className="text-xs text-purple-600 font-semibold uppercase tracking-wider mb-1">Adres Detayı</p>
                            <p className="text-sm text-gray-800 leading-relaxed font-medium">
                              {address.description || 'Açıklama yok'}
                            </p>
                          </div>
                        </div>
                        
                        {/* Location Info */}
                        {address.lat && address.lng ? (
                          <div className="flex items-center p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-200 shadow-sm">
                            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-3">
                              <span className="text-green-600">✅</span>
                            </div>
                            <div>
                              <p className="text-xs text-green-600 font-bold uppercase tracking-wider">Konum Mevcut</p>
                              <p className="text-xs text-green-700 font-mono">
                                {address.lat.toFixed(4)}, {address.lng.toFixed(4)}
                              </p>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center p-4 bg-gradient-to-r from-yellow-50 to-amber-50 rounded-xl border border-yellow-200 shadow-sm">
                            <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                              <span className="text-yellow-600">⚠️</span>
                            </div>
                            <div>
                              <p className="text-xs text-yellow-600 font-bold uppercase tracking-wider">Konum Yok</p>
                              <p className="text-xs text-yellow-700">Manuel adres</p>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Action Button */}
                      <Button 
                        onClick={() => handleSelectAddress(address)}
                        className="w-full mt-6 bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 hover:from-orange-600 hover:via-red-600 hover:to-pink-600 text-white font-bold py-4 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
                      >
                        🍽️ Bu Adrese Göre Restoran Ara
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

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