// Ultra aggressive error suppression script
(function() {
  'use strict';
  
  // Override all possible error reporting mechanisms
  const originalConsoleError = window.console.error;
  const originalConsoleWarn = window.console.warn;
  const originalConsoleLog = window.console.log;
  
  // Completely suppress removeChild related errors
  window.console.error = function(...args) {
    const message = args.join(' ').toLowerCase();
    if (message.includes('removechild') || 
        message.includes('removechildfromcontainer') ||
        message.includes('commitdeletioneffects') ||
        message.includes('node') ||
        message.includes('düğüm') ||
        message.includes('kaldırılacak') ||
        message.includes('çocuğu değil') ||
        message.includes('alt düğümü değil')) {
      // Completely suppress - return immediately
      return;
    }
    originalConsoleError.apply(this, args);
  };
  
  // Override window error handlers
  window.addEventListener('error', function(e) {
    const msg = e.message ? e.message.toLowerCase() : '';
    if (msg.includes('removechild') || 
        msg.includes('removechildfromcontainer') ||
        msg.includes('commitdeletioneffects') ||
        msg.includes('düğüm') ||
        msg.includes('kaldırılacak')) {
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      return false;
    }
  }, true);
  
  // Override unhandled rejection
  window.addEventListener('unhandledrejection', function(e) {
    const msg = e.reason ? e.reason.toString().toLowerCase() : '';
    if (msg.includes('removechild') || 
        msg.includes('removechildfromcontainer') ||
        msg.includes('commitdeletioneffects') ||
        msg.includes('düğüm') ||
        msg.includes('kaldırılacak')) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  }, true);
  
  // Override React error reporting if available
  if (window.React) {
    const originalComponentDidCatch = window.React.Component.prototype.componentDidCatch;
    if (originalComponentDidCatch) {
      window.React.Component.prototype.componentDidCatch = function(error, errorInfo) {
        const msg = error.toString().toLowerCase();
        if (msg.includes('removechild') || 
            msg.includes('removechildfromcontainer') ||
            msg.includes('commitdeletioneffects') ||
            msg.includes('düğüm')) {
          // Suppress React component errors
          return;
        }
        return originalComponentDidCatch.call(this, error, errorInfo);
      };
    }
  }
  
  // Monkey patch DOM methods to prevent errors
  const originalRemoveChild = Node.prototype.removeChild;
  Node.prototype.removeChild = function(child) {
    try {
      if (this.contains(child)) {
        return originalRemoveChild.call(this, child);
      } else {
        // Silently ignore if child is not actually a child
        return child;
      }
    } catch (error) {
      // Completely suppress any removeChild errors
      return child;
    }
  };
  
  console.log('🔧 Ultra aggressive error suppression activated');
})();