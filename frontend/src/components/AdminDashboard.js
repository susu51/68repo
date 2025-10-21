import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://courier-connect-14.preview.emergentagent.com/api';

export const AdminDashboardTab = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/admin/reports/dashboard`, {
        withCredentials: true
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
      toast.error('Dashboard verileri yüklenemedi');
    } finally {
      setLoading(false);
    }
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

  if (!dashboardData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">Dashboard verileri yüklenemedi</p>
      </div>
    );
  }

  const { orders, revenue, users } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Orders */}
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm font-medium">Toplam Sipariş</p>
                <p className="text-3xl font-bold mt-2">{orders.total}</p>
                <p className="text-blue-100 text-xs mt-1">
                  Bu hafta: {orders.this_week}
                </p>
              </div>
              <div className="text-5xl opacity-20">📦</div>
            </div>
          </CardContent>
        </Card>

        {/* Total Revenue */}
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm font-medium">Toplam Gelir</p>
                <p className="text-3xl font-bold mt-2">
                  ₺{revenue.total.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                </p>
                <p className="text-green-100 text-xs mt-1">
                  Bu hafta: ₺{revenue.weekly.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="text-5xl opacity-20">💰</div>
            </div>
          </CardContent>
        </Card>

        {/* Total Users */}
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm font-medium">Toplam Kullanıcı</p>
                <p className="text-3xl font-bold mt-2">
                  {users.total_customers + users.total_businesses + users.total_couriers}
                </p>
                <p className="text-purple-100 text-xs mt-1">
                  Müşteri: {users.total_customers} | İşletme: {users.total_businesses} | Kurye: {users.total_couriers}
                </p>
              </div>
              <div className="text-5xl opacity-20">👥</div>
            </div>
          </CardContent>
        </Card>

        {/* Active Couriers */}
        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100 text-sm font-medium">Aktif Kuryeler</p>
                <p className="text-3xl font-bold mt-2">{users.active_couriers}</p>
                <p className="text-orange-100 text-xs mt-1">
                  Onaylı işletme: {users.active_businesses}
                </p>
              </div>
              <div className="text-5xl opacity-20">🏍️</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Order Status Distribution */}
      {Object.keys(orders.status_distribution || {}).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sipariş Durumu Dağılımı</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(orders.status_distribution).map(([status, count]) => (
                <div key={status} className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-800">{count}</p>
                  <p className="text-sm text-gray-600 capitalize">{status}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Hızlı Erişim</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button className="p-4 text-center bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors">
              <div className="text-3xl mb-2">📊</div>
              <p className="text-sm font-medium text-gray-700">Raporlar</p>
            </button>
            <button className="p-4 text-center bg-green-50 hover:bg-green-100 rounded-lg transition-colors">
              <div className="text-3xl mb-2">⚙️</div>
              <p className="text-sm font-medium text-gray-700">Ayarlar</p>
            </button>
            <button className="p-4 text-center bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors">
              <div className="text-3xl mb-2">🎁</div>
              <p className="text-sm font-medium text-gray-700">Promosyonlar</p>
            </button>
            <button className="p-4 text-center bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors">
              <div className="text-3xl mb-2">💬</div>
              <p className="text-sm font-medium text-gray-700">Mesajlar</p>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Average Order Value */}
      {revenue.average_order_value > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Ortalama Sipariş Değeri</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-6">
              <p className="text-4xl font-bold text-gray-800">
                ₺{revenue.average_order_value.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-gray-600 mt-2">Sipariş başına ortalama gelir</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AdminDashboardTab;
