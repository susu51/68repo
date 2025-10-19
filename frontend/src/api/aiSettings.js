/**
 * AI Settings API Client
 * Handles all AI Settings API calls for Admin Panel
 */

import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-ai-tools.preview.emergentagent.com';

/**
 * Get current AI settings
 * @returns {Promise<Object>} AI settings object
 */
export async function getAISettings() {
  try {
    const response = await axios.get(`${API_BASE}/api/admin/ai/settings`, {
      withCredentials: true,
      timeout: 10000
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 403) {
      toast.error('Yetkisiz erişim.');
      throw new Error('Unauthorized');
    }
    toast.error('Ayarlar yüklenemedi.');
    throw error;
  }
}

/**
 * Update AI settings
 * @param {Object} settings - Settings object to update
 * @returns {Promise<Object>} Updated settings
 */
export async function putAISettings(settings) {
  try {
    const response = await axios.put(
      `${API_BASE}/api/admin/ai/settings`,
      settings,
      {
        withCredentials: true,
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 403) {
      toast.error('Yetkisiz erişim.');
      throw new Error('Unauthorized');
    }
    const errorMessage = error.response?.data?.detail || 'Ayarlar kaydedilemedi.';
    toast.error(errorMessage);
    throw error;
  }
}

/**
 * Test OpenAI connection with current settings
 * @returns {Promise<Object>} Test result
 */
export async function testAISettings() {
  try {
    const response = await axios.post(
      `${API_BASE}/api/admin/ai/settings/test`,
      {},
      {
        withCredentials: true,
        timeout: 30000, // 30 seconds for AI test
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 403) {
      toast.error('Yetkisiz erişim.');
      throw new Error('Unauthorized');
    }
    const errorMessage = error.response?.data?.detail || 'Bağlantı testi başarısız.';
    toast.error(errorMessage);
    throw error;
  }
}

/**
 * Self-test LLM connection
 * @returns {Promise<Object>} Self-test result with provider, model, latency
 */
export async function selftestAI() {
  try {
    const response = await axios.post(
      `${API_BASE}/api/admin/ai/selftest`,
      {},
      {
        withCredentials: true,
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error) {
    if (error.response?.status === 401 || error.response?.status === 403) {
      toast.error('Yetkisiz erişim.');
      throw new Error('Unauthorized');
    }
    const errorMessage = error.response?.data?.detail || 'Self-test başarısız.';
    toast.error(errorMessage);
    throw error;
  }
}
