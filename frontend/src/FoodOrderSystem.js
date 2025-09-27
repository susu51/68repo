import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import toast from 'react-hot-toast';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

// Restaurant Card Component
const RestaurantCard = ({ restaurant, onClick, userLocation }) => {
  return (
    <Card 
      className="hover:shadow-lg transition-all cursor-pointer group border-2 hover:border-orange-200"
      onClick={() => onClick(restaurant)}
    >
      <div className="relative overflow-hidden">
        {restaurant.image_url ? (
          <img 
            src={`${API.replace('/api', '')}${restaurant.image_url}`}
            alt={restaurant.name}
            className="w-full h-48 object-cover group-hover:scale-105 transition-transform"
            onError={(e) => {
              e.target.src = 'https://via.placeholder.com/400x200/f97316/ffffff?text=🍽️+Restoran';
            }}
          />
        ) : (
          <div className="w-full h-48 bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center">
            <span className="text-white text-6xl">🍽️</span>
          </div>
        )}
        
        <div className="absolute top-2 right-2 space-y-1">
          <Badge className="bg-white text-gray-800 shadow-sm">
            ⭐ {restaurant.rating || '4.5'}
          </Badge>
          {restaurant.distance && userLocation && (
            <Badge className="bg-blue-500 text-white shadow-sm">
              📍 {restaurant.distance.toFixed(1)} km
            </Badge>
          )}
        </div>
        
        {restaurant.is_open && (
          <div className="absolute top-2 left-2">
            <Badge className="bg-green-500 text-white shadow-sm animate-pulse">
              🟢 Açık
            </Badge>
          </div>
        )}
      </div>
      
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-bold text-lg text-gray-800">{restaurant.name}</h3>
          <Badge variant="outline" className="text-xs">
            {restaurant.category === 'gida' ? '🍽️ Restoran' : '📦 Kargo'}
          </Badge>
        </div>
        
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {restaurant.description}
        </p>
        
        <div className="flex justify-between items-center text-xs text-gray-500 mb-2">
          <span className="flex items-center">
            <span className="mr-1">📍</span>
            {restaurant.address || restaurant.location?.name}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span className="flex items-center">
              <span className="mr-1">🚲</span>
              {restaurant.delivery_time} dk
            </span>
            <span className="flex items-center">
              <span className="mr-1">💰</span>
              Min. ₺{restaurant.min_order}
            </span>
            {restaurant.distance && userLocation && (
              <span className="flex items-center text-blue-600 font-semibold">
                <span className="mr-1">📍</span>
                {restaurant.distance.toFixed(1)} km
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Product Card Component
const ProductCard = ({ product, onAddToCart, quantity = 0 }) => {
  const [selectedQuantity, setSelectedQuantity] = useState(quantity);

  const handleAddToCart = () => {
    onAddToCart(product);
    setSelectedQuantity(selectedQuantity + 1);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="flex">
        {/* Product Image */}
        <div className="w-1/3">
          {product.photo_url ? (
            <img 
              src={`${API.replace('/api', '')}${product.photo_url}`}
              alt={product.name}
              className="w-full h-full object-cover rounded-l-lg"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/200x150/f97316/ffffff?text=🍽️';
              }}
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-orange-300 to-red-400 rounded-l-lg flex items-center justify-center">
              <span className="text-white text-4xl">🍽️</span>
            </div>
          )}
        </div>
        
        {/* Product Details */}
        <div className="flex-1 p-4">
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-semibold text-lg">{product.name}</h4>
            <span className="font-bold text-green-600 text-lg">₺{product.price}</span>
          </div>
          
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {product.description}
          </p>
          
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3 text-xs text-gray-500">
              <span>⏱️ {product.preparation_time_minutes} dk</span>
              <Badge 
                variant={product.is_available ? "default" : "secondary"}
                className="text-xs"
              >
                {product.is_available ? '✅ Mevcut' : '❌ Tükendi'}
              </Badge>
            </div>
            
            {product.is_available && (
              <div className="flex items-center space-x-2">
                {selectedQuantity > 0 && (
                  <Badge className="bg-orange-100 text-orange-800">
                    Sepette: {selectedQuantity}
                  </Badge>
                )}
                <Button 
                  onClick={handleAddToCart}
                  className="bg-orange-600 hover:bg-orange-700"
                  size="sm"
                >
                  + Sepete Ekle
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

// Cart Summary Component
const CartSummary = ({ cart, onUpdateCart, onRemoveFromCart, onCheckout }) => {
  const getCartTotal = () => {
    return cart.reduce((total, item) => total + item.subtotal, 0);
  };

  const getDeliveryFee = () => {
    const total = getCartTotal();
    return total > 100 ? 0 : 15; // Free delivery over ₺100
  };

  const getFinalTotal = () => {
    return getCartTotal() + getDeliveryFee();
  };

  if (cart.length === 0) {
    return (
      <Card className="sticky top-4">
        <CardContent className="p-6 text-center">
          <div className="text-4xl mb-2">🛒</div>
          <p className="text-gray-600">Sepetiniz boş</p>
          <p className="text-sm text-gray-500 mt-1">Lezzetli yemekleri keşfedin!</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="sticky top-4">
      <CardHeader>
        <CardTitle className="text-lg">Sepetiniz ({cart.length} ürün)</CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <div className="space-y-3 mb-4">
          {cart.map((item) => (
            <div key={item.product_id} className="flex justify-between items-center">
              <div className="flex-1">
                <h5 className="font-medium text-sm">{item.product_name}</h5>
                <div className="flex items-center space-x-2 mt-1">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => onUpdateCart(item.product_id, -1)}
                    className="h-6 w-6 p-0"
                  >
                    -
                  </Button>
                  <span className="text-sm font-medium">{item.quantity}</span>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => onUpdateCart(item.product_id, 1)}
                    className="h-6 w-6 p-0"
                  >
                    +
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => onRemoveFromCart(item.product_id)}
                    className="h-6 w-6 p-0 text-red-500 hover:text-red-700"
                  >
                    🗑️
                  </Button>
                </div>
              </div>
              <span className="font-semibold text-sm">₺{item.subtotal.toFixed(2)}</span>
            </div>
          ))}
        </div>
        
        <div className="border-t pt-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span>Ara Toplam:</span>
            <span>₺{getCartTotal().toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>Teslimat:</span>
            <span className={getDeliveryFee() === 0 ? 'text-green-600' : ''}>
              {getDeliveryFee() === 0 ? 'Ücretsiz' : `₺${getDeliveryFee()}`}
            </span>
          </div>
          <div className="flex justify-between font-bold text-lg border-t pt-2">
            <span>Toplam:</span>
            <span className="text-green-600">₺{getFinalTotal().toFixed(2)}</span>
          </div>
        </div>
        
        <Button 
          onClick={onCheckout}
          className="w-full mt-4 bg-green-600 hover:bg-green-700"
          disabled={cart.length === 0}
        >
          Siparişi Tamamla 🚀
        </Button>
        
        {getCartTotal() < 100 && (
          <p className="text-xs text-gray-500 text-center mt-2">
            ₺{(100 - getCartTotal()).toFixed(2)} daha ekleyin, ücretsiz teslimat kazanın!
          </p>
        )}
      </CardContent>
    </Card>
  );
};

// Main Food Order System Component
export const ProfessionalFoodOrderSystem = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [originalRestaurants, setOriginalRestaurants] = useState([]); // Store original data
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [userLocation, setUserLocation] = useState(null);
  const [locationError, setLocationError] = useState(null);
  const [sortType, setSortType] = useState('nearest'); // 'nearest' or 'citywide'

  useEffect(() => {
    getUserLocation();
    fetchRestaurants();
  }, []);

  // Re-sort when user location changes (only if using nearest sort)
  useEffect(() => {
    if (userLocation && originalRestaurants.length > 0 && sortType === 'nearest') {
      sortAndFilterRestaurants(originalRestaurants, sortType, userLocation);
    }
  }, [userLocation, sortType]);

  const getUserLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Tarayıcınız konum hizmetlerini desteklemiyor');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        setUserLocation(location);
        console.log('Kullanıcı konumu alındı:', location);
      },
      (error) => {
        console.error('Konum alınamadı:', error);
        setLocationError('Konum erişimi reddedildi. En yakın restoranları gösteriyoruz.');
        // Default to Istanbul center if location denied
        setUserLocation({ lat: 41.0082, lng: 28.9784 });
      },
      { 
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000  // 5 minutes cache
      }
    );
  };

  const calculateDistance = (lat1, lng1, lat2, lng2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const fetchRestaurants = async () => {
    try {
      // Use the new public businesses endpoint
      const response = await axios.get(`${API}/businesses`);
      const businessData = response.data;
      
      setOriginalRestaurants(businessData); // Store original data
      sortAndFilterRestaurants(businessData, sortType, userLocation);
      console.log('Restaurants fetched:', businessData);
    } catch (error) {
      console.error('Restoranlar yüklenemedi:', error);
      toast.error('Restoranlar yüklenirken hata oluştu');
    }
    setLoading(false);
  };

  const sortRestaurantsByDistance = () => {
    if (!userLocation || restaurants.length === 0) return;
    
    const sortedBusinesses = restaurants.map(business => ({
      ...business,
      distance: calculateDistance(
        userLocation.lat, userLocation.lng,
        business.location.lat, business.location.lng
      )
    })).sort((a, b) => a.distance - b.distance);
    
    setRestaurants(sortedBusinesses);
  };

  const sortAndFilterRestaurants = (data, type, location) => {
    let sortedData = [...data];
    
    if (type === 'nearest' && location) {
      // Sort by distance (En Yakın)
      sortedData = data.map(business => ({
        ...business,
        distance: calculateDistance(
          location.lat, location.lng,
          business.location.lat, business.location.lng
        )
      })).sort((a, b) => a.distance - b.distance);
    } else if (type === 'citywide') {
      // Sort by rating for citywide (Şehir Geneli)
      sortedData = data.sort((a, b) => {
        const ratingA = parseFloat(a.rating) || 0;
        const ratingB = parseFloat(b.rating) || 0;
        return ratingB - ratingA; // Higher rating first
      });
    }
    
    setRestaurants(sortedData);
  };

  const handleSortChange = (newSortType) => {
    setSortType(newSortType);
    sortAndFilterRestaurants(originalRestaurants, newSortType, userLocation);
  };

  const fetchProducts = async (restaurantId) => {
    try {
      const response = await axios.get(`${API}/businesses/${restaurantId}/products`);
      setProducts(response.data);
      
      // Extract categories
      const productCategories = [...new Set(response.data.map(p => p.category))];
      setCategories(['all', ...productCategories]);
      setSelectedCategory('all');
    } catch (error) {
      console.error('Ürünler yüklenemedi:', error);
      toast.error('Menü yüklenemedi');
    }
  };

  const handleRestaurantSelect = (restaurant) => {
    setSelectedRestaurant(restaurant);
    setCart([]); // Clear cart when switching restaurants
    fetchProducts(restaurant.id);
  };

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.product_id === product.id);
    
    if (existingItem) {
      setCart(cart.map(item => 
        item.product_id === product.id 
          ? { ...item, quantity: item.quantity + 1, subtotal: (item.quantity + 1) * item.product_price }
          : item
      ));
    } else {
      setCart([...cart, {
        product_id: product.id,
        product_name: product.name,
        product_price: product.price,
        quantity: 1,
        subtotal: product.price
      }]);
    }
    
    toast.success(`${product.name} sepete eklendi! ✨`);
  };

  const updateCartQuantity = (productId, change) => {
    setCart(cart.map(item => {
      if (item.product_id === productId) {
        const newQuantity = Math.max(0, item.quantity + change);
        return {
          ...item,
          quantity: newQuantity,
          subtotal: newQuantity * item.product_price
        };
      }
      return item;
    }).filter(item => item.quantity > 0));
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.product_id !== productId));
    toast.success('Ürün sepetten kaldırıldı');
  };

  const handleCheckout = () => {
    if (cart.length === 0) return;
    
    // Here you would integrate with the order creation system
    toast.success('Sipariş oluşturma sayfasına yönlendiriliyorsunuz...');
    // You could call a parent component function or navigate to checkout
  };

  const filteredProducts = products.filter(product => {
    const matchesCategory = selectedCategory === 'all' || product.category === selectedCategory;
    const matchesSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         product.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Restoranlar yükleniyor...</p>
        </div>
      </div>
    );
  }

  // Restaurant Selection View
  if (!selectedRestaurant) {
    return (
      <div className="max-w-6xl mx-auto p-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">🍽️ DeliverTR Yemek</h1>
          <p className="text-gray-600">En lezzetli yemekler kapınızda!</p>
          
          {/* Sort Options */}
          <div className="mt-6 flex justify-center space-x-4">
            <Button
              onClick={() => handleSortChange('nearest')}
              className={`px-6 py-3 rounded-full font-semibold transition-all ${
                sortType === 'nearest'
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              disabled={!userLocation}
            >
              📍 En Yakın Konum
            </Button>
            <Button
              onClick={() => handleSortChange('citywide')}
              className={`px-6 py-3 rounded-full font-semibold transition-all ${
                sortType === 'citywide'
                  ? 'bg-orange-600 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🏙️ Şehir Geneli
            </Button>
          </div>
          
          {/* Location Status */}
          <div className="mt-4 space-y-2">
            {userLocation && sortType === 'nearest' && (
              <div className="inline-flex items-center space-x-2 bg-green-50 px-4 py-2 rounded-full border border-green-200">
                <span className="text-green-600">📍</span>
                <span className="text-sm text-green-700">Konumunuza göre sıralandı ({restaurants.length} restoran)</span>
              </div>
            )}
            
            {sortType === 'citywide' && (
              <div className="inline-flex items-center space-x-2 bg-orange-50 px-4 py-2 rounded-full border border-orange-200">
                <span className="text-orange-600">⭐</span>
                <span className="text-sm text-orange-700">En yüksek puanlı restoranlar ({restaurants.length} restoran)</span>
              </div>
            )}
            
            {locationError && !userLocation && (
              <div className="inline-flex items-center space-x-2 bg-yellow-50 px-4 py-2 rounded-full border border-yellow-200">
                <span className="text-yellow-600">⚠️</span>
                <span className="text-sm text-yellow-700">{locationError}</span>
                <Button 
                  onClick={getUserLocation}
                  size="sm"
                  variant="outline"
                  className="ml-2 text-xs"
                >
                  🔄 Tekrar Dene
                </Button>
              </div>
            )}
            
            {!userLocation && !locationError && (
              <div className="inline-flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-full border border-blue-200">
                <span className="text-blue-600">🔄</span>
                <span className="text-sm text-blue-700">Konum alınıyor... En yakın restoranları gösterebilmek için</span>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {restaurants.map(restaurant => (
            <RestaurantCard
              key={restaurant.id}
              restaurant={restaurant}
              onClick={handleRestaurantSelect}
              userLocation={userLocation}
            />
          ))}
        </div>

        {restaurants.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🏪</div>
            <h3 className="text-xl font-semibold mb-2">Henüz restoran bulunmuyor</h3>
            <p className="text-gray-600">Yakında lezzetli restoranlar eklenecek!</p>
          </div>
        )}
      </div>
    );
  }

  // Restaurant Menu View
  return (
    <div className="max-w-7xl mx-auto p-4">
      {/* Header */}
      <div className="flex items-center mb-6">
        <Button 
          variant="outline" 
          onClick={() => setSelectedRestaurant(null)}
          className="mr-4"
        >
          ← Restoranlar
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{selectedRestaurant.name}</h1>
          <p className="text-sm text-gray-600">{selectedRestaurant.description}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Menu Section */}
        <div className="lg:col-span-3">
          {/* Search and Filters */}
          <div className="mb-6">
            <Input
              placeholder="Menüde ara... (örn: pizza, burger)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="mb-4"
            />
            
            <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
              <TabsList className="grid w-full grid-cols-auto">
                <TabsTrigger value="all">Tümü</TabsTrigger>
                {categories.filter(cat => cat !== 'all').map(category => (
                  <TabsTrigger key={category} value={category}>
                    {category}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
          </div>

          {/* Products */}
          <div className="space-y-4">
            {filteredProducts.map(product => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={addToCart}
                quantity={cart.find(item => item.product_id === product.id)?.quantity || 0}
              />
            ))}
            
            {filteredProducts.length === 0 && (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">🔍</div>
                <p className="text-gray-600">Aradığınız ürün bulunamadı</p>
              </div>
            )}
          </div>
        </div>

        {/* Cart Section */}
        <div className="lg:col-span-1">
          <CartSummary
            cart={cart}
            onUpdateCart={updateCartQuantity}
            onRemoveFromCart={removeFromCart}
            onCheckout={handleCheckout}
          />
        </div>
      </div>
    </div>
  );
};

export default ProfessionalFoodOrderSystem;