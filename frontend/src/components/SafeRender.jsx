/**
 * SafeRender component to prevent React object rendering errors
 */

import React from 'react';

export const SafeRender = ({ children, fallback = '', className = '' }) => {
  const safeRender = (element) => {
    // Handle null/undefined
    if (element === null || element === undefined) {
      return fallback;
    }
    
    // Handle primitives
    if (typeof element === 'string' || typeof element === 'number' || typeof element === 'boolean') {
      return element;
    }
    
    // Handle React elements
    if (React.isValidElement(element)) {
      return element;
    }
    
    // Handle arrays
    if (Array.isArray(element)) {
      return element.map((item, index) => (
        <SafeRender key={index}>{item}</SafeRender>
      ));
    }
    
    // Handle objects - convert to string representation
    if (typeof element === 'object') {
      // Common object types
      if (element.address && typeof element.address === 'string') {
        return element.address;
      }
      
      if (element.name) return element.name;
      if (element.title) return element.title;
      if (element.label) return element.label;
      
      // Address objects
      if (element.address_line) {
        return `${element.address_line}${element.city ? `, ${element.city}` : ''}`;
      }
      
      // Location objects
      if (element.lat && element.lng) {
        return `${element.lat.toFixed(4)}, ${element.lng.toFixed(4)}`;
      }
      
      // Warn about unsafe object rendering
      console.warn('SafeRender: Converting object to JSON string (not recommended):', element);
      return JSON.stringify(element, null, 2);
    }
    
    // Fallback
    return String(element) || fallback;
  };

  try {
    const rendered = safeRender(children);
    
    if (className) {
      return <span className={className}>{rendered}</span>;
    }
    
    return rendered;
  } catch (error) {
    console.error('SafeRender error:', error);
    return <span className="text-red-500">Render Error</span>;
  }
};

// Specific safe renderers for common use cases
export const SafeAddress = ({ address, className = '' }) => {
  if (!address) return <span className={className}>Adres belirtilmemiş</span>;
  
  if (typeof address === 'string') {
    return <span className={className}>{address}</span>;
  }
  
  if (typeof address === 'object') {
    let addressText = '';
    
    if (address.address_line) {
      addressText = [
        address.address_line,
        address.district,
        address.city,
        address.postal_code
      ].filter(Boolean).join(', ');
    } else if (address.address) {
      addressText = address.address;
    } else {
      addressText = 'Geçersiz adres formatı';
    }
    
    return <span className={className} title={JSON.stringify(address)}>{addressText}</span>;
  }
  
  return <span className={className}>Adres formatı hatası</span>;
};

export const SafeLocation = ({ location, className = '' }) => {
  if (!location) return <span className={className}>Konum belirtilmemiş</span>;
  
  if (typeof location === 'string') {
    return <span className={className}>{location}</span>;
  }
  
  if (typeof location === 'object' && location.lat && location.lng) {
    const coords = `${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`;
    return <span className={className} title="Koordinatlar">{coords}</span>;
  }
  
  return <span className={className}>Geçersiz konum</span>;
};

export const SafePrice = ({ amount, currency = '₺', className = '' }) => {
  if (amount === null || amount === undefined) {
    return <span className={className}>-</span>;
  }
  
  const numericAmount = typeof amount === 'number' ? amount : parseFloat(amount);
  
  if (isNaN(numericAmount)) {
    return <span className={className}>Geçersiz fiyat</span>;
  }
  
  return <span className={className}>{currency}{numericAmount.toFixed(2)}</span>;
};

// Debug component to help identify object rendering issues
export const ObjectDebugger = ({ object, name = 'Object' }) => {
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }
  
  return (
    <details className="text-xs text-gray-500 border p-2 rounded mt-2">
      <summary className="cursor-pointer">{name} Debug Info</summary>
      <pre className="mt-2 overflow-auto max-h-32">
        {JSON.stringify(object, null, 2)}
      </pre>
    </details>
  );
};

export default SafeRender;