import React, { useState, useEffect } from 'react';
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

  // Fetch menu items from API
  useEffect(() => {
    if (restaurant && restaurant.id) {
      fetchMenuItems();
    }
  }, [restaurant]);

  const fetchMenuItems = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${BACKEND_URL}/api/businesses/${restaurant.id}/products`);
      
      if (response.data && Array.isArray(response.data)) {
        setMenuItems(response.data);
      } else {
        // Fallback to mock data if no real menu
        setMenuItems(mockMenuItems);
      }
    } catch (error) {
      console.error('Error fetching menu:', error);
      // Use mock data on error
      setMenuItems(mockMenuItems);
    } finally {
      setLoading(false);
    }
  };

  // Mock menu data as fallback
  const mockMenuItems = [
    {
      id: 1,
      name: 'Margherita Pizza',
      description: 'Domates sosu, mozzarella, fesleğen',
      price: 45.00,
      category: 'pizza',
      image: 'https://images.unsplash.com/photo-1604382354936-07c5b6f67692?w=300',
      availability: true
    },
    {
      id: 2,
      name: 'Pepperoni Pizza',
      description: 'Domates sosu, mozzarella, pepperoni',
      price: 52.00,
      category: 'pizza',
      image: 'https://images.unsplash.com/photo-1628840042765-356cda07504e?w=300',
      availability: true
    },
    {
      id: 3,
      name: 'Tavuk Şiş',
      description: 'Izgara tavuk şiş, pilav, salata',
      price: 38.00,
      category: 'main',
      image: 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=300',
      availability: true
    },
    {
      id: 4,
      name: 'Köfte',
      description: 'Ev yapımı köfte, patates kızartması',
      price: 42.00,
      category: 'main',
      image: 'https://images.unsplash.com/photo-1529042410759-befb1204b468?w=300',
      availability: true
    },
    {
      id: 5,
      name: 'Caesar Salata',
      description: 'Marul, parmesan, kruton, sezar sosu',
      price: 28.00,
      category: 'salad',
      image: 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=300',
      availability: true
    },
    {
      id: 6,
      name: 'Tiramisu',
      description: 'Geleneksel İtalyan tatlısı',
      price: 22.00,
      category: 'dessert',
      image: 'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=300',
      availability: true
    }
  ];

  const categories = [
    { id: 'all', name: 'Hepsi', icon: '🍽️' },
    { id: 'pizza', name: 'Pizza', icon: '🍕' },
    { id: 'main', name: 'Ana Yemek', icon: '🍖' },
    { id: 'salad', name: 'Salata', icon: '🥗' },
    { id: 'dessert', name: 'Tatlı', icon: '🍰' }
  ];

  useEffect(() => {
    const loadMenuItems = async () => {
      if (!restaurant?.id) {
        console.error('No restaurant ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        console.log(`Loading menu for business ID: ${restaurant.id}`);
        
        // First try to get business products
        const response = await axios.get(`${BACKEND_URL}/api/businesses/${restaurant.id}/products`);
        console.log('API Response:', response.data);
        
        if (response.data && response.data.length > 0) {
          setMenuItems(response.data);
          console.log(`Loaded ${response.data.length} real menu items`);
        } else {
          console.log('No products found, trying admin endpoint...');
          
          // Try admin products endpoint as fallback
          const adminResponse = await axios.get(`${BACKEND_URL}/api/admin/products?business_id=${restaurant.id}`);
          
          if (adminResponse.data && adminResponse.data.length > 0) {
            setMenuItems(adminResponse.data);
            console.log(`Loaded ${adminResponse.data.length} products from admin endpoint`);
          } else {
            console.log('No products found anywhere - business may not have menu items');
            setMenuItems([]);
          }
        }
      } catch (error) {
        console.error('Error loading menu items:', error);
        console.error('Error details:', error.response?.data);
        
        // Show empty menu instead of mock data
        setMenuItems([]);
      } finally {
        setLoading(false);
      }
    };

    loadMenuItems();
  }, [restaurant?.id]);

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
                    <span>🕒 {restaurant?.deliveryTime || '25-35'} dk</span>
                    <span>💰 Min: ₺{restaurant?.minOrder || '50'}</span>
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2 md:gap-4 w-full sm:w-auto">
                {/* Cart Summary */}
                {cart.items.length > 0 && (
                  <div className="bg-white/20 backdrop-blur-sm rounded-xl p-2 md:p-4 text-center cursor-pointer flex-1 sm:flex-none" onClick={onGoToCart}>
                    <p className="text-xs md:text-sm text-white/90">Sepet</p>
                    <p className="text-sm md:text-xl font-bold">{cartSummary.itemCount} ürün</p>
                    <p className="text-sm md:text-lg">₺{cartSummary.total.toFixed(2)}</p>
                  </div>
                )}
                
                <Button 
                  variant="outline" 
                  onClick={onBack}
                  className="bg-white/20 border-white/30 text-white hover:bg-white/30 rounded-xl backdrop-blur-sm px-3 md:px-4 py-2 text-sm md:text-base"
                >
                  ← Geri
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Category Filter */}
        <Card className="mb-6 border-0 shadow-lg rounded-2xl">
          <CardContent className="p-3 md:p-4 lg:p-6">
            <div className="flex gap-2 md:gap-4 overflow-x-auto pb-2">
              {categories.map(category => (
                <Button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`min-w-fit whitespace-nowrap rounded-xl px-3 md:px-6 py-2 md:py-3 text-sm md:text-base font-semibold transition-all duration-300 touch-manipulation ${
                    selectedCategory === category.id
                      ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category.icon} {category.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Menu Items */}
        {filteredItems.length === 0 ? (
          <div className="text-center py-16">
            <span className="text-6xl mb-4 block">🍽️</span>
            <h3 className="text-xl font-bold text-gray-800 mb-2">
              {menuItems.length === 0 ? 'Henüz menü eklenmemiş' : 'Bu kategoride ürün bulunamadı'}
            </h3>
            <p className="text-gray-600">
              {menuItems.length === 0 
                ? 'Bu işletme henüz menü ürünlerini yüklememiş. Lütfen daha sonra tekrar deneyin.' 
                : 'Farklı bir kategori seçmeyi deneyin.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {filteredItems.map(item => {
            const quantityInCart = getItemQuantity(item.id);
            
            return (
              <Card key={item.id} className="group hover:shadow-2xl hover:scale-105 transition-all duration-300 border-0 shadow-lg bg-white rounded-2xl overflow-hidden">
                <div className="relative">
                  <img 
                    src={item.image} 
                    alt={item.name}
                    className="w-full h-32 sm:h-40 md:h-48 object-cover group-hover:scale-110 transition-transform duration-300"
                  />
                </div>
                
                <CardContent className="p-3 md:p-4 lg:p-6">
                  <h3 className="text-lg md:text-xl font-bold text-gray-800 mb-1 md:mb-2 line-clamp-1">{item.name}</h3>
                  <p className="text-gray-600 text-xs md:text-sm leading-relaxed mb-3 md:mb-4 line-clamp-2">{item.description}</p>
                  
                  <div className="flex items-center justify-between mb-3 md:mb-4">
                    <div className="text-lg md:text-2xl font-bold text-orange-500">₺{item.price?.toFixed(2) || '0.00'}</div>
                    <div className="flex items-center text-green-600">
                      <span className="w-1.5 h-1.5 md:w-2 md:h-2 bg-green-500 rounded-full mr-1 md:mr-2"></span>
                      <span className="text-xs md:text-sm font-medium">Mevcut</span>
                    </div>
                  </div>

                  {/* Add to Cart Controls */}
                  {quantityInCart === 0 ? (
                    <Button 
                      onClick={() => addToCart(item)}
                      className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold py-2 md:py-3 px-2 md:px-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 text-sm md:text-base touch-manipulation"
                    >
                      🛒 Sepete Ekle
                    </Button>
                  ) : (
                    <div className="flex items-center justify-between bg-orange-50 rounded-xl p-2 md:p-3">
                      <Button 
                        onClick={() => addToCart(item, -1)}
                        className="w-8 h-8 md:w-10 md:h-10 bg-red-500 hover:bg-red-600 text-white rounded-full p-0 text-sm md:text-base touch-manipulation"
                      >
                        -
                      </Button>
                      <span className="text-base md:text-lg font-bold text-orange-600 mx-2">{quantityInCart}</span>
                      <Button 
                        onClick={() => addToCart(item, 1)}
                        className="w-8 h-8 md:w-10 md:h-10 bg-green-500 hover:bg-green-600 text-white rounded-full p-0 text-sm md:text-base touch-manipulation"
                      >
                        +
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
          </div>
        )}

        {/* Floating Cart Button - Mobile Optimized */}
        {cart.items.length > 0 && (
          <div className="fixed bottom-4 right-4 md:bottom-6 md:right-6 z-50">
            <Button
              onClick={onGoToCart}
              className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold py-3 px-4 md:py-4 md:px-8 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-105 touch-manipulation"
            >
              <div className="flex items-center gap-2 md:gap-3">
                <span className="text-xl md:text-2xl">🛒</span>
                <div className="text-left">
                  <p className="text-xs md:text-sm opacity-90">Sepet</p>
                  <p className="text-sm md:text-lg font-bold">{cartSummary.itemCount} ürün - ₺{cartSummary.total.toFixed(2)}</p>
                </div>
              </div>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RestaurantMenu;