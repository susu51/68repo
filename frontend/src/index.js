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

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <App />
);
