import React, { useEffect, useRef, useState } from 'react';

const OpenStreetMap = ({ 
  center = [41.0082, 28.9784], 
  zoom = 13, 
  height = "400px",
  markers = [],
  onMarkerClick = null,
  courierLocation = null,
  showDirectionsProp = false
}) => {
  const mapRef = useRef(null);
  const [mapInstance, setMapInstance] = useState(null);
  const [directionsVisible, setDirectionsVisible] = useState(false);
  const [routeData, setRouteData] = useState(null);

  useEffect(() => {
    // Initialize map with vanilla JavaScript (no React-leaflet dependency)
    if (mapRef.current && !mapInstance) {
      initializeMap();
    }
  }, []);

  useEffect(() => {
    if (mapInstance) {
      updateMapMarkers();
      // Fetch route if courier location and delivery markers exist
      if (courierLocation && markers.length > 0) {
        fetchRouteData();
      }
    }
  }, [markers, courierLocation, mapInstance]);

  const fetchRouteData = async () => {
    if (!courierLocation || markers.length === 0) return;
    
    try {
      // Use the first delivery marker as destination
      const destination = markers.find(m => m.type === 'delivery') || markers[0];
      
      // OSRM API for route calculation (free)
      const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${courierLocation.lng},${courierLocation.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson`;
      
      const response = await fetch(osrmUrl);
      const data = await response.json();
      
      if (data.routes && data.routes.length > 0) {
        const route = data.routes[0];
        setRouteData({
          coordinates: route.geometry.coordinates,
          distance: route.distance, // meters
          duration: route.duration  // seconds
        });
      }
    } catch (error) {
      console.error('Route fetch error:', error);
      setRouteData(null);
    }
  };

  const initializeMap = () => {
    const mapContainer = mapRef.current;
    
    // Create simple map using OpenStreetMap tiles
    const mapHTML = `
      <div style="position: relative; width: 100%; height: 100%; background: #f0f0f0; border-radius: 8px;">
        <iframe
          width="100%"
          height="100%"
          frameborder="0"
          scrolling="no"
          marginheight="0"
          marginwidth="0"
          src="https://www.openstreetmap.org/export/embed.html?bbox=${center[1]-0.01},${center[0]-0.01},${center[1]+0.01},${center[0]+0.01}&layer=mapnik&marker=${center[0]},${center[1]}"
          style="border-radius: 8px;">
        </iframe>
        
        <!-- Custom overlay for markers and controls -->
        <div id="map-overlay" style="
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
          z-index: 10;
        ">
          <div id="markers-container" style="position: relative; width: 100%; height: 100%;">
            ${renderMarkersOverlay()}
          </div>
        </div>
        
        <!-- Controls -->
        <div style="
          position: absolute;
          bottom: 10px;
          right: 10px;
          z-index: 20;
          background: white;
          padding: 8px;
          border-radius: 4px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          pointer-events: auto;
        ">
          <button 
            onclick="window.toggleDirections && window.toggleDirections()"
            style="
              background: #007cba;
              color: white;
              border: none;
              padding: 6px 12px;
              border-radius: 4px;
              cursor: pointer;
              font-size: 12px;
            "
          >
            🛣️ Yol Tarifi
          </button>
        </div>
      </div>
    `;
    
    mapContainer.innerHTML = mapHTML;
    setMapInstance(true);
  };

  const renderMarkersOverlay = () => {
    let overlayHTML = '';
    
    // Route line (drawn first, under markers)
    if (routeData && courierLocation && markers.length > 0) {
      const destination = markers.find(m => m.type === 'delivery') || markers[0];
      
      overlayHTML += `
        <svg style="
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 5;
          pointer-events: none;
        ">
          <defs>
            <pattern id="routePattern" patternUnits="userSpaceOnUse" width="10" height="10">
              <rect width="10" height="10" fill="#3b82f6"/>
              <rect width="5" height="10" fill="#1d4ed8"/>
            </pattern>
          </defs>
          <line
            x1="48%" y1="45%"
            x2="${45 + (markers.indexOf(destination) * 3)}%" y2="${40 + (markers.indexOf(destination) * 5)}%"
            stroke="#3b82f6"
            stroke-width="4"
            stroke-dasharray="8,4"
            opacity="0.8"
          />
          <line
            x1="48%" y1="45%"
            x2="${45 + (markers.indexOf(destination) * 3)}%" y2="${40 + (markers.indexOf(destination) * 5)}%"
            stroke="#1d4ed8"
            stroke-width="2"
            stroke-dasharray="8,4"
            opacity="1"
          />
        </svg>
      `;
    }
    
    // Courier location marker
    if (courierLocation) {
      overlayHTML += `
        <div style="
          position: absolute;
          top: 45%;
          left: 48%;
          transform: translate(-50%, -50%);
          z-index: 15;
          animation: pulse 2s infinite;
        ">
          <div style="
            background: #10b981;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 0 0 2px #10b981;
          "></div>
          <div style="
            position: absolute;
            top: -30px;
            left: 50%;
            transform: translateX(-50%);
            background: #10b981;
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            white-space: nowrap;
          ">
            🚴 Kurye
          </div>
        </div>
      `;
    }
    
    // Package/Order markers
    markers.forEach((marker, index) => {
      const topPos = 40 + (index * 5); // Distribute markers
      const leftPos = 45 + (index * 3);
      
      overlayHTML += `
        <div 
          style="
            position: absolute;
            top: ${topPos}%;
            left: ${leftPos}%;
            transform: translate(-50%, -50%);
            z-index: 12;
            cursor: pointer;
          "
          onclick="window.handleMarkerClick && window.handleMarkerClick('${marker.id || index}')"
        >
          <div style="
            background: ${marker.type === 'delivery' ? '#f59e0b' : '#ef4444'};
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
          "></div>
          <div style="
            position: absolute;
            top: -28px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            white-space: nowrap;
            display: none;
          " class="marker-tooltip">
            📦 ${marker.title || 'Paket'}
          </div>
        </div>
      `;
    });
    
    return overlayHTML;
  };

  const updateMapMarkers = () => {
    if (mapRef.current) {
      const markersContainer = mapRef.current.querySelector('#markers-container');
      if (markersContainer) {
        markersContainer.innerHTML = renderMarkersOverlay();
      }
    }
  };

  const showDirections = () => {
    setDirectionsVisible(true);
    
    // Enhanced directions display with real route data
    const distance = routeData ? (routeData.distance / 1000).toFixed(1) : '1.2';
    const duration = routeData ? Math.ceil(routeData.duration / 60) : '8-12';
    
    const directionsHTML = `
      <div style="
        position: absolute;
        top: 10px;
        left: 10px;
        background: white;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        max-width: 220px;
        z-index: 25;
        font-size: 12px;
      ">
        <div style="font-weight: bold; margin-bottom: 8px; color: #3b82f6;">
          🛣️ Aktif Rota
        </div>
        <div style="color: #666; line-height: 1.4;">
          ${routeData ? `
            <div style="background: #f0f9ff; padding: 6px; border-radius: 4px; margin-bottom: 8px;">
              📍 Mesafe: <strong>${distance} km</strong><br/>
              ⏱️ Süre: <strong>~${duration} dakika</strong>
            </div>
            <div style="font-size: 11px;">
              1. Mevcut konumdan çık<br/>
              2. Ana yol üzerinden ${distance}km<br/>
              3. Teslimat adresine ulaş
            </div>
          ` : `
            <div>
              1. Konum bilgisi bekleniyor...<br/>
              2. Rota hesaplanıyor...<br/>
              3. Yönlendirme hazırlanıyor
            </div>
          `}
        </div>
        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
          <div style="font-size: 10px; color: #6b7280; text-align: center;">
            🚴 Gerçek zamanlı takip aktif
          </div>
        </div>
        <button onclick="window.hideDirections && window.hideDirections()" style="
          position: absolute;
          top: 4px;
          right: 4px;
          background: none;
          border: none;
          font-size: 16px;
          cursor: pointer;
          color: #6b7280;
        ">×</button>
      </div>
    `;
    
    const overlay = mapRef.current?.querySelector('#map-overlay');
    if (overlay) {
      const directionsDiv = document.createElement('div');
      directionsDiv.id = 'directions-panel';
      directionsDiv.innerHTML = directionsHTML;
      overlay.appendChild(directionsDiv);
    }
  };

  const hideDirections = () => {
    setDirectionsVisible(false);
    const directionsPanel = mapRef.current?.querySelector('#directions-panel');
    if (directionsPanel) {
      directionsPanel.remove();
    }
  };

  useEffect(() => {
    // Global functions for map interactions
    window.toggleDirections = () => {
      if (directionsVisible) {
        hideDirections();
      } else {
        showDirections();
      }
    };

    window.hideDirections = hideDirections;

    window.handleMarkerClick = (markerId) => {
      if (onMarkerClick) {
        onMarkerClick(markerId);
      } else {
        showDirections();
      }
    };

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.2); }
        100% { transform: translate(-50%, -50%) scale(1); }
      }
      
      .marker-tooltip:hover {
        display: block !important;
      }
    `;
    document.head.appendChild(style);

    return () => {
      window.toggleDirections = null;
      window.hideDirections = null;
      window.handleMarkerClick = null;
    };
  }, [directionsVisible, onMarkerClick]);

  return (
    <div 
      ref={mapRef} 
      style={{ 
        width: '100%', 
        height: height, 
        borderRadius: '8px',
        overflow: 'hidden'
      }}
    >
      {/* Loading placeholder */}
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f3f4f6',
        color: '#6b7280'
      }}>
        <div className="text-center">
          <div className="text-2xl mb-2">🗺️</div>
          <p>Harita yükleniyor...</p>
        </div>
      </div>
    </div>
  );
};

export default OpenStreetMap;