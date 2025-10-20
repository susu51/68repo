/**
 * Kuryecini Ops Co-Pilot Component
 * Admin → Araçlar → Ops Co-Pilot
 * 
 * Features:
 * - 7-block structured Turkish diagnostic responses
 * - Panel selection (müşteri/işletme/kurye/admin/multi)
 * - Preset diagnostic questions
 * - Manual tool invocation buttons
 * - RBAC: SuperAdmin & Operasyon only
 */

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import toast from 'react-hot-toast';
import { askOpsCoPilot, executeTool } from '../api/opsCoPilot';
import ReactMarkdown from 'react-markdown';

const OpsCoPilot = () => {
  const [panel, setPanel] = useState('müşteri');
  const [question, setQuestion] = useState('');
  const [output, setOutput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [toolResults, setToolResults] = useState({});
  const outputRef = useRef(null);

  const presets = [
    {
      id: 'restaurants-missing',
      label: 'Restoranlar Gözükmüyor',
      question: 'restoranlar gözükmüyor, nasıl çözebilirim?',
      testId: 'preset-restaurants'
    },
    {
      id: 'order-button',
      label: 'Sipariş Ver Butonu',
      question: 'Sipariş Ver butonu çalışmıyor, double API prefix olabilir mi?',
      testId: 'preset-order-button'
    },
    {
      id: 'courier-tasks',
      label: 'Kurye Görev Listesi',
      question: 'Kurye panelinde görev listesi boş gözüküyor',
      testId: 'preset-courier-tasks'
    },
    {
      id: 'menu-loading',
      label: 'Menü Yüklenmiyor',
      question: 'Restoran menüsü yüklenmiyor, 404 hatası alıyorum',
      testId: 'preset-menu-loading'
    },
    {
      id: 'performance',
      label: 'Performans Sorunu',
      question: 'API latency yüksek, p95 > 500ms',
      testId: 'preset-performance'
    }
  ];

  const panelTips = {
    'müşteri': 'Restoran keşfi, sepet/checkout, kupon, sipariş takibi',
    'işletme': 'Sipariş liste/onay, menü yönetimi, çalışma saatleri',
    'kurye': 'Görev kabul, WS bağlantısı, rota/konum, ETA',
    'admin': 'Sistem ayarları, KYC, analitik, monitoring',
    'multi': 'Paneller arası karşılaştırma ve çapraz etki analizi'
  };

  const tools = [
    { id: 'http_get', label: '🌐 HTTP GET', description: 'Healthcheck ve endpoint doğrulama' },
    { id: 'logs_tail', label: '📋 Logs Tail', description: 'Son N satır log' },
    { id: 'db_query', label: '🗄️ DB Query', description: 'MongoDB readonly sorgu' },
    { id: 'env_list', label: '⚙️ Env List', description: 'ENV değişkenlerini listele (maskeli)' }
  ];

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

    setIsLoading(true);
    setOutput('');

    try {
      const response = await askOpsCoPilot({
        panel,
        message: queryQuestion
      });
      
      setOutput(response.response);
      toast.success('✅ Teşhis tamamlandı!');
    } catch (error) {
      console.error('Ops Co-Pilot error:', error);
      toast.error(error.message || 'Yanıt alınamadı');
      
      // Show error in 7-block format if available
      if (error.response) {
        setOutput(error.response);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleToolExecution = async (toolId) => {
    // Tool-specific parameter prompts
    let params = {};
    
    try {
      if (toolId === 'http_get') {
        const url = prompt('Endpoint URL:', 'http://localhost:8001/health');
        if (!url) return;
        params = { url };
      } else if (toolId === 'logs_tail') {
        const path = prompt('Log dosyası yolu:', '/var/log/supervisor/backend.out.log');
        const limit = prompt('Kaç satır?', '100');
        if (!path) return;
        params = { path, limit: parseInt(limit) };
      } else if (toolId === 'db_query') {
        const collection = prompt('Koleksiyon adı:', 'businesses');
        const action = prompt('Action (count/find_one/list_indexes):', 'count');
        if (!collection || !action) return;
        params = { collection, action };
      } else if (toolId === 'env_list') {
        params = { mask: true };
      }

      toast.loading(`${toolId} çalıştırılıyor...`);
      
      const result = await executeTool(toolId, params);
      
      toast.dismiss();
      toast.success(`✅ ${toolId} başarılı!`);
      
      // Store tool results
      setToolResults(prev => ({
        ...prev,
        [toolId]: result
      }));
      
      // Append to output
      const resultText = `\n\n---\n## Tool: ${toolId}\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\`\n`;
      setOutput(prev => prev + resultText);
      
    } catch (error) {
      toast.dismiss();
      toast.error(error.message || `Tool ${toolId} başarısız`);
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

  // Check for 7 required sections
  const validate7Blocks = (text) => {
    const required = [
      'Hızlı Teşhis',
      'Derin RCA',
      'Kontrol Komutları',
      'Patch',
      'Test',
      'İzleme & Alarm',
      'DoD'
    ];
    
    return required.filter(block => text.includes(block));
  };

  const foundBlocks = output ? validate7Blocks(output) : [];

  return (
    <div className="space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">🛠️ Kuryecini Ops Co-Pilot</h2>
          <p className="text-sm text-gray-600 mt-1">
            <span className="inline-block bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs">
              7 bloklu yapılandırılmış teşhis sistemi
            </span>
          </p>
        </div>
        
        {/* Validation Badge */}
        {output && foundBlocks.length > 0 && (
          <div className="text-sm bg-green-50 border border-green-200 rounded-lg px-4 py-2">
            <div className="flex items-center space-x-2 text-green-800">
              <span className="font-medium">✅ {foundBlocks.length}/7 blok</span>
              {foundBlocks.length === 7 && <span>• Tam format</span>}
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Panel Seçimi</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Panel Selector */}
          <div>
            <div className="flex space-x-2">
              {['müşteri', 'işletme', 'kurye', 'admin', 'multi'].map((p) => (
                <button
                  key={p}
                  onClick={() => setPanel(p)}
                  data-testid={`panel-${p}`}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    panel === p
                      ? 'bg-orange-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {p === 'müşteri' && '👥'}
                  {p === 'işletme' && '🏪'}
                  {p === 'kurye' && '🚴'}
                  {p === 'admin' && '⚙️'}
                  {p === 'multi' && '🔀'}
                  {' '}{p.charAt(0).toUpperCase() + p.slice(1)}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              💡 {panelTips[panel]}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Presets & Tools (Left) */}
        <div className="lg:col-span-1 space-y-4">
          {/* Preset Questions */}
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
                  disabled={isLoading}
                  className="w-full text-left px-4 py-3 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <p className="font-medium text-sm text-gray-900">{preset.label}</p>
                  <p className="text-xs text-gray-500 mt-1">{preset.question}</p>
                </button>
              ))}
            </CardContent>
          </Card>

          {/* Tool Buttons */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Manuel Tool'lar</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => handleToolExecution(tool.id)}
                  disabled={isLoading}
                  className="w-full text-left px-4 py-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <p className="font-medium text-sm text-gray-900">{tool.label}</p>
                  <p className="text-xs text-gray-500 mt-1">{tool.description}</p>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Diagnostic Area (Right) */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Teşhis Asistanı</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Prompt Input */}
              <div>
                <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
                  Sorun Tanımı (Ctrl+Enter ile gönder)
                </label>
                <textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Örn: restoranlar gözükmüyor, nasıl çözebilirim?"
                  disabled={isLoading}
                  data-testid="ops-copilot-input"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Submit Button */}
              <button
                onClick={() => handleSubmit()}
                disabled={isLoading || !question.trim()}
                data-testid="ops-copilot-send"
                className="w-full bg-orange-600 text-white px-6 py-3 rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Teşhis ediliyor...
                  </span>
                ) : (
                  '🛠️ Teşhis Et'
                )}
              </button>

              {/* Output */}
              {output || isLoading ? (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">Yapılandırılmış Yanıt (7-Blok)</label>
                    {output && (
                      <button
                        onClick={handleCopy}
                        className="text-xs text-orange-600 hover:text-orange-700 font-medium"
                      >
                        📋 Kopyala
                      </button>
                    )}
                  </div>
                  <div
                    ref={outputRef}
                    data-testid="ops-copilot-output"
                    className="bg-gray-50 p-4 rounded-lg max-h-[600px] overflow-y-auto prose prose-sm max-w-none"
                  >
                    {output ? (
                      <ReactMarkdown>{output}</ReactMarkdown>
                    ) : (
                      <div className="flex items-center space-x-2 text-gray-500">
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        <span>Teşhis yapılıyor...</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-lg font-medium">Sorun tanımı girin veya şablon seçin.</p>
                  <p className="text-sm mt-2">Ops Co-Pilot, 7 bloklu yapılandırılmış teşhis raporu üretecek.</p>
                </div>
              )}

              {/* Info Note */}
              {output && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <div className="text-xs text-blue-700 space-y-1">
                    <p>ℹ️ Format: Hızlı Teşhis → Derin RCA → Kontrol Komutları → Patch → Test → İzleme & Alarm → DoD</p>
                    <p>🔒 Kişisel veriler otomatik maskelenmiştir.</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default OpsCoPilot;
