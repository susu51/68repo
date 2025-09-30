import React from 'react';
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";

const StickyCart = ({ 
  cart = [], 
  onUpdateQuantity, 
  onRemoveItem, 
  onCheckout, 
  restaurantName = '',
  isVisible = true 
}) => {
  const getTotalPrice = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0).toFixed(2);
  };

  const getTotalItems = () => {
    return cart.reduce((total, item) => total + item.quantity, 0);
  };

  if (!isVisible || cart.length === 0) return null;

  return (
    <>
      {/* Mobile Sticky Cart - Fixed at bottom */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-medium text-gray-900">
              {getTotalItems()} ürün • {restaurantName}
            </p>
            <p className="text-lg font-bold text-green-600">₺{getTotalPrice()}</p>
          </div>
          <Button 
            onClick={onCheckout}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg"
          >
            Sepeti Onayla
          </Button>
        </div>
        
        {/* Mini cart items - scrollable */}
        <div className="flex space-x-2 overflow-x-auto pb-1">
          {cart.map((item) => (
            <div key={item.id} className="flex-shrink-0 bg-gray-50 rounded-lg p-2 min-w-[120px]">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium truncate">{item.name}</p>
                  <p className="text-xs text-gray-600">₺{item.price}</p>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}
                    className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs"
                  >
                    −
                  </button>
                  <span className="text-xs font-medium w-4 text-center">{item.quantity}</span>
                  <button
                    onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                    className="w-6 h-6 rounded-full bg-orange-500 text-white flex items-center justify-center text-xs"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Desktop Sidebar Cart - Fixed on right */}
      <div className="hidden lg:block fixed right-4 top-1/2 transform -translate-y-1/2 z-40 w-80">
        <Card className="bg-white shadow-xl border border-gray-200">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">🛒 Sepetiniz</h3>
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                {getTotalItems()} ürün
              </Badge>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-1">{restaurantName}</p>
              <div className="h-px bg-gray-200"></div>
            </div>

            {/* Cart items - scrollable */}
            <div className="max-h-64 overflow-y-auto space-y-2 mb-4">
              {cart.map((item) => (
                <div key={item.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-sm">{item.name}</p>
                    <p className="text-sm text-gray-600">₺{item.price} × {item.quantity}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}
                      className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-sm hover:bg-gray-300"
                    >
                      −
                    </button>
                    <span className="font-medium w-6 text-center">{item.quantity}</span>
                    <button
                      onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}
                      className="w-7 h-7 rounded-full bg-orange-500 text-white flex items-center justify-center text-sm hover:bg-orange-600"
                    >
                      +
                    </button>
                    <button
                      onClick={() => onRemoveItem(item.id)}
                      className="ml-2 text-red-500 hover:text-red-700 text-sm"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t pt-3">
              <div className="flex justify-between items-center mb-3">
                <span className="font-bold text-lg">Toplam:</span>
                <span className="font-bold text-lg text-green-600">₺{getTotalPrice()}</span>
              </div>
              
              <Button 
                onClick={onCheckout}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg"
              >
                Sepeti Onayla ({getTotalItems()})
              </Button>
            </div>

            <div className="mt-2 text-xs text-gray-500 text-center">
              Teslimat ücreti ödeme sayfasında hesaplanacaktır
            </div>
          </div>
        </Card>
      </div>

      {/* Mobile spacer - to prevent content from being hidden behind fixed cart */}
      <div className="lg:hidden h-24"></div>
    </>
  );
};

export default StickyCart;