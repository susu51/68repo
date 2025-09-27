import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { toast } from 'react-hot-toast';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001/api';

// Restaurant Card Component
const RestaurantCard = ({ restaurant, onClick }) => {
  return (
    <Card 
      className="hover:shadow-lg transition-all cursor-pointer group border-2 hover:border-orange-200"
      onClick={() => onClick(restaurant)}
    >
      <div className="relative overflow-hidden">
        {restaurant.image && (
          <img 
            src={restaurant.image} 
            alt={restaurant.name}
            className="w-full h-48 object-cover group-hover:scale-105 transition-transform"
          />
        )}
        <div className="absolute top-2 right-2">
          <Badge className="bg-white text-gray-800 shadow-sm">
            ⭐ {restaurant.rating || '4.5'}
          </Badge>
        </div>
      </div>
      
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-bold text-lg text-gray-800">{restaurant.name}</h3>
          <Badge variant="outline" className="text-xs">
            {restaurant.category}
          </Badge>
        </div>
        
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
          {restaurant.description || 'Lezzetli yemekler sizi bekliyor...'}
        </p>
        
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span className="flex items-center">
              <span className="mr-1">🚲</span>
              {restaurant.delivery_time || '25-40'} dk
            </span>
            <span className="flex items-center">
              <span className="mr-1">💰</span>
              Min. ₺{restaurant.min_order || '50'}
            </span>
          </div>
          <Badge className="bg-green-100 text-green-800">
            Açık
          </Badge>
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
            />
          ) : (
            <div className="w-full h-full bg-gray-200 rounded-l-lg flex items-center justify-center">
              <span className="text-4xl">🍽️</span>
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
                {product.is_available ? 'Mevcut' : 'Tükendi'}
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
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchRestaurants();
  }, []);

  const fetchRestaurants = async () => {
    try {
      // Get all businesses
      const response = await axios.get(`${API}/admin/users`);
      const businesses = response.data.filter(user => user.role === 'business');
      
      // Convert to restaurant format
      const restaurantData = businesses.map(business => ({
        id: business.id,
        name: business.business_name || 'İsimsiz Restoran',
        category: business.business_category === 'gida' ? 'Restoran' : 'Kargo',
        description: business.description || 'Lezzetli yemekler sizi bekliyor...',
        rating: (4.0 + Math.random() * 1.5).toFixed(1),
        delivery_time: `${20 + Math.floor(Math.random() * 20)}-${35 + Math.floor(Math.random() * 15)}`,
        min_order: 50 + Math.floor(Math.random() * 50),
        image: `/api/placeholder-restaurant-${business.id.slice(-1)}.jpg`
      }));
      
      setRestaurants(restaurantData);
    } catch (error) {
      console.error('Restoranlar yüklenemedi:', error);
    }
    setLoading(false);
  };

  const fetchProducts = async (restaurantId) => {
    try {
      const response = await axios.get(`${API}/products?business_id=${restaurantId}`);
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
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {restaurants.map(restaurant => (
            <RestaurantCard
              key={restaurant.id}
              restaurant={restaurant}
              onClick={handleRestaurantSelect}
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