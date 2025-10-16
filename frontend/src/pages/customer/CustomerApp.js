import React, { useState, useEffect } from 'react';
import DiscoverPage from './DiscoverPage';
import RestaurantMenu from './RestaurantMenu';
import CartPageEnhanced from './CartPageEnhanced';
import OrdersPage from './OrdersPage';
import { useCart } from '../../contexts/CartContext';
import { Button } from '../../components/ui/button';
import { KuryeciniLogo } from '../../components/KuryeciniLogo';
import { CustomerProfileEnhanced } from '../../components/CustomerProfileEnhanced';
import { AddressSelectorEnhanced } from '../../components/AddressSelectorEnhanced';
import { PaymentOptionsEnhanced } from '../../components/PaymentOptionsEnhanced';
import { RatingModal } from '../../components/RatingModal';
import { AddressManagementPage } from './AddressManagementPage';
import { toast } from 'react-hot-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://deliverypro.preview.emergentagent.com';
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

  // Bottom tab navigation - 3 tabs for mobile compatibility
  const tabs = [
    { id: 'discover', label: 'Keşfet', icon: '🔍' },
    { id: 'orders', label: 'Siparişler', icon: '📦' },
    { id: 'profile', label: 'Profil', icon: '👤' }
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header - Trendyol Go Style */}
      <header className="bg-white dark:bg-card border-b border-border sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left: Logo */}
            <div className="flex items-center space-x-3">
              <KuryeciniLogo />
              <div className="hidden sm:flex items-center space-x-2">
                <span className="text-xs font-medium px-2 py-1 bg-primary/10 text-primary rounded-full">
                  Müşteri
                </span>
              </div>
            </div>
            
            {/* Center: Cart Badge */}
            {cartSummary.itemCount > 0 && activeView !== 'cart' && activeView !== 'checkout' && (
              <Button 
                onClick={handleGoToCart} 
                variant="outline"
                className="relative border-primary text-primary hover:bg-primary/5"
              >
                <span className="text-lg mr-1">🛒</span>
                <span className="hidden sm:inline">Sepet</span>
                <span className="ml-1 sm:ml-2 bg-primary text-primary-foreground text-xs font-bold px-2 py-0.5 rounded-full">
                  {cartSummary.itemCount}
                </span>
              </Button>
            )}
            
            {/* Right: User menu */}
            <div className="flex items-center space-x-2 sm:space-x-4">
              <span className="text-sm font-medium text-foreground hidden sm:inline">
                Merhaba, {user?.first_name || user?.email?.split('@')[0]}
              </span>
              <Button onClick={onLogout} variant="outline" size="sm" className="text-xs sm:text-sm">
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        {/* Discover/Restaurant List */}
        <div style={{ display: activeView === 'discover' ? 'block' : 'none' }}>
          <DiscoverPage
            onRestaurantSelect={handleRestaurantSelect}
            user={user}
          />
        </div>

        {/* Restaurant Menu */}
        <div style={{ display: activeView === 'restaurant' ? 'block' : 'none' }}>
          {selectedRestaurant && (
            <RestaurantMenu
              restaurant={selectedRestaurant}
              onBack={handleBackToDiscover}
              onGoToCart={handleGoToCart}
            />
          )}
        </div>

        {/* Cart */}
        <div style={{ display: activeView === 'cart' ? 'block' : 'none' }}>
          <CartPageEnhanced
            onBack={handleBackToDiscover}
            onProceedToCheckout={handleProceedToCheckout}
          />
        </div>

        {/* Checkout Flow */}
        <div style={{ display: activeView === 'checkout' ? 'block' : 'none' }}>
          <div className="max-w-4xl mx-auto p-6 space-y-6">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-2xl font-bold">Ödeme</h1>
              <Button variant="outline" onClick={handleBackToCart}>
                ← Sepete Dön
              </Button>
            </div>

            {/* Step 1: Address Selection */}
            <AddressSelectorEnhanced
              selectedAddress={selectedAddress}
              onAddressSelect={setSelectedAddress}
            />

            {/* Step 2: Payment Method (shown only if address selected) */}
            {selectedAddress && (
              <PaymentOptionsEnhanced
                selectedMethod={selectedPaymentMethod}
                onMethodSelect={setSelectedPaymentMethod}
              />
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
        </div>

        {/* Orders */}
        <div style={{ display: activeView === 'orders' ? 'block' : 'none' }}>
          <OrdersPage user={user} />
        </div>

        {/* Addresses Management */}
        <div style={{ display: activeView === 'addresses' ? 'block' : 'none' }}>
          <AddressManagementPage 
            onBack={() => setActiveView('discover')}
          />
        </div>

        {/* Profile */}
        <div style={{ display: activeView === 'profile' ? 'block' : 'none' }}>
          <CustomerProfileEnhanced 
            user={user} 
            onLogout={onLogout}
            onNavigateToAddresses={() => setActiveView('addresses')}
          />
        </div>
      </main>

      {/* Bottom Navigation - Trendyol Go Style */}
      <nav className="bg-white dark:bg-card border-t border-border sticky bottom-0 z-40 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-around">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveView(tab.id)}
                className={`flex flex-col items-center py-3 px-4 sm:px-8 transition-all duration-200 relative ${
                  activeView === tab.id
                    ? 'text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {/* Active indicator */}
                {activeView === tab.id && (
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-1 bg-primary rounded-b-full" />
                )}
                <span className={`text-2xl mb-1 transition-transform ${
                  activeView === tab.id ? 'scale-110' : 'scale-100'
                }`}>
                  {tab.icon}
                </span>
                <span className={`text-xs font-medium ${
                  activeView === tab.id ? 'font-semibold' : ''
                }`}>
                  {tab.label}
                </span>
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
