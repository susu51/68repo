import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { useCart } from '../../contexts/CartContext';
import { apiClient } from '../../utils/apiClient';
import { useAuth } from '../../contexts/AuthContext';

const PaymentPage = ({ selectedAddress: initialAddress, onBack, onPaymentSuccess, user }) => {
  const [selectedAddress, setSelectedAddress] = useState(initialAddress);
  const [userAddresses, setUserAddresses] = useState([]);
  const [showAddressSelector, setShowAddressSelector] = useState(false);
  const { cart, getCartSummary, clearCart } = useCart();
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('cash_on_delivery');
  const [processing, setProcessing] = useState(false);
  const [cardDetails, setCardDetails] = useState({
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    cardName: ''
  });

  const cartSummary = getCartSummary();

  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Load user addresses and set initial address
  useEffect(() => {
    loadUserAddresses();
    console.log('PaymentPage - Initial address:', initialAddress);
    if (initialAddress) {
      setSelectedAddress(initialAddress);
    }
  }, [initialAddress]);

  const loadUserAddresses = async () => {
    try {
      const token = localStorage.getItem('kuryecini_access_token');
      if (!token) return;

      const response = await fetch(`${API}/api/user/addresses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const addresses = await response.json();
        setUserAddresses(addresses || []);
        console.log('Loaded addresses:', addresses);
        
        // If no address selected but addresses available, select first one
        if (!selectedAddress && addresses.length > 0) {
          setSelectedAddress(addresses[0]);
          console.log('Auto-selected first address:', addresses[0]);
        }
      } else if (response.status === 401) {
        // Token expired or invalid
        console.log('Authentication failed in PaymentPage, token may be expired');
        toast.error('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
        localStorage.removeItem('kuryecini_access_token');
      } else {
        console.error('Error loading addresses:', response.status, response.statusText);
        toast.error('Adresler yüklenirken bir hata oluştu');
      }
    } catch (error) {
      console.error('Error loading addresses:', error);
    }
  };

  const paymentMethods = [
    {
      id: 'cash_on_delivery',
      name: 'Kapıda Nakit Ödeme',
      icon: '💵',
      description: 'Siparişinizi teslim alırken nakit olarak ödeyebilirsiniz'
    },
    {
      id: 'pos_on_delivery',
      name: 'Kapıda Kart ile Ödeme (POS)',
      icon: '💳',
      description: 'Kurye POS cihazı ile gelecek, kartınızla ödeme yapabilirsiniz'
    },
    {
      id: 'online',
      name: 'Online Kart ile Ödeme',
      icon: '🔒',
      description: 'Güvenli ödeme sistemi ile hemen ödeyebilirsiniz'
    }
  ];

  const handleCardInputChange = (field, value) => {
    setCardDetails(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const formatCardNumber = (value) => {
    // Remove all non-digits and add spaces every 4 digits
    const cleaned = value.replace(/\D/g, '');
    const formatted = cleaned.replace(/(.{4})/g, '$1 ').trim();
    return formatted.substring(0, 19); // Max 16 digits + 3 spaces
  };

  const formatExpiryDate = (value) => {
    // Format as MM/YY
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length >= 2) {
      return cleaned.substring(0, 2) + '/' + cleaned.substring(2, 4);
    }
    return cleaned;
  };

  const validateOnlinePayment = () => {
    if (!cardDetails.cardNumber || cardDetails.cardNumber.replace(/\s/g, '').length < 16) {
      toast.error('Geçerli bir kart numarası girin');
      return false;
    }
    if (!cardDetails.expiryDate || cardDetails.expiryDate.length < 5) {
      toast.error('Geçerli bir son kullanma tarihi girin');
      return false;
    }
    if (!cardDetails.cvv || cardDetails.cvv.length < 3) {
      toast.error('Geçerli bir CVV girin');
      return false;
    }
    if (!cardDetails.cardName.trim()) {
      toast.error('Kart üzerindeki ismi girin');
      return false;
    }
    return true;
  };

  const createOrder = async () => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const token = localStorage.getItem('kuryecini_access_token');

      const orderData = {
        delivery_address: selectedAddress.description,
        delivery_lat: selectedAddress.lat,
        delivery_lng: selectedAddress.lng,
        items: cart.items.map(item => ({
          product_id: item.id,
          product_name: item.name,
          product_price: item.price,
          quantity: item.quantity,
          subtotal: item.price * item.quantity
        })),
        total_amount: cartSummary.total,
        notes: `Ödeme yöntemi: ${paymentMethods.find(p => p.id === selectedPaymentMethod)?.name}`
      };

      const response = await fetch(`${BACKEND_URL}/api/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(orderData)
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Order creation failed: ${error}`);
      }

      const order = await response.json();
      return order;

    } catch (error) {
      console.error('Order creation error:', error);
      throw error;
    }
  };

  const processPayment = async (orderId) => {
    try {
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const token = localStorage.getItem('kuryecini_access_token');

      const paymentData = {
        order_id: orderId,
        payment_method: selectedPaymentMethod,
        amount: cartSummary.total,
        card_details: selectedPaymentMethod === 'online' ? cardDetails : null
      };

      const response = await fetch(`${BACKEND_URL}/api/payments/mock`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(paymentData)
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Payment processing failed: ${error}`);
      }

      const paymentResult = await response.json();
      return paymentResult;

    } catch (error) {
      console.error('Payment processing error:', error);
      throw error;
    }
  };

  const handleCompleteOrder = async () => {
    // Validation
    if (!selectedAddress) {
      toast.error('Teslimat adresi seçilmedi');
      setShowAddressSelector(true);
      return;
    }

    if (cart.items.length === 0) {
      toast.error('Sepetiniz boş');
      return;
    }

    if (selectedPaymentMethod === 'online' && !validateOnlinePayment()) {
      return;
    }

    setProcessing(true);

    try {
      // 1. Create order
      toast.loading('Sipariş oluşturuluyor...', { id: 'order-process' });
      const order = await createOrder();

      // 2. Process payment
      toast.loading('Ödeme işleniyor...', { id: 'order-process' });
      const paymentResult = await processPayment(order.id);

      // 3. Handle payment result
      if (paymentResult.status === 'success') {
        toast.success(paymentResult.message, { id: 'order-process' });
        
        // Clear cart
        clearCart();
        
        // Call success callback
        if (onPaymentSuccess) {
          onPaymentSuccess({
            order,
            paymentResult
          });
        }
      } else {
        toast.error(paymentResult.message, { id: 'order-process' });
      }

    } catch (error) {
      toast.error('Sipariş oluşturulurken bir hata oluştu', { id: 'order-process' });
      console.error('Order completion error:', error);
    } finally {
      setProcessing(false);
    }
  };

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
          <h1 className="text-xl font-bold text-gray-900">Ödeme</h1>
        </div>

        {/* Order Summary */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <h2 className="font-semibold text-gray-900 mb-3">Sipariş Özeti</h2>
          
          {/* Restaurant */}
          {cart.restaurant && (
            <div className="flex items-center mb-3">
              <span className="text-2xl mr-3">🏪</span>
              <div>
                <p className="font-medium">{cart.restaurant.name}</p>
                <p className="text-sm text-gray-600">{cart.items.length} ürün</p>
              </div>
            </div>
          )}

          {/* Address */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <span className="text-2xl mr-3">📍</span>
              <div>
                <p className="font-medium">Teslimat Adresi</p>
                <p className="text-sm text-gray-600">
                  {selectedAddress?.description || 'Adres seçilmedi'}
                </p>
              </div>
            </div>
            <button 
              onClick={() => setShowAddressSelector(true)}
              className="text-blue-500 hover:text-blue-600 text-sm font-medium"
            >
              {selectedAddress ? 'Değiştir' : 'Seç'}
            </button>
          </div>

          {/* Price Breakdown */}
          <div className="border-t pt-3">
            <div className="flex justify-between mb-1">
              <span>Ara Toplam</span>
              <span>₺{cartSummary.subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between mb-1">
              <span>Teslimat Ücreti</span>
              <span>₺{cartSummary.deliveryFee.toFixed(2)}</span>
            </div>
            <div className="flex justify-between mb-3">
              <span>Servis Ücreti</span>
              <span>₺{cartSummary.serviceFee.toFixed(2)}</span>
            </div>
            <div className="flex justify-between font-bold text-lg border-t pt-2">
              <span>Toplam</span>
              <span>₺{cartSummary.total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Payment Methods */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">Ödeme Yöntemi</h2>
          
          <div className="space-y-3">
            {paymentMethods.map((method) => (
              <div 
                key={method.id}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedPaymentMethod === method.id 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
                onClick={() => setSelectedPaymentMethod(method.id)}
              >
                <div className="flex items-center">
                  <span className="text-2xl mr-3">{method.icon}</span>
                  <div className="flex-1">
                    <p className="font-medium">{method.name}</p>
                    <p className="text-sm text-gray-600">{method.description}</p>
                  </div>
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    selectedPaymentMethod === method.id 
                      ? 'border-blue-500 bg-blue-500' 
                      : 'border-gray-300'
                  }`}>
                    {selectedPaymentMethod === method.id && (
                      <div className="w-full h-full bg-white rounded-full scale-50"></div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Online Payment Card Details */}
        {selectedPaymentMethod === 'online' && (
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Kart Bilgileri</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kart Numarası
                </label>
                <input
                  type="text"
                  placeholder="1234 5678 9012 3456"
                  value={cardDetails.cardNumber}
                  onChange={(e) => handleCardInputChange('cardNumber', formatCardNumber(e.target.value))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Son Kullanma
                  </label>
                  <input
                    type="text"
                    placeholder="MM/YY"
                    value={cardDetails.expiryDate}
                    onChange={(e) => handleCardInputChange('expiryDate', formatExpiryDate(e.target.value))}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    CVV
                  </label>
                  <input
                    type="text"
                    placeholder="123"
                    maxLength={3}
                    value={cardDetails.cvv}
                    onChange={(e) => handleCardInputChange('cvv', e.target.value.replace(/\D/g, ''))}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Kart Üzerindeki İsim
                </label>
                <input
                  type="text"
                  placeholder="AHMET YILMAZ"
                  value={cardDetails.cardName}
                  onChange={(e) => handleCardInputChange('cardName', e.target.value.toUpperCase())}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        )}

        {/* Address Selector Modal */}
        {showAddressSelector && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg max-w-md w-full max-h-96 overflow-y-auto">
              <div className="p-4 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-gray-900">Teslimat Adresi Seç</h3>
                  <button 
                    onClick={() => setShowAddressSelector(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div className="p-4">
                {userAddresses.length === 0 ? (
                  <div className="text-center py-8">
                    <span className="text-4xl mb-2 block">📍</span>
                    <p className="text-gray-600 mb-4">Henüz kayıtlı adresiniz yok</p>
                    <p className="text-sm text-gray-500">Sepet sayfasına geri dönüp adres ekleyin</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {userAddresses.map((address) => (
                      <div 
                        key={address.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedAddress?.id === address.id 
                            ? 'border-blue-500 bg-blue-50' 
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                        onClick={() => {
                          setSelectedAddress(address);
                          setShowAddressSelector(false);
                          toast.success('Teslimat adresi seçildi');
                        }}
                      >
                        <p className="font-medium text-gray-900">{address.title}</p>
                        <p className="text-sm text-gray-600">{address.description}</p>
                        {address.city && (
                          <p className="text-xs text-gray-500 mt-1">🏙️ {address.city}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Complete Order Button */}
        <button
          onClick={handleCompleteOrder}
          disabled={processing || !selectedAddress}
          className="w-full bg-blue-500 text-white py-4 rounded-lg font-semibold hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {processing ? 'İşleniyor...' : !selectedAddress ? 'Önce Adres Seçin' : `₺${cartSummary.total.toFixed(2)} - Siparişi Tamamla`}
        </button>

        {/* Security Note */}
        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            🔒 Ödeme bilgileriniz güvenli şekilde şifrelenmektedir
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaymentPage;