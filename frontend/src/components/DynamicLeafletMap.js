import React, { Suspense, lazy } from 'react';
import { Card, CardContent } from './ui/card';

// Lazy load the LeafletMap component for SSR/CSR compatibility
const LeafletMap = lazy(() => import('../LeafletMap'));

const MapLoadingFallback = ({ height = "400px" }) => (
  <div 
    className="flex items-center justify-center bg-gray-100 rounded-lg"
    style={{ height }}
  >
    <div className="text-center space-y-3">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p className="text-gray-600">Harita yükleniyor...</p>
      <div className="text-xs text-gray-500">
        🗺️ Leaflet haritası başlatılıyor
      </div>
    </div>
  </div>
);

const MapErrorFallback = ({ height = "400px", onRetry = null }) => (
  <div 
    className="flex items-center justify-center bg-red-50 border border-red-200 rounded-lg"
    style={{ height }}
  >
    <div className="text-center space-y-3 p-4">
      <div className="text-red-600 text-4xl">⚠️</div>
      <h3 className="font-semibold text-red-800">Harita Yüklenemedi</h3>
      <p className="text-red-600 text-sm">
        Leaflet haritası yüklenirken bir hata oluştu
      </p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
        >
          Tekrar Dene
        </button>
      )}
    </div>
  </div>
);

class MapErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('LeafletMap Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <MapErrorFallback 
          height={this.props.height} 
          onRetry={() => {
            this.setState({ hasError: false });
            window.location.reload();
          }}
        />
      );
    }

    return this.props.children;
  }
}

const DynamicLeafletMap = (props) => {
  return (
    <MapErrorBoundary height={props.height}>
      <Suspense fallback={<MapLoadingFallback height={props.height} />}>
        <LeafletMap {...props} />
      </Suspense>
    </MapErrorBoundary>
  );
};

export default DynamicLeafletMap;