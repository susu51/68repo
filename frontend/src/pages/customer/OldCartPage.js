import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { useCart } from '../../contexts/CartContext';

const CartPage = ({ onBack, onProceedToPayment, user }) => {
  const [couponCode, setCouponCode] = useState('');
  const [discount, setDiscount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cod'); // 'cod' | 'online'
  const [selectedAddress, setSelectedAddress] = useState(null);

  const deliveryFee = orderTotal > 50 ? 0 : 8.50;
  const serviceFee = orderTotal * 0.02; // %2 servis ücreti
  const finalTotal = orderTotal + deliveryFee + serviceFee - discount;

  const handleQuantityChange = (itemId, newQuantity) => {
    if (newQuantity < 1) {
      onRemoveFromCart(itemId);
    } else {
      onUpdateCart(itemId, newQuantity);
    }
  };

  const handleApplyCoupon = () => {
    // Demo coupon logic
    if (couponCode.toLowerCase() === 'indirim20') {
      const discountAmount = orderTotal * 0.20;
      setDiscount(discountAmount);
      toast.success('Kupon uygulandı! %20 indirim');
    } else if (couponCode.toLowerCase() === 'yeni10') {
      const discountAmount = 10;
      setDiscount(discountAmount);
      toast.success('Kupon uygulandı! ₺10 indirim');
    } else {
      toast.error('Geçersiz kupon kodu');
    }
  };

  const handleCheckout = () => {
    if (cartItems.length === 0) {
      toast.error('Sepetiniz boş');
      return;
    }

    if (!selectedAddress) {
      toast.error('Lütfen teslimat adresi seçin');
      return;
    }

    // Simulate order creation
    toast.success('Siparişiniz alındı! Hazırlanmaya başlandı.');
    
    // Navigate to orders tab
    setTimeout(() => {
      onTabChange('orders');
    }, 1500);
  };

  // Empty cart view
  if (cartItems.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center px-4">
          <span className="text-6xl mb-4 block">🛒</span>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Sepetiniz boş
          </h2>
          <p className="text-gray-600 mb-6">
            Keşfet sekmesinden lezzetli yemekleri sepetinize ekleyin
          </p>
          <Button 
            onClick={() => onTabChange('discover')}
            className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3"
          >
            Restoranları Keşfet
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-40">
        <div className="p-4">
          <h1 className="text-xl font-bold text-gray-800">Sepetim</h1>
          <p className="text-sm text-gray-600">{cartItems.length} ürün</p>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Cart Items */}
        <Card>
          <CardHeader>
            <h3 className="font-semibold">Sipariş Özeti</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            {cartItems.map(item => (
              <div key={item.id} className="flex items-center space-x-4 pb-4 border-b border-gray-100 last:border-b-0">
                <div className="w-16 h-16 bg-gray-100 rounded-lg overflow-hidden">
                  {item.image_url ? (
                    <img 
                      src={item.image_url} 
                      alt={item.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xl">
                      🍽️
                    </div>
                  )}
                </div>
                
                <div className="flex-1">
                  <h4 className="font-medium text-gray-800">{item.name}</h4>
                  <p className="text-sm text-gray-600">₺{item.price?.toFixed(2)}</p>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    className="w-8 h-8 p-0"
                  >
                    -
                  </Button>
                  <span className="w-8 text-center font-medium">{item.quantity}</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                    className="w-8 h-8 p-0"
                  >
                    +
                  </Button>
                </div>
                
                <div className="text-right">
                  <p className="font-bold">₺{((item.price || 0) * (item.quantity || 0)).toFixed(2)}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRemoveFromCart(item.id)}
                    className="text-red-500 hover:text-red-700 p-0 h-auto"
                  >
                    Kaldır
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Coupon Section */}
        <Card>
          <CardHeader>
            <h3 className="font-semibold">Kupon & İndirim</h3>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-2">
              <Input
                placeholder="Kupon kodunu girin"
                value={couponCode}
                onChange={(e) => setCouponCode(e.target.value)}
                className="flex-1"
              />
              <Button 
                onClick={handleApplyCoupon}
                variant="outline"
              >
                Uygula
              </Button>
            </div>
            {discount > 0 && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-green-700 font-medium">
                  ✅ Kupon uygulandı! ₺{discount.toFixed(2)} indirim
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payment Method */}
        <Card>
          <CardHeader>
            <h3 className="font-semibold">Ödeme Yöntemi</h3>
          </CardHeader>
          <CardContent className="space-y-3">
            <div 
              className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                paymentMethod === 'cod' 
                  ? 'border-orange-500 bg-orange-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setPaymentMethod('cod')}
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  💵
                </div>
                <div>
                  <p className="font-medium">Kapıda Ödeme</p>
                  <p className="text-sm text-gray-600">Nakit veya kartla</p>
                </div>
                {paymentMethod === 'cod' && (
                  <div className="ml-auto">
                    <span className="text-orange-500">✓</span>
                  </div>
                )}
              </div>
            </div>

            <div 
              className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                paymentMethod === 'online' 
                  ? 'border-orange-500 bg-orange-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setPaymentMethod('online')}
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  💳
                </div>
                <div>
                  <p className="font-medium">Online Ödeme</p>
                  <p className="text-sm text-gray-600">Kredi/banka kartı</p>
                </div>
                {paymentMethod === 'online' && (
                  <div className="ml-auto">
                    <span className="text-orange-500">✓</span>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Address Selection */}
        <Card>
          <CardHeader>
            <h3 className="font-semibold">Teslimat Adresi</h3>
          </CardHeader>
          <CardContent>
            <Button
              variant="outline"
              className="w-full justify-start h-auto p-4"
              onClick={() => {
                // Navigate to address selection
                toast.info('Adres seçimi yakında eklenecek');
              }}
            >
              <div className="text-left">
                {selectedAddress ? (
                  <div>
                    <p className="font-medium">{selectedAddress.label}</p>
                    <p className="text-sm text-gray-600">{selectedAddress.description}</p>
                  </div>
                ) : (
                  <div>
                    <p className="font-medium text-gray-600">📍 Teslimat adresi seçin</p>
                    <p className="text-sm text-gray-500">Kayıtlı adreslerinizden seçin</p>
                  </div>
                )}
              </div>
            </Button>
          </CardContent>
        </Card>

        {/* Order Summary */}
        <Card>
          <CardHeader>
            <h3 className="font-semibold">Ödeme Özeti</h3>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span>Ürün Tutarı</span>
              <span>₺{orderTotal.toFixed(2)}</span>
            </div>
            
            <div className="flex justify-between">
              <span>Teslimat Ücreti</span>
              <span className={deliveryFee === 0 ? 'text-green-600' : ''}>
                {deliveryFee === 0 ? 'Ücretsiz' : `₺${deliveryFee.toFixed(2)}`}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span>Servis Ücreti</span>
              <span>₺{serviceFee.toFixed(2)}</span>
            </div>
            
            {discount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>İndirim</span>
                <span>-₺{discount.toFixed(2)}</span>
              </div>
            )}
            
            <div className="border-t pt-3">
              <div className="flex justify-between font-bold text-lg">
                <span>Toplam</span>
                <span className="text-orange-600">₺{finalTotal.toFixed(2)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Checkout Button */}
        <div className="sticky bottom-20 bg-white p-4 -mx-4 border-t">
          <Button
            onClick={handleCheckout}
            className="w-full bg-orange-500 hover:bg-orange-600 text-white py-4 text-lg font-semibold"
          >
            {paymentMethod === 'online' ? '💳' : '💵'} Siparişi Tamamla (₺{finalTotal.toFixed(2)})
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CartPage;