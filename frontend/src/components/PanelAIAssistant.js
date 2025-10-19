/**
 * Panel AI Asistanı Component
 * Admin → Araçlar → Panel AI Asistanı
 * 
 * Features:
 * - Panel-aware AI chat (customer/business/courier/multi)
 * - Streaming markdown responses
 * - Preset questions in Turkish
 * - Time window selection
 * - Context toggles (metrics only / include logs)
 * - RBAC: SuperAdmin & Operasyon only
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import toast from 'react-hot-toast';
import { askAI } from '../api/panelAI';
import ReactMarkdown from 'react-markdown';

const PanelAIAssistant = () => {
  const [scope, setScope] = useState('customer');
  const [timeWindow, setTimeWindow] = useState(60);
  const [includeLogs, setIncludeLogs] = useState(true);
  const [mode, setMode] = useState('summary');
  const [question, setQuestion] = useState('');
  const [output, setOutput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [metadata, setMetadata] = useState(null); // {provider, model, scope, mode}
  const abortControllerRef = useRef(null);
  const outputRef = useRef(null);

  const presets = [
    {
      id: 'critical',
      label: 'Son 15 dk en kritik 3 hata',
      question: 'Son 15 dakikadaki en kritik 3 hatayı listele ve kök nedenlerini açıkla.',
      testId: 'preset-critical'
    },
    {
      id: 'order-delay',
      label: 'Sipariş akışında gecikme',
      question: 'Sipariş akışında gecikmeye neden olabilecek problemleri analiz et ve çözüm öner.',
      testId: 'preset-delay'
    },
    {
      id: 'performance',
      label: 'Performans yavaşlığı',
      question: 'p95 latency yükseldi. Hızlandırma için neler yapılabilir?',
      testId: 'preset-performance'
    },
    {
      id: 'patch',
      label: 'Patch öner (kodla)',
      question: 'En sık karşılaşılan hatalar için kod düzeltmesi öner (FastAPI/React).',
      testId: 'preset-patch'
    }
  ];

  const scopeTips = {
    customer: 'Restoran keşfi, sepet/checkout, kupon, takip',
    business: 'Sipariş liste/onay, menü, SLA',
    courier: 'Görev kabul, WS, rota/konum',
    multi: 'Paneller arası karşılaştırma ve çapraz etki'
  };

  const handlePresetClick = (preset) => {
    setQuestion(preset.question);
    handleSubmit(preset.question);
  };

  const handleSubmit = async (customQuestion = null) => {
    const queryQuestion = customQuestion || question;
    
    if (!queryQuestion.trim()) {
      toast.error('Lütfen bir soru girin.');
      return;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setIsStreaming(true);
    setOutput('');
    setMetadata(null); // Reset metadata

    try {
      await askAI(
        {
          question: queryQuestion,
          scope,
          time_window_minutes: timeWindow,
          include_logs: includeLogs,
          mode
        },
        (chunk) => {
          setOutput(prev => prev + chunk);
        },
        (error) => {
          toast.error(error);
          setIsStreaming(false);
          
          // If LLM call failed, offer link to settings
          if (error.includes('Model yanıtı alınamadı') || error.includes('ayarları kontrol')) {
            setTimeout(() => {
              toast((t) => (
                <div>
                  <p className="font-medium mb-2">LLM yanıtı alınamadı.</p>
                  <button
                    onClick={() => {
                      window.location.href = '#/admin?tab=settings';
                      toast.dismiss(t.id);
                    }}
                    className="text-sm text-blue-600 hover:text-blue-700 underline"
                  >
                    AI Ayarlarına Git →
                  </button>
                </div>
              ), { duration: 8000 });
            }, 500);
          }
        },
        abortControllerRef.current.signal,
        (meta) => {
          // Metadata callback
          setMetadata(meta);
        }
      );
      
      setIsStreaming(false);
      toast.success('✅ Yanıt tamamlandı!');
    } catch (error) {
      console.error('AI query error:', error);
      setIsStreaming(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(output);
    toast.success('Yanıt kopyalandı!');
  };

  const handleKeyDown = (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleSubmit();
    }
  };

  // Auto-scroll to bottom when output updates
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">🤖 Panel AI Asistanı</h2>
          <p className="text-sm text-gray-600 mt-1">
            <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
              Yalnızca seçilen panelin verileri kullanılır
            </span>
          </p>
        </div>
        
        {/* Metadata Badge */}
        {metadata && (
          <div className="text-sm bg-green-50 border border-green-200 rounded-lg px-4 py-2">
            <div className="flex items-center space-x-3 text-green-800">
              <span className="font-medium">Model: {metadata.model}</span>
              <span>•</span>
              <span>Sağlayıcı: {metadata.provider === 'emergent' ? 'Emergent LLM' : 'OpenAI (Özel)'}</span>
              <span>•</span>
              <span>Mod: {metadata.mode === 'summary' ? 'Özet' : (metadata.mode === 'metrics' ? 'Metrik' : 'Patch')}</span>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Sorgu Ayarları</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Scope Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Panel Seçimi
            </label>
            <div className="flex space-x-2">
              {['customer', 'business', 'courier', 'multi'].map((s) => (
                <button
                  key={s}
                  onClick={() => setScope(s)}
                  data-testid={`scope-${s}`}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    scope === s
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {s === 'customer' && '👥 Customer'}
                  {s === 'business' && '🏪 Business'}
                  {s === 'courier' && '🚴 Courier'}
                  {s === 'multi' && '🔀 Multi'}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              💡 {scopeTips[scope]}
            </p>
          </div>

          {/* Time Window */}
          <div>
            <label htmlFor="time-window" className="block text-sm font-medium text-gray-700 mb-2">
              Zaman Aralığı
            </label>
            <select
              id="time-window"
              value={timeWindow}
              onChange={(e) => setTimeWindow(parseInt(e.target.value))}
              data-testid="time-window"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={15}>15 dakika</option>
              <option value={60}>1 saat</option>
              <option value={1440}>24 saat</option>
            </select>
          </div>

          {/* Context Toggles */}
          <div className="flex items-center space-x-6">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={!includeLogs}
                onChange={(e) => setIncludeLogs(!e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">Sadece metrikleri kullan</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeLogs}
                onChange={(e) => setIncludeLogs(e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">Log özetlerini dahil et</span>
            </label>
          </div>

          {/* Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Yanıt Modu
            </label>
            <div className="flex space-x-2">
              {[
                { value: 'metrics', label: '📊 Metrik Analizi' },
                { value: 'summary', label: '📝 Özet & RCA' },
                { value: 'patch', label: '🔧 Kod Patch' }
              ].map((m) => (
                <button
                  key={m.value}
                  onClick={() => setMode(m.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    mode === m.value
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Presets (Left) */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Şablon Sorular</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handlePresetClick(preset)}
                  data-testid={preset.testId}
                  disabled={isStreaming}
                  className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <p className="font-medium text-sm text-gray-900">{preset.label}</p>
                  <p className="text-xs text-gray-500 mt-1">{preset.question}</p>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Chat Area (Right) */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Sohbet</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Prompt Input */}
              <div>
                <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
                  Sorunuz (Ctrl+Enter ile gönder)
                </label>
                <textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Örn: Son 1 saatte en çok hangi hata oluştu?"
                  disabled={isStreaming}
                  data-testid="ai-chat-input"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Submit Button */}
              <button
                onClick={() => handleSubmit()}
                disabled={isStreaming || !question.trim()}
                data-testid="ai-chat-send"
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isStreaming ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Yanıt alınıyor...
                  </span>
                ) : (
                  '📤 Gönder'
                )}
              </button>

              {/* Output */}
              {output || isStreaming ? (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">Yanıt</label>
                    {output && (
                      <button
                        onClick={handleCopy}
                        className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                      >
                        📋 Kopyala
                      </button>
                    )}
                  </div>
                  <div
                    ref={outputRef}
                    data-testid="ai-chat-output"
                    className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto prose prose-sm max-w-none"
                  >
                    {output ? (
                      <ReactMarkdown>{output}</ReactMarkdown>
                    ) : (
                      <div className="flex items-center space-x-2 text-gray-500">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Yanıt bekleniyor...</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-lg font-medium">Soru sorun veya bir şablon seçin.</p>
                  <p className="text-sm mt-2">AI asistanı, seçilen panele özgü analiz yapacak.</p>
                </div>
              )}

              {/* Info Note */}
              {output && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-700">
                    ℹ️ Kişisel veriler maskeleme ile korunmuştur.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PanelAIAssistant;
