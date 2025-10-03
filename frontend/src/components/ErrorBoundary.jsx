/**
 * Comprehensive Error Boundary for Kuryecini
 * Production-ready error handling with logging and user feedback
 */

import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { toast } from 'sonner';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Generate unique error ID for tracking
    const errorId = `ERR_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId,
      retryCount: 0
    };
  }

  componentDidCatch(error, errorInfo) {
    const { onError } = this.props;
    
    // Enhanced error logging
    this.logError(error, errorInfo);
    
    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo, this.state.errorId);
    }
    
    // Store error info for detailed display
    this.setState({ errorInfo });
    
    // Handle specific error types
    this.handleSpecificErrors(error);
  }

  logError = (error, errorInfo) => {
    const errorData = {
      errorId: this.state.errorId,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: this.props.userId || 'anonymous',
      componentStack: errorInfo?.componentStack,
      errorStack: error?.stack,
      errorMessage: error?.message,
      errorName: error?.name,
      props: this.props.errorContext || {}
    };

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 Error Boundary Caught Error [${errorData.errorId}]`);
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.table(errorData);
      console.groupEnd();
    }

    // Send to error tracking service (Sentry, LogRocket, etc.)
    this.sendErrorToService(errorData);
    
    // Store in localStorage for debugging
    try {
      const existingErrors = JSON.parse(localStorage.getItem('kuryecini_errors') || '[]');
      existingErrors.push(errorData);
      
      // Keep only last 10 errors
      if (existingErrors.length > 10) {
        existingErrors.shift();
      }
      
      localStorage.setItem('kuryecini_errors', JSON.stringify(existingErrors));
    } catch (e) {
      console.warn('Failed to store error in localStorage:', e);
    }
  };

  sendErrorToService = async (errorData) => {
    try {
      // Replace with your error tracking service
      if (window.Sentry) {
        window.Sentry.captureException(new Error(errorData.errorMessage), {
          tags: {
            errorId: errorData.errorId,
            component: 'ErrorBoundary'
          },
          extra: errorData
        });
      }
      
      // Or send to custom error endpoint
      if (process.env.REACT_APP_ERROR_TRACKING_URL) {
        await fetch(process.env.REACT_APP_ERROR_TRACKING_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(errorData)
        });
      }
    } catch (e) {
      console.warn('Failed to send error to tracking service:', e);
    }
  };

  handleSpecificErrors = (error) => {
    const errorMessage = error?.message?.toLowerCase() || '';
    
    // DOM manipulation errors (usually non-critical)
    if (errorMessage.includes('removechild') || 
        errorMessage.includes('appendchild') ||
        errorMessage.includes('insertbefore')) {
      toast.warning('Görsel güncelleme hatası oluştu, tekrar deniyor...', {
        duration: 3000
      });
      return;
    }
    
    // Network errors
    if (errorMessage.includes('network') || 
        errorMessage.includes('fetch')) {
      toast.error('Bağlantı hatası. İnternet bağlantınızı kontrol edin.', {
        duration: 5000
      });
      return;
    }
    
    // Chunk loading errors (code splitting)
    if (errorMessage.includes('loading chunk') || 
        errorMessage.includes('loading css chunk')) {
      toast.error('Uygulama güncellemesi algılandı. Sayfa yenilenecek...', {
        duration: 3000
      });
      
      setTimeout(() => {
        window.location.reload();
      }, 3000);
      return;
    }
    
    // Memory errors
    if (errorMessage.includes('memory') || 
        errorMessage.includes('maximum call stack')) {
      toast.error('Uygulama yavaşladı. Sayfa yenilenecek...', {
        duration: 2000
      });
      
      setTimeout(() => {
        window.location.reload();
      }, 2000);
      return;
    }
    
    // Generic error notification
    toast.error('Beklenmedik bir hata oluştu. Lütfen tekrar deneyin.', {
      duration: 4000
    });
  };

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
    
    toast.success('Sayfa yenileniyor...', {
      duration: 2000
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReportError = () => {
    const errorData = {
      errorId: this.state.errorId,
      message: this.state.error?.message,
      stack: this.state.error?.stack,
      url: window.location.href,
      timestamp: new Date().toISOString()
    };
    
    // Open email client with error details
    const subject = `Kuryecini Hata Raporu - ${this.state.errorId}`;
    const body = `Hata Detayları:\n\n${JSON.stringify(errorData, null, 2)}`;
    const emailUrl = `mailto:support@kuryecini.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    
    window.open(emailUrl);
  };

  render() {
    if (this.state.hasError) {
      const { fallback: CustomFallback, level = 'page' } = this.props;
      
      // Use custom fallback if provided
      if (CustomFallback) {
        return (
          <CustomFallback
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            errorId={this.state.errorId}
            retry={this.handleRetry}
            reload={this.handleReload}
          />
        );
      }

      // Component-level error (smaller boundary)
      if (level === 'component') {
        return (
          <Card className="border-destructive bg-destructive/5">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-3">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                <div className="flex-1">
                  <h4 className="font-semibold text-destructive">
                    Bileşen Yüklenemedi
                  </h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Bu bölüm geçici olarak kullanılamıyor.
                  </p>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={this.handleRetry}
                  className="text-destructive border-destructive hover:bg-destructive/10"
                >
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Tekrar Dene
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      }

      // Page-level error (full page)
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <Card className="max-w-lg w-full">
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
              <CardTitle className="text-xl">
                Bir Hata Oluştu
              </CardTitle>
              <CardDescription>
                Beklenmedik bir sorun yaşandı. Size daha iyi hizmet verebilmek için bu hatayı inceliyoruz.
              </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Error ID for support */}
              <div className="bg-muted/50 rounded-md p-3 text-center">
                <p className="text-sm text-muted-foreground">Hata Kodu:</p>
                <code className="text-xs font-mono bg-background px-2 py-1 rounded border">
                  {this.state.errorId}
                </code>
              </div>

              {/* Action buttons */}
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <Button 
                  onClick={this.handleRetry}
                  className="w-full"
                  variant="default"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Tekrar Dene
                </Button>
                
                <Button 
                  onClick={this.handleReload}
                  variant="outline"
                  className="w-full"
                >
                  Sayfayı Yenile
                </Button>
              </div>

              <Button 
                onClick={this.handleGoHome}
                variant="ghost"
                className="w-full"
              >
                <Home className="h-4 w-4 mr-2" />
                Ana Sayfaya Dön
              </Button>

              {/* Report error */}
              <div className="pt-2 border-t">
                <Button 
                  onClick={this.handleReportError}
                  variant="ghost"
                  size="sm"
                  className="w-full text-muted-foreground"
                >
                  <Bug className="h-4 w-4 mr-2" />
                  Hatayı Bildir
                </Button>
              </div>

              {/* Development mode error details */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 p-3 bg-muted/50 rounded-md">
                  <summary className="cursor-pointer text-sm font-medium">
                    Geliştirici Detayları
                  </summary>
                  <pre className="mt-2 text-xs overflow-auto max-h-32 bg-background p-2 rounded border">
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC for wrapping components with error boundary
export const withErrorBoundary = (Component, options = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...options}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  
  return WrappedComponent;
};

// Hook for error reporting from components
export const useErrorHandler = () => {
  const reportError = (error, errorInfo = {}) => {
    // Create synthetic error boundary error
    const errorBoundary = new ErrorBoundary({});
    errorBoundary.logError(error, errorInfo);
    errorBoundary.handleSpecificErrors(error);
  };

  return { reportError };
};

// Async error boundary for handling promise rejections
export class AsyncErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  componentDidMount() {
    window.addEventListener('unhandledrejection', this.handleUnhandledRejection);
  }

  componentWillUnmount() {
    window.removeEventListener('unhandledrejection', this.handleUnhandledRejection);
  }

  handleUnhandledRejection = (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    
    // Don't show UI for network errors in background
    if (event.reason?.message?.includes('fetch') || 
        event.reason?.name === 'AbortError') {
      return;
    }
    
    toast.error('Arka plan işlemi başarısız oldu. Lütfen tekrar deneyin.', {
      duration: 4000
    });
    
    // Prevent default browser error handling
    event.preventDefault();
  };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Async Error Boundary:', error, errorInfo);
  }

  render() {
    return this.props.children;
  }
}

export default ErrorBoundary;