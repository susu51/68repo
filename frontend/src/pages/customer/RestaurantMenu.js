import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';

const RestaurantMenu = ({ restaurant, onAddToCart, onBack, cartItems = [], cartTotal = 0, onGoToCart }) => {
  const [menuItems, setMenuItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loading, setLoading] = useState(true);

  // Mock menu data - gerçek API'den gelecek
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
    // Mock loading delay
    setTimeout(() => {
      setMenuItems(mockMenuItems);
      setLoading(false);
    }, 1000);
  }, []);

  const filteredItems = selectedCategory === 'all' 
    ? menuItems 
    : menuItems.filter(item => item.category === selectedCategory);

  const getItemQuantityInCart = (itemId) => {
    const item = cartItems.find(cartItem => cartItem.id === itemId);
    return item ? item.quantity : 0;
  };

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
          <CardContent className="p-8 relative">
            <div className="absolute inset-0 bg-white/10 opacity-40">
              <div className="absolute top-0 right-0 w-48 h-48 bg-white/20 rounded-full -mr-24 -mt-24"></div>
              <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/15 rounded-full -ml-16 -mb-16"></div>
            </div>
            
            <div className="relative flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-16 h-16 bg-white/25 backdrop-blur-sm rounded-2xl flex items-center justify-center mr-6 shadow-lg">
                  <span className="text-3xl">🍽️</span>
                </div>
                <div>
                  <h1 className="text-3xl font-bold mb-2">{restaurant?.name || 'Restoran'}</h1>
                  <p className="text-white/90 text-lg flex items-center">
                    <span className="mr-4">⭐ {restaurant?.rating || '4.5'}</span>
                    <span className="mr-4">🕒 {restaurant?.deliveryTime || '25-35'} dk</span>
                    <span>💰 Min: ₺{restaurant?.minOrder || '50'}</span>
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                {/* Cart Summary */}
                {cartItems.length > 0 && (
                  <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 text-center">
                    <p className="text-sm text-white/90">Sepet</p>
                    <p className="text-xl font-bold">{cartItems.length} ürün</p>
                    <p className="text-lg">₺{cartTotal.toFixed(2)}</p>
                  </div>
                )}
                
                <Button 
                  variant="outline" 
                  onClick={onBack}
                  className="bg-white/20 border-white/30 text-white hover:bg-white/30 rounded-xl backdrop-blur-sm"
                >
                  ← Geri
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Category Filter */}
        <Card className="mb-6 border-0 shadow-lg rounded-2xl">
          <CardContent className="p-6">
            <div className="flex gap-4 overflow-x-auto">
              {categories.map(category => (
                <Button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`min-w-fit rounded-xl px-6 py-3 font-semibold transition-all duration-300 ${
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
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredItems.map(item => {
            const quantityInCart = getItemQuantityInCart(item.id);
            
            return (
              <Card key={item.id} className="group hover:shadow-2xl hover:scale-105 transition-all duration-300 border-0 shadow-lg bg-white rounded-2xl overflow-hidden">
                <div className="aspect-w-16 aspect-h-9">
                  <img 
                    src={item.image} 
                    alt={item.name}
                    className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-300"
                  />
                </div>
                
                <CardContent className="p-6">
                  <h3 className="text-xl font-bold text-gray-800 mb-2">{item.name}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed mb-4">{item.description}</p>
                  
                  <div className="flex items-center justify-between mb-4">
                    <div className="text-2xl font-bold text-orange-500">₺{item.price.toFixed(2)}</div>
                    <div className="flex items-center text-green-600">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                      <span className="text-sm font-medium">Mevcut</span>
                    </div>
                  </div>

                  {/* Add to Cart Controls */}
                  {quantityInCart === 0 ? (
                    <Button 
                      onClick={() => onAddToCart(item)}
                      className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                    >
                      🛒 Sepete Ekle
                    </Button>
                  ) : (
                    <div className="flex items-center justify-between bg-orange-50 rounded-xl p-3">
                      <Button 
                        onClick={() => onAddToCart({...item, quantity: -1})}
                        className="w-10 h-10 bg-red-500 hover:bg-red-600 text-white rounded-full p-0"
                      >
                        -
                      </Button>
                      <span className="text-lg font-bold text-orange-600">{quantityInCart}</span>
                      <Button 
                        onClick={() => onAddToCart(item)}
                        className="w-10 h-10 bg-green-500 hover:bg-green-600 text-white rounded-full p-0"
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

        {/* Floating Cart Button */}
        {cartItems.length > 0 && (
          <div className="fixed bottom-6 right-6 z-50">
            <Button 
              onClick={() => {/* Handle go to cart */}}
              className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold py-4 px-6 rounded-2xl shadow-2xl hover:shadow-3xl transition-all duration-300 transform hover:scale-105"
            >
              🛒 Sepete Git ({cartItems.length}) - ₺{cartTotal.toFixed(2)}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RestaurantMenu;