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

export const ModernDashboard = ({ businessInfo, stats, loading, onRefresh, onNavigate }) => {
  const statCards = [
    {
      title: 'Bugünkü Siparişler',
      value: stats.todayOrders ?? '—',
      icon: ShoppingBag,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
      testId: 'card-today-orders'
    },
    {
      title: 'Bugünkü Gelir',
      value: stats.todayRevenue >= 0 ? `₺${stats.todayRevenue.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—',
      icon: DollarSign,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
      testId: 'card-today-revenue'
    },
    {
      title: 'Bekleyen Siparişler',
      value: stats.pendingOrders ?? '—',
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
      urgent: stats.pendingOrders > 3,
      testId: 'card-pending'
    },
    {
      title: 'Menü Ürünleri',
      value: stats.menuItems ?? '—',
      icon: Package,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100 dark:bg-purple-900/20',
      testId: 'card-menu-items'
    },
    {
      title: 'Toplam Müşteri',
      value: stats.totalCustomers ?? '—',
      icon: Users,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100 dark:bg-indigo-900/20',
      testId: 'card-total-customers'
    },
    {
      title: 'Değerlendirme',
      value: stats.rating > 0 ? stats.rating.toFixed(1) : '—',
      icon: Star,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
      suffix: stats.rating > 0 ? '/ 5.0' : '',
      testId: 'card-rating'
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
            <Card key={index} className="card-hover-lift" data-testid={stat.testId}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-muted-foreground mb-2">
                      {stat.title}
                    </p>
                    <div className="flex items-baseline gap-2">
                      <h3 className="text-3xl font-bold text-foreground">
                        {loading ? '...' : stat.value}
                      </h3>
                      {stat.suffix && (
                        <span className="text-sm text-muted-foreground">
                          {stat.suffix}
                        </span>
                      )}
                    </div>
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
            <Button 
              variant="outline" 
              className="h-20 flex flex-col gap-2 hover:bg-primary hover:text-white transition-colors"
              onClick={() => onNavigate && onNavigate('menu')}
            >
              <Package className="h-6 w-6" />
              <span className="text-xs">Yeni Ürün</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex flex-col gap-2 hover:bg-primary hover:text-white transition-colors"
              onClick={() => onNavigate && onNavigate('orders')}
            >
              <ShoppingBag className="h-6 w-6" />
              <span className="text-xs">Siparişler</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex flex-col gap-2 hover:bg-primary hover:text-white transition-colors"
              onClick={() => onNavigate && onNavigate('settings')}
            >
              <Clock className="h-6 w-6" />
              <span className="text-xs">Çalışma Saati</span>
            </Button>
            <Button 
              variant="outline" 
              className="h-20 flex flex-col gap-2 hover:bg-primary hover:text-white transition-colors"
              onClick={() => onNavigate && onNavigate('orders')}
            >
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
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
              <p className="text-sm">Yükleniyor...</p>
            </div>
          ) : stats.activities && stats.activities.length > 0 ? (
            <div className="space-y-4" data-testid="activities-list">
              {stats.activities.slice(0, 20).map((activity, index) => {
                const getActivityIcon = (type) => {
                  switch(type) {
                    case 'order_created':
                      return { Icon: ShoppingBag, bgColor: 'bg-green-100 dark:bg-green-900/20', color: 'text-green-600' };
                    case 'menu_updated':
                      return { Icon: Package, bgColor: 'bg-blue-100 dark:bg-blue-900/20', color: 'text-blue-600' };
                    case 'rating_received':
                      return { Icon: Star, bgColor: 'bg-yellow-100 dark:bg-yellow-900/20', color: 'text-yellow-600' };
                    default:
                      return { Icon: ShoppingBag, bgColor: 'bg-gray-100 dark:bg-gray-900/20', color: 'text-gray-600' };
                  }
                };
                
                const { Icon, bgColor, color } = getActivityIcon(activity.type);
                
                const getTimeAgo = (timestamp) => {
                  if (!timestamp) return '';
                  try {
                    const date = new Date(timestamp);
                    const now = new Date();
                    const diffMs = now - date;
                    const diffMins = Math.floor(diffMs / 60000);
                    
                    if (diffMins < 1) return 'Az önce';
                    if (diffMins < 60) return `${diffMins} dakika önce`;
                    
                    const diffHours = Math.floor(diffMins / 60);
                    if (diffHours < 24) return `${diffHours} saat önce`;
                    
                    const diffDays = Math.floor(diffHours / 24);
                    return `${diffDays} gün önce`;
                  } catch (e) {
                    return '';
                  }
                };
                
                const meta = activity.meta || {};
                const amount = meta.amount ? `₺${parseFloat(meta.amount).toFixed(2)}` : '';
                const details = meta.customer_name || meta.order_code || '';
                
                return (
                  <div key={index} className="flex items-start gap-3 pb-3 border-b border-border last:border-0">
                    <div className={`p-2 rounded-lg ${bgColor}`}>
                      <Icon className={`h-4 w-4 ${color}`} />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {amount && details ? `${amount} - ${details}` : amount || details}
                        {activity.ts && ` - ${getTimeAgo(activity.ts)}`}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p className="text-sm">Henüz aktivite yok</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Wrap with React.memo to prevent unnecessary re-renders
export default React.memo(ModernDashboard);
