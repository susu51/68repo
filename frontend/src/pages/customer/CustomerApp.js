import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../components/ui/card';
// import { Button } from '../../components/ui/button';
import DiscoverPage from './DiscoverPage';
import CartPage from './CartPage';
import OrdersPage from './OrdersPage';
import ProfilePage from './ProfilePage';

// Yeni Trendyol Go tarzı Customer App
export const CustomerApp = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('discover');
  const [cartItems, setCartItems] = useState([]);
  const [orderTotal, setOrderTotal] = useState(0);

  console.log('🚀 CustomerApp rendered - activeTab:', activeTab, 'user:', user?.first_name);

  // Cart management functions
  const handleAddToCart = (item) => {
    console.log('Adding to cart:', item);
    const existingItem = cartItems.find(cartItem => cartItem.id === item.id);
    
    if (existingItem) {
      setCartItems(cartItems.map(cartItem => 
        cartItem.id === item.id 
          ? { ...cartItem, quantity: cartItem.quantity + 1 }
          : cartItem
      ));
    } else {
      setCartItems([...cartItems, { ...item, quantity: 1 }]);
    }
    
    setOrderTotal(orderTotal + item.price);
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
      
      setOrderTotal(orderTotal - item.price);
    }
  };

  const handleUpdateCart = (itemId, newQuantity) => {
    if (newQuantity === 0) {
      handleRemoveFromCart(itemId);
      return;
    }
    
    setCartItems(cartItems.map(item => 
      item.id === itemId ? { ...item, quantity: newQuantity } : item
    ));
    
    // Recalculate total
    const newTotal = cartItems.reduce((total, item) => 
      total + (item.id === itemId ? item.price * newQuantity : item.price * item.quantity), 0
    );
    setOrderTotal(newTotal);
  };

  // Tabs configuration
  const tabs = [
    {
      id: 'discover',
      label: 'Keşfet',
      icon: '🔍',
      component: DiscoverPage
    },
    {
      id: 'cart',
      label: 'Sepet',
      icon: '🛒',
      badge: cartItems.reduce((total, item) => total + item.quantity, 0),
      component: CartPage
    },
    {
      id: 'orders',
      label: 'Siparişler',
      icon: '📦',
      component: OrdersPage
    },
    {
      id: 'profile',
      label: 'Profil',
      icon: '👤',
      component: ProfilePage
    }
  ];

  const activeTabData = tabs.find(tab => tab.id === activeTab);
  const ActiveComponent = activeTabData?.component;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto pb-20">
        {ActiveComponent && (
          <ActiveComponent
            user={user}
            cartItems={cartItems}
            orderTotal={orderTotal}
            onAddToCart={handleAddToCart}
            onRemoveFromCart={handleRemoveFromCart}
            onUpdateCart={handleUpdateCart}
            onLogout={onLogout}
            onTabChange={setActiveTab}
          />
        )}
      </div>

      {/* Bottom Navigation - Trendyol Go Style */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
        <div className="flex items-center justify-around px-2 py-2">
          {tabs.map(tab => (
            <Button
              key={tab.id}
              variant="ghost"
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex flex-col items-center justify-center py-3 px-2 relative rounded-lg transition-all duration-200 ${
                activeTab === tab.id
                  ? 'text-orange-600 bg-orange-50'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              <div className="relative">
                <span className="text-xl mb-1 block">{tab.icon}</span>
                
                {/* Badge for cart items */}
                {tab.badge && tab.badge > 0 && (
                  <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                    {tab.badge > 99 ? '99+' : tab.badge}
                  </div>
                )}
                
                {/* Active indicator */}
                {activeTab === tab.id && (
                  <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-orange-600 rounded-full"></div>
                )}
              </div>
              
              <span className={`text-xs font-medium ${
                activeTab === tab.id ? 'text-orange-600' : 'text-gray-600'
              }`}>
                {tab.label}
              </span>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CustomerApp;