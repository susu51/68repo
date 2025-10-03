/**
 * DOM Safety Utilities for React Components
 * Prevents removeChild and appendChild errors
 */

// Safe DOM element creation and cleanup
export const createSafeDownloadLink = (blob, filename) => {
  return new Promise((resolve, reject) => {
    try {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none'; // Make invisible
      
      // Create cleanup function
      const cleanup = () => {
        try {
          if (link.parentNode === document.body) {
            document.body.removeChild(link);
          } else if (link.remove) {
            link.remove();
          }
          URL.revokeObjectURL(url);
        } catch (cleanupError) {
          console.warn('Download link cleanup warning:', cleanupError.message);
        }
      };
      
      // Safe append and click
      document.body.appendChild(link);
      
      // Use requestAnimationFrame to ensure DOM is ready
      requestAnimationFrame(() => {
        try {
          link.click();
          
          // Clean up after a short delay
          setTimeout(cleanup, 100);
          resolve(true);
        } catch (clickError) {
          cleanup();
          reject(clickError);
        }
      });
      
    } catch (error) {
      reject(error);
    }
  });
};

// Safe event listener management
export const addSafeEventListener = (element, event, handler, options) => {
  if (!element || !element.addEventListener) {
    console.warn('Invalid element for event listener');
    return null;
  }
  
  try {
    element.addEventListener(event, handler, options);
    
    // Return cleanup function
    return () => {
      try {
        if (element && element.removeEventListener) {
          element.removeEventListener(event, handler, options);
        }
      } catch (error) {
        console.warn('Event listener cleanup warning:', error.message);
      }
    };
  } catch (error) {
    console.warn('Failed to add event listener:', error.message);
    return null;
  }
};

// Safe DOM query with error handling
export const safeDOMQuery = (selector, context = document) => {
  try {
    return context.querySelector(selector);
  } catch (error) {
    console.warn('DOM query failed:', error.message);
    return null;
  }
};

// Safe DOM element removal
export const safeRemoveElement = (element) => {
  if (!element) return false;
  
  try {
    // Method 1: Try modern remove() method
    if (element.remove && typeof element.remove === 'function') {
      element.remove();
      return true;
    }
    
    // Method 2: Try traditional removeChild
    if (element.parentNode && element.parentNode.removeChild) {
      element.parentNode.removeChild(element);
      return true;
    }
    
    return false;
  } catch (error) {
    console.warn('Safe element removal failed:', error.message);
    return false;
  }
};

// Safe DOM element creation
export const createSafeElement = (tagName, attributes = {}, parent = null) => {
  try {
    const element = document.createElement(tagName);
    
    // Set attributes safely
    Object.entries(attributes).forEach(([key, value]) => {
      try {
        if (key === 'style' && typeof value === 'object') {
          Object.assign(element.style, value);
        } else {
          element.setAttribute(key, value);
        }
      } catch (attrError) {
        console.warn(`Failed to set attribute ${key}:`, attrError.message);
      }
    });
    
    // Append to parent safely if provided
    if (parent) {
      try {
        parent.appendChild(element);
      } catch (appendError) {
        console.warn('Failed to append element:', appendError.message);
      }
    }
    
    return element;
  } catch (error) {
    console.warn('Failed to create element:', error.message);
    return null;
  }
};

// React component cleanup helper
export const useCleanupRef = () => {
  const cleanupFunctionsRef = useRef([]);
  
  const addCleanup = (cleanupFn) => {
    if (typeof cleanupFn === 'function') {
      cleanupFunctionsRef.current.push(cleanupFn);
    }
  };
  
  const cleanup = () => {
    cleanupFunctionsRef.current.forEach((fn) => {
      try {
        fn();
      } catch (error) {
        console.warn('Cleanup function error:', error.message);
      }
    });
    cleanupFunctionsRef.current = [];
  };
  
  // Auto cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, []);
  
  return { addCleanup, cleanup };
};

export default {
  createSafeDownloadLink,
  addSafeEventListener,
  safeDOMQuery,
  safeRemoveElement,
  createSafeElement,
  useCleanupRef
};