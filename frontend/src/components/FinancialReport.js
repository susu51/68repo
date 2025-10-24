import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL + '/api';

export const FinancialReport = () => {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState({
    start_date: new Date(new Date().setMonth(new Date().getMonth() - 1)).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchFinancialReport();
  }, []);

  const fetchFinancialReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/admin/reports/financial`, {
        params: dateRange,
        withCredentials: true
      });
      setReportData(response.data);
    } catch (error) {
      console.error('Financial report fetch error:', error);
      toast.error('Finansal rapor yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = () => {
    fetchFinancialReport();
  };

  // Calculate Kuryecini earnings from summary
  const calculateKuryeciniEarnings = () => {
    if (!reportData || !reportData.summary) return 0;
    
    const { summary } = reportData;
    
    // Kuryecini kazancı = Platform komisyonu + Teslimat ücreti
    const platformCommission = summary.platform_commission || 0;
    const deliveryFees = summary.total_delivery_fees || 0;
    
    return platformCommission + deliveryFees;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Rapor yükleniyor...</p>
        </div>
      </div>
    );
  }

  const kuryeciniEarnings = calculateKuryeciniEarnings();
  const summary = reportData?.summary || {};

  return (
    <div className="space-y-6">
      {/* Header with Date Range Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            💰 Finansal Rapor - Kuryecini Kazancı
          </CardTitle>
          <CardDescription>
            Platform toplam kazancını ve gelir dağılımını görüntüleyin
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div>
              <Button 
                onClick={handleGenerateReport}
                className="w-full bg-green-600 hover:bg-green-700"
              >
                📊 Rapor Oluştur
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Earnings Card */}
      <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
        <CardContent className="p-8">
          <div className="text-center">
            <p className="text-green-100 text-lg mb-2">Kuryecini Toplam Kazancı</p>
            <p className="text-5xl font-bold mb-4">
              ₺{kuryeciniEarnings.toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
            </p>
            <p className="text-green-100 text-sm">
              {dateRange.start_date} - {dateRange.end_date}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Revenue Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Platform Commission */}
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">💼</div>
              <p className="text-gray-600 text-sm mb-2">Platform Komisyonu</p>
              <p className="text-2xl font-bold text-gray-800">
                ₺{(summary.platform_commission || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                İşletme siparişlerinden %{summary.commission_rate || 5}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Delivery Fees */}
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">🏍️</div>
              <p className="text-gray-600 text-sm mb-2">Teslimat Ücretleri</p>
              <p className="text-2xl font-bold text-gray-800">
                ₺{(summary.total_delivery_fees || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Müşterilerden alınan teslimat ücreti
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Total Orders Revenue */}
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">📦</div>
              <p className="text-gray-600 text-sm mb-2">Toplam Sipariş Tutarı</p>
              <p className="text-2xl font-bold text-gray-800">
                ₺{(summary.total_order_amount || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {summary.total_orders || 0} sipariş
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Business Revenue */}
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">🏪</div>
              <p className="text-gray-600 text-sm mb-2">İşletme Gelirleri</p>
              <p className="text-2xl font-bold text-gray-800">
                ₺{(summary.business_revenue || 0).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Komisyon sonrası işletme payı
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Pie Chart (Simple Visual) */}
      <Card>
        <CardHeader>
          <CardTitle>Gelir Dağılımı</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Platform Commission Bar */}
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Platform Komisyonu</span>
                <span className="text-sm text-gray-600">
                  {summary.total_order_amount > 0 
                    ? ((summary.platform_commission / summary.total_order_amount) * 100).toFixed(1) 
                    : 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-green-600 h-3 rounded-full transition-all"
                  style={{ 
                    width: summary.total_order_amount > 0 
                      ? `${(summary.platform_commission / summary.total_order_amount) * 100}%`
                      : '0%'
                  }}
                ></div>
              </div>
            </div>

            {/* Delivery Fees Bar */}
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Teslimat Ücretleri</span>
                <span className="text-sm text-gray-600">
                  {summary.total_order_amount > 0 
                    ? ((summary.total_delivery_fees / summary.total_order_amount) * 100).toFixed(1)
                    : 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-blue-600 h-3 rounded-full transition-all"
                  style={{ 
                    width: summary.total_order_amount > 0 
                      ? `${(summary.total_delivery_fees / summary.total_order_amount) * 100}%`
                      : '0%'
                  }}
                ></div>
              </div>
            </div>

            {/* Business Revenue Bar */}
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">İşletme Payı</span>
                <span className="text-sm text-gray-600">
                  {summary.total_order_amount > 0 
                    ? ((summary.business_revenue / summary.total_order_amount) * 100).toFixed(1)
                    : 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-purple-600 h-3 rounded-full transition-all"
                  style={{ 
                    width: summary.total_order_amount > 0 
                      ? `${(summary.business_revenue / summary.total_order_amount) * 100}%`
                      : '0%'
                  }}
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-gray-600 text-sm mb-2">Ortalama Sipariş Değeri</p>
            <p className="text-3xl font-bold text-gray-800">
              ₺{summary.total_orders > 0 
                ? (summary.total_order_amount / summary.total_orders).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
                : '0.00'
              }
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-gray-600 text-sm mb-2">Ortalama Komisyon/Sipariş</p>
            <p className="text-3xl font-bold text-gray-800">
              ₺{summary.total_orders > 0 
                ? (summary.platform_commission / summary.total_orders).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
                : '0.00'
              }
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-gray-600 text-sm mb-2">Ortalama Teslimat Ücreti</p>
            <p className="text-3xl font-bold text-gray-800">
              ₺{summary.total_orders > 0 
                ? (summary.total_delivery_fees / summary.total_orders).toLocaleString('tr-TR', { minimumFractionDigits: 2 })
                : '0.00'
              }
            </p>
          </CardContent>
        </Card>
      </div>

      {/* No Data Message */}
      {!reportData || !reportData.summary || Object.keys(reportData.summary).length === 0 ? (
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="p-6 text-center">
            <div className="text-5xl mb-4">📊</div>
            <p className="text-gray-700 font-medium mb-2">Henüz Finansal Veri Yok</p>
            <p className="text-gray-600 text-sm">
              Sipariş oluşturuldukça finansal veriler burada görünecektir.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
};

export default FinancialReport;
