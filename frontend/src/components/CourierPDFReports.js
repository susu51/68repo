import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Calendar, Download, FileText, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://deliverypro.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;

export const CourierPDFReports = () => {
  const [reportType, setReportType] = useState('daily');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [downloading, setDownloading] = useState(false);

  const downloadPDFReport = async () => {
    try {
      setDownloading(true);
      
      // Build URL with parameters
      let url = `${API}/courier/earnings/report/pdf?range=${reportType}`;
      
      if (fromDate) {
        url += `&from_date=${fromDate}`;
      }
      if (toDate) {
        url += `&to_date=${toDate}`;
      }

      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': 'application/pdf'
        }
      });

      if (!response.ok) {
        throw new Error(`PDF indirme başarısız: ${response.status}`);
      }

      // Get the PDF blob
      const blob = await response.blob();
      
      // Check if blob is empty
      if (blob.size === 0) {
        toast.warning('Rapor boş - Bu dönem için veri bulunmuyor');
        return;
      }
      
      // Create download link (React-safe approach)
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `kazanc_raporu_${reportType}_${new Date().toISOString().split('T')[0]}.pdf`;
      a.style.display = 'none';
      
      // Safe DOM manipulation
      try {
        document.body.appendChild(a);
        a.click();
        
        // Cleanup with timeout to avoid React conflicts
        setTimeout(() => {
          try {
            if (a.parentNode) {
              document.body.removeChild(a);
            }
            window.URL.revokeObjectURL(downloadUrl);
          } catch (cleanupError) {
            console.warn('Cleanup error (non-critical):', cleanupError);
          }
        }, 100);
      } catch (domError) {
        console.error('DOM manipulation error:', domError);
        // Fallback: try opening in new tab
        window.open(downloadUrl, '_blank');
        setTimeout(() => window.URL.revokeObjectURL(downloadUrl), 1000);
      }

      toast.success('PDF rapor başarıyla indirildi!');
    } catch (error) {
      console.error('PDF indirme hatası:', error);
      toast.error('PDF indirilemedi: ' + error.message);
    } finally {
      setDownloading(false);
    }
  };

  // Get today's date in YYYY-MM-DD format
  const getTodayDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  // Get date 7 days ago
  const getWeekAgoDate = () => {
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return weekAgo.toISOString().split('T')[0];
  };

  // Get date 30 days ago
  const getMonthAgoDate = () => {
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    return monthAgo.toISOString().split('T')[0];
  };

  // Set date range based on report type
  const handleReportTypeChange = (value) => {
    setReportType(value);
    
    if (value === 'daily') {
      setFromDate(getTodayDate());
      setToDate(getTodayDate());
    } else if (value === 'weekly') {
      setFromDate(getWeekAgoDate());
      setToDate(getTodayDate());
    } else if (value === 'monthly') {
      setFromDate(getMonthAgoDate());
      setToDate(getTodayDate());
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          PDF Kazanç Raporları
        </CardTitle>
        <CardDescription>
          Kazançlarınızı PDF formatında indirin
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Report Type Selection */}
        <div className="space-y-2">
          <Label htmlFor="reportType">Rapor Tipi</Label>
          <select
            id="reportType"
            value={reportType}
            onChange={(e) => handleReportTypeChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="daily">Günlük Rapor</option>
            <option value="weekly">Haftalık Rapor</option>
            <option value="monthly">Aylık Rapor</option>
          </select>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="fromDate">
              <Calendar className="h-4 w-4 inline mr-1" />
              Başlangıç Tarihi
            </Label>
            <Input
              id="fromDate"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              max={getTodayDate()}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="toDate">
              <Calendar className="h-4 w-4 inline mr-1" />
              Bitiş Tarihi
            </Label>
            <Input
              id="toDate"
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              max={getTodayDate()}
              min={fromDate}
            />
          </div>
        </div>

        {/* Quick Date Ranges */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setFromDate(getTodayDate());
              setToDate(getTodayDate());
              setReportType('daily');
            }}
          >
            Bugün
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setFromDate(getWeekAgoDate());
              setToDate(getTodayDate());
              setReportType('weekly');
            }}
          >
            Son 7 Gün
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setFromDate(getMonthAgoDate());
              setToDate(getTodayDate());
              setReportType('monthly');
            }}
          >
            Son 30 Gün
          </Button>
        </div>

        {/* Download Button */}
        <Button
          className="w-full"
          onClick={downloadPDFReport}
          disabled={downloading || !fromDate || !toDate}
        >
          {downloading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              İndiriliyor...
            </>
          ) : (
            <>
              <Download className="h-4 w-4 mr-2" />
              PDF Raporunu İndir
            </>
          )}
        </Button>

        {/* Info Text */}
        <p className="text-sm text-muted-foreground text-center">
          Rapor şunları içerir: Teslimat sayısı, toplam kazanç, işletme bazlı detaylar
        </p>
      </CardContent>
    </Card>
  );
};
