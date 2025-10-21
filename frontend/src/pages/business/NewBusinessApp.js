import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { 
  Store, 
  Package, 
  ShoppingBag, 
  Settings, 
  BarChart3, 
  LogOut,
  Clock,
  MapPin,
  Phone,
  Mail,
  TrendingUp,
  DollarSign,
  Users,
  Star
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { get } from '../../api/http';
import { useTheme } from '../../contexts/ThemeContext';
import { useDashboardSummary } from '../../hooks/useDashboardSummary';
import WSManager from '../../ws/WSManager';

// Sub-components
import { ModernMenuManagement } from './ModernMenuManagement';
import { ModernOrdersManagement } from './ModernOrdersManagement';
import { ModernBusinessSettings } from './ModernBusinessSettings';
import { ModernDashboard } from './ModernDashboard';

export const NewBusinessApp = ({ user, onLogout }) => {
  const [activeView, setActiveView] = useState('dashboard');
  const [businessInfo, setBusinessInfo] = useState(null);
  const [allComponentsMounted, setAllComponentsMounted] = useState(false);
  const { theme, toggleTheme } = useTheme();
  
  // Use real dashboard data hook
  const { 
    data: dashboardData, 
    loading: dashboardLoading, 
    error: dashboardError, 
    refetch: refetchDashboard 
  } = useDashboardSummary(null, {
    autoRefetch: false, // We'll handle refresh via WebSocket
    onError: (error) => {
      console.error('❌ Dashboard load error:', error);
      toast.error('Dashboard verileri yüklenemedi');
    }
  });

  // Map dashboard data to stats format
  const stats = dashboardData ? {
    todayOrders: dashboardData.today_orders_count || 0,
    todayRevenue: dashboardData.today_revenue || 0,
    pendingOrders: dashboardData.pending_orders_count || 0,
    menuItems: dashboardData.menu_items_count || 0,
    rating: dashboardData.rating_avg || 0,
    totalCustomers: dashboardData.total_customers || 0,
    activities: dashboardData.activities || []
  } : {
    todayOrders: 0,
    todayRevenue: 0,
    pendingOrders: 0,
    menuItems: 0,
    rating: 0,
    totalCustomers: 0,
    activities: []
  };
  
  const loading = dashboardLoading;

  // Force light mode for business panel
  useEffect(() => {
    document.documentElement.classList.remove('dark');
    document.documentElement.style.colorScheme = 'light';
    
    // Cleanup: restore dark mode preference when unmounting
    return () => {
      const savedTheme = localStorage.getItem('kuryecini-theme');
      if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.style.colorScheme = 'dark';
      }
    };
  }, []);

  useEffect(() => {
    loadBusinessInfo();
    // Mount all components after initial load
    setTimeout(() => setAllComponentsMounted(true), 100);
  }, []);

  // WebSocket invalidation - refresh dashboard on real-time events
  useEffect(() => {
    const businessId = user?.id;
    if (!businessId) return;

    const handleWebSocketMessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const eventType = message.event_type || message.type;
        
        console.log('📡 WebSocket event received in dashboard:', eventType);
        
        // Invalidate dashboard on relevant events
        const eventsToInvalidate = [
          'order.created',
          'order_created',
          'order.status_changed', 
          'order_status_changed',
          'rating.received',
          'rating_received',
          'menu.updated',
          'menu_updated'
        ];
        
        if (eventsToInvalidate.includes(eventType)) {
          console.log('🔄 Refreshing dashboard due to:', eventType);
          refetchDashboard();
        }
      } catch (error) {
        console.error('❌ Error handling WebSocket message:', error);
      }
    };

    // Subscribe to WebSocket events
    const ws = WSManager.getConnection();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.addEventListener('message', handleWebSocketMessage);
      
      return () => {
        ws.removeEventListener('message', handleWebSocketMessage);
      };
    }
  }, [user?.id, refetchDashboard]);

  const loadBusinessInfo = async () => {
    try {
      // Get business ID from authenticated user
      const businessId = user?.id; // Business user's own ID is the business_id
      
      console.log('🏪 Loading business info for ID:', businessId);
      
      setBusinessInfo({
        id: businessId,
        name: user?.business_name || user?.first_name || 'İşletmem',
        is_open: true,
        rating: 4.5,
        total_reviews: 128,
        phone: user?.phone || '+90 555 000 0000',
        email: user?.email,
        address: 'Ankara, Türkiye',
        opening_hours: '09:00 - 23:00'
      });
      
      console.log('✅ Business info loaded, ID:', businessId);
    } catch (error) {
      console.error('Business info error:', error);
    }
  };

  const handleToggleOpen = async () => {
    const newStatus = !businessInfo.is_open;
    setBusinessInfo(prev => ({ ...prev, is_open: newStatus }));
    toast.success(newStatus ? 'İşletme açıldı' : 'İşletme kapatıldı');
  };

  const tabs = [
    { id: 'dashboard', label: 'Gösterge', icon: BarChart3 },
    { id: 'menu', label: 'Menü', icon: Package },
    { id: 'orders', label: 'Siparişler', icon: ShoppingBag },
    { id: 'settings', label: 'Ayarlar', icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Modern Header */}
      <header className="bg-white dark:bg-card border-b border-border sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left: Business Info */}
            <div className="flex items-center space-x-4">
              <div className="p-2 rounded-xl bg-gradient-orange shadow-orange">
                <Store className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="font-bold text-lg text-foreground">
                  {businessInfo?.name || 'İşletme Paneli'}
                </h1>
                <div className="flex items-center gap-3 text-xs">
                  {/* Status Badge */}
                  <button
                    onClick={handleToggleOpen}
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium transition-all ${
                      businessInfo?.is_open 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 hover:bg-green-200' 
                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 hover:bg-red-200'
                    }`}
                  >
                    <div className={`w-1.5 h-1.5 rounded-full ${businessInfo?.is_open ? 'bg-green-600' : 'bg-red-600'}`}></div>
                    {businessInfo?.is_open ? 'Açık' : 'Kapalı'}
                  </button>
                  
                  {/* Rating */}
                  {businessInfo?.rating && (
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                      {businessInfo.rating}
                      {businessInfo.total_reviews && (
                        <span className="text-muted-foreground">({businessInfo.total_reviews})</span>
                      )}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Quick Stats & Actions */}
            <div className="flex items-center gap-4">
              {/* Quick Stats */}
              <div className="hidden lg:flex items-center gap-6 mr-4">
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Bugün</div>
                  <div className="font-bold text-primary">{stats.todayOrders}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Bekleyen</div>
                  <div className="font-bold text-orange-600">{stats.pendingOrders}</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-muted-foreground">Gelir</div>
                  <div className="font-bold text-green-600">₺{stats.todayRevenue}</div>
                </div>
              </div>

              {/* User Email */}
              <span className="text-sm text-muted-foreground hidden sm:inline">
                {user?.email}
              </span>

              {/* Logout */}
              <Button onClick={onLogout} variant="outline" size="sm">
                <LogOut className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Çıkış</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative overflow-hidden">
        {/* Dashboard - Always rendered, controlled by display */}
        <div 
          style={{ 
            display: activeView === 'dashboard' ? 'block' : 'none',
            height: '100%',
            overflow: 'auto'
          }}
          className="absolute inset-0"
        >
          <ModernDashboard 
            key="dashboard"
            businessInfo={businessInfo} 
            stats={stats} 
            loading={loading}
            onRefresh={refetchDashboard}
            onNavigate={setActiveView}
          />
        </div>

        {/* Menu Management - Always mounted */}
        <div 
          style={{ 
            display: activeView === 'menu' ? 'block' : 'none',
            height: '100%',
            overflow: 'auto'
          }}
          className="absolute inset-0"
        >
          <ModernMenuManagement 
            key="menu"
            businessId={businessInfo?.id}
            onStatsUpdate={loadStats}
          />
        </div>

        {/* Orders Management - Always mounted */}
        <div 
          style={{ 
            display: activeView === 'orders' ? 'block' : 'none',
            height: '100%',
            overflow: 'auto'
          }}
          className="absolute inset-0"
        >
          <ModernOrdersManagement 
            key="orders"
            businessId={businessInfo?.id} 
          />
        </div>

        {/* Settings - Always mounted */}
        <div 
          style={{ 
            display: activeView === 'settings' ? 'block' : 'none',
            height: '100%',
            overflow: 'auto'
          }}
          className="absolute inset-0"
        >
          <ModernBusinessSettings 
            key="settings"
            businessInfo={businessInfo}
            onUpdate={setBusinessInfo}
          />
        </div>
      </main>

      {/* Bottom Navigation - Modern */}
      <nav className="bg-white dark:bg-card border-t border-border sticky bottom-0 z-40 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-around">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeView === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveView(tab.id)}
                  className={`flex flex-col items-center py-3 px-4 sm:px-8 transition-all duration-200 relative ${
                    isActive
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-1 bg-primary rounded-b-full" />
                  )}
                  
                  {/* Badge for pending orders */}
                  <div className="relative">
                    <Icon className={`h-6 w-6 mb-1 transition-transform ${
                      isActive ? 'scale-110' : 'scale-100'
                    }`} />
                    {tab.id === 'orders' && stats.pendingOrders > 0 && (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                        {stats.pendingOrders}
                      </div>
                    )}
                  </div>
                  
                  <span className={`text-xs font-medium ${
                    isActive ? 'font-semibold' : ''
                  }`}>
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>
    </div>
  );
};
