/**
 * Safe object rendering utility to prevent React child object errors
 */

export const safeRenderObject = (obj, fallback = '') => {
  if (obj === null || obj === undefined) {
    return fallback;
  }
  
  if (typeof obj === 'string' || typeof obj === 'number') {
    return obj;
  }
  
  if (typeof obj === 'object') {
    // Handle address objects specifically
    if (obj.address && typeof obj.address === 'string') {
      return obj.address;
    }
    
    if (obj.address_line && obj.city) {
      return `${obj.address_line}, ${obj.city}`;
    }
    
    // Handle coordinate objects
    if (obj.lat && obj.lng) {
      return `Koordinat: ${obj.lat.toFixed(4)}, ${obj.lng.toFixed(4)}`;
    }
    
    // Try to find a string representation
    if (obj.name) return obj.name;
    if (obj.title) return obj.title;
    if (obj.label) return obj.label;
    
    // Last resort: JSON stringify (shouldn't be used in production)
    console.warn('Unsafe object rendering detected:', obj);
    return JSON.stringify(obj);
  }
  
  return String(obj);
};

// Specific address renderer
export const renderAddress = (addressObj) => {
  if (!addressObj) return 'Adres belirtilmemiş';
  
  if (typeof addressObj === 'string') {
    return addressObj;
  }
  
  if (typeof addressObj === 'object') {
    // Full address object
    if (addressObj.address_line) {
      const parts = [
        addressObj.address_line,
        addressObj.district,
        addressObj.city,
        addressObj.postal_code
      ].filter(Boolean);
      
      return parts.join(', ');
    }
    
    // Simple address object
    if (addressObj.address) {
      return addressObj.address;
    }
    
    // Fallback for unknown structure
    console.warn('Unknown address structure:', addressObj);
    return 'Geçersiz adres formatı';
  }
  
  return 'Adres formatı hatası';
};

// Order item safe renderer
export const renderOrderItem = (item) => {
  if (!item) return '';
  
  if (typeof item === 'string') return item;
  
  if (typeof item === 'object') {
    return item.name || item.title || item.product_name || 'Ürün';
  }
  
  return String(item);
};

export default {
  safeRenderObject,
  renderAddress,
  renderOrderItem
};