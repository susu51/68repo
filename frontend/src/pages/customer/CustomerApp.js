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

  // Navigation handlers
  const handleRestaurantSelect = (restaurant) => {
    setSelectedRestaurant(restaurant);
    setActiveView('restaurant');
  };

  const handleGoToCart = () => {
    setActiveView('cart');
  };

  const handleProceedToCheckout = () => {
    if (cartSummary.itemCount === 0) {
      toast.error('Sepetiniz boş');
      return;
    }
    setActiveView('checkout');
  };

  const handleCreateOrder = async () => {
    try {
      if (!selectedAddress) {
        toast.error('Lütfen teslimat adresi seçin');
        return;
      }
      if (!selectedPaymentMethod) {
        toast.error('Lütfen ödeme yöntemi seçin');
        return;
      }

      const orderData = {
        business_id: selectedRestaurant?._id,
        items: cart.map(item => ({
          product_id: item._id,
          title: item.title,
          price: item.price,
          quantity: item.quantity
        })),
        delivery_address: {
          label: selectedAddress.label,
          address: selectedAddress.full,
          lat: selectedAddress.location?.coordinates?.[1] || 0,
          lng: selectedAddress.location?.coordinates?.[0] || 0
        },
        payment_method: selectedPaymentMethod
      };

      const response = await fetch(`${API}/orders`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Sipariş oluşturuldu!');
        clearCart();
        setCurrentOrderId(data.id);
        setActiveView('orders');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Sipariş oluşturulamadı');
      }
    } catch (error) {
      console.error('Sipariş oluşturma hatası:', error);
      toast.error('Bir hata oluştu');
    }
  };

  const handleBackToDiscover = () => {
    setActiveView('discover');
    setSelectedRestaurant(null);
  };

  const handleBackToCart = () => {
    setActiveView('cart');
  };

  // Bottom tab navigation - REMOVED: GPS Keşfet, Adresler | ADDED: Profil
  const tabs = [
    { id: 'discover', label: 'Keşfet', icon: '🔍' },
    { id: 'orders', label: 'Siparişler', icon: '📦' },
    { id: 'profile', label: 'Profil', icon: '👤' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <KuryeciniLogo />
              <span className="text-sm text-gray-600">Müşteri</span>
            </div>
            
            {/* Cart Badge */}
            {cartSummary.itemCount > 0 && activeView !== 'cart' && activeView !== 'checkout' && (
              <Button onClick={handleGoToCart} variant="outline">
                🛒 Sepet ({cartSummary.itemCount})
              </Button>
            )}
            
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Merhaba, {user?.first_name || user?.email?.split('@')[0]}
              </span>
              <Button onClick={onLogout} variant="outline" size="sm">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {/* Discover/Restaurant List */}
        {activeView === 'discover' && (
          <DiscoverPage
            onRestaurantSelect={handleRestaurantSelect}
            user={user}
          />
        )}

        {/* Restaurant Menu */}
        {activeView === 'restaurant' && selectedRestaurant && (
          <RestaurantMenu
            restaurant={selectedRestaurant}
            onBack={handleBackToDiscover}
            onGoToCart={handleGoToCart}
          />
        )}

        {/* Cart */}
        {activeView === 'cart' && (
          <CartPage
            onBack={handleBackToDiscover}
            onProceedToCheckout={handleProceedToCheckout}
          />
        )}

        {/* Checkout Flow */}
        {activeView === 'checkout' && (
          <div className="max-w-4xl mx-auto p-6 space-y-6">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-2xl font-bold">Ödeme</h1>
              <Button variant="outline" onClick={handleBackToCart}>
                ← Sepete Dön
              </Button>
            </div>

            {/* Step 1: Address Selection */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <AddressSelector
                selectedAddress={selectedAddress}
                onAddressSelect={setSelectedAddress}
              />
            </div>

            {/* Step 2: Payment Method (shown only if address selected) */}
            {selectedAddress && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <PaymentOptions
                  selectedMethod={selectedPaymentMethod}
                  onMethodSelect={setSelectedPaymentMethod}
                />
              </div>
            )}

            {/* Order Summary & Confirm */}
            {selectedAddress && selectedPaymentMethod && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="font-bold text-lg mb-4">Sipariş Özeti</h3>
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between">
                    <span>Ürün Toplam:</span>
                    <span>₺{cartSummary.total?.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Teslimat:</span>
                    <span>₺10.00</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg border-t pt-2">
                    <span>Toplam:</span>
                    <span>₺{(cartSummary.total + 10).toFixed(2)}</span>
                  </div>
                </div>
                <Button onClick={handleCreateOrder} className="w-full" size="lg">
                  Siparişi Onayla
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Orders */}
        {activeView === 'orders' && (
          <OrdersPage user={user} />
        )}

        {/* Profile */}
        {activeView === 'profile' && (
          <CustomerProfile user={user} />
        )}
      </main>

      {/* Bottom Navigation */}
      <nav className="bg-white border-t border-gray-200 sticky bottom-0">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-around">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveView(tab.id)}
                className={`flex flex-col items-center py-3 px-6 transition-colors ${
                  activeView === tab.id
                    ? 'text-orange-600 border-t-2 border-orange-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <span className="text-2xl mb-1">{tab.icon}</span>
                <span className="text-xs font-medium">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Rating Modal */}
      {showRatingModal && ratingOrder && (
        <RatingModal
          order={ratingOrder}
          onClose={() => {
            setShowRatingModal(false);
            setRatingOrder(null);
          }}
        />
      )}
    </div>
  );
};
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