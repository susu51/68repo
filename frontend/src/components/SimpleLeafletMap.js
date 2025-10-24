import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-hub.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

// Custom icon creator
const createCustomIcon = (business) => {
  const count = business.active_order_count || 0;
  const iconUrl = business.icon_url || 'https://cdn-icons-png.flaticon.com/512/2830/2830284.png';
  
  const html = `
    <div style="position:relative;width:48px;height:48px;">
      <div style="width:48px;height:48px;border-radius:50%;overflow:hidden;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);background:white;">
        <img src="${iconUrl}" style="width:100%;height:100%;object-fit:cover;" onerror="this.src='https://cdn-icons-png.flaticon.com/512/2830/2830284.png'" />
      </div>
      ${count > 0 ? `<div style="position:absolute;top:-4px;right:-4px;min-width:20px;height:20px;padding:0 6px;border-radius:10px;background:#ef4444;color:white;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 4px rgba(0,0,0,0.3);border:2px solid white;">${count > 9 ? '9+' : count}</div>` : ''}
    </div>
  `;

  return L.divIcon({
    className: 'custom-marker-icon',
    html: html,
    iconSize: [48, 48],
    iconAnchor: [24, 48],
    popupAnchor: [0, -48]
  });
};

// Recenter helper
function ChangeView({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.setView(center, 13);
  }, [center, map]);
  return null;
}

export const SimpleLeafletMap = ({ onBusinessClick }) => {
  const [businesses, setBusinesses] = useState([]);
  const [courierLocation, setCourierLocation] = useState([39.9334, 32.8597]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const style = document.createElement('style');
    style.innerHTML = '.custom-marker-icon { background: transparent !important; border: none !important; }';
    document.head.appendChild(style);

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setCourierLocation([pos.coords.latitude, pos.coords.longitude]),
        () => {}
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
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: '100%' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '4px' }}>Paket Haritası</h2>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            {businesses.reduce((sum, b) => sum + b.active_order_count, 0)} hazır paket • {businesses.length} işletme
          </p>
        </div>
        <button 
          onClick={fetchBusinesses} 
          disabled={loading}
          style={{
            padding: '8px 16px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            background: 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            fontWeight: '500'
          }}
        >
          {loading ? '🔄 Yükleniyor...' : '🔄 Yenile'}
        </button>
      </div>

      <div style={{ height: '600px', borderRadius: '8px', overflow: 'hidden', border: '1px solid #e5e7eb' }}>
        <MapContainer 
          center={courierLocation} 
          zoom={13} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap'
          />
          <ChangeView center={courierLocation} />

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
            <Popup><strong>📍 Konumunuz</strong></Popup>
          </Marker>

          {businesses.map((business) => {
            if (!business.location?.lat || !business.location?.lng) return null;
            return (
              <Marker
                key={business.id}
                position={[business.location.lat, business.location.lng]}
                icon={createCustomIcon(business)}
                eventHandlers={{ click: () => onBusinessClick && onBusinessClick(business) }}
              >
                <Popup>
                  <div style={{ minWidth: '200px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <img 
                        src={business.icon_url || 'https://cdn-icons-png.flaticon.com/512/2830/2830284.png'}
                        alt={business.name}
                        style={{ width: '48px', height: '48px', borderRadius: '50%', border: '2px solid #e5e7eb', objectFit: 'cover' }}
                      />
                      <div>
                        <strong style={{ fontSize: '16px' }}>{business.name}</strong>
                        {business.active_order_count > 0 && (
                          <span style={{ marginLeft: '8px', padding: '2px 8px', borderRadius: '10px', background: '#ef4444', color: 'white', fontSize: '11px', fontWeight: '700' }}>
                            {business.active_order_count} paket
                          </span>
                        )}
                      </div>
                    </div>
                    <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '8px' }}>
                      📍 {business.district}, {business.city}
                    </div>
                    <button
                      onClick={() => onBusinessClick && onBusinessClick(business)}
                      style={{ width: '100%', padding: '8px', background: '#22c55e', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: '600' }}
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

export default SimpleLeafletMap;
