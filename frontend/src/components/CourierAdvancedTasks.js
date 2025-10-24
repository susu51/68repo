import React, { useState, useEffect } from 'react';
import { 
  MapPin, 
  Navigation, 
  Package, 
  Store, 
  RefreshCw, 
  List,
  Map,
  Phone,
  CreditCard,
  User,
  Clock,
  DollarSign,
  Home,
  ShoppingBag
} from 'lucide-react';
import { toast } from 'sonner';
import { PureLeafletMap } from './PureLeafletMap';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CourierAdvancedTasks = () => {
  // Removed viewMode - only map view
  const [nearbyBusinesses, setNearbyBusinesses] = useState([]);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [businessOrders, setBusinessOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [claimingOrderId, setClaimingOrderId] = useState(null);
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
      fetchData();
      const interval = setInterval(fetchData, 30000);
      return () => clearInterval(interval);
    }
  }, [courierLocation]);

  const fetchData = async () => {
    if (!courierLocation) return;
    
    try {
      setLoading(true);
      
      // Fetch nearby businesses with ready orders
      const businessResponse = await fetch(
        `${API}/courier/tasks/nearby-businesses?lat=${courierLocation.lat}&lng=${courierLocation.lng}&radius_m=50000`,
        { method: 'GET', credentials: 'include' }
      );

      if (businessResponse.ok) {
        const businesses = await businessResponse.json();
        setNearbyBusinesses(businesses);
      }
    } catch (error) {
      console.error('❌ Fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBusinessClick = async (business) => {
    setSelectedBusiness(business);
    setSelectedOrder(null);
    
    try {
      const response = await fetch(
        `${API}/courier/tasks/businesses/${business.business_id}/available-orders`,
        { method: 'GET', credentials: 'include' }
      );

      if (response.ok) {
        const orders = await response.json();
        setBusinessOrders(orders);
      }
    } catch (error) {
      console.error('❌ Orders fetch error:', error);
    }
  };

  const handleClaimOrder = async (orderId) => {
    try {
      setClaimingOrderId(orderId);
      const response = await fetch(
        `${API}/courier/tasks/orders/${orderId}/claim`,
        { method: 'POST', credentials: 'include' }
      );

      if (response.ok) {
        toast.success('✅ Sipariş başarıyla alındı! "Siparişler" sekmesine gidin.');
        await fetchData();
        setSelectedOrder(null);
        setSelectedBusiness(null);
        setBusinessOrders([]);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Sipariş alınamadı');
      }
    } catch (error) {
      console.error('❌ Claim error:', error);
      toast.error('Bir hata oluştu');
    } finally {
      setClaimingOrderId(null);
    }
  };

  const openInMaps = (lat, lng, label) => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
      const appleMapsUrl = `maps://maps.apple.com/?daddr=${lat},${lng}&q=${encodeURIComponent(label)}`;
      window.location.href = appleMapsUrl;
      setTimeout(() => {
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
      }, 500);
    } else {
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
    }
  };

  // Map markers - show BUSINESS locations with PACKAGE count (not delivery locations!)
  const mapMarkers = [];
  
  // Add business markers with package icons
  nearbyBusinesses.forEach(business => {
    const coords = business.location?.coordinates || [business.lng || 0, business.lat || 0];
    if (coords[1] && coords[0] && business.pending_ready_count > 0) {
      mapMarkers.push({
        lat: coords[1],
        lng: coords[0],
        type: 'business',
        businessId: business.business_id,
        label: `📦 ${business.name}`,
        count: business.pending_ready_count,
        popup: `<strong>📦 ${business.name}</strong><br/>${business.pending_ready_count} hazır paket`
      });
    }
  });

  // Add courier location
  if (courierLocation) {
    mapMarkers.push({
      lat: courierLocation.lat,
      lng: courierLocation.lng,
      type: 'courier',
      label: '📍 Benim Konumum',
      popup: '<strong>📍 Konumunuz</strong>'
    });
  }

  const formatAddress = (address) => {
    if (typeof address === 'string') return address;
    return address?.label || address?.address || 'Adres bilgisi yok';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: 0 }}>Paket Havuzu - Hazır Siparişler</h2>
          <p style={{ color: '#6b7280', marginTop: '0.25rem' }}>
            {nearbyBusinesses.reduce((sum, b) => sum + b.pending_ready_count, 0)} hazır paket • {nearbyBusinesses.length} işletme
          </p>
        </div>
        <button 
          onClick={fetchData} 
          disabled={loading}
          style={{
            padding: '0.5rem 1rem',
            border: '1px solid #d1d5db',
            borderRadius: '0.375rem',
            background: 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <RefreshCw className={loading ? 'animate-spin' : ''} size={16} />
          Yenile
        </button>
      </div>

      {/* Pure Leaflet Map */}
      <PureLeafletMap
        onBusinessClick={async (business) => {
          const formattedBusiness = {
            business_id: business.id,
            name: business.name,
            pending_ready_count: business.active_order_count,
            location: business.location
          };
          await handleBusinessClick(formattedBusiness);
        }}
      />

      {/* Selected Business Orders */}
      {selectedBusiness && businessOrders.length > 0 && (
        <div style={{ 
          border: '2px solid #10b981', 
          borderRadius: '0.5rem', 
          background: '#f0fdf4', 
          padding: '1rem' 
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                <Store size={20} />
                {selectedBusiness.name}
              </h3>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.25rem' }}>
                📦 {businessOrders.length} hazır paket
              </p>
            </div>
            <button 
              onClick={() => {
                setSelectedBusiness(null);
                setBusinessOrders([]);
                setSelectedOrder(null);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                fontSize: '1.25rem',
                cursor: 'pointer',
                padding: '0.25rem 0.5rem'
              }}
            >
              ✕
            </button>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {businessOrders.map((order) => (
              <div 
                key={order.order_id}
                onClick={() => setSelectedOrder(selectedOrder?.order_id === order.order_id ? null : order)}
                style={{
                  cursor: 'pointer',
                  border: selectedOrder?.order_id === order.order_id ? '2px solid #059669' : '1px solid #d1d5db',
                  borderRadius: '0.5rem',
                  background: 'white',
                  padding: '1rem',
                  boxShadow: selectedOrder?.order_id === order.order_id ? '0 4px 6px rgba(0,0,0,0.1)' : 'none'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div style={{ flex: 1 }}>
                    <h5 style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.5rem', 
                      fontWeight: '600',
                      margin: 0 
                    }}>
                      <Package size={16} />
                      Sipariş #{order.order_code}
                    </h5>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                      👤 {order.customer_name}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                      📦 {order.items_count} ürün
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontWeight: 'bold', color: '#10b981', margin: 0 }}>
                      ₺{order.grand_total?.toFixed(2)}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
                      (₺{order.delivery_fee?.toFixed(2)} teslimat)
                    </p>
                  </div>
                </div>

                {/* Expand when selected */}
                {selectedOrder?.order_id === order.order_id && (
                  <div style={{ 
                    marginTop: '0.75rem', 
                    paddingTop: '0.75rem', 
                    borderTop: '1px solid #e5e7eb',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem'
                  }}>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>
                      📍 {formatAddress(order.delivery_address)}
                    </p>
                    {order.notes && (
                      <p style={{ fontSize: '0.75rem', color: '#ca8a04', margin: 0 }}>
                        💬 {order.notes}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Order Details Panel */}
      {selectedOrder && (
        <div style={{ 
          border: '2px solid #10b981', 
          borderRadius: '0.5rem', 
          background: '#f0fdf4', 
          padding: '1rem' 
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <ShoppingBag size={20} />
              Sipariş Detayları #{selectedOrder.order_code}
            </h3>
            <button 
              onClick={() => setSelectedOrder(null)}
              style={{
                background: 'transparent',
                border: 'none',
                fontSize: '1.25rem',
                cursor: 'pointer',
                padding: '0.25rem 0.5rem'
              }}
            >
              ✕
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Business Info */}
            <div style={{ 
              background: '#fff7ed', 
              border: '1px solid #fed7aa', 
              borderRadius: '0.5rem', 
              padding: '1rem' 
            }}>
              <h4 style={{ 
                fontSize: '0.875rem', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                margin: '0 0 0.75rem 0'
              }}>
                <Store size={16} />
                Alınacak Yer (İşletme)
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>İşletme Adı</p>
                  <p style={{ fontWeight: '600', margin: '0.25rem 0 0 0' }}>{selectedOrder.business_name}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>Adres</p>
                  <p style={{ fontSize: '0.875rem', margin: '0.25rem 0 0 0' }}>{formatAddress(selectedOrder.business_address)}</p>
                </div>
                {selectedOrder.business_location?.lat && selectedOrder.business_location?.lng && (
                  <button
                    onClick={() => openInMaps(
                      selectedOrder.business_location.lat,
                      selectedOrder.business_location.lng,
                      'İşletme - Alış Noktası'
                    )}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      background: '#fed7aa',
                      border: '1px solid #fdba74',
                      borderRadius: '0.375rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.5rem',
                      fontSize: '0.875rem',
                      fontWeight: '500'
                    }}
                  >
                    <Navigation size={16} />
                    İşletmeye Git (Maps)
                  </button>
                )}
              </div>
            </div>

            {/* Customer Info */}
            <div style={{ 
              background: '#eff6ff', 
              border: '1px solid #bfdbfe', 
              borderRadius: '0.5rem', 
              padding: '1rem' 
            }}>
              <h4 style={{ 
                fontSize: '0.875rem', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                margin: '0 0 0.75rem 0'
              }}>
                <User size={16} />
                Müşteri Bilgileri
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>Ad Soyad</p>
                  <p style={{ fontWeight: '600', margin: '0.25rem 0 0 0' }}>{selectedOrder.customer_name}</p>
                </div>
                <div>
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>Teslimat Adresi</p>
                  <p style={{ fontSize: '0.875rem', margin: '0.25rem 0 0 0' }}>{formatAddress(selectedOrder.delivery_address)}</p>
                </div>
                {selectedOrder.customer_phone && (
                  <div>
                    <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>İletişim</p>
                    <a 
                      href={`tel:${selectedOrder.customer_phone}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.875rem',
                        fontWeight: '500',
                        color: '#2563eb',
                        textDecoration: 'none',
                        marginTop: '0.25rem'
                      }}
                    >
                      <Phone size={16} />
                      {selectedOrder.customer_phone}
                    </a>
                  </div>
                )}
                {selectedOrder.delivery_location?.lat && selectedOrder.delivery_location?.lng && (
                  <button
                    onClick={() => openInMaps(
                      selectedOrder.delivery_location.lat,
                      selectedOrder.delivery_location.lng,
                      'Müşteri - Teslimat Noktası'
                    )}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      background: '#dbeafe',
                      border: '1px solid #93c5fd',
                      borderRadius: '0.375rem',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.5rem',
                      fontSize: '0.875rem',
                      fontWeight: '500'
                    }}
                  >
                    <Navigation size={16} />
                    Müşteriye Git (Maps)
                  </button>
                )}
              </div>
            </div>

            {/* Order Details */}
            <div style={{ 
              background: 'white', 
              border: '1px solid #d1d5db', 
              borderRadius: '0.5rem', 
              padding: '1rem' 
            }}>
              <h4 style={{ 
                fontSize: '0.875rem', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                margin: '0 0 0.75rem 0'
              }}>
                <Package size={16} />
                Sipariş İçeriği
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {/* Order Items List */}
                {selectedOrder.items && selectedOrder.items.length > 0 && (
                  <div style={{ 
                    marginBottom: '0.75rem', 
                    padding: '0.75rem', 
                    background: '#f9fafb', 
                    borderRadius: '0.375rem',
                    border: '1px solid #e5e7eb'
                  }}>
                    <p style={{ 
                      fontSize: '0.75rem', 
                      fontWeight: '600', 
                      color: '#374151', 
                      marginBottom: '0.5rem' 
                    }}>
                      📦 Sipariş Detayları:
                    </p>
                    {selectedOrder.items.map((item, index) => (
                      <div 
                        key={index} 
                        style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          fontSize: '0.8125rem',
                          padding: '0.25rem 0',
                          borderBottom: index < selectedOrder.items.length - 1 ? '1px solid #e5e7eb' : 'none'
                        }}
                      >
                        <span style={{ color: '#4b5563' }}>
                          {item.quantity}x {item.name}
                        </span>
                        <span style={{ fontWeight: '500', color: '#1f2937' }}>
                          ₺{(item.price * item.quantity).toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: '#6b7280' }}>Ürün Sayısı:</span>
                  <span style={{ fontWeight: '500' }}>{selectedOrder.items_count} ürün</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: '#6b7280' }}>Sipariş Tutarı:</span>
                  <span style={{ fontWeight: '500' }}>₺{selectedOrder.total_amount?.toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: '#6b7280' }}>Teslimat Ücreti:</span>
                  <span style={{ fontWeight: '500', color: '#10b981' }}>₺{selectedOrder.delivery_fee?.toFixed(2)}</span>
                </div>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  fontSize: '1.125rem',
                  fontWeight: 'bold',
                  paddingTop: '0.5rem',
                  borderTop: '1px solid #e5e7eb'
                }}>
                  <span>Toplam:</span>
                  <span style={{ color: '#10b981' }}>₺{selectedOrder.grand_total?.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Payment Info */}
            <div style={{ 
              background: '#fefce8', 
              border: '1px solid #fde047', 
              borderRadius: '0.5rem', 
              padding: '1rem' 
            }}>
              <h4 style={{ 
                fontSize: '0.875rem', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                margin: '0 0 0.75rem 0'
              }}>
                <CreditCard size={16} />
                Ödeme Bilgisi
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <DollarSign size={20} style={{ color: '#ca8a04' }} />
                <div>
                  <p style={{ fontWeight: '600', margin: 0 }}>
                    {selectedOrder.payment_method === 'cash' ? 'Kapıda Nakit Ödeme' : 
                     selectedOrder.payment_method === 'card' ? 'Kredi Kartı (Ödendi)' : 
                     'Ödeme Bilgisi Yok'}
                  </p>
                  {selectedOrder.payment_method === 'cash' && (
                    <p style={{ fontSize: '0.75rem', color: '#a16207', margin: '0.25rem 0 0 0' }}>
                      ⚠️ Müşteriden ₺{selectedOrder.grand_total?.toFixed(2)} tahsil edilecek
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Notes */}
            {selectedOrder.notes && (
              <div style={{ 
                background: '#faf5ff', 
                border: '1px solid #e9d5ff', 
                borderRadius: '0.5rem', 
                padding: '1rem' 
              }}>
                <h4 style={{ fontSize: '0.875rem', margin: '0 0 0.5rem 0' }}>📝 Notlar</h4>
                <p style={{ fontSize: '0.875rem', margin: 0 }}>{selectedOrder.notes}</p>
              </div>
            )}

            {/* Action Button */}
            <button
              onClick={() => handleClaimOrder(selectedOrder.order_id)}
              disabled={claimingOrderId === selectedOrder.order_id}
              style={{
                width: '100%',
                padding: '1.5rem',
                background: claimingOrderId === selectedOrder.order_id ? '#9ca3af' : '#059669',
                color: 'white',
                border: 'none',
                borderRadius: '0.5rem',
                fontSize: '1.125rem',
                fontWeight: '600',
                cursor: claimingOrderId === selectedOrder.order_id ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
            >
              {claimingOrderId === selectedOrder.order_id ? (
                <>🔄 Sipariş Alınıyor...</>
              ) : (
                <>
                  <ShoppingBag size={20} />
                  Siparişi Al ve Teslimata Başla
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CourierAdvancedTasks;
