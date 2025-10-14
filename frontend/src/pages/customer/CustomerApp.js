import React, { useState, useEffect } from 'react';
import DiscoverPage from './DiscoverPage';
import RestaurantMenu from './RestaurantMenu';
import CartPage from './CartPage';
import OrdersPage from './OrdersPage';
import { useCart } from '../../contexts/CartContext';
import { Button } from '../../components/ui/button';
import { KuryeciniLogo } from '../../components/KuryeciniLogo';
import { CustomerProfile } from '../../components/CustomerProfile';
import { AddressSelector } from '../../components/AddressSelector';
import { PaymentOptions } from '../../components/PaymentOptions';
import { RatingModal } from '../../components/RatingModal';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://quickship-49.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

// PHASE 2 - Customer App: Profil, Checkout Flow, Ratings
export const CustomerApp = ({ user, onLogout }) => {
  const [activeView, setActiveView] = useState('discover'); // discover, restaurant, cart, checkout, orders, profile
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null);
  const [currentOrderId, setCurrentOrderId] = useState(null);
  const [showRatingModal, setShowRatingModal] = useState(false);
  const [ratingOrder, setRatingOrder] = useState(null);
  
  const { cart, getCartSummary, clearCart } = useCart();
  const cartSummary = getCartSummary ? getCartSummary() : { itemCount: 0, total: 0 };

  console.log('🚀 CustomerApp FAZ 2 rendered - activeView:', activeView, 'user:', user?.first_name, 'cart:', cart, 'getCartSummary:', typeof getCartSummary);

  // Set authentication token for API calls
  // Cookie-based authentication - no token management needed
  useEffect(() => {
    if (user) {
      console.log('✅ CustomerApp loaded for user:', user.email);
    }
  }, [user]);

  // Handle address refresh when user adds new address
  const handleAddressAdded = (newAddress) => {
    console.log('📍 New address added:', newAddress);
    // DiscoverPage will be notified via re-render
    if (activeView === 'profile') {
      // Switch back to discover after adding address
      setActiveView('discover');
    }
  };

  // Navigation handlers for the customer journey
  const handleRestaurantSelect = (restaurant) => {
    setSelectedRestaurant(restaurant);
    setActiveView('restaurant');
  };

  const handleGoToCart = () => {
    setActiveView('cart');
  };

  const handleProceedToPayment = (cartData) => {
    console.log('Proceeding to payment with cart data:', cartData);
    if (cartData.selectedAddress) {
      setSelectedAddress(cartData.selectedAddress);
    }
    setActiveView('payment');
  };

  const handlePaymentSuccess = (orderData) => {
    console.log('Payment successful:', orderData);
    setCurrentOrderId(orderData.order.id);
    setActiveView('orderTracking');
  };

  const handleOrderSelect = (orderId) => {
    setCurrentOrderId(orderId);
    setActiveView('orderTracking');
  };

  const handleBackToDiscover = () => {
    setActiveView('discover');
    setSelectedRestaurant(null);
  };

  const handleBackToCart = () => {
    setActiveView('cart');
  };

  const handleBackToOrders = () => {
    setActiveView('orders');
  };

  const handleTabChange = (tab) => {
    setActiveView(tab);
  };

  // Bottom tab navigation data
  const tabs = [
    { 
      id: 'discover', 
      label: 'Keşfet', 
      icon: '🔍',
      active: activeView === 'discover'
    },
    { 
      id: 'gps-discover', 
      label: 'GPS Keşfet', 
      icon: '📍',
      active: activeView === 'gps-discover'
    },
    { 
      id: 'addresses', 
      label: 'Adresler', 
      icon: '🏠',
      active: activeView === 'addresses'
    },
    { 
      id: 'cart', 
      label: 'Sepet', 
      icon: '🛒',
      badge: cart?.items?.length > 0 ? cartSummary.itemCount : null,
      active: activeView === 'cart'
    },
    { 
      id: 'orders', 
      label: 'Siparişler', 
      icon: '📦',
      active: activeView === 'orders'
    },
    { 
      id: 'profile', 
      label: 'Profil', 
      icon: '👤',
      active: activeView === 'profile'
    }
  ];

  // Render current view
  const renderCurrentView = () => {
    switch (activeView) {
      case 'discover':
        return (
          <DiscoverPage 
            user={user}
            onRestaurantSelect={handleRestaurantSelect}
            onTabChange={handleTabChange}
          />
        );

      case 'gps-discover':
        return (
          <CustomerDiscover 
            onSelectBusiness={handleRestaurantSelect}
          />
        );

      case 'addresses':
        return <CustomerAddressManager />;

      case 'restaurant':
        return (
          <RestaurantMenu 
            restaurant={selectedRestaurant}
            onBack={handleBackToDiscover}
            onGoToCart={handleGoToCart}
          />
        );

      case 'cart':
        return (
          <CartPage 
            onBack={handleBackToDiscover}
            onProceedToPayment={handleProceedToPayment}
            user={user}
          />
        );

      case 'payment':
        return (
          <PaymentPage 
            selectedAddress={selectedAddress}
            onBack={handleBackToCart}
            onPaymentSuccess={handlePaymentSuccess}
            user={user}
          />
        );

      case 'orders':
        return (
          <OrdersPage 
            user={user}
            onOrderSelect={handleOrderSelect}
            onTabChange={handleTabChange}
          />
        );

      case 'profile':
        return (
          <ProfilePage 
            user={user}
            onLogout={onLogout}
            onTabChange={handleTabChange}
            onAddressChange={setSelectedAddress}
            selectedAddress={selectedAddress}
            onAddressAdded={handleAddressAdded}
          />
        );

      case 'orderTracking':
        return (
          <OrderTrackingPage 
            orderId={currentOrderId}
            onBack={handleBackToOrders}
            user={user}
          />
        );

      default:
        return (
          <DiscoverPage 
            user={user}
            onRestaurantSelect={handleRestaurantSelect}
            onTabChange={handleTabChange}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Header */}
      <div className="sticky top-0 z-50 bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Brand */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <KuryeciniLogo size="medium" useRealLogo={true} />
                <KuryeciniLogo size="small" />
              </div>
              <div>
                <h1 className="text-lg font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
                  Kuryecini
                </h1>
                <p className="text-xs text-gray-500">Müşteri Paneli</p>
              </div>
            </div>
            
            {/* User Info and Logout */}
            <div className="flex items-center space-x-4">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name || user?.email || 'Kullanıcı'}
                </p>
                <p className="text-xs text-gray-500">
                  {cartSummary.itemCount} ürün • ₺{cartSummary.total}
                </p>
              </div>
              <Button
                onClick={onLogout}
                variant="ghost"
                size="sm"
                className="text-gray-600 hover:text-gray-900"
              >
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col">
        {/* Main Content */}
        <div className="flex-1 pb-20"> {/* Bottom padding for tab bar */}
          {renderCurrentView()}
        </div>

      {/* Bottom Tab Navigation - Only show on main tabs, not on sub-pages */}
      {['discover', 'cart', 'orders', 'profile'].includes(activeView) && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
          <div className="flex justify-around items-center py-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex flex-col items-center py-2 px-4 rounded-lg transition-colors ${
                  tab.active
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                <div className="relative">
                  <span className="text-xl">{tab.icon}</span>
                  {tab.badge && (
                    <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center min-w-5">
                      {tab.badge > 99 ? '99+' : tab.badge}
                    </span>
                  )}
                </div>
                <span className="text-xs mt-1 font-medium">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Floating Cart Button - Show on restaurant page when cart has items */}
      {activeView === 'restaurant' && cart?.items?.length > 0 && (
        <div className="fixed bottom-6 right-6 z-40">
          <button 
            onClick={handleGoToCart}
            className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
          >
            🛒 Sepet ({cartSummary.itemCount}) - ₺{cartSummary.total.toFixed(2)}
          </button>
        </div>
      )}

        {/* Debug Info - Remove in production */}
        {process.env.NODE_ENV === 'development' && (
          <div className="fixed top-4 right-4 bg-black text-white p-2 rounded text-xs z-50 opacity-70">
            View: {activeView} | Cart: {cart?.items?.length || 0} items
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerApp;