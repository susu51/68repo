// Utility to safely render values and prevent React object rendering errors
export const renderSafe = (value) => {
  if (value === null || value === undefined) {
    return '';
  }
  
  if (typeof value === 'object') {
    // If it's an object, don't render it directly
    console.warn('Attempted to render object directly:', value);
    return '[Object]';
  }
  
  return String(value);
};

// Safe location display
export const renderLocation = (location) => {
  if (!location) return 'Konum bilgisi yok';
  
  if (typeof location === 'string') return location;
  
  if (typeof location === 'object') {
    // Handle different location formats
    if (location.address || location.adres) {
      return location.address || location.adres;
    }
    
    if (location.name) return location.name;
    
    // If it has coordinates, show them
    const lat = location.lat || location.enlem;
    const lng = location.lng || location.uzunluk;
    
    if (lat && lng) {
      return `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    }
    
    return 'Konum bilgisi mevcut değil';
  }
  
  return String(location);
};

export default { renderSafe, renderLocation };