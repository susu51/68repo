/**
 * Ops Co-Pilot API Client
 * For structured 7-block diagnostic responses
 */

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://courier-connect-14.preview.emergentagent.com';

/**
 * Ask Ops Co-Pilot for structured diagnostic response
 * @param {Object} params - Query parameters {panel, message, model}
 * @returns {Promise<Object>} Response with {response, panel}
 */
export async function askOpsCoPilot({ panel, message, model }) {
  try {
    const body = { panel, message };
    
    // Add model if specified
    if (model) {
      body.model = model;
    }
    
    const response = await fetch(`${API_BASE}/api/admin/ai/assist`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json; charset=utf-8'
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        throw new Error('Yetkisiz erişim.');
      } else if (response.status === 422) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.[0]?.msg || 'Geçersiz istek.');
      } else if (response.status === 500) {
        const errorData = await response.json();
        // If error response contains 7-block format, throw it
        if (errorData.detail?.response) {
          const error = new Error('LLM hatası');
          error.response = errorData.detail.response;
          throw error;
        }
        throw new Error('Sunucu hatası. Lütfen tekrar deneyin.');
      } else {
        throw new Error(`API hatası: ${response.status}`);
      }
    }

    return await response.json();
  } catch (error) {
    console.error('Ops Co-Pilot error:', error);
    throw error;
  }
}

/**
 * Execute diagnostic tool manually
 * @param {string} toolId - Tool name (http_get, logs_tail, db_query, env_list)
 * @param {Object} params - Tool-specific parameters
 * @returns {Promise<Object>} Tool execution result
 */
export async function executeTool(toolId, params) {
  try {
    let endpoint = '';
    let method = 'POST';
    let body = params;
    
    // Map tool to endpoint
    if (toolId === 'http_get') {
      endpoint = `${API_BASE}/api/admin/ai/tools/http_get`;
    } else if (toolId === 'logs_tail') {
      endpoint = `${API_BASE}/api/admin/ai/tools/logs_tail`;
    } else if (toolId === 'db_query') {
      endpoint = `${API_BASE}/api/admin/ai/tools/db_query`;
    } else if (toolId === 'env_list') {
      endpoint = `${API_BASE}/api/admin/ai/tools/env_list`;
      method = 'GET';
      const queryParams = new URLSearchParams(params).toString();
      endpoint += `?${queryParams}`;
      body = null;
    } else {
      throw new Error(`Unknown tool: ${toolId}`);
    }
    
    const options = {
      method,
      credentials: 'include',
      headers: method === 'POST' ? {
        'Content-Type': 'application/json; charset=utf-8'
      } : {}
    };
    
    if (method === 'POST' && body) {
      options.body = JSON.stringify(body);
    }
    
    const response = await fetch(endpoint, options);

    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        throw new Error('Yetkisiz erişim.');
      } else if (response.status === 422) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.[0]?.msg || `Tool parametreleri hatalı: ${toolId}`);
      } else {
        throw new Error(`Tool ${toolId} hatası: ${response.status}`);
      }
    }

    return await response.json();
  } catch (error) {
    console.error(`Tool ${toolId} error:`, error);
    throw error;
  }
}
