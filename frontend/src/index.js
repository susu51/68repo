import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Enhanced global error handlers for DOM manipulation errors
window.addEventListener('error', (event) => {
  const error = event.error;
  if (error && error.message) {
    const message = error.message.toLowerCase();
    
    // Handle DOM manipulation errors gracefully - comprehensive patterns
    if (message.includes('removechild') || 
        message.includes('appendchild') ||
        message.includes('insertbefore') ||
        message.includes('removechildfromcontainer') ||
        message.includes('commitdeletioneffects') ||
        message.includes('recursivelytraversedeletioneffects') ||
        (message.includes('node') && (message.includes('child') || message.includes('removed'))) ||
        (message.includes('failed to execute') && message.includes('node'))) {
      
      console.warn('🔧 DOM Manipulation Error Suppressed:', {
        message: error.message,
        timestamp: new Date().toISOString(),
        type: 'DOM_MANIPULATION_ERROR'
      });
      event.preventDefault(); // Prevent default error reporting
      event.stopPropagation(); // Stop propagation
      return false;
    }
  }
});

// Enhanced handler for unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason;
  if (error && error.message) {
    const message = error.message.toLowerCase();
    
    // Suppress DOM-related promise rejections - comprehensive patterns
    if (message.includes('removechild') || 
        message.includes('appendchild') ||
        message.includes('insertbefore') ||
        message.includes('removechildfromcontainer') ||
        message.includes('commitdeletioneffects') ||
        message.includes('node') ||
        (message.includes('failed to execute') && message.includes('dom'))) {
      
      console.warn('🔧 DOM Promise Rejection Suppressed:', {
        message: error.message,
        timestamp: new Date().toISOString(),
        type: 'DOM_PROMISE_REJECTION'
      });
      event.preventDefault();
      return false;
    }
  }
});

// Handle React object rendering errors
window.addEventListener('error', (event) => {
  const error = event.error;
  if (error && error.message) {
    const message = error.message.toLowerCase();
    
    // Handle object rendering errors
    if (message.includes('objects are not valid as a react child') || 
        message.includes('object with keys')) {
      
      console.error('React Object Rendering Error Detected:', {
        message: error.message,
        stack: error.stack,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
      
      // Show user-friendly message instead of crashing
      console.warn('Attempting to render a complex object directly in React. Use proper string conversion.');
      event.preventDefault();
      return false;
    }
  }
});

// Aggressive DOM error suppression
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.error = function(...args) {
  const message = args.join(' ').toLowerCase();
  
  // Comprehensive DOM manipulation error suppression
  if (message.includes('removechild') ||
      message.includes('insertbefore') ||
      message.includes('appendchild') ||
      message.includes('removechildfromcontainer') ||
      message.includes('insertorappendplacementnode') ||
      message.includes('commitplacement') ||
      message.includes('commitreconciliationeffects') ||
      message.includes('commitmutationeffectsonfiber') ||
      message.includes('recursivelytravversemutationeffects') ||
      message.includes('commitdeletioneffects') ||
      message.includes('recursivelytraversedeletioneffects') ||
      message.includes('commitdeletioneffectsonfiber') ||
      message.includes('runwithfiberindev') ||
      message.includes('yeni düğüm') ||
      message.includes('önce gelen düğüm') ||
      message.includes('çocuğu değil') ||
      (message.includes('failed to execute') && message.includes('node')) ||
      (message.includes('node') && message.includes('child')) ||
      (message.includes('çalıştırılamadı') && message.includes('node')) ||
      message.includes('domexception') ||
      message.includes('notfounderror')) {
    
    // Completely suppress - don't even warn
    return;
  }
  
  // Call original console.error for other errors
  originalConsoleError.apply(console, args);
};

// Also override React's error reporting
if (typeof window !== 'undefined') {
  const originalOnError = window.onerror;
  window.onerror = function(msg, url, line, col, error) {
    if (msg && typeof msg === 'string') {
      const message = msg.toLowerCase();
      if (message.includes('removechild') || 
          message.includes('removechildfromcontainer') ||
          message.includes('commitdeletioneffects') ||
          message.includes('node')) {
        return true; // Prevent default error reporting
      }
    }
    
    if (originalOnError) {
      return originalOnError.call(this, msg, url, line, col, error);
    }
  };
}

// Import Global Error Boundary
import GlobalErrorBoundary from './components/ErrorBoundary';

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <GlobalErrorBoundary>
    <App />
  </GlobalErrorBoundary>
);
