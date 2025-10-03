import React, { useState } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { toast } from 'react-hot-toast';

const Cart = ({ cartItems = [], onUpdateCart, onRemoveFromCart, onBack, selectedAddress, selectedRestaurant, user }) => {
  const [isOrderProcessing, setIsOrderProcessing] = useState(false);

  const subtotal = cartItems.reduce((total, item) => total + (item.price * item.quantity), 0);
  const deliveryFee = subtotal > 50 ? 0 : 8.99;
  const serviceFee = subtotal * 0.05; // 5% service fee
  const totalAmount = subtotal + deliveryFee + serviceFee;

  const handleQuantityChange = (itemId, change) => {
    const item = cartItems.find(cartItem => cartItem.id === itemId);
    if (item) {
      if (change === -1 && item.quantity === 1) {
        onRemoveFromCart(itemId);
      } else {
        onUpdateCart(itemId, item.quantity + change);
      }
    }
  };

  const handlePlaceOrder = async () => {
    if (!selectedAddress) {
      toast.error('Lütfen bir teslimat adresi seçin');
      return;
    }

    if (cartItems.length === 0) {
      toast.error('Sepetiniz boş');
      return;
    }

    setIsOrderProcessing(true);

    try {
      // Mock API call - gerçek sipariş API'si
      const orderData = {
        userId: user?.id,
        restaurantId: selectedRestaurant?.id,
        items: cartItems,
        address: selectedAddress,
        subtotal: subtotal,
        deliveryFee: deliveryFee,
        serviceFee: serviceFee,
        total: totalAmount,
        orderDate: new Date().toISOString()
      };

      console.log('Placing order:', orderData);

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      toast.success('🎉 Siparişiniz alındı! Hazırlanıyor...');
      
      // Clear cart after successful order
      // onClearCart();
      
    } catch (error) {
      console.error('Order error:', error);
      toast.error('Sipariş verilemedi. Lütfen tekrar deneyin.');
    } finally {
      setIsOrderProcessing(false);
    }
  };

  if (cartItems.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 p-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <Card className="mb-6 border-0 shadow-xl rounded-3xl bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 text-white overflow-hidden">
            <CardContent className="p-8 relative">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-16 h-16 bg-white/25 backdrop-blur-sm rounded-2xl flex items-center justify-center mr-6 shadow-lg">
                    <span className="text-3xl">🛒</span>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold mb-2">Sepetim</h1>
                    <p className="text-white/90 text-lg">Siparişinizi tamamlayın</p>
                  </div>
                </div>
                
                <Button 
                  variant="outline" 
                  onClick={onBack}
                  className="bg-white/20 border-white/30 text-white hover:bg-white/30 rounded-xl backdrop-blur-sm"
                >
                  ← Geri
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Empty Cart */}
          <Card className="text-center py-16 border-0 shadow-xl rounded-3xl">
            <CardContent>
              <div className="w-32 h-32 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-6xl">🛒</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-4">Sepetiniz Boş</h3>
              <p className="text-gray-600 mb-8">Lezzetli yemekler ekleyerek siparişinizi oluşturun</p>
              <Button 
                onClick={onBack}
                className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300"
              >
                🍽️ Menüye Dön
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <Card className="mb-6 border-0 shadow-xl rounded-3xl bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 text-white overflow-hidden">
          <CardContent className="p-8 relative">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-16 h-16 bg-white/25 backdrop-blur-sm rounded-2xl flex items-center justify-center mr-6 shadow-lg">
                  <span className="text-3xl">🛒</span>
                </div>
                <div>
                  <h1 className="text-3xl font-bold mb-2">Sepetim</h1>
                  <p className="text-white/90 text-lg">{cartItems.length} ürün • {selectedRestaurant?.name}</p>
                </div>
              </div>
              
              <Button 
                variant="outline" 
                onClick={onBack}
                className="bg-white/20 border-white/30 text-white hover:bg-white/30 rounded-xl backdrop-blur-sm"
              >
                ← Geri
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Cart Items */}
          <div className="lg:col-span-2">
            <Card className="border-0 shadow-lg rounded-2xl">
              <CardHeader>
                <h2 className="text-xl font-bold text-gray-800">Sipariş Detayları</h2>
              </CardHeader>
              <CardContent className="space-y-4">
                {cartItems.map(item => (
                  <div key={item.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                    <div className="flex items-center">
                      <img 
                        src={item.image} 
                        alt={item.name}
                        className="w-16 h-16 object-cover rounded-lg mr-4"
                      />
                      <div>
                        <h3 className="font-semibold text-gray-800">{item.name}</h3>
                        <p className="text-sm text-gray-600">{item.description}</p>
                        <p className="text-lg font-bold text-orange-500">₺{item.price.toFixed(2)}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Button 
                        onClick={() => handleQuantityChange(item.id, -1)}
                        className="w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full p-0"
                      >
                        -
                      </Button>
                      <span className="text-lg font-bold text-gray-800 w-8 text-center">{item.quantity}</span>
                      <Button 
                        onClick={() => handleQuantityChange(item.id, 1)}
                        className="w-8 h-8 bg-green-500 hover:bg-green-600 text-white rounded-full p-0"
                      >
                        +
                      </Button>
                      <div className="ml-4 text-right">
                        <p className="text-lg font-bold text-gray-800">₺{(item.price * item.quantity).toFixed(2)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Order Summary & Delivery Address */}
          <div className="space-y-6">
            {/* Delivery Address */}
            <Card className="border-0 shadow-lg rounded-2xl">
              <CardHeader>
                <h2 className="text-xl font-bold text-gray-800">📍 Teslimat Adresi</h2>
              </CardHeader>
              <CardContent>
                {selectedAddress ? (
                  <div className="p-4 bg-blue-50 rounded-xl">
                    <h3 className="font-semibold text-gray-800">{selectedAddress.label}</h3>
                    <p className="text-sm text-gray-600">{selectedAddress.city}</p>
                    <p className="text-sm text-gray-600">{selectedAddress.description}</p>
                  </div>
                ) : (
                  <div className="p-4 bg-red-50 rounded-xl text-center">
                    <p className="text-red-600 font-medium">⚠️ Adres seçilmedi</p>
                    <Button className="mt-2 bg-red-500 hover:bg-red-600 text-white">
                      Adres Seç
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Order Summary */}
            <Card className="border-0 shadow-lg rounded-2xl">
              <CardHeader>
                <h2 className="text-xl font-bold text-gray-800">💳 Sipariş Özeti</h2>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Ara Toplam</span>
                    <span className="font-semibold">₺{subtotal.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Teslimat Ücreti</span>
                    <span className="font-semibold">
                      {deliveryFee === 0 ? (
                        <span className="text-green-600">Ücretsiz</span>
                      ) : (
                        `₺${deliveryFee.toFixed(2)}`
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Hizmet Bedeli (%5)</span>
                    <span className="font-semibold">₺{serviceFee.toFixed(2)}</span>
                  </div>
                  <hr className="my-2" />
                  <div className="flex justify-between text-lg">
                    <span className="font-bold">Toplam</span>
                    <span className="font-bold text-orange-500">₺{totalAmount.toFixed(2)}</span>
                  </div>
                </div>

                {deliveryFee > 0 && (
                  <div className="p-3 bg-yellow-50 rounded-xl">
                    <p className="text-sm text-yellow-700">
                      💡 ₺{(50 - subtotal).toFixed(2)} daha ekleyin, teslimat ücretsiz olsun!
                    </p>
                  </div>
                )}

                <Button 
                  onClick={handlePlaceOrder}
                  disabled={isOrderProcessing || !selectedAddress}
                  className="w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-bold py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isOrderProcessing ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Sipariş Veriliyor...
                    </>
                  ) : (
                    <>🎉 Siparişi Tamamla (₺{totalAmount.toFixed(2)})</>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Cart;