import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Button } from './components/ui/button';

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const LeafletMap = ({ 
  center = [39.925533, 32.866287], // Ankara center
  zoom = 10, 
  height = "400px",
  markers = [], 
  onMapClick = null,
  className = "",
  showLocationButton = false,
  courierMode = false,
  onLocationUpdate = null,
  routePolyline = null
}) => {
  const [map, setMap] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [watchId, setWatchId] = useState(null);
  const [locationError, setLocationError] = useState(null);

  // Custom icons for different marker types
  const icons = {
    user: L.divIcon({
      html: `<div style="background: #3B82F6; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 4px solid white; box-shadow: 0 3px 12px rgba(59, 130, 246, 0.4); position: relative;">
               <span style="color: white; font-size: 18px;">📍</span>
               <div style="position: absolute; top: -5px; right: -5px; background: #10B981; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; animation: pulse 2s infinite;"></div>
             </div>`,
      className: 'user-location-marker',
      iconSize: [35, 35],
      iconAnchor: [17, 17],
      popupAnchor: [0, -20]
    }),
    customer: L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    }),
    business: L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    }),
    courier: L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      iconSize: [30, 46],
      iconAnchor: [15, 46],
      popupAnchor: [1, -34],
      shadowSize: [46, 46]
    }),
    delivery: L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    }),
    package: L.divIcon({
      html: `<div style="background: #8B5CF6; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
               <span style="color: white; font-size: 16px;">📦</span>
             </div>`,
      className: 'package-marker',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15]
    }),
    pickup: L.divIcon({
      html: `<div style="background: #10B981; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
               <span style="color: white; font-size: 14px;">🏪</span>
             </div>`,
      className: 'pickup-marker',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
      popupAnchor: [0, -15]
    }),
    myLocation: L.divIcon({
      html: `<div style="background: #3B82F6; width: 20px; height: 20px; border-radius: 50%; border: 4px solid white; box-shadow: 0 0 0 2px #3B82F6, 0 2px 8px rgba(0,0,0,0.3); animation: pulse 2s infinite;">
             </div>
             <style>
               @keyframes pulse {
                 0% { transform: scale(1); opacity: 1; }
                 50% { transform: scale(1.2); opacity: 0.7; }
                 100% { transform: scale(1); opacity: 1; }
               }
             </style>`,
      className: 'my-location-marker',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
      popupAnchor: [0, -14]
    })
  };

  // Location tracking functions
  const startLocationTracking = () => {
    if (!navigator.geolocation) {
      setLocationError('Konum servisi desteklenmiyor');
      return;
    }

    const options = {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000 // 1 minute
    };

    const successCallback = (position) => {
      const { latitude, longitude } = position.coords;
      const newLocation = { lat: latitude, lng: longitude };
      
      setUserLocation(newLocation);
      setLocationError(null);
      
      // Notify parent component
      if (onLocationUpdate) {
        onLocationUpdate(newLocation);
      }
      
      // Center map on user location if first time
      if (map && !userLocation) {
        map.setView([latitude, longitude], 16);
      }
    };

    const errorCallback = (error) => {
      console.error('Konum hatası:', error);
      switch (error.code) {
        case error.PERMISSION_DENIED:
          setLocationError('Konum izni verilmedi');
          break;
        case error.POSITION_UNAVAILABLE:
          setLocationError('Konum bilgisi alınamadı');
          break;
        case error.TIMEOUT:
          setLocationError('Konum alma zaman aşımı');
          break;
        default:
          setLocationError('Bilinmeyen konum hatası');
      }
    };

    // Start watching position
    const id = navigator.geolocation.watchPosition(
      successCallback,
      errorCallback,
      options
    );
    
    setWatchId(id);
  };

  const stopLocationTracking = () => {
    if (watchId) {
      navigator.geolocation.clearWatch(watchId);
      setWatchId(null);
    }
  };

  const centerOnMyLocation = () => {
    if (userLocation && map) {
      map.setView([userLocation.lat, userLocation.lng], 16);
    } else {
      startLocationTracking();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopLocationTracking();
    };
  }, []);

  // Auto-start location tracking in courier mode
  useEffect(() => {
    if (courierMode) {
      startLocationTracking();
    }
  }, [courierMode]);

  // Handle map click events
  const MapClickHandler = () => {
    useEffect(() => {
      if (!map) return;

      const handleClick = (e) => {
        if (onMapClick) {
          onMapClick({
            lat: e.latlng.lat,
            lng: e.latlng.lng
          });
        }
      };

      map.on('click', handleClick);

      return () => {
        map.off('click', handleClick);
      };
    }, [map]);

    return null;
  };

  return (
    <div className={`relative ${className}`} style={{ height }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        ref={setMap}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Route polyline */}
        {routePolyline && routePolyline.length > 0 && (
          <Polyline
            positions={routePolyline}
            color="blue"
            weight={4}
            opacity={0.7}
            dashArray="10, 5"
          />
        )}
        
        {/* User's current location */}
        {userLocation && (
          <Marker
            position={[userLocation.lat, userLocation.lng]}
            icon={icons.myLocation}
          >
            <Popup>
              <div>
                <h3 className="font-semibold text-blue-600">📍 Konumunuz</h3>
                <p className="text-sm">Canlı konum takibi aktif</p>
                <p className="text-xs text-gray-600">
                  Lat: {userLocation.lat.toFixed(6)}<br/>
                  Lng: {userLocation.lng.toFixed(6)}
                </p>
              </div>
            </Popup>
          </Marker>
        )}
        
        {/* Other markers */}
        {markers.map((marker, index) => {
          const icon = icons[marker.type] || icons.customer;
          
          return (
            <Marker
              key={index}
              position={[marker.lat, marker.lng]}
              icon={icon}
            >
              {marker.popup && (
                <Popup>
                  <div>
                    {marker.title && <h3 className="font-semibold">{marker.title}</h3>}
                    {marker.description && <p className="text-sm">{marker.description}</p>}
                    {marker.address && <p className="text-xs text-gray-600 mt-1">{marker.address}</p>}
                    {marker.distance && (
                      <p className="text-xs text-blue-600 mt-1">
                        📏 Mesafe: {marker.distance}
                      </p>
                    )}
                    {marker.estimatedTime && (
                      <p className="text-xs text-green-600">
                        ⏱️ Tahmini: {marker.estimatedTime}
                      </p>
                    )}
                    {marker.orderValue && (
                      <p className="text-sm font-semibold text-purple-600 mt-1">
                        💰 {marker.orderValue}
                      </p>
                    )}
                    {marker.onNavigate && (
                      <Button 
                        size="sm" 
                        className="mt-2 w-full"
                        onClick={() => marker.onNavigate(marker)}
                      >
                        🧭 Yol Tarifi Al
                      </Button>
                    )}
                  </div>
                </Popup>
              )}
            </Marker>
          );
        })}
        
        {onMapClick && <MapClickHandler />}
      </MapContainer>
      
      {/* Location button */}
      {showLocationButton && (
        <div className="absolute bottom-4 right-4 z-[1000]">
          <Button
            onClick={centerOnMyLocation}
            className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
            size="sm"
          >
            {watchId ? '🔄 Konum Takibi' : '📍 Konumumu Bul'}
          </Button>
        </div>
      )}
      
      {/* Location error */}
      {locationError && (
        <div className="absolute top-4 left-4 bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded shadow-lg z-[1000]">
          <p className="text-sm">⚠️ {locationError}</p>
        </div>
      )}
      
      {/* Map Legend */}
      {markers.length > 0 && (
        <div className="absolute top-2 right-2 bg-white p-3 rounded-lg shadow-lg z-[1000] max-w-xs">
          <div className="text-xs space-y-2">
            <div className="font-semibold text-gray-800 mb-2">Harita Sembolleri</div>
            {courierMode ? (
              <>
                <div className="flex items-center space-x-2">
                  <div className="text-lg">📦</div>
                  <span>Paket Teslim</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="text-lg">🏪</div>
                  <span>Paket Alım</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                  <span>Konumunuz</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 border-2 border-blue-500 rounded-full"></div>
                  <span>Yol Tarifi</span>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span>Müşteri</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span>İşletme</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                  <span>Kurye</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span>Teslimat</span>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LeafletMap;