import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://admin-wsocket.preview.emergentagent.com/api';

export const OrderReport = () => {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    business_name: '',
    customer_name: '',
    status: '',
    start_date: '',
    end_date: ''
  });

  const fetchOrderReport = async () => {
    if (!filters.business_name && !filters.customer_name && !filters.status) {
      toast.error('Lütfen en az bir filtre girin (İşletme adı, Müşteri adı veya Durum)');
      return;
    }

    try {
      setLoading(true);
      const params = {};
      if (filters.business_name) params.business_name = filters.business_name;
      if (filters.customer_name) params.customer_name = filters.customer_name;
      if (filters.status) params.status = filters.status;
      if (filters.start_date) params.start_date = filters.start_date;
      if (filters.end_date) params.end_date = filters.end_date;

      const response = await axios.get(`${API_BASE}/admin/reports/orders`, {
        params,
        withCredentials: true
      });
      setReportData(response.data);
      
      if (response.data.orders.length === 0) {
        toast.info('Filtrelere uygun sipariş bulunamadı');
      } else {
        toast.success(`${response.data.orders.length} sipariş bulundu`);
      }
    } catch (error) {
      console.error('Order report fetch error:', error);
      toast.error('Sipariş raporu yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { label: 'Bekliyor', color: 'bg-yellow-100 text-yellow-800' },
      confirmed: { label: 'Onaylandı', color: 'bg-blue-100 text-blue-800' },
      preparing: { label: 'Hazırlanıyor', color: 'bg-purple-100 text-purple-800' },
      ready: { label: 'Hazır', color: 'bg-green-100 text-green-800' },
      picked_up: { label: 'Teslim Alındı', color: 'bg-indigo-100 text-indigo-800' },
      delivered: { label: 'Teslim Edildi', color: 'bg-green-100 text-green-800' },
      cancelled: { label: 'İptal', color: 'bg-red-100 text-red-800' }
    };
    
    const config = statusConfig[status] || { label: status, color: 'bg-gray-100 text-gray-800' };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Filter Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📦 Sipariş Raporu
          </CardTitle>
          <CardDescription>
            İşletme adı veya müşteri bilgisi ile siparişleri filtreleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            {/* Business Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                İşletme Adı
              </label>
              <input
                type="text"
                placeholder="Pizza, Burger, vb."
                value={filters.business_name}
                onChange={(e) => setFilters({ ...filters, business_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Customer Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Müşteri Adı/Soyadı
              </label>
              <input
                type="text"
                placeholder="Ahmet, Yılmaz, vb."
                value={filters.customer_name}
                onChange={(e) => setFilters({ ...filters, customer_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Durum
              </label>
              <select
                value={filters.status}
                onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Tümü</option>
                <option value="pending">Bekliyor</option>
                <option value="confirmed">Onaylandı</option>
                <option value="preparing">Hazırlanıyor</option>
                <option value="ready">Hazır</option>
                <option value="picked_up">Teslim Alındı</option>
                <option value="delivered">Teslim Edildi</option>
                <option value="cancelled">İptal</option>
              </select>
            </div>

            {/* Start Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Başlangıç Tarihi
              </label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bitiş Tarihi
              </label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Search Button */}
            <div className="flex items-end">
              <Button 
                onClick={fetchOrderReport}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loading ? '🔄 Yükleniyor...' : '🔍 Rapor Oluştur'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      {reportData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-blue-50">
            <CardContent className="p-6 text-center">
              <p className="text-blue-600 text-sm mb-2">Toplam Sipariş</p>
              <p className="text-3xl font-bold text-blue-800">
                {reportData.summary.total_orders}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-green-50">
            <CardContent className="p-6 text-center">
              <p className="text-green-600 text-sm mb-2">Toplam Gelir</p>
              <p className="text-3xl font-bold text-green-800">
                ₺{reportData.summary.total_revenue.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-purple-50">
            <CardContent className="p-6 text-center">
              <p className="text-purple-600 text-sm mb-2">Ortalama Sipariş</p>
              <p className="text-3xl font-bold text-purple-800">
                ₺{reportData.summary.average_order_value.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Orders Table */}
      {reportData && reportData.orders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sipariş Listesi ({reportData.orders.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Sipariş ID</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Tarih</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">İşletme</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Müşteri</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Kurye</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Tutar</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Durum</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Detay</th>
                  </tr>
                </thead>
                <tbody>
                  {reportData.orders.map((order) => (
                    <tr key={order.order_id} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-mono text-gray-600">
                        {order.order_id?.slice(0, 8)}...
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        {order.created_at ? new Date(order.created_at).toLocaleDateString('tr-TR') : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          <div className="font-medium text-gray-800">{order.business.name}</div>
                          <div className="text-gray-500 text-xs">{order.business.phone}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          <div className="font-medium text-gray-800">{order.customer.name}</div>
                          <div className="text-gray-500 text-xs">{order.customer.phone}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          <div className="font-medium text-gray-800">{order.courier.name}</div>
                          <div className="text-gray-500 text-xs">{order.courier.phone}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="text-sm">
                          <div className="font-medium text-gray-800">
                            ₺{order.total_amount.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                          </div>
                          <div className="text-gray-500 text-xs">
                            Teslimat: ₺{order.delivery_fee.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        {getStatusBadge(order.status)}
                      </td>
                      <td className="py-3 px-4">
                        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                          Görüntüle
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Results Message */}
      {reportData && reportData.orders.length === 0 && (
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="p-6 text-center">
            <div className="text-5xl mb-4">📭</div>
            <p className="text-gray-700 font-medium mb-2">Sipariş Bulunamadı</p>
            <p className="text-gray-600 text-sm">
              {reportData.message || 'Filtrelere uygun sipariş bulunamadı. Farklı filtreler deneyin.'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default OrderReport;
