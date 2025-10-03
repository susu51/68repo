import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
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

export const NearbyRestaurants = ({ 
  address = null,
  city = null, 
  lat = null, 
  lng = null, 
  radius = 50000,
  onBack,
  onRestaurantSelect 
}) => {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showLocationPermission, setShowLocationPermission] = useState(false);
  const [showCitySelector, setShowCitySelector] = useState(false);
  const [selectedCity, setSelectedCity] = useState(city || 'İstanbul');
  const [locationError, setLocationError] = useState(null);

  useEffect(() => {
    loadRestaurants();
  }, [city, lat, lng]);

  const loadRestaurants = async () => {
    try {
      setLoading(true);
      setLocationError(null);
      
      let url = `${API}/restaurants`;
      let params = new URLSearchParams();

      // Priority: lat/lng > city > ask for location > city selector
      if (lat && lng) {
        url = `${API}/restaurants/near`;
        params.append('lat', lat.toString());
        params.append('lng', lng.toString());
        params.append('radius', radius.toString());
      } else if (city) {
        params.append('city', city);
      } else {
        // No location data, ask user
        setShowLocationPermission(true);
        setLoading(false);
        return;
      }

      const finalUrl = `${url}?${params.toString()}`;
      console.log('Fetching restaurants from:', finalUrl);

      const response = await axios.get(finalUrl);
      const restaurantList = response.data || [];
      
      // Sort by distance if available
      const sortedRestaurants = restaurantList.sort((a, b) => {
        if (a.distance && b.distance) {
          return a.distance - b.distance;
        }
        return 0;
      });

      setRestaurants(sortedRestaurants);
      
      if (restaurantList.length === 0) {
        const locationText = lat && lng ? 
          `50km yakınında` : 
          `${city || selectedCity} şehrinde`;
        toast.error(`${locationText} restoran bulunamadı.`);
      } else {
        const locationText = lat && lng ? 
          `Yakınınızda ${restaurantList.length} restoran bulundu` : 
          `${city || selectedCity} şehrinde ${restaurantList.length} restoran bulundu`;
        toast.success(locationText);
      }

    } catch (error) {
      console.error('Error loading restaurants:', error);
      setLocationError('Restoranlar yüklenirken hata oluştu');
      toast.error('Restoranlar yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const requestLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const currentLat = position.coords.latitude;
          const currentLng = position.coords.longitude;
          
          // Update URL or call parent with new coordinates
          loadRestaurantsWithLocation(currentLat, currentLng);
          setShowLocationPermission(false);
          toast.success('Konum alındı! Yakındaki restoranlar yükleniyor...');
        },
        (error) => {
          console.error('Geolocation error:', error);
          setShowLocationPermission(false);
          setShowCitySelector(true);
          toast.error('Konum izni verilmedi. Şehir seçiniz.');
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 600000 // 10 minutes cache
        }
      );
    } else {
      setShowLocationPermission(false);
      setShowCitySelector(true);
      toast.error('Tarayıcınız konum servisini desteklemiyor.');
    }
  };

  const loadRestaurantsWithLocation = async (latitude, longitude) => {
    try {
      setLoading(true);
      
      const url = `${API}/restaurants/near?lat=${latitude}&lng=${longitude}&radius=${radius}`;
      const response = await axios.get(url);
      const restaurantList = response.data || [];
      
      // Sort by distance
      const sortedRestaurants = restaurantList.sort((a, b) => {
        if (a.distance && b.distance) {
          return a.distance - b.distance;
        }
        return 0;
      });

      setRestaurants(sortedRestaurants);
      
      if (restaurantList.length === 0) {
        toast.error('50km yakınında restoran bulunamadı.');
      } else {
        toast.success(`Yakınınızda ${restaurantList.length} restoran bulundu`);
      }
      
    } catch (error) {
      console.error('Error loading restaurants with location:', error);
      setLocationError('Konum bazlı arama başarısız');
      // Fallback to city selector
      setShowCitySelector(true);
    } finally {
      setLoading(false);
    }
  };

  const searchByCity = async () => {
    try {
      setLoading(true);
      setShowCitySelector(false);
      
      const url = `${API}/restaurants?city=${selectedCity}`;
      const response = await axios.get(url);
      const restaurantList = response.data || [];
      
      setRestaurants(restaurantList);
      
      if (restaurantList.length === 0) {
        toast.error(`${selectedCity} şehrinde restoran bulunamadı.`);
      } else {
        toast.success(`${selectedCity} şehrinde ${restaurantList.length} restoran bulundu`);
      }
      
    } catch (error) {
      console.error('Error loading restaurants by city:', error);
      toast.error('Şehir bazlı arama başarısız');
    } finally {
      setLoading(false);
    }
  };

  const formatDistance = (distance) => {
    if (!distance) return '';
    if (distance < 1) {
      return `${Math.round(distance * 1000)}m`;
    }
    return `${distance.toFixed(1)}km`;
  };

  if (showLocationPermission) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardContent className="p-8">
            <div className="mb-6">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📍</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                Yakındaki Restoranları Bul
              </h3>
              <p className="text-gray-600 mb-6">
                Size en yakın restoranları göstermek için konum iznine ihtiyacımız var.
              </p>
              
              <div className="space-y-3">
                <Button 
                  onClick={requestLocation}
                  className="w-full bg-orange-500 hover:bg-orange-600"
                >
                  📍 Konumu Aç
                </Button>
                
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setShowLocationPermission(false);
                    setShowCitySelector(true);
                  }}
                  className="w-full"
                >
                  🏙️ Şehir Seç
                </Button>
                
                {onBack && (
                  <Button 
                    variant="ghost" 
                    onClick={onBack}
                    className="w-full"
                  >
                    ← Geri Dön
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Restoranlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">🍽️ Restoranlar</h1>
              {address && (
                <p className="text-gray-600 mt-1">
                  📍 {address.label} - {address.city}
                </p>
              )}
              {lat && lng && (
                <p className="text-sm text-green-600">
                  Konum bazlı listeleme (50km yarıçap)
                </p>
              )}
              {city && !lat && !lng && (
                <p className="text-sm text-blue-600">
                  {city} şehri bazlı listeleme
                </p>
              )}
            </div>
            {onBack && (
              <Button variant="outline" onClick={onBack}>
                ← Geri
              </Button>
            )}
          </div>
          
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={requestLocation}
            >
              📍 Yakınımdakiler
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setShowCitySelector(true)}
            >
              🏙️ Şehir Değiştir
            </Button>
          </div>
        </div>

        {/* Error State */}
        {locationError && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <CardContent className="p-4">
              <p className="text-red-600">⚠️ {locationError}</p>
            </CardContent>
          </Card>
        )}

        {/* Restaurant List */}
        {restaurants.length === 0 ? (
          <Card className="text-center py-12">
            <CardContent>
              <div className="mb-6">
                <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-4xl">🍽️</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-2">
                  Restoran bulunamadı
                </h3>
                <p className="text-gray-600 mb-6">
                  {lat && lng ? 
                    'Bu konumda 50km yakınında restoran bulunmuyor.' :
                    `${city || selectedCity} şehrinde restoran bulunmuyor.`
                  }
                </p>
                <div className="space-x-2">
                  <Button 
                    onClick={() => setShowCitySelector(true)}
                    variant="outline"
                  >
                    🏙️ Farklı Şehir Dene
                  </Button>
                  <Button 
                    onClick={requestLocation}
                    className="bg-orange-500 hover:bg-orange-600"
                  >
                    📍 Konum ile Dene
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {restaurants.map((restaurant, index) => (
              <Card key={index} className="hover:shadow-lg transition-all duration-200 cursor-pointer">
                <CardContent className="p-0">
                  {/* Restaurant Image */}
                  <div className="h-48 bg-gradient-to-br from-orange-400 to-red-400 rounded-t-lg flex items-center justify-center">
                    <span className="text-4xl">🍽️</span>
                  </div>
                  
                  <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-bold text-gray-800 line-clamp-1">
                        {restaurant.name || restaurant.business_name || 'Restoran'}
                      </h3>
                      {restaurant.distance && (
                        <Badge variant="secondary" className="text-xs">
                          {formatDistance(restaurant.distance)}
                        </Badge>
                      )}
                    </div>

                    {/* Category & Rating */}
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm text-gray-600">
                        {restaurant.category || restaurant.business_category || 'Restoran'}
                      </span>
                      <div className="flex items-center">
                        <span className="text-yellow-500 mr-1">⭐</span>
                        <span className="text-sm font-medium">
                          {restaurant.rating || '4.0'}
                        </span>
                      </div>
                    </div>

                    {/* Details */}
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">⏱️ Teslimat</span>
                        <span className="font-medium">
                          {restaurant.delivery_time || '25-35 dk'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">💰 Min. Tutar</span>
                        <span className="font-medium">
                          ₺{restaurant.min_order || '30'}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        📍 {restaurant.location?.name || restaurant.address || 'Adres bilgisi yok'}
                      </div>
                    </div>

                    {/* Status */}
                    <div className="flex items-center justify-between mb-4">
                      <Badge 
                        variant={restaurant.is_open !== false ? "default" : "secondary"}
                        className={restaurant.is_open !== false ? "bg-green-100 text-green-800" : ""}
                      >
                        {restaurant.is_open !== false ? "🟢 Açık" : "🔴 Kapalı"}
                      </Badge>
                    </div>

                    {/* Action Button */}
                    <Button 
                      className="w-full bg-orange-500 hover:bg-orange-600"
                      onClick={() => onRestaurantSelect && onRestaurantSelect(restaurant)}
                      disabled={restaurant.is_open === false}
                    >
                      {restaurant.is_open === false ? '❌ Kapalı' : '🛒 Sipariş Ver'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* City Selector Modal */}
        <Dialog open={showCitySelector} onOpenChange={setShowCitySelector}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>🏙️ Şehir Seçin</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <Select 
                value={selectedCity} 
                onValueChange={setSelectedCity}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {turkishCities.map(cityOption => (
                    <SelectItem key={cityOption} value={cityOption}>
                      {cityOption}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  onClick={() => setShowCitySelector(false)}
                  className="flex-1"
                >
                  ❌ İptal
                </Button>
                <Button 
                  onClick={searchByCity}
                  className="flex-1 bg-orange-500 hover:bg-orange-600"
                >
                  🔍 Ara
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default NearbyRestaurants;