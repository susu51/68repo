import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-hub.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

export const PureLeafletMap = ({ onBusinessClick }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const [businesses, setBusinesses] = useState([]);
  const [courierLocation, setCourierLocation] = useState([39.9334, 32.8597]);
  const [loading, setLoading] = useState(false);

  // Initialize map
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // Create map
    const map = L.map(mapRef.current).setView(courierLocation, 13);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19
    }).addTo(map);

    mapInstanceRef.current = map;

    // Get courier location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const newLocation = [pos.coords.latitude, pos.coords.longitude];
          setCourierLocation(newLocation);
          map.setView(newLocation, 13);
        },
        () => console.log('Location not available')
      );
    }

    // Fetch businesses
    fetchBusinesses();
    const interval = setInterval(fetchBusinesses, 30000);

    return () => {
      clearInterval(interval);
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update markers when businesses or courierLocation changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add courier marker
    const courierMarker = L.marker(courierLocation, {
      icon: L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
      })
    }).addTo(mapInstanceRef.current);
    courierMarker.bindPopup('<strong>📍 Konumunuz</strong>');
    markersRef.current.push(courierMarker);

    // Add business markers
    businesses.forEach((business) => {
      if (!business.location?.lat || !business.location?.lng) return;

      const count = business.active_order_count || 0;
      const iconUrl = business.icon_url || 'https://cdn-icons-png.flaticon.com/512/2830/2830284.png';

      // Create custom icon HTML
      const iconHtml = `
        <div style="position:relative;width:48px;height:48px;">
          <div style="width:48px;height:48px;border-radius:50%;overflow:hidden;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);background:white;">
            <img src="${iconUrl}" style="width:100%;height:100%;object-fit:cover;" onerror="this.src='https://cdn-icons-png.flaticon.com/512/2830/2830284.png'" />
          </div>
          ${count > 0 ? `<div style="position:absolute;top:-4px;right:-4px;min-width:20px;height:20px;padding:0 6px;border-radius:10px;background:#ef4444;color:white;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 4px rgba(0,0,0,0.3);border:2px solid white;">${count > 9 ? '9+' : count}</div>` : ''}
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-business-marker',
        html: iconHtml,
        iconSize: [48, 48],
        iconAnchor: [24, 48],
        popupAnchor: [0, -48]
      });

      const marker = L.marker([business.location.lat, business.location.lng], {
        icon: customIcon
      }).addTo(mapInstanceRef.current);

      // Create popup content
      const popupContent = `
        <div style="min-width:200px;">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
            <img 
              src="${business.icon_url || 'https://cdn-icons-png.flaticon.com/512/2830/2830284.png'}"
              alt="${business.name}"
              style="width:48px;height:48px;border-radius:50%;border:2px solid #e5e7eb;object-fit:cover;"
              onerror="this.src='https://cdn-icons-png.flaticon.com/512/2830/2830284.png'"
            />
            <div>
              <strong style="font-size:16px;">${business.name}</strong>
              ${business.active_order_count > 0 ? `<span style="margin-left:8px;padding:2px 8px;border-radius:10px;background:#ef4444;color:white;font-size:11px;font-weight:700;">${business.active_order_count} paket</span>` : ''}
            </div>
          </div>
          <div style="font-size:13px;color:#6b7280;margin-bottom:8px;">
            📍 ${business.district || ''}, ${business.city || ''}
          </div>
          <button 
            id="view-orders-${business.id}" 
            style="width:100%;padding:8px;background:#22c55e;color:white;border:none;border-radius:6px;cursor:pointer;font-weight:600;"
          >
            Siparişleri Gör
          </button>
        </div>
      `;

      marker.bindPopup(popupContent);
      
      // Add click handler for the button
      marker.on('popupopen', () => {
        const button = document.getElementById(`view-orders-${business.id}`);
        if (button) {
          button.onclick = () => {
            if (onBusinessClick) {
              onBusinessClick(business);
            }
            mapInstanceRef.current.closePopup();
          };
        }
      });

      // Add click handler for marker
      marker.on('click', () => {
        if (onBusinessClick) {
          onBusinessClick(business);
        }
      });

      markersRef.current.push(marker);
    });
  }, [businesses, courierLocation, onBusinessClick]);

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
      console.error('Error fetching businesses:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: '100%' }}>
      <style>{`
        .custom-business-marker {
          background: transparent !important;
          border: none !important;
        }
      `}</style>
      
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '4px' }}>Paket Haritası</h2>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            {businesses.reduce((sum, b) => sum + (b.active_order_count || 0), 0)} hazır paket • {businesses.length} işletme
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

      <div 
        ref={mapRef} 
        style={{ 
          height: '600px', 
          borderRadius: '8px', 
          overflow: 'hidden', 
          border: '1px solid #e5e7eb' 
        }}
      />
    </div>
  );
};

export default PureLeafletMap;
