import React from 'react';
import { MapPin, Navigation } from 'lucide-react';

const SimpleMap = ({ 
  center = [39.9334, 32.8597], 
  markers = [],
  onMarkerClick = null,
  height = "500px"
}) => {
  // Generate OpenStreetMap iframe URL
  const generateMapUrl = () => {
    const lat = center[0];
    const lng = center[1];
    const bbox = `${lng-0.02},${lat-0.02},${lng+0.02},${lat+0.02}`;
    
    return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lng}`;
  };

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      {/* Google Maps iframe */}
      <iframe
        width="100%"
        height="100%"
        style={{ border: 0, borderRadius: '8px' }}
        loading="lazy"
        allowFullScreen
        referrerPolicy="no-referrer-when-downgrade"
        src={generateMapUrl()}
      />
      
      {/* Marker overlay - list view on side */}
      {markers.length > 0 && (
        <div 
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            maxHeight: 'calc(100% - 20px)',
            overflowY: 'auto',
            background: 'white',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            padding: '8px',
            maxWidth: '250px',
            zIndex: 10
          }}
        >
          <div style={{ marginBottom: '8px', fontWeight: 'bold', fontSize: '14px' }}>
            {markers.length} Konum
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {markers.map((marker, idx) => (
              <button
                key={idx}
                onClick={() => onMarkerClick && onMarkerClick(marker)}
                style={{
                  padding: '8px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '6px',
                  background: marker.type === 'courier' ? '#10b981' : 
                               marker.type === 'delivery' ? '#3b82f6' : 
                               '#f59e0b',
                  color: 'white',
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {marker.type === 'courier' ? '📍' : 
                 marker.type === 'delivery' ? '📦' : 
                 '🏪'}
                <div style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {marker.label || `Marker ${idx + 1}`}
                </div>
                {marker.count && (
                  <span style={{
                    background: 'rgba(255,255,255,0.3)',
                    padding: '2px 6px',
                    borderRadius: '10px',
                    fontSize: '10px',
                    fontWeight: 'bold'
                  }}>
                    {marker.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleMap;
