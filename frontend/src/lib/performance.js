/**
 * Performance optimization utilities for Kuryecini
 * Includes lazy loading, virtualization, and image optimization
 */

import { useState, useEffect, useCallback, useMemo, memo } from 'react';

// Debounce hook for search and input optimization
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Throttle hook for scroll and resize events
export const useThrottle = (callback, delay) => {
  const [throttledCallback, setThrottledCallback] = useState(null);

  useEffect(() => {
    let lastCall = 0;
    
    const throttled = (...args) => {
      const now = Date.now();
      if (now - lastCall >= delay) {
        lastCall = now;
        return callback(...args);
      }
    };
    
    setThrottledCallback(() => throttled);
  }, [callback, delay]);

  return throttledCallback;
};

// Intersection Observer hook for lazy loading
export const useIntersectionObserver = (
  elementRef,
  options = { threshold: 0.1, rootMargin: '50px' }
) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        setIsIntersecting(entry.isIntersecting);
        
        if (entry.isIntersecting && !hasIntersected) {
          setHasIntersected(true);
        }
      },
      options
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [elementRef, options, hasIntersected]);

  return { isIntersecting, hasIntersected };
};

// Optimized image component with lazy loading
export const OptimizedImage = memo(({ 
  src, 
  alt, 
  className = '', 
  fallbackSrc = '/placeholder-image.jpg',
  loading = 'lazy',
  sizes = '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw',
  ...props 
}) => {
  const [imageSrc, setImageSrc] = useState(loading === 'eager' ? src : null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    if (loading === 'lazy') {
      // Preload image
      const img = new Image();
      img.onload = () => {
        setImageSrc(src);
        setImageLoaded(true);
      };
      img.onerror = () => {
        setImageError(true);
        setImageSrc(fallbackSrc);
      };
      img.src = src;
    } else {
      setImageSrc(src);
    }
  }, [src, fallbackSrc, loading]);

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {!imageLoaded && !imageError && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
          <div className="w-8 h-8 text-gray-400">📷</div>
        </div>
      )}
      
      {imageSrc && (
        <img
          src={imageSrc}
          alt={alt}
          loading={loading}
          sizes={sizes}
          className={`transition-opacity duration-300 ${
            imageLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          onLoad={() => setImageLoaded(true)}
          onError={() => {
            setImageError(true);
            setImageSrc(fallbackSrc);
          }}
          {...props}
        />
      )}
    </div>
  );
});

OptimizedImage.displayName = 'OptimizedImage';

// Virtual list component for large datasets
export const VirtualList = ({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
  className = ''
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );
  
  const visibleItems = useMemo(() => {
    return items.slice(startIndex, endIndex + 1).map((item, index) => ({
      item,
      index: startIndex + index
    }));
  }, [items, startIndex, endIndex]);

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  return (
    <div 
      className={`relative overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={(e) => setScrollTop(e.target.scrollTop)}
    >
      <div style={{ height: totalHeight }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map(({ item, index }) => (
            <div key={index} style={{ height: itemHeight }}>
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Pagination hook for API optimization
export const usePagination = ({
  totalItems,
  itemsPerPage = 10,
  initialPage = 1
}) => {
  const [currentPage, setCurrentPage] = useState(initialPage);
  
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  
  const goToPage = useCallback((page) => {
    const clampedPage = Math.max(1, Math.min(page, totalPages));
    setCurrentPage(clampedPage);
  }, [totalPages]);
  
  const goToNext = useCallback(() => {
    goToPage(currentPage + 1);
  }, [currentPage, goToPage]);
  
  const goToPrevious = useCallback(() => {
    goToPage(currentPage - 1);
  }, [currentPage, goToPage]);
  
  const goToFirst = useCallback(() => {
    goToPage(1);
  }, [goToPage]);
  
  const goToLast = useCallback(() => {
    goToPage(totalPages);
  }, [goToPage, totalPages]);

  return {
    currentPage,
    totalPages,
    startIndex,
    endIndex,
    itemsPerPage,
    hasNextPage: currentPage < totalPages,
    hasPreviousPage: currentPage > 1,
    goToPage,
    goToNext,
    goToPrevious,
    goToFirst,
    goToLast
  };
};

// API cache with TTL
class ApiCache {
  constructor(defaultTTL = 5 * 60 * 1000) { // 5 minutes
    this.cache = new Map();
    this.defaultTTL = defaultTTL;
  }

  set(key, data, ttl = this.defaultTTL) {
    const expiresAt = Date.now() + ttl;
    this.cache.set(key, { data, expiresAt });
  }

  get(key) {
    const item = this.cache.get(key);
    
    if (!item) return null;
    
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return item.data;
  }

  clear() {
    this.cache.clear();
  }

  delete(key) {
    this.cache.delete(key);
  }
}

export const apiCache = new ApiCache();

// Memoized API hook
export const useCachedApi = (key, fetcher, dependencies = [], ttl) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      // Check cache first
      const cachedData = apiCache.get(key);
      
      if (cachedData) {
        setData(cachedData);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        const result = await fetcher();
        
        // Cache the result
        apiCache.set(key, result, ttl);
        
        setData(result);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [key, fetcher, ttl, ...dependencies]);

  const refetch = useCallback(() => {
    apiCache.delete(key);
    setLoading(true);
    
    const fetchData = async () => {
      try {
        const result = await fetcher();
        apiCache.set(key, result, ttl);
        setData(result);
        setError(null);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [key, fetcher, ttl]);

  return { data, loading, error, refetch };
};

// Performance monitoring hook
export const usePerformanceMonitor = (componentName) => {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      if (renderTime > 100) { // Log slow renders
        console.warn(`Slow render detected in ${componentName}: ${renderTime.toFixed(2)}ms`);
      }
    };
  });
  
  const measureAction = useCallback((actionName, action) => {
    const startTime = performance.now();
    const result = action();
    const endTime = performance.now();
    
    console.log(`${componentName} - ${actionName}: ${(endTime - startTime).toFixed(2)}ms`);
    
    return result;
  }, [componentName]);

  return { measureAction };
};

// Resource preloader
export const preloadResource = (url, type = 'image') => {
  return new Promise((resolve, reject) => {
    if (type === 'image') {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = url;
    } else if (type === 'script') {
      const script = document.createElement('script');
      script.onload = () => resolve(script);
      script.onerror = reject;
      script.src = url;
      document.head.appendChild(script);
    }
  });
};

export default {
  useDebounce,
  useThrottle,
  useIntersectionObserver,
  OptimizedImage,
  VirtualList,
  usePagination,
  apiCache,
  useCachedApi,
  usePerformanceMonitor,
  preloadResource
};