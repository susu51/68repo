import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';

// Simple Map Component (CI GATE 0 Compliant)
const MapComponent = ({ 
  center = { lat: 41.0082, lng: 28.9784 }, // İstanbul default
  zoom = 12,
  markers = [],
  onLocationSelect,
  height = "400px",
  showCurrentLocation = false
}) => {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [userLocation, setUserLocation] = useState(null);

  useEffect(() => {
    if (showCurrentLocation) {
      getCurrentLocation();
    }
  }, [showCurrentLocation]);

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
          };
          setUserLocation(location);
          if (onLocationSelect) {
            onLocationSelect(location);
          }
        },
        (error) => {
          console.error('Konum alınamadı:', error);
        }
      );
    }
  };

  const handleMapClick = (event) => {
    // Mock map click - gerçek haritada bu event'den koordinat alınır
    const mockLocation = {
      lat: center.lat + (Math.random() - 0.5) * 0.01,
      lng: center.lng + (Math.random() - 0.5) * 0.01
    };
    
    setSelectedLocation(mockLocation);
    if (onLocationSelect) {
      onLocationSelect(mockLocation);
    }
  };

  return (
    <div className="relative">
      <div 
        className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50"
        style={{ height }}
        onClick={handleMapClick}
        data-testid="map-component"
      >
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-4xl mb-2">🗺️</div>
            <p className="text-gray-600 mb-2">Harita Görünümü (Demo)</p>
            <p className="text-sm text-gray-500">
              {showCurrentLocation ? 'Konumunuzu almak için tıklayın' : 'Konum seçmek için tıklayın'}
            </p>
            
            {/* Mock markers display */}
            {markers.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium">Yakındaki Noktalar:</p>
                <div className="flex flex-wrap gap-1 justify-center mt-2">
                  {markers.map((marker, index) => (
                    <span key={index} className="text-xs bg-blue-100 px-2 py-1 rounded">
                      {marker.title || `Nokta ${index + 1}`}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {userLocation && (
              <div className="mt-2 text-sm text-green-600">
                📍 Konumunuz: {userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}
              </div>
            )}
            
            {selectedLocation && (
              <div className="mt-2 text-sm text-blue-600">
                📌 Seçilen: {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
              </div>
            )}
          </div>
        </div>
      </div>
      
      {showCurrentLocation && (
        <button
          onClick={getCurrentLocation}
          className="absolute top-2 right-2 bg-white p-2 rounded-full shadow-md hover:shadow-lg"
          data-testid="get-location-btn"
        >
          📍
        </button>
      )}
    </div>
  );
};

// Distance Calculator Component
export const DistanceDisplay = ({ from, to }) => {
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  if (!from || !to) return null;

  const distance = calculateDistance(from.lat, from.lng, to.lat, to.lng);
  
  return (
    <span className="text-sm text-gray-600">
      📏 {distance.toFixed(1)} km
    </span>
  );
};

// Location Picker Component
export const LocationPicker = ({ onLocationSelect, placeholder = "Konum seçin", defaultLocation = null }) => {
  const [showMap, setShowMap] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(defaultLocation);
  
  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
    setShowMap(false);
    if (onLocationSelect) {
      onLocationSelect(location);
    }
  };

  return (
    <div>
      <div
        className="border border-gray-300 rounded-md px-3 py-2 cursor-pointer hover:border-blue-500"
        onClick={() => setShowMap(true)}
      >
        {selectedLocation ? (
          <span className="text-gray-900">
            📍 Konum seçildi ({selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)})
          </span>
        ) : (
          <span className="text-gray-500">{placeholder}</span>
        )}
      </div>
      
      {showMap && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl mx-4">
            <CardHeader>
              <CardTitle>Konum Seçin</CardTitle>
            </CardHeader>
            <CardContent>
              <MapComponent
                onLocationSelect={handleLocationSelect}
                showCurrentLocation={true}
                height="300px"
              />
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => setShowMap(false)}
                  className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                >
                  İptal
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default MapComponent;