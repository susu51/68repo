import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { 
  TrendingUp, 
  DollarSign, 
  ShoppingBag, 
  Users, 
  Package,
  Clock,
  Star,
  RefreshCw,
  ArrowUp,
  ArrowDown
} from 'lucide-react';

export const ModernDashboard = ({ businessInfo, stats, loading, onRefresh }) => {
  const statCards = [
    {
      title: 'Bugünkü Siparişler',
      value: stats.todayOrders,
      icon: ShoppingBag,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
      change: '+12%',
      changeType: 'increase'
    },
    {
      title: 'Bugünkü Gelir',
      value: `₺${stats.todayRevenue.toLocaleString()}`,
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
      change: '+8%',
      changeType: 'increase'
    },
    {
      title: 'Bekleyen Siparişler',
      value: stats.pendingOrders,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
      urgent: stats.pendingOrders > 3
    },
    {
      title: 'Menü Ürünleri',
      value: stats.menuItems,
      icon: Package,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20'
    },
    {
      title: 'Toplam Müşteri',
      value: stats.totalCustomers,
      icon: Users,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100 dark:bg-indigo-900/20'
    },
    {
      title: 'Değerlendirme',
      value: stats.rating,
      icon: Star,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
      suffix: '/ 5.0'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Gösterge Paneli</h1>
          <p className="text-sm text-muted-foreground mt-1">
            İşletmenizin genel durumu
          </p>
        </div>
        <Button
          onClick={onRefresh}
          variant="outline"
          size="sm"
          disabled={loading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Yenile
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          
          return (
            <Card key={index} className="card-hover-lift">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground mb-2">
                      {stat.title}
                    </p>
                    <div className="flex items-baseline gap-2">
                      <h3 className="text-3xl font-bold text-foreground">
                        {stat.value}
                      </h3>
                      {stat.suffix && (
                        <span className="text-sm text-muted-foreground">
                          {stat.suffix}
                        </span>
                      )}
                    </div>
                    {stat.change && (
                      <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${
                        stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {stat.changeType === 'increase' ? (
                          <ArrowUp className="h-3 w-3" />
                        ) : (
                          <ArrowDown className="h-3 w-3" />
                        )}
                        {stat.change} dün
                      </div>
                    )}
                    {stat.urgent && (
                      <div className="mt-2 text-xs font-medium text-red-600 animate-pulse">
                        ⚠️ Acil sipariş var!
                      </div>
                    )}
                  </div>
                  <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Actions */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            Hızlı İşlemler
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex flex-col gap-2">
              <Package className="h-6 w-6" />
              <span className="text-xs">Yeni Ürün</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col gap-2">
              <ShoppingBag className="h-6 w-6" />
              <span className="text-xs">Siparişler</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col gap-2">
              <Clock className="h-6 w-6" />
              <span className="text-xs">Çalışma Saati</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col gap-2">
              <Star className="h-6 w-6" />
              <span className="text-xs">Yorumlar</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Son Aktiviteler</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 pb-3 border-b border-border last:border-0">
              <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/20">
                <ShoppingBag className="h-4 w-4 text-green-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Yeni sipariş alındı</p>
                <p className="text-xs text-muted-foreground">₺125.50 - 2 dakika önce</p>
              </div>
            </div>
            <div className="flex items-start gap-3 pb-3 border-b border-border last:border-0">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/20">
                <Package className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Menü güncellendi</p>
                <p className="text-xs text-muted-foreground">3 ürün eklendi - 1 saat önce</p>
              </div>
            </div>
            <div className="flex items-start gap-3 pb-3 border-b border-border last:border-0">
              <div className="p-2 rounded-lg bg-yellow-100 dark:bg-yellow-900/20">
                <Star className="h-4 w-4 text-yellow-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Yeni değerlendirme</p>
                <p className="text-xs text-muted-foreground">5 yıldız - 3 saat önce</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
