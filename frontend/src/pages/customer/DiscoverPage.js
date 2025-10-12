import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'react-hot-toast';
import api from '../../api/http';

const DiscoverPage = ({ user, onRestaurantSelect, onTabChange }) => {
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

  // Load restaurants on component mount
  useEffect(() => {
    loadRestaurants();
  }, []);

  // Reload restaurants when location or sort mode changes
  useEffect(() => {
    if (sortMode === 'location' && userLocation) {
      console.log('🎯 User location changed, reloading restaurants with location sorting...');
      loadRestaurants();
    }
  }, [userLocation, sortMode]);

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
      
      const response = await api.get('/user/addresses');
      console.log('📡 DISCOVER PAGE - Raw API response:', response);
      console.log('📊 DISCOVER PAGE - Response status:', response.status);
      console.log('📄 DISCOVER PAGE - Response data:', response.data);
      
      const addresses = response.data || response || [];
      
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
      
      // Get all restaurants first
      const response = await api.get('/businesses');
      let restaurantsData = response.data || [];
      
      console.log(`📍 Loaded ${restaurantsData.length} restaurants`);
      console.log('🔍 Sort mode:', sortMode, 'Selected address:', selectedAddress);
      console.log('🌍 User location:', userLocation);
      
      if (sortMode === 'location' && userLocation) {
        // Distance-based sorting (GPS location)
        restaurantsData = restaurantsData.map(restaurant => {
          // Get restaurant coordinates - support multiple formats
          const restaurantLat = restaurant.lat || restaurant.location?.lat || 0;
          const restaurantLng = restaurant.lng || restaurant.location?.lng || 0;
          
          const distance = calculateDistance(
            userLocation.lat,
            userLocation.lng,
            restaurantLat,
            restaurantLng
          );
          
          return {
            ...restaurant,
            distance: distance,
            distanceText: distance < 1 ? 
              `${Math.round(distance * 1000)}m` : 
              `${distance.toFixed(1)}km`
          };
        });
        
        // Sort by distance (closest first)
        restaurantsData.sort((a, b) => a.distance - b.distance);
        
        console.log(`🎯 Sorted ${restaurantsData.length} restaurants by GPS distance`);
        console.log('📊 Closest restaurants:', restaurantsData.slice(0, 3).map(r => 
          `${r.business_name || r.name}: ${r.distanceText}`
        ));
        
        toast.success(`${restaurantsData.length} restoran mesafeye göre sıralandı`);
      } else if (selectedAddress && selectedAddress.city) {
        // Address-based smart sorting: District → City → All
        console.log('🏘️ Implementing smart city/district-based sorting...');
        console.log('📍 Customer address:', selectedAddress.city, selectedAddress.district);
        
        // Categorize restaurants by location relevance
        const sameDistrict = [];
        const sameCity = [];
        const others = [];
        
        restaurantsData.forEach(restaurant => {
          const restaurantCity = restaurant.city?.toLowerCase();
          const restaurantDistrict = restaurant.district?.toLowerCase();
          const customerCity = selectedAddress.city?.toLowerCase();
          const customerDistrict = selectedAddress.district?.toLowerCase();
          
          if (restaurantCity === customerCity && restaurantDistrict === customerDistrict) {
            sameDistrict.push(restaurant);
          } else if (restaurantCity === customerCity) {
            sameCity.push(restaurant);
          } else {
            others.push(restaurant);
          }
        });
        
        // Combine in priority order: District → City (NO OTHERS - city filter!)
        restaurantsData = [...sameDistrict, ...sameCity];
        
        console.log(`📊 City-filtered results:`);
        console.log(`  🎯 Same district (${selectedAddress.district}): ${sameDistrict.length}`);
        console.log(`  🏙️ Same city (${selectedAddress.city}): ${sameCity.length}`);
        console.log(`  🚫 Other cities excluded: ${others.length}`);
        
        if (restaurantsData.length === 0) {
          toast.error(`${selectedAddress.city} şehrinde restoran bulunamadı`);
        } else if (sameDistrict.length > 0) {
          toast.success(`${sameDistrict.length} restoran ${selectedAddress.district} ilçesinde, ${sameCity.length} restoran ${selectedAddress.city} genelinde`);
        } else if (sameCity.length > 0) {
          toast.success(`${sameCity.length} restoran ${selectedAddress.city} şehrinde bulundu`);
        }
      } else {
        // Fallback: Show all active restaurants
        console.log(`📋 Showing all ${restaurantsData.length} restaurants (no address filter)`);
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

    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        setUserLocation(location);
        setSortMode('location');
        toast.success('Konum alındı, yakın restoranlar gösteriliyor');
      },
      (error) => {
        console.log('Location error:', error);
        toast.error('Konum alınamadı, şehir geneli gösteriliyor');
        setSortMode('city');
        setLoading(false);
      }
    );
  };

  // Reload restaurants when sort mode changes or selected address changes
  useEffect(() => {
    loadRestaurants();
  }, [sortMode, userLocation, selectedAddress]);

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
                              onAddToCart(product);
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
                        {selectedAddress.label || 'Adresim'} • {selectedAddress.city}
                      </div>
                      <div className="text-xs text-gray-600">
                        {selectedAddress.description}
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
                        toast.success(`Adres değiştirildi: ${address.label}`);
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
                                {address.label}
                              </p>
                              <span className="text-sm bg-orange-100 text-orange-800 px-2 py-1 rounded">
                                {address.city}
                              </span>
                              {address.is_default && (
                                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                  Varsayılan
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              {address.description}
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