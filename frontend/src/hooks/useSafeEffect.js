/**
 * Safe useEffect hook to prevent memory leaks and DOM manipulation errors
 */

import { useEffect, useRef } from 'react';

export const useSafeEffect = (effect, deps) => {
  const isMountedRef = useRef(true);
  
  useEffect(() => {
    isMountedRef.current = true;
    
    const cleanup = effect();
    
    return () => {
      isMountedRef.current = false;
      if (cleanup && typeof cleanup === 'function') {
        try {
          cleanup();
        } catch (error) {
          console.warn('Cleanup function error:', error);
        }
      }
    };
  }, deps);
  
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);
  
  return isMountedRef;
};

// Safe DOM manipulation hook
export const useSafeDOM = () => {
  const isMountedRef = useRef(true);
  
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);
  
  const safeAppendChild = (parent, child) => {
    if (!isMountedRef.current) return false;
    
    try {
      if (parent && child && parent.appendChild) {
        parent.appendChild(child);
        return true;
      }
    } catch (error) {
      console.warn('Safe appendChild failed:', error);
    }
    return false;
  };
  
  const safeRemoveChild = (parent, child) => {
    if (!isMountedRef.current) return false;
    
    try {
      if (parent && child && parent.contains && parent.contains(child)) {
        parent.removeChild(child);
        return true;
      } else if (child && child.remove) {
        child.remove();
        return true;
      }
    } catch (error) {
      console.warn('Safe removeChild failed:', error);
    }
    return false;
  };
  
  const safeRemove = (element) => {
    if (!isMountedRef.current) return false;
    
    try {
      if (element && element.parentNode) {
        element.parentNode.removeChild(element);
        return true;
      } else if (element && element.remove) {
        element.remove();
        return true;
      }
    } catch (error) {
      console.warn('Safe remove failed:', error);
    }
    return false;
  };
  
  return {
    safeAppendChild,
    safeRemoveChild, 
    safeRemove,
    isMounted: () => isMountedRef.current
  };
};

export default useSafeEffect;