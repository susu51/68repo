import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import toast from 'react-hot-toast';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom courier icon
const courierIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
      <circle cx="12" cy="12" r="10" fill="#3B82F6" stroke="#1E40AF" stroke-width="2"/>
      <text x="12" y="16" text-anchor="middle" fill="white" font-size="12">🏃</text>
    </svg>
  `),
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -16],
});

// Order marker icon
const orderIcon = new L.Icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
      <circle cx="12" cy="12" r="10" fill="#EF4444" stroke="#DC2626" stroke-width="2"/>
      <text x="12" y="16" text-anchor="middle" fill="white" font-size="10">📦</text>
    </svg>
  `),
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -16],
});

// Map center component
const MapCenter = ({ center }) => {
  const map = useMap();
  
  useEffect(() => {
    if (center) {
      map.setView(center, 13);
    }
  }, [map, center]);
  
  return null;
};

const CourierMap = ({ orders = [], onOrderSelect, selectedOrder }) => {
  const [courierLocation, setCourierLocation] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const [locationError, setLocationError] = useState(null);
  const [mapCenter, setMapCenter] = useState([41.0082, 28.9784]); // Istanbul default
  const watchIdRef = useRef(null);

  // Get courier location
  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      const error = 'Bu tarayıcı konum hizmetlerini desteklemiyor.';
      setLocationError(error);
      toast.error(error);
      return;
    }

    setLocationError(null);
    
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy
        };
        setCourierLocation(location);
        setMapCenter([location.lat, location.lng]);
        toast.success('Konum alındı!');
      },
      (error) => {
        let errorMessage = 'Konum alınamadı. ';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage += 'Konum izni reddedildi. Lütfen tarayıcı ayarlarından konum iznini etkinleştirin.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage += 'Konum bilgisi mevcut değil.';
            break;
          case error.TIMEOUT:
            errorMessage += 'Konum alma işlemi zaman aşımına uğradı.';
            break;
          default:
            errorMessage += 'Bilinmeyen bir hata oluştu.';
            break;
        }
        setLocationError(errorMessage);
        toast.error(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  };

  // Start location tracking
  const startTracking = () => {
    if (!navigator.geolocation) {
      toast.error('Bu tarayıcı konum takibini desteklemiyor.');
      return;
    }

    setIsTracking(true);
    
    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        const location = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy
        };
        setCourierLocation(location);
        setMapCenter([location.lat, location.lng]);
      },
      (error) => {
        console.error('Location tracking error:', error);
        toast.error('Konum takibi sırasında hata oluştu');
      },
      {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 30000
      }
    );

    toast.success('Konum takibi başlatıldı');
  };

  // Stop location tracking
  const stopTracking = () => {
    if (watchIdRef.current) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setIsTracking(false);
    toast.success('Konum takibi durduruldu');
  };

  // Calculate distance between two points
  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return (R * c).toFixed(2);
  };

  useEffect(() => {
    // Get initial location
    getCurrentLocation();

    // Cleanup on unmount
    return () => {
      if (watchIdRef.current) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return (
    <div className="h-screen flex flex-col">
      {/* Map Controls */}
      <div className="bg-white border-b p-4 flex justify-between items-center">
        <div className="flex space-x-2">
          <Button
            onClick={getCurrentLocation}
            variant="outline"
            size="sm"
          >
            📍 Konumu Al
          </Button>
          
          {isTracking ? (
            <Button
              onClick={stopTracking}
              variant="destructive"
              size="sm"
            >
              ⏹️ Takibi Durdur
            </Button>
          ) : (
            <Button
              onClick={startTracking}
              variant="default"
              size="sm"
            >
              ▶️ Takibi Başlat
            </Button>
          )}
        </div>

        {courierLocation && (
          <div className="text-sm text-gray-600">
            📍 Konum: {courierLocation.lat.toFixed(4)}, {courierLocation.lng.toFixed(4)}
          </div>
        )}
      </div>

      {/* Location Error */}
      {locationError && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{locationError}</p>
              <button
                onClick={getCurrentLocation}
                className="mt-2 text-sm text-red-600 underline hover:text-red-800"
              >
                Tekrar dene
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Map Container */}
      <div className="flex-1 relative">
        <MapContainer
          center={mapCenter}
          zoom={13}
          className="h-full w-full"
          zoomControl={true}
        >
          <MapCenter center={mapCenter} />
          
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Courier Location Marker */}
          {courierLocation && (
            <>
              <Marker 
                position={[courierLocation.lat, courierLocation.lng]} 
                icon={courierIcon}
              >
                <Popup>
                  <div className="text-center">
                    <strong>🚚 Konumunuz</strong><br />
                    <small>Doğruluk: ±{courierLocation.accuracy?.toFixed(0)}m</small>
                  </div>
                </Popup>
              </Marker>
              
              {/* Accuracy Circle */}
              <Circle
                center={[courierLocation.lat, courierLocation.lng]}
                radius={courierLocation.accuracy || 50}
                pathOptions={{ 
                  fillColor: '#3B82F6', 
                  fillOpacity: 0.1, 
                  color: '#3B82F6',
                  weight: 1
                }}
              />
            </>
          )}

          {/* Order Markers */}
          {orders.map((order) => (
            <Marker
              key={order.id}
              position={[order.delivery_lat, order.delivery_lng]}
              icon={orderIcon}
              eventHandlers={{
                click: () => onOrderSelect && onOrderSelect(order)
              }}
            >
              <Popup>
                <div className="min-w-[200px]">
                  <div className="font-semibold mb-2">📦 Sipariş #{order.order_number}</div>
                  <div className="space-y-1 text-sm">
                    <div><strong>Müşteri:</strong> {order.customer_name}</div>
                    <div><strong>Adres:</strong> {order.delivery_address}</div>
                    <div><strong>Tutar:</strong> ₺{order.total_amount}</div>
                    {courierLocation && (
                      <div><strong>Mesafe:</strong> {calculateDistance(
                        courierLocation.lat,
                        courierLocation.lng,
                        order.delivery_lat,
                        order.delivery_lng
                      )} km</div>
                    )}
                  </div>
                  <Button
                    size="sm"
                    className="w-full mt-2"
                    onClick={() => onOrderSelect && onOrderSelect(order)}
                  >
                    Siparişi Al
                  </Button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Selected Order Info */}
        {selectedOrder && (
          <Card className="absolute top-4 left-4 w-80 bg-white shadow-lg z-[1000]">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg">
                🎯 Seçili Sipariş #{selectedOrder.order_number}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div><strong>Müşteri:</strong> {selectedOrder.customer_name}</div>
                <div><strong>Telefon:</strong> {selectedOrder.customer_phone}</div>
                <div><strong>Adres:</strong> {selectedOrder.delivery_address}</div>
                <div><strong>Tutar:</strong> ₺{selectedOrder.total_amount}</div>
                <Badge variant="secondary" className="mt-2">
                  {selectedOrder.status}
                </Badge>
              </div>
              <div className="flex space-x-2 mt-4">
                <Button size="sm" className="flex-1">
                  🚚 Teslimata Başla
                </Button>
                <Button size="sm" variant="outline" className="flex-1">
                  📞 Müşteriyi Ara
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default CourierMap;