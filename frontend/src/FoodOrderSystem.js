import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import toast from 'react-hot-toast';
import AddressSelector from './components/AddressSelector';
import { renderLocation } from './utils/renderSafe';

const API = `${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001'}/api`;

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
            {renderLocation(restaurant.address || restaurant.location)}
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

// Enhanced Product Card Component
const ProductCard = ({ product, onAddToCart, quantity = 0 }) => {
  const [selectedQuantity, setSelectedQuantity] = useState(quantity);
  const [isHovered, setIsHovered] = useState(false);

  const handleQuickAdd = () => {
    onAddToCart(product);
    setSelectedQuantity(selectedQuantity + 1);
  };

  const handleAddToCart = () => {
    onAddToCart(product);
    setSelectedQuantity(selectedQuantity + 1);
  };

  // Determine product badges
  const getProductBadges = () => {
    const badges = [];
    
    if (product.is_popular) badges.push({ text: 'Popüler', color: 'bg-red-500', icon: '🔥' });
    if (product.is_new) badges.push({ text: 'Yeni', color: 'bg-green-500', icon: '✨' });
    if (product.discount_percentage) badges.push({ text: `%${product.discount_percentage} İndirim`, color: 'bg-orange-500', icon: '💸' });
    if (product.is_spicy) badges.push({ text: 'Acılı', color: 'bg-red-600', icon: '🌶️' });
    if (product.is_vegetarian) badges.push({ text: 'Vejeteryan', color: 'bg-green-600', icon: '🥗' });
    
    return badges;
  };

  const badges = getProductBadges();

  return (
    <Card 
      className="hover:shadow-lg transition-all duration-300 group relative overflow-hidden"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex">
        {/* Product Image */}
        <div className="w-1/3 relative">
          {product.photo_url ? (
            <img 
              src={`${API.replace('/api', '')}${product.photo_url}`}
              alt={product.name}
              className="w-full h-32 object-cover rounded-l-lg group-hover:scale-105 transition-transform"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/200x150/f97316/ffffff?text=🍽️';
              }}
            />
          ) : (
            <div className="w-full h-32 bg-gradient-to-br from-orange-300 to-red-400 rounded-l-lg flex items-center justify-center group-hover:scale-105 transition-transform">
              <span className="text-white text-4xl">🍽️</span>
            </div>
          )}
          
          {/* Product Badges */}
          <div className="absolute top-2 left-2 space-y-1">
            {badges.slice(0, 2).map((badge, index) => (
              <Badge 
                key={index}
                className={`${badge.color} text-white text-xs shadow-sm`}
              >
                <span className="mr-1">{badge.icon}</span>
                {badge.text}
              </Badge>
            ))}
          </div>

          {/* Quick Add Button (appears on hover) */}
          {product.is_available && isHovered && (
            <Button
              onClick={handleQuickAdd}
              className="absolute bottom-2 right-2 bg-orange-600 hover:bg-orange-700 text-white rounded-full w-8 h-8 p-0 shadow-lg transform transition-all duration-200"
            >
              +
            </Button>
          )}
        </div>
        
        {/* Product Details */}
        <div className="flex-1 p-4">
          <div className="flex justify-between items-start mb-2">
            <div className="flex-1">
              <h4 className="font-semibold text-lg group-hover:text-orange-600 transition-colors">{product.name}</h4>
              {product.category && (
                <span className="text-xs text-gray-500 capitalize">{product.category}</span>
              )}
            </div>
            <div className="text-right ml-3">
              {product.discount_percentage ? (
                <div>
                  <span className="font-bold text-green-600 text-lg">₺{(product.price * (1 - product.discount_percentage / 100)).toFixed(2)}</span>
                  <span className="text-sm text-gray-500 line-through ml-1">₺{product.price}</span>
                </div>
              ) : (
                <span className="font-bold text-green-600 text-lg">₺{product.price}</span>
              )}
            </div>
          </div>
          
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {product.description}
          </p>
          
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3 text-xs text-gray-500">
              <span className="flex items-center">
                <span className="mr-1">⏱️</span>
                {product.preparation_time_minutes || 15} dk
              </span>
              {product.rating && (
                <span className="flex items-center">
                  <span className="mr-1">⭐</span>
                  {product.rating}
                </span>
              )}
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
// Enhanced Product Card Component with more features
const EnhancedProductCard = ({ product, onAddToCart, quantity = 0 }) => {
  const [selectedQuantity, setSelectedQuantity] = useState(quantity);
  const [isHovered, setIsHovered] = useState(false);

  const handleQuickAdd = () => {
    onAddToCart(product);
    setSelectedQuantity(selectedQuantity + 1);
  };

  const handleAddToCart = () => {
    onAddToCart(product);
    setSelectedQuantity(selectedQuantity + 1);
  };

  // Determine product badges
  const getProductBadges = () => {
    const badges = [];
    
    if (product.is_popular) badges.push({ text: 'Popüler', color: 'bg-red-500', icon: '🔥' });
    if (product.is_new) badges.push({ text: 'Yeni', color: 'bg-green-500', icon: '✨' });
    if (product.discount_percentage) badges.push({ text: `%${product.discount_percentage} İndirim`, color: 'bg-orange-500', icon: '💸' });
    if (product.is_spicy) badges.push({ text: 'Acılı', color: 'bg-red-600', icon: '🌶️' });
    if (product.is_vegetarian) badges.push({ text: 'Vejeteryan', color: 'bg-green-600', icon: '🥗' });
    
    return badges;
  };

  const badges = getProductBadges();

  return (
    <Card 
      className="hover:shadow-xl transition-all duration-300 group relative overflow-hidden border-2 hover:border-orange-200"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative">
        {/* Product Image */}
        <div className="relative h-48 overflow-hidden">
          {product.photo_url ? (
            <img 
              src={`${API.replace('/api', '')}${product.photo_url}`}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
              onError={(e) => {
                e.target.src = 'https://via.placeholder.com/400x200/f97316/ffffff?text=🍽️';
              }}
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-orange-300 to-red-400 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              <span className="text-white text-6xl">🍽️</span>
            </div>
          )}
          
          {/* Product Badges */}
          <div className="absolute top-3 left-3 space-y-2">
            {badges.slice(0, 2).map((badge, index) => (
              <Badge 
                key={index}
                className={`${badge.color} text-white text-xs shadow-lg`}
              >
                <span className="mr-1">{badge.icon}</span>
                {badge.text}
              </Badge>
            ))}
          </div>

          {/* Price Badge */}
          <div className="absolute top-3 right-3">
            {product.discount_percentage ? (
              <div className="bg-white rounded-lg p-2 shadow-lg">
                <span className="font-bold text-green-600 text-lg">₺{(product.price * (1 - product.discount_percentage / 100)).toFixed(2)}</span>
                <span className="text-sm text-gray-500 line-through block">₺{product.price}</span>
              </div>
            ) : (
              <div className="bg-white rounded-lg p-2 shadow-lg">
                <span className="font-bold text-green-600 text-lg">₺{product.price}</span>
              </div>
            )}
          </div>

          {/* Quick Add Button (appears on hover) */}
          {product.is_available && isHovered && (
            <Button
              onClick={handleQuickAdd}
              className="absolute bottom-3 right-3 bg-orange-600 hover:bg-orange-700 text-white rounded-full w-12 h-12 p-0 shadow-lg transform transition-all duration-200 hover:scale-110"
            >
              <span className="text-xl">+</span>
            </Button>
          )}

          {/* Availability Overlay */}
          {!product.is_available && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <Badge className="bg-red-500 text-white text-lg px-4 py-2">
                ❌ Tükendi
              </Badge>
            </div>
          )}
        </div>
        
        {/* Product Details */}
        <div className="p-4">
          <div className="flex justify-between items-start mb-2">
            <div className="flex-1">
              <h4 className="font-bold text-xl group-hover:text-orange-600 transition-colors">{product.name}</h4>
              {product.category && (
                <span className="text-sm text-gray-500 capitalize">{product.category}</span>
              )}
            </div>
          </div>
          
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">
            {product.description}
          </p>
          
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span className="flex items-center">
                <span className="mr-1">⏱️</span>
                {product.preparation_time_minutes || 15} dk
              </span>
              {product.rating && (
                <span className="flex items-center">
                  <span className="mr-1">⭐</span>
                  {product.rating}
                </span>
              )}
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
                  className="bg-orange-600 hover:bg-orange-700 text-white"
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
          className="w-full mt-4 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg shadow-lg hover:shadow-xl transition-all"
          disabled={cart.length === 0}
        >
          <div className="flex items-center justify-center space-x-2">
            <span>🛒</span>
            <span>Siparişi Tamamla</span>
            <span className="font-bold">₺{getCartTotal().toFixed(2)}</span>
          </div>
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
export const ProfessionalFoodOrderSystem = ({ 
  user, 
  locationFilter = 'city', 
  userLocation: propUserLocation = null, 
  selectedCity = 'İstanbul',
  cart = [],
  onUpdateCart,
  onAddToCart,
  onRemoveFromCart
}) => {
  const [restaurants, setRestaurants] = useState([]);
  const [originalRestaurants, setOriginalRestaurants] = useState([]); // Store original data
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [products, setProducts] = useState([]);
  // Remove local cart state - now using props
  // const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [userLocation, setUserLocation] = useState(propUserLocation);
  const [locationError, setLocationError] = useState(null);
  const [sortType, setSortType] = useState(locationFilter === 'nearest' ? 'nearest' : 'citywide');
  const [isMounted, setIsMounted] = useState(true); // Track component mount status
  const [activeMenuTab, setActiveMenuTab] = useState('all'); // 'all', 'food', 'drinks'
  const [sortBy, setSortBy] = useState('popularity');
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [showAvailableOnly, setShowAvailableOnly] = useState(false);

  // Menu categories for filtering
  const menuCategories = [
    'Tümü', 'Ana Yemek', 'Pizza', 'Burger', 'Döner', 'Kebap', 
    'Pasta', 'Çorba', 'Salata', 'Tatlı', 'İçecek', 'Kahve', 'Çay'
  ];

  useEffect(() => {
    setIsMounted(true);
    
    // Use prop location or get from browser
    if (propUserLocation) {
      setUserLocation(propUserLocation);
    } else if (locationFilter === 'nearest') {
      getUserLocation();
    }
    
    // Always fetch restaurants on mount
    const timeoutId = setTimeout(() => {
      if (isMounted) {
        fetchRestaurants();
      }
    }, 100);
    
    // Cleanup function
    return () => {
      setIsMounted(false);
      clearTimeout(timeoutId);
      // Clear any pending state updates
      setLoading(false);
      setLocationError(null);
      // Clear all state to prevent memory leaks
      setRestaurants([]);
      setProducts([]);
      setSelectedRestaurant(null);
    };
  }, [propUserLocation, locationFilter, selectedCity]);

  // Update sort type when location filter changes
  useEffect(() => {
    if (isMounted) {
      setSortType(locationFilter === 'nearest' ? 'nearest' : 'citywide');
    }
    
    return () => {
      // Cleanup any pending state updates
    };
  }, [locationFilter, isMounted]);

  // Re-sort when user location changes (only if using nearest sort)
  useEffect(() => {
    if (isMounted && userLocation && originalRestaurants.length > 0 && sortType === 'nearest') {
      sortAndFilterRestaurants(originalRestaurants, sortType, userLocation);
    }
    
    return () => {
      // Cleanup any pending operations
    };
  }, [userLocation, sortType, isMounted]);

  const getUserLocation = () => {
    if (!navigator.geolocation) {
      if (isMounted) {
        setLocationError('Tarayıcınız konum hizmetlerini desteklemiyor');
      }
      return;
    }

    // Store the geolocation request ID for potential cancellation
    const geoLocationId = navigator.geolocation.getCurrentPosition(
      (position) => {
        if (isMounted) {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setUserLocation(location);
          console.log('Kullanıcı konumu alındı:', `${location.lat}, ${location.lng}`);
        }
      },
      (error) => {
        if (isMounted) {
          console.error('Konum alınamadı:', error);
          setLocationError('Konum erişimi reddedildi. En yakın restoranları gösteriyoruz.');
          // Default to Istanbul center if location denied
          setUserLocation({ lat: 41.0082, lng: 28.9784 });
        }
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

  const getCategoryIcon = (category) => {
    const icons = {
      'Tümü': '🍽️',
      'Ana Yemek': '🍖',
      'Pizza': '🍕',
      'Burger': '🍔',
      'Döner': '🥙',
      'Kebap': '🍢',
      'Pasta': '🍝',
      'Çorba': '🍲',
      'Salata': '🥗',
      'Tatlı': '🍰',
      'İçecek': '🥤',
      'Kahve': '☕',
      'Çay': '🍵'
    };
    return icons[category] || '🍽️';
  };

  const fetchRestaurants = async () => {
    if (!isMounted) return; // Early return if component is unmounted
    
    try {
      // Use the new public businesses endpoint
      const response = await axios.get(`${API}/businesses`);
      const businessData = response.data;
      
      // Double-check isMounted after async operation
      if (isMounted && businessData) {
        setOriginalRestaurants(businessData); // Store original data
        sortAndFilterRestaurants(businessData, sortType, userLocation);
        console.log('Restaurants fetched:', businessData);
      }
    } catch (error) {
      console.error('Restoranlar yüklenemedi:', error);
      if (isMounted) {
        toast.error('Restoranlar yüklenirken hata oluştu');
      }
    } finally {
      // Always set loading to false if component is still mounted
      if (isMounted) {
        setLoading(false);
      }
    }
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
    if (!isMounted) return; // Early return if component is unmounted
    
    let sortedData = [...data];
    
    if (type === 'nearest' && location) {
      // Sort by distance (En Yakın)
      sortedData = data.map(business => {
        // Handle different location data structures (Turkish/English keys)
        const businessLocation = business.location || {};
        const lat = businessLocation.lat || businessLocation.enlem || 41.0082; // Default to Istanbul center
        const lng = businessLocation.lng || businessLocation.uzunluk || 28.9784;
        
        return {
          ...business,
          distance: calculateDistance(
            location.lat, location.lng,
            lat, lng
          )
        };
      }).sort((a, b) => a.distance - b.distance);
    } else if (type === 'citywide') {
      // Sort by rating for citywide (Şehir Geneli)
      sortedData = data.sort((a, b) => {
        const ratingA = parseFloat(a.rating) || 0;
        const ratingB = parseFloat(b.rating) || 0;
        return ratingB - ratingA; // Higher rating first
      });
    }
    
    if (isMounted) {
      setRestaurants(sortedData);
    }
  };

  const handleSortChange = (newSortType) => {
    if (!isMounted) return; // Prevent sort changes if component is unmounted
    
    setSortType(newSortType);
    sortAndFilterRestaurants(originalRestaurants, newSortType, userLocation);
  };

  const fetchProducts = async (restaurantId) => {
    if (!isMounted) return; // Early return if component is unmounted
    
    try {
      setLoading(true);
      const response = await axios.get(`${API}/businesses/${restaurantId}/products`);
      
      // Double-check isMounted after async operation
      if (isMounted && response.data) {
        setProducts(response.data);
        
        // Extract categories from products
        const productCategories = [...new Set(response.data.map(p => p.category).filter(Boolean))];
        setCategories(['all', ...productCategories]);
      }
    } catch (error) {
      if (isMounted) {
        console.error('Products fetch error:', error);
        toast.error('Ürünler yüklenemedi');
        setProducts([]);
      }
    } finally {
      if (isMounted) {
        setLoading(false);
      }
    }
  };

  const handleRestaurantSelect = (restaurant) => {
    if (!isMounted) return; // Prevent restaurant selection if component is unmounted
    
    setSelectedRestaurant(restaurant);
    // Clear cart when switching restaurants - use prop function if available
    if (onRemoveFromCart && cart.length > 0) {
      // Clear all items from cart
      cart.forEach(item => onRemoveFromCart(item.product_id));
    }
    fetchProducts(restaurant.id);
  };

  const addToCart = (product) => {
    if (!isMounted) return; // Prevent cart updates if component is unmounted
    
    // Use the prop function if available, otherwise handle locally
    if (onAddToCart) {
      onAddToCart(product);
    } else {
      // Fallback to local handling (for backward compatibility)
      console.warn('onAddToCart prop not provided, cart functionality may be limited');
    }
    
    if (isMounted) {
      toast.success(`${product.name} sepete eklendi! ✨`);
    }
  };

  const updateCartQuantity = (productId, change) => {
    if (!isMounted) return; // Prevent cart updates if component is unmounted
    
    try {
      // Use the prop function if available
      if (onUpdateCart) {
        // Get current quantity from cart
        const currentItem = cart.find(item => item.product_id === productId);
        if (currentItem) {
          const newQuantity = Math.max(0, currentItem.quantity + change);
          onUpdateCart(productId, newQuantity);
          
          if (newQuantity === 0) {
            toast.success('Ürün sepetten çıkarıldı');
          } else {
            toast.success(`Sepet güncellendi (${newQuantity})`);
          }
        } else {
          toast.error('Ürün sepette bulunamadı');
        }
      } else {
        // Fallback to local handling (for backward compatibility)
        console.warn('onUpdateCart prop not provided, cart functionality may be limited');
        toast.error('Sepet güncellemesi şu anda mümkün değil');
      }
    } catch (error) {
      console.error('Cart update error:', error);
      toast.error('Sepet güncellenirken hata oluştu');
    }
  };

  const removeFromCart = (productId) => {
    if (!isMounted) return; // Prevent cart updates if component is unmounted
    
    try {
      // Use the prop function if available
      if (onRemoveFromCart) {
        const currentItem = cart.find(item => item.product_id === productId);
        const productName = currentItem ? currentItem.product_name || currentItem.name : 'Ürün';
        onRemoveFromCart(productId);
        toast.success(`${productName} sepetten çıkarıldı`);
      } else {
        // Fallback to local handling (for backward compatibility)
        console.warn('onRemoveFromCart prop not provided, cart functionality may be limited');
        toast.error('Sepetten çıkarma şu anda mümkün değil');
      }
    } catch (error) {
      console.error('Cart removal error:', error);
      toast.error('Sepetten çıkarılırken hata oluştu');
    }
  };
      console.warn('onRemoveFromCart prop not provided, cart functionality may be limited');
    }
    
    if (isMounted) {
      toast.success('Ürün sepetten kaldırıldı');
    }
  };

  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('card');

  // Calculate cart total
  const getCartTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0).toFixed(2);
  };

  const handleCheckout = () => {
    if (!isMounted || cart.length === 0) return;
    setShowCheckoutModal(true);
  };

  const handleCompleteOrder = async () => {
    if (!selectedAddress) {
      toast.error('Lütfen teslimat adresi seçin');
      return;
    }

    try {
      // Here you would create the order with the selected address and cart items
      const orderData = {
        restaurant_id: selectedRestaurant?.id,
        items: cart,
        delivery_address: selectedAddress,
        payment_method: paymentMethod,
        total_amount: getCartTotal()
      };
      
      // Mock order creation for demo
      toast.success('Siparişiniz başarıyla alındı!');
      // Clear cart after successful order - use prop function if available
      if (onRemoveFromCart && cart.length > 0) {
        cart.forEach(item => onRemoveFromCart(item.product_id));
      }
      setShowCheckoutModal(false);
      localStorage.removeItem('kuryecini_cart');
      
    } catch (error) {
      toast.error('Sipariş oluşturulamadı');
    }
  };

  const filteredProducts = products.filter(product => {
    // Filter by main category (food/drinks)
    let matchesMainCategory = true;
    if (activeMenuTab === 'food') {
      // Define food categories
      const foodCategories = ['ana yemek', 'başlangıç', 'pizza', 'burger', 'döner', 'kebap', 'pasta', 'çorba', 'salata', 'tatlı'];
      matchesMainCategory = foodCategories.some(cat => 
        product.category?.toLowerCase().includes(cat) || 
        product.name?.toLowerCase().includes(cat)
      );
    } else if (activeMenuTab === 'drinks') {
      // Define drink categories  
      const drinkCategories = ['içecek', 'kahve', 'çay', 'su', 'kola', 'fanta', 'sprite', 'ayran', 'meyve suyu', 'smoothie'];
      matchesMainCategory = drinkCategories.some(cat => 
        product.category?.toLowerCase().includes(cat) || 
        product.name?.toLowerCase().includes(cat)
      );
    }
    
    // Filter by subcategory
    const matchesSubCategory = selectedCategory === 'all' || product.category === selectedCategory;
    
    // Filter by search
    const matchesSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         product.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Filter by price range
    const matchesPrice = (!priceRange.min || product.price >= parseFloat(priceRange.min)) &&
                        (!priceRange.max || product.price <= parseFloat(priceRange.max));
    
    // Filter by availability
    const matchesAvailability = !showAvailableOnly || product.is_available;
    
    return matchesMainCategory && matchesSubCategory && matchesSearch && matchesPrice && matchesAvailability;
  }).sort((a, b) => {
    // Sort products based on sortBy criteria
    switch (sortBy) {
      case 'price_asc':
        return a.price - b.price;
      case 'price_desc':
        return b.price - a.price;
      case 'rating':
        return (b.rating || 0) - (a.rating || 0);
      case 'prep_time':
        return (a.preparation_time_minutes || 15) - (b.preparation_time_minutes || 15);
      case 'popularity':
      default:
        // Sort by popularity (popular items first, then by rating)
        if (a.is_popular && !b.is_popular) return -1;
        if (!a.is_popular && b.is_popular) return 1;
        return (b.rating || 0) - (a.rating || 0);
    }
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
          <h1 className="text-3xl font-bold text-gray-800 mb-2">🍽️ Kuryecini Yemek</h1>
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
            
            {/* Enhanced Menu Categories */}
            <Tabs value={activeMenuTab} onValueChange={setActiveMenuTab}>
              <TabsList className="grid w-full grid-cols-3 mb-4">
                <TabsTrigger value="all" className="flex items-center space-x-2">
                  <span>🍽️</span>
                  <span>Tümü</span>
                </TabsTrigger>
                <TabsTrigger value="food" className="flex items-center space-x-2">
                  <span>🍕</span>
                  <span>Yiyecek</span>
                </TabsTrigger>
                <TabsTrigger value="drinks" className="flex items-center space-x-2">
                  <span>🥤</span>
                  <span>İçecek</span>
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            {/* Secondary Category Filter */}
            {categories.length > 0 && (
              <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
                <TabsList className="flex-wrap h-auto p-1 bg-gray-100">
                  <TabsTrigger value="all" className="text-xs">Tümü</TabsTrigger>
                  {categories.filter(cat => cat !== 'all').map(category => (
                    <TabsTrigger key={category} value={category} className="text-xs">
                      {category}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </Tabs>
            )}
          </div>

          {/* Enhanced Menu Categories & Filters */}
          <div className="space-y-4 mb-6">
            {/* Category Tabs */}
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => setActiveMenuTab(category)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                    activeMenuTab === category
                      ? 'bg-orange-500 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {getCategoryIcon(category)} {category}
                </button>
              ))}
            </div>

            {/* Advanced Filters */}
            <div className="flex items-center space-x-4 p-4 bg-white rounded-lg border">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Sıralama:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="border rounded px-3 py-1 text-sm"
                >
                  <option value="popularity">Popülerlik</option>
                  <option value="price_asc">Fiyat (Düşük-Yüksek)</option>
                  <option value="price_desc">Fiyat (Yüksek-Düşük)</option>
                  <option value="rating">Puan</option>
                  <option value="prep_time">Hazırlık Süresi</option>
                </select>
              </div>
              
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Fiyat:</label>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={priceRange.min}
                    onChange={(e) => setPriceRange({...priceRange, min: e.target.value})}
                    className="w-16 border rounded px-2 py-1 text-sm"
                  />
                  <span className="text-gray-500">-</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={priceRange.max}
                    onChange={(e) => setPriceRange({...priceRange, max: e.target.value})}
                    className="w-16 border rounded px-2 py-1 text-sm"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="availableOnly"
                  checked={showAvailableOnly}
                  onChange={(e) => setShowAvailableOnly(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="availableOnly" className="text-sm text-gray-700">
                  Sadece Mevcut Olanlar
                </label>
              </div>
            </div>
          </div>

          {/* Enhanced Product Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredProducts.map(product => (
              <EnhancedProductCard
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

      {/* Enhanced Checkout Modal */}
      {showCheckoutModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">🛒 Siparişi Tamamla</h2>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setShowCheckoutModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </Button>
              </div>

              {/* Order Summary */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 flex items-center">
                  📋 Sipariş Özeti
                </h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  {cart.map((item, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="text-sm">
                        {item.name} x {item.quantity}
                      </span>
                      <span className="font-medium">
                        ₺{(item.price * item.quantity).toFixed(2)}
                      </span>
                    </div>
                  ))}
                  <div className="border-t pt-2 mt-2">
                    <div className="flex justify-between items-center font-bold text-lg">
                      <span>Toplam:</span>
                      <span className="text-green-600">₺{getCartTotal()}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Address Selection */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 flex items-center">
                  📍 Teslimat Adresi
                </h3>
                <AddressSelector 
                  onAddressSelect={setSelectedAddress}
                  selectedAddress={selectedAddress}
                />
              </div>

              {/* Payment Method */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 flex items-center">
                  💳 Ödeme Yöntemi
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <Button
                    variant={paymentMethod === 'card' ? 'default' : 'outline'}
                    onClick={() => setPaymentMethod('card')}
                    className="flex items-center justify-center space-x-2 p-4 h-auto"
                  >
                    <span>💳</span>
                    <span>Kredi Kartı</span>
                  </Button>
                  <Button
                    variant={paymentMethod === 'cash' ? 'default' : 'outline'}
                    onClick={() => setPaymentMethod('cash')}
                    className="flex items-center justify-center space-x-2 p-4 h-auto"
                  >
                    <span>💵</span>
                    <span>Nakit</span>
                  </Button>
                  <Button
                    variant={paymentMethod === 'wallet' ? 'default' : 'outline'}
                    onClick={() => setPaymentMethod('wallet')}
                    className="flex items-center justify-center space-x-2 p-4 h-auto"
                  >
                    <span>📱</span>
                    <span>Dijital Cüzdan</span>
                  </Button>
                </div>
              </div>

              {/* Delivery Notes */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 flex items-center">
                  📝 Teslimat Notları (İsteğe Bağlı)
                </h3>
                <textarea
                  placeholder="Kurye için özel talimatlar..."
                  className="w-full border rounded-lg p-3 text-sm h-20 resize-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  rows="3"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowCheckoutModal(false)}
                  className="flex-1"
                >
                  🔙 Geri Dön
                </Button>
                <Button
                  onClick={handleCompleteOrder}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                  disabled={!selectedAddress}
                >
                  {selectedAddress ? '✅ Siparişi Onayla' : '📍 Önce Adres Seçin'}
                </Button>
              </div>

              {/* Order Info */}
              <div className="mt-4 text-xs text-gray-500 text-center">
                <p>Tahmini teslimat süresi: 25-45 dakika</p>
                <p>Sipariş sonrası iptal mümkün değildir</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfessionalFoodOrderSystem;