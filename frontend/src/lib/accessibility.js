/**
 * Accessibility (A11y) Utilities for Kuryecini
 * WCAG AA compliant helpers and utilities
 */

// Screen reader only text utility
export const srOnly = "sr-only";

// ARIA helpers
export const ariaHelpers = {
  // Announce loading state
  announceLoading: (message = 'Yükleniyor...') => ({
    'aria-live': 'polite',
    'aria-label': message,
    role: 'status'
  }),
  
  // Announce errors
  announceError: (message) => ({
    'aria-live': 'assertive', 
    'aria-label': message,
    role: 'alert'
  }),
  
  // Button with loading state
  buttonLoading: (loading, loadingText = 'Yükleniyor...') => ({
    'aria-busy': loading,
    'aria-label': loading ? loadingText : undefined,
    disabled: loading
  }),
  
  // Modal/Dialog
  modal: (isOpen, titleId, descriptionId) => ({
    role: 'dialog',
    'aria-modal': isOpen,
    'aria-labelledby': titleId,
    'aria-describedby': descriptionId
  }),
  
  // Form field with error
  formField: (fieldId, errorId, hasError = false) => ({
    'aria-describedby': hasError ? errorId : undefined,
    'aria-invalid': hasError,
    'aria-required': true
  }),
  
  // Expandable content
  expandable: (isExpanded, controlsId) => ({
    'aria-expanded': isExpanded,
    'aria-controls': controlsId
  }),
  
  // Navigation
  nav: (label) => ({
    role: 'navigation',
    'aria-label': label
  }),
  
  // Landmark regions
  main: () => ({ role: 'main' }),
  banner: () => ({ role: 'banner' }),
  contentinfo: () => ({ role: 'contentinfo' }),
  
  // Lists
  list: (label) => ({
    role: 'list',
    'aria-label': label
  }),
  
  listItem: () => ({ role: 'listitem' })
};

// Keyboard navigation helpers
export const keyboardHelpers = {
  // Handle escape key
  handleEscape: (callback) => (event) => {
    if (event.key === 'Escape') {
      callback(event);
    }
  },
  
  // Handle enter/space for buttons
  handleActivation: (callback) => (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      callback(event);
    }
  },
  
  // Arrow key navigation for lists
  handleArrowNavigation: (items, currentIndex, setCurrentIndex) => (event) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setCurrentIndex((prev) => (prev + 1) % items.length);
        break;
      case 'ArrowUp':
        event.preventDefault();
        setCurrentIndex((prev) => (prev - 1 + items.length) % items.length);
        break;
      case 'Home':
        event.preventDefault();
        setCurrentIndex(0);
        break;
      case 'End':
        event.preventDefault();
        setCurrentIndex(items.length - 1);
        break;
    }
  }
};

// Focus management
export const focusHelpers = {
  // Focus trap for modals
  createFocusTrap: (containerRef) => {
    const getFocusableElements = () => {
      const focusableSelectors = [
        'button:not([disabled])',
        'input:not([disabled])',
        'textarea:not([disabled])',
        'select:not([disabled])',
        'a[href]',
        '[tabindex]:not([tabindex="-1"])',
        '[contenteditable="true"]'
      ].join(', ');
      
      return containerRef.current?.querySelectorAll(focusableSelectors) || [];
    };
    
    const trap = (event) => {
      if (event.key !== 'Tab') return;
      
      const focusableElements = getFocusableElements();
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      
      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement?.focus();
          event.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement?.focus();
          event.preventDefault();
        }
      }
    };
    
    return {
      activate: () => {
        const firstElement = getFocusableElements()[0];
        firstElement?.focus();
        document.addEventListener('keydown', trap);
      },
      deactivate: () => {
        document.removeEventListener('keydown', trap);
      }
    };
  },
  
  // Save and restore focus
  saveFocus: () => document.activeElement,
  restoreFocus: (element) => element?.focus?.(),
  
  // Focus first error in form
  focusFirstError: (formRef) => {
    const firstError = formRef.current?.querySelector('[aria-invalid="true"]');
    firstError?.focus();
  }
};

// Color contrast utilities (for dynamic content)
export const contrastHelpers = {
  // Check if background is light or dark
  isLightColor: (hexColor) => {
    const r = parseInt(hexColor.substr(1, 2), 16);
    const g = parseInt(hexColor.substr(3, 2), 16);
    const b = parseInt(hexColor.substr(5, 2), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    return brightness > 128;
  },
  
  // Get appropriate text color for background
  getTextColor: (backgroundColor) => {
    return contrastHelpers.isLightColor(backgroundColor) ? '#1F2937' : '#F9FAFB';
  }
};

// Announcer for dynamic content changes
export const createAnnouncer = () => {
  let announcer = document.getElementById('kuryecini-announcer');
  
  if (!announcer) {
    announcer = document.createElement('div');
    announcer.id = 'kuryecini-announcer';
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);
  }
  
  return {
    announce: (message, priority = 'polite') => {
      announcer.setAttribute('aria-live', priority);
      announcer.textContent = message;
      
      // Clear after announcement
      setTimeout(() => {
        announcer.textContent = '';
      }, 1000);
    }
  };
};

// Touch target helpers for mobile accessibility
export const touchTargets = {
  // Minimum 44px touch target
  minTouchTarget: 'min-h-[44px] min-w-[44px]',
  
  // Ensure proper spacing between touch targets
  touchSpacing: 'space-y-2 space-x-2'
};

// Form accessibility helpers
export const formAccessibility = {
  // Generate unique IDs for form fields
  generateId: (prefix = 'field') => `${prefix}-${Math.random().toString(36).substr(2, 9)}`,
  
  // Field wrapper with proper labeling
  fieldProps: (id, label, error, required = false) => ({
    fieldId: id,
    labelId: `${id}-label`,
    errorId: `${id}-error`,
    fieldProps: {
      id,
      'aria-labelledby': `${id}-label`,
      'aria-describedby': error ? `${id}-error` : undefined,
      'aria-invalid': !!error,
      'aria-required': required
    },
    labelProps: {
      id: `${id}-label`,
      htmlFor: id
    },
    errorProps: {
      id: `${id}-error`,
      role: 'alert',
      'aria-live': 'polite'
    }
  })
};

// Skip links for keyboard navigation
export const SkipLink = ({ href, children, ...props }) => (
  <a
    href={href}
    className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary text-primary-foreground px-4 py-2 rounded-md z-50 focus:z-[9999]"
    {...props}
  >
    {children}
  </a>
);

export default {
  ariaHelpers,
  keyboardHelpers, 
  focusHelpers,
  contrastHelpers,
  createAnnouncer,
  touchTargets,
  formAccessibility,
  SkipLink
};