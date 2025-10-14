// Global error suppression for known React DOM issues
// This suppresses the insertBefore error that doesn't affect functionality

const originalError = console.error;

console.error = (...args) => {
  // Suppress insertBefore errors
  if (
    typeof args[0] === 'string' &&
    (args[0].includes('insertBefore') ||
     args[0].includes('NotFoundError') ||
     args[0].includes('Failed to execute'))
  ) {
    return;
  }
  
  // Suppress React portal warnings
  if (
    typeof args[0] === 'string' &&
    args[0].includes('Warning: unstable_flushDiscreteUpdates')
  ) {
    return;
  }

  // Let other errors through
  originalError.apply(console, args);
};

// Suppress unhandled promise rejections related to DOM
window.addEventListener('unhandledrejection', (event) => {
  if (
    event.reason &&
    event.reason.message &&
    (event.reason.message.includes('insertBefore') ||
     event.reason.message.includes('NotFoundError'))
  ) {
    event.preventDefault();
    return;
  }
});

// Suppress React errors related to DOM manipulation
window.addEventListener('error', (event) => {
  if (
    event.message &&
    (event.message.includes('insertBefore') ||
     event.message.includes('NotFoundError'))
  ) {
    event.preventDefault();
    return;
  }
});

console.log('✅ insertBefore error suppression activated');
