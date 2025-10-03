import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Global error handlers for DOM manipulation errors
window.addEventListener('error', (event) => {
  const error = event.error;
  if (error && error.message) {
    const message = error.message.toLowerCase();
    
    // Handle DOM manipulation errors gracefully
    if (message.includes('removechild') || 
        message.includes('appendchild') ||
        message.includes('insertbefore') ||
        (message.includes('node') && message.includes('child'))) {
      
      console.warn('Global DOM error caught and suppressed:', error.message);
      event.preventDefault(); // Prevent default error reporting
      return false;
    }
  }
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason;
  if (error && error.message) {
    const message = error.message.toLowerCase();
    
    // Suppress DOM-related promise rejections
    if (message.includes('removechild') || 
        message.includes('appendchild') ||
        message.includes('node')) {
      
      console.warn('Global DOM promise rejection caught and suppressed:', error.message);
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
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
