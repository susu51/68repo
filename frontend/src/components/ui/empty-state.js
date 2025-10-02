import React from 'react';
import { Button } from './button';
import { Card, CardContent } from './card';

// Empty State Component
export const EmptyState = ({ 
  icon = '📭', 
  title = 'Veri Bulunamadı', 
  description = 'Henüz herhangi bir veri yok.',
  actionText = null,
  onAction = null,
  className = ''
}) => {
  return (
    <div className={`flex flex-col items-center justify-center min-h-[300px] p-8 text-center ${className}`}>
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-700 mb-2">{title}</h3>
      <p className="text-gray-500 mb-6 max-w-md">{description}</p>
      
      {actionText && onAction && (
        <Button 
          onClick={onAction}
          className="bg-orange-500 hover:bg-orange-600 text-white"
        >
          {actionText}
        </Button>
      )}
    </div>
  );
};

// Empty Restaurant List
export const EmptyRestaurantList = ({ onRefresh }) => {
  return (
    <EmptyState
      icon="🍽️"
      title="Restoran Bulunamadı"
      description="Bu bölgede henüz aktif restoran bulunmuyor. Lütfen daha sonra tekrar kontrol edin."
      actionText="Yenile"
      onAction={onRefresh}
    />
  );
};

// Empty Orders List
export const EmptyOrdersList = ({ userRole = 'customer' }) => {
  const messages = {
    customer: {
      icon: '📦',
      title: 'Henüz Sipariş Yok',
      description: 'İlk siparişinizi vermek için restoranları keşfedin!'
    },
    business: {
      icon: '📋', 
      title: 'Henüz Sipariş Yok',
      description: 'Yeni siparişler geldiğinde burada görüntülenecek.'
    },
    courier: {
      icon: '🚚',
      title: 'Henüz Teslimat Yok', 
      description: 'Online olduğunuzda yeni siparişler burada görünecek.'
    }
  };

  const message = messages[userRole] || messages.customer;

  return (
    <EmptyState
      icon={message.icon}
      title={message.title}
      description={message.description}
    />
  );
};

// Empty Cart
export const EmptyCart = ({ onStartShopping }) => {
  return (
    <EmptyState
      icon="🛒"
      title="Sepet Boş"
      description="Sepetinize ürün eklemek için restoranları keşfedin."
      actionText="Alışverişe Başla"
      onAction={onStartShopping}
    />
  );
};

// Empty Address List
export const EmptyAddressList = ({ onAddAddress }) => {
  return (
    <EmptyState
      icon="📍"
      title="Adres Bulunamadı"
      description="Sipariş verebilmek için önce bir teslimat adresi eklemeniz gerekiyor."
      actionText="Adres Ekle"
      onAction={onAddAddress}
    />
  );
};

// Empty Search Results
export const EmptySearchResults = ({ searchQuery, onClearSearch }) => {
  return (
    <EmptyState
      icon="🔍"
      title="Sonuç Bulunamadı"
      description={`"${searchQuery}" için herhangi bir sonuç bulunamadı. Farklı kelimeler deneyebilirsiniz.`}
      actionText="Aramayı Temizle"
      onAction={onClearSearch}
    />
  );
};

export default EmptyState;