import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import { apiClient } from '../../utils/apiClient';
import { useAuth } from '../../contexts/AuthContext';

const OrdersPage = ({ user, onOrderSelect, onTabChange }) => {
  const { isAuthenticated } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewTarget, setReviewTarget] = useState(null); // 'business' | 'courier'
  const [reviewData, setReviewData] = useState({
    rating: 5,
    comment: ''
  });

  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('kuryecini_access_token');
      
      if (!token) {
        // Show mock data if not authenticated with safe properties
        const safeOrders = mockOrders.map(order => ({
          ...order,
          total: order.total || 0,
          items: order.items || []
        }));
        setOrders(safeOrders);
        setLoading(false);
        return;
      }

      const response = await axios.get(`${API}/api/orders/my`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Ensure all required properties exist and handle item objects
      const ordersData = (response.data || []).map(order => ({
        ...order,
        total: order.total || 0,
        items: (order.items || []).map(item => 
          typeof item === 'string' ? item : (item.product_name || item.name || 'Ürün')
        ),
        status: order.status || 'unknown',
        paymentMethod: order.paymentMethod || order.payment_method || 'unknown'
      }));
      setOrders(ordersData);
    } catch (error) {
      console.error('Error loading orders:', error);
      // Fallback to mock data with safe properties
      const safeOrders = mockOrders.map(order => ({
        ...order,
        total: order.total || 0,
        items: order.items || []
      }));
      setOrders(safeOrders);
    } finally {
      setLoading(false);
    }
  };

  const handleReviewSubmit = async () => {
    if (!selectedOrder || !reviewTarget) return;

    try {
      const token = localStorage.getItem('kuryecini_access_token');
      if (!token) {
        toast.success('Değerlendirmeniz kaydedildi!');
        setShowReviewModal(false);
        return;
      }

      await axios.post(`${API}/api/reviews`, {
        orderId: selectedOrder.id,
        targetType: reviewTarget,
        targetId: reviewTarget === 'business' ? selectedOrder.businessId : selectedOrder.courierId,
        rating: reviewData.rating,
        comment: reviewData.comment
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      toast.success('Değerlendirmeniz kaydedildi!');
      setShowReviewModal(false);
      setReviewData({ rating: 5, comment: '' });
      
      // Update order to mark as reviewed
      setOrders(orders.map(order => 
        order.id === selectedOrder.id 
          ? { ...order, reviewed: true }
          : order
      ));
    } catch (error) {
      console.error('Error submitting review:', error);
      toast.error('Değerlendirme gönderilirken hata oluştu');
    }
  };

  const openReviewModal = (order, target) => {
    setSelectedOrder(order);
    setReviewTarget(target);
    setShowReviewModal(true);
    setReviewData({ rating: 5, comment: '' });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'DELIVERED': return 'text-green-600 bg-green-50';
      case 'PICKED_UP': return 'text-blue-600 bg-blue-50';
      case 'READY': return 'text-orange-600 bg-orange-50';
      case 'CONFIRMED': return 'text-purple-600 bg-purple-50';
      case 'PLACED': return 'text-gray-600 bg-gray-50';
      case 'CANCELLED': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'DELIVERED': return 'Teslim Edildi';
      case 'PICKED_UP': return 'Kurye Aldı';
      case 'READY': return 'Hazırlandı';
      case 'CONFIRMED': return 'Onaylandı';
      case 'PLACED': return 'Sipariş Alındı';
      case 'CANCELLED': return 'İptal Edildi';
      default: return status;
    }
  };

  const mockOrders = [
    {
      id: 'order-1',
      businessName: 'Pizza Palace',
      businessId: 'business-1',
      courierId: 'courier-1',
      courierName: 'Ahmet K.',
      status: 'DELIVERED',
      orderDate: '2024-01-15T14:30:00',
      items: ['Margherita Pizza', 'Coca Cola'],
      total: 89.50,
      paymentMethod: 'cod',
      reviewed: false
    },
    {
      id: 'order-2',
      businessName: 'Burger Deluxe',
      businessId: 'business-2',
      courierId: 'courier-2',
      courierName: 'Mehmet Y.',
      status: 'PICKED_UP',
      orderDate: '2024-01-15T16:45:00',
      items: ['Cheeseburger', 'Patates Kızartması'],
      total: 67.00,
      paymentMethod: 'online',
      reviewed: false
    },
    {
      id: 'order-3',
      businessName: 'Test Restoranı',
      businessId: 'business-3',
      courierId: 'courier-3',
      courierName: 'Ali S.',
      status: 'DELIVERED',
      orderDate: '2024-01-14T19:20:00',
      items: ['Döner Kebap', 'Ayran'],
      total: 45.50,
      paymentMethod: 'cod',
      reviewed: true
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Siparişler yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm sticky top-0 z-40">
        <div className="p-4">
          <h1 className="text-xl font-bold text-gray-800">Siparişlerim</h1>
          <p className="text-sm text-gray-600">{orders.length} sipariş</p>
        </div>
      </div>

      <div className="p-4">
        {orders.length === 0 ? (
          <div className="text-center py-16">
            <span className="text-6xl mb-4 block">📦</span>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">
              Henüz siparişiniz yok
            </h2>
            <p className="text-gray-600 mb-6">
              İlk siparişinizi verin ve lezzetli yemeklerin tadını çıkarın
            </p>
            <Button className="bg-orange-500 hover:bg-orange-600 text-white px-8 py-3">
              Sipariş Ver
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map(order => (
              <Card key={order.id} className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow" onClick={() => onOrderSelect && onOrderSelect(order.id)}>
                <CardContent className="p-0">
                  {/* Order Header */}
                  <div className="p-4 bg-gray-50 border-b">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-gray-800">
                          {order.businessName}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {new Date(order.orderDate).toLocaleDateString('tr-TR', {
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                          {getStatusText(order.status)}
                        </div>
                        <p className="text-lg font-bold text-gray-800 mt-1">
                          ₺{(order.total || 0).toFixed(2)}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Order Items */}
                  <div className="p-4">
                    <div className="space-y-2">
                      {order.items.map((item, index) => (
                        <div key={index} className="flex items-center">
                          <span className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-xs mr-3">
                            {index + 1}
                          </span>
                          <span className="text-gray-700">
                            {typeof item === 'string' ? item : (item.product_name || item.name || 'Ürün')}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Payment Method */}
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Ödeme:</span>
                        <span className="font-medium">
                          {order.paymentMethod === 'cod' ? '💵 Kapıda Ödeme' : '💳 Online Ödeme'}
                        </span>
                      </div>
                      {order.courierName && (
                        <div className="flex items-center justify-between text-sm mt-1">
                          <span className="text-gray-600">Kurye:</span>
                          <span className="font-medium">🚴‍♂️ {order.courierName}</span>
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    {order.status === 'DELIVERED' && !order.reviewed && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <p className="text-sm text-gray-600 mb-3">
                          Siparişiniz teslim edildi. Değerlendirme yapmak ister misiniz?
                        </p>
                        <div className="flex space-x-2">
                          <Button
                            onClick={() => openReviewModal(order, 'business')}
                            variant="outline"
                            size="sm"
                            className="flex-1"
                          >
                            🏪 Restoranı Değerlendir
                          </Button>
                          <Button
                            onClick={() => openReviewModal(order, 'courier')}
                            variant="outline"
                            size="sm"
                            className="flex-1"
                          >
                            🚴‍♂️ Kuryeyi Değerlendir
                          </Button>
                        </div>
                      </div>
                    )}

                    {order.status === 'PICKED_UP' && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                          <div className="flex items-center">
                            <span className="text-blue-600 mr-2">🚴‍♂️</span>
                            <div>
                              <p className="text-blue-800 font-medium">Siparişiniz yolda!</p>
                              <p className="text-blue-600 text-sm">
                                Kurye {order.courierName} siparişinizi size getiriyor
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {order.reviewed && (
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <p className="text-green-600 text-sm">
                          ✅ Değerlendirmeniz alındı. Teşekkürler!
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Review Modal */}
      {showReviewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md">
            <div className="p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                {reviewTarget === 'business' ? '🏪 Restoranı Değerlendir' : '🚴‍♂️ Kuryeyi Değerlendir'}
              </h3>
              
              <div className="space-y-4">
                {/* Rating Stars */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Puanınız (1-5 yıldız)
                  </label>
                  <div className="flex space-x-1">
                    {[1, 2, 3, 4, 5].map(star => (
                      <button
                        key={star}
                        onClick={() => setReviewData({...reviewData, rating: star})}
                        className={`text-2xl ${
                          star <= reviewData.rating ? 'text-yellow-400' : 'text-gray-300'
                        }`}
                      >
                        ⭐
                      </button>
                    ))}
                  </div>
                </div>

                {/* Comment */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Yorumunuz (İsteğe bağlı)
                  </label>
                  <textarea
                    value={reviewData.comment}
                    onChange={(e) => setReviewData({...reviewData, comment: e.target.value})}
                    placeholder="Deneyiminizi paylaşın..."
                    maxLength={200}
                    rows={4}
                    className="w-full border border-gray-300 rounded-lg p-3 text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {reviewData.comment.length}/200 karakter
                  </p>
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <Button
                  onClick={() => setShowReviewModal(false)}
                  variant="outline"
                  className="flex-1"
                >
                  İptal
                </Button>
                <Button
                  onClick={handleReviewSubmit}
                  className="flex-1 bg-orange-500 hover:bg-orange-600 text-white"
                >
                  Gönder
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrdersPage;