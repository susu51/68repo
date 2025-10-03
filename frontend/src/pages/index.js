/**
 * Route-level lazy loading for Kuryecini
 * Performance optimization with React.lazy and Suspense
 */

import { lazy } from 'react';
import { LoadingScreen } from '../components/ui/loading';

// Loading fallback component
export const PageLoadingFallback = ({ pageName }) => (
  <LoadingScreen 
    message={`${pageName} yükleniyor...`}
    icon="⏳"
  />
);

// Lazy load main pages
export const HomePage = lazy(() => 
  import('./HomePage').then(module => ({ 
    default: module.HomePage || module.default 
  }))
);

export const CustomerDashboard = lazy(() => 
  import('./CustomerDashboard').then(module => ({ 
    default: module.CustomerDashboard || module.default 
  }))
);

export const CourierDashboard = lazy(() => 
  import('./CourierDashboard').then(module => ({ 
    default: module.CourierDashboard || module.default 
  }))
);

export const BusinessDashboard = lazy(() => 
  import('./BusinessDashboard').then(module => ({ 
    default: module.BusinessDashboard || module.default 
  }))
);

export const AdminPanel = lazy(() => 
  import('./AdminPanel').then(module => ({ 
    default: module.AdminPanel || module.default 
  }))
);

// Authentication pages
export const LoginPage = lazy(() => 
  import('./auth/LoginPage').then(module => ({ 
    default: module.LoginPage || module.default 
  }))
);

export const RegisterPage = lazy(() => 
  import('./auth/RegisterPage').then(module => ({ 
    default: module.RegisterPage || module.default 
  }))
);

// Customer pages
export const RestaurantList = lazy(() => 
  import('./customer/RestaurantList').then(module => ({ 
    default: module.RestaurantList || module.default 
  }))
);

export const RestaurantDetail = lazy(() => 
  import('./customer/RestaurantDetail').then(module => ({ 
    default: module.RestaurantDetail || module.default 
  }))
);

export const OrderHistory = lazy(() => 
  import('./customer/OrderHistory').then(module => ({ 
    default: module.OrderHistory || module.default 
  }))
);

export const CustomerProfile = lazy(() => 
  import('./customer/CustomerProfile').then(module => ({ 
    default: module.CustomerProfile || module.default 
  }))
);

// Courier pages
export const CourierMap = lazy(() => 
  import('./courier/CourierMap').then(module => ({ 
    default: module.CourierMap || module.default 
  }))
);

export const CourierEarnings = lazy(() => 
  import('./courier/CourierEarnings').then(module => ({ 
    default: module.CourierEarnings || module.default 
  }))
);

// Business pages
export const MenuManagement = lazy(() => 
  import('./business/MenuManagement').then(module => ({ 
    default: module.MenuManagement || module.default 
  }))
);

export const BusinessOrders = lazy(() => 
  import('./business/BusinessOrders').then(module => ({ 
    default: module.BusinessOrders || module.default 
  }))
);

export const BusinessAnalytics = lazy(() => 
  import('./business/BusinessAnalytics').then(module => ({ 
    default: module.BusinessAnalytics || module.default 
  }))
);

// Admin pages
export const UserManagement = lazy(() => 
  import('./admin/UserManagement').then(module => ({ 
    default: module.UserManagement || module.default 
  }))
);

export const KYCManagement = lazy(() => 
  import('./admin/KYCManagement').then(module => ({ 
    default: module.KYCManagement || module.default 
  }))
);

export const SystemSettings = lazy(() => 
  import('./admin/SystemSettings').then(module => ({ 
    default: module.SystemSettings || module.default 
  }))
);

// Error pages
export const NotFoundPage = lazy(() => 
  import('./error/NotFoundPage').then(module => ({ 
    default: module.NotFoundPage || module.default 
  }))
);

export const ErrorPage = lazy(() => 
  import('./error/ErrorPage').then(module => ({ 
    default: module.ErrorPage || module.default 
  }))
);

// Create preload functions for better UX
export const preloadPage = {
  customer: () => {
    import('./CustomerDashboard');
    import('./customer/RestaurantList');
    import('./customer/RestaurantDetail');
  },
  
  courier: () => {
    import('./CourierDashboard');
    import('./courier/CourierMap');
    import('./courier/CourierEarnings');
  },
  
  business: () => {
    import('./BusinessDashboard');
    import('./business/MenuManagement');
    import('./business/BusinessOrders');
  },
  
  admin: () => {
    import('./AdminPanel');
    import('./admin/UserManagement');
    import('./admin/KYCManagement');
  }
};

// Route definitions with metadata for optimization
export const routeConfig = [
  {
    path: '/',
    component: HomePage,
    name: 'Ana Sayfa',
    preload: false,
    critical: true
  },
  {
    path: '/login',
    component: LoginPage,
    name: 'Giriş',
    preload: true,
    critical: true
  },
  {
    path: '/register',
    component: RegisterPage,
    name: 'Kayıt',
    preload: false,
    critical: false
  },
  {
    path: '/customer',
    component: CustomerDashboard,
    name: 'Müşteri Paneli',
    preload: true,
    critical: true
  },
  {
    path: '/courier',
    component: CourierDashboard,
    name: 'Kurye Paneli',
    preload: false,
    critical: true
  },
  {
    path: '/business',
    component: BusinessDashboard,
    name: 'İşletme Paneli',
    preload: false,
    critical: true
  },
  {
    path: '/admin',
    component: AdminPanel,
    name: 'Admin Paneli',
    preload: false,
    critical: false
  }
];

export default {
  HomePage,
  CustomerDashboard,
  CourierDashboard, 
  BusinessDashboard,
  AdminPanel,
  LoginPage,
  RegisterPage,
  preloadPage,
  routeConfig,
  PageLoadingFallback
};