import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { toast } from 'react-hot-toast';

// Cart Context
const CartContext = createContext();

// Cart Actions
const CART_ACTIONS = {
  ADD_ITEM: 'ADD_ITEM',
  REMOVE_ITEM: 'REMOVE_ITEM',
  UPDATE_QUANTITY: 'UPDATE_QUANTITY',
  CLEAR_CART: 'CLEAR_CART',
  SET_RESTAURANT: 'SET_RESTAURANT',
  LOAD_CART: 'LOAD_CART'
};

// Cart Reducer
function cartReducer(state, action) {
  switch (action.type) {
    case CART_ACTIONS.SET_RESTAURANT:
      // If changing restaurant, clear cart
      if (state.restaurant && state.restaurant.id !== action.payload.id && state.items.length > 0) {
        toast.success('Sepet temizlendi - farklı restoran seçildi');
        return {
          ...state,
          restaurant: action.payload,
          items: []
        };
      }
      return {
        ...state,
        restaurant: action.payload
      };

    case CART_ACTIONS.ADD_ITEM:
      const existingItemIndex = state.items.findIndex(item => item.id === action.payload.id);
      
      if (existingItemIndex >= 0) {
        // Item already exists, increase quantity
        const updatedItems = [...state.items];
        updatedItems[existingItemIndex].quantity += action.payload.quantity || 1;
        toast.success(`${action.payload.name} sepete eklendi`);
        
        return {
          ...state,
          items: updatedItems
        };
      } else {
        // New item
        const newItem = {
          ...action.payload,
          quantity: action.payload.quantity || 1
        };
        toast.success(`${action.payload.name} sepete eklendi`);
        
        return {
          ...state,
          items: [...state.items, newItem]
        };
      }

    case CART_ACTIONS.UPDATE_QUANTITY:
      const { itemId, quantity } = action.payload;
      
      if (quantity <= 0) {
        return cartReducer(state, { type: CART_ACTIONS.REMOVE_ITEM, payload: itemId });
      }
      
      return {
        ...state,
        items: state.items.map(item =>
          item.id === itemId ? { ...item, quantity } : item
        )
      };

    case CART_ACTIONS.REMOVE_ITEM:
      const itemToRemove = state.items.find(item => item.id === action.payload);
      if (itemToRemove) {
        toast.success(`${itemToRemove.name} sepetten çıkarıldı`);
      }
      
      return {
        ...state,
        items: state.items.filter(item => item.id !== action.payload)
      };

    case CART_ACTIONS.CLEAR_CART:
      toast.success('Sepet temizlendi');
      return {
        ...state,
        items: [],
        restaurant: null
      };

    case CART_ACTIONS.LOAD_CART:
      return {
        ...state,
        ...action.payload
      };

    default:
      return state;
  }
}

// Initial state
const initialState = {
  items: [],
  restaurant: null
};

// Cart Provider Component
export function CartProvider({ children }) {
  const [cart, dispatch] = useReducer(cartReducer, initialState);

  // Load cart from localStorage on mount
  useEffect(() => {
    const savedCart = localStorage.getItem('kuryecini_cart');
    if (savedCart) {
      try {
        const parsedCart = JSON.parse(savedCart);
        dispatch({ type: CART_ACTIONS.LOAD_CART, payload: parsedCart });
      } catch (error) {
        console.error('Error loading cart from localStorage:', error);
        localStorage.removeItem('kuryecini_cart');
      }
    }
  }, []);

  // Save cart to localStorage whenever cart changes
  useEffect(() => {
    localStorage.setItem('kuryecini_cart', JSON.stringify(cart));
  }, [cart]);

  // Cart utility functions
  const addToCart = (product, quantity = 1) => {
    if (!product || !product.id) {
      console.error('Invalid product data:', product);
      return;
    }

    if (quantity < 0) {
      // Handle negative quantity as a decrease
      const currentItem = cart.items?.find(item => item.id === product.id);
      if (currentItem) {
        const newQuantity = currentItem.quantity + quantity;
        if (newQuantity <= 0) {
          removeFromCart(product.id);
        } else {
          updateQuantity(product.id, newQuantity);
        }
      }
      return;
    }
    
    dispatch({ 
      type: CART_ACTIONS.ADD_ITEM, 
      payload: { ...product, quantity } 
    });
  };

  const removeFromCart = (itemId) => {
    dispatch({ 
      type: CART_ACTIONS.REMOVE_ITEM, 
      payload: itemId 
    });
  };

  const updateQuantity = (itemId, quantity) => {
    dispatch({ 
      type: CART_ACTIONS.UPDATE_QUANTITY, 
      payload: { itemId, quantity } 
    });
  };

  const clearCart = () => {
    dispatch({ type: CART_ACTIONS.CLEAR_CART });
  };

  const setRestaurant = (restaurant) => {
    dispatch({ 
      type: CART_ACTIONS.SET_RESTAURANT, 
      payload: restaurant 
    });
  };

  // Calculate totals
  const getItemCount = () => {
    return cart.items.reduce((total, item) => total + item.quantity, 0);
  };

  const getSubtotal = () => {
    return cart.items.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  const getDeliveryFee = () => {
    const subtotal = getSubtotal();
    return subtotal >= 50 ? 0 : 8.50; // Free delivery over 50 TL
  };

  const getServiceFee = () => {
    const subtotal = getSubtotal();
    return subtotal * 0.02; // 2% service fee
  };

  const getTotal = () => {
    return getSubtotal() + getDeliveryFee() + getServiceFee();
  };

  const getCartSummary = () => ({
    itemCount: getItemCount(),
    subtotal: getSubtotal(),
    deliveryFee: getDeliveryFee(),
    serviceFee: getServiceFee(),
    total: getTotal()
  });

  // Check if item is in cart
  const isInCart = (itemId) => {
    return cart.items.some(item => item.id === itemId);
  };

  // Get item quantity in cart
  const getItemQuantity = (itemId) => {
    const item = cart.items.find(item => item.id === itemId);
    return item ? item.quantity : 0;
  };

  const value = {
    cart,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart,
    setRestaurant,
    getItemCount,
    getSubtotal,
    getDeliveryFee,
    getServiceFee,
    getTotal,
    getCartSummary,
    isInCart,
    getItemQuantity
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
}

// Custom hook to use cart context
export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}

export default CartContext;