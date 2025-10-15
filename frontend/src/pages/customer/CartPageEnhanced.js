import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { useCart } from '../../contexts/CartContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { ShoppingCart, Trash2, Plus, Minus, Tag, AlertCircle } from 'lucide-react';

const CartPageEnhanced = ({ onBack, onProceedToCheckout }) => {
  const { 
    cart, 
    updateQuantity, 
    removeFromCart, 
    clearCart, 
    getCartSummary 
  } = useCart();
  
  const [couponCode, setCouponCode] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState(null);

  // Safety check for cart
  const safeCart = Array.isArray(cart) ? cart : [];
  const cartSummary = getCartSummary ? getCartSummary() : { itemCount: 0, total: 0 };
  
  // Calculate totals
  const subtotal = cartSummary.total || 0;
  const deliveryFee = 10.0;
  const discount = appliedCoupon ? appliedCoupon.amount : 0;
  const finalTotal = Math.max(0, subtotal + deliveryFee - discount);

  const handleQuantityChange = (itemId, newQuantity) => {
    if (newQuantity < 1) {
      removeFromCart(itemId);
      toast.success('Ürün sepetten kaldırıldı');
    } else {
      updateQuantity(itemId, newQuantity);
    }
  };

  const handleApplyCoupon = () => {
    // Demo coupon logic - Trendyol style coupons
    const code = couponCode.toLowerCase();
    
    if (code === 'indirim20') {
      const discountAmount = subtotal * 0.20;
      setAppliedCoupon({
        code: 'INDIRIM20',
        amount: discountAmount,
        type: 'percentage',
        description: '%20 İndirim'
      });
      toast.success('🎉 Kupon uygulandı! %20 indirim');
    } else if (code === 'yeni10') {
      setAppliedCoupon({
        code: 'YENI10',
        amount: 10,
        type: 'fixed',
        description: '₺10 İndirim'
      });
      toast.success('🎉 Kupon uygulandı! ₺10 indirim');
    } else if (code === 'teslimat0') {
      setAppliedCoupon({
        code: 'TESLIMAT0',
        amount: deliveryFee,
        type: 'free_delivery',
        description: 'Ücretsiz Teslimat'
      });
      toast.success('🎉 Kupon uygulandı! Ücretsiz teslimat');
    } else {
      toast.error('Geçersiz kupon kodu');
    }
    setCouponCode('');
  };

  const removeCoupon = () => {
    setAppliedCoupon(null);
    toast.success('Kupon kaldırıldı');
  };

  const handleProceed = () => {
    if (!cart || cart.length === 0) {
      toast.error('Sepetiniz boş');
      return;
    }
    onProceedToCheckout();
  };

  // Empty cart state
  if (!safeCart || safeCart.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center py-16">
          <ShoppingCart className="h-24 w-24 text-muted-foreground mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-foreground mb-3">Sepetiniz Boş</h2>
          <p className="text-muted-foreground mb-6">
            Henüz sepetinize ürün eklemediniz
          </p>
          <Button onClick={onBack} className="bg-primary hover:bg-primary-hover">
            Alışverişe Başla
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Button onClick={onBack} variant="outline" size="sm">
            ← Geri
          </Button>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Sepetim</h1>
        </div>
        {safeCart.length > 0 && (
          <Button 
            onClick={() => {
              clearCart();
              toast.success('Sepet temizlendi');
            }}
            variant="outline" 
            size="sm"
            className="text-destructive hover:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Sepeti Temizle
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {cart.map((item) => (
            <Card key={item._id} className="card-hover-lift">
              <CardContent className="p-4">
                <div className="flex gap-4">
                  {/* Product Image */}
                  <div className="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
                    {item.photo ? (
                      <img 
                        src={item.photo} 
                        alt={item.title} 
                        className="w-full h-full object-cover rounded-lg"
                      />
                    ) : (
                      <span className="text-3xl">🍽️</span>
                    )}
                  </div>

                  {/* Product Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-foreground mb-1 truncate">
                      {item.title}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-2">
                      {item.description || 'Lezzetli yemek'}
                    </p>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-primary">
                        ₺{item.price?.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Quantity Controls */}
                  <div className="flex flex-col items-end justify-between">
                    <Button
                      onClick={() => removeFromCart(item._id)}
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>

                    <div className="flex items-center gap-2 bg-secondary rounded-lg p-1">
                      <Button
                        onClick={() => handleQuantityChange(item._id, item.quantity - 1)}
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                      >
                        <Minus className="h-4 w-4" />
                      </Button>
                      <span className="font-semibold text-foreground w-8 text-center">
                        {item.quantity}
                      </span>
                      <Button
                        onClick={() => handleQuantityChange(item._id, item.quantity + 1)}
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>

                    <span className="text-sm font-semibold text-foreground">
                      ₺{(item.price * item.quantity).toFixed(2)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Coupon Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Tag className="h-5 w-5 text-primary" />
                İndirim Kuponu
              </CardTitle>
              <CardDescription>
                Kupon kodunuz varsa buradan kullanabilirsiniz
              </CardDescription>
            </CardHeader>
            <CardContent>
              {appliedCoupon ? (
                <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Tag className="h-4 w-4 text-green-600 dark:text-green-400" />
                    <div>
                      <p className="font-semibold text-green-700 dark:text-green-300">
                        {appliedCoupon.code}
                      </p>
                      <p className="text-sm text-green-600 dark:text-green-400">
                        {appliedCoupon.description}
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={removeCoupon}
                    variant="ghost"
                    size="sm"
                    className="text-green-600 hover:text-green-700"
                  >
                    Kaldır
                  </Button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Input
                    placeholder="Kupon kodu giriniz"
                    value={couponCode}
                    onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                    onKeyPress={(e) => e.key === 'Enter' && handleApplyCoupon()}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleApplyCoupon}
                    disabled={!couponCode}
                    className="bg-primary hover:bg-primary-hover"
                  >
                    Uygula
                  </Button>
                </div>
              )}
              
              {/* Demo coupon hints */}
              <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-blue-700 dark:text-blue-300">
                    <p className="font-semibold mb-1">Demo Kuponlar:</p>
                    <p>• <span className="font-mono">INDIRIM20</span> - %20 indirim</p>
                    <p>• <span className="font-mono">YENI10</span> - ₺10 indirim</p>
                    <p>• <span className="font-mono">TESLIMAT0</span> - Ücretsiz teslimat</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Order Summary */}
        <div className="lg:col-span-1">
          <Card className="sticky top-20 shadow-orange">
            <CardHeader>
              <CardTitle>Sipariş Özeti</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Summary Lines */}
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Ürün Toplamı:</span>
                  <span className="font-medium text-foreground">₺{subtotal.toFixed(2)}</span>
                </div>
                
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Teslimat Ücreti:</span>
                  <span className="font-medium text-foreground">₺{deliveryFee.toFixed(2)}</span>
                </div>

                {appliedCoupon && (
                  <div className="flex justify-between text-sm text-green-600 dark:text-green-400">
                    <span>İndirim ({appliedCoupon.code}):</span>
                    <span className="font-medium">-₺{appliedCoupon.amount.toFixed(2)}</span>
                  </div>
                )}

                <div className="border-t border-border pt-3">
                  <div className="flex justify-between">
                    <span className="font-bold text-lg text-foreground">Toplam:</span>
                    <span className="font-bold text-xl text-primary">
                      ₺{finalTotal.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Proceed Button */}
              <Button
                onClick={handleProceed}
                className="w-full bg-primary hover:bg-primary-hover text-primary-foreground font-semibold py-6 shadow-orange"
                size="lg"
              >
                Siparişi Tamamla
              </Button>

              {/* Info */}
              <p className="text-xs text-center text-muted-foreground">
                Siparişinizi onayladıktan sonra teslimat adresinizi ve ödeme yöntemini seçeceksiniz
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CartPageEnhanced;
