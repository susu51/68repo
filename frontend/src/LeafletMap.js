import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

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
  className = ""
}) => {
  const [map, setMap] = useState(null);

  // Custom icons for different marker types
  const icons = {
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
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    }),
    delivery: L.icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    })
  };

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
                    {marker.address && <p className="text-xs text-gray-600">{marker.address}</p>}
                  </div>
                </Popup>
              )}
            </Marker>
          );
        })}
        
        {onMapClick && <MapClickHandler />}
      </MapContainer>
      
      {/* Map Legend */}
      {markers.length > 0 && (
        <div className="absolute top-2 right-2 bg-white p-2 rounded shadow-lg z-[1000]">
          <div className="text-xs space-y-1">
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
          </div>
        </div>
      )}
    </div>
  );
};

export default LeafletMap;