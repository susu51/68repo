import React, { useState, useEffect } from 'react';
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import toast from 'react-hot-toast';

export const LocationControls = ({ 
  onLocationChange, 
  currentLocation = null,
  locationMode = 'city',
  onLocationModeChange 
}) => {
  const [locationLoading, setLocationLoading] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [selectedCity, setSelectedCity] = useState('İstanbul');
  const [locationError, setLocationError] = useState(null);

  const turkishCities = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", 
    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", 
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", 
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", 
    "Giresun", "Gümüşhane", "Hakkâri", "Hatay", "Isparta", "Mersin", "İstanbul", 
    "İzmir", "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", 
    "Konya", "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", 
    "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt", 
    "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", 
    "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", 
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova", 
    "Karabük", "Kilis", "Osmaniye", "Düzce"
  ];

  // Get user's current location using browser geolocation
  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Tarayıcınız konum servislerini desteklemiyor');
      return;
    }

    setLocationLoading(true);
    setLocationError(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        
        try {
          // Reverse geocoding to get city/district info
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=10&addressdetails=1`
          );
          
          if (response.ok) {
            const data = await response.json();
            const address = data.address || {};
            
            const locationInfo = {
              latitude,
              longitude,
              city: address.city || address.state || address.county || 'Bilinmeyen Şehir',
              district: address.town || address.suburb || address.neighbourhood || null,
              address: data.display_name || 'Konum bilgisi alınamadı'
            };
            
            setUserLocation(locationInfo);
            onLocationChange(locationInfo);
            toast.success(`📍 Konumunuz: ${locationInfo.city}${locationInfo.district ? `, ${locationInfo.district}` : ''}`);
          } else {
            throw new Error('Konum bilgisi alınamadı');
          }
        } catch (error) {
          console.error('Reverse geocoding error:', error);
          const basicLocation = {
            latitude,
            longitude,
            city: 'Konum Tespit Edildi',
            district: null,
            address: `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
          };
          
          setUserLocation(basicLocation);
          onLocationChange(basicLocation);
          toast.success('📍 Konumunuz tespit edildi');
        }
        
        setLocationLoading(false);
      },
      (error) => {
        setLocationLoading(false);
        let errorMessage = 'Konum alınamadı';
        
        switch(error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Konum izni reddedildi. Lütfen tarayıcı ayarlarından konum izni verin.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Konum bilgisi kullanılamıyor.';
            break;
          case error.TIMEOUT:
            errorMessage = 'Konum tespiti zaman aşımına uğradı.';
            break;
        }
        
        setLocationError(errorMessage);
        toast.error(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000 // 5 minutes
      }
    );
  };

  // Handle city selection
  const handleCityChange = (city) => {
    setSelectedCity(city);
    const cityLocation = {
      city,
      district: null,
      latitude: null,
      longitude: null,
      address: city
    };
    onLocationChange(cityLocation);
  };

  // Handle location mode change
  const handleModeChange = (mode) => {
    onLocationModeChange(mode);
    
    if (mode === 'nearest' && !userLocation) {
      getCurrentLocation();
    } else if (mode === 'city') {
      handleCityChange(selectedCity);
    }
  };

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex flex-col space-y-4">
          {/* Mode Selection */}
          <div className="flex flex-col sm:flex-row gap-2">
            <Button
              variant={locationMode === 'nearest' ? 'default' : 'outline'}
              onClick={() => handleModeChange('nearest')}
              disabled={locationLoading}
              className="flex-1 flex items-center justify-center space-x-2"
            >
              <span className="text-lg">📍</span>
              <span>En Yakınım</span>
              {locationMode === 'nearest' && userLocation && (
                <Badge variant="secondary" className="ml-2">
                  {userLocation.city}
                </Badge>
              )}
            </Button>
            
            <Button
              variant={locationMode === 'city' ? 'default' : 'outline'}
              onClick={() => handleModeChange('city')}
              className="flex-1 flex items-center justify-center space-x-2"
            >
              <span className="text-lg">🏙️</span>
              <span>Şehir Geneli</span>
              {locationMode === 'city' && (
                <Badge variant="secondary" className="ml-2">
                  {selectedCity}
                </Badge>
              )}
            </Button>
          </div>

          {/* Location Details */}
          <div className="bg-gray-50 rounded-lg p-3">
            {locationMode === 'nearest' && (
              <div className="space-y-2">
                {locationLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                    <span className="text-sm text-gray-600">Konumunuz tespit ediliyor...</span>
                  </div>
                ) : userLocation ? (
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="text-sm font-medium">
                        {userLocation.city}{userLocation.district && `, ${userLocation.district}`}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 ml-6">
                      Mesafe öncelikli sıralama aktif
                    </p>
                  </div>
                ) : locationError ? (
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-red-600">❌</span>
                      <span className="text-sm text-red-600">Konum alınamadı</span>
                    </div>
                    <p className="text-xs text-gray-500 ml-6">{locationError}</p>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={getCurrentLocation}
                      className="ml-6 mt-2"
                    >
                      🔄 Tekrar Dene
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-blue-600">📍</span>
                      <span className="text-sm">Konumunuzu tespit etmek için tıklayın</span>
                    </div>
                    <Button 
                      size="sm" 
                      onClick={getCurrentLocation}
                      className="ml-6 bg-orange-600 hover:bg-orange-700"
                    >
                      📍 Şu Anki Konumum
                    </Button>
                  </div>
                )}
              </div>
            )}

            {locationMode === 'city' && (
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="text-blue-600">🏙️</span>
                  <span className="text-sm font-medium">Şehir seçimi</span>
                </div>
                <Select value={selectedCity} onValueChange={handleCityChange}>
                  <SelectTrigger className="ml-6 max-w-xs">
                    <SelectValue placeholder="Şehir seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {turkishCities.map((city) => (
                      <SelectItem key={city} value={city}>
                        {city}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 ml-6">
                  Seçilen şehirdeki tüm aktif restoranlar gösteriliyor
                </p>
              </div>
            )}
          </div>

          {/* Location Stats */}
          <div className="flex justify-between items-center text-xs text-gray-500 border-t pt-2">
            <span>
              {locationMode === 'nearest' ? '📍 Mesafeye göre sıralı' : '🏙️ Şehir geneli'}
            </span>
            <span>
              {currentLocation && (
                locationMode === 'nearest' && userLocation
                  ? `${userLocation.latitude?.toFixed(4)}, ${userLocation.longitude?.toFixed(4)}`
                  : `📍 ${selectedCity}`
              )}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LocationControls;