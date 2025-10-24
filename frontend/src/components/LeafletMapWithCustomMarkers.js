import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RefreshCw } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-hub.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

// Custom icon creator with badge
const createCustomIcon = (business) => {
  const count = business.active_order_count || 0;
  const iconUrl = business.icon_url || 'https://cdn-icons-png.flaticon.com/512/2830/2830284.png'; // Package icon
  
  const html = `
    <div class="custom-marker-wrapper">
      <div class="custom-marker">
        <img src="${iconUrl}" alt="${business.name}" onerror="this.src='https://cdn-icons-png.flaticon.com/512/2830/2830284.png'" />
      </div>
      ${count > 0 ? `
        <div class="marker-badge">
          ${count > 9 ? '9+' : count}
        </div>
      ` : ''}
    </div>
  `;

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: html,
    iconSize: [48, 48],
    iconAnchor: [24, 48],
    popupAnchor: [0, -48]
  });
};

// Component to recenter map when courier location changes
function ChangeView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
}

export const LeafletMapWithCustomMarkers = ({ onBusinessClick }) => {
  const [businesses, setBusinesses] = useState([]);
  const [courierLocation, setCourierLocation] = useState([39.9334, 32.8597]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Inject custom CSS for markers
    const style = document.createElement('style');
    style.innerHTML = `
      .custom-leaflet-marker {
        background: transparent !important;
        border: none !important;
      }
      
      .custom-marker-wrapper {
        position: relative;
        width: 48px;
        height: 48px;
      }
      
      .custom-marker {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        overflow: hidden;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        background: white;
        cursor: pointer;
        transition: transform 0.2s;
      }
      
      .custom-marker:hover {
        transform: scale(1.1);
      }
      
      .custom-marker img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }
      
      .marker-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        min-width: 20px;
        height: 20px;
        padding: 0 6px;
        border-radius: 10px;
        background: #ef4444;
        color: white;
        font-size: 11px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        border: 2px solid white;
      }
      
      .leaflet-popup-content-wrapper {
        border-radius: 8px;
      }
      
      .leaflet-popup-content {
        margin: 12px;
        font-family: system-ui, -apple-system, sans-serif;
      }
    `;
    document.head.appendChild(style);

    // Get courier location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCourierLocation([position.coords.latitude, position.coords.longitude]);
        },
        (error) => {
          console.error('Location error:', error);
        }
      );
    }

    fetchBusinesses();
    const interval = setInterval(fetchBusinesses, 30000);
    return () => {
      clearInterval(interval);
      document.head.removeChild(style);
    };
  }, []);

  const fetchBusinesses = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/map/businesses`, {
        method: 'GET',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setBusinesses(data);
        console.log('📍 Map businesses:', data);
      }
    } catch (error) {
      console.error('❌ Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Paket Haritası</h2>
          <p className="text-muted-foreground">
            {businesses.reduce((sum, b) => sum + b.active_order_count, 0)} hazır paket • {businesses.length} işletme
          </p>
        </div>
        <button 
          onClick={fetchBusinesses} 
          disabled={loading}
          style={{
            padding: '6px 12px',
            border: '1px solid #e5e7eb',
            borderRadius: '6px',
            background: 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '14px'
          }}
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Yenile
        </button>
      </div>

      {/* Leaflet Map */}
      <div style={{ height: '600px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e5e7eb' }}>
        <MapContainer 
          center={courierLocation} 
          zoom={13} 
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <ChangeView center={courierLocation} zoom={13} />

          {/* Courier Location Marker */}
          <Marker 
            position={courierLocation}
            icon={L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
              shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34],
              shadowSize: [41, 41]
            })}
          >
            <Popup>
              <div>
                <strong>📍 Konumunuz</strong>
              </div>
            </Popup>
          </Marker>

          {/* Business Markers */}
          {businesses.map((business) => {
            if (!business.location?.lat || !business.location?.lng) return null;
            
            return (
              <Marker
                key={business.id}
                position={[business.location.lat, business.location.lng]}
                icon={createCustomIcon(business)}
                eventHandlers={{
                  click: () => {
                    console.log('Clicked business:', business);
                    if (onBusinessClick) {
                      onBusinessClick(business);
                    }
                  }
                }}
              >
                <Popup>
                  <div style={{ minWidth: '200px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <img 
                        src={business.icon_url || 'https://cdn-icons-png.flaticon.com/512/2830/2830284.png'}
                        alt={business.name}
                        style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '50%',
                          border: '2px solid #e5e7eb',
                          objectFit: 'cover'
                        }}
                      />
                      <div style={{ flex: 1 }}>
                        <strong style={{ fontSize: '16px' }}>{business.name}</strong>
                        {business.active_order_count > 0 && (
                          <div style={{
                            display: 'inline-block',
                            marginLeft: '8px',
                            padding: '2px 8px',
                            borderRadius: '10px',
                            background: '#ef4444',
                            color: 'white',
                            fontSize: '11px',
                            fontWeight: '700'
                          }}>
                            {business.active_order_count} paket
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '8px' }}>
                      📍 {business.district}, {business.city}
                    </div>
                    <button
                      onClick={() => onBusinessClick && onBusinessClick(business)}
                      style={{
                        width: '100%',
                        padding: '8px 16px',
                        marginTop: '8px',
                        background: '#22c55e',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '14px',
                        fontWeight: '600'
                      }}
                    >
                      Siparişleri Gör
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
};

export default LeafletMapWithCustomMarkers;
