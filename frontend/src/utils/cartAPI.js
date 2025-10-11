/**
 * Cart API Management - DB entegrasyonu (CI GATE 0 Compliant)
 * Müşteri sepeti backend'de tutulur, logout/login sonrası korunur
 */

// HARDCODED FOR DEVELOPMENT - BYPASS .ENV ISSUES
const API = import.meta.env.VITE_API_BASE_URL.replace('/api', '');

class CartAPI {
  // Sepeti backend'den yükle
  static async loadCart() {
    try {
      // Using cookie authentication - no token needed
      console.log('🛒 Loading cart from database...');

      const response = await fetch(`${API}/customer/cart`, {
        credentials: 'include',  // Include cookies
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const cartData = await response.json();
        console.log('✅ Cart loaded from DB:', cartData);
        return cartData;
      } else if (response.status === 404) {
        // Sepet yok, yeni sepet
        console.log('🆕 No cart found, creating empty cart');
        return { items: [], restaurant: null };
      } else {
        console.error('❌ Failed to load cart:', response.status);
        return { items: [], restaurant: null };
      }
    } catch (error) {
      console.error('❌ Cart load error:', error);
      return { items: [], restaurant: null };
    }
  }

  // Sepeti backend'e kaydet
  static async saveCart(cartData) {
    try {
      // Cookie authentication - no token needed

      const response = await fetch(`${API}/customer/cart`, {
        method: 'POST',
        credentials: 'include',  // Include cookies
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cartData)
      });

      if (response.ok) {
        console.log('✅ Cart saved to DB');
        return true;
      } else {
        console.error('❌ Failed to save cart:', response.status);
        return false;
      }
    } catch (error) {
      console.error('❌ Cart save error:', error);
      return false;
    }
  }

  // Sepeti temizle
  static async clearCart() {
    try {
      // Cookie authentication - no token needed

      const response = await fetch(`${API}/customer/cart`, {
        method: 'DELETE',
        credentials: 'include',  // Include cookies
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('🗑️ Cart cleared from DB');
      return response.ok;
    } catch (error) {
      console.error('❌ Cart clear error:', error);
      return false;
    }
  }

  // Ürün sepete ekle (optimistic update)
  static async addToCart(product, quantity = 1) {
    try {
      // Cookie authentication - no token needed

      const response = await fetch(`${API}/customer/cart/add`, {
        method: 'POST',
        credentials: 'include',  // Include cookies
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          product_id: product.id,
          quantity: quantity,
          product_info: {
            title: product.title || product.name,
            price: product.price,
            business_id: product.business_id
          }
        })
      });

      if (response.ok) {
        console.log('✅ Item added to cart in DB');
        return true;
      } else {
        console.error('❌ Failed to add item to cart:', response.status);
        return false;
      }
    } catch (error) {
      console.error('❌ Add to cart error:', error);
      return false;
    }
  }
}

export default CartAPI;