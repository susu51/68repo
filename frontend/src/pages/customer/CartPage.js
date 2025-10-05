import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { useCart } from '../../contexts/CartContext';

const CartPage = ({ onBack, onProceedToPayment, user }) => {
  const { 
    cart, 
    updateQuantity, 
    removeFromCart, 
    clearCart, 
    getCartSummary 
  } = useCart();
  
  const [couponCode, setCouponCode] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [userAddresses, setUserAddresses] = useState([]);
  const [showAddressSelector, setShowAddressSelector] = useState(false);

  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Load user addresses
  useEffect(() => {
    loadUserAddresses();
  }, []);

  const loadUserAddresses = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      if (!token) return;

      const response = await fetch(`${API}/api/addresses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const addresses = await response.json();
        setUserAddresses(addresses || []);
        
        // Auto-select first address if available
        if (addresses.length > 0 && !selectedAddress) {
          setSelectedAddress(addresses[0]);
        }
      }
    } catch (error) {
      console.error('Error loading addresses:', error);
    }
  };

  const cartSummary = getCartSummary();
  const discount = appliedCoupon ? appliedCoupon.amount : 0;
  const finalTotal = Math.max(0, cartSummary.total - discount);

  const handleQuantityChange = (itemId, newQuantity) => {
    if (newQuantity < 1) {
      removeFromCart(itemId);
    } else {
      updateQuantity(itemId, newQuantity);
    }
  };

  const handleApplyCoupon = () => {
    // Mock coupon logic
    if (couponCode.toLowerCase() === 'indirim20') {
      const discountAmount = cartSummary.subtotal * 0.20;
      setAppliedCoupon({
        code: 'INDIRIM20',
        amount: discountAmount,
        type: 'percentage'
      });
      toast.success('Kupon uygulandı! %20 indirim');
    } else if (couponCode.toLowerCase() === 'yeni10') {
      setAppliedCoupon({
        code: 'YENI10',
        amount: 10,
        type: 'fixed'
      });
      toast.success('Kupon uygulandı! ₺10 indirim');
    } else if (couponCode.toLowerCase() === 'teslimat0') {
      setAppliedCoupon({
        code: 'TESLIMAT0',
        amount: cartSummary.deliveryFee,
        type: 'free_delivery'
      });
      toast.success('Kupon uygulandı! Ücretsiz teslimat');
    } else {
      toast.error('Geçersiz kupon kodu');
    }
    setCouponCode('');
  };

  const removeCoupon = () => {
    setAppliedCoupon(null);
    toast.success('Kupon kaldırıldı');
  };

  const handleProceedToPayment = () => {
    if (cart.items.length === 0) {
      toast.error('Sepetiniz boş');
      return;
    }

    if (!selectedAddress) {
      toast.error('Lütfen teslimat adresi seçin');
      setShowAddressSelector(true);
      return;
    }

    // Pass cart data, selected address and totals to payment process
    onProceedToPayment({
      cart,
      cartSummary,
      discount,
      appliedCoupon,
      finalTotal,
      selectedAddress
    });
  };

  // Empty cart view
  if (cart.items.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center px-4">
          <span className="text-6xl mb-4 block">🛒</span>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Sepetiniz boş
          </h2>
          <p className="text-gray-600 mb-6">
            Keşfet bölümünden lezzetli yemekleri sepetinize ekleyin
          </p>
          <button 
            onClick={onBack}
            className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3 rounded-lg font-semibold"
          >
            Restoranları Keşfet
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="flex items-center mb-6">
          <button 
            onClick={onBack}
            className="mr-4 p-2 rounded-full hover:bg-gray-200"
          >
            ←
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Sepetim</h1>
            <p className="text-sm text-gray-600">{cartSummary.itemCount} ürün</p>
          </div>
        </div>

        {/* Restaurant Info */}
        {cart.restaurant && (
          <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🏪</span>
              <div>
                <h3 className="font-semibold text-gray-900">{cart.restaurant.name}</h3>
                <p className="text-sm text-gray-600">
                  Teslimat süresi: {cart.restaurant.deliveryTime || '25-35'} dk
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Cart Items */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <h3 className="font-semibold text-gray-900 mb-4">Sipariş Detayları</h3>
          
          <div className="space-y-4">
            {cart.items.map((item) => (
              <div key={item.id} className="flex items-center space-x-4 py-3 border-b last:border-b-0">
                <div className="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                  <img 
                    src={item.image || 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=300'} 
                    alt={item.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=300';
                    }}
                  />
                </div>
                
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 truncate">{item.name}</h4>
                  <p className="text-sm text-gray-600">₺{item.price.toFixed(2)}</p>
                </div>
                
                {/* Quantity Controls */}
                <div className="flex items-center space-x-2">
                  <button 
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    className="w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
                  >
                    -
                  </button>
                  <span className="w-8 text-center font-medium">{item.quantity}</span>
                  <button 
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                    className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center hover:bg-green-600"
                  >
                    +
                  </button>
                </div>
                
                <div className="text-right">
                  <p className="font-semibold">₺{(item.price * item.quantity).toFixed(2)}</p>
                  <button 
                    onClick={() => removeFromCart(item.id)}
                    className="text-red-500 text-sm hover:text-red-700"
                  >
                    Sil
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Coupon Section */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <h3 className="font-semibold text-gray-900 mb-3">İndirim Kuponu</h3>
          
          {appliedCoupon ? (
            <div className="flex items-center justify-between bg-green-50 p-3 rounded-lg">
              <div>
                <p className="font-medium text-green-700">🎫 {appliedCoupon.code}</p>
                <p className="text-sm text-green-600">
                  -{appliedCoupon.type === 'percentage' ? '%20' : '₺' + appliedCoupon.amount.toFixed(2)} indirim
                </p>
              </div>
              <button 
                onClick={removeCoupon}
                className="text-red-500 hover:text-red-700 text-sm"
              >
                Kaldır
              </button>
            </div>
          ) : (
            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="Kupon kodunuz (örn: INDIRIM20)"
                value={couponCode}
                onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button 
                onClick={handleApplyCoupon}
                disabled={!couponCode.trim()}
                className="bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Uygula
              </button>
            </div>
          )}

          <div className="mt-3 text-xs text-gray-500">
            <p>Geçerli kuponlar: INDIRIM20 (%20 indirim), YENI10 (₺10 indirim), TESLIMAT0 (ücretsiz teslimat)</p>
          </div>
        </div>

        {/* Price Summary */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-4">
          <h3 className="font-semibold text-gray-900 mb-3">Ödeme Özeti</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Ara Toplam</span>
              <span>₺{cartSummary.subtotal.toFixed(2)}</span>
            </div>
            
            <div className="flex justify-between">
              <span>Teslimat Ücreti</span>
              <span className={appliedCoupon?.type === 'free_delivery' ? 'line-through text-gray-400' : ''}>
                ₺{cartSummary.deliveryFee.toFixed(2)}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span>Servis Ücreti</span>
              <span>₺{cartSummary.serviceFee.toFixed(2)}</span>
            </div>
            
            {appliedCoupon && (
              <div className="flex justify-between text-green-600">
                <span>İndirim ({appliedCoupon.code})</span>
                <span>-₺{appliedCoupon.amount.toFixed(2)}</span>
              </div>
            )}
            
            <div className="flex justify-between font-bold text-lg border-t pt-2">
              <span>Toplam</span>
              <span>₺{finalTotal.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={handleProceedToPayment}
            className="w-full bg-blue-500 text-white py-4 rounded-lg font-semibold hover:bg-blue-600 transition-colors"
          >
            Ödemeye Geç - ₺{finalTotal.toFixed(2)}
          </button>
          
          <button
            onClick={clearCart}
            className="w-full bg-gray-500 text-white py-3 rounded-lg font-medium hover:bg-gray-600 transition-colors"
          >
            Sepeti Temizle
          </button>
        </div>

        {/* Security Note */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            🔒 Güvenli ödeme sistemi ile korunuyorsunuz
          </p>
        </div>
      </div>
    </div>
  );
};

export default CartPage;