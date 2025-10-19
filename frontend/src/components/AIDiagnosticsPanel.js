// AI Diagnostics Panel - Phase 1
// Shell UI with tabs: Özet, Kümeler, Loglar
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Activity, AlertCircle, FileText, Settings, Brain } from 'lucide-react';

export const AIDiagnosticsPanel = () => {
  const [activeTab, setActiveTab] = useState('summary');

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-600" />
            AI Diagnostik
          </h2>
          <p className="text-muted-foreground">
            Merkezi log analizi, hata kümeleme ve AI destekli sorun çözme
          </p>
        </div>
        <Badge variant="outline" className="bg-purple-50 text-purple-700">
          Phase 1 - Temel Altyapı
        </Badge>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('summary')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'summary'
              ? 'border-b-2 border-purple-600 text-purple-600'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Activity className="inline h-4 w-4 mr-2" />
          Özet
        </button>
        
        <button
          onClick={() => setActiveTab('clusters')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'clusters'
              ? 'border-b-2 border-purple-600 text-purple-600'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <AlertCircle className="inline h-4 w-4 mr-2" />
          Kümeler
        </button>
        
        <button
          onClick={() => setActiveTab('logs')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'logs'
              ? 'border-b-2 border-purple-600 text-purple-600'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <FileText className="inline h-4 w-4 mr-2" />
          Loglar
        </button>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'summary' && <SummaryTab />}
        {activeTab === 'clusters' && <ClustersTab />}
        {activeTab === 'logs' && <LogsTab />}
      </div>
    </div>
  );
};

// Summary Tab - KPI Overview
const SummaryTab = () => {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Son 15 Dakika</p>
                <p className="text-2xl font-bold">-</p>
                <p className="text-xs text-muted-foreground">Error Rate</p>
              </div>
              <div className="text-4xl">🟢</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Aktif Kümeler</p>
                <p className="text-2xl font-bold">-</p>
                <p className="text-xs text-muted-foreground">24 Saat</p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">P95 Latency</p>
                <p className="text-2xl font-bold">-</p>
                <p className="text-xs text-muted-foreground">Milliseconds</p>
              </div>
              <div className="text-4xl">⚡</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Queue Depth</p>
                <p className="text-2xl font-bold">-</p>
                <p className="text-xs text-muted-foreground">Bekleyen</p>
              </div>
              <div className="text-4xl">📦</div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Phase 1 - Tamamlandı ✅</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>PII Redaction: E-posta, telefon, IBAN, JWT maskeleme</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>Log Ingestion: POST /admin/logs/ingest endpoint</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>Fingerprinting: Otomatik hata kümeleme</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>MongoDB Collections: ai_logs, ai_clusters</span>
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-600">✓</span>
              <span>Admin UI: AI Diagnostik tab (RBAC korumalı)</span>
            </li>
          </ul>
          
          <div className="mt-4 p-3 bg-purple-50 rounded-lg">
            <p className="text-sm font-medium text-purple-900">Sonraki: Phase 2</p>
            <p className="text-xs text-purple-700 mt-1">
              ChatGPT entegrasyonu, AI Assistant UI, rate limiting
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Clusters Tab - Placeholder
const ClustersTab = () => {
  return (
    <Card>
      <CardContent className="text-center py-12">
        <AlertCircle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Kümeler</h3>
        <p className="text-muted-foreground mb-4">
          Hata kümeleri Phase 2'de görüntülenecek
        </p>
        <Badge variant="outline">Phase 2'de gelecek</Badge>
      </CardContent>
    </Card>
  );
};

// Logs Tab - Placeholder
const LogsTab = () => {
  return (
    <Card>
      <CardContent className="text-center py-12">
        <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Log Görüntüleyici</h3>
        <p className="text-muted-foreground mb-4">
          Gerçek zamanlı log akışı Phase 3'te aktif olacak
        </p>
        <Badge variant="outline">Phase 3'te gelecek</Badge>
      </CardContent>
    </Card>
  );
};

export default AIDiagnosticsPanel;
