import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Store, Package, ShoppingBag, Settings, BarChart3, LogOut } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { MenuManagement } from './MenuManagement';
import { OrdersManagement } from './OrdersManagement';
import { BusinessSettings } from './BusinessSettings';
import { BusinessAnalytics } from './BusinessAnalytics';

export const BusinessApp = ({ user, onLogout }) => {
  const [activeView, setActiveView] = useState('menu');
  const [businessInfo, setBusinessInfo] = useState(null);

  useEffect(() => {
    loadBusinessInfo();
  }, []);

  const loadBusinessInfo = async () => {
    try {
      // Load business info from user data or API
      setBusinessInfo({
        name: user?.business_name || 'İşletmem',
        is_open: true,
        rating: 4.5
      });
    } catch (error) {
      console.error('Business info error:', error);
    }
  };

  const tabs = [
    { id: 'menu', label: 'Menü Yönetimi', icon: Package },
    { id: 'orders', label: 'Siparişler', icon: ShoppingBag },
    { id: 'analytics', label: 'Analitik', icon: BarChart3 },
    { id: 'settings', label: 'Ayarlar', icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header - Trendyol Go Style */}
      <header className="bg-white dark:bg-card border-b border-border sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left: Business Info */}
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Store className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="font-bold text-lg text-foreground">
                  {businessInfo?.name || 'İşletme Paneli'}
                </h1>
                <div className="flex items-center gap-2 text-xs">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full ${
                    businessInfo?.is_open 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}>
                    {businessInfo?.is_open ? '🟢 Açık' : '🔴 Kapalı'}
                  </span>
                  {businessInfo?.rating && (
                    <span className="text-muted-foreground">
                      ⭐ {businessInfo.rating}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Right: User menu */}
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground hidden sm:inline">
                {user?.email}
              </span>
              <Button onClick={onLogout} variant="outline" size="sm">
                <LogOut className="h-4 w-4 mr-2" />
                Çıkış
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative">
        {/* Menu Management */}
        <div style={{ display: activeView === 'menu' ? 'block' : 'none' }}>
          <MenuManagement />
        </div>

        {/* Orders Management */}
        <div style={{ display: activeView === 'orders' ? 'block' : 'none' }}>
          <OrdersManagement />
        </div>

        {/* Analytics */}
        <div style={{ display: activeView === 'analytics' ? 'block' : 'none' }}>
          <BusinessAnalytics />
        </div>

        {/* Settings */}
        <div style={{ display: activeView === 'settings' ? 'block' : 'none' }}>
          <BusinessSettings />
        </div>
      </main>

      {/* Bottom Navigation - Trendyol Go Style */}
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
                  <Icon className={`h-6 w-6 mb-1 transition-transform ${
                    isActive ? 'scale-110' : 'scale-100'
                  }`} />
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
