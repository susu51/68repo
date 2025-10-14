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
