import React from 'react';
import toast from 'react-hot-toast';

class FoodOrderErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to console for debugging
    console.error('FoodOrderSystem Error Boundary caught an error:', error, errorInfo);
    
    // Show user-friendly message
    if (error.message?.includes('removeChild') || error.message?.includes('appendChild')) {
      console.warn('DOM manipulation error caught by boundary:', error.message);
      // Don't show toast for DOM errors as they're usually non-critical
    } else {
      toast.error('Bir hata oluştu. Sayfa yeniden yükleniyor...');
      // Reload the page after a brief delay for serious errors
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    }
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI for DOM manipulation errors - just retry rendering
      if (this.state.error?.message?.includes('removeChild') || 
          this.state.error?.message?.includes('appendChild')) {
        // For DOM errors, try to recover by re-rendering
        setTimeout(() => {
          this.setState({ hasError: false, error: null });
        }, 100);
        
        return (
          <div className="flex items-center justify-center p-8">
            <div className="text-center">
              <div className="text-2xl mb-2">🔄</div>
              <p className="text-gray-600">Yükleniyor...</p>
            </div>
          </div>
        );
      }
      
      // For other errors, show a proper error state
      return (
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold mb-2">Bir sorun oluştu</h3>
            <p className="text-gray-600 mb-4">Restoran menüsü yüklenirken bir hata meydana geldi.</p>
            <button 
              onClick={() => this.setState({ hasError: false, error: null })}
              className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600"
            >
              Tekrar Dene
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default FoodOrderErrorBoundary;