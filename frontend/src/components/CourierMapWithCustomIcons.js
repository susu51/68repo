import React, { useState, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { RefreshCw } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://courier-dashboard-3.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierMapWithCustomIcons = ({ onBusinessClick }) => {
  const [businesses, setBusinesses] = useState([]);
  const [courierLocation, setCourierLocation] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Get courier location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCourierLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.error('Location error:', error);
          setCourierLocation({ lat: 39.9334, lng: 32.8597 });
        }
      );
    } else {
      setCourierLocation({ lat: 39.9334, lng: 32.8597 });
    }
  }, []);

  useEffect(() => {
    if (courierLocation) {
      fetchBusinesses();
      const interval = setInterval(fetchBusinesses, 30000);
      return () => clearInterval(interval);
    }
  }, [courierLocation]);

  const fetchBusinesses = async () => {
    if (!courierLocation) return;
    
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

  // Generate map iframe with center
  const generateMapUrl = () => {
    if (!courierLocation) return '';
    const { lat, lng } = courierLocation;
    const bbox = `${lng-0.02},${lat-0.02},${lng+0.02},${lat+0.02}`;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lng}`;
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
        <Button onClick={fetchBusinesses} disabled={loading} size="sm" variant="outline">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''} mr-2`} />
          Yenile
        </Button>
      </div>

      {/* Map Container */}
      <div style={{ position: 'relative', width: '100%', height: '500px', background: '#f0f0f0', borderRadius: '8px', overflow: 'hidden' }}>
        {/* OpenStreetMap iframe */}
        <iframe
          width="100%"
          height="100%"
          style={{ border: 0 }}
          loading="lazy"
          src={generateMapUrl()}
          title="Map"
        />

        {/* Custom Marker Overlays */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          pointerEvents: 'none'
        }}>
          {businesses.map((business, idx) => {
            if (!business.location?.lat || !business.location?.lng) return null;
            
            // Calculate pixel position (simplified - would need proper projection in production)
            const latRange = 0.04; // bbox range
            const lngRange = 0.04;
            const centerLat = courierLocation?.lat || 39.9334;
            const centerLng = courierLocation?.lng || 32.8597;
            
            const relLat = (business.location.lat - centerLat) / latRange;
            const relLng = (business.location.lng - centerLng) / lngRange;
            
            const pixelX = 50 + (relLng * 400); // centered positioning
            const pixelY = 50 - (relLat * 400); // inverted Y
            
            return (
              <div
                key={business.id}
                style={{
                  position: 'absolute',
                  left: `${pixelX}%`,
                  top: `${pixelY}%`,
                  transform: 'translate(-50%, -50%)',
                  pointerEvents: 'auto',
                  cursor: 'pointer'
                }}
                onClick={() => onBusinessClick && onBusinessClick(business)}
              >
                {/* Custom Marker */}
                <div style={{
                  position: 'relative',
                  width: '56px',
                  height: '56px'
                }}>
                  {/* Business Icon */}
                  <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    overflow: 'hidden',
                    border: '3px solid white',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                    background: '#fff'
                  }}>
                    <img 
                      src={business.icon_url || '/static/icons/box-default.png'}
                      alt={business.name}
                      style={{
                        width: '100%',
                        height: '100%',
                        objectFit: 'cover',
                        display: 'block'
                      }}
                      onError={(e) => {
                        e.target.src = '/static/icons/box-default.png';
                      }}
                    />
                  </div>
                  
                  {/* Badge - Active Order Count */}
                  {business.active_order_count > 0 && (
                    <div style={{
                      position: 'absolute',
                      top: '-4px',
                      right: '-4px',
                      minWidth: '20px',
                      height: '20px',
                      padding: '0 6px',
                      borderRadius: '10px',
                      background: '#ef4444',
                      color: 'white',
                      fontSize: '11px',
                      fontWeight: '700',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                      border: '2px solid white'
                    }}>
                      {business.active_order_count > 9 ? '9+' : business.active_order_count}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Business List (Right Panel) */}
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          maxHeight: 'calc(100% - 20px)',
          overflowY: 'auto',
          background: 'white',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          padding: '12px',
          maxWidth: '280px',
          zIndex: 10
        }}>
          <div style={{ marginBottom: '12px', fontWeight: 'bold', fontSize: '14px' }}>
            {businesses.length} İşletme
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {businesses.filter(b => b.active_order_count > 0).map((business) => (
              <button
                key={business.id}
                onClick={() => onBusinessClick && onBusinessClick(business)}
                style={{
                  padding: '10px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  background: 'white',
                  cursor: 'pointer',
                  textAlign: 'left',
                  fontSize: '13px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {/* Icon */}
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  overflow: 'hidden',
                  border: '2px solid #e5e7eb',
                  flexShrink: 0
                }}>
                  <img 
                    src={business.icon_url || '/static/icons/box-default.png'}
                    alt={business.name}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover'
                    }}
                  />
                </div>
                
                {/* Info */}
                <div style={{ flex: 1, overflow: 'hidden' }}>
                  <div style={{ fontWeight: '600', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {business.name}
                  </div>
                  <div style={{ fontSize: '11px', color: '#6b7280' }}>
                    {business.district}
                  </div>
                </div>
                
                {/* Badge */}
                <div style={{
                  minWidth: '24px',
                  height: '24px',
                  padding: '0 6px',
                  borderRadius: '12px',
                  background: '#ef4444',
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: '700',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {business.active_order_count}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourierMapWithCustomIcons;
