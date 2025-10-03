import React from 'react';

class GlobalErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Check if this is a DOM manipulation error
    const errorMessage = error.toString().toLowerCase();
    const isDOMError = errorMessage.includes('removechild') || 
                       errorMessage.includes('removechildfromcontainer') ||
                       errorMessage.includes('commitdeletioneffects') ||
                       errorMessage.includes('node');

    if (isDOMError) {
      console.warn('🔧 DOM Error Caught by Error Boundary:', {
        error: error.toString(),
        errorInfo: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        suppressed: true
      });
      
      // Reset the error boundary and continue
      setTimeout(() => {
        this.setState({ hasError: false, error: null, errorInfo: null });
      }, 100);
      
      return;
    }

    // For non-DOM errors, log normally
    console.error('Error Boundary Caught:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError && this.state.error && !this.state.error.toString().toLowerCase().includes('removechild')) {
      // Fallback UI for non-DOM errors
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center p-8">
            <h2 className="text-xl font-bold text-red-600 mb-4">Bir hata oluştu</h2>
            <p className="text-gray-600 mb-4">Sayfa yeniden yükleniyor...</p>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-blue-500 text-white px-4 py-2 rounded"
            >
              Sayfayı Yenile
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default GlobalErrorBoundary;