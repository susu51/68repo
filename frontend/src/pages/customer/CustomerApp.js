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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://admin-wsocket.preview.emergentagent.com';
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

  console.log('🚀 CustomerApp - cart:', cart, 'items:', cart?.items?.length, 'cartSummary:', cartSummary);

  // Force light mode for customer panel by removing dark class
  useEffect(() => {
    document.documentElement.classList.remove('dark');
    document.documentElement.style.colorScheme = 'light';
    
    // Cleanup: restore dark mode preference when unmounting
    return () => {
      const savedTheme = localStorage.getItem('kuryecini-theme');
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.style.colorScheme = 'dark';
      }
    };
  }, []);

  // Navigation handlers
  const handleRestaurantSelect = (restaurant) => {
    setSelectedRestaurant(restaurant);
    setActiveView('restaurant');
  };

  const handleGoToCart = () => {
    setActiveView('cart');
  };

  const handleProceedToCheckout = () => {
    console.log('🛒 Proceeding to checkout, cart:', cartSummary);
    
    if (cartSummary.itemCount === 0) {
      toast.error('Sepetiniz boş');
      return;
    }
    
    console.log('✅ Setting activeView to checkout');
    setActiveView('checkout');
    toast.success('Ödeme sayfasına yönlendiriliyorsunuz...');
  };

  const handleCreateOrder = async () => {
    console.log('🎬 handleCreateOrder STARTED');
    console.log('📍 selectedAddress:', selectedAddress);
    console.log('💳 selectedPaymentMethod:', selectedPaymentMethod);
    console.log('🛒 cart:', cart);
    
    try {
      if (!selectedAddress) {
        console.error('❌ VALIDATION FAILED: No address selected');
        toast.error('Lütfen teslimat adresi seçin');
        return;
      }
      if (!selectedPaymentMethod) {
        console.error('❌ VALIDATION FAILED: No payment method selected');
        toast.error('Lütfen ödeme yöntemi seçin');
        return;
      }

      // Check cart items
      const cartItems = cart?.items || [];
      console.log('🛒 Cart items:', cartItems);
      
      if (!cartItems || cartItems.length === 0) {
        console.error('❌ VALIDATION FAILED: Cart is empty');
        toast.error('Sepetiniz boş');
        return;
      }

      // Get restaurant_id from cart
      const restaurant_id = cart?.restaurant?.id || cart?.businessId;
      console.log('🏪 Restaurant ID:', restaurant_id);
      
      if (!restaurant_id) {
        console.error('❌ VALIDATION FAILED: No restaurant ID');
        toast.error('Restoran bilgisi bulunamadı');
        return;
      }

      // Prepare order data matching backend OrderCreate model
      const orderData = {
        business_id: restaurant_id,
        items: cartItems.map(item => ({
          product_id: item.id,
          title: item.name || item.title,
          price: item.price,
          quantity: item.quantity,
          notes: item.notes || ''
        })),
        delivery_address: {
          label: selectedAddress.label || selectedAddress.adres_basligi || 'Ev',
          address: selectedAddress.address || selectedAddress.acik_adres || selectedAddress.full,
          lat: selectedAddress.lat || 0,
          lng: selectedAddress.lng || 0,
          notes: selectedAddress.notes || ''
        },
        payment_method: selectedPaymentMethod === 'Nakit' ? 'cash_on_delivery' : 
                       selectedPaymentMethod === 'Kart' ? 'pos_on_delivery' : 'online',
        notes: cart?.notes || ''
      };

      console.log('🎉 Creating order with backend API:', JSON.stringify(orderData, null, 2));

      const response = await fetch(`${API}/api/orders`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });

      console.log('📡 API Response status:', response.status);

      if (response.ok) {
        const orderData = await response.json();
        console.log('✅ Order created successfully:', orderData);
        
        // Show success message with order code
        toast.success(`✅ Siparişiniz Onaylandı!\n\nSipariş Kodu: ${orderData.id.substring(0, 8).toUpperCase()}`, {
          duration: 6000,
          icon: '🎉',
          style: {
            fontSize: '16px',
            fontWeight: 'bold'
          }
        });
        
        console.log('✅ Order created:', orderData);
        console.log('📦 Order ID:', orderData.id);
        console.log('🏪 Business ID:', orderData.business_id);
        console.log('👤 Business Name:', orderData.business_name);
        console.log('💰 Total:', orderData.total_amount);
        
        // Clear cart and navigate
        clearCart();
        setCurrentOrderId(orderData.id);
        
        // Show business confirmation
        setTimeout(() => {
          toast.success(`Siparişiniz ${orderData.business_name || 'restorana'} iletildi`, {
            duration: 4000
          });
        }, 800);
        
        // Navigate to orders page after a brief delay
        setTimeout(() => {
          setActiveView('orders');
        }, 1200);
      } else {
        const error = await response.json();
        console.error('❌ Order creation error:', error);
        toast.error(error.detail || 'Sipariş oluşturulamadı');
      }
    } catch (error) {
      console.error('❌ Sipariş oluşturma hatası:', error);
      console.error('❌ Error stack:', error.stack);
      toast.error('Bir hata oluştu: ' + error.message);
    }
  };
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
              <h1 className="text-2xl font-bold">✅ Ödeme ve Teslimat</h1>
              <Button variant="outline" onClick={handleBackToCart}>
                ← Sepete Dön
              </Button>
            </div>

            {/* Debug Info */}
            {console.log('🎯 Checkout page - selectedAddress:', selectedAddress, 'selectedPaymentMethod:', selectedPaymentMethod)}

            {/* Step 1: Address Selection */}
            <AddressSelectorEnhanced
              selectedAddress={selectedAddress}
              onAddressSelect={(addr) => {
                console.log('📍 Address selected:', addr);
                setSelectedAddress(addr);
                toast.success('Adres seçildi');
              }}
            />

            {/* Step 2: Payment Method (shown only if address selected) */}
            {selectedAddress && (
              <PaymentOptionsEnhanced
                selectedMethod={selectedPaymentMethod}
                onMethodSelect={(method) => {
                  console.log('💳 Payment method selected:', method);
                  setSelectedPaymentMethod(method);
                  toast.success('Ödeme yöntemi seçildi');
                }}
              />
            )}

            {/* Order Summary & Confirm */}
            {selectedAddress && selectedPaymentMethod && (
              <div className="bg-white rounded-lg shadow-sm p-6 border-2 border-green-200">
                <h3 className="font-bold text-lg mb-4 text-green-700">✅ Sipariş Özeti</h3>
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
                <Button 
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('🎉 Create order button CLICKED!');
                    console.log('🎉 Button event:', e);
                    handleCreateOrder();
                  }} 
                  className="w-full bg-green-600 hover:bg-green-700" 
                  type="button"
                >
                  🎉 Siparişi Onayla ve Ver
                </Button>
              </div>
            )}

            {/* Show hint if payment method not selected */}
            {selectedAddress && !selectedPaymentMethod && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">⚠️ Ödeme yöntemi seçin</p>
              </div>
            )}

            {/* Show hint if address not selected */}
            {!selectedAddress && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-800">ℹ️ Yukarıdan teslimat adresinizi seçin</p>
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
