import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://order-system-44.preview.emergentagent.com';

export const CustomerDiscover = ({ onSelectBusiness }) => {
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [addresses, setAddresses] = useState([]);

  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    try {
      const response = await axios.get(`${API_BASE}/customer/addresses`, {
        withCredentials: true
      });
      setAddresses(response.data.addresses || []);
      
      // Set default address if exists
      const defaultAddr = response.data.addresses?.find(a => a.is_default);
      if (defaultAddr) {
        setSelectedAddress(defaultAddr);
        discoverFromAddress(defaultAddr);
      }
    } catch (error) {
      console.error('Addresses fetch error:', error);
    }
  };

  const getGPSLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Tarayıcınız GPS desteklemiyor');
      return;
    }

    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        setUserLocation(location);
        discoverBusinesses(location.lat, location.lng);
      },
      (error) => {
        toast.error('GPS konumu alınamadı');
        setLoading(false);
      }
    );
  };

  const discoverFromAddress = async (address) => {
    if (!address.lat || !address.lng) {
      toast.error('Adres konum bilgisi eksik');
      return;
    }
    discoverBusinesses(address.lat, address.lng);
  };

  const discoverBusinesses = async (lat, lng) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/customer/discover`, {
        params: { lat, lng, radius_km: 50 },
        withCredentials: true
      });
      setBusinesses(response.data.businesses || []);
      toast.success(`${response.data.total_found} restoran bulundu`);
    } catch (error) {
      console.error('Discover error:', error);
      toast.error('Restoranlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Location Selector */}
      <Card>
        <CardHeader>
          <CardTitle>📍 Konum Seç</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button onClick={getGPSLocation} className="bg-blue-600" disabled={loading}>
              📱 GPS Konumunu Kullan
            </Button>
            <select
              className="px-3 py-2 border rounded-lg"
              value={selectedAddress?.id || ''}
              onChange={(e) => {
                const addr = addresses.find(a => a.id === e.target.value);
                setSelectedAddress(addr);
                if (addr) discoverFromAddress(addr);
              }}
            >
              <option value="">Kayıtlı Adres Seç</option>
              {addresses.map(addr => (
                <option key={addr.id} value={addr.id}>
                  {addr.title} - {addr.city}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Business List */}
      {loading && (
        <div className="text-center py-12">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p>Restoranlar aranıyor...</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {businesses.map((business) => (
          <Card key={business.id} className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => onSelectBusiness && onSelectBusiness(business)}>
            <CardContent className="p-4">
              {business.image_url && (
                <img src={business.image_url} alt={business.name} className="w-full h-40 object-cover rounded-lg mb-3" />
              )}
              <h3 className="text-lg font-bold mb-2">{business.name}</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p>📍 {business.distance_km} km uzaklıkta</p>
                <p>🏙️ {business.city}</p>
                <p>⭐ {business.rating}/5</p>
                {business.cuisine_type && <p>🍴 {business.cuisine_type}</p>}
              </div>
              <Button className="w-full mt-3 bg-green-600">
                Menüyü Gör
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {businesses.length === 0 && !loading && (
        <Card className="bg-yellow-50">
          <CardContent className="p-12 text-center">
            <p className="text-5xl mb-4">🍴</p>
            <p className="text-gray-700">Yakınınızda restoran bulunamadı</p>
            <p className="text-sm text-gray-600 mt-2">GPS konumunuzu açın veya kayıtlı adres seçin</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CustomerDiscover;