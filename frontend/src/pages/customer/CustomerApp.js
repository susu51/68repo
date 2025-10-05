import React, { useState } from 'react';
import { useCart } from '../../contexts/CartContext';

export const CustomerApp = ({ user, onLogout }) => {
  const [activeView, setActiveView] = useState('discover');
  
  // Test Cart Context
  const { cart, getCartSummary } = useCart();
  const cartSummary = getCartSummary ? getCartSummary() : { itemCount: 0, total: 0 };

  console.log('🚀 Minimal CustomerApp rendered - activeView:', activeView, 'cart:', cart, 'getCartSummary:', typeof getCartSummary);

  const tabs = [
    { 
      id: 'discover', 
      label: 'Keşfet', 
      icon: '🔍',
      active: activeView === 'discover'
    },
    { 
      id: 'cart', 
      label: 'Sepet', 
      icon: '🛒',
      badge: cart?.items?.length > 0 ? cartSummary.itemCount : null,
      active: activeView === 'cart'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Main Content */}
      <div className="flex-1 pb-20">
        <div className="text-center p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Kuryecini - {activeView} View
          </h1>
          <p className="text-gray-600 mb-4">
            Hoş geldin {user?.first_name || 'Müşteri'}!
          </p>
          <p className="text-sm text-green-600 mb-4">
            ✅ Minimal version with Cart Context
          </p>
          <p className="text-sm text-blue-600">
            Cart Items: {cart?.items?.length || 0} | Total: ₺{cartSummary.total.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Bottom Tab Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50">
        <div className="flex justify-around items-center py-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`flex flex-col items-center py-2 px-4 rounded-lg transition-colors ${
                tab.active
                  ? 'text-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              <div className="relative">
                <span className="text-xl">{tab.icon}</span>
                {tab.badge && (
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center min-w-5">
                    {tab.badge > 99 ? '99+' : tab.badge}
                  </span>
                )}
              </div>
              <span className="text-xs mt-1 font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Debug Info */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed top-4 right-4 bg-black text-white p-2 rounded text-xs z-50 opacity-70">
          View: {activeView} | Cart: {cart?.items?.length || 0} items
        </div>
      )}
    </div>
  );
};

export default CustomerApp;