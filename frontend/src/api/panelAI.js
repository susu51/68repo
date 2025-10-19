/**
 * Panel AI Assistant API Client
 * Handles streaming AI responses from backend
 */

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'https://kuryecini-ai-tools.preview.emergentagent.com';

/**
 * Ask AI question with streaming response
 * @param {Object} params - Query parameters
 * @param {function} onChunk - Callback for each streamed chunk
 * @param {function} onError - Error callback
 * @param {AbortSignal} signal - Abort signal for cancellation
 */
export async function askAI({ question, scope, time_window_minutes, include_logs, mode }, onChunk, onError, signal) {
  try {
    const response = await fetch(`${API_BASE}/api/admin/ai/ask`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        question,
        scope,
        time_window_minutes,
        include_logs,
        mode
      }),
      signal
    });

    if (!response.ok) {
      if (response.status === 429) {
        throw new Error('Hız limiti aşıldı, lütfen biraz sonra tekrar deneyin.');
      } else if (response.status === 403) {
        throw new Error('Yetkisiz erişim.');
      } else {
        throw new Error(`API hatası: ${response.status}`);
      }
    }

    // Read streaming response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.substring(6);
          
          if (data === '[DONE]') {
            return;
          }
          
          if (data.trim()) {
            onChunk(data);
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
