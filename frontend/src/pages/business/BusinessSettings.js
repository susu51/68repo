import React from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Settings } from 'lucide-react';

export const BusinessSettings = () => {
  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold text-foreground mb-6">Ayarlar</h1>
      <Card>
        <CardContent className="text-center py-12">
          <Settings className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">İşletme Ayarları</h3>
          <p className="text-muted-foreground">Çalışma saatleri, adres ve diğer ayarlar yakında</p>
        </CardContent>
      </Card>
    </div>
  );
};