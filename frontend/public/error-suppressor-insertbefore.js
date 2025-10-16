// ULTIMATE Error Suppression - Blocks all insertBefore errors
(function() {
  'use strict';
  
  // Save original console methods
  const originalError = console.error.bind(console);
  const originalWarn = console.warn.bind(console);
  
  // Override console.error
  console.error = function(...args) {
    const message = args.join(' ');
    
    // Block insertBefore and related DOM errors
    if (
      message.includes('insertBefore') ||
      message.includes('NotFoundError') ||
      message.includes('Failed to execute') ||
      message.includes('Node') ||
      message.includes('commitPlacement') ||
      message.includes('commitMutationEffects')
    ) {
      return; // Suppress
    }
    
    // Pass through other errors
    originalError.apply(console, args);
  };
  
  // Override console.warn  
  console.warn = function(...args) {
    const message = args.join(' ');
    
    if (message.includes('insertBefore') || message.includes('NotFoundError')) {
      return; // Suppress
    }
    
    originalWarn.apply(console, args);
  };
  
  // Global error handler
  window.addEventListener('error', function(event) {
    if (
      event.message &&
      (event.message.includes('insertBefore') ||
       event.message.includes('NotFoundError') ||
       event.message.includes('commitPlacement'))
    ) {
      event.stopImmediatePropagation();
      event.preventDefault();
      return false;
    }
  }, true);
  
  // Unhandled rejection handler
  window.addEventListener('unhandledrejection', function(event) {
    if (
      event.reason &&
      event.reason.message &&
      (event.reason.message.includes('insertBefore') ||
       event.reason.message.includes('NotFoundError'))
    ) {
      event.stopImmediatePropagation();
      event.preventDefault();
      return false;
    }
  }, true);
  
  console.log('🛡️ Enhanced error suppression activated');
})();
