/**
 * Cart API Management - LocalStorage based (simplified for quick ordering)
 * Müşteri sepeti browser'da localStorage'de tutulur
 */

const CART_STORAGE_KEY = 'kuryecini_cart';

class CartAPI {
  // Sepeti localStorage'den yükle
  static async loadCart() {
    try {
      console.log('🛒 Loading cart from localStorage...');
      const cartString = localStorage.getItem(CART_STORAGE_KEY);
      
      if (cartString) {
        const cartData = JSON.parse(cartString);
        console.log('✅ Cart loaded from localStorage:', cartData);
        return cartData;
      } else {
        console.log('🆕 No cart found, creating empty cart');
        return { items: [], restaurant: null };
      }
    } catch (error) {
      console.error('❌ Cart load error:', error);
      return { items: [], restaurant: null };
    }
  }

  // Sepeti localStorage'e kaydet
  static async saveCart(cartData) {
    try {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cartData));
      console.log('✅ Cart saved to localStorage');
      return true;
    } catch (error) {
      console.error('❌ Cart save error:', error);
      return false;
    }
  }

  // Sepeti temizle
  static async clearCart() {
    try {
      localStorage.removeItem(CART_STORAGE_KEY);
      console.log('🗑️ Cart cleared from localStorage');
      return true;
    } catch (error) {
      console.error('❌ Cart clear error:', error);
      return false;
    }
  }

  // Ürün sepete ekle (localStorage güncellemesi otomatik olacak)
  static async addToCart(product, quantity = 1) {
    try {
      console.log('✅ Item will be added to cart (handled by CartContext)');
      return true;
    } catch (error) {
      console.error('❌ Add to cart error:', error);
      return false;
    }
  }
}

export default CartAPI;