import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://ai-order-debug.preview.emergentagent.com/api';

export const UserReport = () => {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchUserReport = async () => {
    if (!searchTerm.trim()) {
      toast.error('Lütfen müşteri adı, soyadı veya email girin');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/admin/reports/user`, {
        params: { customer_name: searchTerm },
        withCredentials: true
      });
      setReportData(response.data);
      
      if (response.data.customers_found === 0) {
        toast.info('Müşteri bulunamadı');
      } else {
        toast.success(`${response.data.customers_found} müşteri bulundu`);
      }
    } catch (error) {
      console.error('User report fetch error:', error);
      toast.error('Kullanıcı raporu yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            👤 Kullanıcı Raporu
          </CardTitle>
          <CardDescription>
            Müşteri adı, soyadı veya email ile arama yapın ve detaylı analiz görün
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Müşteri adı, soyadı veya email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && fetchUserReport()}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
            />
            <Button 
              onClick={fetchUserReport}
              disabled={loading}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {loading ? '🔄 Arıyor...' : '🔍 Ara'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Customer Cards */}
      {reportData && reportData.customers.map((customerData, index) => (
        <Card key={index} className="border-l-4 border-purple-500">
          <CardContent className="p-6">
            {/* Customer Info Header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-2">
                  {customerData.customer.name}
                </h3>
                <div className="space-y-1 text-sm text-gray-600">
                  <p>📧 {customerData.customer.email}</p>
                  <p>📱 {customerData.customer.phone}</p>
                  <p>📅 Kayıt: {customerData.customer.created_at ? new Date(customerData.customer.created_at).toLocaleDateString('tr-TR') : 'N/A'}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-4xl mb-2">🎯</div>
                <span className="px-3 py-1 bg-purple-100 text-purple-800 text-sm font-medium rounded-full">
                  Müşteri
                </span>
              </div>
            </div>

            {/* Analytics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {/* Total Orders */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-blue-600 text-sm mb-1">Toplam Sipariş</p>
                <p className="text-3xl font-bold text-blue-800">
                  {customerData.analytics.total_orders}
                </p>
              </div>

              {/* Total Spent */}
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-green-600 text-sm mb-1">Toplam Harcama</p>
                <p className="text-3xl font-bold text-green-800">
                  ₺{customerData.analytics.total_spent.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                </p>
              </div>

              {/* Average Order Value */}
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-orange-600 text-sm mb-1">Ortalama Sipariş</p>
                <p className="text-3xl font-bold text-orange-800">
                  ₺{customerData.analytics.average_order_value.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>

            {/* Status Distribution */}
            {Object.keys(customerData.analytics.status_distribution || {}).length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-700 mb-3">Sipariş Durumu Dağılımı</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(customerData.analytics.status_distribution).map(([status, count]) => (
                    <div key={status} className="bg-gray-50 p-3 rounded-lg text-center">
                      <p className="text-2xl font-bold text-gray-800">{count}</p>
                      <p className="text-xs text-gray-600 capitalize">{status}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Favorite Businesses */}
            {customerData.analytics.favorite_businesses.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-700 mb-3">En Çok Sipariş Verdiği İşletmeler</h4>
                <div className="space-y-2">
                  {customerData.analytics.favorite_businesses.map((business, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">🏪</span>
                        <span className="font-medium text-gray-800">{business.name}</span>
                      </div>
                      <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                        {business.order_count} sipariş
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Last Order */}
            {customerData.analytics.last_order_date && (
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Son Sipariş</p>
                <p className="text-lg font-medium text-gray-800">
                  {new Date(customerData.analytics.last_order_date).toLocaleDateString('tr-TR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}

      {/* No Results */}
      {reportData && reportData.customers_found === 0 && (
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="p-6 text-center">
            <div className="text-5xl mb-4">🔍</div>
            <p className="text-gray-700 font-medium mb-2">Müşteri Bulunamadı</p>
            <p className="text-gray-600 text-sm">
              "{reportData.search_term}" için sonuç bulunamadı. Farklı bir arama terimi deneyin.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UserReport;
