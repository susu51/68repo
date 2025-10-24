import React, { useState, useEffect } from 'react';
import { Package, Store, User, Phone, Navigation, DollarSign, ShoppingBag } from 'lucide-react';
import { toast } from 'sonner';
import { SimpleLeafletMap } from './SimpleLeafletMap';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-hub.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierAdvancedTasksNative = () => {
  const [selectedBusiness, setSelectedBusiness] = useState(null);
  const [businessOrders, setBusinessOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [claimingOrderId, setClaimingOrderId] = useState(null);

  const handleBusinessClick = async (business) => {
    setSelectedBusiness(business);
    setSelectedOrder(null);
    
    try {
      const response = await fetch(
        `${API}/courier/tasks/businesses/${business.id}/available-orders`,
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
      window.location.href = `maps://maps.apple.com/?daddr=${lat},${lng}&q=${encodeURIComponent(label)}`;
      setTimeout(() => {
        window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
      }, 500);
    } else {
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
    }
  };

  const formatAddress = (address) => {
    if (typeof address === 'string') return address;
    return address?.label || address?.address || 'Adres bilgisi yok';
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Map */}
      <SimpleLeafletMap onBusinessClick={handleBusinessClick} />

      {/* Selected Business Orders */}
      {selectedBusiness && businessOrders.length > 0 && (
        <div style={{
          marginTop: '24px',
          border: '2px solid #22c55e',
          borderRadius: '8px',
          background: '#f0fdf4',
          padding: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ fontSize: '20px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Store style={{ width: '20px', height: '20px' }} />
                {selectedBusiness.name}
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '4px' }}>
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
                padding: '8px 16px',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                fontSize: '20px'
              }}
            >
              ✕
            </button>
          </div>

          {/* Orders Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {businessOrders.map((order) => (
              <div 
                key={order.order_id}
                style={{
                  padding: '16px',
                  background: 'white',
                  borderRadius: '8px',
                  border: selectedOrder?.order_id === order.order_id ? '2px solid #22c55e' : '1px solid #e5e7eb',
                  cursor: 'pointer',
                  boxShadow: selectedOrder?.order_id === order.order_id ? '0 4px 8px rgba(0,0,0,0.1)' : 'none'
                }}
                onClick={() => setSelectedOrder(selectedOrder?.order_id === order.order_id ? null : order)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div style={{ flex: 1 }}>
                    <h5 style={{ fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Package style={{ width: '16px', height: '16px' }} />
                      Sipariş #{order.order_code}
                    </h5>
                    <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                      👤 {order.customer_name}
                    </p>
                    <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                      📦 {order.items_count} ürün
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontWeight: 'bold', color: '#22c55e', fontSize: '18px' }}>
                      ₺{order.grand_total?.toFixed(2)}
                    </p>
                    <p style={{ fontSize: '11px', color: '#6b7280' }}>
                      (₺{order.delivery_fee?.toFixed(2)} teslimat)
                    </p>
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedOrder?.order_id === order.order_id && (
                  <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #e5e7eb' }}>
                    <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>
                      📍 {formatAddress(order.delivery_address)}
                    </p>
                    {order.notes && (
                      <p style={{ fontSize: '12px', color: '#ca8a04', marginBottom: '8px' }}>
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
          marginTop: '24px',
          border: '2px solid #22c55e',
          borderRadius: '8px',
          background: '#f0fdf4',
          padding: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '20px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShoppingBag style={{ width: '20px', height: '20px' }} />
              Sipariş Detayları #{selectedOrder.order_code}
            </h3>
            <button 
              onClick={() => setSelectedOrder(null)}
              style={{ background: 'transparent', border: 'none', fontSize: '20px', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>

          {/* Business Info */}
          <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Store style={{ width: '16px', height: '16px' }} />
              Alınacak Yer (İşletme)
            </h4>
            <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>İşletme</p>
            <p style={{ fontWeight: '600', marginBottom: '8px' }}>{selectedOrder.business_name}</p>
            <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Adres</p>
            <p style={{ fontSize: '13px', marginBottom: '12px' }}>{formatAddress(selectedOrder.business_address)}</p>
            {selectedOrder.business_location?.lat && selectedOrder.business_location?.lng && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openInMaps(selectedOrder.business_location.lat, selectedOrder.business_location.lng, 'İşletme');
                }}
                style={{
                  width: '100%',
                  padding: '8px',
                  background: '#fed7aa',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <Navigation style={{ width: '16px', height: '16px' }} />
                İşletmeye Git
              </button>
            )}
          </div>

          {/* Customer Info */}
          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <User style={{ width: '16px', height: '16px' }} />
              Müşteri Bilgileri
            </h4>
            <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Ad Soyad</p>
            <p style={{ fontWeight: '600', marginBottom: '8px' }}>{selectedOrder.customer_name}</p>
            {selectedOrder.customer_phone && (
              <>
                <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Telefon</p>
                <a 
                  href={`tel:${selectedOrder.customer_phone}`}
                  style={{ fontSize: '14px', color: '#2563eb', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', textDecoration: 'none' }}
                >
                  <Phone style={{ width: '16px', height: '16px' }} />
                  {selectedOrder.customer_phone}
                </a>
              </>
            )}
            <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Teslimat Adresi</p>
            <p style={{ fontSize: '13px', marginBottom: '12px' }}>{formatAddress(selectedOrder.delivery_address)}</p>
            {selectedOrder.delivery_location?.lat && selectedOrder.delivery_location?.lng && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openInMaps(selectedOrder.delivery_location.lat, selectedOrder.delivery_location.lng, 'Müşteri');
                }}
                style={{
                  width: '100%',
                  padding: '8px',
                  background: '#bfdbfe',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                <Navigation style={{ width: '16px', height: '16px' }} />
                Müşteriye Git
              </button>
            )}
          </div>

          {/* Payment Info */}
          <div style={{ background: '#fef9c3', border: '1px solid #fde047', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <DollarSign style={{ width: '16px', height: '16px' }} />
              Ödeme Bilgisi
            </h4>
            <p style={{ fontWeight: '600', marginBottom: '4px' }}>
              {selectedOrder.payment_method === 'cash' ? 'Kapıda Nakit Ödeme' : 
               selectedOrder.payment_method === 'card' ? 'Kredi Kartı (Ödendi)' : 
               'Ödeme Bilgisi Yok'}
            </p>
            {selectedOrder.payment_method === 'cash' && (
              <p style={{ fontSize: '12px', color: '#a16207' }}>
                ⚠️ Müşteriden ₺{selectedOrder.grand_total?.toFixed(2)} tahsil edilecek
              </p>
            )}
          </div>

          {/* Claim Button */}
          <button
            onClick={() => handleClaimOrder(selectedOrder.order_id)}
            disabled={claimingOrderId === selectedOrder.order_id}
            style={{
              width: '100%',
              padding: '16px',
              background: '#22c55e',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: claimingOrderId ? 'not-allowed' : 'pointer',
              opacity: claimingOrderId ? 0.7 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {claimingOrderId === selectedOrder.order_id ? (
              <>🔄 Sipariş Alınıyor...</>
            ) : (
              <>
                <ShoppingBag style={{ width: '20px', height: '20px' }} />
                Siparişi Al ve Teslimata Başla
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default CourierAdvancedTasksNative;
