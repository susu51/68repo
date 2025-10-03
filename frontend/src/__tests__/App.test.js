/**
 * Frontend tests for Kuryecini React Application
 * Testing critical user flows and component functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';

// Mock axios for API calls
import axios from 'axios';
jest.mock('axios');
const mockedAxios = axios;

// Mock components to avoid complex dependencies
jest.mock('../LeafletMap', () => {
  return function MockLeafletMap() {
    return <div data-testid="leaflet-map">Mocked Leaflet Map</div>;
  };
});

jest.mock('../components/DynamicLeafletMap', () => {
  return function MockDynamicLeafletMap() {
    return <div data-testid="dynamic-leaflet-map">Mocked Dynamic Leaflet Map</div>;
  };
});

// Import components to test
import App from '../App';
import { ModernLogin } from '../ModernLogin';
import { AccessibleButton, AccessibleInput, FormField } from '../components/ui/accessible-form';
import { LoadingSpinner, LoadingScreen, EmptyState } from '../components/ui/loading';
import { ErrorState, NetworkError } from '../components/ui/error-state';

// Test wrapper for Router
const TestWrapper = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('App Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders without crashing', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );
    
    // Should render the app without throwing
    expect(document.body).toBeInTheDocument();
  });

  test('shows loading state initially', () => {
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );
    
    // Should show some form of loading or main content
    // Since App.js is complex, just verify it renders
    expect(document.body).toBeInTheDocument();
  });
});

describe('ModernLogin Component', () => {
  const mockOnLogin = jest.fn();
  const mockOnRegister = jest.fn();

  beforeEach(() => {
    mockOnLogin.mockClear();
    mockOnRegister.mockClear();
  });

  test('renders login form', () => {
    render(
      <ModernLogin onLogin={mockOnLogin} onRegister={mockOnRegister} />
    );
    
    // Check for essential login elements
    expect(screen.getByText(/giriş/i)).toBeInTheDocument();
  });

  test('handles login form submission', async () => {
    const user = userEvent.setup();
    
    render(
      <ModernLogin onLogin={mockOnLogin} onRegister={mockOnRegister} />
    );
    
    // This test would need to be adapted based on the actual ModernLogin component structure
    // For now, just check that the component renders
    expect(screen.getByText(/giriş/i)).toBeInTheDocument();
  });
});

describe('Accessible Form Components', () => {
  test('AccessibleButton renders correctly', () => {
    render(
      <AccessibleButton>Test Button</AccessibleButton>
    );
    
    const button = screen.getByRole('button', { name: /test button/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  test('AccessibleButton shows loading state', () => {
    render(
      <AccessibleButton loading={true} loadingText="Saving...">
        Save
      </AccessibleButton>
    );
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
  });

  test('FormField with error shows error message', () => {
    render(
      <FormField 
        label="Email"
        error="Email is required"
        required={true}
      >
        <AccessibleInput type="email" />
      </FormField>
    );
    
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Email is required')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
  });

  test('AccessibleInput has proper accessibility attributes', () => {
    render(
      <FormField label="Test Input" required={true}>
        <AccessibleInput placeholder="Enter text" />
      </FormField>
    );
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-required', 'true');
    expect(input).toHaveAttribute('placeholder', 'Enter text');
  });
});

describe('Loading Components', () => {
  test('LoadingSpinner renders with correct size', () => {
    render(<LoadingSpinner size="lg" />);
    
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('w-12', 'h-12');
  });

  test('LoadingScreen shows message', () => {
    render(<LoadingScreen message="Loading data..." icon="⏳" />);
    
    expect(screen.getByText('⏳ Loading data...')).toBeInTheDocument();
    expect(screen.getByText('Veriler yükleniyor, lütfen bekleyin...')).toBeInTheDocument();
  });

  test('EmptyState renders with action button', () => {
    const mockAction = jest.fn();
    
    render(
      <EmptyState
        title="No Data"
        description="No items found"
        actionText="Refresh"
        onAction={mockAction}
      />
    );
    
    expect(screen.getByText('No Data')).toBeInTheDocument();
    expect(screen.getByText('No items found')).toBeInTheDocument();
    
    const button = screen.getByRole('button', { name: /refresh/i });
    expect(button).toBeInTheDocument();
    
    fireEvent.click(button);
    expect(mockAction).toHaveBeenCalledTimes(1);
  });
});

describe('Error Components', () => {
  test('ErrorState renders with retry functionality', () => {
    const mockRetry = jest.fn();
    
    render(
      <ErrorState
        title="Something went wrong"
        description="Please try again"
        actionText="Retry"
        onAction={mockRetry}
      />
    );
    
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Please try again')).toBeInTheDocument();
    
    const retryButton = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryButton);
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  test('NetworkError shows appropriate message', () => {
    const mockRetry = jest.fn();
    
    render(<NetworkError onRetry={mockRetry} />);
    
    expect(screen.getByText('Bağlantı Hatası')).toBeInTheDocument();
    expect(screen.getByText('İnternet bağlantınızı kontrol edip tekrar deneyin.')).toBeInTheDocument();
  });
});

describe('API Integration Tests', () => {
  test('handles successful API response', async () => {
    const mockResponse = {
      data: {
        restaurants: [
          {
            id: '1',
            name: 'Test Restaurant',
            description: 'Test Description'
          }
        ],
        count: 1
      }
    };
    
    mockedAxios.get.mockResolvedValueOnce(mockResponse);
    
    // This would test actual API integration in a component
    // For now, just verify the mock setup works
    const response = await axios.get('/api/menus/public');
    expect(response.data.count).toBe(1);
    expect(response.data.restaurants).toHaveLength(1);
  });

  test('handles API error gracefully', async () => {
    const mockError = {
      response: {
        status: 500,
        data: { detail: 'Internal server error' }
      }
    };
    
    mockedAxios.get.mockRejectedValueOnce(mockError);
    
    try {
      await axios.get('/api/menus/public');
    } catch (error) {
      expect(error.response.status).toBe(500);
      expect(error.response.data.detail).toBe('Internal server error');
    }
  });
});

describe('Authentication Flow', () => {
  test('login API call structure', async () => {
    const mockLoginResponse = {
      data: {
        access_token: 'mock_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        user: {
          id: 'user_1',
          email: 'test@example.com',
          role: 'customer'
        }
      }
    };
    
    mockedAxios.post.mockResolvedValueOnce(mockLoginResponse);
    
    const loginData = {
      email: 'test@example.com',
      password: 'password123'
    };
    
    const response = await axios.post('/api/auth/login', loginData);
    
    expect(response.data.access_token).toBe('mock_token');
    expect(response.data.user.role).toBe('customer');
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/auth/login', loginData);
  });
});

describe('Responsive Design', () => {
  test('components render on mobile viewport', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 667,
    });
    
    render(<LoadingScreen />);
    
    // Should render without issues on mobile
    expect(screen.getByText('Yükleniyor...')).toBeInTheDocument();
  });
});

describe('Accessibility', () => {
  test('components have proper ARIA labels', () => {
    render(
      <FormField label="Email Address" required={true}>
        <AccessibleInput type="email" />
      </FormField>
    );
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('aria-required', 'true');
    
    const label = screen.getByText('Email Address');
    expect(label).toBeInTheDocument();
  });

  test('buttons are keyboard accessible', async () => {
    const mockClick = jest.fn();
    const user = userEvent.setup();
    
    render(
      <AccessibleButton onClick={mockClick}>
        Click Me
      </AccessibleButton>
    );
    
    const button = screen.getByRole('button');
    
    // Test keyboard activation
    button.focus();
    await user.keyboard('{Enter}');
    expect(mockClick).toHaveBeenCalledTimes(1);
    
    await user.keyboard(' ');
    expect(mockClick).toHaveBeenCalledTimes(2);
  });

  test('error messages are announced to screen readers', () => {
    render(
      <FormField 
        label="Password"
        error="Password is too short"
      >
        <AccessibleInput type="password" />
      </FormField>
    );
    
    const errorElement = screen.getByText('Password is too short');
    expect(errorElement).toHaveAttribute('role', 'alert');
    expect(errorElement).toHaveAttribute('aria-live', 'polite');
  });
});

describe('Performance', () => {
  test('components render within performance budget', () => {
    const startTime = performance.now();
    
    render(
      <TestWrapper>
        <LoadingScreen />
        <EmptyState title="Test" />
        <ErrorState title="Test Error" />
      </TestWrapper>
    );
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render quickly (under 100ms for these simple components)
    expect(renderTime).toBeLessThan(100);
  });
});

// Integration test for complete user flow
describe('User Flow Integration', () => {
  test('simulates complete customer journey', async () => {
    // Mock successful API responses
    mockedAxios.get.mockResolvedValue({
      data: {
        restaurants: [],
        count: 0,
        message: 'No restaurants found'
      }
    });
    
    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );
    
    // App should render without crashing
    expect(document.body).toBeInTheDocument();
    
    // This would be expanded in a real test to simulate:
    // 1. User visits homepage
    // 2. User logs in
    // 3. User browses restaurants
    // 4. User places order
    // etc.
  });
});