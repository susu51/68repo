/**
 * Panel AI Assistant API Client - HARDENED
 * Proper SSE parsing with UTF-8 handling and error recovery
 */

const API_BASE = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_BACKEND_URL;

/**
 * Ask AI question with streaming response
 * @param {Object} params - Query parameters
 * @param {function} onChunk - Callback for each streamed chunk
 * @param {function} onError - Error callback
 * @param {AbortSignal} signal - Abort signal for cancellation
 * @param {function} onMeta - Metadata callback (optional)
 */
export async function askAI({ question, scope, time_window_minutes, include_logs, mode, provider }, onChunk, onError, signal, onMeta) {
  try {
    const body = {
      question,
      scope,
      time_window_minutes,
      include_logs,
      mode
    };
    
    // Add provider only if explicitly set
    if (provider) {
      body.provider = provider;
    }
    
    const response = await fetch(`${API_BASE}/api/admin/ai/ask`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json; charset=utf-8'
      },
      body: JSON.stringify(body),
      signal
    });

    if (!response.ok) {
      if (response.status === 429) {
        throw new Error('Hız limiti aşıldı, lütfen biraz sonra tekrar deneyin.');
      } else if (response.status === 403) {
        throw new Error('Yetkisiz erişim.');
      } else if (response.status === 502 || response.status === 503) {
        throw new Error('Model yanıtı alınamadı. Lütfen ayarları kontrol edip tekrar deneyin.');
      } else if (response.status === 400) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `API hatası: ${response.status}`);
      } else {
        throw new Error(`API hatası: ${response.status}`);
      }
    }

    // Read streaming response with proper UTF-8 handling
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });
      
      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (!line.trim()) continue; // Skip empty lines
        
        if (line.startsWith('data: ')) {
          const data = line.substring(6).trim();
          
          if (data === '[DONE]') {
            return;
          }
          
          if (data) {
            try {
              // Try to parse as JSON
              const parsed = JSON.parse(data);
              
              // Handle error
              if (parsed.error) {
                onError(parsed.error);
                if (parsed.llm_call_failed) {
                  // Special handling for LLM failures
                  console.error('LLM call failed:', parsed.error);
                }
                return;
              }
              
              // Handle metadata
              if (parsed.meta && onMeta) {
                onMeta(parsed.meta);
              }
              
              // Handle delta (content chunk)
              if (parsed.delta) {
                onChunk(parsed.delta);
              }
            } catch (e) {
              // Fallback: treat as plain text (backward compatibility)
              onChunk(data);
            }
          }
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('AI request aborted');
    } else {
      onError(error.message);
    }
  }
}

/**
 * Get AI ingest health status
 */
export async function getAIHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/admin/ai/ingest/health`, {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('AI health check error:', error);
    return { ok: false, error: error.message };
  }
}
