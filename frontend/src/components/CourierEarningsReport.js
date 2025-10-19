import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-ai-tools.preview.emergentagent.com/api';

export const CourierEarningsReport = () => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState('daily');

  useEffect(() => {
    fetchReport();
  }, [period]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/courier/earnings-report`, {
        params: { period },
        withCredentials: true
      });
      setReport(response.data);
    } catch (error) {
      console.error('Earnings report fetch error:', error);
      toast.error('Kazanç raporu yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = () => {
    if (!report) return;
    
    const printContent = `
      <html>
        <head>
          <title>Kazanç Raporu</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            h1 { color: #2563eb; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #2563eb; color: white; }
            .summary { background-color: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0; }
          </style>
        </head>
        <body>
          <h1>🏍️ Kurye Kazanç Raporu</h1>
          <p><strong>Dönem:</strong> ${report.period === 'daily' ? 'Günlük' : report.period === 'weekly' ? 'Haftalık' : 'Aylık'}</p>
          <p><strong>Tarih Aralığı:</strong> ${new Date(report.start_date).toLocaleDateString('tr-TR')} - ${new Date(report.end_date).toLocaleDateString('tr-TR')}</p>
          
          <div class="summary">
            <h2>Özet</h2>
            <p><strong>Toplam Teslimat:</strong> ${report.summary.total_deliveries}</p>
            <p><strong>Toplam Kazanç:</strong> ₺${report.summary.total_earnings.toFixed(2)}</p>
            <p><strong>Ortalama/Teslimat:</strong> ₺${report.summary.average_per_delivery.toFixed(2)}</p>
          </div>

          <h2>Günlük Dağılım</h2>
          <table>
            <thead>
              <tr>
                <th>Tarih</th>
                <th>Teslimat Sayısı</th>
                <th>Kazanç</th>
              </tr>
            </thead>
            <tbody>
              ${Object.entries(report.daily_breakdown || {}).map(([date, data]) => `
                <tr>
                  <td>${new Date(date).toLocaleDateString('tr-TR')}</td>
                  <td>${data.count}</td>
                  <td>₺${data.earnings.toFixed(2)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <p style="margin-top: 30px; color: #666; font-size: 12px;">Rapor Tarihi: ${new Date().toLocaleString('tr-TR')}</p>
        </body>
      </html>
    `;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(printContent);
    printWindow.document.close();
    printWindow.print();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Rapor hazırlanıyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <Card>
        <CardHeader>
          <CardTitle>💰 Kazanç Raporu</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-center">
            <div className="flex gap-2">
              {['daily', 'weekly', 'monthly'].map((p) => (
                <Button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={period === p ? 'bg-blue-600' : 'bg-gray-200 text-gray-700'}
                >
                  {p === 'daily' ? '📅 Günlük' : p === 'weekly' ? '📅 Haftalık' : '📅 Aylık'}
                </Button>
              ))}
            </div>
            <Button onClick={downloadPDF} className="bg-green-600 ml-auto">
              📄 PDF İndir
            </Button>
          </div>
        </CardContent>
      </Card>

      {report && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-blue-50">
              <CardContent className="p-6 text-center">
                <p className="text-blue-600 text-sm mb-2">Toplam Teslimat</p>
                <p className="text-4xl font-bold text-blue-800">{report.summary.total_deliveries}</p>
              </CardContent>
            </Card>
            <Card className="bg-green-50">
              <CardContent className="p-6 text-center">
                <p className="text-green-600 text-sm mb-2">Toplam Kazanç</p>
                <p className="text-4xl font-bold text-green-800">₺{report.summary.total_earnings.toFixed(2)}</p>
              </CardContent>
            </Card>
            <Card className="bg-purple-50">
              <CardContent className="p-6 text-center">
                <p className="text-purple-600 text-sm mb-2">Ortalama/Teslimat</p>
                <p className="text-4xl font-bold text-purple-800">₺{report.summary.average_per_delivery.toFixed(2)}</p>
              </CardContent>
            </Card>
          </div>

          {/* Daily Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Günlük Dağılım</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4">Tarih</th>
                      <th className="text-left py-3 px-4">Teslimat</th>
                      <th className="text-left py-3 px-4">Kazanç</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(report.daily_breakdown || {}).map(([date, data]) => (
                      <tr key={date} className="border-b hover:bg-gray-50">
                        <td className="py-3 px-4">{new Date(date).toLocaleDateString('tr-TR')}</td>
                        <td className="py-3 px-4">{data.count}</td>
                        <td className="py-3 px-4 font-bold text-green-600">₺{data.earnings.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};

export default CourierEarningsReport;