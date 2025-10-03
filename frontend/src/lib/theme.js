/**
 * Kuryecini Design System - Theme Configuration
 * Professional design tokens for consistent UI/UX
 */

// Brand Colors - Kuryecini Identity
export const brandColors = {
  // Primary brand colors
  orange: {
    50: '#FFF7ED',
    100: '#FFEDD5', 
    200: '#FED7AA',
    300: '#FDBA74',
    400: '#FB923C',
    500: '#F97316', // Main brand orange
    600: '#EA580C',
    700: '#C2410C',
    800: '#9A3412',
    900: '#7C2D12',
    950: '#431407'
  },
  
  // Secondary colors
  red: {
    50: '#FEF2F2',
    500: '#EF4444', // Error states
    600: '#DC2626'
  },
  
  green: {
    50: '#F0FDF4', 
    500: '#10B981', // Success states
    600: '#059669'
  },
  
  yellow: {
    50: '#FFFBEB',
    500: '#F59E0B', // Warning states
    600: '#D97706'
  },
  
  blue: {
    50: '#EFF6FF',
    500: '#3B82F6', // Info states
    600: '#2563EB'
  },
  
  // Neutral grays
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB', 
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
    950: '#030712'
  }
};

// Typography Scale
export const typography = {
  // Font families
  fontFamily: {
    sans: [
      'Inter', 
      '-apple-system', 
      'BlinkMacSystemFont', 
      'Segoe UI', 
      'Roboto', 
      'Oxygen', 
      'Ubuntu', 
      'Cantarell', 
      'sans-serif'
    ],
    mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace']
  },
  
  // Font sizes (rem units)
  fontSize: {
    xs: '0.75rem',     // 12px
    sm: '0.875rem',    // 14px  
    base: '1rem',      // 16px
    lg: '1.125rem',    // 18px
    xl: '1.25rem',     // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
    '5xl': '3rem',     // 48px
    '6xl': '3.75rem'   // 60px
  },
  
  // Font weights
  fontWeight: {
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800
  },
  
  // Line heights
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2
  }
};

// Spacing Scale (rem units)
export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
  32: '8rem',     // 128px
  40: '10rem',    // 160px
  48: '12rem',    // 192px
  56: '14rem',    // 224px
  64: '16rem'     // 256px
};

// Border radius scale
export const borderRadius = {
  none: '0',
  sm: '0.125rem',   // 2px
  base: '0.25rem',  // 4px
  md: '0.375rem',   // 6px
  lg: '0.5rem',     // 8px
  xl: '0.75rem',    // 12px
  '2xl': '1rem',    // 16px
  '3xl': '1.5rem',  // 24px
  full: '9999px'
};

// Shadow scale
export const boxShadow = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  base: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)'
};

// Animation & Transitions
export const animation = {
  // Transition timing
  transition: {
    fast: '150ms ease-out',
    normal: '250ms ease-out', 
    slow: '350ms ease-out'
  },
  
  // Easing functions
  easing: {
    linear: 'cubic-bezier(0.0, 0.0, 1.0, 1.0)',
    easeIn: 'cubic-bezier(0.4, 0.0, 1.0, 1.0)',
    easeOut: 'cubic-bezier(0.0, 0.0, 0.2, 1.0)',
    easeInOut: 'cubic-bezier(0.4, 0.0, 0.2, 1.0)'
  }
};

// Component-specific design tokens
export const components = {
  // Button variants
  button: {
    height: {
      sm: '2rem',     // 32px
      md: '2.5rem',   // 40px  
      lg: '3rem'      // 48px
    },
    padding: {
      sm: '0.5rem 0.75rem',
      md: '0.625rem 1rem', 
      lg: '0.75rem 1.5rem'
    }
  },
  
  // Input variants
  input: {
    height: {
      sm: '2rem',
      md: '2.5rem',
      lg: '3rem'
    }
  },
  
  // Card variants
  card: {
    padding: {
      sm: '1rem',
      md: '1.5rem',
      lg: '2rem'
    }
  }
};

// Layout breakpoints (mobile-first)
export const breakpoints = {
  xs: '475px',
  sm: '640px', 
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px'
};

// Z-index scale
export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800
};

// Theme configuration object
export const theme = {
  colors: brandColors,
  typography,
  spacing,
  borderRadius,
  boxShadow,
  animation,
  components,
  breakpoints,
  zIndex
};

export default theme;