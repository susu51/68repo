import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://ai-order-debug.preview.emergentagent.com/api';

export const CourierOrderHistory = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({ total_deliveries: 0, total_earnings: 0 });

  useEffect(() => {
    fetchOrderHistory();
  }, []);

  const fetchOrderHistory = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/courier/order-history`, {
        withCredentials: true
      });
      setOrders(response.data.orders || []);
      setSummary(response.data.summary || { total_deliveries: 0, total_earnings: 0 });
    } catch (error) {
      console.error('Order history fetch error:', error);
      toast.error('Sipariş geçmişi yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      delivered: { label: 'Teslim Edildi', color: 'bg-green-100 text-green-800' },
      completed: { label: 'Tamamlandı', color: 'bg-blue-100 text-blue-800' },
      cancelled: { label: 'İptal', color: 'bg-red-100 text-red-800' }
    };
    const config = statusConfig[status] || { label: status, color: 'bg-gray-100 text-gray-800' };
    return <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>{config.label}</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <p className="text-blue-100 text-sm mb-2">Toplam Teslimat</p>
            <p className="text-4xl font-bold">{summary.total_deliveries}</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <p className="text-green-100 text-sm mb-2">Toplam Kazanç</p>
            <p className="text-4xl font-bold">₺{summary.total_earnings.toFixed(2)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Orders List */}
      <Card>
        <CardHeader>
          <CardTitle>Sipariş Geçmişi ({orders.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.order_id} className="border-l-4 border-blue-500">
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="font-mono text-sm text-gray-500">#{order.order_id?.slice(0, 8)}...</p>
                      <p className="text-xs text-gray-500">
                        {order.created_at ? new Date(order.created_at).toLocaleString('tr-TR') : 'N/A'}
                      </p>
                    </div>
                    {getStatusBadge(order.status)}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">📦 İşletme</p>
                      <p className="font-medium">{order.business.name}</p>
                      <p className="text-xs text-gray-600">{order.business.address}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">👤 Müşteri</p>
                      <p className="font-medium">{order.customer.name}</p>
                      <p className="text-xs text-gray-600">
                        {order.customer.address?.street || 'Adres bilgisi yok'}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4 pt-3 border-t">
                    <div>
                      <p className="text-xs text-gray-500">Sipariş Tutarı</p>
                      <p className="font-bold text-gray-800">₺{order.total_amount.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Teslimat Ücreti</p>
                      <p className="font-bold text-gray-800">₺{order.delivery_fee.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Kazancınız</p>
                      <p className="font-bold text-green-600">₺{order.courier_earning.toFixed(2)}</p>
                    </div>
                  </div>

                  {order.items && order.items.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs text-gray-500 mb-2">Ürünler:</p>
                      <div className="space-y-1">
                        {order.items.map((item, idx) => (
                          <p key={idx} className="text-sm">
                            {item.quantity}x {item.name} - ₺{(item.price * item.quantity).toFixed(2)}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {orders.length === 0 && (
            <div className="text-center py-12">
              <p className="text-5xl mb-4">📦</p>
              <p className="text-gray-600">Henüz teslimat geçmişiniz yok</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CourierOrderHistory;