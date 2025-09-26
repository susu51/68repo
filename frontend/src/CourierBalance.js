import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CourierBalance = () => {
  const [balanceData, setBalanceData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBalance();
  }, []);

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem('delivertr_token');
      const response = await axios.get(`${API}/courier/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setBalanceData(response.data);
    } catch (error) {
      console.error('Bakiye alınamadı:', error);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <div className="w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p className="text-sm text-gray-600">Bakiye yükleniyor...</p>
        </CardContent>
      </Card>
    );
  }

  const balance = balanceData?.balance;
  const earnings = balanceData?.recent_earnings || [];

  return (
    <div className="space-y-6">
      {/* Balance Overview */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Mevcut Bakiye</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              ₺{balance?.available_balance?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-gray-600 mt-1">Çekilebilir</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Bekleyen Ödeme</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              ₺{balance?.pending_balance?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-gray-600 mt-1">Teslim sonrası</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Toplam Kazanç</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              ₺{balance?.total_earnings?.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {balance?.total_deliveries || 0} teslimat
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Withdraw Button */}
      <Card>
        <CardHeader>
          <CardTitle>Bakiye İşlemleri</CardTitle>
          <CardDescription>IBAN: TR** **** **** **34 5678</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">
                Minimum çekim tutarı: ₺50.00
              </p>
              <p className="text-xs text-gray-500">
                Para transferi 1-2 iş günü içinde hesabınıza geçer
              </p>
            </div>
            <Button
              disabled={(balance?.available_balance || 0) < 50}
              className="bg-green-600 hover:bg-green-700"
              data-testid="withdraw-btn"
            >
              Para Çek
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Earnings */}
      <Card>
        <CardHeader>
          <CardTitle>Son Kazançlar</CardTitle>
          <CardDescription>Son teslimatlarınızdan elde ettiğiniz kazançlar</CardDescription>
        </CardHeader>
        <CardContent>
          {earnings.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">💰</div>
              <p>Henüz kazanç kaydınız yok</p>
              <p className="text-sm">Teslimat yaparak para kazanmaya başlayın</p>
            </div>
          ) : (
            <div className="space-y-3">
              {earnings.map((earning) => (
                <div
                  key={earning.id}
                  className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium">₺{earning.amount?.toFixed(2)}</p>
                    <p className="text-sm text-gray-600">{earning.description}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(earning.created_at).toLocaleString('tr-TR')}
                    </p>
                  </div>
                  <Badge 
                    className={
                      earning.transaction_type === 'delivery' ? 'bg-green-100 text-green-800' :
                      earning.transaction_type === 'bonus' ? 'bg-blue-100 text-blue-800' :
                      'bg-red-100 text-red-800'
                    }
                  >
                    {earning.transaction_type === 'delivery' && '🚚 Teslimat'}
                    {earning.transaction_type === 'bonus' && '🎁 Bonus'}
                    {earning.transaction_type === 'penalty' && '⚠️ Kesinti'}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Earning Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Kazanç İpuçları</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <span className="text-green-600">💡</span>
              <span>Yoğun saatlerde (12:00-14:00, 19:00-22:00) daha fazla sipariş alabilirsiniz</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-blue-600">⚡</span>
              <span>Express paket siparişleri %50 daha fazla kazanç sağlar</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-orange-600">🎯</span>
              <span>Müşteri memnuniyetini artırmak için zamanında teslim yapın</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="text-purple-600">📍</span>
              <span>Konumunuzu güncel tutarak daha yakın siparişler alın</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CourierBalance;