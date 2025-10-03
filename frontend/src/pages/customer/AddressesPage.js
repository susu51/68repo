import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "../../components/ui/dialog";
import { toast } from 'react-hot-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

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

export const AddressesPage = ({ onSelectAddress, onBack }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAddress, setNewAddress] = useState({
    label: '',
    city: 'İstanbul',
    description: '',
    lat: null,
    lng: null
  });

  useEffect(() => {
    loadAddresses();
  }, []);

  const loadAddresses = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('kuryecini_access_token');
      console.log('Loading addresses - Token debug:', token ? `Token exists (${token.length} chars)` : 'No token found');
      
      const response = await axios.get(`${API}/user/addresses`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Load addresses response:', response.data);
      setAddresses(response.data || []);
    } catch (error) {
      console.error('Error loading addresses:', error);
      console.log('Error details:', error.response?.data);
      // If no addresses or error, show empty state
      setAddresses([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAddress = async () => {
    try {
      if (!newAddress.label || !newAddress.city || !newAddress.description) {
        toast.error('Lütfen tüm zorunlu alanları doldurun');
        return;
      }

      const token = localStorage.getItem('kuryecini_access_token');
      console.log('Token debug:', token ? `Token exists (${token.length} chars)` : 'No token found');

      const addressData = {
        ...newAddress,
        // Normalize city name on the frontend as well
        city_original: newAddress.city,
        city_normalized: newAddress.city.toLowerCase().replace('ı', 'i')
      };

      console.log('Address data to send:', addressData);

      const response = await axios.post(`${API}/user/addresses`, addressData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      console.log('Add address response:', response.data);

      toast.success('Adres başarıyla eklendi!');
      setAddresses([...addresses, response.data]);
      setShowAddForm(false);
      setNewAddress({
        label: '',
        city: 'İstanbul',
        description: '',
        lat: null,
        lng: null
      });
    } catch (error) {
      console.error('Error adding address:', error);
      toast.error('Adres eklenirken hata oluştu');
    }
  };

  const handleSelectAddress = (address) => {
    if (onSelectAddress) {
      onSelectAddress(address);
    }
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setNewAddress({
            ...newAddress,
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
          toast.success('Konum başarıyla alındı!');
        },
        (error) => {
          console.error('Geolocation error:', error);
          toast.error('Konum alınamadı. Lütfen el ile girin.');
        }
      );
    } else {
      toast.error('Tarayıcınız konum servisini desteklemiyor.');
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
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-800">📍 Kayıtlı Adreslerim</h1>
            {onBack && (
              <Button variant="outline" onClick={onBack}>
                ← Geri
              </Button>
            )}
          </div>
          <p className="text-gray-600">
            Restoran araması için bir adres seçin. Adresinizdeki şehre göre restoranları listeleyeceğiz.
          </p>
        </div>

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
                  onClick={() => setShowAddForm(true)}
                  className="bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 hover:from-orange-600 hover:via-red-600 hover:to-pink-600 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105"
                >
                  ➕ İlk Adresimi Ekle
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          // Address list
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Adresleriniz ({addresses.length})</h2>
              <Button 
                onClick={() => setShowAddForm(true)}
                className="bg-green-500 hover:bg-green-600"
              >
                ➕ Yeni Adres Ekle
              </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {addresses.map((address, index) => (
                <Card key={index} className="group hover:shadow-2xl hover:scale-105 transition-all duration-500 border-0 shadow-lg bg-white rounded-2xl overflow-hidden">
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

        {/* Add Address Dialog - Enhanced Card Design */}
        <Dialog open={showAddForm} onOpenChange={setShowAddForm}>
          <DialogContent className="sm:max-w-[700px] p-0 border-0 shadow-2xl rounded-3xl overflow-hidden">
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
                          onChange={(e) => setNewAddress({...newAddress, label: e.target.value})}
                        />
                      </div>
                      
                      <div>
                        <Label className="text-sm font-semibold text-gray-700">Şehir *</Label>
                        <Select 
                          value={newAddress.city} 
                          onValueChange={(value) => setNewAddress({...newAddress, city: value})}
                        >
                          <SelectTrigger className="mt-2 rounded-xl border-gray-200 focus:border-orange-500 h-12">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="rounded-xl">
                            {turkishCities.map(city => (
                              <SelectItem key={city} value={city} className="rounded-lg">{city}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
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
                      onChange={(e) => setNewAddress({...newAddress, description: e.target.value})}
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
                          onChange={(e) => setNewAddress({...newAddress, lat: parseFloat(e.target.value) || null})}
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
                          onChange={(e) => setNewAddress({...newAddress, lng: parseFloat(e.target.value) || null})}
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
                    onClick={() => setShowAddForm(false)}
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
      </div>
    </div>
  );
};

export default AddressesPage;