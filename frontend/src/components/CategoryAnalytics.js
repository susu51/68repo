import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://order-system-44.preview.emergentagent.com/api';

export const CategoryAnalytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState({
    start_date: new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/admin/reports/category-analytics`, {
        params: dateRange,
        withCredentials: true
      });
      setAnalyticsData(response.data);
    } catch (error) {
      console.error('Category analytics fetch error:', error);
      toast.error('Kategori analizi yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      'yemek': '🍽️',
      'food': '🍽️',
      'içecek': '🥤',
      'drink': '🥤',
      'beverage': '🥤',
      'atıştırmalık': '🍿',
      'snack': '🍿',
      'tatlı': '🍰',
      'dessert': '🍰'
    };
    return icons[category?.toLowerCase()] || '📦';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Analiz yükleniyor...</p>
        </div>
      </div>
    );
  }

  const categories = analyticsData?.categories || [];
  const summary = analyticsData?.summary || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            📊 Kategori Analizi
          </CardTitle>
          <CardDescription>
            En çok satış yapan ürün kategorilerini görüntüleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Başlangıç Tarihi
              </label>
              <input
                type="date"
                value={dateRange.start_date}
                onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bitiş Tarihi
              </label>
              <input
                type="date"
                value={dateRange.end_date}
                onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <Button 
                onClick={fetchAnalytics}
                className="w-full bg-indigo-600 hover:bg-indigo-700"
              >
                📊 Analiz Oluştur
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Top Category Card */}
      {summary.top_category && (
        <Card className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
          <CardContent className="p-8">
            <div className="text-center">
              <div className="text-6xl mb-4">{getCategoryIcon(summary.top_category)}</div>
              <p className="text-indigo-100 text-lg mb-2">En Çok Satan Kategori</p>
              <p className="text-4xl font-bold mb-4 capitalize">{summary.top_category}</p>
              <p className="text-2xl font-semibold">
                ₺{summary.top_category_revenue.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Cards */}
      {categories.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="text-4xl">{getCategoryIcon(category.category)}</div>
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm font-medium rounded-full">
                    #{index + 1}
                  </span>
                </div>
                
                <h3 className="text-xl font-bold text-gray-800 mb-4 capitalize">
                  {category.category}
                </h3>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Satış</span>
                    <span className="font-bold text-gray-800">
                      ₺{category.revenue.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Miktar</span>
                    <span className="font-medium text-gray-700">{category.quantity} adet</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600 text-sm">Sipariş</span>
                    <span className="font-medium text-gray-700">{category.order_count}</span>
                  </div>
                  
                  {/* Percentage Bar */}
                  <div>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Toplam Satış İçindeki Payı</span>
                      <span>{category.percentage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full transition-all"
                        style={{ width: `${category.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      {categories.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Özet İstatistikler</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-600 text-sm mb-2">Toplam Gelir</p>
                <p className="text-3xl font-bold text-gray-800">
                  ₺{summary.total_revenue.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                </p>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-600 text-sm mb-2">Kategori Sayısı</p>
                <p className="text-3xl font-bold text-gray-800">{summary.total_categories}</p>
              </div>
              
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-600 text-sm mb-2">Ortalama/Kategori</p>
                <p className="text-3xl font-bold text-gray-800">
                  ₺{(summary.total_revenue / summary.total_categories).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Data */}
      {categories.length === 0 && (
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="p-6 text-center">
            <div className="text-5xl mb-4">📊</div>
            <p className="text-gray-700 font-medium mb-2">Henüz Kategori Verisi Yok</p>
            <p className="text-gray-600 text-sm">
              Sipariş oluşturuldukça kategori analizleri burada görünecektir.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CategoryAnalytics;
