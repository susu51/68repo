import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { useCart } from '../../contexts/CartContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.VITE_REACT_APP_BACKEND_URL;

const RestaurantMenu = ({ restaurant, onBack, onGoToCart }) => {
  const { cart, addToCart, getItemQuantity, setRestaurant, getCartSummary } = useCart();
  const [menuItems, setMenuItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  // Set restaurant in cart context when component mounts
  useEffect(() => {
    if (restaurant) {
      setRestaurant(restaurant);
    }
  }, [restaurant, setRestaurant]);

  const fetchMenuItems = useCallback(async () => {
    try {
      setLoading(true);
      console.log(`Loading menu for business ID: ${restaurant.id}`);
      
      // Use the correct customer endpoint for business products
      const response = await axios.get(`${BACKEND_URL}/api/businesses/${restaurant.id}/products`);
      
      if (response.data && Array.isArray(response.data) && response.data.length > 0) {
        setMenuItems(response.data.map(item => ({
          id: item.id || item._id,
          name: item.name || item.title,
          description: item.description || 'Lezzetli ürün',
          price: parseFloat(item.price) || 0,
          category: item.category || 'main',
          image: item.image || 'https://via.placeholder.com/300x200?text=Yemek',
          availability: item.availability !== false
        })));
        console.log(`Loaded ${response.data.length} real menu items`);
      } else {
        console.log('No products found - showing empty menu');
        setMenuItems([]);
      }
    } catch (error) {
      console.error('Error fetching menu:', error);
      // Show empty menu on error instead of mock data
      setMenuItems([]);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { id: 'all', name: 'Hepsi', icon: '🍽️' },
    { id: 'pizza', name: 'Pizza', icon: '🍕' },
    { id: 'main', name: 'Ana Yemek', icon: '🍖' },
    { id: 'salad', name: 'Salata', icon: '🥗' },
    { id: 'dessert', name: 'Tatlı', icon: '🍰' },
    { id: 'drink', name: 'İçecek', icon: '🥤' }
  ];

  const filteredItems = selectedCategory === 'all' 
    ? menuItems 
    : menuItems.filter(item => item.category === selectedCategory);

  const cartSummary = getCartSummary();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-16">
            <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600 text-lg">Menü yükleniyor...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Restaurant Header */}
        <Card className="mb-6 border-0 shadow-xl rounded-3xl bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 text-white overflow-hidden">
          <CardContent className="p-4 md:p-6 lg:p-8 relative">
            <div className="absolute inset-0 bg-white/10 opacity-40">
              <div className="absolute top-0 right-0 w-48 h-48 bg-white/20 rounded-full -mr-24 -mt-24"></div>
              <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/15 rounded-full -ml-16 -mb-16"></div>
            </div>
            
            <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center">
                <div className="w-12 h-12 md:w-16 md:h-16 bg-white/25 backdrop-blur-sm rounded-2xl flex items-center justify-center mr-3 md:mr-6 shadow-lg">
                  <span className="text-2xl md:text-3xl">🍽️</span>
                </div>
                <div>
                  <h1 className="text-xl md:text-2xl lg:text-3xl font-bold mb-1 md:mb-2">{restaurant?.name || 'Restoran'}</h1>
                  <p className="text-white/90 text-sm md:text-base lg:text-lg flex flex-wrap items-center gap-2 md:gap-4">
                    <span>⭐ {restaurant?.rating || '4.5'}</span>
                    <span>📍 {restaurant?.distance ? `${restaurant.distance}m` : 'Yakın'}</span>
                    <span>⏱️ {restaurant?.deliveryTime || '30-45 dk'}</span>
                  </p>
                </div>
              </div>
              <Button
                onClick={onBack}
                variant="outline"
                size="sm"
                className="bg-white/20 border-white/30 text-white hover:bg-white/30 transition-all duration-300 backdrop-blur-sm"
              >
                ← Geri Dön
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Category Filters */}
        <div className="mb-6">
          <div className="flex flex-wrap gap-2 justify-center">
            {categories.map((category) => (
              <Button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                variant={selectedCategory === category.id ? "default" : "outline"}
                size="sm"
                className={`
                  rounded-full transition-all duration-300 min-w-24
                  ${selectedCategory === category.id 
                    ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg scale-105' 
                    : 'bg-white/80 text-gray-700 hover:bg-white hover:shadow-md'
                  }
                `}
              >
                <span className="mr-1">{category.icon}</span>
                {category.name}
              </Button>
            ))}
          </div>
        </div>

        {/* Menu Items */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {filteredItems.length === 0 ? (
            <div className="col-span-full text-center py-16">
              <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl text-gray-400">🍽️</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">Henüz menü eklenmemiş</h3>
              <p className="text-gray-500">Bu restoran henüz menüsünü eklemiyor. Daha sonra tekrar deneyin.</p>
            </div>
          ) : (
            filteredItems.map((item) => (
              <Card key={item.id} className="border-0 shadow-lg rounded-2xl overflow-hidden bg-white/90 backdrop-blur-sm hover:shadow-xl transition-all duration-300 hover:scale-[1.02]">
                <div className="aspect-video bg-gradient-to-br from-orange-100 to-red-100 overflow-hidden">
                  <img 
                    src={item.image} 
                    alt={item.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/300x200?text=Yemek';
                    }}
                  />
                </div>
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-gray-900 text-lg leading-tight">{item.name}</h3>
                    <span className="text-xl font-bold text-orange-600 ml-2">₺{item.price.toFixed(2)}</span>
                  </div>
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">{item.description}</p>
                  
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      {getItemQuantity(item.id) > 0 ? (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => addToCart(item, -1)}
                            className="w-8 h-8 p-0 rounded-full border-orange-300 text-orange-600 hover:bg-orange-50"
                          >
                            -
                          </Button>
                          <span className="font-semibold text-orange-600 min-w-8 text-center">
                            {getItemQuantity(item.id)}
                          </span>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => addToCart(item, 1)}
                            className="w-8 h-8 p-0 rounded-full border-orange-300 text-orange-600 hover:bg-orange-50"
                          >
                            +
                          </Button>
                        </>
                      ) : (
                        <Button
                          onClick={() => addToCart(item)}
                          className="bg-gradient-to-r from-orange-500 to-red-500 text-white hover:from-orange-600 hover:to-red-600 transition-all duration-300 rounded-full px-6"
                          disabled={!item.availability}
                        >
                          {item.availability ? 'Sepete Ekle' : 'Tükendi'}
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Fixed Bottom Cart Summary */}
        {cartSummary.totalItems > 0 && (
          <div className="fixed bottom-4 left-4 right-4 z-50">
            <div className="max-w-6xl mx-auto">
              <Card className="bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 text-white shadow-2xl border-0 rounded-2xl">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-white/90">
                        {cartSummary.totalItems} ürün
                      </p>
                      <p className="text-xl font-bold">
                        ₺{cartSummary.totalPrice.toFixed(2)}
                      </p>
                    </div>
                    <Button
                      onClick={onGoToCart}
                      className="bg-white/20 border-white/30 text-white hover:bg-white/30 transition-all duration-300 backdrop-blur-sm rounded-xl px-6"
                    >
                      Sepete Git
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RestaurantMenu;