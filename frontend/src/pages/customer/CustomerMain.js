import React, { useState } from 'react';
import AddressesPage from './AddressesPage';
import NearbyRestaurants from './NearbyRestaurants';
import RestaurantMenu from './RestaurantMenu';
import Cart from './Cart';
import Profile from './Profile';

export const CustomerMain = ({ user }) => {
  const [currentView, setCurrentView] = useState('menu'); // 'menu' | 'addresses' | 'restaurants' | 'restaurant_menu' | 'cart' | 'profile'
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [cartItems, setCartItems] = useState([]);
  const [orderTotal, setOrderTotal] = useState(0);
  
  console.log('🏠 CustomerMain rendered - currentView:', currentView, 'user:', user?.first_name);

  const handleAddressSelect = (address) => {
    console.log('Selected address:', address);
    setSelectedAddress(address);
    setCurrentView('restaurants');
  };

  const handleBackToAddresses = () => {
    setCurrentView('addresses');
    setSelectedAddress(null);
  };

  const handleRestaurantSelect = (restaurant) => {
    console.log('Selected restaurant:', restaurant);
    setSelectedRestaurant(restaurant);
    setCurrentView('restaurant_menu');
  };

  const handleAddToCart = (item) => {
    console.log('Adding to cart:', item);
    const existingItem = cartItems.find(cartItem => cartItem.id === item.id);
    
    if (item.action === 'decrease') {
      // Decrease quantity
      if (existingItem && existingItem.quantity > 1) {
        setCartItems(cartItems.map(cartItem => 
          cartItem.id === item.id 
            ? { ...cartItem, quantity: cartItem.quantity - 1 }
            : cartItem
        ));
        setOrderTotal(orderTotal - item.price);
      } else if (existingItem && existingItem.quantity === 1) {
        // Remove item completely
        setCartItems(cartItems.filter(cartItem => cartItem.id !== item.id));
        setOrderTotal(orderTotal - item.price);
      }
    } else {
      // Increase quantity or add new item
      if (existingItem) {
        setCartItems(cartItems.map(cartItem => 
          cartItem.id === item.id 
            ? { ...cartItem, quantity: cartItem.quantity + 1 }
            : cartItem
        ));
      } else {
        setCartItems([...cartItems, { ...item, quantity: 1 }]);
      }
      
      // Update total
      setOrderTotal(orderTotal + item.price);
    }
  };

  const handleRemoveFromCart = (itemId) => {
    const item = cartItems.find(cartItem => cartItem.id === itemId);
    if (item) {
      if (item.quantity > 1) {
        setCartItems(cartItems.map(cartItem => 
          cartItem.id === itemId 
            ? { ...cartItem, quantity: cartItem.quantity - 1 }
            : cartItem
        ));
      } else {
        setCartItems(cartItems.filter(cartItem => cartItem.id !== itemId));
      }
      
      const newTotal = orderTotal - item.price;
      setOrderTotal(newTotal);
    }
  };

  const handleGoToCart = () => {
    setCurrentView('cart');
  };

  const handleBackToMenu = () => {
    setCurrentView('menu');
  };

  const handleLogout = () => {
    // Clear user data and redirect to login
    console.log('User logging out...');
    // This would be handled by parent component
  };

  const handleUpdateCart = (itemId, newQuantity) => {
    setCartItems(cartItems.map(item => 
      item.id === itemId ? { ...item, quantity: newQuantity } : item
    ));
    
    // Recalculate total
    const newTotal = cartItems.reduce((total, item) => 
      total + (item.id === itemId ? item.price * newQuantity : item.price * item.quantity), 0
    );
    setOrderTotal(newTotal);
  };

  // Restaurant Menu View
  if (currentView === 'restaurant_menu') {
    return (
      <RestaurantMenu
        restaurant={selectedRestaurant}
        onAddToCart={handleAddToCart}
        onBack={() => setCurrentView('restaurants')}
        cartItems={cartItems}
        cartTotal={orderTotal}
        onGoToCart={() => setCurrentView('cart')}
      />
    );
  }

  // Cart View
  if (currentView === 'cart') {
    return (
      <Cart
        cartItems={cartItems}
        onUpdateCart={handleUpdateCart}
        onRemoveFromCart={handleRemoveFromCart}
        onBack={() => setCurrentView('restaurant_menu')}
        selectedAddress={selectedAddress}
        selectedRestaurant={selectedRestaurant}
        user={user}
      />
    );
  }

  // Profile View
  if (currentView === 'profile') {
    return (
      <Profile
        user={user}
        onBack={() => setCurrentView('menu')}
        onLogout={handleLogout}
      />
    );
  }

  // Restaurants View
  if (currentView === 'restaurants') {
    return (
      <NearbyRestaurants
        address={selectedAddress}
        city={selectedAddress?.city || selectedAddress?.city_normalized}
        lat={selectedAddress?.lat}
        lng={selectedAddress?.lng}
        onBack={handleBackToAddresses}
        onRestaurantSelect={handleRestaurantSelect}
      />
    );
  }

  if (currentView === 'addresses') {
    return (
      <AddressesPage
        key="addresses-page"
        onSelectAddress={handleAddressSelect}
        onBack={() => setCurrentView('menu')}
      />
    );
  }

  // Default menu view
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Welcome Header */}
        <div className="text-center mb-8">
          <div className="w-24 h-24 bg-gradient-to-br from-orange-500 to-red-500 rounded-full mx-auto mb-4 flex items-center justify-center shadow-xl">
            <span className="text-4xl text-white">👤</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Hoş Geldiniz, {user?.first_name}!
          </h1>
          <p className="text-lg text-gray-600">
            Kuryecini ile sipariş vermeye hazır mısınız?
          </p>
        </div>

        {/* Menu Options */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-3xl mx-auto">
          
          {/* Kayıtlı Adreslerim */}
          <div 
            className="group cursor-pointer"
            onClick={() => setCurrentView('addresses')}
          >
            <div className="bg-white rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 border-2 border-transparent hover:border-orange-200">
              <div className="text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                  <span className="text-3xl text-white">📍</span>
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">
                  Kayıtlı Adreslerim
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Adreslerinizi yönetin ve yeni adres ekleyin
                </p>
              </div>
            </div>
          </div>

          {/* Restoran Keşfet */}
          <div 
            className="group cursor-pointer"
            onClick={() => setCurrentView('addresses')}
          >
            <div className="bg-white rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 border-2 border-transparent hover:border-green-200">
              <div className="text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                  <span className="text-3xl text-white">🍽️</span>
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">
                  Restoran Keşfet
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Çevrendeki restoranları keşfet ve sipariş ver
                </p>
              </div>
            </div>
          </div>

          {/* Profil */}
          <div 
            className="group cursor-pointer"
            onClick={() => setCurrentView('profile')}
          >
            <div className="bg-white rounded-3xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 transform hover:scale-105 border-2 border-transparent hover:border-purple-200">
              <div className="text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                  <span className="text-3xl text-white">⚙️</span>
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">
                  Profil Ayarları
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  Hesap bilgilerinizi düzenleyin
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default CustomerMain;