import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'react-hot-toast';
import api from '../../api/http';
import AdvertisementBanner from '../../components/AdvertisementBanner';
import { useCart } from '../../contexts/CartContext';

const DiscoverPage = ({ user, onRestaurantSelect, onTabChange }) => {
  const { addToCart, setRestaurant } = useCart();
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userLocation, setUserLocation] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortMode, setSortMode] = useState('city'); // 'city' (smart address-based) or 'location' (GPS-based)
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [restaurantProducts, setRestaurantProducts] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [userAddresses, setUserAddresses] = useState([]);
  const [showAddressSelector, setShowAddressSelector] = useState(false);

  // Load user's saved addresses when component mounts or user changes
  useEffect(() => {
    console.log('🚀 DISCOVER PAGE - useEffect for address loading triggered');
    console.log('👤 DISCOVER PAGE - User object:', user);
    console.log('🔑 DISCOVER PAGE - User email:', user?.email);
    
    if (user) {
      console.log('✅ DISCOVER PAGE - User exists, calling loadUserAddresses...');
      loadUserAddresses();
    } else {
      console.log('❌ DISCOVER PAGE - No user, skipping address loading');
    }
  }, [user]);

  // Load restaurants when selectedAddress becomes available or changes
  useEffect(() => {
    if (selectedAddress) {
      console.log('🔄 Selected address changed, loading restaurants...');
      loadRestaurants();
    }
  }, [selectedAddress]);

  // Reload restaurants when location or sort mode changes
  useEffect(() => {
    if (sortMode === 'location' && userLocation) {
      console.log('🎯 User location changed, reloading restaurants with location sorting...');
      loadRestaurants();
    } else if (sortMode === 'city' && selectedAddress) {
      console.log('🏙️ Sort mode changed to city, reloading restaurants...');
      loadRestaurants();
    }
  }, [userLocation, sortMode]);

  // Calculate distance between two coordinates using Haversine formula
  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in kilometers
  };

  const loadUserAddresses = async () => {
    try {
      console.log('🔍 DISCOVER PAGE - Loading user addresses for user:', user?.email);
      
      const result = await api.get('/user/addresses');
      console.log('📡 DISCOVER PAGE - Raw API response:', result);
      
      const addresses = result.data || [];
      
      console.log('✅ DISCOVER PAGE - Processed addresses:', addresses.length, addresses);
      
      setUserAddresses(addresses);
      if (addresses && addresses.length > 0) {
        // Use first address as default
        setSelectedAddress(addresses[0]);
        console.log('✅ DISCOVER PAGE - Default address set:', addresses[0]);
      } else {
        console.log('❌ DISCOVER PAGE - No addresses found - userAddresses will be empty array');
      }
    } catch (error) {
      console.error('❌ DISCOVER PAGE - Address loading error:', error);
      console.error('❌ DISCOVER PAGE - Error details:', error.response?.data);
      console.error('❌ DISCOVER PAGE - Error status:', error.response?.status);
    }
  };

  const loadRestaurants = async () => {
    try {
      setLoading(true);
      
      let restaurantsData = [];
      
      // Priority 1: GPS location-based search (if user has shared location)
      if (sortMode === 'location' && userLocation) {
        console.log(`📍 Loading restaurants by GPS location: ${userLocation.lat}, ${userLocation.lng}`);
        
        try {
          // Try to get city from selected address, but GPS search works without it
          const city = selectedAddress?.il || selectedAddress?.city;
          
          // Build params - lat/lng are required, city is optional
          const params = new URLSearchParams({
            lat: userLocation.lat.toString(),
            lng: userLocation.lng.toString(),
            radius: '50' // 50km radius for GPS search
          });
          
          // Add city if available for better filtering
          if (city) {
            params.append('city', city);
            console.log(`📍 GPS search in city: ${city}`);
          } else {
            console.log(`📍 GPS search without city filter (nationwide)`);
          }
          
          const response = await api.get(`/catalog/city-nearby?${params.toString()}`);
          restaurantsData = response.data?.businesses || response.data || [];
          
          console.log(`✅ Loaded ${restaurantsData.length} nearby restaurants`);
          
          // Calculate and add distance to each restaurant
          restaurantsData = restaurantsData.map(restaurant => {
            const distance = restaurant.lat && restaurant.lng 
              ? calculateDistance(userLocation.lat, userLocation.lng, restaurant.lat, restaurant.lng)
              : null;
            return {
              ...restaurant,
              distance,
              business_name: restaurant.name || restaurant.business_name,
              business_category: restaurant.category || restaurant.business_category
            };
          });
          
          // Sort by distance
          restaurantsData.sort((a, b) => {
            if (!a.distance) return 1;
            if (!b.distance) return -1;
            return a.distance - b.distance;
          });
          
          if (restaurantsData.length > 0) {
            toast.success(`${restaurantsData.length} yakın restoran bulundu`);
          } else {
            toast.error('Yakınınızda restoran bulunamadı (50km içinde)');
          }
        } catch (gpsError) {
          console.error('❌ GPS-based loading failed:', gpsError);
          toast.error('GPS ile restoranlar yüklenemedi: ' + gpsError.message);
        }
      }
      // Priority 2: Use selected address (city/district filter)
      else if (selectedAddress) {
        const city = selectedAddress?.il || selectedAddress?.city;
        const district = selectedAddress?.ilce || selectedAddress?.district;
        
        if (city) {
          console.log(`🏙️ Loading restaurants by city/district: ${city}${district ? '/' + district : ''}`);
          
          try {
            const params = new URLSearchParams({
              city: city
            });
            
            if (district) {
              params.append('district', district);
            }
            
            const response = await api.get(`/businesses?${params.toString()}`);
            restaurantsData = response.data || [];
            
            console.log(`✅ Loaded ${restaurantsData.length} restaurants in ${city}${district ? '/' + district : ''}`);
            
            // Add business_name field for compatibility
            restaurantsData = restaurantsData.map(restaurant => ({
              ...restaurant,
              business_name: restaurant.name,
              business_category: restaurant.category
            }));
            
            if (restaurantsData.length > 0) {
              toast.success(`${restaurantsData.length} restoran bulundu`);
            } else {
              toast.error(`${city}${district ? '/' + district : ''} bölgesinde restoran bulunamadı`);
            }
          } catch (addressError) {
            console.error('❌ Address-based loading failed:', addressError);
            toast.error('Restoranlar yüklenemedi');
          }
        } else {
          console.log('⚠️ No city in selected address');
          toast.error('Lütfen şehir bilgisi içeren bir adres seçin');
        }
      } else {
        console.log('⚠️ No address selected');
        toast.error('Lütfen bir teslimat adresi seçin');
      }
      
      setRestaurants(restaurantsData);
      
    } catch (error) {
      console.error('Error loading restaurants:', error);
      toast.error('Restoranlar yüklenirken hata oluştu');
      setRestaurants([]);
    } finally {
      setLoading(false);
    }
  };

  // Get user location
  const requestLocation = () => {
    if (!navigator.geolocation) {
      toast.error('Konum desteği mevcut değil');
      return;
    }

    toast.loading('Konumunuz alınıyor...');
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        toast.dismiss();
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        console.log('✅ GPS konum alındı:', location);
        setUserLocation(location);
        setSortMode('location');
        toast.success(`Konumunuz: ${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`);
        // loadRestaurants will be called by useEffect
      },
      (error) => {
        toast.dismiss();
        console.log('❌ GPS konum hatası:', error);
        toast.error('Konum alınamadı. Lütfen tarayıcı izinlerini kontrol edin.');
        setSortMode('city');
        setLoading(false);
      }
    );
  };

  const handleRestaurantClick = async (restaurant) => {
    // Call parent component's handler to navigate to restaurant menu page
    if (onRestaurantSelect) {
      onRestaurantSelect(restaurant);
    }
  };

  const handleBackToRestaurants = () => {
    setSelectedRestaurant(null);
    setRestaurantProducts([]);
  };

  const filteredRestaurants = restaurants.filter(restaurant => {
    const searchLower = searchQuery.toLowerCase();
    const name = restaurant.business_name || restaurant.name || '';
    const category = restaurant.business_category || restaurant.category || '';
    
    return (
      !searchQuery || // If no search query, show all
      name.toLowerCase().includes(searchLower) ||
      category.toLowerCase().includes(searchLower)
    );
  });
  
  // Restaurants ready for display

  // Restaurant Menu View
  if (selectedRestaurant) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm sticky top-0 z-40">
          <div className="flex items-center p-4">
            <Button 
              variant="ghost" 
              onClick={handleBackToRestaurants}
              className="mr-3 p-2"
            >
              ←
            </Button>
            <div className="flex-1">
              <h1 className="text-lg font-bold text-gray-800">
                {selectedRestaurant.business_name}
              </h1>
              <p className="text-sm text-gray-600">
                {selectedRestaurant.business_category} • 
                <span className="ml-1">⭐ 4.8 • 25-35 dk</span>
              </p>
            </div>
          </div>
        </div>

        {/* Restaurant Info Card */}
        <div className="p-4">
          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-orange-100 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">🍽️</span>
                </div>
                <div className="flex-1">
                  <h2 className="font-bold text-lg">{selectedRestaurant.business_name}</h2>
                  <p className="text-gray-600 text-sm">{selectedRestaurant.description}</p>
                  <div className="flex items-center mt-2 space-x-4">
                    <span className="text-sm">⭐ 4.8 (120+ değerlendirme)</span>
                    <span className="text-sm">🕒 25-35 dk</span>
                    <span className="text-sm">🚚 Ücretsiz teslimat</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Products */}
          {loading ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p>Menü yükleniyor...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {restaurantProducts.map(product => (
                <Card key={product.id} className="overflow-hidden">
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-4">
                      <div className="w-20 h-20 bg-gray-100 rounded-xl overflow-hidden">
                        {product.image_url ? (
                          <img 
                            src={product.image_url} 
                            alt={product.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-2xl">
                            🍽️
                          </div>
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-800">{product.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{product.description}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-lg font-bold text-orange-600">
                            ₺{product.price?.toFixed(2)}
                          </span>
                          <Button
                            onClick={() => {
                              // Set the restaurant first
                              if (selectedRestaurant) {
                                setRestaurant(selectedRestaurant);
                              }
                              // Add product to cart
                              addToCart({
                                id: product.id,
                                name: product.name,
                                description: product.description || '',
                                price: product.price,
                                image: product.image_url,
                                quantity: 1
                              });
                              toast.success(`${product.name} sepete eklendi!`);
                            }}
                            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm"
                          >
                            Sepete Ekle
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {restaurantProducts.length === 0 && (
                <div className="text-center py-8">
                  <span className="text-4xl mb-2 block">🍽️</span>
                  <p className="text-gray-600">Henüz menü eklenmemiş</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Main Discover View
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-40">
        <div className="p-4">
          {/* Location/Address Bar */}
          <div className="flex items-center mb-4">
            <div 
              className="flex-1 bg-gray-100 rounded-xl p-3 mr-3 cursor-pointer hover:bg-gray-200 transition-colors"
              onClick={() => setShowAddressSelector(true)}
            >
              <div className="flex items-center">
                <span className="text-orange-500 mr-2">📍</span>
                <div className="flex-1">
                  {selectedAddress ? (
                    <div>
                      <div className="text-sm font-medium text-gray-800">
                        {selectedAddress.adres_basligi || selectedAddress.label || 'Adresim'}
                      </div>
                      <div className="text-xs text-gray-600 line-clamp-2">
                        {selectedAddress.acik_adres || selectedAddress.full || 
                         `${selectedAddress.mahalle || ''}, ${selectedAddress.ilce || selectedAddress.district || ''}, ${selectedAddress.il || selectedAddress.city || ''}`}
                      </div>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600 cursor-pointer" onClick={() => onTabChange('profile')}>
                      <span className="text-blue-600 underline">Teslimat adresi seçin</span> 
                      <span className="text-xs block text-gray-500">Adres eklemek için tıklayın</span>
                    </div>
                  )}
                </div>
                <span className="text-gray-400 ml-2">▼</span>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={requestLocation}
              className="px-3 py-3"
            >
              📍
            </Button>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Input
              placeholder="Restoran, yemek ara..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 rounded-xl border-gray-200"
            />
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">🔍</span>
          </div>
        </div>
      </div>

      {/* Sort Buttons */}
      <div className="px-4 py-3 bg-white border-b">
        <div className="flex space-x-3">
          <Button
            variant={sortMode === 'location' ? 'default' : 'outline'}
            onClick={() => {
              if (userLocation) {
                setSortMode('location');
              } else {
                requestLocation();
              }
            }}
            className="flex-1"
          >
            📍 GPS Konum
          </Button>
          <Button
            variant={sortMode === 'city' ? 'default' : 'outline'}
            onClick={() => setSortMode('city')}
            className="flex-1"
          >
            🎯 Akıllı Sıralama
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Advertisement Banner */}
        <AdvertisementBanner userCity={selectedAddress?.city || user?.city} />

        {loading ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Restoranlar yükleniyor...</p>
          </div>
        ) : (
          <>
            {/* Status Message */}
            <div className="mb-4">
              <p className="text-sm text-gray-600">
                {sortMode === 'location' 
                  ? `📍 Konumunuza yakın ${filteredRestaurants.length} restoran`
                  : `🏙️ Şehir geneli ${filteredRestaurants.length} restoran`
                }
              </p>
            </div>

            {/* Restaurant List */}
            <div className="space-y-4">
              {filteredRestaurants.map(restaurant => (
                <Card 
                  key={restaurant.id} 
                  className="cursor-pointer hover:shadow-lg transition-all duration-200"
                  onClick={() => handleRestaurantClick(restaurant)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-4">
                      <div className="w-16 h-16 bg-orange-100 rounded-xl overflow-hidden">
                        {restaurant.logo_url ? (
                          <img 
                            src={restaurant.logo_url} 
                            alt={restaurant.business_name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-2xl">
                            🍽️
                          </div>
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-800 mb-1">
                          {restaurant.business_name || restaurant.name || 'İsimsiz Restoran'}
                        </h3>
                        <p className="text-sm text-gray-600 mb-1">
                          {restaurant.business_category || restaurant.category || 'Restoran'}
                        </p>
                        {(restaurant.city || restaurant.district || restaurant.address) && (
                          <p className="text-xs text-blue-600 mb-2 font-medium">
                            📍 {restaurant.address || `${restaurant.district || ''}, ${restaurant.city || ''}`}
                          </p>
                        )}
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>⭐ 4.8</span>
                          <span>🕒 25-35 dk</span>
                          <span>🚚 Ücretsiz</span>
                          <span>Min. ₺50</span>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-xs text-gray-500">
                          {sortMode === 'location' && restaurant.distanceText && (
                            <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                              📍 {restaurant.distanceText}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {filteredRestaurants.length === 0 && (
                <div className="text-center py-16">
                  <span className="text-6xl mb-4 block">🔍</span>
                  <h3 className="text-xl font-bold text-gray-800 mb-2">
                    Restoran bulunamadı
                  </h3>
                  <p className="text-gray-600">
                    Arama kriterlerinizi değiştirip tekrar deneyin
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Address Selector Modal */}
      {showAddressSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-gray-800">Teslimat Adresi Seç</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddressSelector(false)}
                  className="p-1"
                >
                  ✕
                </Button>
              </div>
              
              <div className="space-y-3">
                {userAddresses.length === 0 ? (
                  <div className="text-center py-8">
                    <span className="text-4xl">📍</span>
                    <p className="text-gray-600 mt-2">Henüz kayıtlı adresiniz yok</p>
                    <Button
                      onClick={() => {
                        onTabChange('profile');
                        setShowAddressSelector(false);
                      }}
                      className="mt-4 bg-orange-500 hover:bg-orange-600"
                    >
                      Adres Ekle
                    </Button>
                  </div>
                ) : (
                  userAddresses.map((address) => (
                    <Card 
                      key={address.id} 
                      className={`cursor-pointer hover:shadow-md transition-shadow ${
                        selectedAddress?.id === address.id ? 'ring-2 ring-orange-500' : ''
                      }`}
                      onClick={() => {
                        setSelectedAddress(address);
                        setShowAddressSelector(false);
                        toast.success(`Adres değiştirildi: ${address.adres_basligi || address.label}`);
                      }}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                            📍
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <p className="font-semibold text-gray-800">
                                {address.adres_basligi || address.label}
                              </p>
                              {address.is_default && (
                                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                  Varsayılan
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                              {address.acik_adres || address.full || 
                               `${address.mahalle || ''}, ${address.ilce || address.district || ''}, ${address.il || address.city || ''}`}
                            </p>
                          </div>
                          {selectedAddress?.id === address.id && (
                            <span className="text-orange-500">✓</span>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscoverPage;