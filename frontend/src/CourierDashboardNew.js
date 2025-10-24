import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { 
  MapPin, 
  Package, 
  TrendingUp, 
  User, 
  LogOut,
  Clock,
  DollarSign,
  CheckCircle,
  Navigation
} from 'lucide-react';
import { toast } from 'sonner';
import { CourierReadyOrdersMap } from './components/CourierReadyOrdersMap';
import { CourierWaitingTasks } from './components/CourierWaitingTasks';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CourierDashboardNew = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('map');
  const [stats, setStats] = useState({
    todayDeliveries: 0,
    todayEarnings: 0,
    activeOrders: 0,
    rating: 4.8
  });
  const [loading, setLoading] = useState(false);

  // Fetch courier stats
  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 60000); // Every minute
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      // Mock stats for now - can be replaced with real API
      setStats({
        todayDeliveries: 12,
        todayEarnings: 450.50,
        activeOrders: 2,
        rating: 4.8
      });
    } catch (error) {
      console.error('Stats fetch error:', error);
    }
  };

  const tabs = [
    { id: 'map', label: 'Hazır Siparişler', icon: MapPin, color: 'green' },
    { id: 'waiting', label: 'Bekleyen Görevler', icon: Clock, color: 'orange' },
    { id: 'active', label: 'Aktif Teslimatlar', icon: Package, color: 'blue' },
    { id: 'profile', label: 'Profil', icon: User, color: 'purple' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-green-700 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Kurye Paneli</h1>
              <p className="text-green-100 text-sm">
                Hoş geldin, {user?.first_name || user?.email}
              </p>
            </div>
            <Button
              variant="ghost"
              onClick={onLogout}
              className="text-white hover:bg-white/20"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Çıkış
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Bugünkü Teslimat</p>
                  <p className="text-2xl font-bold">{stats.todayDeliveries}</p>
                </div>
                <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Bugünkü Kazanç</p>
                  <p className="text-2xl font-bold">₺{stats.todayEarnings.toFixed(2)}</p>
                </div>
                <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <DollarSign className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Aktif Siparişler</p>
                  <p className="text-2xl font-bold">{stats.activeOrders}</p>
                </div>
                <div className="h-12 w-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <Package className="h-6 w-6 text-orange-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Değerlendirme</p>
                  <p className="text-2xl font-bold">{stats.rating} ⭐</p>
                </div>
                <div className="h-12 w-12 bg-yellow-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="h-6 w-6 text-yellow-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-sm p-2 mb-6">
          <div className="flex gap-2 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <Button
                  key={tab.id}
                  variant={isActive ? "default" : "ghost"}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 whitespace-nowrap ${
                    isActive 
                      ? (tab.color === 'green' ? 'bg-green-600 hover:bg-green-700 text-white' :
                         tab.color === 'orange' ? 'bg-orange-600 hover:bg-orange-700 text-white' :
                         tab.color === 'blue' ? 'bg-blue-600 hover:bg-blue-700 text-white' :
                         'bg-purple-600 hover:bg-purple-700 text-white')
                      : ''
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </Button>
              );
            })}
          </div>
        </div>

        {/* Content Area */}
        <div className="space-y-4">
          {/* Hazır Siparişler (Map) */}
          {activeTab === 'map' && (
            <div>
              <CourierReadyOrdersMap />
            </div>
          )}

          {/* Bekleyen Görevler */}
          {activeTab === 'waiting' && (
            <div>
              <CourierWaitingTasks />
            </div>
          )}

          {/* Aktif Teslimatlar */}
          {activeTab === 'active' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Aktif Teslimatlarım
                </CardTitle>
                <CardDescription>
                  Şu anda teslim etmekte olduğunuz siparişler
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-muted-foreground">
                  <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Şu an aktif teslimatınız bulunmuyor</p>
                  <p className="text-sm mt-2">Hazır siparişler sekmesinden sipariş alabilirsiniz</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Profil */}
          {activeTab === 'profile' && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Profil Bilgilerim
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Ad Soyad</p>
                      <p className="font-medium">
                        {user?.first_name} {user?.last_name}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">E-posta</p>
                      <p className="font-medium">{user?.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Telefon</p>
                      <p className="font-medium">{user?.phone || 'Belirtilmemiş'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Rol</p>
                      <Badge>Kurye</Badge>
                    </div>
                  </div>

                  <div className="border-t pt-4 mt-4">
                    <h3 className="font-semibold mb-3">İstatistikler</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Toplam Teslimat</p>
                        <p className="text-xl font-bold">{stats.todayDeliveries * 30}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Ortalama Puan</p>
                        <p className="text-xl font-bold">{stats.rating} ⭐</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(CourierDashboardNew);
