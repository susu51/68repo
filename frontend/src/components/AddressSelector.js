import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { toast } from 'sonner';

const turkishCities = [
  'Adana', 'Adıyaman', 'Afyonkarahisar', 'Ağrı', 'Aksaray', 'Amasya', 'Ankara', 'Antalya', 'Ardahan', 'Artvin',
  'Aydın', 'Balıkesir', 'Bartın', 'Batman', 'Bayburt', 'Bilecik', 'Bingöl', 'Bitlis', 'Bolu', 'Burdur',
  'Bursa', 'Çanakkale', 'Çankırı', 'Çorum', 'Denizli', 'Diyarbakır', 'Düzce', 'Edirne', 'Elazığ', 'Erzincan',
  'Erzurum', 'Eskişehir', 'Gaziantep', 'Giresun', 'Gümüşhane', 'Hakkâri', 'Hatay', 'Iğdır', 'Isparta', 'İstanbul',
  'İzmir', 'Kahramanmaraş', 'Karabük', 'Karaman', 'Kars', 'Kastamonu', 'Kayseri', 'Kırıkkale', 'Kırklareli', 'Kırşehir',
  'Kilis', 'Kocaeli', 'Konya', 'Kütahya', 'Malatya', 'Manisa', 'Mardin', 'Mersin', 'Muğla', 'Muş',
  'Nevşehir', 'Niğde', 'Ordu', 'Osmaniye', 'Rize', 'Sakarya', 'Samsun', 'Siirt', 'Sinop', 'Sivas',
  'Şanlıurfa', 'Şırnak', 'Tekirdağ', 'Tokat', 'Trabzon', 'Tunceli', 'Uşak', 'Van', 'Yalova', 'Yozgat', 'Zonguldak'
];

export const AddressSelector = ({ 
  selectedAddress, 
  onAddressSelect, 
  onNewAddress, 
  showNewAddressForm = false,
  className = ""
}) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(showNewAddressForm);
  const [newAddress, setNewAddress] = useState({
    title: '',
    address_line: '',
    district: '',
    city: 'İstanbul',
    postal_code: '',
    building_info: '',
    floor_apartment: '',
    phone: '',
    notes: ''
  });

  useEffect(() => {
    loadAddresses();
  }, []);

  const loadAddresses = async () => {
    try {
      setLoading(true);
      // Mock data for demo - in real app this would be API call
      const mockAddresses = [
        {
          id: 'addr-1',
          title: 'Ev',
          address_line: 'Atatürk Caddesi No:123 Kat:3 Daire:7',
          district: 'Kadıköy',
          city: 'İstanbul',
          postal_code: '34710',
          is_default: true
        },
        {
          id: 'addr-2', 
          title: 'İş',
          address_line: 'Büyükdere Caddesi No:45 Plaza Kat:12',
          district: 'Şişli',
          city: 'İstanbul',
          postal_code: '34394',
          is_default: false
        }
      ];
      
      setAddresses(mockAddresses);
      
      // Auto-select default address if none selected
      if (!selectedAddress && mockAddresses.length > 0) {
        const defaultAddr = mockAddresses.find(addr => addr.is_default) || mockAddresses[0];
        onAddressSelect && onAddressSelect(defaultAddr);
      }
    } catch (error) {
      toast.error('Adresler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAddress = async () => {
    if (!newAddress.title || !newAddress.address_line || !newAddress.city) {
      toast.error('Lütfen gerekli alanları doldurun');
      return;
    }

    try {
      setLoading(true);
      
      const addressToSave = {
        ...newAddress,
        id: `addr-${Date.now()}`,
        is_default: addresses.length === 0 // First address becomes default
      };
      
      // Mock save - in real app this would be API call
      const updatedAddresses = [...addresses, addressToSave];
      setAddresses(updatedAddresses);
      
      // Select the new address
      onAddressSelect && onAddressSelect(addressToSave);
      onNewAddress && onNewAddress(addressToSave);
      
      // Reset form
      setNewAddress({
        title: '',
        address_line: '',
        district: '',
        city: 'İstanbul',
        postal_code: '',
        building_info: '',
        floor_apartment: '',
        phone: '',
        notes: ''
      });
      
      setShowForm(false);
      toast.success('Adres başarıyla kaydedildi');
    } catch (error) {
      toast.error('Adres kaydetme hatası');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Teslimat Adresi</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowForm(true)}
          className="text-blue-600 border-blue-200"
        >
          + Yeni Adres
        </Button>
      </div>

      {/* Saved Addresses */}
      {addresses.length > 0 && (
        <div className="space-y-3">
          {addresses.map((address) => (
            <Card 
              key={address.id}
              className={`cursor-pointer transition-all duration-200 ${
                selectedAddress?.id === address.id 
                  ? 'ring-2 ring-blue-500 bg-blue-50' 
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => onAddressSelect && onAddressSelect(address)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h4 className="font-semibold">{address.title}</h4>
                      {address.is_default && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                          Varsayılan
                        </span>
                      )}
                      {selectedAddress?.id === address.id && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          Seçili
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-1">
                      {address.address_line}
                    </p>
                    <p className="text-sm text-gray-500">
                      {address.district}, {address.city} {address.postal_code}
                    </p>
                  </div>
                  <div className="ml-4">
                    {selectedAddress?.id === address.id ? (
                      <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </div>
                    ) : (
                      <div className="w-5 h-5 border-2 border-gray-300 rounded-full"></div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* New Address Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Yeni Adres Ekle</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="title">Adres Başlığı *</Label>
                <Input
                  id="title"
                  placeholder="Ev, İş, vb."
                  value={newAddress.title}
                  onChange={(e) => setNewAddress({...newAddress, title: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="city">Şehir *</Label>
                <Select value={newAddress.city} onValueChange={(value) => setNewAddress({...newAddress, city: value})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Şehir seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {turkishCities.map(city => (
                      <SelectItem key={city} value={city}>{city}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="address_line">Adres *</Label>
              <Input
                id="address_line"
                placeholder="Sokak, cadde, mahalle bilgisi"
                value={newAddress.address_line}
                onChange={(e) => setNewAddress({...newAddress, address_line: e.target.value})}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="district">İlçe</Label>
                <Input
                  id="district"
                  placeholder="İlçe"
                  value={newAddress.district}
                  onChange={(e) => setNewAddress({...newAddress, district: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="postal_code">Posta Kodu</Label>
                <Input
                  id="postal_code"
                  placeholder="34000"
                  value={newAddress.postal_code}
                  onChange={(e) => setNewAddress({...newAddress, postal_code: e.target.value})}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="building_info">Bina Bilgisi</Label>
                <Input
                  id="building_info"
                  placeholder="Apartman adı, site adı"
                  value={newAddress.building_info}
                  onChange={(e) => setNewAddress({...newAddress, building_info: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="floor_apartment">Kat/Daire</Label>
                <Input
                  id="floor_apartment"
                  placeholder="Kat 3, Daire 7"
                  value={newAddress.floor_apartment}
                  onChange={(e) => setNewAddress({...newAddress, floor_apartment: e.target.value})}
                />
              </div>
            </div>

            <div>
              <Label htmlFor="phone">Telefon</Label>
              <Input
                id="phone"
                placeholder="+90 XXX XXX XX XX"
                value={newAddress.phone}
                onChange={(e) => setNewAddress({...newAddress, phone: e.target.value})}
              />
            </div>

            <div>
              <Label htmlFor="notes">Adres Tarifi (Opsiyonel)</Label>
              <Input
                id="notes"
                placeholder="Kapıcıya söyleyin, 2. binadan girin vb."
                value={newAddress.notes}
                onChange={(e) => setNewAddress({...newAddress, notes: e.target.value})}
              />
            </div>

            <div className="flex space-x-3 pt-4">
              <Button 
                onClick={handleSaveAddress}
                disabled={loading}
                className="flex-1"
              >
                {loading ? 'Kaydediliyor...' : 'Adresi Kaydet'}
              </Button>
              <Button 
                variant="outline" 
                onClick={() => setShowForm(false)}
                className="flex-1"
              >
                İptal
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {addresses.length === 0 && !showForm && (
        <Card className="text-center py-8">
          <CardContent>
            <div className="text-gray-500 mb-4">
              <div className="text-4xl mb-2">📍</div>
              <p>Henüz kayıtlı adresiniz yok</p>
            </div>
            <Button onClick={() => setShowForm(true)}>
              İlk Adresinizi Ekleyin
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AddressSelector;