/**
 * Analytics and Performance Monitoring for Kuryecini
 * Privacy-friendly analytics with Vercel Analytics integration
 */

// Vercel Analytics (privacy-friendly)
import { track } from '@vercel/analytics';

// Custom analytics events
export const analytics = {
  // Page tracking
  pageView: (page, userId = null) => {
    try {
      // Vercel Analytics
      track('page_view', {
        page,
        user_id: userId,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        referrer: document.referrer,
        language: navigator.language
      });
      
      // Google Analytics 4 (if enabled)
      if (window.gtag && process.env.REACT_APP_GA_MEASUREMENT_ID) {
        window.gtag('event', 'page_view', {
          page_title: document.title,
          page_location: window.location.href,
          user_id: userId
        });
      }
    } catch (error) {
      console.warn('Analytics page view tracking failed:', error);
    }
  },

  // User authentication events
  login: (method, userId, userRole) => {
    track('user_login', {
      method,
      user_id: userId,
      user_role: userRole,
      timestamp: new Date().toISOString()
    });
  },

  signup: (method, userId, userRole) => {
    track('user_signup', {
      method,
      user_id: userId,
      user_role: userRole,
      timestamp: new Date().toISOString()
    });
  },

  logout: (userId) => {
    track('user_logout', {
      user_id: userId,
      session_duration: performance.now()
    });
  },

  // E-commerce events
  restaurantView: (restaurantId, restaurantName) => {
    track('restaurant_view', {
      restaurant_id: restaurantId,
      restaurant_name: restaurantName,
      timestamp: new Date().toISOString()
    });
  },

  productView: (productId, productName, restaurantId, price) => {
    track('product_view', {
      product_id: productId,
      product_name: productName,
      restaurant_id: restaurantId,
      price,
      currency: 'TRY'
    });
  },

  addToCart: (productId, productName, price, quantity) => {
    track('add_to_cart', {
      product_id: productId,
      product_name: productName,
      price,
      quantity,
      value: price * quantity,
      currency: 'TRY'
    });
  },

  removeFromCart: (productId, productName) => {
    track('remove_from_cart', {
      product_id: productId,
      product_name: productName
    });
  },

  beginCheckout: (cartValue, itemCount) => {
    track('begin_checkout', {
      value: cartValue,
      currency: 'TRY',
      items: itemCount
    });
  },

  purchase: (orderId, totalAmount, items, restaurantId) => {
    track('purchase', {
      transaction_id: orderId,
      value: totalAmount,
      currency: 'TRY',
      items: items.length,
      restaurant_id: restaurantId,
      timestamp: new Date().toISOString()
    });
  },

  // Search and filtering
  search: (query, resultsCount, filters = {}) => {
    track('search', {
      search_term: query,
      results_count: resultsCount,
      filters: JSON.stringify(filters)
    });
  },

  filterUsed: (filterType, filterValue, resultsCount) => {
    track('filter_used', {
      filter_type: filterType,
      filter_value: filterValue,
      results_count: resultsCount
    });
  },

  // User engagement
  buttonClick: (buttonName, location, userId = null) => {
    track('button_click', {
      button_name: buttonName,
      location,
      user_id: userId
    });
  },

  formSubmit: (formName, success, errors = []) => {
    track('form_submit', {
      form_name: formName,
      success,
      errors: errors.join(', ') || null
    });
  },

  // Performance events
  performanceMetric: (metric, value, page) => {
    track('performance_metric', {
      metric,
      value,
      page,
      timestamp: new Date().toISOString()
    });
  },

  // Error tracking
  error: (errorType, errorMessage, component, userId = null) => {
    track('error_occurred', {
      error_type: errorType,
      error_message: errorMessage,
      component,
      user_id: userId,
      url: window.location.href,
      user_agent: navigator.userAgent
    });
  },

  // Custom events
  custom: (eventName, properties = {}) => {
    track(eventName, {
      ...properties,
      timestamp: new Date().toISOString()
    });
  }
};

// Performance monitoring
export class PerformanceMonitor {
  constructor() {
    this.metrics = {};
    this.observers = {};
    this.startTime = performance.now();
  }

  // Core Web Vitals monitoring
  initWebVitals() {
    try {
      // Largest Contentful Paint (LCP)
      if ('PerformanceObserver' in window) {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          
          if (lastEntry) {
            const lcp = lastEntry.startTime;
            this.recordMetric('LCP', lcp);
            
            if (lcp > 2500) {
              analytics.performanceMetric('LCP', lcp, window.location.pathname);
            }
          }
        });

        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.lcp = lcpObserver;

        // First Input Delay (FID)
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            const fid = entry.processingStart - entry.startTime;
            this.recordMetric('FID', fid);
            
            if (fid > 100) {
              analytics.performanceMetric('FID', fid, window.location.pathname);
            }
          });
        });

        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.fid = fidObserver;

        // Cumulative Layout Shift (CLS)
        let clsScore = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (!entry.hadRecentInput) {
              clsScore += entry.value;
            }
          });
          
          this.recordMetric('CLS', clsScore);
          
          if (clsScore > 0.1) {
            analytics.performanceMetric('CLS', clsScore, window.location.pathname);
          }
        });

        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.cls = clsObserver;
      }
    } catch (error) {
      console.warn('Web Vitals monitoring initialization failed:', error);
    }
  }

  // Navigation timing
  recordNavigationTiming() {
    if (performance.getEntriesByType) {
      const navigation = performance.getEntriesByType('navigation')[0];
      if (navigation) {
        const metrics = {
          DNS: navigation.domainLookupEnd - navigation.domainLookupStart,
          TCP: navigation.connectEnd - navigation.connectStart,
          SSL: navigation.secureConnectionStart > 0 ? 
                navigation.connectEnd - navigation.secureConnectionStart : 0,
          TTFB: navigation.responseStart - navigation.requestStart,
          Download: navigation.responseEnd - navigation.responseStart,
          DOM: navigation.domContentLoadedEventEnd - navigation.navigationStart,
          Load: navigation.loadEventEnd - navigation.navigationStart
        };

        Object.entries(metrics).forEach(([key, value]) => {
          this.recordMetric(key, value);
          
          // Track slow metrics
          const thresholds = {
            DNS: 500, TCP: 500, SSL: 500,
            TTFB: 1000, Download: 1000,
            DOM: 3000, Load: 5000
          };
          
          if (value > thresholds[key]) {
            analytics.performanceMetric(key, value, window.location.pathname);
          }
        });
      }
    }
  }

  // Resource timing
  recordResourceTiming() {
    if (performance.getEntriesByType) {
      const resources = performance.getEntriesByType('resource');
      const slowResources = resources.filter(resource => 
        resource.duration > 1000 && resource.name.includes(window.location.origin)
      );
      
      slowResources.forEach(resource => {
        analytics.performanceMetric('slow_resource', resource.duration, resource.name);
      });
    }
  }

  recordMetric(name, value) {
    this.metrics[name] = value;
  }

  getMetrics() {
    return { ...this.metrics };
  }

  cleanup() {
    Object.values(this.observers).forEach(observer => {
      observer.disconnect();
    });
  }
}

// Memory monitoring
export const monitorMemoryUsage = () => {
  if ('memory' in performance) {
    const memory = performance.memory;
    const memoryMB = {
      used: Math.round(memory.usedJSHeapSize / 1048576),
      total: Math.round(memory.totalJSHeapSize / 1048576),
      limit: Math.round(memory.jsHeapSizeLimit / 1048576)
    };

    // Alert if memory usage is high
    if (memoryMB.used > 100) { // 100MB threshold
      analytics.performanceMetric('high_memory_usage', memoryMB.used, window.location.pathname);
    }

    return memoryMB;
  }
  return null;
};

// Error boundary analytics integration
export const reportError = (error, errorInfo, component) => {
  analytics.error(
    error.name || 'UnknownError',
    error.message || 'No error message',
    component,
    localStorage.getItem('user_id')
  );
};

// User session tracking
export class SessionTracker {
  constructor() {
    this.sessionId = this.generateSessionId();
    this.startTime = Date.now();
    this.pageViews = 0;
    this.interactions = 0;
    
    this.setupEventListeners();
  }

  generateSessionId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  setupEventListeners() {
    // Track user interactions
    ['click', 'scroll', 'keypress'].forEach(eventType => {
      document.addEventListener(eventType, () => {
        this.interactions++;
      }, { passive: true, capture: true });
    });

    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.recordSessionData();
      }
    });

    // Track before page unload
    window.addEventListener('beforeunload', () => {
      this.recordSessionData();
    });
  }

  recordPageView() {
    this.pageViews++;
  }

  recordSessionData() {
    const sessionDuration = Date.now() - this.startTime;
    
    track('session_data', {
      session_id: this.sessionId,
      duration_ms: sessionDuration,
      page_views: this.pageViews,
      interactions: this.interactions,
      bounce: this.pageViews <= 1 && this.interactions < 5
    });
  }
}

// Initialize analytics
export const initAnalytics = () => {
  // Initialize performance monitoring
  const performanceMonitor = new PerformanceMonitor();
  performanceMonitor.initWebVitals();
  
  // Record initial navigation timing
  if (document.readyState === 'complete') {
    performanceMonitor.recordNavigationTiming();
    performanceMonitor.recordResourceTiming();
  } else {
    window.addEventListener('load', () => {
      setTimeout(() => {
        performanceMonitor.recordNavigationTiming();
        performanceMonitor.recordResourceTiming();
      }, 0);
    });
  }

  // Initialize session tracking
  const sessionTracker = new SessionTracker();
  
  // Monitor memory usage periodically
  setInterval(() => {
    monitorMemoryUsage();
  }, 60000); // Every minute

  return {
    performanceMonitor,
    sessionTracker
  };
};

export default analytics;